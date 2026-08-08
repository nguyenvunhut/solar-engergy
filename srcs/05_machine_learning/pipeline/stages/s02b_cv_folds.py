"""Stage 02b: chia 5 fold TimeSeriesSplit trong tap development.

Tach tu muc 9-11 cua run_split_time_series() trong 01_data_preprocessing.py.

VI SAO KHONG DUNG KFold: KFold tron ngau nhien -> fold sau co the nam TRUOC fold truoc
ve thoi gian, tuc la train tren tuong lai de du bao qua khu. TimeSeriesSplit dam bao
train luon nam truoc val ve thoi gian.

expanding vs sliding:
  expanding (mac dinh): tap train lon dan qua tung fold, giu het lich su.
  sliding             : tap train co do dai co dinh, truot theo thoi gian.
Chon expanding vi du lieu chi co ~2 nam, cat bot lich su lam mat mua vu.
"""
from __future__ import annotations

import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from core.columns import TIMESTAMP_COL
from core.config import Cfg


def tinh_kich_thuoc_fold(so_timestamp: int, cfg: Cfg) -> tuple[int, int | None]:
    """Tinh (test_size, max_train_size) cho TimeSeriesSplit."""
    n_splits = int(cfg.data["n_splits"])
    chien_luoc = cfg.data.get("split_strategy", "expanding")
    so_khoi_train = int(cfg.data.get("sliding_train_blocks", 3))

    if chien_luoc == "sliding":
        test_size = so_timestamp // (n_splits + so_khoi_train)
        max_train = test_size * so_khoi_train
    else:
        test_size = so_timestamp // (n_splits + 1)
        max_train = None

    if test_size <= 0:
        raise ValueError(
            f"Cua so validation rong: {so_timestamp} timestamp / {n_splits} fold "
            f"(chien luoc {chien_luoc}). Can them du lieu hoac giam n_splits."
        )
    if so_timestamp <= n_splits * test_size:
        raise ValueError(
            f"Khong du timestamp cho TimeSeriesSplit: {so_timestamp} timestamp, "
            f"{n_splits} fold x {test_size} = {n_splits * test_size}."
        )
    return test_size, max_train


def tao_folds(ts_development: pd.Series, cfg: Cfg) -> list[dict]:
    """Chia truc timestamp thanh cac fold. Tra ve list moc thoi gian tung fold."""
    n_splits = int(cfg.data["n_splits"])
    truc = pd.Series(ts_development).reset_index(drop=True)
    if len(truc) < n_splits + 2:
        raise ValueError(
            f"Chi co {len(truc)} timestamp trong development, can it nhat {n_splits + 2}."
        )

    test_size, max_train = tinh_kich_thuoc_fold(len(truc), cfg)
    print(f"Chien luoc: {cfg.data.get('split_strategy', 'expanding')} | "
          f"cua so val: {test_size} timestamp/fold | max_train: {max_train}")

    bo_chia = TimeSeriesSplit(n_splits=n_splits, test_size=test_size,
                             max_train_size=max_train)
    folds = []
    for so, (idx_train, idx_val) in enumerate(bo_chia.split(truc), start=1):
        ts_train = truc.iloc[idx_train].reset_index(drop=True)
        ts_val = truc.iloc[idx_val].reset_index(drop=True)
        folds.append({
            "fold": so,
            "train_timestamps": len(ts_train), "val_timestamps": len(ts_val),
            "train_start_ts": pd.Timestamp(ts_train.iloc[0]),
            "train_end_ts": pd.Timestamp(ts_train.iloc[-1]),
            "val_start_ts": pd.Timestamp(ts_val.iloc[0]),
            "val_end_ts": pd.Timestamp(ts_val.iloc[-1]),
        })
    return folds


def loc_cua_so(df: pd.DataFrame, tu: pd.Timestamp, den: pd.Timestamp) -> pd.DataFrame:
    """Lay cac dong co timestamp trong [tu, den] - hai dau deu tinh."""
    mask = (df[TIMESTAMP_COL] >= tu) & (df[TIMESTAMP_COL] <= den)
    return df.loc[mask].copy(deep=False)


def kiem_fold_khong_ro_ri(folds: list[dict]) -> None:
    """Trong moi fold, train phai ket thuc TRUOC khi val bat dau."""
    for f in folds:
        if f["train_end_ts"] >= f["val_start_ts"]:
            raise ValueError(
                f"RO RI o fold {f['fold']}: train ket thuc {f['train_end_ts']} "
                f"nhung val bat dau {f['val_start_ts']}."
            )
    print(f"Kiem {len(folds)} fold: DAT (train luon ket thuc truoc val)")


def bang_tom_tat(folds: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(folds)[
        ["fold", "train_timestamps", "val_timestamps",
         "train_start_ts", "train_end_ts", "val_start_ts", "val_end_ts"]
    ]
