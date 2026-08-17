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


def nap_val_kieu_06_4(ctx: Ctx) -> pd.DataFrame:
    """Gop cac fold validation theo dung load_val_folds() cua notebook 06_4."""
    cfg, paths = ctx.cfg, ctx.paths
    h = int(ctx.horizon_steps)
    eps = float(cfg.features["eps_elev"])
    cot_tat_dinh = list(cfg.features["cot_tat_dinh"])

    khung = []
    n = 1
    while (duong := paths.fold(n, "val")).exists():
        # can doc CA cot goc cua cac cot _mt de con dich duoc sang T+h
        goc = [c[:-3] if c.endswith("_mt") and c[:-3] in cot_tat_dinh else c
               for c in ctx.features]
        muon = list(dict.fromkeys(goc + [
            SITE_COL, TIMESTAMP_COL, TARGET_COL, "site_scale", "sin_elevation",
            "tran_cong_suat", "energy_source", "is_daylight",
        ]))
        d = read_parquet(duong, sap_xep=None)
        d = d[[c for c in muon if c in d.columns]]
        d = d.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)

        d["y_true"] = d.groupby(SITE_COL)[TARGET_COL].shift(-h)
        g = d.groupby(SITE_COL)
        for c in cot_tat_dinh:
            if c in d.columns and f"{c}_mt" in ctx.features:
                d[f"{c}_mt"] = g[c].shift(-h)
        d = d.dropna(subset=["y_true"])
        # KHONG bo site 19/24 va KHONG loc weight - dung y notebook 06_4
        d = d[(d["site_scale"] > 0) & (d["sin_elevation"] > eps)].copy()
        khung.append(d)
        n += 1

    if not khung:
        raise FileNotFoundError(
            f"Khong tim thay fold validation nao trong {paths.stage('s07_selected')}"
        )
    return pd.concat(khung, ignore_index=True)


def _du_bao(ctx: Ctx, val: pd.DataFrame) -> np.ndarray:
    """Du bao roi nhan nguoc mau chuan hoa - dung cong thuc cua notebook 06_4."""
    cfg: Cfg = ctx.cfg
    eps = float(cfg.features["eps_elev"])
    he_so = float(cfg.train["tran_cong_suat_he_so"])
    medians = pd.Series({k: float(v) for k, v in ctx.medians.items()})
    X = val[ctx.features].fillna(medians).astype(cfg.runtime["dtype"])
    k = np.clip(ctx.model.predict(X), cfg.train["k_target_min"], cfg.train["k_target_max"])
    mau = val["site_scale"].to_numpy() * val["sin_elevation"].to_numpy()
    yp = np.minimum(k * mau, val["tran_cong_suat"].to_numpy() * he_so)
    return np.where(val["sin_elevation"].to_numpy() <= eps, 0.0, yp)


def tinh_metrics_val_06_4(ctx: Ctx) -> dict:
    """Tra ve dict {measured_daylight, all} y het notebook 06_4 ghi vao metrics_val.json."""
    ctx.bat_buoc_co("model", "features", "medians")
    val = nap_val_kieu_06_4(ctx)
    y_that = val["y_true"].to_numpy()
    y_du_bao = _du_bao(ctx, val)

    # Pham vi hep: energy_source cua CHINH DONG (khong phai nhan tai T+h) va ban ngay
    mask = np.ones(len(val), dtype=bool)
    if "energy_source" in val.columns:
        mask &= (val["energy_source"] == "measured").to_numpy()
    if "is_daylight" in val.columns:
        mask &= val["is_daylight"].fillna(False).astype(bool).to_numpy()

    return {
        "measured_daylight": compute_metrics(y_that[mask], y_du_bao[mask]),
        "all": compute_metrics(y_that, y_du_bao),
    }
