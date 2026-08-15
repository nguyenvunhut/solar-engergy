"""Stage 08c: train mo hinh cuoi tren TOAN BO development + danh gia tren VALIDATION.

Tach tu train_develop() + train_valid() cua 04_x_train_*.py.

TAP TEST KHONG XUAT HIEN O FILE NAY. Ban cu cham diem tap test ngay trong buoc train;
ban moi doi toan bo phan do sang stage s09, sau khi mo hinh vo dich da duoc chon xong.
Moi con so sinh ra o day deu tren tap VALIDATION.

TIEU CHI NGHIEM THU (quan trong hon ca WAPE): du bao phai DUNG THOI DIEM.
Gia tri cao hay thap hon thuc te con chap nhan duoc, nhung neu du bao den SAU thi
no khong con la du bao nua.
"""
from __future__ import annotations

import time

import pandas as pd

from core.columns import PRED_COL, TARGET_SHIFTED
from core.context import Ctx
from core.lgbm import chuan_bi_X, fit_an_toan, kiem_tra_gpu, them_tham_so_gpu
from core.metrics import compute_metrics, metrics_3_pham_vi
from core.phase_lag import do_tre_theo_site, quet_do_tre
from core.target import du_bao_ve_kwh
from core.weights import scope_masks


def train(ctx: Ctx) -> Ctx:
    """Train tren toan bo development. KHONG cham tap test o day."""
    ctx.bat_buoc_co("X_dev", "y_dev", "w_dev")
    cfg = ctx.cfg

    ctx.gpu_san_sang, loi = kiem_tra_gpu(cfg)
    print(f"Che do tinh toan: {'GPU' if ctx.gpu_san_sang else 'CPU'}"
          + (f" ({loi})" if loi else ""))

    tho, nguon = cfg.sieu_tham_so(ctx.loss_name, ctx.horizon_steps)
    params = them_tham_so_gpu(tho, cfg, ctx.gpu_san_sang)
    ctx.best_params = params
    print(f"Loss = {ctx.loss_name} | objective = {params['objective']} "
          f"| n_estimators = {params['n_estimators']}")
    # In ra NGUON tham so: neu roi ve default_params trong khi dang muon tai lap notebook
    # thi model se khac han - phai thay ngay o log chu khong de doan.
    print(f"Nguon sieu tham so: {nguon}")

    t0 = time.time()
    ctx.model, ctx.da_lui_ve_cpu = fit_an_toan(
        params, ctx.X_dev, ctx.y_dev, sample_weight=ctx.w_dev, cfg=cfg
    )
    print(f"Train xong sau {(time.time() - t0) / 60:.1f} phut"
          + (" (da lui ve CPU)" if ctx.da_lui_ve_cpu else ""))
    return ctx


def dac_trung_quan_trong(ctx: Ctx, top: int = 12) -> pd.Series:
    ctx.bat_buoc_co("model")
    return (
        pd.Series(ctx.model.feature_importances_, index=ctx.features)
        .sort_values(ascending=False)
        .head(top)
    )


def kiem_tre_pha(ctx: Ctx, khung: pd.DataFrame) -> Ctx:
    """Quet do tre tren tap VALIDATION + tach rieng tung tram.

    Bat buoc co ca hai: con so tong the co the la +0,0 phut trong khi 1 tram le
    tre 45 phut - do van la bug, khong duoc de con so gop che mat.
    """
    freq = int(ctx.cfg.data["freq_minutes"])

    ctx.quet_tre = quet_do_tre(khung, TARGET_SHIFTED, PRED_COL, k_max=3)
    k_tot = min(ctx.quet_tre, key=ctx.quet_tre.get)
    print("--- QUET DO TRE TOAN BO ---")
    print("So du bao(T) voi thuc te(T - k buoc). k=0 nho nhat la KHONG tre.")
    for k, v in ctx.quet_tre.items():
        print(f"   k={k} ({k * freq:>2} phut truoc): MAE {v:.4f}"
              + ("  <== nho nhat" if k == k_tot else ""))
    print(f"Ket luan: {'KHONG TRE PHA' if k_tot == 0 else f'TRE {k_tot} BUOC = {k_tot * freq} PHUT'}")

    ctx.df_tre_theo_site = do_tre_theo_site(khung, TARGET_SHIFTED, PRED_COL, freq)
    vuot = ctx.df_tre_theo_site["tre_phut"].abs() > freq / 2
    print(f"So tram tre qua nua buoc ({freq / 2:.1f} phut): {int(vuot.sum())}/{len(ctx.df_tre_theo_site)}")
    return ctx


def bang_8_pham_vi(ctx: Ctx, khung: pd.DataFrame) -> pd.DataFrame:
    """Metric tach theo 8 pham vi giong scope_masks cua srcs/Forcasting_v3.

    Diem can doc: physical_over_capacity_rows phai co sai so RAT LON. Do la dau hieu
    TOT - nghia la model KHONG hoc theo may dong vuot tran vat ly do.
    """
    dong = []
    for ten, mask in scope_masks(khung).items():
        n = int(mask.sum())
        if n < 10:
            dong.append({"pham_vi": ten, "so_dong": n})
            continue
        z = khung.loc[mask]
        m = compute_metrics(z[TARGET_SHIFTED].values, z[PRED_COL].values)
        dong.append({
            "pham_vi": ten, "so_dong": n,
            "wape_%": round(m["wape"], 4), "rmse": round(m["rmse"], 4),
            "mae": round(m["mae"], 4), "r2": round(m["r2"], 4),
        })
    return pd.DataFrame(dong)


def doc_val_that(ctx: Ctx) -> pd.DataFrame:
    """Doc tap VALIDATION THAT (v4_val_selected), xu ly y het doc_fold().

    TACH BIET HOAN TOAN voi tap hoc: mo hinh cuoi chi hoc v4_train_selected, nen moi
    dong o day deu la dong CHUA TUNG duoc hoc.

    Truoc day ham goi no gop 3 fold validation lai - nhung fold nam trong development
    (= train + val) ma mo hinh cuoi lai hoc ca development, nen con so thu duoc la cham
    tren bai DA HOC. Do da tren bo v4: pooled 3 fold cho 886.148 dong va WAPE h4
    26,09%, con tap validation that cho 288.815 dong va 26,97% - tuc ban cu lac quan
    hon gan mot diem. Notebook 06 da sua tu 2026-08-09, ban .py nay sua theo.
    """
    from stages.s08b_train_folds import doc_fold  # dung chung cach xu ly

    duong_dan = ctx.paths.selected("val_selected")
    if not duong_dan.exists():
        raise FileNotFoundError(
            f"Khong tim thay tap validation that: {duong_dan}. "
            "Chay stage s07 truoc de sinh tep nay."
        )
    return doc_fold(ctx, None, "val", duong_dan=duong_dan)


def tinh_metrics_val(ctx: Ctx) -> Ctx:
    """Tinh metric tren tap VALIDATION that - dung de CHON mo hinh vo dich.

    CHONG RO RI - day la diem sua loi quan trong nhat cua ban cu: metrics_val.json
    truoc day bi ghi tu so lieu TEST, khien viec chon MAE/Huber/MSE "nhin truoc" tap
    test niem phong. Chon mo hinh BAT BUOC phai dua tren validation, tap test chi
    duoc cham DUY NHAT 1 LAN o cuoi de bao cao.
    """
    ctx.bat_buoc_co("model")
    val_h = doc_val_that(ctx)
    X_val = chuan_bi_X(val_h, ctx.features, ctx.medians, dtype=ctx.cfg.runtime["dtype"])
    val_h[PRED_COL] = du_bao_ve_kwh(ctx.model.predict(X_val), val_h, ctx.cfg)
    ctx.metrics_val = metrics_3_pham_vi(val_h)

    print(f"--- METRIC TREN VALIDATION THAT ({len(val_h):,} dong, dung de CHON mo hinh) ---")
    print(pd.DataFrame(ctx.metrics_val).T[["n", "wape", "rmse", "mae", "r2"]].round(4).to_string())
    return val_h
