"""Ham dung chung cho dashboard - hien tai chi co load CSS."""
from pathlib import Path

import streamlit as st

_CSS_PATH = Path(__file__).parent / "style.css"


def load_shared_css() -> None:
    """Nap file style.css chung, tranh lap lai CSS o tung trang."""
    css = _CSS_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
