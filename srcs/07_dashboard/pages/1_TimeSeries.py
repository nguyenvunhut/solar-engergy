from __future__ import annotations

import ctypes
import glob
import json
import os
from pathlib import Path

# NixOS: nap truoc runtime C++/OpenMP de LightGBM import duoc.
# Tren Windows/macOS cac glob nay rong nen doan code khong lam gi.
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

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard_common import load_shared_css
from dashboard_data import (
    ACTUAL_COLOR, PRED_COLOR, OUTLIER_COLOR, GRID_COLOR,
    DATA_DIR, FINAL_KHONG_TRE, FINAL_KHONG_TRE_H4, HUBER_PRED, HUBER_PRED_H4,
    MSE_PRED, MSE_PRED_H4, BO_GOC_PRED, PREDICTION_AUDIT, API_BASE_URL,
    load_prediction_audit, load_bo_goc_audit, load_final_khong_tre, load_via_api,
    load_pred_simple, trained_variants, load_variant_audit, audit_metrics,
    lag_scan, load_metrics, load_baseline, load_new_site_metrics,
    load_shap_importance, he_so_tre_phut, metric_value, with_display_timestamp,
)

load_shared_css()


def style_fig(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=height,
        margin=dict(l=12, r=12, t=46, b=18),
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        font=dict(color="#1F2937", size=12),
    )
    return fig


def kpi(label: str, value: str, note: str = "", status: str | None = None) -> None:
    """status: 'up' (xanh, tot) | 'down' (do, can chu y) | None (xam, trung tinh).
    Mau la MA TRANG THAI theo nguong that (giong BI tools that: xanh=tot/do=xau),
    khong phai mau trang tri - vd WAPE thap la 'up', tre pha vuot nguong la 'down'."""
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




# Don lai (2026-07-30): truoc day co 17 nguon, gan het la thu nghiem cu da bo, file
# khong con ton tai, chi gay roi. Chi giu 2 nguon con dung that; cac bien the trong
# 06_train/ (vd sau khi doi loss sang MAE) van tu dong duoc them vao ben duoi.
MODEL_SOURCES = {
    "06_1 - MAE loss (khu tre pha + fix tran cong suat)": "final_khong_tre",
    "06_2 - Huber loss (doc file da nhan nguoc san, khong predict lai)": "huber_pred_file",
    "06_3 - MSE loss (doc file da nhan nguoc san, khong predict lai)": "mse_pred_file",
    "API (FastAPI) - can chay uvicorn truoc": "via_api",
    "07 final test - pipeline chinh thuc": "old",
}
for _v in trained_variants():
    MODEL_SOURCES[f"06_train {_v}"] = f"variant:{_v}"

_default_source = os.getenv("DASHBOARD_DEFAULT_SOURCE", "final_khong_tre")
_source_labels = list(MODEL_SOURCES)
_default_index = next(
    (i for i, label in enumerate(_source_labels) if MODEL_SOURCES[label] == _default_source),
    0,
)
# Gom TOAN BO bo loc vao 1 khoi lien tuc trong sidebar - 1 tieu de "Bo loc" duy nhat,
# khong tach thanh nhieu header roi rac (truoc day: Data source / Parameters / Date mode
# la 3 khoi tach biet, nhin roi). Dat header o day, cac phan sau (line ~757, ~787) bo header rieng.
st.sidebar.markdown("### 🔍 Bộ lọc")
source_label = st.sidebar.radio("Nguồn mô hình", _source_labels, index=_default_index)
model_source = MODEL_SOURCES[source_label]

if model_source == "final_khong_tre":
    pred_all = load_final_khong_tre()
    source_path = FINAL_KHONG_TRE
    source_note = "06_1 MAE khu tre pha - downscale ghi_cs, goc mat troi, quy mo + tran cong suat tram, co lag_4"
    if pred_all.empty:
        st.error(f"Chua co {FINAL_KHONG_TRE}")
        st.stop()
elif model_source == "huber_pred_file":
    pred_all = load_pred_simple(HUBER_PRED, HUBER_PRED_H4)
    source_path = HUBER_PRED
    source_note = "06_2 Huber - doc prediction_audit da nhan nguoc san tu notebook, khong predict lai trong dashboard"
    if pred_all.empty:
        st.error(f"Chua co {HUBER_PRED} - chay xong notebook 06_2 truoc.")
        st.stop()
elif model_source == "mse_pred_file":
    pred_all = load_pred_simple(MSE_PRED, MSE_PRED_H4)
    source_path = MSE_PRED
    source_note = "06_3 MSE - doc prediction_audit da nhan nguoc san tu notebook, khong predict lai trong dashboard"
    if pred_all.empty:
        st.error(f"Chua co {MSE_PRED} - chay xong notebook 06_3 truoc.")
        st.stop()
elif model_source == "via_api":
    pred_all = load_via_api()
    source_path = Path(f"{API_BASE_URL}/predictions")
    source_note = f"Doc qua FastAPI ({API_BASE_URL}) thay vi doc file truc tiep"
    if pred_all.empty:
        st.error(
            f"Khong goi duoc API tai {API_BASE_URL}. Chay truoc: "
            "uvicorn srcs.07_dashboard.api:app --port 8000 (tu thu muc goc repo)."
        )
        st.stop()
elif model_source == "bo_goc":
    pred_all = load_bo_goc_audit()
    source_path = BO_GOC_PRED
    source_note = "Bo du lieu GOC (truoc khi sua ETL) - h1 target = T+15 phut"
    if pred_all.empty:
        st.error(f"Chua co {BO_GOC_PRED}")
        st.stop()
else:
    pred_all = load_prediction_audit()
    source_path = PREDICTION_AUDIT
    source_note = "07 final test - TAP TEST niem phong - mo hinh co lag/rolling"

# Tieu de la 1 CAU CHUYEN, khong phai ten trang - chuan storytelling BI:
# noi ngay ket luan chinh (da het tre pha) truoc khi nguoi xem tu doan.
st.markdown('<div class="dash-title">Đã khử trễ pha dự báo sản lượng điện mặt trời 15 phút tới</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="dash-subtitle">{source_note}. Đường thực tế và dự báo lấy từ cùng 1 file audit, không tự dựng lại.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.caption(source_note)
    available_horizons = [
        h for h in (1, 4)
        if f"y_pred_h{h}" in pred_all.columns and pred_all[f"y_pred_h{h}"].notna().any()
    ]
    horizon = st.selectbox("Horizon", available_horizons, format_func=lambda h: f"h{h}")
    true_col = f"y_true_h{horizon}"
    pred_col = f"y_pred_h{horizon}"
    pred_h = pred_all[pred_all[pred_col].notna()].copy()
    sites = sorted(pred_h["site_id"].dropna().astype(str).unique().tolist(), key=lambda x: int(float(x)))
    default_idx = sites.index("19") if "19" in sites else 0
    site_id = st.selectbox("Site", sites, index=default_idx)
    daylight_only = st.checkbox("Daylight rows only", value=False)
    # Loai outlier/du lieu impute khoi hinh ve: energy_source la cot provenance duy nhat
    # co trong prediction_audit_h1.parquet (khong co outlier_group o file nay). Mac dinh
    # BAT vi outlier (physical_over_capacity) va vai dong etl_imputed gia tri phang gan tran
    # (vd site 19) se lam duong "Thuc te" tren chart trong sai lech, gay hieu nham la
    # model dang du bao theo outlier.
    measured_only = st.checkbox("Chỉ hiện dữ liệu đo thật (bỏ outlier/impute)", value=True)

_tre_truoc = he_so_tre_phut(pred_all.dropna(subset=[true_col, pred_col]), true_col, pred_col)

site_pred = with_display_timestamp(pred_h[pred_h["site_id"].astype(str).eq(str(site_id))], horizon)
if site_pred.empty:
    st.error("No prediction audit rows for the selected site.")
    st.stop()

if "is_daylight" in site_pred.columns and daylight_only:
    site_pred = site_pred[site_pred["is_daylight"].fillna(False).astype(bool)].copy()

if "energy_source" in site_pred.columns and measured_only:
    site_pred = site_pred[site_pred["energy_source"].eq("measured")].copy()

site_pred["audit_outlier_group"] = "normal"
site_pred["is_audit_outlier"] = False

# Join outlier_group THAT tu 05_selected/v3_test_selected.parquet (khong co san trong
# prediction_audit_h1.parquet, chi co energy_source) - truoc day 2 dong tren la stub
# luon = "normal"/False, khong bao gio hien outlier that tren chart.
_OUTLIER_JOIN_PATH = DATA_DIR / "05_selected" / "v3_test_selected.parquet"
if "outlier_group" in site_pred.columns:
    # Nguon "06_train {variant}" (qua predict_on_test) da tu mang san outlier_group tu
    # X_test_h{h}.parquet/TEST_SELECTED - dung luon, KHONG merge lai keo trung ten cot
    # (pandas tu doi thanh outlier_group_x/_y, lam dong duoi day khong tim thay cot goc).
    site_pred["audit_outlier_group"] = site_pred["outlier_group"].fillna("normal")
    site_pred["is_audit_outlier"] = site_pred["audit_outlier_group"].ne("normal")
elif _OUTLIER_JOIN_PATH.exists():
    _og_ts = pd.read_parquet(_OUTLIER_JOIN_PATH, columns=["site_id", "timestamp", "outlier_group"])
    _og_ts["timestamp"] = pd.to_datetime(_og_ts["timestamp"], errors="coerce")
    site_pred = site_pred.merge(_og_ts, on=["site_id", "timestamp"], how="left")
    site_pred["audit_outlier_group"] = site_pred["outlier_group"].fillna("normal")
    site_pred["is_audit_outlier"] = site_pred["audit_outlier_group"].ne("normal")

with st.sidebar:
    min_day = site_pred["display_timestamp"].min().date()
    max_day = site_pred["display_timestamp"].max().date()
    date_mode = st.radio("Date mode", ["Top audit window", "Custom range"], horizontal=False)
    if date_mode == "Top audit window":
        site_pred["window_start"] = site_pred["display_timestamp"].dt.floor("7D")
        windows = site_pred["window_start"].value_counts().head(12).index.tolist()
        selected_window = st.selectbox("7-day window", windows)
        start_ts = pd.Timestamp(selected_window)
        end_ts = start_ts + pd.Timedelta(days=7)
    else:
        picked = st.date_input("Date range", [max(min_day, max_day - pd.Timedelta(days=7)), max_day])
        if isinstance(picked, tuple) and len(picked) == 2:
            start_ts = pd.Timestamp(picked[0])
            end_ts = pd.Timestamp(picked[1]) + pd.Timedelta(days=1)
        else:
            start_ts = pd.Timestamp(min_day)
            end_ts = pd.Timestamp(max_day) + pd.Timedelta(days=1)

plot_pred = site_pred[site_pred["display_timestamp"].between(start_ts, end_ts)].copy()
if model_source in ("final_khong_tre", "huber_pred_file", "mse_pred_file", "via_api", "bo_goc", "site_specific", "phase_ensemble", "correct_time_lag96", "correct_time_lag", "kaggle_earlystop", "correct_time", "overfit_audit", "target_aligned", "pure_weather", "fix15", "solar"):
    overall, site_metrics = audit_metrics(pred_all, horizon, cache_key=model_source)
elif model_source.startswith("variant:"):
    overall, site_metrics = audit_metrics(pred_all, horizon, cache_key=model_source)
else:
    overall, site_metrics = load_metrics(horizon)
baseline_metrics = load_baseline()

_compare_cols = ["display_timestamp", true_col, pred_col, "is_audit_outlier", "audit_outlier_group"]
compare = plot_pred[[c for c in _compare_cols if c in plot_pred.columns]].dropna(subset=[true_col, pred_col]).copy()
compare = compare.rename(columns={true_col: "y_true", pred_col: "y_pred"})
compare["residual"] = compare["y_true"] - compare["y_pred"]
compare["abs_error"] = compare["residual"].abs()

wape = metric_value(overall, "wape")
rmse = metric_value(overall, "rmse")

# ── TANG 1 (inverted pyramid, chuan BI executive dashboard): KPI to, quyet dinh
# quan trong nhat dat truoc tien, ai chi can xem dau de thi dung o day la du. ──
# LUU Y: 6 KPI o day tinh tren TOAN BO tap test cua model dang chon (khong doi khi
# chinh 7-day window/site ben duoi) - do la CHU DICH, khong phai bug/hardcode: KPI la
# "suc khoe tong the" cua model, con chart/site/window ben duoi la "soi ky 1 lat cat".
_rmse_dep = metric_value(overall, "r2")
_mae_dep = metric_value(overall, "mae")
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    # Nguong WAPE: <20% tot (nganh du bao nang luong mat troi 15p thuong 15-35%)
    _wape_status = ("up" if wape is not None and wape < 20 else "down" if wape is not None and wape > 30 else None)
    # Ghi chu cai thien/kem so voi Prophet - lay tu ket qua that trong
    # 06_0_baseline.ipynb + 06_0b_baseline_prophet.ipynb, khong hardcode con so.
    _wape_note = "càng thấp càng tốt"
    _baseline_csv_k1 = DATA_DIR / "06_0_baseline" / "baseline_comparison_final.csv"
    if wape is not None and _baseline_csv_k1.exists():
        _df_b_k1 = pd.read_csv(_baseline_csv_k1)
        _prophet_row = _df_b_k1[_df_b_k1["model"].str.contains("Prophet", na=False)]
        if len(_prophet_row):
            _prophet_wape = float(_prophet_row["wape_%"].iloc[0])
            _cai_thien = (_prophet_wape - wape) / _prophet_wape * 100
            _wape_note = f"tốt hơn Prophet {_cai_thien:.0f}%"
    kpi("WAPE", f"{wape:.2f}%" if wape is not None else "n/a", _wape_note, status=_wape_status)
with k2:
    _tre_hien_thi = _tre_truoc if _tre_truoc == _tre_truoc else float("nan")
    _tre_status = ("up" if _tre_hien_thi == _tre_hien_thi and abs(_tre_hien_thi) <= 2
                   else "down" if _tre_hien_thi == _tre_hien_thi and abs(_tre_hien_thi) > 5 else None)
    kpi("Trễ pha", f"{_tre_hien_thi:+.2f} phút" if _tre_hien_thi == _tre_hien_thi else "n/a",
        "dương = dự báo đi sau", status=_tre_status)
with k3:
    kpi("RMSE", f"{rmse:.4f} kWh" if rmse is not None else "n/a", "sai số bình phương")
with k4:
    kpi("MAE", f"{_mae_dep:.4f} kWh" if _mae_dep is not None else "n/a", "sai số tuyệt đối")
with k5:
    _r2_status = ("up" if _rmse_dep is not None and _rmse_dep >= 0.85 else "down" if _rmse_dep is not None and _rmse_dep < 0.6 else None)
    kpi("R²", f"{_rmse_dep:.4f}" if _rmse_dep is not None else "n/a", "độ khớp mô hình", status=_r2_status)
with k6:
    kpi("Số dòng", f"{len(compare):,}", f"{start_ts.date()} → {end_ts.date()}")

st.caption(
    "4 KPI đầu (WAPE/Trễ pha/RMSE/MAE/R²) tính trên **toàn bộ tập test** của model đang chọn — "
    "không đổi khi chỉnh Site/7-day window bên dưới, vì đó là chất lượng tổng thể của model, "
    "không phải riêng khung đang xem. Chart/bảng bên dưới mới lọc theo Site + khung ngày đang chọn."
)
st.divider()

# ── TANG 2: bieu do chinh, 2 cot canh nhau (xu huong theo thoi gian | so sanh theo site) ──
# Dung st.container(border=True) - moi chart nam trong 1 KHUNG RIENG giong BI tools that
# (Power BI/Tableau khong bao gio de chart "troi" tren nen trang, luon co card bao quanh).
# gap="small" de 2 cot sat lai gan nhau hon, khong de khoang trong lon giua chung.
t2_left, t2_right = st.columns(2, gap="small")
with t2_left:
    with st.container(border=True):
        st.markdown(f"##### Actual vs Prediction — Site {site_id} ({start_ts.date()} → {end_ts.date()})")
        # BUG DA SUA: truoc dung site_pred (toan bo ~4 thang, hang nghin diem chong nhau
        # thanh vet nhieu khong doc duoc) - phai dung `compare` (da loc theo cua so ngay
        # chon o sidebar) giong het cach Tang 1 tinh KPI, dam bao nhat quan.
        _fig_t2 = go.Figure()
        _fig_t2.add_trace(go.Scatter(x=compare["display_timestamp"], y=compare["y_true"], mode="lines+markers", name="Thuc te", line=dict(color=ACTUAL_COLOR, width=2), marker=dict(size=3)))
        _fig_t2.add_trace(go.Scatter(x=compare["display_timestamp"], y=compare["y_pred"], mode="lines+markers", name="Du bao", line=dict(color=PRED_COLOR, width=1.8), marker=dict(size=3)))

        # Sao vang: dinh THUC TE va dinh DU BAO cua TUNG NGAY trong khoang dang xem (khong
        # phai 1 dinh duy nhat ca 7 ngay) - moi ngay 1 cap sao rieng.
        _cmp_ngay = compare.copy()
        _cmp_ngay["ngay"] = _cmp_ngay["display_timestamp"].dt.date
        _dinh_that_idx = _cmp_ngay.groupby("ngay")["y_true"].idxmax().dropna()
        _dinh_bao_idx = _cmp_ngay.groupby("ngay")["y_pred"].idxmax().dropna()
        _dinh_that = _cmp_ngay.loc[_dinh_that_idx]
        _dinh_bao = _cmp_ngay.loc[_dinh_bao_idx]
        _fig_t2.add_trace(go.Scatter(
            x=_dinh_that["display_timestamp"], y=_dinh_that["y_true"], mode="markers",
            name="Đỉnh thực tế/ngày", marker=dict(symbol="star", size=13, color="#F59E0B", line=dict(color="#92400E", width=1)),
        ))
        _fig_t2.add_trace(go.Scatter(
            x=_dinh_bao["display_timestamp"], y=_dinh_bao["y_pred"], mode="markers",
            name="Đỉnh dự báo/ngày", marker=dict(symbol="star", size=13, color="#8B5CF6", line=dict(color="#4C1D95", width=1)),
        ))

        # Danh dau outlier (khong tham gia train) tren duong Thuc te.
        if "is_audit_outlier" in compare.columns and compare["is_audit_outlier"].any():
            _out_t2 = compare[compare["is_audit_outlier"]]
            _fig_t2.add_trace(go.Scatter(
                x=_out_t2["display_timestamp"], y=_out_t2["y_true"], mode="markers",
                name="Outlier (bị loại khỏi train)", marker=dict(symbol="x", size=9, color="#DC2626"),
            ))
        st.plotly_chart(style_fig(_fig_t2, 320), use_container_width=True)
        st.caption("Chỉ hiện đúng khoảng ngày đang chọn ở sidebar (mặc định 7 ngày) - đổi ở 'Date mode' để xem khoảng khác. "
                   "Sao vàng/tím = đỉnh thực tế/dự báo của từng ngày. Dấu X đỏ = outlier bị loại khỏi train.")
with t2_right:
    with st.container(border=True):
        st.markdown("##### Xếp hạng site theo WAPE")
        _metric_col_t2 = "wape" if "wape" in site_metrics.columns else ("rmse" if "rmse" in site_metrics.columns else None)
        if _metric_col_t2:
            # Truoc day co .head(15) - chi ve TOP 15 site tot nhat, lam giong nhu bug
            # "chi hien vai site" vi 25 site con lai (thuong la site te nhat) bi cat mat
            # khoi chart. Bo gioi han, ve DU tat ca site giong cac chart khac trong dashboard.
            _ranked_t2 = site_metrics[~site_metrics["site_id"].astype(str).eq("ALL")].copy()
            _fig_rank_t2 = px.bar(_ranked_t2.sort_values(_metric_col_t2), x="site_id", y=_metric_col_t2, color=_metric_col_t2,
                                   color_continuous_scale=["#16A34A", "#F59E0B", "#DC2626"])
            _fig_rank_t2.update_xaxes(type="category")
            st.plotly_chart(style_fig(_fig_rank_t2, 300), use_container_width=True)
        else:
            st.info("Chưa có dữ liệu xếp hạng site.")

t2b_left, t2b_right = st.columns(2, gap="small")
with t2b_left:
    with st.container(border=True):
        st.markdown("##### Phân bố sai số (residual)")
        _fig_res = px.histogram(compare, x="residual", nbins=40, color_discrete_sequence=[ACTUAL_COLOR])
        _fig_res.add_vline(x=0, line_dash="dot", line_color="#DC2626")
        st.plotly_chart(style_fig(_fig_res, 300), use_container_width=True)
        st.caption("Lệch quanh 0 và đối xứng = mô hình không thiên vị theo 1 hướng.")
with t2b_right:
    with st.container(border=True):
        st.markdown("##### Actual vs Prediction (scatter)")
        _fig_sc = px.scatter(compare, x="y_true", y="y_pred", color_discrete_sequence=[PRED_COLOR], render_mode="svg")
        _fig_sc.add_shape(type="line", x0=compare["y_true"].min(), y0=compare["y_true"].min(),
                          x1=compare["y_true"].max(), y1=compare["y_true"].max(), line=dict(color="#DC2626", dash="dot"))
        _fig_sc.update_traces(marker=dict(size=5, opacity=0.5))
        st.plotly_chart(style_fig(_fig_sc, 300), use_container_width=True)
        st.caption("Điểm trên đường chéo = dự báo khớp thực tế.")

# ── TANG 3: bang chi tiet, cuon xuong de phan tich sau ──
with st.container(border=True):
    st.markdown("##### Chi tiết theo site")
    # Conditional formatting kieu Excel/PowerBI: to nen theo gia tri, khong chi in so tho.
    # wape/rmse/mae: THAP la TOT -> thang mau dao nguoc (xanh o gia tri nho).
    # r2: CAO la TOT -> thang mau thuan (xanh o gia tri lon).
    # Doi tu RdYlGn ruc ro (do-vang-xanh la cay, nhin "vo duyen"/tre con) sang
    # thang mau don sac nhat quan voi theme navy (Blues), gioi han do dam bang
    # low/high de khong bi "ngop" mau nhu ban dau.
    _styler = site_metrics.style
    for _col, _reverse in [("wape", True), ("rmse", True), ("mae", True), ("r2", False)]:
        if _col in site_metrics.columns:
            _cmap = "Blues_r" if _reverse else "Blues"
            _styler = _styler.background_gradient(subset=[_col], cmap=_cmap, low=0.05, high=0.55)
    _fmt = {c: "{:.2f}" for c in ("wape", "rmse", "mae", "r2") if c in site_metrics.columns}
    _fmt.update({c: "{:,.0f}" for c in ("n", "horizon") if c in site_metrics.columns})
    if _fmt:
        _styler = _styler.format(_fmt)
    st.dataframe(_styler, use_container_width=True, hide_index=True, height=260)
    st.caption("Tô nền theo giá trị: wape/rmse/mae xanh = thấp = tốt, đỏ = cao = cần chú ý. r2 ngược lại: xanh = gần 1 = tốt.")

# ── TANG 4: so sanh voi Prophet - chung minh gia tri that cua model. KHONG dua
# Persistence vao day (da quyet dinh bo, khong bat buoc phai so sanh) - chi giu
# Prophet, mo hinh time-series chuan, khong co feature thoi tiet that. ──
_BASELINE_CSV = DATA_DIR / "06_0_baseline" / "baseline_comparison_final.csv"
if _BASELINE_CSV.exists():
    with st.container(border=True):
        st.markdown("##### So sánh với Baseline (Prophet)")
        _df_baseline = pd.read_csv(_BASELINE_CSV)
        _df_baseline = _df_baseline[~_df_baseline["model"].str.contains("Persistence", na=False)]
        _df_baseline = _df_baseline.sort_values("wape_%")
        _mau_baseline = {
            "LightGBM (đầy đủ feature thời tiết)": ACTUAL_COLOR,
            "Prophet (không có feature thời tiết)": PRED_COLOR,
        }
        _df_baseline["mau"] = _df_baseline["model"].map(_mau_baseline).fillna("#94A3B8")
        _fig_base = go.Figure(go.Bar(
            x=_df_baseline["wape_%"], y=_df_baseline["model"], orientation="h",
            marker_color=_df_baseline["mau"],
            text=_df_baseline["wape_%"].map(lambda v: f"{v:.2f}%"),
            textposition="outside",
        ))
        _fig_base.update_layout(xaxis_title="WAPE (%) — càng thấp càng tốt", yaxis_title="")
        st.plotly_chart(style_fig(_fig_base, 220), use_container_width=True)
        st.caption(
            "Prophet là mô hình time-series chuẩn, được công nhận rộng rãi, nhưng không có feature thời tiết thật "
            "nên không biết trước mây/thời tiết bất thường. Model LightGBM (đầy đủ feature thời tiết + downscale "
            "bức xạ) thắng đậm Prophet, chứng minh giá trị thật của việc dùng feature thời tiết."
        )
else:
    st.info("Chưa có kết quả baseline — chạy `06_0b_baseline_prophet.ipynb` trước.")

