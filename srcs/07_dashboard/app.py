from pathlib import Path

import streamlit as st

from dashboard_common import load_shared_css

# KHONG goi nap_runtime_cpp() o day. Truoc day app.py nap libstdc++ tu /nix/store
# bang RTLD_GLOBAL cho MOI trang, trong khi pyarrow da mang san ban rieng — hai ban
# trong mot tien trinh lam Streamlit segfault ngay tai pd.read_parquet (coredump
# 2026-08-10 xac nhan, xem docstring nap_runtime_cpp). Chi trang 2_SHAP.py can
# LightGBM/SHAP nen chi trang do goi, va chi goi khi import that su that bai.

st.set_page_config(
    page_title="Solar Forecast Analytics | The Outliers",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme dong bo voi pages/1_TimeSeries.py va pages/2_SHAP.py - nen sang, chuyen nghiep,
# giong style BI (Tableau/PowerBI light). CSS chung nam o style.css, nap qua
# dashboard_common.load_shared_css() de khong lap lai CSS o tung file (truoc day
# 4 file co 4 khoi <style> gan giong het nhau).
load_shared_css()

PAGES_DIR = Path(__file__).parent / "pages"

# Trang "Phase Lag Story" da bo (2026-08-09): do tre pha gio con lai 1 KPI tren
# trang Time Series. Mot trang rieng chi de ke lai mot chi so da ve 0 khong con
# xung dang chiem 1/3 dieu huong.
# Ba trang, tach theo BAN CHAT du lieu chu khong theo chu de:
#   1-2 doc artifact da tinh san  -> nhanh, la ket qua DA DO DUOC tren tap test
#   3   goi Open-Meteo + chay model -> cham, la du bao SE XAY RA
# Khong tron trang 3 vao trang 1: dat du bao 14 ngay canh WAPE 17,64% khien nguoi
# xem doc con so do thanh do chinh xac cua du bao dai han, trong khi no do nang luc
# MOT BUOC.
pg = st.navigation([
    st.Page(PAGES_DIR / "1_TimeSeries.py", title="Time Series & Baseline", icon="📈"),
    st.Page(PAGES_DIR / "2_SHAP.py", title="Model Explainability (XAI)", icon="🔬"),
    st.Page(PAGES_DIR / "3_Du_Bao.py", title="Dự báo tới & What-if", icon="🔮"),
])

st.sidebar.markdown("<p class='sidebar-brand'>⚡ Solar Forecast Analytics</p>", unsafe_allow_html=True)
st.sidebar.caption("The Outliers · Energy Forecasting")

pg.run()
