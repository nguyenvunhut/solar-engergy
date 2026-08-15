"""Stage 04: dac trung khong gian - hinh hoc mat troi, downscale buc xa, quy mo tram.

    python srcs/05_machine_learning/pipeline/run.py --stage s04

Dau vao : data/model/v3/03_1_features_time<suffix>/
Dau ra  : data/model/v3/03_2_features_spatial<suffix>/

THU TU BAT BUOC trong tung tap:
  1. metadata tram            (s04a) - capacity_per_panel, co thieu du lieu
  2. hinh hoc mat troi        (s04a) - sinh ghi_cs, PHAI truoc buoc 3 va 4
  3. ap cs_factor             (s04b) - hieu chinh ghi_cs theo tung tram
  4. downscale buc xa         (s04b) - dung ghi_cs da hieu chinh
  5. quy mo tram              (s04c) - site_scale, tran_cong_suat, ty_le_bao_hoa

QUY MO TRAM TINH TRUOC MOI THU: thong ke lay tu tap TRAIN, luu ra JSON, roi ap chung
cho moi tap. Neu tinh rieng tren tung tap thi val/test se mang thong tin cua chinh no.
"""
from __future__ import annotations

import gc

from core.columns import VERSION
from core.config import Cfg, load_config
from core.io import read_parquet, write_parquet
from core.paths import Paths

from stages import s04a_solar_geometry, s04b_downscale_radiation, s04c_site_scale


def _xu_ly_1_tap(duong_vao, duong_ra, thong_ke: dict, cfg: Cfg) -> tuple[int, int, dict]:
    df = read_parquet(duong_vao)
    truoc = df["shortwave_radiation"].copy() if "shortwave_radiation" in df.columns else None

    df = s04a_solar_geometry.add_metadata_features(df)
    df = s04a_solar_geometry.add_solar_geometry_features(df, cfg)
    df = s04b_downscale_radiation.ap_he_so_troi_quang(df, thong_ke)
    df = s04b_downscale_radiation.add_downscaled_radiation(df, cfg)
    df = s04c_site_scale.add_site_scale_features(df, thong_ke)

    bao_cao = (s04b_downscale_radiation.bao_cao_downscale(truoc, df["shortwave_radiation"])
               if truoc is not None else {})
    write_parquet(df, duong_ra)
    hinh = (len(df), df.shape[1])
    del df, truoc
    gc.collect()
    return (*hinh, bao_cao)


def run_s04(cfg: Cfg | None = None):
    cfg = cfg or load_config()
    paths = Paths(cfg)
    vao = paths.stage_doc("s03_features")
    ra = paths.stage("s04_spatial")
    if not vao.exists():
        raise FileNotFoundError(
            f"Khong tim thay {vao}. Chay stage s03 truoc:\n"
            f"    python srcs/05_machine_learning/pipeline/run.py --stage s03"
        )
    ra.mkdir(parents=True, exist_ok=True)

    print("[1/3] Tinh quy mo tram CHI TU TAP TRAIN (chong ro ri)")
    thong_ke = s04c_site_scale.tinh_quy_mo_tu_train(
        vao / f"{VERSION}_train_time.parquet", cfg, ra
    )
    print(f"      da tinh cho {len(thong_ke['site_scale'])} tram | "
          f"luu: {ra / s04c_site_scale.TEN_FILE_QUY_MO}\n")

    print("[2/3] 4 tap chinh")
    for ten in ("development", "test", "train", "val"):
        n, c, bc = _xu_ly_1_tap(
            vao / f"{VERSION}_{ten}_time.parquet",
            ra / f"{VERSION}_{ten}_spatial.parquet",
            thong_ke, cfg,
        )
        them = (f" | buoc co buc xa BIEN DOI: {bc['ty_le_bien_doi_truoc_%']}% -> "
                f"{bc['ty_le_bien_doi_sau_%']}%" if bc else "")
        print(f"      {ten:<12}: {n:>9,} dong x {c} cot{them}")

    print(f"\n[3/3] {int(cfg.data['n_splits'])} fold cross-validation")
    # CHONG RO RI TRONG CV: moi fold phai dung thong ke quy mo tinh RIENG tu
    # fold_n_train cua chinh no. Ban cu ap chung `thong_ke` cua CA tap train (trai toi
    # 2021-08) cho ca 5 fold - voi fold 1..4 thi do la thong ke cua TUONG LAI so voi
    # chinh fold do, khien diem CV lac quan hon thuc te va Optuna chon sieu tham so tren
    # so da bi thoi. Rieng fold 5 khong doi vi fold_5_train chinh la ca tap train.
    thu_muc_fold = vao / "time_series_folds"
    ra_fold = ra / "time_series_folds"
    ra_fold.mkdir(parents=True, exist_ok=True)
    thong_ke_fold: dict[str, dict] = {}
    for f in sorted(thu_muc_fold.glob("fold_*_train_time.parquet")):
        so = f.name.split("_")[1]
        thong_ke_fold[so] = s04c_site_scale.tinh_quy_mo_tu_train(
            f, cfg, ra_fold, ten_file=f"quy_mo_tram_fold_{so}.json"
        )
        print(f"      thong ke rieng cho fold {so}: "
              f"{len(thong_ke_fold[so]['site_scale'])} tram")

    for f in sorted(thu_muc_fold.glob("fold_*_time.parquet")):
        goc = f.name.replace("_time.parquet", "")
        so = goc.split("_")[1]
        tk = thong_ke_fold.get(so, thong_ke)
        n, c, _ = _xu_ly_1_tap(f, ra_fold / f"{goc}_spatial.parquet", tk, cfg)
        print(f"      {goc:<16}: {n:>9,} dong x {c} cot (thong ke fold {so})")

    print(f"\nDa ghi vao: {ra}")
    return ra
