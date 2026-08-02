"""Dashboard 3: 'Mo hinh hoc duoc gi?' - SHAP explainability, dong bo theme sang
voi 2 trang kia. Sua 2 bug that: (1) plotly_dark + COLOR_BG toi cung trong code
lam lech theme, (2) px.scatter tu dong bat WebGL (scattergl) khi nhieu diem, loi
tren may/trinh duyet khong ho tro WebGL - ep render_mode='svg' de an toan.
"""

import ctypes
import glob
import pickle
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import shap
import streamlit as st

from dashboard_common import load_shared_css

for _lib in ("libstdc++.so.6", "libgomp.so.1"):
    for _p in (
        glob.glob(f"/nix/store/*gcc*/lib/{_lib}")
        + glob.glob(f"/run/current-system/sw/lib/{_lib}")
        + glob.glob(f"/usr/lib*/{_lib}")
    ):
        try:
            ctypes.CDLL(_p, mode=ctypes.RTLD_GLOBAL)
            break
        except Exception:
            pass

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "model" / "v3"

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

st.markdown('<div class="dash-title">Mô hình học được gì? — phân tích SHAP</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="dash-subtitle">Đóng góp của từng đặc trưng tới dự báo sản lượng quang điện.</div>',
    unsafe_allow_html=True,
)


MODEL_PATH = DATA_DIR / "06_1_khu_tre_pha" / "model_h1.pkl"


@st.cache_data
def load_native_importance() -> pd.DataFrame:
    """LightGBM co san feature_importances_ - tinh theo GAIN trung binh qua TAT CA
    cay trong ensemble (khac SHAP: SHAP la dong gop tung du bao, cai nay la mo hinh
    hoc duoc gi noi chung). Doc thang tu model that, khong tu suy dien."""
    if not MODEL_PATH.exists():
        return pd.DataFrame()
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)
    model = bundle["model"]
    feats = bundle["features"]
    model.set_params(importance_type="gain")
    gain = model.booster_.feature_importance(importance_type="gain")
    split = model.booster_.feature_importance(importance_type="split")
    return pd.DataFrame({"feature": feats, "gain": gain, "split": split}).sort_values("gain", ascending=False)


X_TEST_PATH = DATA_DIR / "06_train" / "mae" / "h1" / "X_test_h1.parquet"


@st.cache_data
def load_real_feature_values(feat_val_keys: pd.DataFrame) -> pd.DataFrame:
    """shap_values.parquet CHI chua gia tri SHAP (bien do nho +-0.01..0.09), KHONG
    chua gia tri dac trung goc (vd shortwave_radiation phai la 0-1100 W/m2 that,
    khong phai +-0.06). Phai join voi X_test_h1.parquet (co gia tri that) qua
    site_id+timestamp de lay dung du lieu cho PDP/scatter, khong dung nham SHAP
    lam gia tri dac trung nhu ban dau."""
    if not X_TEST_PATH.exists() or feat_val_keys.empty:
        return pd.DataFrame()
    x_real = pd.read_parquet(X_TEST_PATH)
    keys = feat_val_keys[["site_id", "timestamp"]].copy()
    keys["timestamp"] = pd.to_datetime(keys["timestamp"])
    x_real["timestamp"] = pd.to_datetime(x_real["timestamp"])
    return keys.merge(x_real, on=["site_id", "timestamp"], how="left")


@st.cache_data
def load_local_shap(feat_set: str = "") -> tuple[pd.DataFrame, pd.DataFrame]:
    suffix = "_no_lag1" if feat_set == "no_lag1" else ""
    p_imp = DATA_DIR / "08_explain" / f"shap_importance{suffix}.csv"
    p_val = DATA_DIR / "08_explain" / f"shap_values{suffix}.parquet"
    if not p_imp.exists():
        p_imp = DATA_DIR / "08_explain" / "shap_importance.csv"
    if not p_val.exists():
        p_val = DATA_DIR / "08_explain" / "shap_values.parquet"
    df_imp = pd.read_csv(p_imp) if p_imp.exists() else pd.DataFrame()
    df_val = pd.read_parquet(p_val) if p_val.exists() else pd.DataFrame()
    return df_imp, df_val


with st.sidebar:
    st.markdown("### Bộ lọc XAI")
    feat_choice = st.selectbox("Bộ đặc trưng mô hình", ["no_lag1 (khắc phục trễ pha 15p)", "full (đầy đủ)"])
feat_param = "no_lag1" if "no_lag1" in feat_choice else "full"

df_imp, df_val = load_local_shap(feat_param)
if df_imp.empty:
    st.warning(f"Chưa có dữ liệu SHAP cho {feat_choice}. Hãy chạy notebook 08_explainable_ai.ipynb trước.")
    st.stop()


def get_group(name: str) -> str:
    if name.startswith("lag_") or name.startswith("rolling_"):
        return "Lịch sử & Lag"
    if any(k in name for k in ["ghi", "poa", "temp", "dhi", "dni", "cloud", "pv_", "radiation", "shortwave"]):
        return "Thời tiết & Bức xạ"
    if any(k in name for k in ["hour", "month", "day", "sin", "cos", "doy", "minute"]):
        return "Thời gian & Chu kỳ"
    return "Vị trí & Metadata"


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
df_x_real = load_real_feature_values(df_val)

# ── HANG A: 2 bieu do GLOBAL canh nhau - LightGBM Gain (trai) | PDP phi tuyen (phai) ──
rowA_left, rowA_right = st.columns(2, gap="small")

df_native = load_native_importance()
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
        _pick = _force_box.selectbox("Chọn 1 dòng để giải thích", _opt_df["nhan"].tolist())
        _row_idx = _opt_df[_opt_df["nhan"] == _pick].index[0]
        _shap_row = df_val.loc[_row_idx, feature_cols].astype(float)
        _real_row = df_x_real.loc[_row_idx] if _row_idx in df_x_real.index else None

        _cL, _cR = _force_box.columns(2)
        with _cL:
            _thuc_te = _real_row["y_true"] if _real_row is not None and "y_true" in _real_row else None
            kpi("Thực tế", f"{_thuc_te:.2f} kWh" if _thuc_te is not None else "n/a", "")
        with _cR:
            kpi("Tổng đóng góp SHAP", f"{float(_shap_row.sum()):+.4f}", "so với base value")

        # Ve DUNG bang thu vien shap that (shap.plots.force, matplotlib=True) - giong
        # y het anh trong repo tham khao (nguyenhads/sales_forecasting_xai, notebook 05,
        # cell 31): 1 thanh lien tuc dang phieu, mui ten hong (tang) va xanh duong (giam)
        # hop lai o f(x). KHONG tu ve lai bang Plotly (go.Waterfall truoc day la thanh
        # roi rac, sai kieu dang - da bi phat hien va yeu cau sua).
        _base_value = float(df_val[feature_cols].mean().sum()) if not df_val.empty else 0.0
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
            "Cộng dồn từ base value ra tới f(x) — giống shap.force_plot()/shap.plots.waterfall(). "
            "Chỉ hiện 6 đặc trưng ảnh hưởng mạnh nhất, phần còn lại đã gộp vào base value."
        )
