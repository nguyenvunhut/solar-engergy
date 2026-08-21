"""Tang du lieu cua dashboard: doc artifact, tinh metric. KHONG chua UI.

File nay chi co ham xu ly du lieu - khong st.markdown tieu de, khong st.columns,
khong tao plotly figure. Cac trang trong pages/ import tu day roi chi lo hien thi.

BA NGUYEN TAC SAU LAN REFACTOR 2026-08-09
-----------------------------------------
1. Dashboard CHI DOC artifact pipeline da tinh san, KHONG goi model.predict().
   Ban cu co ham predict_on_test() chay inference ngay trong tang frontend, keo
   theo ca logic nhan nguoc chuan hoa k_target -> kWh. Logic do bi lap lai o day
   va co the lech voi pipeline that ma khong ai phat hien; da bo han.

2. Chi mot nguon chinh thuc: 07_final_test - model duoc chon tu validation,
   cham diem tren tap test niem phong. Ban cu khai bao 30
   hang duong dan, trong do 16 tro toi thu muc thi nghiem da xoa - da bo het.

3. Prophet la mo hinh doi chung duy nhat, doc tu 08_baseline_prophet_test - noi
   Prophet duoc do tren DUNG tap dong ma mo hinh duoc cham diem. Khong dung
   06_0_baseline cu: file do Prophet tu cat 80/20 rieng nen khac tap voi mo hinh.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Doi phien ban bang bien moi truong, vi du: DASHBOARD_VERSION=v4 streamlit run ...
# Mac dinh v3 de khong doi hanh vi cua nhung phien dang mo.
VERSION = os.environ.get("DASHBOARD_VERSION", "v5")
DATA_DIR = PROJECT_ROOT / "data" / "model" / VERSION

# ── Nguon chinh thuc duy nhat ────────────────────────────────────────────────
FINAL_DIR = DATA_DIR / "07_final_test"
PREDICTION_AUDIT = FINAL_DIR / "prediction_audit.parquet"
BEST_LOSS = FINAL_DIR / "best_loss.json"

# ── Doi chung Prophet, do tren dung tap dong cua mo hinh ─────────────────────
PROPHET_DIR = DATA_DIR / "08_baseline_prophet_test"
PROPHET_PRED = PROPHET_DIR / "prophet_test_predictions.parquet"
PROPHET_BY_SITE = PROPHET_DIR / "prophet_test_by_site.csv"
PROPHET_SUMMARY = PROPHET_DIR / "prophet_test_summary.json"

# ── Dac trung tap test (dung cho outlier_group va phan What-if) ──────────────
TEST_SELECTED = DATA_DIR / "05_selected" / f"{VERSION}_test_selected.parquet"
SELECTED_FEATURES = DATA_DIR / "05_selected" / "selected_features.json"
SHAP_DIR = DATA_DIR / "08_explain"

API_BASE_URL = os.environ.get("DASHBOARD_API_URL", "http://127.0.0.1:8000")

ACTUAL_COLOR = "#6366F1"    # Indigo - duong thuc te
PRED_COLOR = "#D9822B"      # Cam    - du bao mo hinh
PROPHET_COLOR = "#0E9F6E"   # Xanh la - doi chung Prophet
OUTLIER_COLOR = "#C23B22"
GRID_COLOR = "#D9DEE7"


# ══════════════════════════════════════════════════════════════════════════════
#  Doc artifact
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60)
def load_prediction_audit() -> pd.DataFrame:
    """Ket qua model duoc chon tren tap test niem phong."""
    if not PREDICTION_AUDIT.exists():
        return pd.DataFrame()
    df = pd.read_parquet(PREDICTION_AUDIT)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df.dropna(subset=["timestamp"])


@st.cache_data(ttl=60)
def load_prophet_predictions() -> pd.DataFrame:
    """Du bao Prophet tai cung cac moc thoi gian muc tieu voi mo hinh.

    Cot prophet_h{h} la gia tri Prophet du bao cho thoi diem T+h, doi chieu theo
    (site_id, timestamp) - tuc cung khoa voi prediction_audit.
    """
    if not PROPHET_PRED.exists():
        return pd.DataFrame()
    d = pd.read_parquet(PROPHET_PRED)
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    return d.dropna(subset=["timestamp"])


@st.cache_data(ttl=60)
def load_prophet_summary() -> dict:
    """Tom tat Skill Score cua mo hinh so voi Prophet, tren cung tap dong."""
    if not PROPHET_SUMMARY.exists():
        return {}
    return json.loads(PROPHET_SUMMARY.read_text(encoding="utf-8"))


@st.cache_data(ttl=60)
def load_prophet_by_site() -> pd.DataFrame:
    if not PROPHET_BY_SITE.exists():
        return pd.DataFrame()
    return pd.read_csv(PROPHET_BY_SITE)


@st.cache_data(ttl=60)
def load_best_loss() -> dict:
    """best_loss.json - ghi ro mo hinh nao thang va thang tren TAP NAO.

    Quan trong khi trinh bay: loss duoc chon HOAN TOAN tren tap validation, tap
    test khong tham gia vao quyet dinh nay.
    """
    if not BEST_LOSS.exists():
        return {}
    return json.loads(BEST_LOSS.read_text(encoding="utf-8"))


@st.cache_data(ttl=60)
def load_metrics(horizon: int) -> tuple[dict, pd.DataFrame]:
    """Metric chinh thuc do pipeline ghi ra (khong tinh lai trong dashboard)."""
    overall_path = FINAL_DIR / f"h{horizon}" / "metrics_overall.json"
    site_path = FINAL_DIR / f"h{horizon}" / "metrics_by_site.csv"
    overall = pd.read_json(overall_path, typ="series").to_dict() if overall_path.exists() else {}
    site = pd.read_csv(site_path) if site_path.exists() else pd.DataFrame()
    if not site.empty:
        site["horizon"] = int(horizon)
    return overall, site


@st.cache_data(ttl=60)
def load_outlier_group() -> pd.DataFrame:
    """Nhan outlier that tu tap test - prediction_audit khong mang cot nay."""
    if not TEST_SELECTED.exists():
        return pd.DataFrame()
    d = pd.read_parquet(TEST_SELECTED, columns=["site_id", "timestamp", "outlier_group"])
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    return d


@st.cache_data(ttl=60)
def load_shap_importance() -> pd.DataFrame:
    path = SHAP_DIR / "shap_importance_no_lag1.csv"
    if not path.exists():
        path = SHAP_DIR / "shap_importance.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
#  Tinh toan
# ══════════════════════════════════════════════════════════════════════════════
def _thong_ke(x: pd.DataFrame, tc: str, pc: str) -> dict:
    err = x[pc] - x[tc]
    mau = x[tc].abs().sum()
    ss_tot = ((x[tc] - x[tc].mean()) ** 2).sum()
    return {
        "wape": float(err.abs().sum() / mau * 100) if mau > 0 else float("nan"),
        "rmse": float(np.sqrt((err**2).mean())),
        "mae": float(err.abs().mean()),
        "r2": float(1 - (err**2).sum() / ss_tot) if ss_tot > 0 else float("nan"),
        "n": int(len(x)),
    }


@st.cache_data(ttl=60)
def audit_metrics(_df: pd.DataFrame, horizon: int, cache_key: str = "") -> tuple[dict, pd.DataFrame]:
    """Tinh metric tai cho cho bat ky nguon nao co y_true_h/y_pred_h."""
    df = _df
    tc, pc = f"y_true_h{horizon}", f"y_pred_h{horizon}"
    if df.empty or tc not in df.columns:
        return {}, pd.DataFrame()
    d = df.dropna(subset=[tc, pc]).copy()
    # SUA 2026-08-22: pham vi phai TRUNG voi con so cong bo trong bao cao:
    #   nhan la do that  &  ban ngay  &  khong vuot tran cong suat vat ly,
    # va cả ba dieu kien xet tai MOC NHAN T+h (cot nhan_*), khong phai tai T.
    # Ban cu chi loc is_daylight tai T nen gom ca dong ETL dien khuyet (de doan hon)
    # va cho ra WAPE thap hon bao cao 0,60 diem o H1 va 0,80 diem o H4.
    _ng = d.get(f"nhan_energy_source_h{horizon}", d.get("energy_source"))
    _bn = d.get(f"nhan_is_daylight_h{horizon}", d.get("is_daylight"))
    _og = d.get(f"nhan_outlier_group_h{horizon}")
    if _bn is not None:
        d = d[_bn.reindex(d.index).fillna(False).astype(bool)]
    if _ng is not None:
        d = d[_ng.reindex(d.index).astype(str) == "measured"]
    if _og is not None:
        d = d[_og.reindex(d.index).astype(str) != "physical_over_capacity"]
    overall = {"measured_daylight": _thong_ke(d, tc, pc)}
    by_site = (
        d.groupby("site_id")
        .apply(lambda x: pd.Series(_thong_ke(x, tc, pc)), include_groups=False)
        .reset_index()
    )
    by_site["site_id"] = by_site["site_id"].astype(str)
    by_site["horizon"] = int(horizon)
    return overall, by_site


def he_so_tre_phut(d: pd.DataFrame, col_true: str, col_pred: str) -> float:
    """Do tre theo do doc: pred(t) ~ actual(t - c buoc) => err ~ -c * doc.

    Chi so nay tach sai BIEN DO ra khoi sai THOI DIEM: du bao cao hay thap deu
    khong anh huong, chi lech thoi diem moi lam no khac 0. Tra ve so phut.
    """
    x = d.sort_values(["site_id", "timestamp"]).copy()
    g = x.groupby("site_id")[col_true]
    doc = (g.shift(-1) - g.shift(1)) / 2
    err = x[col_pred] - x[col_true]
    m = doc.notna() & err.notna()
    if "is_daylight" in x.columns:
        m = m & x["is_daylight"].fillna(False).astype(bool)
    a, b = doc[m].to_numpy(), err[m].to_numpy()
    if a.size < 50 or (a**2).sum() == 0:
        return float("nan")
    return -float((a * b).sum() / (a * a).sum()) * 15


def skill_score(wape_model: float, wape_baseline: float) -> float:
    """SS = (1 - WAPE_mo_hinh / WAPE_doi_chung) x 100%."""
    if not wape_baseline or np.isnan(wape_baseline) or wape_baseline == 0:
        return float("nan")
    return (1 - wape_model / wape_baseline) * 100.0


def metric_value(overall: dict, key: str) -> float | None:
    scope = overall.get("measured_daylight")
    if isinstance(scope, dict) and key in scope:
        return scope.get(key)
    return None


def with_display_timestamp(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Them cot thoi diem de ve: moc MUC TIEU T+h, khong phai moc lay dac trung."""
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
