"""Trang 1 — Chuoi thoi gian & doi chung Prophet.

REFACTOR 2026-08-09:
  - Bo bo chon "Nguon mo hinh" 8 lua chon (06_1 / 06_2 / 06_3 / API / bo_goc /
    cac bien the 06_train...). Dashboard bao cao KET QUA CHINH THUC, khong phai
    cong cu duyet thi nghiem; 5 trong 8 nguon do da tro toi file khong con ton tai.
    Nguon chinh thuc bay gio: 07_final_test - model duoc chon tu validation.
  - Bo goi model.predict() trong trang (ham predict_on_test cu). Trang chi ve lai
    artifact pipeline da ghi, khong tu suy dien lai ket qua.
  - Them duong Prophet vao chart va o so sanh WAPE, lay tu 08_baseline_prophet_test
    (Prophet do tren DUNG tap dong cua mo hinh).
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


from dashboard_common import header_bao_cao, load_shared_css
from api.ml.dashboard_data import (

    ACTUAL_COLOR, PRED_COLOR, PROPHET_COLOR, GRID_COLOR,
    audit_metrics, he_so_tre_phut, load_best_loss, load_metrics,
    load_outlier_group, load_prediction_audit, load_prophet_by_site,
    load_prophet_predictions, load_prophet_summary, metric_value, skill_score,
    with_display_timestamp,
)



def style_fig(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=height,
        margin=dict(l=12, r=12, t=88, b=18),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        font=dict(color="#1F2937", size=12),
    )
    return fig


def kpi(label: str, value: str, note: str = "", status: str | None = None) -> None:
    """status: 'up' (xanh, tot) | 'down' (do, can chu y) | None (xam, trung tinh).

    Mau la MA TRANG THAI theo nguong that giong BI tool that (xanh=tot/do=xau),
    khong phai mau trang tri.
    """
    _cls = f"kpi-note {status}" if status in ("up", "down") else "kpi-note"
    _icon = "▲" if status == "up" else ("▼" if status == "down" else "")
    st.markdown(
        f"""
<div class="kpi-card">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{value}</div>
  <div class="{_cls}">{_icon} {note}</div>
</div>
""",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Nap du lieu
# ══════════════════════════════════════════════════════════════════════════════
pred_all = load_prediction_audit()
if pred_all.empty:
    st.error("Chưa có `07_final_test/prediction_audit.parquet` — chạy stage s09 trước.")
    st.stop()

best_loss = load_best_loss()
prophet_pred = load_prophet_predictions()
prophet_tom_tat = load_prophet_summary()

# Ghi RO tap nao quyet dinh dieu gi. Day la diem hoi dong hay hoi nhat: mo hinh
# duoc CHON tren validation, va chi sau khi chot moi mo tap test de cham diem.
_h1 = best_loss.get("h1", {})
_h4 = best_loss.get("h4", {})
_nhan_chon = (
    f"Mô hình được chọn: H1 = <b>{_h1.get('winning_loss', '?').upper()}</b> "
    f"(WAPE validation {_h1.get('val_wape', float('nan')):.2f}%), "
    f"H4 = <b>{_h4.get('winning_loss', '?').upper()}</b> "
    f"(WAPE validation {_h4.get('val_wape', float('nan')):.2f}%). "
    "Quyết định chỉ dùng validation; các số dưới đây đo trên tập Test niêm phong."
) if _h1 else "Nguồn: 07_final_test — tập Test niêm phong."

# ══════════════════════════════════════════════════════════════════════════════
#  Bo loc
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("### 🔍 Bộ lọc")
with st.sidebar:
    available_horizons = [
        h for h in (1, 4)
        if f"y_pred_h{h}" in pred_all.columns and pred_all[f"y_pred_h{h}"].notna().any()
    ]
    horizon = st.selectbox("Horizon", available_horizons, format_func=lambda h: f"h{h} ({h * 15} phút)")
    _model_for_horizon = best_loss.get(f"h{horizon}", {}).get("winning_loss", "?").upper()
    st.caption(f"Artifact đang hiển thị: {_model_for_horizon} · H{horizon} — chọn từ validation")
    true_col, pred_col = f"y_true_h{horizon}", f"y_pred_h{horizon}"

    pred_h = pred_all[pred_all[pred_col].notna()].copy()
    sites = sorted(pred_h["site_id"].dropna().astype(str).unique(), key=lambda x: int(float(x)))
    site_id = st.selectbox("Site", sites, index=sites.index("19") if "19" in sites else 0)
    daylight_only = st.checkbox("Chỉ dòng ban ngày", value=False)
    # Mac dinh BAT: outlier va vai dong etl_imputed gia tri phang gan tran se lam
    # duong "Thuc te" tren chart trong sai lech, gay hieu nham la model dang du bao
    # theo outlier.
    measured_only = st.checkbox("Chỉ dữ liệu đo thật (bỏ outlier/impute)", value=True)
    hien_prophet = st.checkbox("Hiện đường Prophet (đối chứng)", value=True,
                               disabled=prophet_pred.empty)

_tre_pha = he_so_tre_phut(pred_all.dropna(subset=[true_col, pred_col]), true_col, pred_col)

site_pred = with_display_timestamp(
    pred_h[pred_h["site_id"].astype(str).eq(str(site_id))], horizon)
if site_pred.empty:
    st.error("Không có dòng nào cho trạm đang chọn.")
    st.stop()

if daylight_only and "is_daylight" in site_pred.columns:
    site_pred = site_pred[site_pred["is_daylight"].fillna(False).astype(bool)].copy()
if measured_only and "energy_source" in site_pred.columns:
    site_pred = site_pred[site_pred["energy_source"].eq("measured")].copy()

# Nhan outlier that - prediction_audit khong mang cot nay, phai join tu tap test.
site_pred["audit_outlier_group"] = "normal"
site_pred["is_audit_outlier"] = False
_og = load_outlier_group()
if not _og.empty:
    site_pred = site_pred.merge(_og, on=["site_id", "timestamp"], how="left")
    site_pred["audit_outlier_group"] = site_pred["outlier_group"].fillna("normal")
    site_pred["is_audit_outlier"] = site_pred["audit_outlier_group"].ne("normal")

# Gan du bao Prophet vao cung khung de ve chung 1 chart.
prophet_col = f"prophet_h{horizon}"
if hien_prophet and not prophet_pred.empty and prophet_col in prophet_pred.columns:
    site_pred = site_pred.merge(
        prophet_pred[["site_id", "timestamp", prophet_col]],
        on=["site_id", "timestamp"], how="left")

with st.sidebar:
    min_day = site_pred["display_timestamp"].min().date()
    max_day = site_pred["display_timestamp"].max().date()
    date_mode = st.radio("Khoảng ngày", ["Cửa sổ 7 ngày", "Tự chọn"])
    if date_mode == "Cửa sổ 7 ngày":
        site_pred["window_start"] = site_pred["display_timestamp"].dt.floor("7D")
        windows = site_pred["window_start"].value_counts().head(12).index.tolist()
        start_ts = pd.Timestamp(st.selectbox("Cửa sổ", windows))
        end_ts = start_ts + pd.Timedelta(days=7)
    else:
        picked = st.date_input("Từ ngày → đến ngày",
                               [max(min_day, max_day - pd.Timedelta(days=7)), max_day])
        if isinstance(picked, tuple) and len(picked) == 2:
            start_ts, end_ts = pd.Timestamp(picked[0]), pd.Timestamp(picked[1]) + pd.Timedelta(days=1)
        else:
            start_ts, end_ts = pd.Timestamp(min_day), pd.Timestamp(max_day) + pd.Timedelta(days=1)

plot_pred = site_pred[site_pred["display_timestamp"].between(start_ts, end_ts)].copy()

overall, site_metrics = load_metrics(horizon)
if not overall:
    overall, site_metrics = audit_metrics(pred_all, horizon, cache_key="final")

_cols = ["display_timestamp", true_col, pred_col, prophet_col,
         "is_audit_outlier", "audit_outlier_group"]
compare = (plot_pred[[c for c in _cols if c in plot_pred.columns]]
           .dropna(subset=[true_col, pred_col])
           .rename(columns={true_col: "y_true", pred_col: "y_pred", prophet_col: "y_prophet"}))
compare["residual"] = compare["y_true"] - compare["y_pred"]

# ══════════════════════════════════════════════════════════════════════════════
#  Tang 1 — KPI
# ══════════════════════════════════════════════════════════════════════════════
wape = metric_value(overall, "wape")
rmse = metric_value(overall, "rmse")
mae = metric_value(overall, "mae")
r2 = metric_value(overall, "r2")
_pro = prophet_tom_tat.get(f"h{horizon}", {})
_wape_common = _pro.get("wape_lightgbm_%")
_ss = (skill_score(_wape_common, _pro["wape_prophet_%"])
       if _wape_common and _pro.get("wape_prophet_%") else None)

with _KPI_TS:
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        # Nguong WAPE: <20% tot (nganh du bao mat troi 15 phut thuong 15-35%).
        _st = "up" if wape and wape < 20 else "down" if wape and wape > 30 else None
        _note = (f"Skill Score common {_ss:+.1f}%" if _ss is not None
                 else "càng thấp càng tốt")
        kpi("WAPE", f"{wape:.2f}%" if wape else "n/a", _note, status=_st)
    with k2:
        _st = "up" if _tre_pha == _tre_pha and abs(_tre_pha) <= 2 else (
            "down" if _tre_pha == _tre_pha and abs(_tre_pha) > 5 else None)
        kpi("Trễ pha", f"{_tre_pha:+.2f} phút" if _tre_pha == _tre_pha else "n/a",
            "dương = dự báo đi sau", status=_st)
    with k3:
        kpi("Skill Score", f"{_ss:+.1f}%" if _ss is not None else "n/a",
            "common scope với Prophet",
            status="up" if _ss and _ss > 0 else "down" if _ss else None)
    with k4:
        kpi("MAE", f"{mae:.4f} kWh" if mae else "n/a", "sai số tuyệt đối")
    with k5:
        _st = "up" if r2 and r2 >= 0.85 else "down" if r2 and r2 < 0.6 else None
        kpi("R²", f"{r2:.4f}" if r2 else "n/a", "% biến động sản lượng được giải thích", status=_st)
    with k6:
        kpi("RMSE", f"{rmse:.4f} kWh" if rmse else "n/a", f"{len(compare):,} dòng đang xem")

st.caption(
    f"KPI WAPE/RMSE/MAE/R² lấy từ phạm vi Test chính thức **measured + daylight** "
    f"(n={overall.get('measured_daylight_test_rows', 'n/a')}) của model {_model_for_horizon} · H{horizon}; "
    f"Skill Score lấy từ phạm vi chung với Prophet (n={_pro.get('n_dong', 'n/a')}). "
    "Các KPI không đổi khi chỉnh Site hay khoảng ngày; chart và bảng bên dưới mới lọc theo sidebar."
)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  Tang 2 — chart chinh
# ══════════════════════════════════════════════════════════════════════════════
t2_left, t2_right = st.columns(2, gap="small")
with t2_left:
    with st.container(border=True):
        st.markdown(f"##### Thực tế vs Dự báo — Trạm {site_id} ({start_ts.date()} → {end_ts.date()})")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=compare["display_timestamp"], y=compare["y_true"],
                                 mode="lines+markers", name="Thực tế",
                                 line=dict(color=ACTUAL_COLOR, width=2), marker=dict(size=3)))
        fig.add_trace(go.Scatter(x=compare["display_timestamp"], y=compare["y_pred"],
                                 mode="lines+markers", name=f"LightGBM · {_model_for_horizon} H{horizon}",
                                 line=dict(color=PRED_COLOR, width=1.8), marker=dict(size=3)))
        if "y_prophet" in compare.columns and compare["y_prophet"].notna().any():
            fig.add_trace(go.Scatter(x=compare["display_timestamp"], y=compare["y_prophet"],
                                     mode="lines", name="Prophet (đối chứng)",
                                     line=dict(color=PROPHET_COLOR, width=1.6, dash="dot")))
        # Sao vang/tim: dinh THUC TE va dinh DU BAO cua TUNG NGAY, khong phai 1 dinh
        # duy nhat ca 7 ngay - de nhin ra lech dinh theo ngay.
        _c = compare.copy()
        _c["ngay"] = _c["display_timestamp"].dt.date
        for _col, _ten, _mau, _vien in (("y_true", "Đỉnh thực tế/ngày", "#F59E0B", "#92400E"),
                                        ("y_pred", "Đỉnh dự báo/ngày", "#8B5CF6", "#4C1D95")):
            _idx = _c.groupby("ngay")[_col].idxmax().dropna()
            _d = _c.loc[_idx]
            fig.add_trace(go.Scatter(x=_d["display_timestamp"], y=_d[_col], mode="markers",
                                     name=_ten, marker=dict(symbol="star", size=13, color=_mau,
                                                            line=dict(color=_vien, width=1))))
        if compare.get("is_audit_outlier", pd.Series(dtype=bool)).any():
            _o = compare[compare["is_audit_outlier"]]
            fig.add_trace(go.Scatter(x=_o["display_timestamp"], y=_o["y_true"], mode="markers",
                                     name="Outlier (đã gắn nhãn nhóm)",
                                     marker=dict(symbol="x", size=9, color="#DC2626")))
        st.plotly_chart(style_fig(fig, 320), width='stretch')

with t2_right:
    with st.container(border=True):
        st.markdown("##### Xếp hạng 42 trạm theo WAPE")
        _mc = "wape" if "wape" in site_metrics.columns else None
        if _mc:
            _r = site_metrics[~site_metrics["site_id"].astype(str).eq("ALL")]
            _f = px.bar(_r.sort_values(_mc), x="site_id", y=_mc, color=_mc,
                        color_continuous_scale=["#16A34A", "#F59E0B", "#DC2626"])
            _f.update_xaxes(type="category")
            st.plotly_chart(style_fig(_f, 300), width='stretch')
        else:
            st.info("Chưa có dữ liệu xếp hạng trạm.")
# ══════════════════════════════════════════════════════════════════════════════
#  Tang 3 — bang chi tiet
# ══════════════════════════════════════════════════════════════════════════════
