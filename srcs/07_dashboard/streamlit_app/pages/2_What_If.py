"""Trang Mo phong What-If toi uu hoa hieu suat — nhanh BI Mart.

Tang FRONTEND: chi trinh bay, khong chua nghiep vu. Moi phep tinh goi sang
bimart.api.services.

Bo cuc:
    1. Tong quan      — chi so hien tai; doi ngay khi tich hang muc
    2. Bang tong hop  — 7 hang muc, kWh · tien · CapEx · hoan von · ROI
    3. Chi tiet       — so xuong tung hang muc: co che, tac dong, cong thuc

Chay: cd srcs/07_dashboard && streamlit run bimart/streamlit/trang_whatif.py
"""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from api.bimart.core import config as cfg                    # noqa: E402
from api.bimart.services.whatif import chay_kich_ban          # noqa: E402
from dashboard_common import header_bao_cao, load_shared_css  # noqa: E402


LUC, DO, XANH, LUOI = "#0E9F6E", "#DC2626", "#6366F1", "#D9DEE7"

st.set_page_config(page_title="What-If Tối ưu hoá | BI Mart",
                   layout="wide", initial_sidebar_state="expanded")
load_shared_css()
header_bao_cao("Mô phỏng What-If — Tối ưu hoá hiệu suất & tài chính",
               "42 trạm áp mái La Trobe · 2.428 kWp · 5 khuôn viên · dữ liệu 2020–2022",
               "BI MART")

st.markdown("""
<style>
.tq{display:flex;gap:14px;flex-wrap:wrap;margin:2px 0 8px}
.tq-c{flex:1;min-width:186px;background:#fff;border:1px solid #E4E4F0;border-radius:12px;padding:14px 16px}
.tq-l{font-size:.78rem;color:#6B7280;text-transform:uppercase;letter-spacing:.04em}
.tq-b{font-size:.92rem;color:#9CA3AF;margin-top:2px}
.tq-v{font-size:1.8rem;font-weight:700;color:#111827;line-height:1.15;margin-top:2px}
.tq-d{font-size:1.3rem;font-weight:800;margin-top:4px}
.up{color:#0E9F6E}.zero{color:#9CA3AF}
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


def the(nhan: str, co_so: str, hien_tai: str, delta: str) -> str:
    cls = "up" if co_chon else "zero"
    return (f'<div class="tq-c"><div class="tq-l">{nhan}</div>'
            f'<div class="tq-b">cơ sở: {co_so}</div>'
            f'<div class="tq-v">{hien_tai}</div>'
            f'<div class="tq-d {cls}">{delta}</div></div>')


def style_fig(f: go.Figure, h: int = 340) -> go.Figure:
    f.update_layout(template="plotly_white", paper_bgcolor="#FFF", plot_bgcolor="#FFF",
                    height=h, margin=dict(l=12, r=12, t=44, b=18),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                    xaxis=dict(gridcolor=LUOI, zeroline=False),
                    yaxis=dict(gridcolor=LUOI, zeroline=False),
                    font=dict(color="#1F2937", size=12))
    return f


# ══ 1. TONG QUAN ═════════════════════════════════════════════════════════════
st.markdown("### 1. Tổng quan")
st.caption("Chưa tích hạng mục nào thì đây là hiện trạng vận hành. Mỗi hạng mục được "
           "tích sẽ cộng thêm phần đóng góp của nó vào các chỉ số dưới đây."
           if not co_chon else
           f"Đang áp dụng **{len(bat)}/7** hạng mục cải tiến.")

st.markdown('<div class="tq">'
    + the("Sản lượng", f"{c['e_kwh']/1e6:.2f} GWh", f"{s['e_kwh']/1e6:.2f} GWh",
          f"+{d['e_kwh']:,.0f} kWh ({d['ty_le_%']:+.2f}%)" if co_chon else "hiện trạng")
    + the("Performance Ratio", f"{c['pr_%']:.2f}%", f"{s['pr_%']:.2f}%",
          f"{s['pr_%']-c['pr_%']:+.2f} điểm" if co_chon else "hiện trạng")
    + the("Capacity Factor", f"{c['cf_%']:.2f}%", f"{s['cf_%']:.2f}%",
          f"{s['cf_%']-c['cf_%']:+.2f} điểm" if co_chon else "hiện trạng")
    + the("Doanh thu", tien_str(c["revenue_aud"]), tien_str(s["revenue_aud"]),
          f"+{tien_str(d['revenue_aud'])}/năm" if co_chon else "hiện trạng")
    + the("CO2 tránh được", f"{c['co2_kg']/1000:,.0f} tấn", f"{s['co2_kg']/1000:,.0f} tấn",
          f"+{d['co2_kg']/1000:,.0f} tấn/năm" if co_chon else "hiện trạng")
    + '</div>', unsafe_allow_html=True)

g1, g2 = st.columns([1.25, 1])
with g1:
    with st.container(border=True):
        st.markdown("##### Từ sản lượng cơ sở tới sản lượng sau cải tiến")
        b = pd.DataFrame([h for h in kq["hang_muc"] if h["bat"]])
        ten = ["Cơ sở"] + ([f"{r.stt}. {r.ten[:24]}" for r in b.itertuples()] if len(b) else []) + ["Hiện tại"]
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
        st.markdown("##### Thành phần tổn thất — phần đã khử và phần còn lại")
        t = pd.DataFrame(kq["ton_that"])
        t["da_khu_%"] = t["truoc_%"] - t["sau_%"]
        f2 = go.Figure()
        # Cot xep chong: tong do dai = ton that ban dau. Phan xanh la da khu, phan do
        # la con lai. Cach nay thay ro ca truong hop khu hoan toan (sau = 0), thu ma
        # bieu do cot ghep khong hien duoc vi cot dai bang 0.
        f2.add_bar(y=t["ten"], x=t["sau_%"], orientation="h", name="Còn lại",
                   marker_color=DO, opacity=.9,
                   text=[f"{v:.2f}%" if v > 0.15 else "" for v in t["sau_%"]],
                   textposition="inside", insidetextanchor="middle")
        f2.add_bar(y=t["ten"], x=t["da_khu_%"], orientation="h", name="Đã khử",
                   marker_color=LUC,
                   text=[f"−{v:.2f}%" if v > 0.15 else "" for v in t["da_khu_%"]],
                   textposition="inside", insidetextanchor="middle")
        f2.update_layout(barmode="stack", xaxis_title="% tổn thất so với sản lượng cơ sở",
                         yaxis=dict(autorange="reversed"))
        for i, r in t.iterrows():
            f2.add_annotation(x=r["truoc_%"], y=r["ten"], text=f"  {r['truoc_%']:.2f}%",
                              showarrow=False, xanchor="left",
                              font=dict(size=11, color="#6B7280"))
        st.plotly_chart(style_fig(f2, 380), width="stretch")

# ══ 2. BANG TONG HOP ═════════════════════════════════════════════════════════
st.markdown("### 2. Bảy hạng mục cải tiến")
with st.container(border=True):
    bb = pd.DataFrame(kq["hang_muc"]).sort_values("stt")
    hien = pd.DataFrame({
        "Áp dụng": bb["bat"].map({True: "Có", False: "Không"}),
        "#": bb["stt"], "Hạng mục": bb["ten"], "Hiệu suất": bb["hieu_suat"],
        "kWh/năm": bb["delta_kwh"],
        f"{tien}/năm": bb["delta_revenue_aud"].map(lambda v: cfg.quy_doi(v, tien)),
        f"CapEx ({tien})": bb["capex_aud"].map(
            lambda v: None if pd.isna(v) else cfg.quy_doi(v, tien)),
        "Hoàn vốn": bb["payback"], "ROI/năm": bb["roi_%"],
    })
    st.dataframe(
        hien.style.format({"kWh/năm": "{:,.0f}", f"{tien}/năm": "{:,.0f}",
                           f"CapEx ({tien})": lambda v: "—" if pd.isna(v) else f"{v:,.0f}",
                           "ROI/năm": lambda v: "—" if pd.isna(v) else f"{v:,.0f}%"})
            .background_gradient(subset=["kWh/năm"], cmap="Blues", low=.1, high=.6),
        width="stretch", hide_index=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng CapEx", tien_str(d["capex_aud"]) if co_chon else "—")
    m2.metric("Doanh thu tăng", f"{tien_str(d['revenue_aud'])}/năm" if co_chon else "—")
    m3.metric("Hoàn vốn trung bình",
              f"{d['payback_nam']:.2f} năm" if d.get("payback_nam") else "—")

# ══ 3. CHI TIET TUNG HANG MUC ════════════════════════════════════════════════
st.markdown("### 3. Chi tiết từng hạng mục")
for h in sorted(kq["hang_muc"], key=lambda x: x["stt"]):
    ct = cfg.CHI_TIET_HANG_MUC[h["ma"]]
    nhan = "đang áp dụng" if h["bat"] else "chưa áp dụng"
    with st.expander(f"Hạng mục {h['stt']} — {ct['tieu_de']}  ·  {nhan}", expanded=False):
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Sản lượng thu hồi", f"{h['delta_kwh']:,.0f} kWh/năm")
        k2.metric("Doanh thu", f"{tien_str(h['delta_revenue_aud'])}/năm")
        k3.metric("CapEx", tien_str(h["capex_aud"]) if h["capex_aud"] else "—")
        k4.metric("Hoàn vốn", h["payback"])
        st.markdown(f"**Cơ chế.** {ct['co_che']}")
        st.markdown(f"**Tác động chỉ số.** {ct['tac_dong']}")
        if ct["cong_thuc"]:
            st.markdown("**Công thức tính trên từng dòng dữ liệu:**")
            st.code("\n".join(ct["cong_thuc"]), language="text")
        if h["ton_that"]:
            tt = cfg.TON_THAT_CO_SO[h["ton_that"]]
            st.caption(f"Thành phần tổn thất liên quan: **{tt['ten']}** — "
                       f"{tt['ty_le']*100:.2f}% ({tt['kwh']:,} kWh/năm) "
                       f"giảm còn {tt['sau']*100:.2f}%.")

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
