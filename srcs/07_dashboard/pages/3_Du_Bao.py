"""Trang 3 — Dự báo tới & What-if.

VI SAO TACH RIENG MOT TRANG (khong nhet vao Time Series hay SHAP)
-----------------------------------------------------------------
Trang Time Series toan so DO DUOC tren tap test (WAPE 17,64%, R² 0,9319). Dat du
bao 14 ngay canh do thi nguoi xem se doc 17,64% thanh "do chinh xac cua du bao 14
ngay" — SAI, vi de quy tich luy sai so. Tron "da do duoc" voi "se xay ra" tren cung
mot trang la cho de hieu nham nhat.

Du bao va What-if di chung vi CUNG DUNG MOT LAN KEO THOI TIET Open-Meteo. Tach ra
la phai goi mang hai lan cho cung mot khoang thoi gian.

Toan bo logic nam o forecast_service.py — trang nay chi ve.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard_common import load_shared_css
from dashboard_data import ACTUAL_COLOR, GRID_COLOR, PRED_COLOR, PROPHET_COLOR

load_shared_css()

BIEN_THOI_TIET = {
    "buc_xa": ("shortwave_radiation", "direct_normal_irradiance", "diffuse_solar_radiation"),
    "nhiet_do": ("temperature_c",),
    "may": ("cloud_cover_total", "cloud_cover_low"),
}


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


def kpi(label: str, value: str, note: str = "", status: str | None = None) -> None:
    _cls = f"kpi-note {status}" if status in ("up", "down") else "kpi-note"
    _icon = "▲" if status == "up" else ("▼" if status == "down" else "")
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="{_cls}">{_icon} {note}</div></div>',
        unsafe_allow_html=True,
    )


@st.cache_resource
def _dich_vu():
    from forecast_service import lay_dich_vu

    return lay_dich_vu()


@st.cache_data(ttl=1800, show_spinner=False)
def _thoi_tiet(site_id: int, so_ngay: int) -> pd.DataFrame:
    dv = _dich_vu()
    md = dv.sieu_du_lieu()
    md = md[md["site_id"] == site_id].iloc[0]
    return dv.lay_thoi_tiet(float(md["latitude"]), float(md["longitude"]), so_ngay)


@st.cache_data(ttl=1800, show_spinner=False)
def _du_bao_de_quy(site_id: int, so_ngay: int) -> pd.DataFrame:
    return _dich_vu().du_bao(site_id=site_id, so_ngay=so_ngay)


@st.cache_data(ttl=1800, show_spinner=False)
def _du_bao_mot_buoc(site_id: int, so_ngay: int, dieu_chinh_key: tuple) -> pd.DataFrame:
    """dieu_chinh_key la tuple de cache duoc (dict khong hashable)."""
    return _dich_vu().du_bao_mot_buoc(
        site_id=site_id, so_ngay=so_ngay, dieu_chinh=dict(dieu_chinh_key) or None)


# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="dash-title">Dự báo sản lượng những ngày tới</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="dash-subtitle">Thời tiết lấy trực tiếp từ Open-Meteo theo toạ độ thật '
    'của trạm, đưa qua đúng chuỗi đặc trưng của pipeline rồi vào mô hình vô địch.</div>',
    unsafe_allow_html=True,
)

dv = _dich_vu()
st.sidebar.markdown("### 🔍 Bộ lọc")
with st.sidebar:
    site_id = st.selectbox("Trạm", dv.danh_sach_tram(), index=0)
    so_ngay = st.slider("Số ngày dự báo", 1, 14, 7)
    st.caption("Dự báo đệ quy mất khoảng 1 giây mỗi ngày.")

with st.spinner(f"Đang kéo thời tiết Open-Meteo và dự báo {so_ngay} ngày…"):
    tt = _thoi_tiet(site_id, so_ngay)
    db = _du_bao_de_quy(site_id, so_ngay)

theo_ngay = (db.assign(ngay=db["plot_timestamp"].dt.date)
             .groupby("ngay")
             .agg(tong_kwh=("y_pred_kwh", "sum"), dinh_kwh=("y_pred_kwh", "max"))
             .reset_index())
tt_ngay = (tt.assign(ngay=tt["timestamp"].dt.date)
           .groupby("ngay")
           .agg(may_tb=("cloud_cover_total", "mean"),
                buc_xa_dinh=("shortwave_radiation", "max"),
                nhiet_do_tb=("temperature_c", "mean"))
           .reset_index())
theo_ngay = theo_ngay.merge(tt_ngay, on="ngay", how="left")

k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi("Tổng dự báo", f"{db['y_pred_kwh'].sum():,.0f} kWh", f"{so_ngay} ngày tới")
with k2:
    _i = theo_ngay["tong_kwh"].idxmax()
    kpi("Ngày cao nhất", f"{theo_ngay.loc[_i, 'tong_kwh']:,.0f} kWh",
        str(theo_ngay.loc[_i, "ngay"]), status="up")
with k3:
    _i = theo_ngay["tong_kwh"].idxmin()
    kpi("Ngày thấp nhất", f"{theo_ngay.loc[_i, 'tong_kwh']:,.0f} kWh",
        str(theo_ngay.loc[_i, "ngay"]), status="down")
with k4:
    kpi("Số bước đệ quy", f"{len(db):,}", "mỗi bước 15 phút")

st.warning(
    "**Con số WAPE 17,64% ở trang Time Series KHÔNG phải độ chính xác của dự báo này.** "
    "Chỉ số đó đo năng lực dự báo **một bước** (15 phút tới) trên tập test. Dự báo nhiều "
    "ngày được thực hiện bằng đệ quy — giá trị vừa dự báo trở thành đầu vào `lag_4`/"
    "`rolling_*` cho bước kế tiếp — nên sai số tích lũy dần và độ tin cậy giảm theo "
    "khoảng cách. Ngày đầu đáng tin hơn hẳn ngày thứ mười bốn."
)

# ── Chart: sản lượng dự báo + thời tiết ──────────────────────────────────────
with st.container(border=True):
    st.markdown(f"##### Sản lượng dự báo theo bước 15 phút — Trạm {site_id}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=db["plot_timestamp"], y=db["y_pred_kwh"],
                             mode="lines", name="Sản lượng dự báo (kWh)",
                             line=dict(color=PRED_COLOR, width=1.8),
                             fill="tozeroy", fillcolor="rgba(217,130,43,0.12)"))
    fig.add_trace(go.Scatter(x=tt["timestamp"], y=tt["shortwave_radiation"],
                             mode="lines", name="Bức xạ sóng ngắn (W/m²)",
                             line=dict(color=ACTUAL_COLOR, width=1.2, dash="dot"),
                             yaxis="y2"))
    fig.update_layout(yaxis2=dict(overlaying="y", side="right",
                                  title="W/m²", showgrid=False))
    st.plotly_chart(style_fig(fig, 340), width="stretch")
    st.caption("Đường cam là sản lượng dự báo, đường chấm chàm là bức xạ Open-Meteo. "
               "Hai đường đi cùng nhịp chính là bằng chứng mô hình đang bám thời tiết.")

with st.container(border=True):
    st.markdown("##### Tổng hợp theo ngày — đối chiếu với thời tiết dự báo")
    b = theo_ngay.rename(columns={
        "ngay": "Ngày", "tong_kwh": "Tổng (kWh)", "dinh_kwh": "Đỉnh (kWh)",
        "may_tb": "Mây TB (%)", "buc_xa_dinh": "Bức xạ đỉnh (W/m²)",
        "nhiet_do_tb": "Nhiệt độ TB (°C)"})
    b["Ngày"] = b["Ngày"].astype(str)
    st.dataframe(
        b.style.background_gradient(subset=["Tổng (kWh)"], cmap="Blues", low=0.1, high=0.6)
        .background_gradient(subset=["Mây TB (%)"], cmap="Greys", low=0.1, high=0.5)
        .format({"Tổng (kWh)": "{:,.1f}", "Đỉnh (kWh)": "{:.2f}", "Mây TB (%)": "{:.0f}",
                 "Bức xạ đỉnh (W/m²)": "{:.0f}", "Nhiệt độ TB (°C)": "{:.1f}"}),
        width="stretch", hide_index=True, height=min(38 * (len(b) + 1) + 8, 420))
    st.caption("Ngày nhiều mây cho tổng thấp, ngày trời quang cho tổng cao — quan hệ này "
               "giữ được suốt chân trời dự báo.")

# ══════════════════════════════════════════════════════════════════════════════
#  What-if
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="dash-title">What-if — nếu điều kiện khác đi thì sao?</div>',
            unsafe_allow_html=True)

st.info(
    "**Phần này chạy ở chế độ một bước, không đệ quy.** Bốn trong mười đặc trưng quan "
    "trọng nhất là `lag_4` và `rolling_*_4` — sản lượng gần đây. Khi đệ quy, chúng lấy từ "
    "chính đầu ra của mô hình, tạo vòng tự neo làm tắt tín hiệu thời tiết: đo thực tế trên "
    "trạm 1, bức xạ +20% cho **+7,33%** ở chế độ một bước nhưng chỉ **+0,47%** khi đệ quy "
    "7 ngày, có ngày còn đổi dấu. Dùng số đệ quy ở đây sẽ ra biểu đồ gần như phẳng và "
    "người đọc kết luận sai rằng mô hình không quan tâm thời tiết."
)

c1, c2 = st.columns([1, 2], gap="medium")
with c1:
    st.markdown("##### Điều chỉnh")
    buc_xa = st.slider("Bức xạ mặt trời", 0.5, 1.5, 1.0, 0.05,
                       help="Hệ số nhân lên bức xạ sóng ngắn, trực xạ và tán xạ.")
    nhiet_do = st.slider("Nhiệt độ", 0.5, 1.5, 1.0, 0.05,
                         help="Nhiệt độ cao làm giảm hiệu suất tấm pin.")
    may = st.slider("Độ mây", 0.0, 2.0, 1.0, 0.05,
                    help="Hệ số nhân lên độ mây tổng và mây thấp.")
    quy_mo = st.slider("Quy mô hệ thống (số tấm pin)", 0.5, 2.0, 1.0, 0.05,
                       help="Nhân số tấm pin — ảnh hưởng tuyến tính lên công suất trạm.")
    st.caption(
        "Không có thanh **tốc độ gió**: `wind_speed` không nằm trong 54 đặc trưng của mô "
        "hình, mọi hệ số nhân đều cho đúng 0,00% thay đổi. Bày một nút không làm gì là "
        "đánh lừa người dùng."
    )

dieu_chinh = {}
for cot in BIEN_THOI_TIET["buc_xa"]:
    dieu_chinh[cot] = buc_xa
for cot in BIEN_THOI_TIET["nhiet_do"]:
    dieu_chinh[cot] = nhiet_do
for cot in BIEN_THOI_TIET["may"]:
    dieu_chinh[cot] = may

with st.spinner("Đang tính kịch bản…"):
    goc = _du_bao_mot_buoc(site_id, so_ngay, ())
    kb = _du_bao_mot_buoc(site_id, so_ngay, tuple(sorted(dieu_chinh.items())))

# Quy mo he thong nhan tuyen tinh len san luong: cong suat tram ty le voi so tam pin.
t_goc = float(goc["y_pred_kwh"].sum())
t_kb = float(kb["y_pred_kwh"].sum()) * quy_mo

with c2:
    st.markdown("##### Kết quả")
    m1, m2, m3 = st.columns(3)
    with m1:
        kpi("Hiện tại", f"{t_goc:,.0f} kWh", f"{so_ngay} ngày")
    with m2:
        kpi("Kịch bản", f"{t_kb:,.0f} kWh", "sau điều chỉnh")
    with m3:
        _pc = (t_kb - t_goc) / t_goc * 100 if t_goc else 0.0
        kpi("Thay đổi", f"{_pc:+.2f}%", f"{t_kb - t_goc:+,.0f} kWh",
            status="up" if _pc > 0.05 else "down" if _pc < -0.05 else None)

    fig = go.Figure(go.Bar(
        x=[t_goc, t_kb], y=["Hiện tại", "Kịch bản"], orientation="h",
        marker_color=[PROPHET_COLOR, PRED_COLOR],
        text=[f"{t_goc:,.0f} kWh", f"{t_kb:,.0f} kWh"], textposition="outside",
    ))
    fig.update_layout(xaxis_title="Tổng sản lượng (kWh)", yaxis_title="")
    st.plotly_chart(style_fig(fig, 220), width="stretch")

# ── Quét độ nhạy từng biến ───────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("##### Quét độ nhạy — mỗi biến thay đổi riêng lẻ")
    if st.button("Chạy quét độ nhạy", help="Chạy lại mô hình cho từng mức của từng biến"):
        muc = [0.7, 0.85, 1.0, 1.15, 1.3]
        dong = []
        thanh = st.progress(0.0)
        tong_buoc = len(muc) * len(BIEN_THOI_TIET)
        i = 0
        for ten, cot_list in BIEN_THOI_TIET.items():
            for m in muc:
                dc = {c: m for c in cot_list}
                r = _du_bao_mot_buoc(site_id, so_ngay, tuple(sorted(dc.items())))
                t = float(r["y_pred_kwh"].sum())
                dong.append({"Biến": ten, "Hệ số": m, "Tổng (kWh)": t,
                             "Thay đổi (%)": (t - t_goc) / t_goc * 100 if t_goc else np.nan})
                i += 1
                thanh.progress(i / tong_buoc)
        thanh.empty()
        d = pd.DataFrame(dong)
        nhan = {"buc_xa": "Bức xạ", "nhiet_do": "Nhiệt độ", "may": "Độ mây"}
        fig = go.Figure()
        for ten, g in d.groupby("Biến"):
            fig.add_trace(go.Scatter(x=g["Hệ số"], y=g["Thay đổi (%)"], mode="lines+markers",
                                     name=nhan.get(ten, ten)))
        fig.add_hline(y=0, line_dash="dot", line_color="#94A3B8")
        fig.update_layout(xaxis_title="Hệ số nhân áp lên biến",
                          yaxis_title="Thay đổi sản lượng (%)")
        st.plotly_chart(style_fig(fig, 320), width="stretch")
        d["Biến"] = d["Biến"].map(nhan).fillna(d["Biến"])
        st.dataframe(d.style.format({"Hệ số": "{:.2f}", "Tổng (kWh)": "{:,.1f}",
                                     "Thay đổi (%)": "{:+.2f}"}),
                     width="stretch", hide_index=True, height=300)
        st.caption(
            "Đường dốc lên nghĩa là mô hình phản ứng đúng chiều với biến đó. Bức xạ thường "
            "bất đối xứng — giảm gây thiệt nhiều hơn tăng mang lại lợi, vì chỉ số trời quang "
            "bị chặn ở 1,5 và sản lượng còn bị chặn bởi trần công suất trạm."
        )
    else:
        st.caption("Bấm nút trên để quét 5 mức × 3 biến. Mỗi lần quét chạy lại mô hình 15 lần.")

st.caption(
    "**Giới hạn diễn giải:** đây là phân tích độ nhạy của mô hình, không phải dự báo thời "
    "tiết. Nhân bức xạ lên 1,3 lần không có nghĩa trời sẽ nắng hơn 30%; nó trả lời câu hỏi "
    "\"nếu bức xạ cao hơn 30% thì mô hình nói gì\"."
)
