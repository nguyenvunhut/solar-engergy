"""Backend cho dashboard: doc du lieu, predict, tinh metric.

Tach ra tu pages/1_TimeSeries.py (truoc day gan 1150 dong gom ca UI lan logic
xu ly du lieu chung 1 file). File nay CHI chua ham xu ly du lieu (load parquet,
goi model, tinh WAPE/RMSE...) - khong chua doan ve UI (khong st.markdown tieu
de, khong st.columns, khong tao plotly figure). pages/1_TimeSeries.py import
tu day roi chi lo phan hien thi.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "model" / "v3"
PREDICTION_AUDIT = DATA_DIR / "07_final_test" / "prediction_audit.parquet"
OVERFIT_AUDIT = DATA_DIR / "06_13_overfit_plot_audit" / "prediction_audit.parquet"
CORRECT_TIME_AUDIT = DATA_DIR / "06_14_weather_correct_time" / "prediction_audit_h1.parquet"
CORRECT_TIME_LAG_AUDIT = (
    DATA_DIR / "06_16_weather_correct_time_lag96_lag4" / "prediction_audit_h1.parquet"
)
CORRECT_TIME_LAG96_AUDIT = (
    DATA_DIR / "06_15_weather_correct_time_lag96" / "prediction_audit_h1.parquet"
)
PHASE_ENSEMBLE_AUDIT = (
    DATA_DIR / "06_17_phase_balanced_ensemble" / "prediction_audit_h1.parquet"
)
SITE_SPECIFIC_AUDIT = DATA_DIR / "06_18_site_specific" / "prediction_audit_h1.parquet"
TARGET_EXOGENOUS_AUDIT = DATA_DIR / "06_19_target_exogenous_h1" / "prediction_audit_h1.parquet"
PVLIB_LAG96_AUDIT = DATA_DIR / "06_20_pvlib_lag96_h1" / "prediction_audit_h1.parquet"
KAGGLE_EARLYSTOP_AUDIT = (
    PROJECT_ROOT
    / "data"
    / "experiments"
    / "forecasting_v3_outputs_slim_earlystoping"
    / "data"
    / "model"
    / "v3_final_cleaned"
    / "07_metrics"
    / "kaggle_v3_main_huber_regularization_20_trials"
    / "prediction_audit.parquet"
)
METRICS_DIR = DATA_DIR / "07_final_test"
PURE_WEATHER_DIR = DATA_DIR / "06_5_pure_weather"
VAL_SELECTED = DATA_DIR / "05_selected" / "v3_val_selected.parquet"
TEST_SELECTED = DATA_DIR / "05_selected" / "v3_test_selected.parquet"
TEST_SELECTED_FIX15 = DATA_DIR / "05_selected_fix15" / "v3_test_selected.parquet"
FIX15_DIR = DATA_DIR / "06_6_fix15"
SOLAR_DIR = DATA_DIR / "06_7_solar"
FINAL_KHONG_TRE = DATA_DIR / "06_1_khu_tre_pha" / "prediction_audit_h1.parquet"
FINAL_KHONG_TRE_H4 = DATA_DIR / "06_1_khu_tre_pha_h4" / "prediction_audit_h4.parquet"
HUBER_PRED = DATA_DIR / "06_2_train_huber" / "prediction_audit_h1.parquet"
HUBER_PRED_H4 = DATA_DIR / "06_2_train_huber_h4" / "prediction_audit_h4.parquet"
MSE_PRED = DATA_DIR / "06_3_train_mse" / "prediction_audit_h1.parquet"
MSE_PRED_H4 = DATA_DIR / "06_3_train_mse_h4" / "prediction_audit_h4.parquet"
BO_GOC_PRED = DATA_DIR / "07_kiem_tra_bo_goc" / "prediction_bo_goc_h1.parquet"
TARGET_ALIGNED_DIR = DATA_DIR / "06_12_target_aligned"
MLMART_BASE = PROJECT_ROOT / "data" / "mlmart_base" / "v3_final_cleaned.parquet"
BASELINE_PATH = DATA_DIR / "06_0_baseline" / "baseline_metrics.csv"
SHAP_DIR = DATA_DIR / "08_explain"
NEW_METRICS_DIR = (
    PROJECT_ROOT
    / "srcs"
    / "07_dashboard_v3_2_artifacts"
    / "data"
    / "model"
    / "v3_final_cleaned"
    / "07_metrics"
    / "kaggle_v3_main_huber_regularization_20_trials"
)

ACTUAL_COLOR = "#6366F1"   # Indigo - dong bo theme moi
PRED_COLOR = "#D9822B"
OUTLIER_COLOR = "#C23B22"
GRID_COLOR = "#D9DEE7"


@st.cache_data(ttl=60)
def load_prediction_audit() -> pd.DataFrame:
    df = pd.read_parquet(PREDICTION_AUDIT)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df.dropna(subset=["timestamp"])


def predict_on_test(model, feats, medians, horizon, label_offset_steps, test_path=None,
                     chuan_hoa=False, cot_quy_mo=None, cot_sin_elev=None, cot_tran=None,
                     eps_elev=0.02) -> pd.DataFrame:
    """Chay inference tren tap test. label_offset_steps la so buoc dich cua nhan (quy uoc train).

    Cac dac trung ket thuc bang '_mt' (COT_TAT_DINH trong notebook 06) la gia tri TAT DINH
    (hinh hoc mat troi...) tai thoi diem MUC TIEU T+h, khong luu san trong TEST_SELECTED
    (file goc 05_selected) - notebook chi tinh runtime bang shift(-h) tren cot goc. Phai tu
    tinh lai o day, khong duoc bo qua/dien median, vi day la gia tri tat dinh biet truoc
    duoc (khong phai leak), model duoc train voi gia tri dung.

    Neu chuan_hoa=True (model_config.json cua notebook 06 co 'chuan_hoa': true), model KHONG
    du bao thang kWh - no du bao ty le k_target = energy / (site_scale * sin_elevation), gioi
    han [0, 1.5]. Phai nhan nguoc dung cong thuc notebook da dung luc train, neu khong y_pred
    se ra toan so gan 0-1.5 trong khi y_true la kWh thuc (hang chuc) - "du bao duoi dat, thuc
    te tren troi" dung nhu bug da gap.
    """
    path = test_path or TEST_SELECTED
    mt_feats = [c for c in feats if c.endswith("_mt")]
    mt_base_cols = [c[:-3] for c in mt_feats if c[:-3] not in mt_feats]
    base_cols = ["site_id", "timestamp", "energy_generated_kwh", "is_daylight", "outlier_group"]
    chuan_hoa_cols = [c for c in (cot_quy_mo, cot_sin_elev, cot_tran) if chuan_hoa and c]
    have = set(pq.ParquetFile(path).schema_arrow.names)
    cols = [c for c in dict.fromkeys(list(feats) + base_cols + mt_base_cols + chuan_hoa_cols) if c in have]
    d = pd.read_parquet(path, columns=cols).sort_values(["site_id", "timestamp"])

    if label_offset_steps:
        target = d.groupby("site_id")["energy_generated_kwh"].shift(-int(label_offset_steps))
    else:
        target = d["energy_generated_kwh"]
    keep = target.notna()
    d = d[keep.to_numpy()].copy()
    d[f"y_true_h{horizon}"] = target[keep].to_numpy()

    for mt_col in mt_feats:
        base_col = mt_col[:-3]
        if mt_col not in d.columns and base_col in d.columns:
            d[mt_col] = d.groupby("site_id")[base_col].shift(-int(label_offset_steps))

    raw_pred = model.predict(d[feats].fillna(medians).astype(np.float32))
    if chuan_hoa and cot_quy_mo in d.columns and cot_sin_elev in d.columns:
        k_pred = np.clip(raw_pred, 0, 1.5)
        mau = d[cot_quy_mo].to_numpy() * np.clip(d[cot_sin_elev].to_numpy(), eps_elev, None)
        y_pred = k_pred * mau
        if cot_tran in d.columns:
            y_pred = np.minimum(y_pred, d[cot_tran].to_numpy() * 1.02)
        y_pred = np.where(d[cot_sin_elev].to_numpy() <= eps_elev, 0.0, y_pred)
        d[f"y_pred_h{horizon}"] = y_pred
    else:
        d[f"y_pred_h{horizon}"] = raw_pred
    d[f"plot_timestamp_h{horizon}"] = d["timestamp"] + pd.to_timedelta(int(label_offset_steps) * 15, unit="m")
    cols_out = ["site_id", "timestamp", "is_daylight", "outlier_group",
                f"y_true_h{horizon}", f"y_pred_h{horizon}", f"plot_timestamp_h{horizon}"]
    return d[[c for c in cols_out if c in d.columns]]


def merge_horizon_frames(frames: dict) -> pd.DataFrame:
    keys = sorted(frames)
    out = frames[keys[0]]
    for h in keys[1:]:
        drop = [c for c in ("is_daylight", "outlier_group") if c in frames[h].columns]
        out = out.merge(frames[h].drop(columns=drop), on=["site_id", "timestamp"], how="outer")
    return out


def he_so_tre_phut(d: pd.DataFrame, col_true: str, col_pred: str) -> float:
    """Do tre theo do doc: pred(t) ~ actual(t - c buoc) => err ~ -c * doc. Tra ve c tinh bang phut.
    Chi so nay tach sai BIEN DO ra khoi sai THOI DIEM: du bao cao hay thap deu khong anh huong."""
    x = d.sort_values(["site_id", "timestamp"]).copy()
    g = x.groupby("site_id")[col_true]
    doc = (g.shift(-1) - g.shift(1)) / 2
    err = x[col_pred] - x[col_true]
    m = doc.notna() & err.notna()
    if "is_daylight" in x.columns:
        m = m & x["is_daylight"].fillna(False).astype(bool)
    a = doc[m].to_numpy()
    b = err[m].to_numpy()
    if a.size < 50 or (a ** 2).sum() == 0:
        return float("nan")
    return -float((a * b).sum() / (a * a).sum()) * 15


@st.cache_data(ttl=60)
def load_bo_goc_audit() -> pd.DataFrame:
    """Du bao train tren BO DU LIEU GOC (truoc khi sua ETL). h1: target = T+15 phut."""
    if not BO_GOC_PRED.exists():
        return pd.DataFrame()
    d = pd.read_parquet(BO_GOC_PRED)
    d["timestamp"] = pd.to_datetime(d["timestamp"])
    d = d.rename(columns={"y_true": "y_true_h1", "y_pred": "y_pred_h1"})
    d["plot_timestamp_h1"] = pd.to_datetime(d["plot_timestamp"])
    return d


@st.cache_data(ttl=60)
def load_final_khong_tre() -> pd.DataFrame:
    """06_1: downscale thoi tiet 15 phut, goc mat troi, quy mo tram, lag_1 + lag_96. Gop them
    H4 (06_1_khu_tre_pha_h4) neu da train, de selectbox Horizon co ca h1 va h4."""
    if not FINAL_KHONG_TRE.exists():
        return pd.DataFrame()
    d = pd.read_parquet(FINAL_KHONG_TRE)
    d["timestamp"] = pd.to_datetime(d["timestamp"])
    d = d.rename(columns={"y_true": "y_true_h1", "y_pred": "y_pred_h1"})
    d["plot_timestamp_h1"] = pd.to_datetime(d["plot_timestamp"])

    if FINAL_KHONG_TRE_H4.exists():
        d4 = pd.read_parquet(FINAL_KHONG_TRE_H4)
        d4["timestamp"] = pd.to_datetime(d4["timestamp"])
        d4 = d4.rename(columns={
            "y_true": "y_true_h4", "y_pred": "y_pred_h4",
            "plot_timestamp": "plot_timestamp_h4",
        })
        d4["plot_timestamp_h4"] = pd.to_datetime(d4["plot_timestamp_h4"])
        _h4_cols = ["site_id", "timestamp", "y_true_h4", "y_pred_h4", "plot_timestamp_h4"]
        d = d.merge(d4[_h4_cols], on=["site_id", "timestamp"], how="outer")

    return d


API_BASE_URL = os.environ.get("DASHBOARD_API_URL", "http://127.0.0.1:8000")


@st.cache_data(ttl=60)
def load_via_api() -> pd.DataFrame:
    """Doc prediction qua FastAPI (srcs/07_dashboard/api.py) thay vi doc file
    truc tiep - minh hoa dashboard co the tach khoi logic doc du lieu. Can chay
    truoc: uvicorn srcs.07_dashboard.api:app --port 8000 (tu thu muc goc repo)."""
    import requests

    try:
        resp = requests.get(f"{API_BASE_URL}/predictions", params={"limit": 200000}, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        st.error(f"Loi goi API ({API_BASE_URL}): {type(e).__name__}: {e}")
        return pd.DataFrame()
    rows = resp.json()
    if not rows:
        return pd.DataFrame()
    d = pd.DataFrame(rows)
    d["timestamp"] = pd.to_datetime(d["timestamp"])
    d = d.rename(columns={"y_true": "y_true_h1", "y_pred": "y_pred_h1"})
    if "plot_timestamp" in d.columns:
        d["plot_timestamp_h1"] = pd.to_datetime(d["plot_timestamp"])
    else:
        d["plot_timestamp_h1"] = d["timestamp"] + pd.to_timedelta(15, unit="m")
    return d


@st.cache_data(ttl=60)
def load_pred_simple(path_h1: Path, path_h4: Path) -> pd.DataFrame:
    """Doc thang prediction_audit da tinh san (notebook 06_2/06_3 tu nhan nguoc chuan hoa
    va export ra kWh that, giong het 06_1) - KHONG goi model.predict() trong Streamlit,
    tranh lech logic voi notebook."""
    if not path_h1.exists():
        return pd.DataFrame()
    d = pd.read_parquet(path_h1)
    d["timestamp"] = pd.to_datetime(d["timestamp"])
    d = d.rename(columns={"y_true": "y_true_h1", "y_pred": "y_pred_h1"})
    d["plot_timestamp_h1"] = pd.to_datetime(d["plot_timestamp"])

    if path_h4.exists():
        d4 = pd.read_parquet(path_h4)
        d4["timestamp"] = pd.to_datetime(d4["timestamp"])
        d4 = d4.rename(columns={
            "y_true": "y_true_h4", "y_pred": "y_pred_h4",
            "plot_timestamp": "plot_timestamp_h4",
        })
        d4["plot_timestamp_h4"] = pd.to_datetime(d4["plot_timestamp_h4"])
        _h4_cols = ["site_id", "timestamp", "y_true_h4", "y_pred_h4", "plot_timestamp_h4"]
        d = d.merge(d4[_h4_cols], on=["site_id", "timestamp"], how="outer")
    return d


def trained_variants() -> list[str]:
    """Cac bien the da train trong 06_train: mse, mae, huber, huber_no_lag1, huber_no_lag_rolling..."""
    root = DATA_DIR / "06_train"
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and (p / "h1" / "model.pkl").exists())


@st.cache_data(ttl=60)
def load_variant_audit(variant: str) -> pd.DataFrame:
    """Inference bien the 06_train tren TAP TEST. Quy uoc nhan cu: h1 -> y(t), h4 -> y(t+3 buoc)."""
    import pickle

    root = DATA_DIR / "06_train" / variant
    frames = {}
    for h in (1, 4):
        model_path = root / f"h{h}" / "model.pkl"
        config_path = root / f"h{h}" / "model_config.json"
        if not model_path.exists() or not config_path.exists():
            continue
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        with open(model_path, "rb") as fh:
            model = pickle.load(fh)
        medians = pd.Series(cfg.get("feature_medians", {}), dtype="float64")
        configured_horizon = int(cfg.get("horizon_steps", -1))
        if configured_horizon != h:
            raise ValueError(
                f"Model {variant}/h{h} khai bao horizon_steps={configured_horizon}"
            )
        # Notebook 06 da tu export X_test_h{h}.parquet ngay canh model.pkl, da co san cac
        # cot '_mt' tinh dung luc train - uu tien doc file nay thay vi TEST_SELECTED (file
        # tho, thieu cot '_mt') de khong phai tai tao lai bang shift() o predict_on_test.
        _x_test_path = root / f"h{h}" / f"X_test_h{h}.parquet"
        frames[h] = predict_on_test(
            model, list(cfg["features"]), medians, h, label_offset_steps=h,
            test_path=_x_test_path if _x_test_path.exists() else None,
            chuan_hoa=bool(cfg.get("chuan_hoa")),
            cot_quy_mo=cfg.get("cot_quy_mo"), cot_sin_elev=cfg.get("cot_sin_elev"),
            cot_tran=cfg.get("cot_tran"), eps_elev=float(cfg.get("eps_elev", 0.02)),
        )

    if not frames:
        return pd.DataFrame()
    return merge_horizon_frames(frames)


@st.cache_data(ttl=60)
def audit_metrics(_df: pd.DataFrame, horizon: int, cache_key: str = "") -> tuple[dict, pd.DataFrame]:
    """Tinh metric tai cho cho bat ky nguon nao co y_true_h/y_pred_h."""
    df = _df
    tc, pc = f"y_true_h{horizon}", f"y_pred_h{horizon}"
    if df.empty or tc not in df.columns:
        return {}, pd.DataFrame()
    d = df.dropna(subset=[tc, pc]).copy()
    if "is_daylight" in d.columns:
        d = d[d["is_daylight"].fillna(False).astype(bool)]

    def _stats(x: pd.DataFrame) -> dict:
        err = x[pc] - x[tc]
        denom = x[tc].abs().sum()
        ss_tot = ((x[tc] - x[tc].mean()) ** 2).sum()
        return {
            "wape": float(err.abs().sum() / denom * 100) if denom > 0 else float("nan"),
            "rmse": float(np.sqrt((err**2).mean())),
            "mae": float(err.abs().mean()),
            "r2": float(1 - (err**2).sum() / ss_tot) if ss_tot > 0 else float("nan"),
            "n": int(len(x)),
        }

    overall = {"measured_daylight": _stats(d)}
    by_site = d.groupby("site_id").apply(lambda x: pd.Series(_stats(x)), include_groups=False).reset_index()
    by_site["site_id"] = by_site["site_id"].astype(str)
    by_site["horizon"] = int(horizon)
    return overall, by_site


@st.cache_data(ttl=60)
def lag_scan(_df: pd.DataFrame, horizon: int, site_id: str | None = None, cache_key: str = "") -> pd.DataFrame:
    """Voi moi do dich k, tinh RMSE giua du_bao(t) va thuc_te(t+k). k=0 la khong tre."""
    df = _df
    tc, pc = f"y_true_h{horizon}", f"y_pred_h{horizon}"
    if df.empty or tc not in df.columns:
        return pd.DataFrame()
    d = df[["site_id", "timestamp", tc, pc]].dropna().sort_values(["site_id", "timestamp"])
    if "is_daylight" in df.columns:
        mask = df.loc[d.index, "is_daylight"].fillna(False).astype(bool)
        d = d[mask.to_numpy()]
    if site_id is not None:
        d = d[d["site_id"].astype(str).eq(str(site_id))]
    if d.empty:
        return pd.DataFrame()

    grp = d.groupby("site_id")[tc]
    rows = []
    for k in range(-4, 5):
        shifted = grp.shift(-k)
        keep = shifted.notna()
        if keep.sum() < 50:
            continue
        err = d.loc[keep, pc] - shifted[keep]
        rows.append(
            {
                "do_dich_buoc": k,
                "do_dich_phut": k * 15,
                "so_dong": int(keep.sum()),
                "rmse": float(np.sqrt((err**2).mean())),
                "mae": float(err.abs().mean()),
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(ttl=60)
def load_metrics(horizon: int) -> tuple[dict, pd.DataFrame]:
    overall_path = METRICS_DIR / f"h{horizon}" / "metrics_overall.json"
    site_path = METRICS_DIR / f"h{horizon}" / "metrics_by_site.csv"
    overall = pd.read_json(overall_path, typ="series").to_dict() if overall_path.exists() else {}
    site = pd.read_csv(site_path) if site_path.exists() else pd.DataFrame()
    if not site.empty:
        site["horizon"] = int(horizon)
    return overall, site


@st.cache_data(ttl=60)
def load_baseline() -> pd.DataFrame:
    return pd.read_csv(BASELINE_PATH) if BASELINE_PATH.exists() else pd.DataFrame()


@st.cache_data(ttl=60)
def load_new_site_metrics(horizon: int) -> pd.DataFrame:
    path = NEW_METRICS_DIR / "metrics_by_site.csv"
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    if not df.empty and "horizon" in df.columns:
        df = df[df["horizon"].astype(str).eq(str(horizon))].copy()
        if "scope" in df.columns:
            df = df[df["scope"].astype(str).isin(["headline", "normal_rows", "eligible_rows"])]
    return df


@st.cache_data(ttl=60)
def load_shap_importance() -> pd.DataFrame:
    path = SHAP_DIR / "shap_importance_no_lag1.csv"
    if not path.exists():
        path = SHAP_DIR / "shap_importance.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def metric_value(overall: dict, key: str) -> float | None:
    scope = overall.get("measured_daylight")
    if isinstance(scope, dict) and key in scope:
        return scope.get(key)
    return None


def with_display_timestamp(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    out = df.copy()
    plot_col = f"plot_timestamp_h{horizon}"
    label_col = f"label_timestamp_h{horizon}"
    if plot_col in out.columns:
        out["display_timestamp"] = pd.to_datetime(out[plot_col], errors="coerce")
    elif label_col in out.columns:
        out["display_timestamp"] = pd.to_datetime(out[label_col], errors="coerce")
    else:
        out["display_timestamp"] = out["timestamp"] + pd.to_timedelta(int(horizon) * 15, unit="m")
    return out.dropna(subset=["display_timestamp"]).sort_values("display_timestamp")
