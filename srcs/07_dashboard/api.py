import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
import pandas as pd

app = FastAPI(title="Energy Forecasting API")

# Cấu hình đường dẫn dữ liệu từ gốc repository
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "model" / "v3"

# Biến global lưu dữ liệu nạp 1 lần lúc khởi động
STORE = {}


@app.on_event("startup")
def startup_event():
    # 1. Metrics overall từ notebook 07
    p_overall = DATA_DIR / "07_final_test" / "metrics_overall.json"
    if p_overall.exists():
        with open(p_overall, "r", encoding="utf-8") as f:
            STORE["metrics_overall"] = json.load(f)

    # 2. Metrics by site từ notebook 07
    p_site = DATA_DIR / "07_final_test" / "metrics_by_site.csv"
    if p_site.exists():
        STORE["metrics_by_site"] = pd.read_csv(p_site)

    # 3. Prediction audit từ notebook 07
    p_pred = DATA_DIR / "07_final_test" / "prediction_audit.parquet"
    if p_pred.exists():
        df_pred = pd.read_parquet(p_pred)
        if "timestamp" in df_pred.columns:
            df_pred["timestamp"] = pd.to_datetime(df_pred["timestamp"])
        STORE["predictions"] = df_pred
        if "site_id" in df_pred.columns:
            STORE["sites"] = sorted(df_pred["site_id"].unique().tolist())

    # 4. Baseline metrics từ notebook 06_0
    p_base = DATA_DIR / "06_0_baseline" / "baseline_metrics.csv"
    if p_base.exists():
        STORE["baseline"] = pd.read_csv(p_base)

    # 5. SHAP importance từ notebook 08
    p_shap_imp = DATA_DIR / "08_explain" / "shap_importance.csv"
    if p_shap_imp.exists():
        STORE["shap_importance"] = pd.read_csv(p_shap_imp)

    # 6. SHAP values từ notebook 08
    p_shap_val = DATA_DIR / "08_explain" / "shap_values.parquet"
    if p_shap_val.exists():
        STORE["shap_values"] = pd.read_parquet(p_shap_val)


@app.get("/sites")
def get_sites():
    if "sites" not in STORE:
        raise HTTPException(
            404, "Chưa có dữ liệu danh sách trạm, hãy chạy notebook 07 trước."
        )
    return {"sites": STORE["sites"]}


@app.get("/metrics/overall")
def get_metrics_overall():
    if "metrics_overall" not in STORE:
        raise HTTPException(
            404, "Chưa có file metrics_overall.json, hãy chạy notebook 07 trước."
        )
    return STORE["metrics_overall"]


@app.get("/metrics/by_site")
def get_metrics_by_site():
    if "metrics_by_site" not in STORE:
        raise HTTPException(
            404, "Chưa có file metrics_by_site.csv, hãy chạy notebook 07 trước."
        )
    return STORE["metrics_by_site"].to_dict(orient="records")


@app.get("/predictions")
def get_predictions(
    site_id: str | None = None, start: str | None = None, end: str | None = None
):
    if "predictions" not in STORE:
        raise HTTPException(
            404,
            "Chưa có file prediction_audit.parquet, hãy chạy notebook 07 trước.",
        )
    df = STORE["predictions"]
    if site_id:
        df = df[df["site_id"].astype(str) == str(site_id)]
    if start and "timestamp" in df.columns:
        df = df[df["timestamp"] >= pd.to_datetime(start)]
    if end and "timestamp" in df.columns:
        df = df[df["timestamp"] <= pd.to_datetime(end)]
    out = df.copy()
    if "timestamp" in out.columns:
        out["timestamp"] = out["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return out.head(2000).to_dict(orient="records")


@app.get("/baseline")
def get_baseline():
    if "baseline" not in STORE:
        raise HTTPException(
            404, "Chưa có file baseline_metrics.csv, hãy chạy notebook 06_0 trước."
        )
    return STORE["baseline"].to_dict(orient="records")


@app.get("/shap/importance")
def get_shap_importance():
    if "shap_importance" not in STORE:
        raise HTTPException(
            404, "Chưa có file shap_importance.csv, hãy chạy notebook 08 trước."
        )
    return STORE["shap_importance"].to_dict(orient="records")


@app.get("/shap/values")
def get_shap_values(limit: int = 500):
    if "shap_values" not in STORE:
        raise HTTPException(
            404, "Chưa có file shap_values.parquet, hãy chạy notebook 08 trước."
        )
    df = STORE["shap_values"].head(limit).copy()
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    return df.to_dict(orient="records")
