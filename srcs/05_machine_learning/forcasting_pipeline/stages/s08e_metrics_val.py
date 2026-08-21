"""Stage 08e: tinh metrics_val.json theo DUNG cach notebook 06_4 lam.

NGUON: notebook 06_4_validate_model_selection.ipynb, ham load_val_folds() + eval_one().

VI SAO PHAI CO FILE RIENG NAY (doc ky truoc khi sua):
  Trong bo notebook co HAI dinh nghia khac nhau ve "tap validation":

  (1) notebook 06_1/2/3 dung doc_fold(): bo site 19/24, loc weight > 0, va xet nhan
      energy_source tai THOI DIEM MUC TIEU T+h (cot nhan_energy_source).
      -> n = 791.047 dong (h1)
  (2) notebook 06_4 dung load_val_folds(): KHONG bo site 19/24, KHONG loc weight, va xet
      energy_source cua CHINH DONG do.
      -> n = 866.826 dong (h1)

  Notebook 06_4 chay SAU CUNG va GHI DE metrics_val.json cua ca 6 cau hinh (xem chu thich
  trong chinh no: "Ghi de truc tiep metrics_val.json THAT ... de notebook 07 doc dung").
  Nen file nam tren dia - thu ma notebook 07 doc de CHON mo hinh vo dich - la ban (2).

  Pipeline phai tai lap ban (2) thi metrics_val.json moi khop notebook. Cach tinh (1) van
  duoc giu de in ra log va lam cac bang chan doan cua s08c, vi no danh gia dung tren pham
  vi ma model duoc train.

  LUU Y CHUYEN MON: ban (2) cham diem tren ca dong cua site 19/24 va dong outlier bi
  zero-weight - tuc rong hon pham vi train. Ca hai cach deu chon HUBER thang o ca h1 lan
  h4 nen ket luan chon mo hinh khong doi.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.columns import SITE_COL, TARGET_COL, TIMESTAMP_COL
from core.config import Cfg
from core.context import Ctx
from core.io import read_parquet
from core.metrics import compute_metrics


COT_NHAN = ["energy_source", "is_daylight"]


def nap_val_kieu_06_4(ctx: Ctx) -> pd.DataFrame:
    """Nap tap validation theo dung load_val_holdout() cua notebook 06_4 ban v4.

    BON DIEM DOI SO VOI BAN v3 (day la nguon lech WAPE do ngay 17/08):
      1. Doc MOT tep v4_val_selected.parquet, khong gop cac fold nua.
      2. LOAI site trong data.exclude_sites (19, 24) - v3 giu lai.
      3. Dich cot nhan sang T+h thanh nhan_* de loc pham vi cho dung moc nhan.
      4. (o _du_bao) cat k tai clip_k cua chinh model, khong phai k_target_max.
    """
    cfg, paths = ctx.cfg, ctx.paths
    h = int(ctx.horizon_steps)
    eps = float(cfg.features["eps_elev"])
    cot_tat_dinh = list(cfg.features["cot_tat_dinh"])

    duong = paths.selected("val_selected")
    if not duong.exists():
        raise FileNotFoundError(f"Khong tim thay {duong}. Chay stage s07 truoc.")

    # can doc CA cot goc cua cac cot _mt de con dich duoc sang T+h
    goc = [c[:-3] if c.endswith("_mt") and c[:-3] in cot_tat_dinh else c
           for c in ctx.features]
    muon = list(dict.fromkeys(goc + [
        SITE_COL, TIMESTAMP_COL, TARGET_COL, "site_scale", "sin_elevation",
        "tran_cong_suat", *COT_NHAN,
    ]))
    d = read_parquet(duong, sap_xep=None)
    d = d[[c for c in muon if c in d.columns]]
    d = d.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)

    bo = list(cfg.data.get("exclude_sites") or [])
    if bo and SITE_COL in d.columns:
        n0 = len(d)
        d = d[~d[SITE_COL].isin(bo)].reset_index(drop=True)
        print(f"   Loai site {bo}: {n0:,} -> {len(d):,} dong")

    # SUA 2026-08-21: TRA THEO MOC THOI GIAN, khong con shift(-h) theo DONG.
    # shift(-h) dem theo VI TRI DONG nen chi dung khi luoi 15 phut con nguyen ven. Thieu
    # mot moc - dong bi loc hoac ETL khong sinh - la no vo phai dong ke tiep CON SONG chu
    # khong phai moc T+h that. Lay CA BA nhom (y_true, cac cot _mt, cac cot nhan_*) trong
    # CUNG mot phep tra de chung chac chan cung thuoc mot thoi diem.
    freq = int(cfg.data["freq_minutes"])
    d["plot_timestamp"] = d[TIMESTAMP_COL] + pd.Timedelta(minutes=freq * h)
    _mt = [c for c in cot_tat_dinh if c in d.columns and f"{c}_mt" in ctx.features]
    _nhan = [c for c in COT_NHAN if c in d.columns]
    _doi = {TIMESTAMP_COL: "plot_timestamp", TARGET_COL: "y_true"}
    _doi.update({c: f"{c}_mt" for c in _mt})
    _doi.update({c: f"nhan_{c}" for c in _nhan})
    _tra = d[[SITE_COL, TIMESTAMP_COL, TARGET_COL] + _mt + _nhan].rename(columns=_doi)
    d = d.merge(_tra, on=[SITE_COL, "plot_timestamp"], how="left")

    d = d.dropna(subset=["y_true"])
    # Mau so chuan hoa lay tai T+h, nen nguong ban ngay cung phai xet tai T+h.
    return d[(d["site_scale"] > 0) & (d["sin_elevation_mt"] > eps)].copy()


def _du_bao(ctx: Ctx, val: pd.DataFrame) -> np.ndarray:
    """Du bao roi nhan nguoc mau chuan hoa - dung cong thuc notebook 06_4.

    Cat k tai clip_k CUA CHINH MODEL (suy tu phan vi 99 cua k tren tap train, ghi
    trong model_config.json), khong phai k_target_max. Hai nguong khac nhau cho hai
    bo metric khac nhau tren cung mot model.
    """
    cfg: Cfg = ctx.cfg
    eps = float(cfg.features["eps_elev"])
    he_so = float(cfg.train["tran_cong_suat_he_so"])
    tran = float(cfg.train.get("clip_k") or cfg.train["k_target_max"])
    medians = pd.Series({k: float(v) for k, v in ctx.medians.items()})
    X = val[ctx.features].fillna(medians).astype(cfg.runtime["dtype"])
    k = np.clip(ctx.model.predict(X), cfg.train["k_target_min"], tran)
    mau = val["site_scale"].to_numpy() * val["sin_elevation_mt"].to_numpy()
    yp = np.minimum(k * mau, val["tran_cong_suat"].to_numpy() * he_so)
    return np.where(val["sin_elevation_mt"].to_numpy() <= eps, 0.0, yp)


def tinh_metrics_val_06_4(ctx: Ctx) -> dict:
    """Tra ve dict {measured_daylight, all} y het notebook 06_4 ghi vao metrics_val.json."""
    ctx.bat_buoc_co("model", "features", "medians")
    val = nap_val_kieu_06_4(ctx)
    y_that = val["y_true"].to_numpy()
    y_du_bao = _du_bao(ctx, val)

    # Pham vi hep: xet NHAN tai T+h (nhan_*), khong phai cot tai T
    mask = np.ones(len(val), dtype=bool)
    if "nhan_energy_source" in val.columns:
        mask &= (val["nhan_energy_source"] == "measured").to_numpy()
    if "nhan_is_daylight" in val.columns:
        mask &= val["nhan_is_daylight"].fillna(False).astype(bool).to_numpy()

    return {
        "measured_daylight": compute_metrics(y_that[mask], y_du_bao[mask]),
        "all": compute_metrics(y_that, y_du_bao),
    }
