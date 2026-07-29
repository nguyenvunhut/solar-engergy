from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="Solar PV Energy Forecasting Dashboard",
    layout="wide",
)

# Cấu hình đường dẫn trang từ vị trí file app.py
PAGES_DIR = Path(__file__).parent / "pages"

pg = st.navigation(
    [
        st.Page(
            PAGES_DIR / "1_TimeSeries.py",
            title="1. Chuỗi Thời Gian & Dự Báo",
        ),
        st.Page(
            PAGES_DIR / "2_SHAP.py",
            title="2. Giải Thích Mô Hình (SHAP)",
        ),
    ]
)

st.sidebar.title("Hệ Thống Dự Báo Quang Điện")
st.sidebar.caption("Dự án Tốt nghiệp - Nhóm The Outliers")

pg.run()
