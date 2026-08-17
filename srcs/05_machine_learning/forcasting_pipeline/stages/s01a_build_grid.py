"""Stage 01a: dung luoi thoi gian 15 phut lien tuc cho tung site + cot lich.

Tach tu muc 4-6 cua run_reindex_mask_outlier() trong 01_data_preprocessing.py.

VI SAO PHAI REINDEX: du lieu goc co slot bi thieu (mat ket noi, bao tri). Neu khong
dung luoi lien tuc thi shift(-h) va rolling() se nhay qua khoang trong - lag_96 se
khong con dung 24h truoc, tinh sai ma khong bao loi.
"""
from __future__ import annotations

import pandas as pd

from core.columns import SITE_COL, TIMESTAMP_COL
from core.config import Cfg

# Nam ban cau (Uc): thang 12-2 la he, 6-8 la dong - nguoc voi Bac ban cau.
MUA_NAM_BAN_CAU = {
    12: "summer", 1: "summer", 2: "summer",
    3: "autumn", 4: "autumn", 5: "autumn",
    6: "winter", 7: "winter", 8: "winter",
    9: "spring", 10: "spring", 11: "spring",
}

COT_THOI_TIET = [
    "weather_is_day", "shortwave_radiation", "direct_normal_irradiance",
    "diffuse_solar_radiation", "temperature_c", "cloud_cover_total",
    "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high",
    "wind_speed", "precipitation_mm", "sunshine_duration",
    "weather_code", "weather_condition", "weather_description",
]

# Gia tri mac dinh cho cot provenance tren dong moi chen
MAC_DINH_PROVENANCE = {
    "energy_source": "",
    "exclude_from_training": False,
    "exclude_reason": "",
    "training_quality_reason": "",
    "after_source_gap_steps_remaining": 0,
    "gmm_if_outlier_flag": False,
    "gmm_if_outlier_reason": "",
}


def reindex_luoi(df: pd.DataFrame, cfg: Cfg) -> pd.DataFrame:
    """Tao luoi timestamp lien tuc tu min den max cua TUNG site.

    Lam theo tung site chu khong theo toan bo bang: cac site co khoang thoi gian
    hoat dong khac nhau, dung chung min/max se sinh ra hang trieu dong rong.
    """
    freq = f"{int(cfg.data['freq_minutes'])}min"
    phan = []
    for site_id, nhom in df.groupby(SITE_COL, observed=True, sort=True):
        luoi = pd.DataFrame({
            TIMESTAMP_COL: pd.date_range(
                nhom[TIMESTAMP_COL].min(), nhom[TIMESTAMP_COL].max(), freq=freq
            )
        })
        gop = luoi.merge(nhom, on=TIMESTAMP_COL, how="left", sort=True)
        gop[SITE_COL] = gop[SITE_COL].fillna(site_id)
        gop["timestamp_was_inserted"] = (
            gop["timestamp_was_inserted"].fillna(True).astype(bool)
        )
        phan.append(gop)

    out = pd.concat(phan, ignore_index=True)
    return out.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)


def them_cot_lich(df: pd.DataFrame) -> pd.DataFrame:
    """Them cot lich suy ra tu timestamp - deu la ham xac dinh, khong phai du lieu do."""
    out = df.copy()
    ts = pd.to_datetime(out[TIMESTAMP_COL])
    out["minute_of_day"] = ts.dt.hour * 60 + ts.dt.minute
    out["quarter_hour"] = out["minute_of_day"] // 15
    out["hour_of_day"] = ts.dt.hour
    out["day_of_week_model"] = ts.dt.dayofweek
    out["month_model"] = ts.dt.month
    out["day_of_year"] = ts.dt.dayofyear
    out["season_model"] = ts.dt.month.map(MUA_NAM_BAN_CAU)
    return out


def gan_provenance_mac_dinh(df: pd.DataFrame) -> pd.DataFrame:
    """Dien gia tri mac dinh cho cot provenance tren dong moi chen + co weather_is_observed."""
    out = df.copy()
    for cot, mac_dinh in MAC_DINH_PROVENANCE.items():
        if cot not in out.columns:
            out[cot] = mac_dinh
            continue
        out[cot] = out[cot].fillna(mac_dinh)
        if isinstance(mac_dinh, bool):
            out[cot] = out[cot].astype(bool)
        elif isinstance(mac_dinh, int):
            out[cot] = out[cot].astype(int)

    # weather_is_observed = dong goc VA co it nhat 1 truong thoi tiet do duoc.
    # Can co nay de phan biet thoi tiet DO THAT voi thoi tiet duoc ffill xuong.
    kiem = [c for c in ("shortwave_radiation", "temperature_c", "cloud_cover_total",
                        "wind_speed", "precipitation_mm") if c in out.columns]
    out["weather_is_observed"] = (
        (~out["timestamp_was_inserted"]) & out[kiem].notna().any(axis=1)
        if kiem else False
    )
    return out


def ffill_thoi_tiet(df: pd.DataFrame, cfg: Cfg) -> tuple[pd.DataFrame, dict]:
    """Forward-fill thoi tiet theo TUNG SITE.

    CHI ffill (keo qua khu sang hien tai). TUYET DOI khong bfill - bfill keo gia tri
    cua gio SAU ve gio TRUOC, tuc la dua thong tin tuong lai vao qua khu = ro ri.
    """
    if cfg.data["weather_fill"] != "ffill":
        raise ValueError(
            f"weather_fill = '{cfg.data['weather_fill']}' khong hop le. Chi chap nhan "
            f"'ffill' - moi cach dien khac deu co nguy co keo du lieu tuong lai ve qua khu."
        )
    out = df.copy()
    cot = [c for c in COT_THOI_TIET if c in out.columns]
    truoc = int(out[cot].isna().sum().sum())
    out[cot] = out.groupby(SITE_COL)[cot].transform(lambda x: x.ffill())
    sau = int(out[cot].isna().sum().sum())
    return out, {"so_cot": len(cot), "nan_truoc": truoc, "nan_sau": sau,
                 "da_lap": truoc - sau}
