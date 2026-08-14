"""Stage 05a: dac trung tuong tac thoi tiet (ngoai sinh).

Tach tu buoc 4 cua run_features_aggregate() trong 02_3_features_aggregate.py.

KHONG RO RI: moi dac trung o day chi to hop cac bien THOI TIET voi nhau, khong dung
toi target. Tat ca deu la du lieu do tai thoi diem T (khong dich sang T+h).

VI SAO TACH RIENG cloud_cover_low: may tang THAP moi thuc su che nang manh, may tang
CAO (cirrus) gan nhu khong can nang - gop chung vao cloud_cover_total co the mat tin
hieu nay. Nguon: ScienceDirect pii S0960148125004835 (SHAP analysis, xep hang PPS -
ty le PV bi che - va cac dac trung lien quan may/bong); MDPI 1996-1073/18/8/2108.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Tran cho cac ty le - buc xa khuech tan/truc tiep chia cho tong co the no khi mau gan 0
TRAN_TY_LE = 10.0


def add_weather_domain_features(df: pd.DataFrame) -> pd.DataFrame:
    """Tao dac trung tuong tac thoi tiet. Bo qua cap cot nao khong co du."""
    out = df.copy()
    co = set(out.columns)

    if {"shortwave_radiation", "temperature_c"} <= co:
        # nhiet do cao lam giam hieu suat quang dien - tuong tac nay phi tuyen
        out["temp_x_shortwave"] = out["temperature_c"] * out["shortwave_radiation"]

    if {"shortwave_radiation", "diffuse_solar_radiation"} <= co:
        mau = out["shortwave_radiation"].replace(0, np.nan)
        out["diffuse_ratio"] = (
            out["diffuse_solar_radiation"] / mau
        ).clip(lower=0, upper=TRAN_TY_LE)

    if {"direct_normal_irradiance", "shortwave_radiation"} <= co:
        mau = out["shortwave_radiation"].replace(0, np.nan)
        out["dni_ratio"] = (
            out["direct_normal_irradiance"] / mau
        ).clip(lower=0, upper=TRAN_TY_LE)

    if {"cloud_cover_total", "shortwave_radiation"} <= co:
        out["cloud_x_shortwave"] = out["cloud_cover_total"] * out["shortwave_radiation"]

    if {"cloud_cover_low", "shortwave_radiation"} <= co:
        out["cloud_low_x_shortwave"] = (
            out["cloud_cover_low"] * out["shortwave_radiation"]
        )
    return out


def kiem_khong_inf(df: pd.DataFrame) -> dict:
    """Dem gia tri inf/NaN o cac cot vua tao - ty le chia co the sinh inf."""
    cot = [c for c in ("temp_x_shortwave", "diffuse_ratio", "dni_ratio",
                       "cloud_x_shortwave", "cloud_low_x_shortwave") if c in df.columns]
    ket = {}
    for c in cot:
        s = df[c]
        ket[c] = {
            "inf": int(np.isinf(s.to_numpy(dtype="float64", na_value=0.0)).sum()),
            "nan": int(s.isna().sum()),
            "nan_%": round(float(s.isna().mean() * 100), 2),
        }
    ket["dat"] = all(v["inf"] == 0 for v in ket.values() if isinstance(v, dict))
    return ket
