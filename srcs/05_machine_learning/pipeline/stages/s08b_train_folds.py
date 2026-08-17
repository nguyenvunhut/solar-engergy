"""Stage 08b: nap 5 fold TimeSeriesSplit de danh gia CV / phuc vu Optuna.

Tach tu doc_fold() + khoi nap CAC_FOLD trong train_fold() cua 04_x_train_*.py.

LUU Y: pipeline chuan KHONG bat buoc chay stage nay. No chi can khi:
  - chay actions/tune_optuna.py (can fold de toi uu sieu tham so), hoac
  - muon bao cao pooled WAPE tren CV.
Train mo hinh cuoi (s08c) train tren TOAN BO development, khong dung fold.
"""
from __future__ import annotations

import gc

import numpy as np
import pandas as pd

from core.columns import SITE_COL, TARGET_SHIFTED
from core.config import Cfg
from core.context import Ctx
from core.io import cot_co_san, read_parquet
from core.target import k_target, mau_chuan_hoa, them_muc_tieu
from core.weights import build_sample_weight


def doc_fold(ctx: Ctx, n: int | None, vai_tro: str,
             duong_dan=None) -> pd.DataFrame | None:
    """Doc 1 fold, dung muc tieu va weight GIONG HET cach lam voi tap development.

    Tra ve None neu file khong ton tai (de vong lap biet dung).

    Tham so `duong_dan` cho phep dung chinh cach xu ly nay cho mot tep khong phai fold
    (vi du tap validation that o s08c) - de hai duong khong the lech nhau ve cach dung
    muc tieu, loc nguong va tinh trong so.
    """
    cfg = ctx.cfg
    if duong_dan is None:
        duong_dan = ctx.paths.fold(n, vai_tro)
    if not duong_dan.exists():
        return None

    co_san = cot_co_san(duong_dan)
    muon = list(dict.fromkeys(
        ctx.features + cfg.features["cot_phu"] + cfg.features["cot_bat_buoc"]
    ))
    d = read_parquet(duong_dan, columns=[c for c in muon if c in co_san])

    loai = cfg.data["exclude_sites"]
    if loai and SITE_COL in d.columns:
        d = d[~d[SITE_COL].isin(loai)]

    d = them_muc_tieu(d, ctx.horizon_steps, cfg)
    eps = float(cfg.features["eps_elev"])
    d = d[(d["site_scale"] > 0) & (d["sin_elevation"] > eps)].copy()
    d["k_target"] = k_target(d, cfg)
    d["w"] = build_sample_weight(d, cfg)
    return d[d["w"].gt(0)]


def nap_cac_fold(ctx: Ctx) -> Ctx:
    """Nap lan luot fold 1, 2, 3... den khi het file. Dien vao ctx.cac_fold."""
    ctx.bat_buoc_co("dev_h")
    cfg = ctx.cfg
    dtype = cfg.runtime["dtype"]
    eps = float(cfg.features["eps_elev"])
    cac_fold = []

    n = 1
    while True:
        tr = doc_fold(ctx, n, "train")
        va = doc_fold(ctx, n, "val")
        if tr is None or va is None:
            break
        # Median tinh RIENG tung fold tu tap train cua fold do - khong dung median
        # cua toan bo development, neu khong la ro ri thong tin giua cac fold.
        med = tr[ctx.features].median(numeric_only=True).fillna(0.0)
        cac_fold.append({
            "fold": n,
            "Xtr": tr[ctx.features].fillna(med).astype(dtype),
            "ytr": tr["k_target"].astype(dtype),
            "wtr": tr["w"].astype(dtype),
            "Xva": va[ctx.features].fillna(med).astype(dtype),
            # danh gia tren thang do GOC (kWh), khong phai thang do chuan hoa
            "yva_kwh": va[TARGET_SHIFTED].to_numpy(),
            "mau_va": mau_chuan_hoa(va, eps),
            "tran_va": va["tran_cong_suat"].to_numpy(),
            "sin_va": va["sin_elevation"].to_numpy(),
        })
        print(f"- fold {n}: train {len(tr):,} dong, val {len(va):,} dong (da ap weight)")
        del tr, va
        gc.collect()
        n += 1

    if not cac_fold:
        raise FileNotFoundError(
            f"Khong tim thay fold nao trong {ctx.paths.stage('s07_selected')}. "
            f"Hay chay lai stage s02 den s07 truoc."
        )

    ram = sum(
        f["Xtr"].memory_usage(deep=True).sum() + f["Xva"].memory_usage(deep=True).sum()
        for f in cac_fold
    ) / 1024**3
    print(f"Da nap {len(cac_fold)} fold, chiem khoang {ram:.2f} GB RAM")
    ctx.cac_fold = cac_fold
    return ctx


def du_bao_fold(model, fold: dict, cfg: Cfg) -> np.ndarray:
    """Du bao 1 fold roi nhan nguoc mau chuan hoa, tra ve thang do kWh.

    Khong dung du_bao_ve_kwh() cua core/target.py vi fold luu san mang numpy
    (mau_va/tran_va/sin_va) chu khong giu ca DataFrame - tiet kiem RAM khi giu 5 fold.
    """
    eps = float(cfg.features["eps_elev"])
    he_so = float(cfg.train["tran_cong_suat_he_so"])
    k = np.clip(model.predict(fold["Xva"]), cfg.train["k_target_min"], cfg.train["k_target_max"])
    yp = np.minimum(k * fold["mau_va"], fold["tran_va"] * he_so)
    return np.where(fold["sin_va"] <= eps, 0.0, yp)


def pooled_wape(model_theo_fold: list, ctx: Ctx) -> tuple[float, dict[int, float]]:
    """WAPE gop tren toan bo fold + WAPE rieng tung fold.

    Gop bang cach cong tu so va mau so (khong lay trung binh cac WAPE) - dung dinh
    nghia WAPE. Tra ve them WAPE tung fold vi fold dau it du lieu nen thuong te hon
    han cac fold sau, giai thich vi sao pooled WAPE > WAPE test cuoi cung.
    """
    tong_sai, tong_that, theo_fold = 0.0, 0.0, {}
    for model, fold in zip(model_theo_fold, ctx.cac_fold):
        yp = du_bao_fold(model, fold, ctx.cfg)
        sai = float(np.abs(yp - fold["yva_kwh"]).sum())
        that = float(np.abs(fold["yva_kwh"]).sum())
        theo_fold[fold["fold"]] = sai / that * 100.0 if that > 0 else np.nan
        tong_sai += sai
        tong_that += that
    gop = tong_sai / tong_that * 100.0 if tong_that > 0 else np.nan
    return gop, theo_fold
