"""Stage 03: sinh dac trung thoi gian + lag/rolling cho moi tap con (dieu phoi).

    python srcs/05_machine_learning/pipeline/run.py --stage s03

Dau vao : data/model/v3/02_split<suffix>/
Dau ra  : data/model/v3/03_1_features_time<suffix>/

QUY TAC BACKWARD CONTEXT (quan trong): tap sau dung tap TRUOC lam context lich su.
  development -> khong can context (la du lieu som nhat)
  test        -> context = TOAN BO development
  fold_n_val  -> context = fold_n_train cua chinh no (moi fold la 1 thi nghiem khep kin)
Context chi di tu QUA KHU sang, khong bao gio nguoc lai -> khong ro ri.
"""
from __future__ import annotations

import gc

from core.columns import VERSION
from core.config import Cfg, load_config
from core.io import read_parquet, write_parquet
from core.paths import Paths
from stages import s03b_lag_rolling


def _sinh_va_ghi(ctx_df, target_df, vai_tro: str, duong_ra, cfg: Cfg) -> tuple[int, int]:
    kq = s03b_lag_rolling.build_features_with_backward_context(
        ctx_df, target_df, vai_tro, cfg
    )
    write_parquet(kq, duong_ra)
    hinh = (len(kq), kq.shape[1])
    del kq
    gc.collect()
    return hinh


def run_s03(cfg: Cfg | None = None):
    cfg = cfg or load_config()
    paths = Paths(cfg)
    vao = paths.stage_doc("s02_split")
    ra = paths.stage("s03_features")
    if not vao.exists():
        raise FileNotFoundError(
            f"Khong tim thay {vao}. Chay stage s02 truoc:\n"
            f"    python srcs/05_machine_learning/pipeline/run.py --stage s02"
        )
    ra.mkdir(parents=True, exist_ok=True)
    print(f"So cot lag/rolling se tao: {s03b_lag_rolling.so_cot_se_tao(cfg)} "
          f"(lags={cfg.features['lags']}, rolling={cfg.features['rolling_windows']})\n")

    print("[1/3] development va test")
    dev = read_parquet(vao / "development" / f"{VERSION}_development.parquet")
    test = read_parquet(vao / "test" / f"{VERSION}_test.parquet")
    n_dev = _sinh_va_ghi(None, dev, "development",
                         ra / f"{VERSION}_development_time.parquet", cfg)
    n_test = _sinh_va_ghi(dev, test, "test",
                          ra / f"{VERSION}_test_time.parquet", cfg)
    print(f"      development: {n_dev[0]:,} dong x {n_dev[1]} cot")
    print(f"      test       : {n_test[0]:,} dong x {n_test[1]} cot (context = development)")
    del dev, test
    gc.collect()

    print("\n[2/3] alias train / val")
    tr = read_parquet(vao / "train" / f"{VERSION}_train.parquet")
    va = read_parquet(vao / "val" / f"{VERSION}_val.parquet")
    n_tr = _sinh_va_ghi(None, tr, "train_alias", ra / f"{VERSION}_train_time.parquet", cfg)
    n_va = _sinh_va_ghi(tr, va, "val_alias", ra / f"{VERSION}_val_time.parquet", cfg)
    print(f"      train: {n_tr[0]:,} dong | val: {n_va[0]:,} dong (context = train)")
    del tr, va
    gc.collect()

    print("\n[3/3] 5 fold cross-validation")
    thu_muc_fold = vao / "time_series_folds"
    thu_muc_ra_fold = ra / "time_series_folds"
    thu_muc_ra_fold.mkdir(parents=True, exist_ok=True)

    ten_train = sorted(p.name for p in thu_muc_fold.glob("fold_*_train.parquet"))
    if not ten_train:
        raise FileNotFoundError(f"Khong thay fold nao trong {thu_muc_fold}")

    for ten in ten_train:
        goc = ten.replace("_train.parquet", "")
        duong_val = thu_muc_fold / f"{goc}_val.parquet"
        if not duong_val.exists():
            raise FileNotFoundError(f"Thieu file val cua fold: {duong_val}")

        f_tr = read_parquet(thu_muc_fold / ten)
        f_va = read_parquet(duong_val)
        a = _sinh_va_ghi(None, f_tr, f"{goc}_train",
                         thu_muc_ra_fold / f"{goc}_train_time.parquet", cfg)
        b = _sinh_va_ghi(f_tr, f_va, f"{goc}_val",
                         thu_muc_ra_fold / f"{goc}_val_time.parquet", cfg)
        print(f"      {goc}: train {a[0]:,} dong | val {b[0]:,} dong | {a[1]} cot")
        del f_tr, f_va
        gc.collect()

    print(f"\nDa ghi vao: {ra}")
    return ra
