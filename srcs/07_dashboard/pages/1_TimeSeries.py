from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "model" / "v3"
API_URL = "http://127.0.0.1:8000"

st.title("Phân Tích Chuỗi Thời Gian & Benchmark Dự Báo")


def fetch_api(endpoint, params=None):
    try:
        res = requests.get(f"{API_URL}{endpoint}", params=params, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None


@st.cache_data
def load_local_predictions():
    p = DATA_DIR / "07_final_test" / "prediction_audit.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


@st.cache_data
def load_local_metrics():
    p = DATA_DIR / "07_final_test" / "metrics_by_site.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


@st.cache_data
def load_local_baseline():
    p = DATA_DIR / "06_0_baseline" / "baseline_metrics.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


pred_data = fetch_api("/predictions")
df_pred = pd.DataFrame(pred_data) if pred_data else load_local_predictions()

if df_pred.empty:
    st.warning("Chưa có dữ liệu dự báo. Hãy chạy notebook 07_final_test.ipynb trước!")
    st.stop()

if "timestamp" in df_pred.columns:
    df_pred["timestamp"] = pd.to_datetime(df_pred["timestamp"])

all_sites = sorted(df_pred["site_id"].unique().tolist())

# Sidebar filters
st.sidebar.header("Bộ Lọc Dữ Liệu")
selected_sites = st.sidebar.multiselect("Chọn Trạm Quang Điện", all_sites, default=all_sites[:2])
scope = st.sidebar.selectbox("Phạm Vi Metric", ["measured_daylight", "measured", "all"])

min_date, max_date = df_pred["timestamp"].min().date(), df_pred["timestamp"].max().date()
date_range = st.sidebar.date_input("Khoảng Thời Gian", [min_date, max_date])

# Lọc dữ liệu
mask = df_pred["site_id"].isin(selected_sites)
if len(date_range) == 2:
    mask &= df_pred["timestamp"].dt.date.between(date_range[0], date_range[1])
filtered_df = df_pred[mask].sort_values("timestamp")

# Top Metric Cards
st.subheader("Chỉ Số Hiệu Năng Tổng Quan")
c1, c2, c3, c4 = st.columns(4)
overall_json = fetch_api("/metrics/overall")
if overall_json and scope in overall_json:
    m = overall_json[scope]
    c1.metric("WAPE (Ban ngày)", f"{m.get('wape', 0):.2f}%")
    c2.metric("RMSE", f"{m.get('rmse', 0):.4f}")
    c3.metric("MAE", f"{m.get('mae', 0):.4f}")
    c4.metric("R2 Score", f"{m.get('r2', 0):.4f}")

# BẢNG BENCHMARK SO SÁNH (ML MODEL VS BASELINES)
st.subheader("Bảng Benchmark So Sánh (LightGBM vs Baseline Models)")
base_api = fetch_api("/baseline")
df_base = pd.DataFrame(base_api) if base_api else load_local_baseline()

if not df_base.empty:
    bench_df = df_base[df_base["scope"] == scope].copy()
    cols_show = [c for c in ["horizon", "baseline_model", "evaluated_rows", "wape", "rmse", "mae", "r2"] if c in bench_df.columns]
    st.dataframe(bench_df[cols_show], use_container_width=True)
else:
    st.info("Chưa có dữ liệu baseline_metrics.csv từ notebook 06_0.")

# 1. Biểu đồ đường dự báo vs thực tế
st.subheader("1. So Sánh Chuỗi Thời Gian Dự Báo vs Thực Tế")
y_cols = [c for c in ["y_true", "y_pred", "y_true_h1", "y_pred_h1"] if c in filtered_df.columns]
fig_line = px.line(filtered_df, x="timestamp", y=y_cols, color_discrete_sequence=["blue", "orange"])
fig_line.update_layout(hovermode="x unified", template="plotly_white")
st.plotly_chart(fig_line, use_container_width=True)

# 2. Dải Min-Max dự báo theo giờ
st.subheader("2. Khoảng Min-Max Dự Báo Theo Giờ Trong Ngày")
if not filtered_df.empty:
    pred_col = "y_pred_h1" if "y_pred_h1" in filtered_df.columns else "y_pred"
    filtered_df["hour"] = filtered_df["timestamp"].dt.hour
    h_stats = filtered_df.groupby("hour")[pred_col].agg(["min", "max", "mean"]).reset_index()

    fig_band = go.Figure()
    fig_band.add_trace(go.Scatter(x=h_stats["hour"], y=h_stats["max"], mode="lines", name="Max", line=dict(width=0)))
    fig_band.add_trace(go.Scatter(x=h_stats["hour"], y=h_stats["min"], mode="lines", name="Min", fill="tonexty", fillcolor="rgba(255,165,0,0.2)", line=dict(width=0)))
    fig_band.add_trace(go.Scatter(x=h_stats["hour"], y=h_stats["mean"], mode="lines+markers", name="Trung bình", line=dict(color="orange", width=2)))
    fig_band.update_layout(xaxis_title="Giờ trong ngày", yaxis_title="Sản lượng (kWh)", template="plotly_white")
    st.plotly_chart(fig_band, use_container_width=True)

# 3 & 4. Sản Lượng Cộng Dồn & Bar Metric
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("3. Sản Lượng Cộng Dồn Theo Ngày")
    if not filtered_df.empty:
        filtered_df["date"] = filtered_df["timestamp"].dt.date
        pred_col = "y_pred_h1" if "y_pred_h1" in filtered_df.columns else "y_pred"
        d_sum = filtered_df.groupby("date")[pred_col].sum().cumsum().reset_index()
        fig_area = px.area(d_sum, x="date", y=pred_col)
        st.plotly_chart(fig_area, use_container_width=True)

with col_b:
    st.subheader("4. Chỉ Số RMSE Theo Từng Trạm")
    site_m = fetch_api("/metrics/by_site")
    df_sm = pd.DataFrame(site_m) if site_m else load_local_metrics()
    if not df_sm.empty and "rmse" in df_sm.columns:
        fig_bar = px.bar(df_sm, x="site_id", y="rmse", color="rmse")
        st.plotly_chart(fig_bar, use_container_width=True)
