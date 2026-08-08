import ctypes
import glob
import os
from pathlib import Path
import streamlit as st

from dashboard_common import load_shared_css

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
