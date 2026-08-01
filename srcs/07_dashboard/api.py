import ctypes
import glob
import json
from pathlib import Path

# Pre-load libstdc++.so.6 into global symbol table for C-extensions on Linux/NixOS
for _p in (
    glob.glob("/nix/store/*gcc*/lib/libstdc++.so.6")
    + glob.glob("/usr/lib*/libstdc++.so.6")
    + glob.glob("/run/current-system/sw/lib/libstdc++.so.6")
):
    try:
        ctypes.CDLL(_p, mode=ctypes.RTLD_GLOBAL)
        break
    except Exception:
        pass

from fastapi import FastAPI, HTTPException
import pandas as pd

app = FastAPI(title="Energy Forecasting API")


def _safe_records(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> list[dict] an toan cho JSON. NaN/NaT khong hop le trong JSON
    chuan (gay ValueError: Out of range float values are not JSON compliant),
    phai doi thanh None truoc khi tra ve."""
    return df.astype(object).where(pd.notnull(df), None).to_dict(orient="records")

# Cau hinh duong dan du lieu tu goc repository
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "model" / "v3"

# Model chinh dang dung tren dashboard (06_1 = MAE, khu tre pha, co lag_4).
# 07_final_test/prediction_audit.parquet la ket qua chinh thuc da qua notebook 07
# (so sanh MSE/MAE/Huber, chon mo hinh vo dich) - dung file nay lam nguon /predictions.
PRED_H1 = DATA_DIR / "07_final_test" / "prediction_audit.parquet"
FALLBACK_PRED_H1 = DATA_DIR / "06_1_khu_tre_pha" / "prediction_audit_h1.parquet"
BASELINE_COMPARISON = DATA_DIR / "06_0_baseline" / "baseline_comparison_final.csv"
SHAP_IMPORTANCE = DATA_DIR / "08_explain" / "shap_importance.csv"
SHAP_VALUES = DATA_DIR / "08_explain" / "shap_values.parquet"

STORE: dict = {}


@app.on_event("startup")
def startup_event():
    # 1. Metrics overall + theo site, tach rieng h1/h4 (tu notebook 07)
    for h in ("h1", "h4"):
        p_overall = DATA_DIR / "07_final_test" / h / "metrics_overall.json"
        if p_overall.exists():
            with open(p_overall, "r", encoding="utf-8") as f:
                STORE[f"metrics_overall_{h}"] = json.load(f)
        p_site = DATA_DIR / "07_final_test" / h / "metrics_by_site.csv"
        if p_site.exists():
            STORE[f"metrics_by_site_{h}"] = pd.read_csv(p_site)

    p_best_loss = DATA_DIR / "07_final_test" / "best_loss.json"
    if p_best_loss.exists():
        with open(p_best_loss, "r", encoding="utf-8") as f:
            STORE["best_loss"] = json.load(f)

    # 2. Prediction audit - uu tien ket qua chinh thuc tu 07, fallback ve 06_1 truc tiep
    pred_path = PRED_H1 if PRED_H1.exists() else FALLBACK_PRED_H1
    if pred_path.exists():
        df_pred = pd.read_parquet(pred_path)
        if "timestamp" in df_pred.columns:
            df_pred["timestamp"] = pd.to_datetime(df_pred["timestamp"])
        STORE["predictions"] = df_pred
        if "site_id" in df_pred.columns:
            STORE["sites"] = sorted(df_pred["site_id"].astype(str).unique().tolist())

    # 3. Baseline so sanh (Prophet) - KHONG con Persistence, da bo theo yeu cau
    if BASELINE_COMPARISON.exists():
        df_base = pd.read_csv(BASELINE_COMPARISON)
        STORE["baseline"] = df_base[~df_base["model"].str.contains("Persistence", na=False)]

    # 4. SHAP importance + values tu notebook 08
    if SHAP_IMPORTANCE.exists():
        STORE["shap_importance"] = pd.read_csv(SHAP_IMPORTANCE)
    if SHAP_VALUES.exists():
        STORE["shap_values"] = pd.read_parquet(SHAP_VALUES)


@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Chao mung ban den voi Energy Forecasting API (Group The Outliers)",
        "documentation_swagger": "/docs",
        "available_endpoints": [
            "/sites",
            "/metrics/overall",
            "/metrics/by_site",
            "/predictions",
            "/baseline",
            "/shap/importance",
            "/shap/values",
        ],
    }


@app.get("/sites")
def get_sites():
    if "sites" not in STORE:
        raise HTTPException(404, "Chua co du lieu danh sach tram, hay chay notebook 07 truoc.")
    return {"sites": STORE["sites"]}


@app.get("/metrics/overall")
def get_metrics_overall(horizon: str = "h1"):
    key = f"metrics_overall_{horizon}"
    if key not in STORE:
        raise HTTPException(
            404, f"Chua co metrics_overall cho {horizon}, hay chay notebook 07 truoc."
        )
    return STORE[key]


@app.get("/metrics/by_site")
def get_metrics_by_site(horizon: str = "h1"):
    key = f"metrics_by_site_{horizon}"
    if key not in STORE:
        raise HTTPException(
            404, f"Chua co metrics_by_site cho {horizon}, hay chay notebook 07 truoc."
        )
    return _safe_records(STORE[key])


@app.get("/predictions")
def get_predictions(
    site_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = 2000,
):
    if "predictions" not in STORE:
        raise HTTPException(
            404, "Chua co prediction_audit.parquet, hay chay notebook 06_1/07 truoc."
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
    if "plot_timestamp" in out.columns:
        out["plot_timestamp"] = pd.to_datetime(out["plot_timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return _safe_records(out.head(limit))


@app.get("/baseline")
def get_baseline():
    if "baseline" not in STORE:
        raise HTTPException(
            404, "Chua co baseline_comparison_final.csv, hay chay notebook 06_0b truoc."
        )
    return _safe_records(STORE["baseline"])


@app.get("/shap/importance")
def get_shap_importance():
    if "shap_importance" not in STORE:
        raise HTTPException(404, "Chua co shap_importance.csv, hay chay notebook 08 truoc.")
    return _safe_records(STORE["shap_importance"])


@app.get("/shap/values")
def get_shap_values(limit: int = 500):
    if "shap_values" not in STORE:
        raise HTTPException(404, "Chua co shap_values.parquet, hay chay notebook 08 truoc.")
    df = STORE["shap_values"].head(limit).copy()
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return _safe_records(df)
