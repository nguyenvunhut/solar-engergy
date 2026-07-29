from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "model" / "v3"
API_URL = "http://127.0.0.1:8000"

st.title("Giải Thích Mô Hình (Explainable AI - SHAP)")


def fetch_api(endpoint, params=None):
    try:
        res = requests.get(f"{API_URL}{endpoint}", params=params, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None


@st.cache_data
def load_local_shap_importance():
    p = DATA_DIR / "08_explain" / "shap_importance.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


@st.cache_data
def load_local_shap_values():
    p = DATA_DIR / "08_explain" / "shap_values.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


imp_data = fetch_api("/shap/importance")
df_imp = (
    pd.DataFrame(imp_data) if imp_data else load_local_shap_importance()
)

val_data = fetch_api("/shap/values?limit=500")
df_val = pd.DataFrame(val_data) if val_data else load_local_shap_values()

if df_imp.empty:
    st.warning(
        "Chưa có dữ liệu SHAP. Hãy chạy notebook 08_explainable_ai.ipynb trước!"
    )
    st.stop()

# 1. Bar chart Global Feature Importance
st.subheader("1. Tầm Quan Trọng Tổng Thể (Global SHAP Importance)")
fig_bar = px.bar(
    df_imp.head(15),
    x="mean_abs_shap",
    y="feature",
    orientation="h",
    labels={"mean_abs_shap": "Trung bình |SHAP Value|", "feature": "Đặc trưng"},
    color="mean_abs_shap",
    color_continuous_scale="Viridis",
)
fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig_bar, use_container_width=True)

# 2. Importance By Feature Type
st.subheader("2. Tầm Quan Trọng Theo Nhóm Đặc Trưng")
if "feature_group" in df_imp.columns:
    grp_df = (
        df_imp.groupby("feature_group")["mean_abs_shap"]
        .sum()
        .reset_index()
        .sort_values("mean_abs_shap", ascending=False)
    )
    fig_grp = px.pie(
        grp_df,
        names="feature_group",
        values="mean_abs_shap",
        hole=0.3,
        title="Tỷ lệ đóng góp theo Nhóm Đặc Trưng",
    )
    st.plotly_chart(fig_grp, use_container_width=True)

# 3. Beeswarm Scatter Plot với Jitter
st.subheader("3. Biểu Đồ Tương Tác Beeswarm / Scatter Distribution")
shap_cols = [c for c in df_val.columns if c.startswith("shap_")]

if shap_cols:
    feature_names = [c.replace("shap_", "") for c in shap_cols]
    selected_feat = st.selectbox(
        "Chọn đặc trưng xem phân bố SHAP", feature_names
    )
    target_shap_col = f"shap_{selected_feat}"

    if target_shap_col in df_val.columns:
        y_vals = df_val[target_shap_col]
        x_jitter = np.random.normal(0, 0.05, size=len(y_vals))

        fig_bee = px.scatter(
            x=x_jitter,
            y=y_vals,
            color=y_vals,
            color_continuous_scale="RdBu_r",
            labels={
                "x": "Phân bố (Jitter)",
                "y": f"SHAP Value cho {selected_feat}",
            },
        )
        fig_bee.update_layout(template="plotly_white")
        st.plotly_chart(fig_bee, use_container_width=True)

# 4. Dependency Plot (2 Dropdowns)
st.subheader("4. SHAP Dependency Plot (Mối Quan Hệ 2 Đặc Trưng)")
col_dep1, col_dep2 = st.columns(2)
with col_dep1:
    feat_x = st.selectbox("Chọn Đặc Trưng X", feature_names, index=0)
with col_dep2:
    feat_color = st.selectbox(
        "Chọn Đặc Trưng Tô Màu",
        feature_names,
        index=min(1, len(feature_names) - 1),
    )

if f"shap_{feat_x}" in df_val.columns:
    fig_dep = px.scatter(
        df_val,
        x=feat_x if feat_x in df_val.columns else f"shap_{feat_x}",
        y=f"shap_{feat_x}",
        color=feat_color if feat_color in df_val.columns else None,
        labels={
            f"shap_{feat_x}": f"SHAP Value của {feat_x}",
            feat_x: feat_x,
        },
    )
    fig_dep.update_layout(template="plotly_white")
    st.plotly_chart(fig_dep, use_container_width=True)

# 5. Local Explanation Waterfall Bar Plot
st.subheader("5. Giải Thích Cục Bộ (Local Explanation Waterfall)")
if not df_val.empty:
    sample_idx = st.slider("Chọn dòng mẫu dự báo (Row Index)", 0, len(df_val) - 1, 0)
    row_data = df_val.iloc[sample_idx]

    local_shaps = []
    for c in shap_cols:
        f_name = c.replace("shap_", "")
        local_shaps.append({"feature": f_name, "shap_value": row_data[c]})

    df_local = (
        pd.DataFrame(local_shaps)
        .reindex(
            pd.DataFrame(local_shaps)["shap_value"].abs().sort_values(ascending=False).index
        )
        .head(10)
    )

    fig_waterfall = px.bar(
        df_local,
        x="shap_value",
        y="feature",
        orientation="h",
        color="shap_value",
        color_continuous_scale="RdBu_r",
        labels={
            "shap_value": "Mức độ tác động SHAP",
            "feature": "Đặc trưng",
        },
        title=f"Top 10 Tác Động SHAP Cho Dòng Mẫu #{sample_idx}",
    )
    fig_waterfall.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_waterfall, use_container_width=True)
