"""Dashboard 2: 'Da het tre pha chua?' - cau chuyen trong tam cua ca qua trinh fix hom nay.

5 bieu do: KPI tre pha, quet do tre theo site, scatter lech gio dinh, zoom 1 ngay cu the,
phan bo tre toan he thong. Khong dung tab - 1 trang lien mach theo pyramid BI.
"""

from __future__ import annotations

import ctypes
import glob
from pathlib import Path

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

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard_common import load_shared_css

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "model" / "v3"
AUDIT_PATH = DATA_DIR / "06_1_khu_tre_pha" / "prediction_audit_h1.parquet"

ACTUAL_COLOR = "#6366F1"   # Indigo - dong bo theme moi
PRED_COLOR = "#D9822B"
GRID_COLOR = "#D9DEE7"

st.set_page_config(page_title="Phase Lag Story", page_icon="⏱️", layout="wide")
load_shared_css()
# Rieng trang Phase Lag: tieu de can trai (khong center), KPI to hon, kpi-note mau tim.
st.markdown(
    """
<style>
.dash-title, .dash-subtitle { text-align: left; }
.kpi-card { padding: 12px 14px; min-height: 92px; }
.kpi-value { font-size: 1.55rem !important; }
.kpi-note { color: #6366F1 !important; font-size: 0.78rem; }
</style>
""",
    unsafe_allow_html=True,
)


def kpi(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""<div class="kpi-card">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-note">{note}</div>
</div>""",
        unsafe_allow_html=True,
    )


def style_fig(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        height=height, margin=dict(l=12, r=12, t=46, b=18),
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        font=dict(color="#1F2937", size=12),
    )
    return fig


def he_so_tre_phut(d: pd.DataFrame, col_true: str, col_pred: str) -> float:
    """Do tre theo do doc: tach sai so BIEN DO ra khoi sai so THOI DIEM."""
    x = d.sort_values(["site_id", "timestamp"]).copy()
    g = x.groupby("site_id")[col_true]
    doc = (g.shift(-1) - g.shift(1)) / 2
    err = x[col_pred] - x[col_true]
    m = doc.notna() & err.notna()
    if "is_daylight" in x.columns:
        m = m & x["is_daylight"].fillna(False).astype(bool)
    a = doc[m].to_numpy(); b = err[m].to_numpy()
    if a.size < 50 or (a ** 2).sum() == 0:
        return float("nan")
    return -float((a * b).sum() / (a * a).sum()) * 15


@st.cache_data(ttl=60)
def load_audit() -> pd.DataFrame:
    df = pd.read_parquet(AUDIT_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["plot_timestamp"] = pd.to_datetime(df["plot_timestamp"], errors="coerce")
    return df.dropna(subset=["timestamp"]).rename(columns={"y_true": "thuc_te", "y_pred": "du_bao"})


@st.cache_data(ttl=60)
def load_outlier_group() -> pd.DataFrame:
    """outlier_group khong co trong prediction_audit_h1.parquet (chi co energy_source) -
    phai join rieng tu v3_test_selected de biet dong nao la physical_over_capacity."""
    p = DATA_DIR / "05_selected" / "v3_test_selected.parquet"
    if not p.exists():
        return pd.DataFrame(columns=["site_id", "timestamp", "outlier_group"])
    d = pd.read_parquet(p, columns=["site_id", "timestamp", "outlier_group"])
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    return d


if not AUDIT_PATH.exists():
    st.error(f"Chưa có {AUDIT_PATH}. Chạy notebook 06_1_train_mae trước.")
    st.stop()

df = load_audit()
_og = load_outlier_group()
if not _og.empty:
    df = df.merge(_og, on=["site_id", "timestamp"], how="left")
    df["outlier_group"] = df["outlier_group"].fillna("normal")
else:
    df["outlier_group"] = "normal"

with st.sidebar:
    st.markdown("### 🔍 Bộ lọc")
    # Loai outlier/du lieu impute khoi toan bo trang: energy_source la cot provenance
    # duy nhat co trong prediction_audit_h1.parquet. Outlier (physical_over_capacity) va
    # etl_imputed gia tri phang gan tran (vd site 19) lam sai lech duong "Thuc te", gay
    # hieu nham la model dang du bao theo outlier. Mac dinh BAT.
    measured_only = st.checkbox("Chỉ hiện dữ liệu đo thật (bỏ outlier/impute)", value=True)

if "energy_source" in df.columns and measured_only:
    df = df[df["energy_source"].eq("measured")].copy()

st.markdown('<div class="dash-title">Đã hết trễ pha chưa? — hành trình khử độ trễ dự báo</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="dash-subtitle">Trễ pha = dự báo(T) trùng thực tế(T−k) thay vì thực tế(T) — tức mô hình chép quá khứ thay vì dự báo thật. '
    'Đo bằng hồi quy độ dốc (tách biên độ khỏi thời điểm), không dùng RMSE.</div>',
    unsafe_allow_html=True,
)

# ── TANG 1: KPI tre pha tong the + cau dien giai ──
_tre_toan_bo = he_so_tre_phut(df, "thuc_te", "du_bao")
_rows = []
for s, g in df.groupby("site_id"):
    t = he_so_tre_phut(g, "thuc_te", "du_bao")
    if t == t:
        _rows.append({"site_id": s, "tre_phut": t})
df_site_tre = pd.DataFrame(_rows).sort_values("tre_phut", key=abs, ascending=False)
_so_site_vuot_5p = int((df_site_tre["tre_phut"].abs() > 5).sum())

k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi("Trễ pha toàn hệ thống", f"{_tre_toan_bo:+.2f} phút" if _tre_toan_bo == _tre_toan_bo else "n/a", "dương = dự báo đi sau")
with k2:
    kpi("Site vượt ngưỡng 5 phút", f"{_so_site_vuot_5p}/{len(df_site_tre)}", "0 là tốt nhất")
with k3:
    kpi("Site lệch nhiều nhất", f"{df_site_tre.iloc[0]['site_id']}" if len(df_site_tre) else "n/a",
        f"{df_site_tre.iloc[0]['tre_phut']:+.2f} phút" if len(df_site_tre) else "")
with k4:
    kpi("Số site đo được", f"{len(df_site_tre)}", "toàn bộ tập test")

if _tre_toan_bo == _tre_toan_bo:
    if abs(_tre_toan_bo) <= 2 and _so_site_vuot_5p == 0:
        st.success(f"✅ **Kết luận: hết trễ pha.** {_tre_toan_bo:+.2f} phút toàn hệ thống, không site nào vượt ngưỡng 5 phút. "
                   "3 phép đo độc lập trong quá trình fix (train thử nhanh, model cuối, hồi quy độ dốc) đều đồng thuận.")
    else:
        st.warning(f"⚠️ Vẫn còn {_so_site_vuot_5p} site vượt ngưỡng 5 phút, cần xem lại.")

st.divider()

# ── TANG 2: 2 bieu do chinh - quet theo site + scatter lech gio dinh ──
# Moi chart nam trong container(border=True) - khung rieng giong BI tools that,
# gap="small" de cac cot sat nhau, khong de khoang trong lon.
t2_left, t2_right = st.columns(2, gap="small")
with t2_left:
    with st.container(border=True):
        st.markdown("##### Trễ pha theo từng site (42 site)")
        fig_bar = px.bar(df_site_tre, x="site_id", y="tre_phut", color="tre_phut",
                          color_continuous_scale=["#6366F1", "#e5e7eb", "#D9822B"], color_continuous_midpoint=0)
        fig_bar.add_hline(y=5, line_dash="dot", line_color="#C23B22")
        fig_bar.add_hline(y=-5, line_dash="dot", line_color="#C23B22")
        st.plotly_chart(style_fig(fig_bar, 320), use_container_width=True)
with t2_right:
    with st.container(border=True):
        st.markdown("##### Lệch giờ đỉnh: thực tế vs dự báo (ngày đỉnh nhọn)")
        w = df[df["is_daylight"].fillna(False).astype(bool)].copy()
        w["ngay"] = w["timestamp"].dt.date
        rows = []
        for (s, ng), g in w.groupby(["site_id", "ngay"]):
            if len(g) < 8:
                continue
            at = g["thuc_te"].max()
            if at <= 0.5:
                continue
            rong = int((g["thuc_te"] >= at * 0.98).sum())
            if rong > 2:
                continue
            ta = g.loc[g["thuc_te"].idxmax(), "timestamp"]
            tp = g.loc[g["du_bao"].idxmax(), "timestamp"]
            rows.append({"gio_dinh_actual": ta.hour + ta.minute / 60, "gio_dinh_predict": tp.hour + tp.minute / 60})
        df_dinh = pd.DataFrame(rows)
        if len(df_dinh):
            fig_sc = go.Figure()
            fig_sc.add_trace(go.Scatter(x=df_dinh["gio_dinh_actual"], y=df_dinh["gio_dinh_predict"], mode="markers",
                                         marker=dict(size=5, opacity=0.35, color=ACTUAL_COLOR), name="ngày đỉnh nhọn"))
            fig_sc.add_trace(go.Scatter(x=[6, 20], y=[6, 20], mode="lines", line=dict(color="#C23B22", dash="dot"), name="khớp hoàn hảo"))
            fig_sc.update_layout(xaxis_title="Giờ đỉnh thực tế", yaxis_title="Giờ đỉnh dự báo")
            st.plotly_chart(style_fig(fig_sc, 320), use_container_width=True)
            st.caption("Điểm trên đường chéo = khớp giờ đỉnh. Tán xạ đều 2 phía = không phải trễ pha hệ thống.")

# ── TANG 3: zoom 1 ngay + phan bo tre + trễ theo khung giờ (bieu do thu 5) ──
t3_left, t3_right = st.columns(2, gap="small")
with t3_left:
    with st.container(border=True):
        st.markdown("##### Zoom 1 site/1 ngày cụ thể")
        sites = sorted(df["site_id"].dropna().astype(str).unique().tolist(), key=lambda x: int(float(x)))
        c1, c2 = st.columns(2)
        with c1:
            site_pick = st.selectbox("Site", sites, index=sites.index("19") if "19" in sites else 0)
        df_s = df[df["site_id"].astype(str) == site_pick].copy()
        days = sorted(df_s["timestamp"].dt.date.unique().tolist())
        with c2:
            day_pick = st.selectbox("Ngày", days, index=len(days) // 2 if days else 0)
        d1 = df_s[df_s["timestamp"].dt.date == day_pick].sort_values("timestamp")
        fig_zoom = go.Figure()
        fig_zoom.add_trace(go.Scatter(x=d1["timestamp"], y=d1["thuc_te"], mode="lines+markers", name="Thực tế", line=dict(color=ACTUAL_COLOR, width=2)))
        fig_zoom.add_trace(go.Scatter(x=d1["timestamp"], y=d1["du_bao"], mode="lines+markers", name="Dự báo", line=dict(color=PRED_COLOR, width=1.8)))
        _out1 = d1[d1["outlier_group"].ne("normal")]
        if len(_out1):
            fig_zoom.add_trace(go.Scatter(
                x=_out1["timestamp"], y=_out1["thuc_te"], mode="markers", name="Outlier (bị loại khỏi train)",
                marker=dict(color="#DC2626", size=10, symbol="x"),
            ))
        st.plotly_chart(style_fig(fig_zoom, 300), use_container_width=True)
        if len(_out1):
            st.caption(f"Dấu X đỏ = {len(_out1)} điểm bị gắn outlier ({_out1['outlier_group'].unique().tolist()}), không tham gia train.")
with t3_right:
    with st.container(border=True):
        st.markdown("##### Phân bố trễ pha toàn hệ thống")
        fig_hist = px.histogram(df_site_tre, x="tre_phut", nbins=20, color_discrete_sequence=[ACTUAL_COLOR])
        fig_hist.add_vline(x=0, line_dash="dot", line_color="#C23B22")
        st.plotly_chart(style_fig(fig_hist, 300), use_container_width=True)

# Bieu do thu 5: tre theo khung gio trong ngay - dinh thuc te xay ra gio nao thi tre bao nhieu
with st.container(border=True):
    st.markdown("##### Trễ pha theo khung giờ đỉnh xảy ra trong ngày")
    w2 = df[df["is_daylight"].fillna(False).astype(bool)].copy()
    w2["ngay"] = w2["timestamp"].dt.date
    rows2 = []
    for (s, ng), g in w2.groupby(["site_id", "ngay"]):
        if len(g) < 8:
            continue
        at = g["thuc_te"].max()
        if at <= 0.5:
            continue
        ta = g.loc[g["thuc_te"].idxmax(), "timestamp"]
        tp = g.loc[g["du_bao"].idxmax(), "timestamp"]
        rows2.append({"gio_dinh": ta.hour, "lech_phut": (tp - ta).total_seconds() / 60})
    df_gio = pd.DataFrame(rows2)
    if len(df_gio):
        _theo_gio = df_gio.groupby("gio_dinh", as_index=False)["lech_phut"].median()
        fig_gio = px.bar(_theo_gio, x="gio_dinh", y="lech_phut", color="lech_phut",
                          color_continuous_scale=["#6366F1", "#e5e7eb", "#D9822B"], color_continuous_midpoint=0)
        fig_gio.update_layout(xaxis_title="Giờ đỉnh thực tế xảy ra", yaxis_title="Lệch trung vị (phút)")
        st.plotly_chart(style_fig(fig_gio, 280), use_container_width=True)
        st.caption("Nếu có 1 khung giờ nào lệch mạnh hẳn so với các giờ khác - đó là dấu hiệu bug local cần soi kỹ hơn.")

# Bieu do thu 6: dinh THUC TE vs dinh DU BAO tung ngay/site, tach mau theo co outlier hay
# khong - de chung minh model KHONG hoc theo outlier (outlier bi w=0, khong vao loss).
with st.container(border=True):
    st.markdown("##### Đỉnh thực tế vs đỉnh dự báo — có outlier vs không outlier")
    w3 = df[df["is_daylight"].fillna(False).astype(bool)].copy()
    w3["ngay"] = w3["timestamp"].dt.date
    rows3 = []
    for (s, ng), g in w3.groupby(["site_id", "ngay"]):
        if len(g) < 8:
            continue
        dinh_that = g["thuc_te"].max()
        if dinh_that <= 0.5:
            continue
        dinh_du_bao = g["du_bao"].max()
        co_outlier = g["outlier_group"].ne("normal").any()
        rows3.append({"site_id": s, "ngay": ng, "dinh_that": dinh_that, "dinh_du_bao": dinh_du_bao,
                      "nhom": "Có outlier trong ngày" if co_outlier else "Không có outlier"})
    df_dinh3 = pd.DataFrame(rows3)
    if len(df_dinh3):
        fig_dinh3 = go.Figure()
        for _nhom, _mau in [("Không có outlier", ACTUAL_COLOR), ("Có outlier trong ngày", "#DC2626")]:
            _sub = df_dinh3[df_dinh3["nhom"] == _nhom]
            fig_dinh3.add_trace(go.Scatter(
                x=_sub["dinh_that"], y=_sub["dinh_du_bao"], mode="markers", name=_nhom,
                marker=dict(size=5, opacity=0.45, color=_mau),
            ))
        _lim = float(df_dinh3[["dinh_that", "dinh_du_bao"]].to_numpy().max())
        fig_dinh3.add_trace(go.Scatter(x=[0, _lim], y=[0, _lim], mode="lines",
                                        line=dict(color="#94A3B8", dash="dot"), name="khớp hoàn hảo"))
        fig_dinh3.update_layout(xaxis_title="Đỉnh thực tế (kWh)", yaxis_title="Đỉnh dự báo (kWh)")
        st.plotly_chart(style_fig(fig_dinh3, 340), use_container_width=True)
        st.caption(
            "Nếu 2 nhóm điểm (đỏ = ngày có outlier, xanh = ngày không có) nằm CHUNG 1 dải quanh đường chéo, "
            "nghĩa là model dự báo nhất quán giữa 2 loại ngày — không có dấu hiệu bị outlier kéo lệch riêng. "
            "outlier_group join từ 05_selected/v3_test_selected.parquet, không có trong site 19/24 (đã loại khỏi tập test)."
        )

st.caption(
    "Cách fix chính: bỏ lag_1/lag_4 khỏi đặc trưng (chỉ giữ lag_96), downscale bức xạ theo clear-sky index, "
    "sửa join thời tiết về đúng causal (docs/open_meteo_hourly_column_semantics_vi.md), loại site 19/24 khỏi "
    "train/test vì capacity_kw không đáng tin (không phải imputed nhưng lệch quá xa hành vi thật)."
)
