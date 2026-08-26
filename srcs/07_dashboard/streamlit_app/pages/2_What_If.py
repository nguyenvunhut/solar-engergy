"""Trang Mo phong What-If toi uu hoa hieu suat — nhanh BI Mart.

Tang FRONTEND: chi trinh bay, khong chua nghiep vu. Moi phep tinh goi sang
bimart.api.services.

Bo cuc:
    1. Tong quan      — chi so hien tai; doi ngay khi tich hang muc
    2. Bang tong hop  — 7 hang muc: dien them, tien them, tien bo ra, hoan von
    3. Chi tiet       — so xuong tung hang muc: co che, tac dong, cong thuc

Chay: cd srcs/07_dashboard && streamlit run streamlit_app/app.py
"""
from __future__ import annotations

from api.bimart.core import config as cfg
from api.bimart.services import phan_ra
from api.bimart.services.whatif import chay_kich_ban
from dashboard_common import header_bao_cao, load_shared_css
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

LUC, DO, XANH, LUOI = "#0E9F6E", "#DC2626", "#6366F1", "#D9DEE7"

st.set_page_config(page_title="What-If Tối ưu hoá | BI Mart",
                   layout="wide", initial_sidebar_state="expanded")
load_shared_css()
header_bao_cao("Mô phỏng What-If — Tối ưu hoá hiệu suất & tài chính",
               "42 trạm áp mái La Trobe · 2.428 kWp · 5 khuôn viên · dữ liệu 2020–2022",
               "BI MART")

st.markdown("""
<style>
/* Checkbox sidebar -> the bam duoc. Streamlit dung emotion-css do uu tien cao nen
   moi quy tac deu can !important; o vuong duoc an bang nhieu bien the selector vi
   cau truc DOM khac nhau giua cac ban Streamlit. */
section[data-testid="stSidebar"] div[data-testid="stCheckbox"]{
  margin:0 0 7px!important;
}
section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label{
  position:relative!important;display:flex!important;align-items:center!important;
  gap:0!important;width:100%!important;
  padding:10px 13px!important;border:1px solid #E4E4F0!important;border-radius:10px!important;
  background:#FCFCFE!important;cursor:pointer!important;
  transition:background .13s ease,border-color .13s ease,transform .13s ease!important;
}
section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label:hover{
  background:#EEF0FB!important;border-color:#A5ACEC!important;transform:translateX(2px);
}
/* An o vuong ma khong dung toi khoi chu: chi giau nhung phan tu con truc tiep
   vua KHONG phai khoi chu, vua KHONG chua khoi chu ben trong. Nho vay khong can
   biet truoc Streamlit long the nao. Neu trinh duyet khong ho tro :has() thi ca
   quy tac bi bo qua — o vuong hien lai, chu van con nguyen. */
section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label>*:not([data-testid="stMarkdownContainer"]):not(:has([data-testid="stMarkdownContainer"])){
  position:absolute!important;width:1px!important;height:1px!important;
  padding:0!important;margin:0!important;border:0!important;overflow:hidden!important;
  clip:rect(0 0 0 0)!important;white-space:nowrap!important;opacity:0!important;
}
section[data-testid="stSidebar"] div[data-testid="stCheckbox"] p{
  font-size:.88rem!important;line-height:1.38!important;color:#374151!important;
  margin:0!important;font-weight:650!important;
}
/* Trang thai da tich */
section[data-testid="stSidebar"] div[data-testid="stCheckbox"]:has(input:checked) label{
  background:#6366F1!important;border-color:#6366F1!important;
  box-shadow:0 1px 6px rgba(99,102,241,.28)!important;
}
section[data-testid="stSidebar"] div[data-testid="stCheckbox"]:has(input:checked) p{
  color:#FFFFFF!important;font-weight:700!important;
}
section[data-testid="stSidebar"] div[data-testid="stCheckbox"]:has(input:checked) label:hover{
  background:#5457D8!important;border-color:#5457D8!important;
}
/* Dai the tong quan: dung lai .kpi-card cua style.css de dong bo voi trang ML,
   chi bo sung dong "co so" va co chu cho phan chenh lech. */
details summary p, div[data-testid="stExpander"] summary p{
  font-weight:650!important;color:#1F2937;
}
.tq{display:flex;gap:12px;flex-wrap:wrap;margin:2px 0 8px}
.tq>div{flex:1 1 250px;min-width:250px}
.kpi-doi{display:grid;grid-template-columns:1fr auto 1fr;gap:6px;
         align-items:center;margin-top:7px}
.kpi-doi>div{min-width:0}
.kpi-mui{color:#A5ACEC;font-size:1.15rem;font-weight:800;line-height:1;padding:0 1px}
.kpi-cot-nhan{color:#98A2B3;font-size:.62rem;font-weight:700;text-transform:uppercase;
              letter-spacing:.03em;margin-bottom:1px}
.kpi-cot-tri{color:#1F2937;font-size:1.0rem;font-weight:760;line-height:1.25;
             white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kpi-cot-tri.sim{color:#4F46E5}
.kpi-delta{font-size:.98rem;font-weight:700;margin-top:4px}
.kpi-delta.up{color:#16A34A}.kpi-delta.zero{color:#98A2B3}
</style>""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Hạng mục cải tiến")
    bat = [ma for ma, v in sorted(cfg.HANG_MUC_CAI_TIEN.items(), key=lambda x: x[1]["stt"])
           if st.checkbox(f"{v['stt']}. {v['ten']}", value=False, key=f"cb_{ma}")]
    st.divider()
    nam = st.selectbox("Biểu giá NEM Victoria", [None, 2020, 2021, 2022],
                       format_func=lambda n: "Trung bình 3 năm" if n is None else f"Năm {n}")
    tien = st.radio("Đơn vị tiền", list(cfg.TIEN_TE), horizontal=True, index=0)
    _t = cfg.TIEN_TE[tien]
    st.caption(f"{_t['ten']} — quy đổi từ AUD, tỷ giá {_t['ty_gia']:,g}"
               if tien != "AUD" else f"{_t['ten']} — đơn vị gốc của tài liệu")

kq = chay_kich_ban(bat=bat, nam=nam)
c, s, d = kq["co_so"], kq["sau_cai_tien"], kq["delta"]
co_chon = bool(bat)


def tien_str(aud: float) -> str:
    return cfg.dinh_dang_tien(aud, tien)


def tien_gon(aud: float) -> str:
    """Rut gon cho the KPI: tren mot trieu thi hien dang 'A$ 1,16 M'."""
    t = cfg.TIEN_TE[tien]
    v = cfg.quy_doi(aud, tien)
    if abs(v) >= 1e9:
        return f"{v/1e9:,.2f}".replace(".", ",") + f" tỷ {t['ky_hieu']}"
    if abs(v) >= 1e6:
        return f"{v/1e6:,.2f}".replace(".", ",") + f" M {t['ky_hieu']}"
    return f"{v:,.0f} {t['ky_hieu']}"


def the(nhan: str, co_so: str, mo_phong: str, delta: str) -> str:
    """The KPI: hien nay -> sau cai tien, chenh lech nam phia duoi."""
    cls = "up" if co_chon else "zero"
    return (f'<div><div class="kpi-card">'
            f'<div class="kpi-label">{nhan}</div>'
            f'<div class="kpi-doi">'
            f'<div><div class="kpi-cot-nhan">Hiện nay</div>'
            f'<div class="kpi-cot-tri">{co_so}</div></div>'
            f'<div class="kpi-mui">&#8594;</div>'
            f'<div><div class="kpi-cot-nhan">Sau cải tiến</div>'
            f'<div class="kpi-cot-tri sim">{mo_phong}</div></div>'
            f'</div>'
            f'<div class="kpi-delta {cls}">{delta}</div>'
            f'</div></div>')


def style_fig(f: go.Figure, h: int = 340) -> go.Figure:
    f.update_layout(template="plotly_white", paper_bgcolor="#FFF", plot_bgcolor="#FFF",
                    height=h, margin=dict(l=12, r=12, t=44, b=18),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                    xaxis=dict(gridcolor=LUOI, zeroline=False),
                    yaxis=dict(gridcolor=LUOI, zeroline=False),
                    font=dict(color="#1F2937", size=12))
    return f


# ══ 1. TONG QUAN ═════════════════════════════════════════════════════════════
st.markdown("### Tổng quan")
st.caption("Chưa tích hạng mục nào thì đây là hiện trạng vận hành. Mỗi hạng mục được "
           "tích sẽ cộng thêm phần đóng góp của nó vào các chỉ số dưới đây."
           if not co_chon else
           f"Đang áp dụng **{len(bat)}/7** hạng mục cải tiến.")

st.markdown('<div class="tq">'
    + the("Điện làm ra", f"{c['e_kwh']/1e6:.2f} GWh", f"{s['e_kwh']/1e6:.2f} GWh",
          f"+{d['e_kwh']:,.0f} kWh ({d['ty_le_%']:+.2f}%)" if co_chon else "chưa thay đổi")
    + the("Hiệu suất thực tế (PR)", f"{c['pr_%']:.2f}%", f"{s['pr_%']:.2f}%",
          f"{s['pr_%']-c['pr_%']:+.2f} điểm" if co_chon else "chưa thay đổi")
    + the("Mức chạy so với công suất lắp (CF)", f"{c['cf_%']:.2f}%", f"{s['cf_%']:.2f}%",
          f"{s['cf_%']-c['cf_%']:+.2f} điểm" if co_chon else "chưa thay đổi")
    + the("Tiền bán điện", tien_gon(c["revenue_aud"]), tien_gon(s["revenue_aud"]),
          f"+{tien_str(d['revenue_aud'])}/năm" if co_chon else "chưa thay đổi")
    + the("CO₂ giảm được", f"{c['co2_kg']/1000:,.0f} tấn", f"{s['co2_kg']/1000:,.0f} tấn",
          f"+{d['co2_kg']/1000:,.0f} tấn/năm" if co_chon else "chưa thay đổi")
    + '</div>', unsafe_allow_html=True)

g1, g2 = st.columns([1.25, 1])
with g1:
    with st.container(border=True):
        st.markdown("##### Điện tăng thêm nhờ từng hạng mục")
        b = pd.DataFrame([h for h in kq["hang_muc"] if h["bat"]])
        ten = ["Cơ sở"] + ([f"{r.stt}. {r.ten[:24]}" for r in b.itertuples()] if len(b) else []) + ["Simulation"]
        gt = [c["e_kwh"]] + (b["delta_kwh"].tolist() if len(b) else []) + [0]
        f = go.Figure(go.Waterfall(orientation="v",
                                   measure=["absolute"] + ["relative"]*len(b) + ["total"],
                                   x=ten, y=gt,
                                   text=[f"{v:,.0f}" if v else "" for v in gt],
                                   textposition="outside",
                                   connector=dict(line=dict(color=LUOI)),
                                   increasing=dict(marker_color=LUC),
                                   totals=dict(marker_color=XANH)))
        f.update_layout(yaxis_title="kWh/năm", xaxis_tickangle=-25)
        st.plotly_chart(style_fig(f, 380), width="stretch")
with g2:
    with st.container(border=True):
        st.markdown("##### Điện bị mất — phần lấy lại được và phần còn lại")
        t = pd.DataFrame(kq["ton_that"])
        t["da_khu_%"] = t["truoc_%"] - t["sau_%"]
        f2 = go.Figure()
        # Cot xep chong: tong do dai = ton that ban dau. Phan xanh la da khu, phan do
        # la con lai. Cach nay thay ro ca truong hop khu hoan toan (sau = 0), thu ma
        # bieu do cot ghep khong hien duoc vi cot dai bang 0.
        f2.add_bar(y=t["ten"], x=t["sau_%"], orientation="h", name="Tổn thất còn lại",
                   marker_color=DO, opacity=.9,
                   text=[f"{v:.2f}%" if v > 0.15 else "" for v in t["sau_%"]],
                   textposition="inside", insidetextanchor="middle")
        f2.add_bar(y=t["ten"], x=t["da_khu_%"], orientation="h", name="Cắt giảm được",
                   marker_color=LUC,
                   text=[f"−{v:.2f}%" if v > 0.15 else "" for v in t["da_khu_%"]],
                   textposition="inside", insidetextanchor="middle")
        f2.update_layout(barmode="stack", xaxis_title="% điện bị mất so với sản lượng cả năm",
                         yaxis=dict(autorange="reversed"))
        for i, r in t.iterrows():
            f2.add_annotation(x=r["truoc_%"], y=r["ten"], text=f"  {r['truoc_%']:.2f}%",
                              showarrow=False, xanchor="left",
                              font=dict(size=11, color="#6B7280"))
        st.plotly_chart(style_fig(f2, 380), width="stretch")

# ══ 2. BANG TONG HOP ═════════════════════════════════════════════════════════
st.markdown("### Bảy hạng mục cải tiến")
with st.container(border=True):
    bb = pd.DataFrame(kq["hang_muc"]).sort_values("stt")
    hien = pd.DataFrame({
        "Áp dụng": bb["bat"].map({True: "Có", False: "Không"}),
        "Hạng mục": bb["ten"],
        "Tăng sản lượng": bb["delta_kwh"] / cfg.CO_SO["e_baseline_kwh"],
        "Điện thêm (kWh/năm)": bb["delta_kwh"],
        f"Tiền thêm ({tien}/năm)": bb["delta_revenue_aud"].map(
            lambda v: cfg.quy_doi(v, tien)),
        f"Tiền bỏ ra ({tien})": bb["capex_aud"].map(
            lambda v: None if pd.isna(v) else cfg.quy_doi(v, tien)),
        "Bao lâu lấy lại vốn": bb["payback"],
    })
    st.dataframe(
        hien.style.format({"Tăng sản lượng": "+{:.2%}",
                           "Điện thêm (kWh/năm)": "{:,.0f}",
                           f"Tiền thêm ({tien}/năm)": "{:,.0f}",
                           f"Tiền bỏ ra ({tien})":
                               lambda v: "—" if pd.isna(v) else f"{v:,.0f}"})
            .background_gradient(subset=["Điện thêm (kWh/năm)"], cmap="Blues",
                                 low=.1, high=.6)
            .set_properties(subset=["Hạng mục"], **{"font-weight": "650"}),
        width="stretch", hide_index=True)
    st.caption("Cột *Tăng sản lượng* tính chung một mẫu số — lấy phần điện tăng thêm chia "
               f"cho sản lượng cả năm hiện nay ({cfg.CO_SO['e_baseline_kwh']:,.0f} kWh), "
               "nên bảy hạng mục so sánh được trực tiếp với nhau.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng tiền phải bỏ ra", tien_str(d["capex_aud"]) if co_chon else "—")
    m2.metric("Tiền thu thêm", f"{tien_str(d['revenue_aud'])}/năm" if co_chon else "—")
    m3.metric("Trung bình bao lâu lấy lại vốn",
              f"{d['payback_nam']:.2f} năm" if d.get("payback_nam") else "—")

# ══ 3. CHI TIET TUNG HANG MUC ════════════════════════════════════════════════
st.markdown("### Chi tiết từng hạng mục")
st.caption("Bảng thông số lấy từ tài liệu; biểu đồ dựng từ dữ liệu vận hành thực tế "
           "của 42 trạm (2020–2022).")

for h in sorted(kq["hang_muc"], key=lambda x: x["stt"]):
    ma = h["ma"]
    ct = cfg.CHI_TIET_HANG_MUC[ma]
    nhan = "đang áp dụng" if h["bat"] else "chưa áp dụng"
    with st.expander(f"**Hạng mục {h['stt']} — {ct['tieu_de']}**  ·  {nhan}", expanded=False):

        st.markdown("**Bảng thông số**")
        st.dataframe(pd.DataFrame([
            {"Chỉ tiêu": "Tăng được bao nhiêu", "Giá trị": h["hieu_suat"]},
            {"Chỉ tiêu": "Điện lấy lại được", "Giá trị": f"{h['delta_kwh']:,.0f} kWh/năm"},
            {"Chỉ tiêu": "Tiền thu thêm mỗi năm", "Giá trị": f"{tien_str(h['delta_revenue_aud'])}/năm"},
            {"Chỉ tiêu": "Tiền phải bỏ ra",
             "Giá trị": tien_str(h["capex_aud"]) if h["capex_aud"]
                        else "Gộp vào đợt thay tấm pin"},
            {"Chỉ tiêu": "Bao lâu lấy lại vốn", "Giá trị": h["payback"]},
        ]), width="stretch", hide_index=True)

        st.markdown(f"**Cơ chế.** {ct['co_che']}")
        st.markdown(f"**Tác động chỉ số.** {ct['tac_dong']}")

        if ma == "bess":
            c_l, c_r = st.columns(2)
            with c_l:
                st.markdown("**Phân bổ theo khuôn viên**")
                cp = phan_ra.theo_campus("bess")
                f = go.Figure(go.Bar(x=cp["kwh"], y=cp["campus"], orientation="h",
                                     marker_color=XANH,
                                     text=[f"{v:,.0f} kWh" for v in cp["kwh"]],
                                     textposition="auto"))
                f.update_layout(xaxis_title="kWh/năm", yaxis=dict(autorange="reversed"))
                st.plotly_chart(style_fig(f, 280), width="stretch")
                st.dataframe(pd.DataFrame({
                    "Khuôn viên": cp["campus"], "Số trạm": cp["so_tram"],
                    "Tỷ trọng": (cp["ty_trong"] * 100).round(1),
                    "kWh/năm": cp["kwh"].round(0)})
                    .style.format({"Tỷ trọng": "{:.1f}%", "kWh/năm": "{:,.0f}"}),
                    width="stretch", hide_index=True)
            with c_r:
                st.markdown("**Tổn thất cắt ngọn theo tháng (kWh, không phải tỷ lệ)**")
                t = phan_ra.clip_ton_that_thang()
                f2 = go.Figure()
                f2.add_bar(x=t["ten"], y=t["thu_hoi_kwh"], name="Thu hồi qua BESS",
                           marker_color=LUC)
                f2.add_bar(x=t["ten"], y=t["con_lai_kwh"], name="Còn mất", marker_color=DO)
                f2.add_scatter(x=t["ten"], y=t["buc_xa"], name="Bức xạ TB (W/m²)",
                               yaxis="y2", mode="lines+markers", line=dict(color="#6B7280"))
                f2.update_layout(barmode="stack", yaxis_title="kWh",
                                 yaxis2=dict(title="W/m²", overlaying="y", side="right",
                                             showgrid=False))
                st.plotly_chart(style_fig(f2, 300), width="stretch")

        elif ma == "tilt":
            st.markdown("**Cấu thành sản lượng theo mùa**")
            t = phan_ra.tilt_theo_mua()
            f = go.Figure(go.Bar(x=t["mua"], y=t["kwh"],
                                 marker_color=[LUC if v > 0 else DO for v in t["kwh"]],
                                 text=[f"{v:+,.0f} kWh" for v in t["kwh"]],
                                 textposition="outside"))
            f.update_layout(yaxis_title="kWh/năm")
            st.plotly_chart(style_fig(f, 300), width="stretch")
            st.dataframe(t.rename(columns={"mua": "Thành phần", "kwh": "kWh/năm",
                                           "ghi_chu": "Diễn giải"})
                         .style.format({"kWh/năm": "{:+,.0f}"}),
                         width="stretch", hide_index=True)
            st.caption("Mùa hè giảm nhẹ do nắng gần thẳng đứng, nhưng mùa đông tăng mạnh "
                       "nên tổng cả năm vẫn dương.")

        elif ma == "ventilation":
            st.markdown("**Nhiệt độ tấm pin theo tháng — áp mái so với có khe thông gió**")
            t = phan_ra.nhiet_cell_theo_thang()
            f = go.Figure()
            f.add_scatter(x=t["ten"], y=t["t_flush"], name="Áp sát mái", mode="lines+markers",
                          line=dict(color=DO, width=2))
            f.add_scatter(x=t["ten"], y=t["t_open"], name="Có khe thông gió 15 cm",
                          mode="lines+markers", line=dict(color=LUC, width=2), fill="tonexty",
                          fillcolor="rgba(14,159,110,.12)")
            f.update_layout(yaxis_title="Nhiệt độ tấm pin (°C)")
            st.plotly_chart(style_fig(f, 300), width="stretch")
            st.dataframe(pd.DataFrame({
                "Tháng": t["ten"], "Áp mái (°C)": t["t_flush"].round(2),
                "Thông gió (°C)": t["t_open"].round(2),
                "Chênh lệch (°C)": t["delta_t"].round(2)}),
                width="stretch", hide_index=True)
            st.caption(f"Mức hạ nhiệt trung bình cả năm: **{t['delta_t'].mean():.2f} °C** "
                       "(tính bằng mô hình Sandia SAPM trên dữ liệu nhiệt độ và gió thực đo).")

        elif ma == "cbm":
            c_l, c_r = st.columns([1.1, 1])
            with c_l:
                st.markdown("**Sản lượng hụt theo mã nguyên nhân dị thường**")
                o = phan_ra.outlier_theo_ma_loi()
                f = go.Figure(go.Bar(x=o["hut_kwh"], y=o["ma_loi"], orientation="h",
                                     marker_color=DO,
                                     text=[f"{v:,.0f} kWh" for v in o["hut_kwh"]],
                                     textposition="auto"))
                f.update_layout(xaxis_title="kWh bị mất", yaxis=dict(autorange="reversed"))
                st.plotly_chart(style_fig(f, 280), width="stretch")
                o2 = o.copy()
                o2["khac_phuc_kwh"] = o2["hut_kwh"] * 0.857
                st.dataframe(pd.DataFrame({
                    "Mã nguyên nhân": o2["ma_loi"], "Số dòng": o2["so_dong"],
                    "Hụt (kWh)": o2["hut_kwh"].round(0),
                    "Khắc phục được (kWh)": o2["khac_phuc_kwh"].round(0)})
                    .style.format({"Số dòng": "{:,.0f}", "Hụt (kWh)": "{:,.0f}",
                                   "Khắc phục được (kWh)": "{:,.0f}"}),
                    width="stretch", hide_index=True)
                st.caption("Hệ số cứu vãn 85,7% — rút MTTR từ 14 ngày xuống 2 ngày "
                           "(brief mục 4.2 hạng mục 3).")
            with c_r:
                st.markdown("**Số dòng bị gắn cờ và sản lượng hụt theo tháng**")
                m = phan_ra.outlier_theo_thang()
                f2 = go.Figure()
                f2.add_bar(x=m["ten"], y=m["hut_kwh"], name="Sản lượng hụt", marker_color=DO)
                f2.add_scatter(x=m["ten"], y=m["so_co"], name="Số dòng gắn cờ", yaxis="y2",
                               mode="lines+markers", line=dict(color="#6B7280"))
                f2.update_layout(yaxis_title="kWh",
                                 yaxis2=dict(title="số dòng", overlaying="y", side="right",
                                             showgrid=False))
                st.plotly_chart(style_fig(f2, 300), width="stretch")

        elif ma == "inverter":
            st.markdown("**Số giờ biến tần có nguy cơ giảm tải, theo tháng**")
            t = phan_ra.gio_derating_theo_thang()
            f = go.Figure()
            f.add_bar(x=t["ten"], y=t["gio_canh_bao"], name="Cảnh báo (≥30°C & ≥700 W/m²)",
                      marker_color="#F59E0B", opacity=.8)
            f.add_bar(x=t["ten"], y=t["gio_derating"], name="Giảm tải (≥35°C & ≥800 W/m²)",
                      marker_color=DO)
            f.update_layout(barmode="overlay", yaxis_title="số giờ")
            st.plotly_chart(style_fig(f, 300), width="stretch")
            st.caption(f"Tổng **{t['gio_derating'].sum():,.0f} giờ** chạm ngưỡng giảm tải và "
                       f"**{t['gio_canh_bao'].sum():,.0f} giờ** chạm ngưỡng cảnh báo, dồn vào "
                       "các tháng hè (T12–T2).")

        elif ma == "washing":
            st.markdown("**Lượng mưa và tỷ lệ ngày khô theo tháng**")
            t = phan_ra.chuoi_kho_theo_thang()
            f = go.Figure()
            f.add_bar(x=t["ten"], y=t["mua_mm"], name="Lượng mưa TB (mm/ngày)",
                      marker_color="#38BDF8")
            f.add_scatter(x=t["ten"], y=t["ty_le_ngay_kho"], name="Tỷ lệ ngày khô (%)",
                          yaxis="y2", mode="lines+markers", line=dict(color=DO))
            f.update_layout(yaxis_title="mm/ngày",
                            yaxis2=dict(title="%", overlaying="y", side="right",
                                        showgrid=False, range=[0, 105]))
            st.plotly_chart(style_fig(f, 300), width="stretch")
            st.caption("Ngưỡng kích hoạt rửa: chuỗi khô ≥ 21 ngày liên tục và mưa tích luỹ "
                       "< 2 mm. Tháng nào tỷ lệ ngày khô cao thì tổn thất bám bụi tích tụ nhanh.")

        elif ma == "topcon":
            st.markdown("**Lợi ích hệ số nhiệt TOPCon theo dải nhiệt độ tấm pin**")
            t = phan_ra.loi_ich_nhiet_topcon()
            f = go.Figure(go.Bar(x=t["dai"].astype(str), y=t["loi_ich_kwh"],
                                 marker_color=XANH,
                                 text=[f"{v:,.0f}" for v in t["loi_ich_kwh"]],
                                 textposition="outside"))
            f.update_layout(yaxis_title="kWh thu hồi thêm", xaxis_title="Mức nóng của tấm pin")
            st.plotly_chart(style_fig(f, 300), width="stretch")
            st.dataframe(pd.DataFrame({
                "Dải nhiệt độ": t["dai"].astype(str), "Số giờ": t["so_gio"],
                "Sản lượng (kWh)": t["kwh"].round(0),
                "Lợi ích nhiệt (kWh)": t["loi_ich_kwh"].round(0)})
                .style.format({"Số giờ": "{:,.0f}", "Sản lượng (kWh)": "{:,.0f}",
                               "Lợi ích nhiệt (kWh)": "{:,.0f}"}),
                width="stretch", hide_index=True)
            st.caption("Hệ số nhiệt cải thiện từ −0,38%/°C xuống −0,30%/°C, nên càng nóng "
                       "thì lợi ích càng lớn.")

        if ct.get("cong_thuc_tex"):
            st.markdown("**Công thức tính**")
            for _ct in ct["cong_thuc_tex"]:
                st.latex(_ct)

# ══ Nguon ════════════════════════════════════════════════════════════════════
with st.expander("Nguồn số liệu"):
    st.markdown(f"""
| Nhóm số liệu | Nguồn |
|---|---|
| Bộ chỉ số cơ sở, 5 khuôn viên, 6 thành phần tổn thất | Brief mục 2 |
| Bảy hạng mục: kWh, doanh thu, CapEx, hoàn vốn | Brief mục 3 |
| Cơ chế, tác động, công thức từng hạng mục | Brief mục 3 và 4.2 |
| Ma trận biểu giá NEM Victoria 2020–2022 | Báo cáo định lượng mục 2.2 |

Đơn giá điện quy đổi **{cfg.DON_GIA_DIEN:.2f} AUD/kWh**. Chọn năm cụ thể sẽ thay bằng
đơn giá bình quân gia quyền của năm đó; phần doanh thu ngoài điện giữ nguyên.
Tỷ giá quy đổi: 1 AUD = {cfg.TIEN_TE['USD']['ty_gia']} USD = {cfg.TIEN_TE['VND']['ty_gia']:,g} VND.
""")
