"""Trang 1 — Dashboard Machine Learning.

Mot mach lien tuc. Dai KPI cua ca hai phan duoc dua len DAU trang bang vung chua
tao san (_KPI_TS, _KPI_XAI); phan noi dung ben duoi do vao do khi tinh xong.
"""
from __future__ import annotations

from dashboard_common import header_bao_cao
import duong_dan
import streamlit as st

_PHAN = duong_dan.GOC / "pages" / "_phan"

header_bao_cao("Dự báo sản lượng điện mặt trời",
               "42 trạm áp mái La Trobe · bước 15 phút · mô hình LightGBM",
               "MACHINE LEARNING")

_KPI_TS = st.container()
# _KPI_XAI la st.empty() vi phan XAI chay trong fragment: fragment rerun khong reset
# container ngoai, viet thang vao container se nhan doi KPI moi lan bam widget.
_KPI_XAI = st.empty()


def _nap(ten: str, **bien) -> None:
    tep = _PHAN / ten
    moi_truong = {"__file__": str(tep), **bien}
    exec(compile(tep.read_text(encoding="utf-8"), str(tep), "exec"), moi_truong)


_nap("chuoi_thoi_gian.py", _KPI_TS=_KPI_TS)


# Phan SHAP chay trong fragment: bam widget cua phan nay chi chay lai rieng no,
# khong keo phan chuoi thoi gian chay theo. Widget cua fragment phai nam trong
# than fragment nen bo loc XAI dat trong than trang, khong o sidebar.
@st.fragment
def _phan_xai() -> None:
    _nap("giai_thich_mo_hinh.py", _KPI_XAI=_KPI_XAI)


_phan_xai()
