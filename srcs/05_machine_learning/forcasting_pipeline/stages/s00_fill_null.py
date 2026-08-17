"""Stage 00: dien khuyet sieu du lieu va bien khi tuong.

    python srcs/05_machine_learning/forcasting_pipeline/run.py --stage s00

Dau vao : data/mlmart_base/v4_tai_lap/v4_preprocessing.parquet   (khoa paths.mlmart_raw)
Dau ra  : data/mlmart_base/v4_tai_lap/v4_final_cleaned.parquet   (khoa paths.mlmart_base)

Ca hai deu nam trong thu muc rieng v4_tai_lap/. Ban goc o cap tren
(data/mlmart_base/v4_preprocessing.parquet) KHONG duoc cham toi.

NGUON: notebook 00_fill_null_imputation.ipynb, ham run_pipeline().
Chep NGUYEN SI thu tu goi ham va tung nhanh dieu kien - doi thu tu la doi ket qua, vi
cac buoc sau doc gia tri ma buoc truoc vua dien.

THU TU BAT BUOC, khong duoc dao:
  1. fill_geo_coordinates      - toa do truoc, vi campus_name suy tu site_id
  2. fill_solar_site_metadata  - campus_name truoc, vi capacity_kw lay trung vi THEO campus
  3. fill_weather_metadata     - weather_type_id can month_tmp/hour_tmp
  4. fill_weather_is_day       - can hour_tmp, va doc bue xa da co
  5. fill_weather_metrics_advanced - dien 0 ban dem TRUOC roi moi ffill/trung vi

Hai cot tam month_tmp/hour_tmp duoc tao dau ham va xoa cuoi ham - khong ghi ra tep.

CAC COT CO Y KHONG DIEN (kiem lai truoc khi "sua"):
  gmm_if_outlier_reason  - chi dong bi gan nhan ngoai lai moi co ly do
  weather_id             - khoa tham chieu, vong lap bo qua bang `continue`
  weather_timestamp      - chi ep kieu ngay gio, khong co nhanh dien
  weather_type_is_day    - khong nam trong danh sach weather_meta
"""
from __future__ import annotations

import gc

import numpy as np
import pandas as pd

from core.config import Cfg, load_config
from core.io import read_parquet, write_parquet
from core.paths import Paths

COT_SIEU_DU_LIEU = ["campus_name", "capacity_kw", "number_of_panels", "panel",
                    "inverter", "optimizers", "site_metric", "location_name"]
COT_TOA_DO = ["latitude", "longitude"]
COT_THOI_TIET_META = ["weather_id", "weather_type_id", "weather_timestamp",
                      "weather_is_day", "weather_code", "weather_condition",
                      "weather_description"]
COT_DIEN_0_BAN_DEM = ["shortwave_radiation", "direct_normal_irradiance",
                      "diffuse_solar_radiation", "sunshine_duration",
                      "cloud_cover_total", "cloud_cover_low",
                      "cloud_cover_mid", "cloud_cover_high"]
COT_MAY = ["cloud_cover_total", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high"]
COT_BUC_XA = ["shortwave_radiation", "direct_normal_irradiance",
              "diffuse_solar_radiation", "sunshine_duration"]


def _dien_toa_do(df: pd.DataFrame) -> pd.DataFrame:
    for c in COT_TOA_DO:
        if c in df.columns:
            df[c] = df.groupby("site_id", observed=True)[c].transform(
                lambda x: x.ffill().bfill())
    return df


def _dien_sieu_du_lieu_tram(df: pd.DataFrame) -> pd.DataFrame:
    """capacity_kw/number_of_panels lay trung vi THEO KHUON VIEN nen campus_name phai xong truoc."""
    df["campus_name"] = df.groupby("site_id", observed=True)["campus_name"].transform(
        lambda x: x.ffill().bfill())
    df["campus_name"] = df["campus_name"].fillna("Unknown")

    for c in ("capacity_kw", "number_of_panels"):
        if c not in df.columns:
            continue
        df[f"{c}_is_imputed"] = df[c].isnull().astype(int)
        df[c] = df[c].fillna(
            df.groupby("campus_name", observed=True)[c].transform("median"))
        df[c] = df[c].fillna(df[c].median())

    for c in ("panel", "inverter", "location_name"):
        if c in df.columns:
            df[c] = df.groupby("site_id", observed=True)[c].transform(
                lambda x: x.ffill().bfill())
            df[c] = df[c].fillna("Unknown")

    if "optimizers" in df.columns:
        df["optimizers"] = df["optimizers"].fillna("None")
    if "site_metric" in df.columns:
        df["site_metric"] = df["site_metric"].fillna("kWh")
    return df


def _dien_thoi_tiet_meta(df: pd.DataFrame) -> pd.DataFrame:
    if "weather_timestamp" in df.columns:
        df["weather_timestamp"] = pd.to_datetime(df["weather_timestamp"], errors="coerce")
        df.loc[df["weather_timestamp"].dt.year < 2019, "weather_timestamp"] = pd.NaT

    for c in COT_THOI_TIET_META:
        if c not in df.columns or c == "weather_id":
            continue
        if c == "weather_type_id":
            df[c] = df.groupby("site_id", observed=True)[c].transform(
                lambda x: x.ffill().bfill())
            df[c] = df[c].fillna(
                df.groupby(["month_tmp", "hour_tmp"], observed=True)[c].transform(
                    lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan))
            df[c] = df[c].fillna(df[c].mode()[0] if not df[c].mode().empty else np.nan)
        elif c in ("weather_condition", "weather_description"):
            df[c] = df.groupby("site_id", observed=True)[c].transform(lambda x: x.ffill())
            df[c] = df[c].fillna("Unknown")
        elif c == "weather_code":
            df[c] = df.groupby("site_id", observed=True)[c].transform(
                lambda x: x.ffill().bfill())
    return df


def _dien_ban_ngay(df: pd.DataFrame) -> pd.DataFrame:
    if "weather_is_day" not in df.columns:
        return df
    la_ban_ngay = ((df["hour_tmp"] >= 6) & (df["hour_tmp"] <= 18)).astype(int)
    df["weather_is_day"] = df["weather_is_day"].fillna(la_ban_ngay)
    for c in COT_BUC_XA:
        if c in df.columns:
            m = df["weather_is_day"].isnull()
            df.loc[m, "weather_is_day"] = (df.loc[m, c] > 0).astype(int)
    df["weather_is_day"] = df["weather_is_day"].fillna(0)
    return df


def _dien_khi_tuong(df: pd.DataFrame) -> pd.DataFrame:
    """Dien 0 cho ban dem TRUOC, roi moi ffill/trung vi cho phan con lai."""
    df = df.sort_values(by=["site_id", "timestamp"]).set_index("timestamp")
    ban_dem = (df["hour_tmp"] < 5.5) | (df["hour_tmp"] >= 18.5)

    for c in COT_DIEN_0_BAN_DEM:
        if c in df.columns:
            df.loc[df[c].isnull() & ban_dem, c] = 0.0

    for c, han in (("temperature_c", 12), ("wind_speed", 4)):
        if c not in df.columns:
            continue
        df[f"{c}_is_imputed"] = df[c].isnull().astype(int)
        df[c] = df.groupby("site_id", observed=True)[c].transform(
            lambda x: x.ffill(limit=han))
        df[c] = df[c].fillna(
            df.groupby(["site_id", "hour_tmp"], observed=True)[c].transform("median"))
        df[c] = df[c].fillna(df[c].median())

    for c in COT_MAY:
        if c not in df.columns:
            continue
        df[f"{c}_is_imputed"] = df[c].isnull().astype(int)
        df[c] = df.groupby("site_id", observed=True)[c].transform(
            lambda x: x.ffill(limit=8))
        df[c] = df[c].fillna(
            df.groupby(["site_id", "hour_tmp"], observed=True)[c].transform("median"))
        df[c] = df[c].fillna(df[c].median())

    if "precipitation_mm" in df.columns:
        df["precipitation_mm_is_imputed"] = df["precipitation_mm"].isnull().astype(int)
        df["precipitation_mm"] = df["precipitation_mm"].fillna(0.0)

    return df.reset_index()


def run_s00(cfg: Cfg | None = None):
    cfg = cfg or load_config()
    paths = Paths(cfg)

    duong_vao = paths.mlmart_raw
    duong_ra = paths.mlmart_base
    if not duong_vao.exists():
        raise FileNotFoundError(
            f"Khong tim thay {duong_vao}. Kiem lai paths.yaml: mlmart_raw")
    if duong_ra.exists():
        raise FileExistsError(
            f"{duong_ra} da ton tai. Stage nay KHONG duoc ghi de - doi paths.yaml: "
            f"mlmart_base sang duong dan moi, hoac xoa tay tep cu neu that su muon dung lai.")

    df = read_parquet(duong_vao, sap_xep=None)
    n_dong_vao, n_cot_vao = df.shape
    nan_truoc = int((df.isna().sum() > 0).sum())
    print(f"Doc {duong_vao.name}: {n_dong_vao:,} dong x {n_cot_vao} cot "
          f"| {nan_truoc} cot mang o khuyet")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["month_tmp"] = df["timestamp"].dt.month
    df["hour_tmp"] = df["timestamp"].dt.hour

    df = _dien_toa_do(df)
    df = _dien_sieu_du_lieu_tram(df)
    df = _dien_thoi_tiet_meta(df)
    df = _dien_ban_ngay(df)
    df = _dien_khi_tuong(df)

    df = df.drop(columns=["month_tmp", "hour_tmp"])

    nan_sau = int((df.isna().sum() > 0).sum())
    co_cua = [c for c in df.columns if c.endswith("_is_imputed")]
    if len(df) != n_dong_vao:
        raise AssertionError(
            f"So dong doi: vao {n_dong_vao:,} ra {len(df):,}. Stage nay chi duoc dien "
            f"gia tri, khong duoc them/bot dong.")

    paths.tao_thu_muc(duong_ra.parent)
    write_parquet(df, duong_ra)
    print(f"Ghi {duong_ra.name}: {len(df):,} dong x {df.shape[1]} cot")
    print(f"  cot mang o khuyet: {nan_truoc} -> {nan_sau}")
    print(f"  cot co danh dau da dien: {len(co_cua)} ({', '.join(co_cua)})")

    del df
    gc.collect()
    return duong_ra
