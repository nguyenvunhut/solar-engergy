"""Diem chay cua ung dung Streamlit.

    cd srcs/07_dashboard
    streamlit run streamlit_app/app.py --server.port 8501
"""
from __future__ import annotations

from dashboard_common import load_shared_css
import duong_dan
import streamlit as st

st.set_page_config(
    page_title="Solar Forecast Analytics | The Outliers",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_shared_css()

pg = st.navigation([
    st.Page(duong_dan.GOC / "pages" / "1_ML.py", title="Dự báo sản lượng (ML)"),
    st.Page(duong_dan.GOC / "pages" / "2_What_If.py", title="What-If tối ưu hoá (BI Mart)"),
])

st.sidebar.markdown("<p class='sidebar-brand'>Solar Analytics</p>", unsafe_allow_html=True)
st.sidebar.caption("The Outliers · Energy Forecasting")

pg.run()
