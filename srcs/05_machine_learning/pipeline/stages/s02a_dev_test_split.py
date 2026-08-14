"""Stage 02a: tach tap Development / Test niem phong theo TRUC THOI GIAN.

Tach tu muc 7-8 cua run_split_time_series() trong 01_data_preprocessing.py.

HAI DIEU CHONG RO RI, khong duoc lam khac:
  1. Cat theo THOI GIAN, khong random. Chuoi thoi gian ma cat ngau nhien la dua
     tuong lai vao tap train -> WAPE dep gia tao, ra thuc te thi hong.
  2. Cat tren truc UNIQUE TIMESTAMP, khong phai tren tung dong. Neu cat theo dong,
     cung 1 timestamp co the roi vao ca train lan test o 2 site khac nhau - luc do
     model biet truoc "gio do troi the nao".
"""
from __future__ import annotations

import pandas as pd

from core.columns import SITE_COL, TIMESTAMP_COL
from core.config import Cfg


def tim_moc_cat(df: pd.DataFrame, cfg: Cfg) -> tuple[pd.Timestamp, pd.Series, pd.Series]:
    """Tim timestamp bat dau tap test. Tra ve (moc_cat, ts_development, ts_test)."""
    ty_le = float(cfg.data["test_ratio"])
    n_splits = int(cfg.data["n_splits"])

    ts = pd.Series(df[TIMESTAMP_COL].dropna().sort_values().unique())
    n = len(ts)
    if n < n_splits + 3:
        raise ValueError(
            f"Chi co {n} unique timestamp, khong du de vua tach test vua chia "
            f"{n_splits} fold. Kiem lai du lieu dau vao."
        )

    # Giu it nhat n_splits + 2 timestamp cho development, va it nhat 1 cho test
    vi_tri = int(n * (1.0 - ty_le))
    vi_tri = min(max(vi_tri, n_splits + 2), n - 1)

    moc = pd.Timestamp(ts.iloc[vi_tri])
    return moc, ts.iloc[:vi_tri].reset_index(drop=True), ts.iloc[vi_tri:].reset_index(drop=True)


def gan_nhan_holdout(
    df: pd.DataFrame, moc_cat: pd.Timestamp, cfg: Cfg, version: str = "v3"
) -> pd.DataFrame:
    """Gan cot <version>_holdout_split = development | test + metadata ve cach chia."""
    out = df.copy()
    out[f"{version}_holdout_split"] = "development"
    out.loc[out[TIMESTAMP_COL] >= moc_cat, f"{version}_holdout_split"] = "test"
    out[f"{version}_test_start_timestamp"] = moc_cat
    out[f"{version}_split_strategy"] = cfg.data.get("split_strategy", "expanding")
    out[f"{version}_n_time_series_splits"] = int(cfg.data["n_splits"])
    return out


def tach(df: pd.DataFrame, cfg: Cfg, version: str = "v3") -> dict:
    """Tach thanh development / test. Tra ve dict chua ca hai va thong tin moc cat."""
    moc, ts_dev, ts_test = tim_moc_cat(df, cfg)
    n_ts = len(ts_dev) + len(ts_test)

    print(f"Tong unique timestamp : {n_ts:,}")
    print(f"Moc bat dau tap test  : {moc}")
    print(f"Development : {len(ts_dev):,} timestamp ({len(ts_dev) / n_ts:.2%})  "
          f"{ts_dev.iloc[0]} -> {ts_dev.iloc[-1]}")
    print(f"Test        : {len(ts_test):,} timestamp ({len(ts_test) / n_ts:.2%})  "
          f"{ts_test.iloc[0]} -> {ts_test.iloc[-1]}")

    df = gan_nhan_holdout(df, moc, cfg, version)
    cot_nhan = f"{version}_holdout_split"
    dev = df.loc[df[cot_nhan].eq("development")].copy(deep=False)
    test = df.loc[df[cot_nhan].eq("test")].copy(deep=False)

    print(f"Development : {len(dev):,} dong ({len(dev) / len(df):.2%}), "
          f"{dev[SITE_COL].nunique()} site")
    print(f"Test        : {len(test):,} dong ({len(test) / len(df):.2%}), "
          f"{test[SITE_COL].nunique()} site")

    kiem_khong_chong_lan(dev, test)
    return {
        "df": df, "development": dev, "test": test,
        "moc_cat": moc, "ts_development": ts_dev, "ts_test": ts_test,
    }


def kiem_khong_chong_lan(dev: pd.DataFrame, test: pd.DataFrame) -> None:
    """Bao loi neu 2 tap co timestamp trung nhau - dau hieu ro ri nghiem trong."""
    if dev.empty or test.empty:
        raise ValueError("Mot trong hai tap development/test rong sau khi tach.")
    max_dev = dev[TIMESTAMP_COL].max()
    min_test = test[TIMESTAMP_COL].min()
    if max_dev >= min_test:
        raise ValueError(
            f"RO RI: development ket thuc {max_dev} nhung test bat dau {min_test}. "
            f"Hai tap phai tach roi han theo thoi gian."
        )
    chung = set(dev[TIMESTAMP_COL].unique()) & set(test[TIMESTAMP_COL].unique())
    if chung:
        raise ValueError(f"RO RI: {len(chung)} timestamp xuat hien o CA development lan test.")
    print(f"Kiem chong lan: DAT (development het luc {max_dev}, test bat dau {min_test})")
