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

from core.columns import PRED_COL, SITE_COL, TARGET_SHIFTED, TIMESTAMP_COL
from core.context import Ctx
from core.io import cot_co_san, read_parquet
from core.lgbm import chuan_bi_X, fit_an_toan, kiem_tra_gpu, them_tham_so_gpu
from core.metrics import compute_metrics, metrics_3_pham_vi
from core.phase_lag import do_tre_theo_site, quet_do_tre
from core.target import nguong_cat, du_bao_ve_kwh, k_target, them_muc_tieu
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

    # NGUON: notebook 06_x cell 50. Dung som chay hai pha - pha 1 fit kem early_stopping
    # chi de lay best_iteration_, pha 2 fit lai khong dung som voi dung so cay do.
    # Bat/tat bang early_stopping_rounds trong train.yaml.
    vong = int(cfg.train.get("early_stopping_rounds") or 0)
    if ctx.loss_name not in LOSS_DUNG_SOM:
        vong = 0        # xem ghi chu o LOSS_DUNG_SOM
    if vong:
        # HAI tap validation KHAC NHAU, khong duoc dung lan:
        #   - Cham metric  -> doc_val_that() theo notebook 06_4 load_val_holdout:
        #     chi loai 2 site khong dang tin + loc ban ngay, GIU moi dong con lai
        #     (319.957 dong o H1). Day la ban dang cho metrics_val.json khop notebook.
        #   - Early stopping -> notebook 06_1/06_2/06_3 doc_val_that() con loc them
        #     w > 0 (288.216 dong). Dung nham ban 319.957 thi best_iteration lech:
        #     do duoc H4 huber 813 thay vi 822, H4 mse 462 thay vi 582.
        val_es = _val_cho_dung_som(ctx)
        X_val = chuan_bi_X(val_es, ctx.features, ctx.medians, dtype=cfg.runtime["dtype"])
        # Nhan cham early stopping o thang k, KHONG phai kWh: model du bao ty le k.
        # Notebook 06_x cell 26/48: _y_val_es = val_h['k_target'].astype(DTYPE).
        # Ban truoc dung val_h[TARGET_SHIFTED] (= y_true, thang kWh) nen loss lech thang
        # do -> dung som kich hoat bay -> phai tat han bang early_stopping_rounds: 0.
        y_val = k_target(val_es, cfg).astype(cfg.runtime["dtype"])
        m_do, _ = fit_an_toan(
            params, ctx.X_dev, ctx.y_dev, sample_weight=ctx.w_dev, cfg=cfg,
            eval_set=[(ctx.X_dev, ctx.y_dev), (X_val, y_val)], dung_som=vong,
        )
        so_cay_tot = int(m_do.best_iteration_ or params["n_estimators"])
        print(f"Dung som {vong} vong tren {len(val_es):,} dong validation "
              f"-> best_iteration = {so_cay_tot} (yeu cau {params['n_estimators']})")
        params = {**params, "n_estimators": so_cay_tot}
        ctx.best_params = params
        # GIU luon model vua fit, KHONG fit lai. Notebook 06_x cell 26/48 chi fit MOT lan
        # roi dung thang ket qua do (`model = fit_an_toan(..., _X_val_es, _y_val_es, ...)`).
        # Fit lai cho ra dung cung bo cay va cung du bao (da do: 0/500 diem khac bit),
        # nhung object thieu metadata early stopping nen model.pkl khac nen file. Giu lai
        # thi .pkl trung bit voi notebook.
        ctx.model, ctx.da_lui_ve_cpu = m_do, False
        t0 = time.time()
    else:
        t0 = time.time()
        ctx.model, ctx.da_lui_ve_cpu = fit_an_toan(
            params, ctx.X_dev, ctx.y_dev, sample_weight=ctx.w_dev, cfg=cfg
        )
    so_cay = ctx.model.booster_.num_trees()
    print(f"Train xong sau {(time.time() - t0) / 60:.1f} phut"
          + (" (da lui ve CPU)" if ctx.da_lui_ve_cpu else "")
          + f" | {so_cay} cay thuc / {params['n_estimators']} yeu cau")
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


# Loss nao fit mo hinh CUOI kem early stopping. Do trong artifact notebook:
#   06_1 (mae)  : model = fit_an_toan(BEST_PARAMS, X_dev, y_dev, w_dev)          <- KHONG
#   06_2 (huber): model = fit_an_toan(..., _X_val_es, _y_val_es, LICH_SU_...)    <- CO
#   06_3 (mse)  : model = fit_an_toan(..., _X_val_es, _y_val_es, LICH_SU_...)    <- CO
# Kiem lai bang chinh model.pkl cua notebook:
#   mae/h1   _evals_result RONG, best_iteration_ = 0
#   huber/h1 _evals_result CO,   best_iteration_ = 891
#   mse/h1   _evals_result CO,   best_iteration_ = 337
# Ba notebook viet khac nhau - day khong phai lua chon cua pipeline, chi la ghi lai cho
# dung de tai lap. Ap early stopping cho mae thi model.pkl khong con trung bit voi
# notebook (du so cay va moi metric van y het, vi best_iteration = n_estimators).
LOSS_DUNG_SOM = ("huber", "mse")


def _val_cho_dung_som(ctx: Ctx) -> pd.DataFrame:
    """Tap validation dung RIENG cho early stopping - ban co loc w > 0.

    Notebook 06_1/06_2/06_3, ham doc_val_that() (cell 16):
        d['w'] = build_sample_weight(d)
        return d[d['w'].gt(0)]
    Ban nay CHI de chon so cay. Cham metric van dung doc_val_that() (khong loc w),
    vi do la ban ma notebook 06_4 load_val_holdout dung va metrics_val.json dang khop.
    """
    from core.weights import build_sample_weight

    d = doc_val_that(ctx).copy()
    d["w"] = build_sample_weight(d, ctx.cfg)
    return d[d["w"].gt(0)]


def doc_val_that(ctx: Ctx) -> pd.DataFrame:
    """Doc tap VALIDATION THAT (v4_val_selected), xu ly y het doc_fold().

    TACH BIET HOAN TOAN voi tap hoc: mo hinh cuoi chi hoc v4_train_selected, nen moi
    dong o day deu la dong CHUA TUNG duoc hoc.

    Truoc day ham goi no gop 3 fold validation lai - nhung fold nam trong development
    (= train + val) ma mo hinh cuoi lai hoc ca development, nen con so thu duoc la cham
    tren bai DA HOC. Do da tren bo v4: pooled 3 fold cho 886.148 dong va WAPE h4
    26,09%, con tap validation that cho 288.815 dong va 26,97% - tuc ban cu lac quan
    hon gan mot diem. Notebook 06 da sua tu 2026-08-09, ban .py nay sua theo.

    KHONG duoc dung doc_fold() o day. doc_fold() la duong doc cua tap HOC nen no loc
    them exclude_from_training / has_complete_history_features / w > 0 - dung cho fold,
    sai cho holdout. Notebook 06_4 (load_val_holdout) chi loai 2 site khong dang tin roi
    loc ban ngay, giu nguyen moi dong con lai de pham vi 'all' phan anh CA tap validation.
    Loc thua lam 'all' tut tu 318.981 xuong 288.811 dong, tuc thanh ban sao cua
    'measured_daylight' va mat y nghia doi chieu "toan bo du lieu vs du lieu do that".
    """
    duong_dan = ctx.paths.selected("val_selected")
    if not duong_dan.exists():
        raise FileNotFoundError(
            f"Khong tim thay tap validation that: {duong_dan}. "
            "Chay stage s07 truoc de sinh tep nay."
        )
    from stages.s08a_prepare import _loc_ban_ngay

    cfg = ctx.cfg
    muon = list(dict.fromkeys(
        ctx.features + cfg.features["cot_phu"] + cfg.features["cot_bat_buoc"]
    ))
    d = read_parquet(duong_dan, columns=[c for c in muon if c in cot_co_san(duong_dan)])
    d = d.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)

    loai = cfg.data["exclude_sites"]
    if loai and SITE_COL in d.columns:
        n0 = len(d)
        d = d[~d[SITE_COL].isin(loai)].reset_index(drop=True)
        print(f"   Loai site {loai}: {n0:,} -> {len(d):,} dong")

    d = them_muc_tieu(d, ctx.horizon_steps, cfg)
    return _loc_ban_ngay(d, float(cfg.features["eps_elev"]))


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
    # NGUON: notebook 06_4. Cat k tai clip_k cua chinh model (phan vi 99 cua k tren tap
    # train); de trong thi du_bao_ve_kwh() lui ve k_target_max, ra bo metric khac.
    val_h[PRED_COL] = du_bao_ve_kwh(
        ctx.model.predict(X_val), val_h, ctx.cfg, clip_k=nguong_cat(ctx.cfg)
    )
    ctx.metrics_val = metrics_3_pham_vi(val_h)

    print(f"--- METRIC TREN VALIDATION THAT ({len(val_h):,} dong, dung de CHON mo hinh) ---")
    print(pd.DataFrame(ctx.metrics_val).T[["n", "wape", "rmse", "mae", "r2"]].round(4).to_string())
    return val_h
