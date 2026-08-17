"""Stage 02: tach Development/Test + chia 5 fold CV (dieu phoi).

    python srcs/05_machine_learning/pipeline/run.py --stage s02

Dau vao : data/model/v3/01_reindex<suffix>/v3_continuous_grid.parquet
Dau ra  : data/model/v3/02_split<suffix>/
            development/     test/            final_train/
            train/  val/     (alias cua fold cuoi, de tuong thich code cu)
            time_series_folds/fold_{n}_{train|val}.parquet
            summaries/

TAP TEST TU DAY TRO DI LA "NIEM PHONG": khong duoc dung de train, tune, hay chon
mo hinh. Chi cham DUY NHAT 1 LAN o stage s09.
"""
from __future__ import annotations

import pandas as pd

from core.columns import SITE_COL, TARGET_COL, TIMESTAMP_COL, VERSION
from core.config import Cfg, load_config
from core.io import read_parquet, write_csv, write_parquet
from core.paths import Paths
from stages import s02a_dev_test_split, s02b_cv_folds

THU_MUC_CON = ("development", "test", "final_train", "train", "val",
               "time_series_folds", "summaries")

# Cac cot co dem trong bang tom tat, neu phan du lieu co chua chung (notebook 02).
COT_CO_DEM = tuple(
    f"{VERSION}_{ten}" for ten in (
        "missing_weather_flag", "outlier_flag", "exclude_from_loss_flag",
        "has_complete_history_features", "gap_after_prev_flag",
    )
)


def tom_tat_phan(ten: str, phan, fold=None, vai_tro=None) -> dict:
    """Mot dong tom tat cho 1 phan du lieu - copy nguyen si summarize_part() cua notebook 02.

    THU TU KHOA quyet dinh thu tu cot cua file CSV, phai giu dung: name, rows,
    site_count, min_timestamp, max_timestamp, target_null_rows, [fold], [role], [cac cot dem].
    """
    dong = {
        "name": ten,
        "rows": int(len(phan)),
        "site_count": int(phan[SITE_COL].nunique()) if SITE_COL in phan else 0,
        "min_timestamp": phan[TIMESTAMP_COL].min() if len(phan) else pd.NaT,
        "max_timestamp": phan[TIMESTAMP_COL].max() if len(phan) else pd.NaT,
        "target_null_rows": (
            int(phan[TARGET_COL].isna().sum()) if TARGET_COL in phan else 0
        ),
    }
    if fold is not None:
        dong["fold"] = fold
    if vai_tro is not None:
        dong["role"] = vai_tro
    for cot in COT_CO_DEM:
        if cot in phan.columns:
            dong[cot] = int(phan[cot].fillna(False).sum())
    return dong


def run_s02(cfg: Cfg | None = None):
    cfg = cfg or load_config()
    paths = Paths(cfg)

    duong_vao = paths.stage_doc("s01_reindex")
    if not duong_vao.exists():
        raise FileNotFoundError(
            f"Khong tim thay {duong_vao}. Chay stage s01 truoc:\n"
            f"    python srcs/05_machine_learning/pipeline/run.py --stage s01"
        )
    # SAP THEO (timestamp, site) - dung y notebook 02, KHONG phai (site, timestamp).
    # Thu tu dong tren dia anh huong truc tiep den .sample(random_state=...) o stage s07
    # (cham diem Mutual Information), nen sai thu tu la lech diem MI va lech ca danh sach
    # dac trung duoc chon.
    df = read_parquet(duong_vao, sap_xep=(TIMESTAMP_COL, SITE_COL))
    print(f"Doc {duong_vao.name}: {len(df):,} dong (sap theo timestamp, site)\n")

    print("[1/3] Tach Development / Test niem phong")
    kq = s02a_dev_test_split.tach(df, cfg, VERSION)
    df, dev, test = kq["df"], kq["development"], kq["test"]
    print()

    print("[2/3] Chia fold TimeSeriesSplit trong development")
    folds = s02b_cv_folds.tao_folds(kq["ts_development"], cfg)
    s02b_cv_folds.kiem_fold_khong_ro_ri(folds)
    bang = s02b_cv_folds.bang_tom_tat(folds)
    print(bang.to_string(index=False))
    print()

    print("[3/3] Ghi ket qua")
    goc = paths.stage("s02_split")
    for con in THU_MUC_CON:
        (goc / con).mkdir(parents=True, exist_ok=True)

    write_parquet(dev, goc / "development" / f"{VERSION}_development.parquet")
    write_parquet(test, goc / "test" / f"{VERSION}_test.parquet")
    write_parquet(dev, goc / "final_train" / f"{VERSION}_final_train.parquet")

    for f in folds:
        n = f["fold"]
        tr = s02b_cv_folds.loc_cua_so(df, f["train_start_ts"], f["train_end_ts"])
        va = s02b_cv_folds.loc_cua_so(df, f["val_start_ts"], f["val_end_ts"])
        for phan, vai_tro in ((tr, "train"), (va, "val")):
            phan[f"{VERSION}_cv_fold"] = n
            phan[f"{VERSION}_cv_role"] = vai_tro
            write_parquet(phan, goc / "time_series_folds" / f"fold_{n}_{vai_tro}.parquet")
        del tr, va

    # Alias train/val = fold CUOI, giu de code cu doc duoc. Loc lai tu df goc (khong tai
    # dung frame fold o tren) de KHONG mang theo cot cv_fold/cv_role - alias la tap doc lap.
    cuoi = folds[-1]
    tr_alias = s02b_cv_folds.loc_cua_so(df, cuoi["train_start_ts"], cuoi["train_end_ts"])
    va_alias = s02b_cv_folds.loc_cua_so(df, cuoi["val_start_ts"], cuoi["val_end_ts"])
    tr_alias[f"{VERSION}_split"] = "train"
    va_alias[f"{VERSION}_split"] = "val"
    test[f"{VERSION}_split"] = "test"
    write_parquet(tr_alias, goc / "train" / f"{VERSION}_train.parquet")
    write_parquet(va_alias, goc / "val" / f"{VERSION}_val.parquet")
    write_parquet(test, goc / "test" / f"{VERSION}_test.parquet")
    print(f"      alias train/val lay tu fold {cuoi['fold']} "
          f"({len(tr_alias):,} / {len(va_alias):,} dong)")

    # Hai bang tom tat: dung dinh dang cua notebook 02 (split_summary / fold_detail).
    # Truoc day file nay ghi mot dinh dang tu nghi ra (version/test_start_timestamp/...
    # va bang truc thoi gian) nen lech han voi notebook - sua 2026-08-08.
    write_csv(
        pd.DataFrame([
            tom_tat_phan("development", dev),
            tom_tat_phan("train_alias_final_fold", tr_alias),
            tom_tat_phan("val_alias_final_fold", va_alias),
            tom_tat_phan("test", test),
        ]),
        goc / "summaries" / f"{VERSION}_split_summary.csv",
    )

    dong_fold = []
    for f in folds:
        n = f["fold"]
        tr = s02b_cv_folds.loc_cua_so(df, f["train_start_ts"], f["train_end_ts"])
        va = s02b_cv_folds.loc_cua_so(df, f["val_start_ts"], f["val_end_ts"])
        dong_fold.append(tom_tat_phan(f"fold_{n}_train", tr, fold=n, vai_tro="train"))
        dong_fold.append(tom_tat_phan(f"fold_{n}_val", va, fold=n, vai_tro="val"))
        del tr, va
    write_csv(pd.DataFrame(dong_fold),
              goc / "summaries" / f"{VERSION}_time_series_fold_summary.csv")

    print(f"\nDa ghi vao: {goc}")
    print(f"  development : {len(dev):,} dong")
    print(f"  test        : {len(test):,} dong (NIEM PHONG - chi cham 1 lan o s09)")
    print(f"  folds       : {len(folds)} fold x 2 parquet")
    return {"development": dev, "test": test, "folds": folds}
