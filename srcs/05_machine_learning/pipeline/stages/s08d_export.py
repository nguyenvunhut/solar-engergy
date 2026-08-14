"""Stage 08d: ghi artifact ra dia theo dung dinh dang ma stage s09/s10 mong doi.

Tach tu export() cua 04_x_train_*.py.

BA LOI CUA BAN CU DA SUA O DAY:
  1. 04_2/04_3 hardcode 'model_h1.pkl' va 'prediction_audit_h1.parquet' -> chay h4 van
     ghi ten _h1. Gio dung ctx.h_label nen h4 ra dung _h4.
  2. metrics_val.json truoc day bi ghi tu so lieu TEST -> chon mo hinh "nhin truoc" tap
     test niem phong. Gio ghi tu ctx.metrics_val (tinh tren fold validation that).
  3. Ban cu ghi ca metrics_test.json va X_test_h{n}.parquet ngay o buoc train, tuc la
     da mo tap test truoc khi chon mo hinh. Gio KHONG file nao lien quan test duoc ghi
     o day - toan bo chuyen sang stage s09.
"""
from __future__ import annotations

import pickle

import pandas as pd

from core.columns import (
    DAYLIGHT_COL,
    PRED_COL,
    SITE_COL,
    SOURCE_COL,
    TARGET_COL,
    TARGET_SHIFTED,
    TIMESTAMP_COL,
)
from core.context import Ctx
from core.io import write_csv, write_json, write_parquet
from core.metrics import PHAM_VI_CHINH_THUC

# Cai dat chay may, khong phai sieu tham so mo hinh - de ngoai model_params cho khop
# notebook (notebook cung loc dung 3 khoa device/gpu_platform_id/gpu_device_id).
_KHOA_GPU = ("device", "gpu_platform_id", "gpu_device_id", "gpu_use_dp")


def _pham_vi_chinh(m: dict) -> dict:
    """Lay pham vi measured_daylight; khong co thi lui dan sang measured roi all."""
    return m.get(PHAM_VI_CHINH_THUC, m.get("measured", m.get("all", {})))


def ghi_model(ctx: Ctx) -> None:
    """model.pkl (model tho, de s09 goi model.predict truc tiep) + model_config.json."""
    ctx.bat_buoc_co("model", "medians")
    d = ctx.thu_muc_ra
    d.mkdir(parents=True, exist_ok=True)

    with open(d / ctx.paths.file("model"), "wb") as f:
        pickle.dump(ctx.model, f)

    cau_hinh = {
        "horizon_steps": int(ctx.horizon_steps),
        "loss_name": ctx.loss_name,
        "feature_set_name": "",
    }
    # KHOA NAY CHI CO O H1. Notebook 06_x co HAI o export rieng cho h1 va h4, va o h4
    # sot mat 'excluded_features'. Gia tri la [] o ca hai horizon (khong dac trung ngan
    # nao bi loai) nen khong mat thong tin gi. Bam theo notebook de model_config.json
    # khop TUNG BYTE - day la ban ghi ma bao cao trich dan, lech mot khoa la phai giai
    # trinh truoc hoi dong.
    if ctx.horizon_steps == 1:
        cau_hinh["excluded_features"] = ctx.bo_di
    cau_hinh.update({
        "lgb_objective": ctx.best_params.get("objective"),
        "features": ctx.features,
        "feature_medians": {k: float(v) for k, v in ctx.medians.items()},
        "train_rows": int(len(ctx.X_dev)),
        # Bon khoa duoi cho biet PHAI nhan nguoc mau chuan hoa khi du bao. Bo qua la
        # y_pred ra thang do 0..1,5 trong khi y_true la kWh - bug "du bao duoi dat".
        "chuan_hoa": bool(ctx.cfg.train["chuan_hoa"]),
        "cot_quy_mo": "site_scale",
        "cot_sin_elev": "sin_elevation",
        "cot_tran": "tran_cong_suat",
        "eps_elev": float(ctx.cfg.features["eps_elev"]),
        "model_params": {k: v for k, v in ctx.best_params.items() if k not in _KHOA_GPU},
    })
    # KHONG them khoa nao khac vao day (truoc co 'train_tren_gpu' - da bo): notebook
    # khong ghi nen them vao la model_config.json khong con khop tung byte. Thiet bi
    # train da duoc ghi trong log chay va cau hinh o runtime.yaml: gpu.use_gpu.
    write_json(cau_hinh, d / ctx.paths.file("model_config"))


def ghi_metrics(ctx: Ctx) -> None:
    """Chi ghi metrics_val.json. Khong co metrics_test o day - test chua he duoc mo.

    s09 doc dung file nay de chon mo hinh vo dich, roi moi mo tap test 1 lan duy nhat.

    CON SO GHI RA LAY THEO CACH CUA NOTEBOOK 06_4, khong phai cach cua s08c. Ly do day du
    o stages/s08e_metrics_val.py: trong bo notebook co hai dinh nghia tap validation, va
    06_4 chay sau cung nen chinh no ghi de len file nay - do la ban ma notebook 07 doc de
    chon mo hinh. Muon metrics_val.json khop notebook thi phai tai lap dung ban do.
    Con so cua s08c (tinh dung tren pham vi da train) van duoc in ra log va dua vao
    ket_qua_{h}.json de doi chieu.
    """
    ctx.bat_buoc_co("model")
    d = ctx.thu_muc_ra
    d.mkdir(parents=True, exist_ok=True)

    if not ctx.metrics_val:
        raise RuntimeError(
            "Chua co ctx.metrics_val - phai goi s08c.tinh_metrics_val() truoc khi export. "
            "Khong duoc ghi metrics_val.json tu so lieu test (day la loi ro ri cua ban cu)."
        )

    from stages.s08e_metrics_val import tinh_metrics_val_06_4

    m = tinh_metrics_val_06_4(ctx)
    write_json({
        "horizon_steps": int(ctx.horizon_steps),
        "loss_name": ctx.loss_name,
        "feature_set_name": "",
        PHAM_VI_CHINH_THUC: m["measured_daylight"],
        "all": m["all"],
    }, d / ctx.paths.file("metrics_val"))
    print(f"metrics_val.json (cach notebook 06_4): WAPE = "
          f"{m['measured_daylight']['wape']:.4f}% tren {m['measured_daylight']['n']:,} dong")


def ghi_bao_cao(ctx: Ctx, val_h) -> None:
    """Bang tre pha theo tram, metrics.csv, ket_qua.json - deu tren tap VALIDATION."""
    d = ctx.thu_muc_ra
    h = ctx.h_label

    cot_audit = [c for c in [SITE_COL, TIMESTAMP_COL, "plot_timestamp", TARGET_SHIFTED,
                             PRED_COL, DAYLIGHT_COL, SOURCE_COL] if c in val_h.columns]
    write_parquet(val_h[cot_audit], d / f"prediction_audit_val_{h}.parquet")

    if ctx.df_tre_theo_site is not None:
        write_csv(ctx.df_tre_theo_site, d / f"tre_pha_theo_tram_val_{h}.csv")
    if ctx.metrics_val:
        bang = pd.DataFrame(ctx.metrics_val).T[["n", "wape", "rmse", "mae", "r2"]].round(4)
        write_csv(bang.reset_index(names="pham_vi"), d / f"metrics_val_{h}.csv")

    k_tot = min(ctx.quet_tre, key=ctx.quet_tre.get) if ctx.quet_tre else None
    write_json({
        "loss": ctx.loss_name,
        "horizon_steps": int(ctx.horizon_steps),
        "so_dac_trung": len(ctx.features),
        "features": ctx.features,
        "bo_di": ctx.bo_di,
        "best_params": {k: v for k, v in ctx.best_params.items() if k not in _KHOA_GPU},
        "quet_do_tre_val": {str(k): v for k, v in ctx.quet_tre.items()},
        "k_tot_nhat_val": int(k_tot) if k_tot is not None else None,
        "metrics_val": ctx.metrics_val,
        "ghi_chu": "Moi con so o day tinh tren tap VALIDATION. Tap test chi duoc mo o s09.",
    }, d / f"ket_qua_{h}.json")


def export_tat_ca(ctx: Ctx, val_h) -> Ctx:
    """Goi ca 3 buoc ghi. Dung o cuoi 1 lan train (1 loss x 1 horizon)."""
    ghi_model(ctx)
    ghi_metrics(ctx)
    ghi_bao_cao(ctx, val_h)
    d = ctx.thu_muc_ra
    print(f"Da ghi artifact vao: {d}")
    for f in sorted(p.name for p in d.iterdir()):
        print(f"   {f}")
    return ctx
