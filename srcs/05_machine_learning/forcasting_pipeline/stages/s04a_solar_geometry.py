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

from zoneinfo import ZoneInfo

import pvlib  # noqa: F401  (in phien ban trong log de truy vet)
from pvlib import clearsky, solarposition

from core.columns import TIMESTAMP_COL, require_columns
from core.config import Cfg

_TZ_MELBOURNE = ZoneInfo("Australia/Melbourne")


def offset_gio_theo_ngay(ts) -> np.ndarray:
    """Offset UTC cua Melbourne theo NGAY, lay tai 12h trua.

    DST doi luc 2-3h sang nen gia tri giua trua dung cho toan bo phan ban ngay,
    va tranh duoc gio mo ho quanh moc doi gio. Chep tu notebook 03_2.
    """
    ngay = pd.Series(pd.to_datetime(np.asarray(ts))).dt.normalize()
    bang = {d: pd.Timestamp(d + pd.Timedelta(hours=12), tz=_TZ_MELBOURNE)
                 .utcoffset().total_seconds() / 3600.0
            for d in ngay.unique()}
    return ngay.map(bang).to_numpy()

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
        # Ep ve float64 cua numpy TRUOC khi chia: tu ban trich v5, hai cot cong suat giu
        # nguyen khuyet o 17/42 tram nen chung co the mang dtype nullable (Int64/Float64
        # chua pd.NA). np.isfinite khong nhan pd.NA va se nem TypeError - loi chi lo ra o
        # duong phuc vu (dashboard doc metadata tram), khong lo ra khi chay notebook.
        cap = pd.to_numeric(out["capacity_kw"], errors="coerce").astype("float64")
        panels = pd.to_numeric(out["number_of_panels"], errors="coerce").astype("float64")
        out["capacity_per_panel"] = cap / panels
        out.loc[~np.isfinite(out["capacity_per_panel"]), "capacity_per_panel"] = np.nan
    return out


def add_solar_geometry_features(df: pd.DataFrame, cfg: Cfg) -> pd.DataFrame:
    """Them goc mat troi (pvlib SPA) va buc xa troi quang (pvlib Haurwitz).

    SUA 2026-08-22: bo cong thuc NOAA tu viet + mui gio xap xi THEO THANG, thay bang
    pvlib SPA + lich DST that cua Australia/Melbourne - dung y notebook 03_2. Ban cu
    lech toi 12,5 do goc cao quanh cac moc doi gio (notebook 03_2b do duoc p99 8,54 do,
    max 12,35 do tren 19/844 ngay), keo theo sai lech o sin_elevation, ghi_cs, ky_vong,
    ty_le_bao_hoa va rad_x_sinelev. Trich dan: Reda & Andreas 2004 (SPA); Haurwitz
    1945/46; Holmgren et al. 2018, pvlib python, JOSS 3(29):884.
    """
    require_columns(df, ["latitude", "longitude", TIMESTAMP_COL])
    out = df.copy()

    tz_gio = offset_gio_theo_ngay(out[TIMESTAMP_COL])
    utc = (pd.DatetimeIndex(out[TIMESTAMP_COL])
           - pd.to_timedelta(tz_gio, unit="h")).tz_localize("UTC")

    # Goi pvlib theo tung cap toa do (5 khuon vien -> 5 loi goi vector hoa)
    el = np.full(len(out), np.nan)
    az = np.full(len(out), np.nan)
    for (lat, lon), vi_tri in out.groupby(["latitude", "longitude"]).indices.items():
        sp = solarposition.get_solarposition(utc[vi_tri], latitude=lat, longitude=lon)
        # 'elevation' = goc cao HINH HOC (khong khuc xa) - cung he quy chieu voi ban cu
        el[vi_tri] = sp["elevation"].to_numpy()
        az[vi_tri] = sp["azimuth"].to_numpy()   # 0 do = Bac, thuan chieu kim dong ho

    out["solar_elevation"] = el.astype("float32")
    out["solar_azimuth"] = az.astype("float32")
    # Goc phuong vi dang vong co diem gian doan o 0/360 - cay quyet dinh se coi 359 do va
    # 1 do la xa nhau trong khi thuc te chung canh nhau. Dang sin/cos khong co diem do.
    az_rad = np.radians(az)
    out["azimuth_sin"] = np.sin(az_rad).astype("float32")
    out["azimuth_cos"] = np.cos(az_rad).astype("float32")
    out["sin_elevation"] = np.clip(np.sin(np.radians(el)), 0, None).astype("float32")

    # Troi quang Haurwitz: goi THANG ban cai dat cua pvlib thay vi viet lai cong thuc,
    # de khong lech he so suy hao. Clip zenith ve [0, 90] tranh tran so o goc am.
    _zen = np.clip(90.0 - out["solar_elevation"].to_numpy(dtype="float64"), 0.0, 90.0)
    _ghi = clearsky.haurwitz(pd.Series(_zen))["ghi"].to_numpy()
    out["ghi_cs"] = np.where(out["sin_elevation"] > 0, _ghi, 0.0).astype("float32")
    out["clearsky_proxy"] = (out["sin_elevation"] ** 1.2).astype("float32")
    return out
