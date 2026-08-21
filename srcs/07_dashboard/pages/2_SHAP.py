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
import plotly.express as px
import plotly.graph_objects as go
import shap
import streamlit as st

from dashboard_common import header_bao_cao, load_shared_css, nap_runtime_cpp

# Trang nay import shap va doc model LightGBM nen can runtime C++ tren NixOS.
# Goi lai o day (khong chi dua vao app.py) de trang van chay duoc khi mo truc tiep
# bang `streamlit run pages/2_SHAP.py`. CDLL nap lai cung tep la thao tac vo hai.
nap_runtime_cpp()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VERSION = os.environ.get("DASHBOARD_VERSION", "v5")
DATA_DIR = PROJECT_ROOT / "data" / "model" / VERSION

st.set_page_config(page_title="Model Explainability (XAI)", page_icon="🔬", layout="wide")
load_shared_css()
# Rieng trang SHAP: kpi-value nho hon mac dinh (nhieu KPI hon tren 1 hang).
st.markdown("<style>.kpi-value { font-size: 1.15rem !important; }</style>", unsafe_allow_html=True)


def kpi(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
<div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>""",
        unsafe_allow_html=True,
    )

header_bao_cao(
    "Mô hình học được gì? — phân tích SHAP",
    "Đóng góp của từng đặc trưng tới dự báo sản lượng quang điện.",
    nhan_phai="GIẢI THÍCH MÔ HÌNH",
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
            local_cases_path = explain_dir / "local_shap_cases.parquet" if key == persisted_explain_key else None
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
                "local_cases_path": local_cases_path,
            }
    return specs


MODEL_SPECS = _build_model_specs()
SITE_METADATA_PATH = DATA_DIR / "02_split" / "test" / f"{VERSION}_test.parquet"


def _unwrap_model(bundle):
    return bundle.get("model", bundle) if isinstance(bundle, dict) else bundle


@st.cache_data
def load_native_importance(model_path: str, config_path: str) -> pd.DataFrame:
    """LightGBM co san feature_importances_ - tinh theo GAIN trung binh qua TAT CA
    cay trong ensemble (khac SHAP: SHAP la dong gop tung du bao, cai nay la mo hinh
    hoc duoc gi noi chung). Doc thang tu model that, khong tu suy dien."""
    model_file = Path(model_path)
    if not model_file.exists():
        return pd.DataFrame()
    with open(model_file, "rb") as f:
        bundle = pickle.load(f)
    model = _unwrap_model(bundle)
    feats = bundle.get("features") if isinstance(bundle, dict) else None
    if not feats:
        feats = json.loads(Path(config_path).read_text(encoding="utf-8"))["features"]
    model.set_params(importance_type="gain")
    gain = model.booster_.feature_importance(importance_type="gain")
    split = model.booster_.feature_importance(importance_type="split")
    return pd.DataFrame({"feature": feats, "gain": gain, "split": split}).sort_values("gain", ascending=False)


@st.cache_data
def load_real_feature_values(feat_val_keys: pd.DataFrame, x_test_path: str) -> pd.DataFrame:
    """shap_values.parquet CHI chua gia tri SHAP (bien do nho +-0.01..0.09), KHONG
    chua gia tri dac trung goc (vd shortwave_radiation phai la 0-1100 W/m2 that,
    khong phai +-0.06). Phai join voi X_test_h1.parquet (co gia tri that) qua
    site_id+timestamp de lay dung du lieu cho PDP/scatter, khong dung nham SHAP
    lam gia tri dac trung nhu ban dau."""
    x_test_file = Path(x_test_path)
    if not x_test_file.exists() or feat_val_keys.empty:
        return pd.DataFrame()
    x_real = pd.read_parquet(x_test_file)
    keys = feat_val_keys[["site_id", "timestamp"]].copy()
    keys["timestamp"] = pd.to_datetime(keys["timestamp"])
    x_real["timestamp"] = pd.to_datetime(x_real["timestamp"])
    return keys.merge(x_real, on=["site_id", "timestamp"], how="left")


@st.cache_resource
def load_what_if_model(model_path: str, config_path: str):
    with open(model_path, "rb") as fh:
        model = _unwrap_model(pickle.load(fh))
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    return model, config


@st.cache_data
def load_what_if_data(x_test_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Doc feature dung luc inference va metadata goc cua tung site."""
    features = pd.read_parquet(x_test_path)
    features["timestamp"] = pd.to_datetime(features["timestamp"])
    metadata = pd.read_parquet(
        SITE_METADATA_PATH, columns=["site_id", "number_of_panels", "capacity_kw"]
    )
    metadata = metadata.groupby("site_id", as_index=False).first()
    return features, metadata


def predict_what_if(row: pd.Series, model, config: dict, panel_ratio: float) -> tuple[float, float]:
    """Predict baseline va kich ban quy mo; khong dich timestamp hay sua weather."""
    feature_names = list(config["features"])
    medians = pd.Series(config.get("feature_medians", {}), dtype="float64")

    baseline = row.reindex(feature_names).fillna(medians).astype(np.float32)
    scenario = baseline.copy()
    scale_features = [
        name for name in feature_names
        if name.startswith(("lag_", "rolling_")) or name in {"ky_vong", "ky_vong_mt", "tran_cong_suat"}
    ]
    scenario.loc[scale_features] = scenario.loc[scale_features] * panel_ratio

    raw_base = float(model.predict(baseline.to_frame().T)[0])
    raw_scenario = float(model.predict(scenario.to_frame().T)[0])
    eps = float(config.get("eps_elev", 0.05))
    sin_elevation = max(float(row[config["cot_sin_elev"]]), eps)
    site_scale = float(row["site_scale"])
    cap_base = float(row[config["cot_tran"]])

    base_kwh = np.clip(raw_base, 0.0, 1.5) * site_scale * sin_elevation
    scenario_kwh = np.clip(raw_scenario, 0.0, 1.5) * site_scale * panel_ratio * sin_elevation
    base_kwh = min(base_kwh, cap_base * 1.02)
    scenario_kwh = min(scenario_kwh, cap_base * panel_ratio * 1.02)
    if float(row[config["cot_sin_elev"]]) <= eps:
        return 0.0, 0.0
    return float(base_kwh), float(scenario_kwh)


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


@st.cache_data
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
def load_local_cases(local_cases_path: str | None) -> pd.DataFrame:
    """Load the three local examples selected by notebook 08 for the winning model."""
    if not local_cases_path:
        return pd.DataFrame()
    path = Path(local_cases_path)
    if not path.is_file():
        return pd.DataFrame()
    cases = pd.read_parquet(path)
    if "timestamp" in cases.columns:
        cases["timestamp"] = pd.to_datetime(cases["timestamp"])
    return cases


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


with st.sidebar:
    st.markdown("### Bộ lọc XAI")
    if not MODEL_SPECS:
        st.error(f"Không tìm thấy model artifact trong data/model/{VERSION}/06_train.")
        st.stop()
    _model_keys = list(MODEL_SPECS)
    _default_key = "mae_h1" if "mae_h1" in MODEL_SPECS else _model_keys[0]
    _model_key = st.selectbox(
        "Mô hình / horizon",
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
_local_cases = load_local_cases(
    str(_model_spec["local_cases_path"]) if _model_spec["local_cases_path"] else None
)
if df_imp.empty:
    st.warning(f"Chưa có dữ liệu SHAP cho {_model_spec['label']} và không thể tính từ artifact hiện có.")
    st.stop()
st.caption(
    f"Đang xem {_model_spec['label']}. Gain, SHAP cục bộ và What-if dùng cùng model artifact; "
    "bộ dữ liệu đầu vào lấy từ Test niêm phong khi file tồn tại."
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


df_imp["group"] = df_imp["feature"].apply(get_group)

# ── TANG 1: KPI dang the (dong bo voi 2 trang kia, khong dung st.metric mac dinh) ──
_top_grp = df_imp.groupby("group")["mean_abs_shap"].sum().idxmax()
k1, k2, k3 = st.columns(3)
with k1:
    kpi("Số đặc trưng", f"{len(df_imp)}", "trong bộ đang chọn")
with k2:
    kpi("Đặc trưng quan trọng nhất", str(df_imp.iloc[0]["feature"]), f"SHAP {df_imp.iloc[0]['mean_abs_shap']:.4f}")
with k3:
    kpi("Nhóm đóng góp nhiều nhất", _top_grp, "theo tổng |SHAP|")

# ── TANG 2: 2 bieu do chinh trong container(border=True), gap="small" ──
t2_left, t2_right = st.columns(2, gap="small")
with t2_left:
    with st.container(border=True):
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
        st.dataframe(_styler, use_container_width=True, hide_index=True, height=300)
with t2_right:
    with st.container(border=True):
        st.markdown("##### Tỉ trọng đóng góp theo nhóm đặc trưng")
        grp_df = df_imp.groupby("group", as_index=False)["mean_abs_shap"].sum().sort_values("mean_abs_shap", ascending=False)
        fig_pie = px.pie(
            grp_df, values="mean_abs_shap", names="group", hole=0.45,
            color_discrete_sequence=["#6366F1", "#D9822B", "#38BDF8", "#94A3B8"],
        )
        fig_pie.update_layout(
            template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
            height=300, font=dict(color="#1F2937", size=12),
            legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# feature_cols dung chung cho ca Local Explanation va SHAP Dependence phia duoi -
# phai dinh nghia TRUOC khi 2 phan do dung toi, tranh loi bien chua duoc gan.
feature_cols = [c for c in df_val.columns if c not in ("site_id", "timestamp", "y_true", "y_pred")]
df_x_real = load_real_feature_values(df_val, str(_model_spec["x_test_path"]))

# ── HANG A: 2 bieu do GLOBAL canh nhau - LightGBM Gain (trai) | PDP phi tuyen (phai) ──
rowA_left, rowA_right = st.columns(2, gap="small")

df_native = load_native_importance(str(_model_spec["model_path"]), str(_model_spec["config_path"]))
with rowA_left:
    if not df_native.empty:
        with st.container(border=True):
            st.markdown("##### LightGBM Feature Importance (Gain trung bình qua toàn bộ cây)")
            _top_native = df_native.head(15)
            fig_native = px.bar(
                _top_native.sort_values("gain"), x="gain", y="feature", orientation="h",
                color="gain", color_continuous_scale="Blues",
                labels={"gain": "Gain trung bình"},
            )
            fig_native.update_layout(
                template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                height=340, font=dict(color="#1F2937", size=12),
            )
            st.plotly_chart(fig_native, use_container_width=True)
            st.caption(
                "Gain = tổng mức giảm loss mỗi khi đặc trưng được dùng để chia nhánh, cộng dồn và lấy trung bình "
                "qua tất cả cây. Khác SHAP (đóng góp từng dự báo cụ thể) — đây là mức 'hữu ích' ở cấp cấu trúc cây."
            )

with rowA_right:
    # SHAP Dependence Plot - dung DUNG shap.plots.scatter() cua thu vien shap that, giong
    # y het cell 28 trong repo tham khao (nguyenhads/sales_forecasting_xai, notebook 05):
    #   shap.plots.scatter(shap_values_valid[:, feature_name], color=shap_values_valid[:, feature_name])
    # Truoc day o day la Partial Dependence Plot (sklearn.inspection) - da doi theo yeu cau
    # "cái này chuyển thành shap dependence plot của đúng shap đi". Mau sac tu dong theo
    # tuong tac voi feature manh nhat (shap tu chon), khac PDP la khong the hien duoc.
    if not df_val.empty and not df_x_real.empty:
        _feats_shp = [c for c in feature_cols if c in df_x_real.columns]
        if _feats_shp:
            with st.container(border=True):
                st.markdown("##### SHAP Dependence Plot — tính phi tuyến (shap.plots.scatter)")
                _feat_shp = st.selectbox("Chọn đặc trưng xem tính phi tuyến", _feats_shp,
                                          index=_feats_shp.index("shortwave_radiation") if "shortwave_radiation" in _feats_shp else 0,
                                          key="shap_scatter_feat")
                _common_idx = df_val.index.intersection(df_x_real.index)
                _expl = shap.Explanation(
                    values=df_val.loc[_common_idx, _feats_shp].to_numpy(dtype=float),
                    data=df_x_real.loc[_common_idx, _feats_shp].to_numpy(dtype=float),
                    feature_names=_feats_shp,
                )
                plt.close("all")
                shap.plots.scatter(_expl[:, _feat_shp], color=_expl[:, _feat_shp], show=False)
                _fig_shp = plt.gcf()
                _fig_shp.set_size_inches(9, 4.5)
                st.pyplot(_fig_shp, use_container_width=True)
                plt.close(_fig_shp)
                st.caption(
                    "Mỗi điểm = 1 dự báo thật. Trục X = giá trị đặc trưng thật, trục Y = mức SHAP đẩy dự báo "
                    "lên/xuống. Màu tự động theo đặc trưng tương tác mạnh nhất do SHAP tự chọn."
                )

# ── HANG B: Local Explanation FULL-WIDTH rieng 1 hang ──


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
        _opt_df["nhan"] = _opt_df["site_id"].astype(str) + " · " + _opt_df["timestamp"].astype(str)
        _local_choice = "Tự chọn site + timestamp"
        if not _local_cases.empty and {"site_id", "timestamp", "case_label"}.issubset(_local_cases.columns):
            _case_names = {
                "upward_contribution": "Mẫu đẩy dự báo lên",
                "downward_contribution": "Mẫu kéo dự báo xuống",
                "near_baseline": "Mẫu gần baseline",
            }
            _local_cases["nhan"] = (
                _local_cases["site_id"].astype(str)
                + " · "
                + _local_cases["timestamp"].astype(str)
            )
            _local_cases["hien_thi"] = _local_cases["case_label"].map(_case_names).fillna(
                _local_cases["case_label"].astype(str)
            )
            _local_options = [
                f"{row.hien_thi} — {row.nhan}" for row in _local_cases.itertuples()
            ]
            _local_choice = _force_box.selectbox(
                "Mẫu local từ notebook 08",
                [_local_choice, *_local_options],
            )
        if _local_choice == "Tự chọn site + timestamp":
            _pick = _force_box.selectbox("Chọn 1 dòng để giải thích", _opt_df["nhan"].tolist())
        else:
            _selected_local = _local_cases.iloc[_local_options.index(_local_choice)]
            _pick = _selected_local["nhan"]
            _force_box.caption("Đang hiển thị mẫu local đã chọn trong notebook 08.")
        _row_idx = _opt_df[_opt_df["nhan"] == _pick].index[0]
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
        _force_box.caption(
            "Đỏ = kéo dự báo LÊN so với mức trung bình (base value), xanh navy = kéo XUỐNG. "
            "Force Plot giữ ở thang đầu ra chuẩn hóa k để bảo toàn tính cộng SHAP; KPI Dự báo quy đổi "
            "đã nhân ngược site_scale × sin_elevation và chặn theo trần công suất. "
            "Base value lấy trực tiếp từ TreeExplainer của mô hình đang chọn. "
            "Cộng dồn từ base value ra tới f(x) — giống shap.force_plot()/shap.plots.waterfall(). "
            "Chỉ hiện 6 đặc trưng ảnh hưởng mạnh nhất, phần còn lại đã gộp vào base value."
        )


# ── WHAT-IF: dat trong trang XAI de lien ket "model hoc gi" voi tac dong kinh doanh. ──
st.markdown("<br>", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown("##### What-if Analysis — thay đổi quy mô hệ thống")
    st.caption(
        f"Giữ nguyên thời tiết và thời điểm, thay đổi số lượng tấm pin để mô phỏng sản lượng "
        f"{str(_model_spec['horizon']).upper()}. Kịch bản chạy lại {_model_spec['label']} đang chọn, "
        "không nhân trực tiếp kết quả sau dự báo."
    )

    if not (
        Path(_model_spec["model_path"]).exists()
        and Path(_model_spec["config_path"]).exists()
        and Path(_model_spec["x_test_path"]).exists()
    ):
        st.warning(f"Thiếu artifact của {_model_spec['label']} để chạy What-if Analysis.")
    else:
        _what_if_features, _site_metadata = load_what_if_data(str(_model_spec["x_test_path"]))
        _what_if_model, _what_if_config = load_what_if_model(
            str(_model_spec["model_path"]), str(_model_spec["config_path"])
        )
        # Kich ban What-if nhan theo SO TAM PIN nen chi chay duoc o tram co metadata cong
        # suat. Tu ban trich v5, capacity_kw / number_of_panels khong con duoc dien bia:
        # 17/42 tram giu nguyen khuyet (xem muc 6.1.1 bao cao), nen phai loc truoc khi
        # dua vao o chon - neu khong int(NaN) se nem TypeError va sap ca trang.
        _meta_du = _site_metadata.dropna(subset=["number_of_panels", "capacity_kw"])
        _site_ids = sorted(
            set(_what_if_features["site_id"].dropna().unique().tolist())
            & set(_meta_du["site_id"].tolist())
        )
        _so_tram_thieu_meta = len(_site_metadata) - len(_meta_du)

        if not _site_ids:
            st.warning(
                "Khong tram nao co du metadata so tam pin de chay What-if "
                f"({_so_tram_thieu_meta}/{len(_site_metadata)} tram thieu)."
            )
            st.stop()

        if _so_tram_thieu_meta:
            st.caption(
                f"Da an {_so_tram_thieu_meta}/{len(_site_metadata)} tram thieu metadata "
                "so tam pin - kich ban What-if can con so nay de nhan ty le."
            )

        _ctl_site, _ctl_date, _ctl_time, _ctl_panels = st.columns([0.8, 1.2, 1.0, 1.2])
        with _ctl_site:
            _wi_site = st.selectbox("Site", _site_ids, key="wi_site")

        _site_rows = _what_if_features[_what_if_features["site_id"].eq(_wi_site)].copy()
        _site_rows["date"] = _site_rows["timestamp"].dt.date
        _dates = sorted(_site_rows["date"].unique().tolist())
        with _ctl_date:
            _wi_date = st.selectbox("Ngày", _dates, index=len(_dates) // 2, key="wi_date")

        _day_rows = _site_rows[_site_rows["date"].eq(_wi_date)].sort_values("timestamp")
        _daylight_rows = _day_rows[_day_rows["is_daylight"].fillna(False)]
        if not _daylight_rows.empty:
            _day_rows = _daylight_rows
        _time_labels = _day_rows["timestamp"].dt.strftime("%H:%M").tolist()
        with _ctl_time:
            _wi_time = st.selectbox(
                "Thời điểm nguồn", _time_labels, index=len(_time_labels) // 2, key="wi_time"
            )

        _meta_row = _site_metadata[_site_metadata["site_id"].eq(_wi_site)].iloc[0]
        _base_panels = int(_meta_row["number_of_panels"])
        with _ctl_panels:
            _new_panels = st.number_input(
                "Số lượng tấm pin", min_value=1, max_value=5000,
                value=_base_panels, step=max(1, _base_panels // 20), key="wi_panels",
            )

        _selected_ts = pd.Timestamp(f"{_wi_date} {_wi_time}")
        _row = _day_rows[_day_rows["timestamp"].eq(_selected_ts)].iloc[0]
        _ratio = float(_new_panels) / _base_panels
        _baseline_kwh, _scenario_kwh = predict_what_if(
            _row, _what_if_model, _what_if_config, _ratio
        )
        _delta_kwh = _scenario_kwh - _baseline_kwh
        _delta_pct = (_delta_kwh / _baseline_kwh * 100) if _baseline_kwh else 0.0
        _new_capacity = float(_meta_row["capacity_kw"]) * _ratio

        _m1, _m2, _m3, _m4 = st.columns(4)
        with _m1:
            kpi("Dự báo gốc", f"{_baseline_kwh:.2f} kWh", f"{_base_panels:,} tấm pin")
        with _m2:
            kpi("Dự báo kịch bản", f"{_scenario_kwh:.2f} kWh", f"{int(_new_panels):,} tấm pin")
        with _m3:
            kpi("Thay đổi sản lượng", f"{_delta_kwh:+.2f} kWh", f"{_delta_pct:+.1f}%")
        with _m4:
            kpi("Công suất kịch bản", f"{_new_capacity:.2f} kWp", f"gốc {float(_meta_row['capacity_kw']):.2f} kWp")

        _comparison = pd.DataFrame(
            {
                "Kịch bản": ["Hiện tại", "What-if"],
                f"Sản lượng {str(_model_spec['horizon']).upper()} (kWh)": [_baseline_kwh, _scenario_kwh],
            }
        )
        _fig_what_if = go.Figure(
            go.Bar(
                x=_comparison["Kịch bản"], y=_comparison[f"Sản lượng {str(_model_spec['horizon']).upper()} (kWh)"],
                marker_color=["#6366F1", "#D9822B"],
                text=[f"{v:.2f} kWh" for v in _comparison[f"Sản lượng {str(_model_spec['horizon']).upper()} (kWh)"]],
                textposition="outside",
            )
        )
        _fig_what_if.update_layout(
            template="plotly_white", height=280, margin=dict(l=20, r=20, t=30, b=20),
            yaxis_title=f"Sản lượng dự báo {str(_model_spec['horizon']).upper()} (kWh)",
            xaxis_title=None, showlegend=False,
        )
        st.plotly_chart(_fig_what_if, width="stretch")
        st.caption(
            f"Nguồn tại {_selected_ts:%d/%m/%Y %H:%M}, dự báo cho {(_selected_ts + pd.Timedelta(minutes=15)):%H:%M}. "
            "Weather và hình học mặt trời được giữ nguyên; lag/rolling, kỳ vọng và trần công suất được scale theo số tấm pin."
        )
