"""Stage 04a: hinh hoc mat troi (goc cao, goc phuong vi) + buc xa troi quang.

Tach tu buoc 4 va 4.1 cua run_features_spatial() trong 02_2_features_spatial.py.

KHONG RO RI: goc mat troi la HAM XAC DINH cua (thoi diem, vi do, kinh do) - tinh bang
cong thuc thien van NOAA, khong phai du lieu do. Biet truoc 100 nam sau cung duoc.
Do la ly do duy nhat khien no duoc phep dich sang T+h (cot _mt) o stage s08.

HAI LOI DA SUA (giu lai ghi chu de khong tai pham):
  1. Goc phuong vi phai dung atan2, KHONG dung arccos. Ban arccos cu sinh diem gian
     doan gia, khien "trua mat troi" lech 40 phut so voi dinh cua sin_elevation.
  2. Mui gio phai theo mua (Uc doi gio he/dong). Tuong quan sin(goc cao) voi buc xa do
     duoc: 0,8625 khi theo mua vs 0,7523 neu dung UTC+10 co dinh.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.columns import TIMESTAMP_COL, require_columns
from core.config import Cfg

THANG_MUA_HE_UC = (10, 11, 12, 1, 2, 3)   # Uc doi sang gio he thang 10 -> thang 3
HANG_SO_HAURWITZ = 1098.0                 # W/m2
# He so suy hao trong cong thuc Haurwitz, lay DUNG ban cua pvlib (pvlib/clearsky.py, ham
# haurwitz): ghi = 1098 * cos(goc thien dinh) * exp(-0.059 / cos(goc thien dinh)).
# Truoc day o day la 0.057 trong khi notebook 03_2 dung 0.059, nen ghi_cs hai ben lech
# trung binh 0,365%. Sai lech do di thang vao he so cs_factor (phan vi 98 cua ty so
# shortwave/ghi_cs) roi lan ra ghi_cs, chi_so_troi_quang, rad_x_sinelev - cuoi cung lam
# WAPE kiem dinh lech toi 0,12 diem.
HE_SO_SUY_HAO = 0.059                     # he so suy hao quang hoc khi quyen chuan


def tinh_goc_mat_troi(ts, lat, lon, tz_gio) -> tuple[np.ndarray, np.ndarray]:
    """Goc cao va goc phuong vi mat troi theo do, cong thuc NOAA.

    Chuyen het sang numpy ngay tu dau: neu de pandas Series thi no giong theo INDEX,
    va vo khi dau vao co index khong lien tuc (frame da bi loc dong).
    """
    ts = pd.Series(pd.to_datetime(np.asarray(ts)))
    tz_gio = pd.Series(np.asarray(tz_gio, dtype="float64"))
    lat = pd.Series(np.asarray(lat, dtype="float64"))
    lon = pd.Series(np.asarray(lon, dtype="float64"))

    utc = ts - pd.to_timedelta(tz_gio, unit="h")
    doy = utc.dt.dayofyear.to_numpy()
    gio = utc.dt.hour.to_numpy() + utc.dt.minute.to_numpy() / 60
    g = 2 * np.pi / 365 * (doy - 1 + (gio - 12) / 24)

    eqtime = 229.18 * (
        0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g)
        - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g)
    )
    decl = (
        0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g)
        - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g)
        - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g)
    )
    tst = gio * 60 + eqtime + 4 * lon.to_numpy()
    ha = np.radians(tst / 4 - 180)
    la = np.radians(lat.to_numpy())

    sin_el = np.clip(
        np.sin(la) * np.sin(decl) + np.cos(la) * np.cos(decl) * np.cos(ha), -1, 1
    )
    el = np.degrees(np.arcsin(sin_el))
    # atan2 lien tuc tren ca vong 360 do - KHONG duoc thay bang arccos (xem docstring dau file)
    az = np.degrees(
        np.arctan2(-np.sin(ha), np.tan(decl) * np.cos(la) - np.sin(la) * np.cos(ha))
    )
    az = (az + 360.0) % 360.0   # 0 do = huong Bac, tang theo chieu kim dong ho
    return el, az


def add_metadata_features(df: pd.DataFrame) -> pd.DataFrame:
    """Dac trung metadata tram dang SO + co thieu du lieu.

    KHONG ma hoa categorical o day - viec do lam o stage s05, de bang ma duoc fit tren
    tap train roi moi ap cho val/test. Ma hoa som se gan ma khong nhat quan giua cac fold.
    """
    out = df.copy()
    for cot in ("capacity_kw", "number_of_panels"):
        if cot in out.columns:
            out[f"{cot}_missing_flag"] = out[cot].isna().astype("int8")

    if {"capacity_kw", "number_of_panels"}.issubset(out.columns):
        out["capacity_per_panel"] = out["capacity_kw"] / out["number_of_panels"]
        out.loc[~np.isfinite(out["capacity_per_panel"]), "capacity_per_panel"] = np.nan
    return out


def add_solar_geometry_features(df: pd.DataFrame, cfg: Cfg) -> pd.DataFrame:
    """Them goc mat troi va buc xa troi quang Haurwitz."""
    require_columns(df, ["latitude", "longitude", TIMESTAMP_COL])
    out = df.copy()

    thang = out[TIMESTAMP_COL].dt.month
    tz = pd.Series(
        np.where(thang.isin(THANG_MUA_HE_UC),
                 float(cfg.features["tz_he"]), float(cfg.features["tz_dong"])),
        index=out.index,
    )
    el, az = tinh_goc_mat_troi(out[TIMESTAMP_COL], out["latitude"], out["longitude"], tz)

    out["solar_elevation"] = el.astype("float32")
    out["solar_azimuth"] = az.astype("float32")
    # Goc phuong vi dang vong co diem gian doan o 0/360 - cay quyet dinh se coi 359 do va
    # 1 do la xa nhau trong khi thuc te chung canh nhau. Dang sin/cos khong co diem do.
    az_rad = np.radians(az)
    out["azimuth_sin"] = np.sin(az_rad).astype("float32")
    out["azimuth_cos"] = np.cos(az_rad).astype("float32")
    out["sin_elevation"] = np.clip(np.sin(np.radians(el)), 0, None).astype("float32")

    se = out["sin_elevation"]
    out["ghi_cs"] = np.where(
        se > 0,
        HANG_SO_HAURWITZ * se * np.exp(-HE_SO_SUY_HAO / np.clip(se, 1e-3, None)),
        0.0,
    ).astype("float32")
    out["clearsky_proxy"] = (out["sin_elevation"] ** 1.2).astype("float32")
    return out
