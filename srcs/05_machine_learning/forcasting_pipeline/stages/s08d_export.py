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
from core.target import nguong_cat

# Cai dat chay may, khong phai sieu tham so mo hinh - de ngoai model_params cho khop
# notebook (notebook cung loc dung 3 khoa device/gpu_platform_id/gpu_device_id).
_KHOA_GPU = ("device", "gpu_platform_id", "gpu_device_id", "gpu_use_dp")

# Cot mang QUY MO cua tram, dong thoi la ten MAU SO chuan hoa dang dung. Hai khoa
# 'cot_quy_mo' va 'mau_so' trong model_config.json deu tro ve day nen khong the lech nhau.
COT_QUY_MO = "site_scale"


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
    # Do da: notebook 06_1 (mae) ghi khoa nay o CA h1 va h4; 06_2 (huber) va 06_3 (mse)
    # chi ghi o h1, o export h4 thi sot. Gia tri la [] o moi truong hop nen khong mat
    # thong tin - bam theo notebook de model_config.json khop tung byte.
    if ctx.horizon_steps == 1 or ctx.loss_name == "mae":
        cau_hinh["excluded_features"] = ctx.bo_di
    cau_hinh.update({
        "lgb_objective": ctx.best_params.get("objective"),
        "features": ctx.features,
        "feature_medians": {k: float(v) for k, v in ctx.medians.items()},
        "train_rows": int(len(ctx.X_dev)),
        # Bon khoa duoi cho biet PHAI nhan nguoc mau chuan hoa khi du bao. Bo qua la
        # y_pred ra thang do 0..1,5 trong khi y_true la kWh - bug "du bao duoi dat".
        "chuan_hoa": bool(ctx.cfg.train["chuan_hoa"]),
        "cot_quy_mo": COT_QUY_MO,
        "cot_sin_elev": "sin_elevation_mt",
        "cot_tran": "tran_cong_suat",
        "eps_elev": float(ctx.cfg.features["eps_elev"]),
        # Nguong cat muc tieu, suy tu phan vi cua k tren tap train. Notebook 06 ghi khoa
        # nay va stage s09 doc lai de cham diem bang DUNG nguong da train; thieu no thi
        # khong ai kiem duoc hai ben co cat cung mot muc hay khong.
        "clip_k": float(nguong_cat(ctx.cfg)),
        # Cong tac chon MAU SO chuan hoa muc tieu. Notebook 06 co hai lua chon:
        # 'site_scale' (quy mo tram nhan sin goc cao) va 'lonij' (phan vi 80 cua 15 ngay
        # lien truoc, Lonij et al. 2012). Pipeline .py chi cai dat duong site_scale -
        # core.target.mau_chuan_hoa() khong co nhanh lonij - nen gia tri ghi ra luon la
        # ten cot quy mo dang dung. Thieu khoa nay thi stage s09 va notebook 07 khong
        # biet ban ghi duoc chuan hoa bang mau so nao de nhan nguoc cho dung.
        "mau_so": COT_QUY_MO,
        # Notebook 06_x cell 44/52: dung model.get_params() chu KHONG dung bo tham so
        # YEU CAU. get_params() la thu LightGBM THUC SU dung - gom ca khoa mac dinh ma
        # Optuna khong dong toi (boosting_type, max_depth, subsample_for_bin...), va
        # n_estimators la gia tri TRUYEN VAO constructor (929) chu khong phai so cay
        # sau dung som (891). Ban truoc ghi ctx.best_params nen thieu 8 khoa mac dinh
        # va ghi nham n_estimators -> model_config.json khong khop notebook.
        "model_params": {k: v for k, v in ctx.model.get_params().items()
                         if k not in _KHOA_GPU},
    })
    # KHONG them khoa nao khac vao day (truoc co 'train_tren_gpu' - da bo): notebook
    # khong ghi nen them vao la model_config.json khong con khop tung byte. Thiet bi
    # train da duoc ghi trong log chay va cau hinh o runtime.yaml: gpu.use_gpu.
    write_json(cau_hinh, d / ctx.paths.file("model_config"))


def ghi_metrics(ctx: Ctx) -> None:
    """Chi ghi metrics_val.json. Khong co metrics_test o day - test chua he duoc mo.

    s09 doc dung file nay de chon mo hinh vo dich, roi moi mo tap test 1 lan duy nhat.

    CON SO GHI RA lay tu ctx.metrics_val, tuc cham tren TAP VALIDATION THAT
    (v4_val_selected) do s08c.doc_val_that() nap.

    Truoc day cho nay goi stages/s08e_metrics_val.tinh_metrics_val_06_4(), tai lap
    load_val_folds() cua notebook 06_4: gop 3 fold validation, khong bo site 19/24,
    khong loc weight. Ban notebook do DA BI THAY: 06_4 bay gio dung load_val_holdout().
    Ba fold validation nam trong development ma mo hinh cuoi lai hoc ca development, nen
    cach cu cham tren bai DA HOC va cho con so lac quan hon - do tren bo v4: 779.099 dong
    voi WAPE h4 26,09% so voi 272.569 dong va 26,97% cua tap validation that.
    """
    ctx.bat_buoc_co("model")
    d = ctx.thu_muc_ra
    d.mkdir(parents=True, exist_ok=True)

    if not ctx.metrics_val:
        raise RuntimeError(
            "Chua co ctx.metrics_val - phai goi s08c.tinh_metrics_val() truoc khi export. "
            "Khong duoc ghi metrics_val.json tu so lieu test (day la loi ro ri cua ban cu)."
        )

    m = ctx.metrics_val
    write_json({
        "horizon_steps": int(ctx.horizon_steps),
        "loss_name": ctx.loss_name,
        "feature_set_name": "",
        PHAM_VI_CHINH_THUC: m[PHAM_VI_CHINH_THUC],
        "all": m["all"],
    }, d / ctx.paths.file("metrics_val"))
    print(f"metrics_val.json (tap validation that): WAPE = "
          f"{m[PHAM_VI_CHINH_THUC]['wape']:.4f}% tren {m[PHAM_VI_CHINH_THUC]['n']:,} dong")


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
