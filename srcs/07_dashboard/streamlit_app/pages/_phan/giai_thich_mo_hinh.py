"""Dashboard 3: 'Mo hinh hoc duoc gi?' - SHAP explainability, dong bo theme sang
voi 2 trang kia. Sua 2 bug that: (1) plotly_dark + COLOR_BG toi cung trong code
lam lech theme, (2) px.scatter tu dong bat WebGL (scattergl) khi nhieu diem, loi
tren may/trinh duyet khong ho tro WebGL - ep render_mode='svg' de an toan.
"""

import json
import os
import pickle
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import streamlit as st

from dashboard_common import header_bao_cao, load_shared_css, nap_runtime_cpp

# Trang nay import shap va doc model LightGBM nen can runtime C++ tren NixOS.
# Goi lai o day (khong chi dua vao app.py) de trang van chay duoc khi mo truc tiep
# bang `streamlit run pages/2_SHAP.py`. CDLL nap lai cung tep la thao tac vo hai.
nap_runtime_cpp()

PROJECT_ROOT = Path(__file__).resolve().parents[5]
VERSION = os.environ.get("DASHBOARD_VERSION", "v5")
DATA_DIR = PROJECT_ROOT / "data" / "model" / VERSION

# Rieng trang SHAP: kpi-value nho hon mac dinh (nhieu KPI hon tren 1 hang).
st.markdown("<style>.kpi-value { font-size: 1.15rem !important; }</style>", unsafe_allow_html=True)


def kpi(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
<div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>""",
        unsafe_allow_html=True,
    )



def _build_model_specs() -> dict[str, dict[str, Path | str]]:
    """Discover model artifacts so every XAI view uses one selected model."""
    specs: dict[str, dict[str, Path | str]] = {}
    best_loss_path = DATA_DIR / "07_final_test" / "best_loss.json"
    best_loss = json.loads(best_loss_path.read_text(encoding="utf-8")) if best_loss_path.exists() else {}
    persisted_explain_key = f"{best_loss.get('h1', {}).get('winning_loss', '')}_h1"
    for loss in ("mae", "huber", "mse"):
        for horizon in ("h1", "h4"):
            key = f"{loss}_{horizon}"
            model_path = DATA_DIR / "06_train" / loss / horizon / "model.pkl"
            config_path = DATA_DIR / "06_train" / loss / horizon / "model_config.json"
            final_test_path = DATA_DIR / "07_final_test" / horizon / f"X_test_{horizon}.parquet"
            train_test_path = DATA_DIR / "06_train" / loss / horizon / f"X_test_{horizon}.parquet"
            if not (model_path.exists() and config_path.exists()):
                continue
            x_test_path = final_test_path if final_test_path.exists() else train_test_path
            explain_dir = DATA_DIR / "08_explain"
            shap_path = explain_dir / "shap_values.parquet" if key == persisted_explain_key else None
            importance_path = explain_dir / "shap_importance.csv" if key == persisted_explain_key else None
            specs[key] = {
                "key": key,
                "label": f"{loss.upper()} · {horizon.upper()}",
                "loss": loss,
                "horizon": horizon,
                "model_path": model_path,
                "config_path": config_path,
                "x_test_path": x_test_path,
                "shap_path": shap_path,
                "importance_path": importance_path,
            }
    return specs


MODEL_SPECS = _build_model_specs()


def _unwrap_model(bundle):
    return bundle.get("model", bundle) if isinstance(bundle, dict) else bundle


# cache_resource (khong phai cache_data): tranh copy frame 483k dong moi lan goi va
# tranh bam DataFrame lon lam khoa cache — khoa la cache_key, frame `_` khong bi bam.
# Ket qua la object dung chung: CHI DOC, khong duoc mutate.
@st.cache_resource
def load_real_feature_values(
    cache_key: str, _feat_val_keys: pd.DataFrame, x_test_path: str
) -> pd.DataFrame:
    """shap_values.parquet CHI chua gia tri SHAP (bien do nho +-0.01..0.09), KHONG
    chua gia tri dac trung goc (vd shortwave_radiation phai la 0-1100 W/m2 that,
    khong phai +-0.06). Phai join voi X_test_h1.parquet (co gia tri that) qua
    site_id+timestamp de lay dung du lieu cho PDP/scatter, khong dung nham SHAP
    lam gia tri dac trung nhu ban dau."""
    del cache_key  # chi dung lam khoa cache thay cho viec bam _feat_val_keys
    x_test_file = Path(x_test_path)
    if not x_test_file.exists() or _feat_val_keys.empty:
        return pd.DataFrame()
    x_real = pd.read_parquet(x_test_file)
    # Ep float32 cho cot so: giam ~mot nua RAM cua frame 483k dong ma khong anh
    # huong hien thi (bieu do chi can 7 chu so co nghia).
    for c in x_real.columns:
        if pd.api.types.is_float_dtype(x_real[c]):
            x_real[c] = x_real[c].astype(np.float32)
    keys = _feat_val_keys[["site_id", "timestamp"]].copy()
    keys["timestamp"] = pd.to_datetime(keys["timestamp"])
    x_real["timestamp"] = pd.to_datetime(x_real["timestamp"])
    return keys.merge(x_real, on=["site_id", "timestamp"], how="left")


@st.cache_data(show_spinner="Đang tính SHAP cho mô hình đã chọn...")
def compute_local_shap(model_path: str, config_path: str, x_test_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute a deterministic 2,000-row SHAP sample when no persisted artifact exists."""
    with open(model_path, "rb") as fh:
        model = _unwrap_model(pickle.load(fh))
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    test_df = pd.read_parquet(x_test_path).reset_index(drop=True)
    features = list(config["features"])
    feat_cols = [c for c in features if c in test_df.columns and pd.api.types.is_numeric_dtype(test_df[c])]
    medians = pd.Series(config.get("feature_medians", {}), dtype="float64")
    x_test = test_df[feat_cols].fillna(medians).astype(float)
    rng = np.random.default_rng(42)
    sample_idx = rng.choice(len(x_test), size=min(2000, len(x_test)), replace=False)
    x_sample = x_test.iloc[sample_idx]
    shap_values = shap.TreeExplainer(model).shap_values(x_sample)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    df_values = pd.DataFrame(shap_values, columns=feat_cols)
    df_importance = pd.DataFrame(
        {"feature": feat_cols, "mean_abs_shap": np.abs(shap_values).mean(axis=0)}
    ).sort_values("mean_abs_shap", ascending=False)
    sample_meta = test_df.iloc[sample_idx][["site_id", "timestamp"]].reset_index(drop=True)
    return df_importance, pd.concat([sample_meta, df_values.reset_index(drop=True)], axis=1)


# cache_resource: shap_values.parquet nang 126 MB — cache_data se tra BAN COPY moi
# lan goi. Ket qua la object dung chung, CHI DOC.
@st.cache_resource
def load_local_shap(
    model_key: str,
    model_path: str,
    config_path: str,
    x_test_path: str,
    importance_path: str | None,
    shap_path: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    del model_key
    p_imp = Path(importance_path) if importance_path else None
    p_val = Path(shap_path) if shap_path else None
    if p_imp is not None and p_val is not None and p_imp.is_file() and p_val.is_file():
        return pd.read_csv(p_imp), pd.read_parquet(p_val)
    return compute_local_shap(model_path, config_path, x_test_path)


@st.cache_data
def load_shap_base_value(model_path: str) -> float:
    with open(model_path, "rb") as fh:
        model = _unwrap_model(pickle.load(fh))
    expected = np.asarray(shap.TreeExplainer(model).expected_value).reshape(-1)
    return float(expected[0])


def denormalize_local_prediction(
    base_value: float, shap_total: float, row: pd.Series | None, config_path: str
) -> float | None:
    """Convert local model output k back to kWh using the notebook formula."""
    if row is None:
        return None
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    scale_col = config.get("cot_quy_mo", "site_scale")
    elev_col = config.get("cot_sin_elev", "sin_elevation")
    tran_col = config.get("cot_tran", "tran_cong_suat")
    if not all(col in row.index and pd.notna(row[col]) for col in (scale_col, elev_col)):
        return None

    eps = float(config.get("eps_elev", 0.05))
    sin_elev = float(row[elev_col])
    if sin_elev <= eps:
        return 0.0
    k_pred = float(np.clip(base_value + shap_total, 0.0, 1.5))
    y_pred = k_pred * float(row[scale_col]) * max(sin_elev, eps)
    if tran_col in row.index and pd.notna(row[tran_col]):
        y_pred = min(y_pred, float(row[tran_col]) * 1.02)
    return float(y_pred)


# Bo loc XAI nam trong THAN TRANG (khong o sidebar): phan nay chay trong st.fragment
# (xem 1_ML.py) va fragment khong duoc ve widget vao sidebar.
if not MODEL_SPECS:
    st.error(f"Không tìm thấy model artifact trong data/model/{VERSION}/06_train.")
    st.stop()
_model_keys = list(MODEL_SPECS)
_default_key = "mae_h1" if "mae_h1" in MODEL_SPECS else _model_keys[0]
_c_loc_xai, _ = st.columns([1, 2], gap="small")
_model_key = _c_loc_xai.selectbox(
    "Bộ lọc XAI — Mô hình / horizon",
    _model_keys,
    index=_model_keys.index(_default_key),
    format_func=lambda key: MODEL_SPECS[key]["label"],
)

_model_spec = MODEL_SPECS[_model_key]
df_imp, df_val = load_local_shap(
    _model_key,
    str(_model_spec["model_path"]),
    str(_model_spec["config_path"]),
    str(_model_spec["x_test_path"]),
    str(_model_spec["importance_path"]) if _model_spec["importance_path"] else None,
    str(_model_spec["shap_path"]) if _model_spec["shap_path"] else None,
)
if df_imp.empty:
    st.warning(f"Chưa có dữ liệu SHAP cho {_model_spec['label']} và không thể tính từ artifact hiện có.")
    st.stop()
st.caption(
    f"Đang xem {_model_spec['label']}. Bảng xếp hạng, beeswarm và Local Explanation dùng cùng "
    "model artifact; bộ dữ liệu đầu vào lấy từ Test niêm phong khi file tồn tại."
)


# SUA 2026-08-22: ban cu khop CHUOI CON nen phan nhom sai nhieu cho:
#   sin_elevation -> "Thoi gian" (vi co "sin"), ghi_cs -> "Thoi tiet" (vi co "ghi"),
#   solar_elevation/solar_azimuth roi xuong "Vi tri & Metadata".
# Hau qua: bieu do dong gop theo nhom gan cong cho "Thoi tiet" phan von la thien van
# TAT DINH. Ban duoi phan nhom theo TEN CHINH XAC, xet theo thu tu uu tien.
_NHOM_HINH_HOC = {
    "solar_elevation", "solar_azimuth", "azimuth_sin", "azimuth_cos",
    "sin_elevation", "ghi_cs", "clearsky_proxy", "ky_vong", "ty_le_bao_hoa",
}
_NHOM_LICH = {
    "hour", "hour_of_day", "hour_bucket_model", "hour_sin", "hour_cos",
    "minute", "minute_of_day", "day", "day_of_week", "day_of_year",
    "month", "doy_sin", "doy_cos",
}
_NHOM_TRAM = {
    "site_scale", "tran_cong_suat", "capacity_kw", "number_of_panels",
    "con_cach_tran", "capacity_per_panel",
}


def get_group(name: str) -> str:
    """Phan nhom dac trung de ve dong gop SHAP. Cot _mt cung nhom voi cot goc."""
    goc = name[:-3] if name.endswith("_mt") else name
    if goc.startswith(("lag_", "rolling_")):
        return "Lịch sử & Lag"
    if goc in _NHOM_HINH_HOC:
        return "Hình học Mặt Trời"
    if goc in _NHOM_LICH:
        return "Thời gian & Chu kỳ"
    if goc in _NHOM_TRAM or goc.endswith("_enc"):
        return "Vị trí & Metadata"
    if "_x_" in goc:
        return "Tương tác"
    if any(k in goc for k in ("radiation", "irradiance", "shortwave", "diffuse",
                              "temperature", "cloud", "wind", "precip",
                              "troi_quang", "cs_factor", "sunshine")):
        return "Thời tiết & Bức xạ"
    return "Khác"


# .assign() tao frame moi: df_imp la object dung chung trong cache_resource.
df_imp = df_imp.assign(group=df_imp["feature"].apply(get_group))


_Y_NGHIA_FEATURE = {
    "shortwave_radiation": "bức xạ tổng",
    "direct_normal_irradiance": "bức xạ trực tiếp",
    "diffuse_solar_radiation": "bức xạ tán xạ",
    "diffuse_ratio": "tỷ lệ tán xạ (mức che phủ mây)",
    "temperature_c": "nhiệt độ môi trường",
    "cloud_cover_total": "độ che phủ mây",
    "cloud_cover_low": "mây tầng thấp",
    "wind_speed": "tốc độ gió",
    "sunshine_duration": "số giây nắng",
    "minute_of_day": "thời điểm trong ngày",
    "hour_sin": "chu kỳ giờ trong ngày",
    "hour_cos": "chu kỳ giờ trong ngày",
    "doy_sin": "chu kỳ mùa trong năm",
    "doy_cos": "chu kỳ mùa trong năm",
    "sin_elevation": "độ cao mặt trời",
    "solar_elevation": "độ cao mặt trời",
    "solar_azimuth": "hướng mặt trời",
    "ghi_cs": "bức xạ trời quang lý thuyết",
    "clearsky_proxy": "chỉ số trời quang",
    "ky_vong": "sản lượng kỳ vọng theo công suất",
    "site_scale": "quy mô trạm",
    "tran_cong_suat": "trần công suất trạm",
    "cloud_low": "mây tầng thấp",
    "cloud": "độ che phủ mây",
    "temp": "nhiệt độ",
    "shortwave": "bức xạ tổng",
}


def y_nghia_feature(ten: str) -> str:
    """Dich ten feature sang nghia nghiep vu de dua vao cau nhan dinh."""
    goc = ten[:-3] if ten.endswith("_mt") else ten
    if goc.startswith(("lag_", "rolling_")):
        return "sản lượng đo được trong giờ gần nhất"
    if goc.endswith("_enc") or goc == "site_id_enc":
        return "đặc điểm riêng của trạm"
    if "_x_" in goc:
        a, b = goc.split("_x_", 1)
        return f"tương tác {_Y_NGHIA_FEATURE.get(a, a)} × {_Y_NGHIA_FEATURE.get(b, b)}"
    return _Y_NGHIA_FEATURE.get(goc, goc)

# ── TANG 1: KPI dang the (dong bo voi 2 trang kia, khong dung st.metric mac dinh) ──
# _KPI_XAI la st.empty() (xem 1_ML.py): .container() thay noi dung nguyen khoi moi
# fragment-rerun de KPI khong bi nhan doi.
_top_grp = df_imp.groupby("group")["mean_abs_shap"].sum().idxmax()
with _KPI_XAI.container():
    k1, k2, k3 = st.columns(3)
    with k1:
        kpi("Số đặc trưng", f"{len(df_imp)}", "trong bộ đang chọn")
    with k2:
        kpi("Đặc trưng quan trọng nhất", str(df_imp.iloc[0]["feature"]), f"SHAP {df_imp.iloc[0]['mean_abs_shap']:.4f}")
    with k3:
        kpi("Nhóm đóng góp nhiều nhất", _top_grp, "theo tổng |SHAP|")

# SUA 2026-08-28 (bo cuc): bang "Top dac trung" doi cho — truoc day la khoi full-width
# rieng, gio nam CANH TRAI cung hang voi SHAP Dependence (canh phai), hai khung cung
# chieu cao co dinh de VIEN DUOI thang hang (xem HANG A ben duoi).

# feature_cols dung chung cho ca Local Explanation va SHAP Dependence phia duoi -
# phai dinh nghia TRUOC khi 2 phan do dung toi, tranh loi bien chua duoc gan.
feature_cols = [c for c in df_val.columns if c not in ("site_id", "timestamp", "y_true", "y_pred")]
# cache_key = model_key: doi model moi doc/merge lai; bam widget khac thi lay tu cache ngay.
df_x_real = load_real_feature_values(_model_key, df_val, str(_model_spec["x_test_path"]))

# ── HANG A: bang Top dac trung (TRAI) ‖ SHAP Beeswarm tong (PHAI) ──
# 2026-08-28: bo bieu do LightGBM Gain (trung vai tro voi bang Top dac trung) va bo
# SHAP Dependence ve truc tiep (scatter 483k diem mat ~10s moi dac trung, khong the
# vua du du lieu vua tuc thi). Thay bang anh Beeswarm TONG do stage s10 ve san tren
# toan bo du lieu — hien ngay, dashboard khong tinh toan gi.
# Hai khung cung chieu cao co dinh de vien duoi thang hang (mot ben co caption).
_H_HANG_A = 680
_BEESWARM_PNG = DATA_DIR / "08_explain" / "notebook_shap_beeswarm.png"
rowA_left, rowA_right = st.columns(2, gap="small")

with rowA_left:
    with st.container(border=True, height=_H_HANG_A):
        st.markdown("##### Top đặc trưng quan trọng nhất (Data Bars)")
        top_n = st.slider("Top N đặc trưng", 5, min(40, len(df_imp)), 15)
        df_top = df_imp.head(top_n)[["feature", "mean_abs_shap", "group"]].reset_index(drop=True)
        # Conditional formatting "ong dai ngan" = Data Bars cua Excel/PowerBI: thanh ngang
        # trong o, dai ngan theo gia tri - pandas Styler.bar() lam dung viec nay.
        _styler = (
            df_top.style
            .bar(subset=["mean_abs_shap"], color="#6366F1", vmin=0)
            .format({"mean_abs_shap": "{:.4f}"})
        )
        st.dataframe(_styler, use_container_width=True, hide_index=True, height=480)

with rowA_right:
    with st.container(border=True, height=_H_HANG_A):
        st.markdown("##### SHAP Beeswarm — bức tranh đóng góp tổng (vẽ sẵn từ stage s10)")
        if _BEESWARM_PNG.is_file():
            # width co dinh: anh goc 1171x1099 gan vuong, de use_container_width thi
            # tren man hinh rong anh cao hon khung va sinh scroll trong khung.
            st.image(str(_BEESWARM_PNG), width=540)
            st.caption(
                "Ảnh do stage s10 vẽ trên toàn bộ dữ liệu. Mỗi điểm = 1 dự báo; màu đỏ = giá trị "
                "đặc trưng cao, xanh = thấp; điểm lệch phải đẩy dự báo lên, lệch trái kéo xuống."
            )
        else:
            st.info("Chưa có ảnh 08_explain/notebook_shap_beeswarm.png — chạy stage s10 để sinh.")

# ── HANG B: Local Explanation FULL-WIDTH rieng 1 hang ──


@st.cache_resource
def tim_mau_tieu_bieu(
    cache_key: str, _df_val: pd.DataFrame, _df_x_real: pd.DataFrame,
    feats: tuple[str, ...], base_value: float,
    scale_col: str, elev_col: str, eps: float, tran_col: str,
) -> dict[str, int]:
    """Chon 3 dong tieu bieu (day len / keo xuong / gan baseline) tu toan bo du lieu.

    Du bao quy doi tinh bang DUNG cong thuc cua denormalize_local_prediction (cot
    lay tu model_config.json) de con so chon mau khop voi KPI tren trang.
    Rao chan de mau trinh dien thuyet phuc:
      - ban ngay ro (do cao mat troi > 0.15) va co san luong that (y_true > 1 kWh);
      - k = base_value + tong SHAP > 0.08: tong SHAP am nhat toan cuc luon bi
        clip(k, 0, 1.5) ep du bao ve dung 0 kWh — nhin nhu loi mo hinh;
      - mo hinh du bao SAT thuc te (sai so <= 35%): mau "keo xuong" phai la ca
        mo hinh ha du bao va ha DUNG, khong phai ca du bao truot.
    """
    del cache_key
    tong = _df_val[list(feats)].sum(axis=1)
    ok = pd.Series(True, index=tong.index)
    if elev_col in _df_x_real.columns:
        ok &= _df_x_real[elev_col].reindex(tong.index) > 0.15
    if "y_true" in _df_x_real.columns:
        ok &= _df_x_real["y_true"].reindex(tong.index) > 1.0
    k = base_value + tong
    ok &= k > 0.08
    if {"y_true", elev_col, scale_col}.issubset(_df_x_real.columns):
        y_pred = (
            k.clip(0.0, 1.5)
            * _df_x_real[scale_col].reindex(tong.index)
            * _df_x_real[elev_col].reindex(tong.index).clip(lower=eps)
        )
        if tran_col in _df_x_real.columns:
            y_pred = y_pred.clip(upper=_df_x_real[tran_col].reindex(tong.index) * 1.02)
        y_true = _df_x_real["y_true"].reindex(tong.index)
        ok &= (y_pred - y_true).abs() <= 0.35 * y_true
    t = tong[ok.fillna(False)]
    if t.empty:
        t = tong
    return {
        "len": int(t.idxmax()),
        "xuong": int(t.idxmin()),
        "baseline": int(t.abs().idxmin()),
    }


# Ngoai le duy nhat voi quy tac "2 bieu do/hang": shap.plots.force can toan bo chieu
# rong trang de hien chu khong de (nhu trong repo tham khao, chart nay luon chiem
# het do rong o moi vi du). Nhet vao cot nua trang lam chu chong len nhau khong doc
# duoc du da gioi han con 12 -> 6 feature, da thu va van khong du cho.
if True:
    # LOCAL EXPLANATION - giai thich cho 1 DU BAO CU THE (khac Hang A, deu la GLOBAL).
    # Tham khao cau truc tu github.com/nguyenhads/sales_forecasting_xai
    # (docs/shap_analysis_summary_report.md, muc "Local Explanation Examples").
    if not df_x_real.empty:
        # st.markdown('<div>') KHONG bao duoc cac widget st.* goi sau do (moi widget la 1
        # component rieng, khong nam trong div) -> tao khung mau rong vo nghia. Dung
        # st.container(border=True) chuan cua Streamlit thay vi tu ve div mau.
        _force_box = st.container(border=True)
        _force_box.markdown("##### Local Explanation — 1 dự báo cụ thể")
        _opt_df = df_val[["site_id", "timestamp"]].copy()
        _opt_df["timestamp"] = pd.to_datetime(_opt_df["timestamp"])
        _cfg_mau = json.loads(
            Path(str(_model_spec["config_path"])).read_text(encoding="utf-8")
        )
        _mau = tim_mau_tieu_bieu(
            _model_key, df_val, df_x_real, tuple(feature_cols),
            load_shap_base_value(str(_model_spec["model_path"])),
            _cfg_mau.get("cot_quy_mo", "site_scale"),
            _cfg_mau.get("cot_sin_elev", "sin_elevation"),
            float(_cfg_mau.get("eps_elev", 0.05)),
            _cfg_mau.get("cot_tran", "tran_cong_suat"),
        )
        _ten_mau = {
            "len": "Mẫu đẩy dự báo lên",
            "xuong": "Mẫu kéo dự báo xuống",
            "baseline": "Mẫu gần baseline",
        }
        _tu_chon = "Tự chọn site + timestamp"
        _options = [
            f"{_ten_mau[k]} — trạm {_opt_df.loc[i, 'site_id']} · {_opt_df.loc[i, 'timestamp']}"
            for k, i in _mau.items()
        ] + [_tu_chon]
        _local_choice = _force_box.selectbox("Chọn dự báo cần giải thích", _options)
        if _local_choice == _tu_chon:
            # Chon 3 cap thay vi 1 selectbox 483k lua chon: van toi duoc moi dong,
            # nhung moi hop chi vai chuc muc.
            _c_tram, _c_ngay, _c_gio = _force_box.columns(3)
            _sites_local = sorted(_opt_df["site_id"].unique().tolist())
            _site_pick = _c_tram.selectbox("Trạm", _sites_local, key="local_site")
            _sub_site = _opt_df[_opt_df["site_id"] == _site_pick]
            _days_local = sorted(_sub_site["timestamp"].dt.date.unique().tolist())
            _day_pick = _c_ngay.selectbox("Ngày", _days_local, key="local_day")
            _sub_day = _sub_site[_sub_site["timestamp"].dt.date == _day_pick]
            _times_local = sorted(_sub_day["timestamp"].dt.time.unique().tolist())
            _time_pick = _c_gio.selectbox(
                "Giờ", _times_local,
                format_func=lambda t: t.strftime("%H:%M"), key="local_time",
            )
            _row_idx = _sub_day[_sub_day["timestamp"].dt.time == _time_pick].index[0]
            _loai_mau = "tu_chon"
        else:
            _loai_mau = list(_mau)[_options.index(_local_choice)]
            _row_idx = _mau[_loai_mau]
        _shap_row = df_val.loc[_row_idx, feature_cols].astype(float)
        _real_row = df_x_real.loc[_row_idx] if _row_idx in df_x_real.index else None
        _base_value = load_shap_base_value(str(_model_spec["model_path"]))
        _shap_total = float(_shap_row.sum())
        _predicted_kwh = denormalize_local_prediction(
            _base_value,
            _shap_total,
            _real_row,
            str(_model_spec["config_path"]),
        )

        _cL, _cM, _cR = _force_box.columns(3)
        with _cL:
            _thuc_te = _real_row["y_true"] if _real_row is not None and "y_true" in _real_row else None
            kpi("Thực tế", f"{_thuc_te:.2f} kWh" if _thuc_te is not None else "n/a", "")
        with _cM:
            kpi("Dự báo quy đổi", f"{_predicted_kwh:.2f} kWh" if _predicted_kwh is not None else "n/a", "từ đầu ra k")
        with _cR:
            kpi("Tổng đóng góp SHAP", f"{_shap_total:+.4f}", "đầu ra chuẩn hóa k")

        # Ve DUNG bang thu vien shap that (shap.plots.force, matplotlib=True) - giong
        # y het anh trong repo tham khao (nguyenhads/sales_forecasting_xai, notebook 05,
        # cell 31): 1 thanh lien tuc dang phieu, mui ten hong (tang) va xanh duong (giam)
        # hop lai o f(x). KHONG tu ve lai bang Plotly (go.Waterfall truoc day la thanh
        # roi rac, sai kieu dang - da bi phat hien va yeu cau sua).
        # Dùng expected_value thật của TreeExplainer, không lấy trung bình tổng SHAP.
        # reindex thay vi .loc[row, feature_cols] truc tiep: model moi train co the co
        # feature (vd optimizers_enc, longitude) khong ton tai trong X_test_h1.parquet cu
        # (sinh tu lan train truoc) -> KeyError. reindex tao cot thieu = NaN roi fillna 0.
        _real_vals = (df_x_real.loc[_row_idx].reindex(feature_cols).fillna(0.0) if _row_idx in df_x_real.index
                      else pd.Series(0.0, index=feature_cols))
        # Chi giu TOP 6 feature |shap| lon nhat: full-width van khong du cho 12 nhan
        # chu khong chong nhau (da thu 12, van don cuc). Phan con lai gop vao base
        # value de f(x) (tong cuoi) van dung, khong mat thong tin tong the.
        _top_idx = _shap_row.abs().sort_values(ascending=False).head(6).index
        _rest_sum = float(_shap_row.drop(_top_idx).sum())
        _shap_top = _shap_row.loc[_top_idx]
        _real_top = _real_vals.loc[_top_idx]
        plt.close("all")
        shap.plots.force(
            _base_value + _rest_sum, _shap_top.to_numpy(), _real_top,
            matplotlib=True, show=False, figsize=(22, 3.4), text_rotation=18,
        )
        _fig_force = plt.gcf()
        _force_box.pyplot(_fig_force, use_container_width=True)
        plt.close(_fig_force)
        # Insight: Boi canh / Co che / Nhan dinh. Moi dong gop deu quy doi ra kWh theo
        # dung cong thuc pipeline (cot lay tu model_config.json — v5 dung
        # sin_elevation_mt, KHONG phai sin_elevation) va kem cau "vi sao" theo co che
        # vat ly/nghiep vu cua dac trung do.
        _cfg_ins = json.loads(
            Path(str(_model_spec["config_path"])).read_text(encoding="utf-8")
        )
        _scale_col_ins = _cfg_ins.get("cot_quy_mo", "site_scale")
        _elev_col_ins = _cfg_ins.get("cot_sin_elev", "sin_elevation")
        _eps_ins = float(_cfg_ins.get("eps_elev", 0.05))

        def _tri_dong(*ten: str) -> float | None:
            """Doc gia tri tu dong X_test DAY DU (_real_row co ca cot ngoai feature)."""
            if _real_row is None:
                return None
            for _t in ten:
                if _t in _real_row.index and pd.notna(_real_row[_t]):
                    return float(_real_row[_t])
            return None

        _scale_ins = _tri_dong(_scale_col_ins, "site_scale")
        _elev_ins = _tri_dong(_elev_col_ins, "sin_elevation")
        # ky_vong = quy mo x do cao mat troi — phuong an du phong de khong bao gio ra n/a.
        _he_so_kwh = (
            _scale_ins * max(_elev_ins, _eps_ins)
            if _scale_ins is not None and _elev_ins is not None
            else _tri_dong("ky_vong")
        )
        _tong_abs = float(_shap_row.abs().sum()) or 1.0
        _top3_ins = _shap_row.abs().sort_values(ascending=False).head(3).index

        def _kwh_cua(f: str) -> float | None:
            return float(_shap_row[f]) * _he_so_kwh if _he_so_kwh is not None else None

        def _phan_tram(f: str) -> float:
            return abs(float(_shap_row[f])) / _tong_abs * 100

        def _chuoi_luong(f: str) -> str:
            _k = _kwh_cua(f)
            return f"{_k:+.2f} kWh" if _k is not None else f"{float(_shap_row[f]):+.3f} điểm k"

        def _ly_do_dong_gop(f: str) -> str:
            """Cau 'vi sao' theo co che vat ly/nghiep vu cua tung ho dac trung."""
            goc = f[:-3] if f.endswith("_mt") else f
            len_ = float(_shap_row[f]) > 0
            v = _tri_dong(f)
            if goc.startswith(("lag_", "rolling_")):
                return ("một giờ vừa qua trạm đang phát tốt — quán tính sản lượng cho thấy "
                        "trời đang thuận lợi nên mô hình tự tin nâng dự báo" if len_ else
                        "một giờ vừa qua trạm phát thấp — quán tính sản lượng cho thấy trời "
                        "đang xấu, mô hình dè chừng hạ theo")
            if goc == "direct_normal_irradiance":
                if v is not None and v <= 5:
                    return ("không còn tia nắng nào chiếu trực tiếp tới tấm pin (mặt trời bị "
                            "mây che hoàn toàn) — nguồn năng lượng đầu vào chính mất hẳn")
                return ("nắng chiếu trực tiếp mạnh — nguồn năng lượng chính của tấm pin đang "
                        "dồi dào" if len_ else
                        "nắng trực tiếp yếu hơn mức thường thấy của khung giờ này")
            if goc == "diffuse_ratio":
                if v is not None and v >= 0.8:
                    return ("gần như toàn bộ ánh sáng là tán xạ — trời phủ mây kín, tấm pin "
                            "chỉ nhận được ánh sáng khuếch tán yếu")
                if v is not None and v <= 0.3:
                    return "tỷ lệ tán xạ thấp — trời quang, nắng trực tiếp chiếm ưu thế"
                return "mây rải rác — ánh sáng pha trộn giữa trực tiếp và khuếch tán"
            if goc == "shortwave_radiation":
                return ("tổng bức xạ tới bề mặt đang cao — nhiên liệu đầu vào của cả hệ "
                        "thống dồi dào" if len_ else
                        "tổng bức xạ tới bề mặt thấp — nhiên liệu đầu vào của hệ thống thiếu hụt")
            if "cloud" in goc and "_x_" in goc:
                return ("bức xạ có nhưng mây tầng thấp dày chặn bớt phần thực sự tới được "
                        "tấm pin" if not len_ else
                        "mây tầng thấp mỏng nên phần bức xạ tới được tấm pin gần như trọn vẹn")
            if goc == "temperature_c" or ("temp" in goc and "_x_" in goc):
                return ("nhiệt độ cao làm cell pin nóng lên, suy hao hiệu suất ~0,38%/°C "
                        "vượt 25°C" if not len_ else
                        "nhiệt độ mát giúp cell pin giữ hiệu suất chuyển đổi tốt")
            if goc == "ky_vong":
                return ("mốc sản lượng kỳ vọng theo công suất của giờ này cao và điều kiện "
                        "thực đang bám sát mốc" if len_ else
                        "mốc kỳ vọng theo công suất của giờ này cao nhưng điều kiện thực tế "
                        "không đạt nổi, mô hình phải trừ sâu so với mức nền")
            if goc in ("minute_of_day", "hour_sin", "hour_cos", "hour", "hour_of_day"):
                return ("thời điểm đang ở pha thuận lợi của chu kỳ nhật động trong ngày"
                        if len_ else
                        "thời điểm chưa tới hoặc đã qua pha phát cao của chu kỳ nhật động")
            if goc.endswith("_enc") or goc in ("site_scale", "tran_cong_suat"):
                return ("đặc điểm riêng của trạm (hướng lắp, hiệu suất lịch sử) mà mô hình "
                        "học được từ dữ liệu vận hành")
            if goc in ("sin_elevation", "solar_elevation"):
                return ("mặt trời đang lên cao, góc chiếu thuận lợi" if len_ else
                        "mặt trời còn thấp, góc chiếu xiên làm giảm năng lượng nhận được")
            return ("giá trị đang ở vùng thuận lợi so với quy luật mô hình học được"
                    if len_ else
                    "giá trị đang ở vùng bất lợi so với quy luật mô hình học được")

        _co_che = []
        for _f in _top3_ins:
            _v = _real_vals.get(_f)
            _gia_tri = f"{_v:,.3g}" if pd.notna(_v) else "?"
            _co_che.append(
                f"- `{_f}` = {_gia_tri} → **{_chuoi_luong(_f)}** ({_phan_tram(_f):.0f}% "
                f"tổng tác động): {_ly_do_dong_gop(_f)}."
            )

        # Tong luc day / keo tren TOAN BO dac trung, va do lech du bao vs thuc te.
        _tong_len_kwh = (float(_shap_row[_shap_row > 0].sum()) * _he_so_kwh
                         if _he_so_kwh is not None else None)
        _tong_xuong_kwh = (float(_shap_row[_shap_row < 0].sum()) * _he_so_kwh
                           if _he_so_kwh is not None else None)
        _s_len = f"{_tong_len_kwh:+.2f} kWh" if _tong_len_kwh is not None else "không đáng kể"
        _s_xuong = f"{_tong_xuong_kwh:+.2f} kWh" if _tong_xuong_kwh is not None else "không đáng kể"
        # Muc nen = du bao "dieu kien trung binh" cua khung gio nay (base value x he so
        # quy doi) — de nguoi doc hieu luc day/keo dang so voi cai gi.
        _s_nen = (f"mức nền ~{_base_value * _he_so_kwh:.1f} kWh của khung giờ này"
                  if _he_so_kwh is not None else "mức nền của khung giờ này")
        _lech_txt = ""
        if _thuc_te is not None and _predicted_kwh is not None and _thuc_te > 0:
            _lech = abs(_predicted_kwh - _thuc_te)
            _lech_txt = (f"Dự báo lệch thực tế chỉ {_lech:.2f} kWh "
                         f"(~{_lech / _thuc_te * 100:.0f}%). ")

        _bx = _tri_dong("shortwave_radiation", "shortwave_radiation_mt")
        _tan_xa = _tri_dong("diffuse_ratio", "diffuse_ratio_mt")
        _nhiet = _tri_dong("temperature_c", "temperature_c_mt")
        _phan_troi = []
        if _bx is not None:
            _muc_bx = "mạnh" if _bx >= 500 else ("trung bình" if _bx >= 200 else "yếu")
            _phan_troi.append(f"bức xạ tổng ~{_bx:,.0f} W/m² ({_muc_bx})")
        if _tan_xa is not None:
            _muc_may = ("trời nhiều mây" if _tan_xa > 0.6
                        else "mây rải rác" if _tan_xa > 0.3 else "trời quang")
            _phan_troi.append(f"tỷ lệ tán xạ {_tan_xa:.2f} → {_muc_may}")
        if _nhiet is not None:
            _phan_troi.append(f"nhiệt độ {_nhiet:.0f}°C")
        _thoi_tiet = ("Trời lúc này: " + "; ".join(_phan_troi) + ". ") if _phan_troi else ""

        _nhan_dinh = {
            "len": f"{_thoi_tiet}Tổng lực đẩy {_s_len} so với mức nền, áp đảo lực kéo "
                   f"({_s_xuong}). {_lech_txt}Chính kiến: đây là giờ phát đỉnh thật do thời "
                   "tiết, không phải nhiễu đo đếm — dồn phụ tải tiêu thụ tại chỗ (điều hòa, "
                   "bơm, trạm sạc) vào đúng khung giờ này để tăng tự tiêu thụ, giảm mua điện "
                   "lưới.",
            "xuong": f"{_thoi_tiet}Tổng lực kéo {_s_xuong} so với mức nền, áp đảo lực đẩy "
                     f"({_s_len}). {_lech_txt}Chính kiến: mức hụt là thật và đến từ thời "
                     "tiết, không phải suy giảm thiết bị — chưa cần lệnh bảo trì; chỉ kích "
                     "hoạt kiểm tra inverter/cảm biến (CBM) nếu thực đo tụt sâu dưới cả mức "
                     "dự báo đã hạ.",
            "baseline": f"{_thoi_tiet}Lực đẩy {_s_len} và lực kéo {_s_xuong} gần như triệt "
                        f"tiêu nhau. {_lech_txt}Chính kiến: giờ vận hành chuẩn mực, chiếm đa "
                        "số thời gian phát điện — lấy nhóm giờ này làm mốc cam kết chỉ tiêu "
                        "sản lượng tháng/quý và làm cửa sổ xếp lịch bảo trì ít ảnh hưởng "
                        "doanh thu nhất.",
            "tu_chon": f"{_thoi_tiet}Lực đẩy {_s_len}, lực kéo {_s_xuong}. {_lech_txt}Chính "
                       "kiến: đối chiếu từng dòng cơ chế ở trên với điều kiện trời quan sát "
                       "được — nếu hai bên mâu thuẫn (trời quang nhưng quán tính sản lượng "
                       "vẫn kéo sâu), ưu tiên kiểm tra dữ liệu và thiết bị của trạm trước "
                       "khi nghi ngờ mô hình.",
        }[_loai_mau]
        _ts_row = _opt_df.loc[_row_idx]
        # Expander so xuong TAI CHO (popover bi mo nguoc len tren, che mat force plot).
        with _force_box.expander("Cơ chế & nhận định", expanded=False):
            st.markdown(
                f"**Bối cảnh.** Trạm {_ts_row['site_id']}, thời điểm {_ts_row['timestamp']}: thực tế "
                f"{f'{_thuc_te:.2f} kWh' if _thuc_te is not None else '—'}, mô hình dự báo "
                f"{f'{_predicted_kwh:.2f} kWh' if _predicted_kwh is not None else '—'}.\n\n"
                f"**Cơ chế — vì sao từng yếu tố đóng góp như vậy:**\n" + "\n".join(_co_che)
                + f"\n\n**Nhận định.** {_nhan_dinh}"
            )

            # Cau noi sang trang What-If: doc so lieu hang muc TRUC TIEP tu config
            # cua nhanh BI (chi doc, khong sua) de hai trang luon khop so.
            try:
                from api.bimart.core.config import HANG_MUC_CAI_TIEN as _HM_BI
            except Exception:
                _HM_BI = {}

            def _ten_hm(ma: str) -> str:
                _h = _HM_BI[ma]
                return (f"hạng mục {_h['stt']} \"{_h['ten']}\" ({_h['hieu_suat']}, "
                        f"hoàn vốn {_h['payback']})")

            _goc_am = [
                (f[:-3] if f.endswith("_mt") else f)
                for f in _top3_ins if float(_shap_row[f]) < 0
            ]
            _cau_bi = []
            if any("temp" in g for g in _goc_am) and "ventilation" in _HM_BI:
                _cau_bi.append(
                    f"suy hao nhiệt đang kéo dự báo xuống → khớp {_ten_hm('ventilation')}"
                )
            if (any(g.startswith(("lag_", "rolling_")) for g in _goc_am)
                    and _tan_xa is not None and _tan_xa <= 0.3 and "cbm" in _HM_BI):
                _cau_bi.append(
                    "trời quang nhưng quán tính sản lượng vẫn kéo xuống — nghi thiết bị, "
                    f"đúng bài toán của {_ten_hm('cbm')}"
                )
            if any(("cloud" in g) or g in
                   ("diffuse_ratio", "direct_normal_irradiance", "shortwave_radiation")
                   for g in _goc_am):
                _cau_bi.append(
                    "phần hụt do mây/bức xạ là tổn thất thời tiết, không cải tạo phần cứng "
                    "được — giá trị của dự báo nằm ở điều phối phụ tải, đúng vai trò mô "
                    "phỏng của trang What-If"
                )
            if _loai_mau == "len" and "bess" in _HM_BI:
                _cau_bi.append(
                    "giờ phát đỉnh là lúc dễ chạm trần công suất (tổn thất cắt ngọn) → "
                    f"liên hệ {_ten_hm('bess')}"
                )
            if _cau_bi:
                st.markdown("**Gắn với What-If (BI).** " + "; ".join(_cau_bi) + ".")
