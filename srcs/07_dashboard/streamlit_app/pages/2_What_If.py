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

from pathlib import Path

from api.bimart.core import config as cfg
from api.bimart.services import phan_ra
from api.bimart.services.whatif import chay_kich_ban
from dashboard_common import header_bao_cao, load_shared_css, nap_css
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

LUC, DO, XANH, LUOI = "#0E9F6E", "#DC2626", "#6366F1", "#D9DEE7"
CAO = 330   # chieu cao dung chung: bieu do va bang canh no phai bang nhau,
            # va moi cot chi duoc chua dung mot tieu de + mot khoi noi dung

st.set_page_config(page_title="What-If Tối ưu hoá | BI Mart",
                   layout="wide", initial_sidebar_state="expanded")
load_shared_css()
header_bao_cao("Mô phỏng What-If — Tối ưu hoá hiệu suất & tài chính",
               "42 trạm áp mái La Trobe · 2.428 kWp · 5 khuôn viên · dữ liệu 2020–2022",
               "BI MART")

_THU_MUC = Path(__file__).resolve().parent.parent
nap_css(_THU_MUC / "what_if.css")


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


def _o(lop: str, noi_dung: str = "") -> str:
    """Mot the <div> mang lop CSS cho truoc. Gom lai de khoi lap the tho."""
    return f'<div class="{lop}">{noi_dung}</div>'


def phan_tram(truoc: float, sau: float) -> str:
    """Muc cai thien tinh theo phan tram, de moi the KPI deu co mot con so % ."""
    return f"{(sau - truoc) / truoc * 100:+.2f}%" if truoc else "—"


def the(nhan: str, co_so: str, mo_phong: str, delta: str) -> str:
    """Mot the KPI.

    Chua tich hang muc nao: chi hien con so hien trang.
    Da tich: hien "Co so -> Mo phong" tren mot luoi 3 cot x 2 hang (hang tren
    la nhan, hang duoi la so, mui ten nam giua hang duoi), kem dong chenh lech.
    Cac lop CSS tuong ung nam trong streamlit_app/what_if.css.
    """
    if not co_chon:
        than = _o("kpi-doi-don", _o("kpi-cot-nhan", "Cơ sở") + _o("kpi-cot-tri", co_so))
    else:
        luoi = (_o("kpi-cot-nhan", "Cơ sở") + _o("") + _o("kpi-cot-nhan", "Mô phỏng")
                + _o("kpi-cot-tri", co_so) + _o("kpi-mui", "&#8594;")
                + _o("kpi-cot-tri sim", mo_phong))
        than = _o("kpi-doi", luoi) + _o("kpi-delta up", delta)
    return _o("", _o("kpi-card", _o("kpi-label", nhan) + than))


def dai_card(muc: list[tuple[str, str]]) -> None:
    """Ve mot dai card "nhan - gia tri" nam ngang, tu dong xuong hang khi hep."""
    st.markdown(_o("ct", "".join(
        _o("", _o("ct-nhan", nhan) + _o("ct-tri", gia_tri)) for nhan, gia_tri in muc)),
        unsafe_allow_html=True)


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
           f"Đang áp dụng **{len(bat)}/{len(cfg.HANG_MUC_CAI_TIEN)}** hạng mục cải tiến.")

st.markdown('<div class="tq">'
    + the("Điện làm ra", f"{c['e_kwh']/1e6:.2f} GWh", f"{s['e_kwh']/1e6:.2f} GWh",
          f"+{d['e_kwh']:,.0f} kWh ({d['ty_le_%']:+.2f}%)")
    + the("Hiệu suất thực tế (PR)", f"{c['pr_%']:.2f}%", f"{s['pr_%']:.2f}%",
          f"{s['pr_%']-c['pr_%']:+.2f} điểm ({phan_tram(c['pr_%'], s['pr_%'])})")
    + the("Mức chạy so với công suất lắp (CF)", f"{c['cf_%']:.2f}%", f"{s['cf_%']:.2f}%",
          f"{s['cf_%']-c['cf_%']:+.2f} điểm ({phan_tram(c['cf_%'], s['cf_%'])})")
    + the("Tiền điện tiết kiệm", tien_gon(c["revenue_aud"]), tien_gon(s["revenue_aud"]),
          f"+{tien_str(d['revenue_aud'])}/năm "
          f"({phan_tram(c['revenue_aud'], s['revenue_aud'])})")
    + the("CO₂ giảm được", f"{c['co2_kg']/1000:,.0f} tấn", f"{s['co2_kg']/1000:,.0f} tấn",
          f"+{d['co2_kg']/1000:,.0f} tấn/năm "
          f"({phan_tram(c['co2_kg'], s['co2_kg'])})")
    + '</div>', unsafe_allow_html=True)

g1, g2 = st.columns([1.25, 1])
with g1:
    with st.container(border=True):
        st.markdown("##### Điện tăng thêm nhờ từng hạng mục")
        b = pd.DataFrame([h for h in kq["hang_muc"] if h["bat"]])
        ten = ["Cơ sở"] + ([f"{r.stt}. {r.ten[:24]}" for r in b.itertuples()] if len(b) else []) + ["Mô phỏng"]
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
        st.markdown("##### Điện bị mất: lấy lại được và còn lại")
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
st.markdown(f"### {len(cfg.HANG_MUC_CAI_TIEN)} hạng mục cải tiến")
with st.container(border=True):
    bb = pd.DataFrame(kq["hang_muc"]).sort_values("stt")
    hien = pd.DataFrame({
        "Áp dụng": bb["bat"].map({True: "Có", False: "Không"}),
        "Hạng mục": bb["ten"],
        "Tỷ lệ cải thiện": bb["hieu_suat"],
        "Điện thêm (kWh/năm)": bb["delta_kwh"],
        f"Tiền thêm ({tien}/năm)": bb["delta_revenue_aud"].map(
            lambda v: cfg.quy_doi(v, tien)),
        f"Tiền bỏ ra ({tien})": bb["capex_aud"].map(
            lambda v: None if pd.isna(v) else cfg.quy_doi(v, tien)),
        "Bao lâu lấy lại vốn": bb["payback"],
    })
    st.dataframe(
        hien.style.format({"Điện thêm (kWh/năm)": "{:,.0f}",
                           f"Tiền thêm ({tien}/năm)": "{:,.0f}",
                           f"Tiền bỏ ra ({tien})":
                               lambda v: "—" if pd.isna(v) else f"{v:,.0f}"})
            .background_gradient(subset=["Điện thêm (kWh/năm)"], cmap="Blues",
                                 low=.1, high=.6)
            .set_properties(subset=["Hạng mục"], **{"font-weight": "650"}),
        width="stretch", hide_index=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng tiền phải bỏ ra", tien_str(d["capex_aud"]) if co_chon else "—")
    m2.metric("Tiền thu thêm", f"{tien_str(d['revenue_aud'])}/năm" if co_chon else "—")
    m3.metric("Trung bình bao lâu lấy lại vốn",
              f"{d['payback_nam']:.2f} năm" if d.get("payback_nam") else "—")

# ══ 3. CHI TIET TUNG HANG MUC ════════════════════════════════════════════════
st.markdown("### Chi tiết từng hạng mục")
st.caption("Số liệu từ tài liệu; biểu đồ từ dữ liệu vận hành thực tế "
           "của 42 trạm (2020–2022).")

for h in sorted(kq["hang_muc"], key=lambda x: x["stt"]):
    ma = h["ma"]
    ct = cfg.CHI_TIET_HANG_MUC[ma]
    nhan = "đang áp dụng" if h["bat"] else "chưa áp dụng"
    with st.expander(f"**Hạng mục {h['stt']} — {ct['tieu_de']}**  ·  {nhan}", expanded=False):

        st.markdown("**Bảng thông số**")
        if ma == "bess":
            dai_card([
                ("Thu hồi cắt ngọn", "69.782 kWh/năm (+1,53% PR)"),
                ("Điện xả hữu ích", "712.182 kWh/năm"),
                ("Giá trị kinh tế", f"{tien_str(h['delta_revenue_aud'])}/năm"),
                ("CapEx đầu tư", tien_str(h["capex_aud"])),
                ("Thời gian hoàn vốn", h["payback"]),
            ])
        else:
            dai_card([
                ("Tỷ lệ cải thiện", h["hieu_suat"]),
                ("Điện thu hồi", f"{h['delta_kwh']:,.0f} kWh/năm"),
                ("Giá trị kinh tế", f"{tien_str(h['delta_revenue_aud'])}/năm"),
                ("CapEx đầu tư", tien_str(h["capex_aud"]) if h["capex_aud"]
                                 else "Tích hợp kỳ đại tu"),
                ("Thời gian hoàn vốn", h["payback"]),
            ])

        with st.popover("Cơ chế & tác động"):
            st.markdown(f"**Cơ chế.** {ct['co_che']}")
            st.markdown(f"**Tác động chỉ số.** {ct['tac_dong']}")

            so_do_tep = _THU_MUC / "assets" / "diagrams" / f"diagram_popover_{h['stt']:02d}_{ma}.svg"
            if so_do_tep.exists():
                st.markdown("---")
                st.markdown("**Sơ đồ trực quan cơ chế tác động:**")
                st.image(str(so_do_tep), use_container_width=True)

        if ma == "bess":
            st.caption("💡 **Cơ chế kép của BESS:** (1) Thu hồi trực tiếp **69.782 kWh/năm** điện sạch bị biến tần xén bỏ trưa hè (giảm tổn thất cắt ngọn từ 2,30% về 0,28%); (2) Điều tiết xả **712.182 kWh/năm** vào giờ cao điểm TOU (17:00–21:00) và gọt đỉnh **800 kW** phụ tải trường học.")
            cp = phan_ra.theo_campus("bess")
            c_l, c_r = st.columns([1.15, 1], vertical_alignment="top")
            with c_l:
                st.markdown("**Phân bổ thu hồi cắt ngọn theo khuôn viên**")
                f = go.Figure(go.Bar(x=cp["kwh"], y=cp["campus"], orientation="h",
                                     marker_color=XANH,
                                     text=[f"{v:,.0f} kWh" for v in cp["kwh"]],
                                     textposition="auto"))
                f.update_layout(xaxis_title="kWh thu hồi / năm", yaxis=dict(autorange="reversed"))
                st.plotly_chart(style_fig(f, CAO), width="stretch")
            with c_r:
                st.markdown("**Số liệu định cỡ & xả điện từng khuôn viên**")
                st.dataframe(pd.DataFrame({
                    "Khuôn viên": cp["campus"], "Số trạm": cp["so_tram"],
                    "CS BESS": cp["bess_kw"],
                    "Dung lượng": cp["bess_kwh"],
                    "Thu hồi cắt ngọn": cp["kwh"].round(0),
                    "Điện xả hữu ích": cp["e_xa_kwh"].round(0)})
                    .style.format({"CS BESS": "{:,.0f} kW",
                                   "Dung lượng": "{:,.0f} kWh",
                                   "Thu hồi cắt ngọn": "{:,.0f} kWh",
                                   "Điện xả hữu ích": "{:,.0f} kWh"}),
                    width="stretch", hide_index=True, height=CAO)

            st.markdown("**Tổn thất cắt ngọn theo tháng (kWh)**")
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
            t = phan_ra.tilt_theo_mua()
            st.markdown("**Điện tăng / giảm theo từng tháng**")
            f = go.Figure()
            f.add_bar(x=t["ten"], y=t["delta_kwh"], name="Điện thay đổi",
                      marker_color=[LUC if v > 0 else DO for v in t["delta_kwh"]],
                      text=[f"{v:+,.0f}" for v in t["delta_kwh"]],
                      textposition="outside", textfont=dict(size=9))
            f.add_scatter(x=t["ten"], y=t["ty_le_%"], name="Mức thay đổi (%)",
                          mode="lines+markers", yaxis="y2",
                          line=dict(color=XANH, width=2), marker=dict(size=6))
            f.add_hline(y=0, line_width=1, line_color="#9CA3AF")
            f.update_layout(yaxis_title="kWh/tháng",
                            yaxis2=dict(title="%", overlaying="y", side="right",
                                        showgrid=False, ticksuffix="%"))
            st.plotly_chart(style_fig(f, 340), width="stretch")
            st.caption("Hè giảm nhẹ 1,2–1,6%; đông tăng mạnh 13,7–20,8%.")

            c_l, c_r = st.columns([1.1, 1], vertical_alignment="top")
            with c_l:
                st.markdown("**Hình dạng mùa: báo cáo so với dữ liệu**")
            f2 = go.Figure()
            f2.add_scatter(x=t["ten"], y=t["ty_le_bc_%"], name="Theo báo cáo",
                           mode="lines+markers", line=dict(color="#9CA3AF", width=2,
                                                           dash="dot"))
            f2.add_scatter(x=t["ten"], y=t["ty_le_dl_%"], name="Đo trên dữ liệu",
                           mode="lines+markers", line=dict(color=XANH, width=2))
            f2.update_layout(yaxis_title="% sản lượng cả năm", yaxis_ticksuffix="%")
            with c_l:
                st.plotly_chart(style_fig(f2, CAO), width="stretch")

            bang = pd.DataFrame({
                "Tháng": t["ten"], "Mùa": t["mua"],
                "Nắng trưa cao (°)": t["goc_cao"],
                "Điện nền (kWh)": t["kwh_co_so"],
                "Thay đổi (%)": t["ty_le_%"] / 100.0,
                "Thay đổi (kWh)": t["delta_kwh"],
                f"Tiền ({tien})": t["aud"].map(lambda v: cfg.quy_doi(v, tien)),
            })
            with c_r:
                st.markdown("**Cân bằng năng lượng 12 tháng**")
                st.dataframe(
                    bang.style.format({"Nắng trưa cao (°)": "{:.1f}",
                                       "Điện nền (kWh)": "{:,.0f}",
                                       "Thay đổi (%)": "{:+.2%}",
                                       "Thay đổi (kWh)": "{:+,.0f}",
                                       f"Tiền ({tien})": "{:+,.0f}"})
                        .background_gradient(subset=["Thay đổi (kWh)"], cmap="RdYlGn",
                                             vmin=-12_000, vmax=12_000),
                    width="stretch", hide_index=True, height=CAO)
            st.caption("Hình dạng mùa khớp dữ liệu 42 trạm, r = "
                       f"{t['ty_le_bc_%'].corr(t['ty_le_dl_%']):.3f}.")
            c1, c2, c3 = st.columns(3)
            c1.metric("Bốn tháng đông (T05–T08)",
                      f"{t.loc[t['thang'].between(5, 8), 'delta_kwh'].sum():+,.0f} kWh")
            c2.metric("Bốn tháng hè (T11–T02)",
                      f"{t.loc[t['thang'].isin([11, 12, 1, 2]), 'delta_kwh'].sum():+,.0f} kWh")
            c3.metric("Mưa tự rửa bùn viền đáy",
                      f"+{cfg.TILT_TU_RUA_TROI_KWH:,.0f} kWh")
            st.caption(f"Cộng lại {t['delta_kwh'].sum() + cfg.TILT_TU_RUA_TROI_KWH:+,.0f} "
                       "kWh/năm.")

        elif ma == "ventilation":
            t = phan_ra.nhiet_cell_theo_thang()
            c_l, c_r = st.columns([1.25, 1], vertical_alignment="top")
            with c_l:
                st.markdown("**Nhiệt độ tấm pin theo tháng**")
            f = go.Figure()
            f.add_scatter(x=t["ten"], y=t["t_flush"], name="Áp sát mái", mode="lines+markers",
                          line=dict(color=DO, width=2))
            f.add_scatter(x=t["ten"], y=t["t_open"], name="Có khe thông gió 15 cm",
                          mode="lines+markers", line=dict(color=LUC, width=2), fill="tonexty",
                          fillcolor="rgba(14,159,110,.12)")
            f.update_layout(yaxis_title="Nhiệt độ tấm pin (°C)")
            with c_l:
                st.plotly_chart(style_fig(f, CAO), width="stretch")
            with c_r:
                st.markdown("**Chênh lệch từng tháng**")
                st.dataframe(pd.DataFrame({
                    "Tháng": t["ten"],
                    "Áp sát mái (°C)": t["t_flush"],
                    "Có khe thông gió (°C)": t["t_open"],
                    "Chênh lệch (°C)": t["t_open"] - t["t_flush"]})
                    .style.format({"Áp sát mái (°C)": "{:.2f}",
                                   "Có khe thông gió (°C)": "{:.2f}",
                                   "Chênh lệch (°C)": "{:+.2f}"}),
                    width="stretch", hide_index=True, height=CAO)
            st.caption(f"Hạ trung bình {t['delta_t'].mean():.2f} °C (mô hình Sandia SAPM).")

        elif ma == "cbm":
            c_l, c_r = st.columns([1.15, 1], vertical_alignment="top")
            with c_l:
                st.markdown("**Điện hụt theo nguyên nhân**")
                o = phan_ra.outlier_theo_ma_loi()
                f = go.Figure(go.Bar(x=o["hut_kwh"], y=o["ma_loi"], orientation="h",
                                     marker_color=DO,
                                     text=[f"{v:,.0f} kWh" for v in o["hut_kwh"]],
                                     textposition="auto"))
                f.update_layout(xaxis_title="kWh bị mất", yaxis=dict(autorange="reversed"))
                st.plotly_chart(style_fig(f, CAO), width="stretch")
            with c_r:
                st.markdown("**Số liệu từng nguyên nhân**")
                o2 = o.copy()
                o2["khac_phuc_kwh"] = o2["hut_kwh"] * 0.857
                st.dataframe(pd.DataFrame({
                    "Mã nguyên nhân": o2["ma_loi"], "Số dòng": o2["so_dong"],
                    "Hụt (kWh)": o2["hut_kwh"].round(0),
                    "Khắc phục được (kWh)": o2["khac_phuc_kwh"].round(0)})
                    .style.format({"Số dòng": "{:,.0f}", "Hụt (kWh)": "{:,.0f}",
                                   "Khắc phục được (kWh)": "{:,.0f}"}),
                    width="stretch", hide_index=True, height=CAO)
            st.caption("Cứ 100 kWh mất thì lấy lại 85,7 kWh.")

            st.markdown("**Số dòng gắn cờ và điện hụt theo tháng**")
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
            st.markdown("**Số giờ biến tần có nguy cơ giảm tải**")
            t = phan_ra.gio_derating_theo_thang()
            f = go.Figure()
            f.add_bar(x=t["ten"], y=t["gio_canh_bao"], name="Cảnh báo (≥30°C & ≥700 W/m²)",
                      marker_color="#F59E0B", opacity=.8)
            f.add_bar(x=t["ten"], y=t["gio_derating"], name="Giảm tải (≥35°C & ≥800 W/m²)",
                      marker_color=DO)
            f.update_layout(barmode="overlay", yaxis_title="số giờ")
            st.plotly_chart(style_fig(f, 300), width="stretch")
            st.caption(f"{t['gio_derating'].sum():,.0f} giờ giảm tải, "
                       f"{t['gio_canh_bao'].sum():,.0f} giờ cảnh báo — dồn vào mùa hè.")

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
            st.caption("Rửa khi khô ≥ 21 ngày và mưa < 2 mm.")

        elif ma == "topcon":
            t = phan_ra.loi_ich_nhiet_topcon()
            c_l, c_r = st.columns([1.2, 1], vertical_alignment="top")
            with c_l:
                st.markdown("**Lợi ích theo mức nóng tấm pin**")
            f = go.Figure(go.Bar(x=t["dai"].astype(str), y=t["loi_ich_kwh"],
                                 marker_color=XANH,
                                 text=[f"{v:,.0f}" for v in t["loi_ich_kwh"]],
                                 textposition="outside"))
            f.update_layout(yaxis_title="kWh thu hồi thêm", xaxis_title="Mức nóng của tấm pin")
            with c_l:
                st.plotly_chart(style_fig(f, CAO), width="stretch")
            with c_r:
                st.markdown("**Số liệu từng dải nhiệt**")
                st.dataframe(pd.DataFrame({
                    "Dải nhiệt độ": t["dai"].astype(str), "Số giờ": t["so_gio"],
                    "Sản lượng (kWh)": t["kwh"].round(0),
                    "Lợi ích nhiệt (kWh)": t["loi_ich_kwh"].round(0)})
                    .style.format({"Số giờ": "{:,.0f}", "Sản lượng (kWh)": "{:,.0f}",
                                   "Lợi ích nhiệt (kWh)": "{:,.0f}"}),
                    width="stretch", hide_index=True, height=CAO)
            st.caption("Hệ số nhiệt −0,38 → −0,30 %/°C: càng nóng lợi càng nhiều.")

        if ct.get("cong_thuc_tex"):
            # Popover chu khong phai expander: Streamlit cam long expander trong expander.
            with st.popover("Công thức tính"):
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
