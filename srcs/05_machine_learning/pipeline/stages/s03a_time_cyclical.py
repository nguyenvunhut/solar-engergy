"""Stage 03a: dac trung thoi gian (lich + tuan hoan) va mat na lich su lien tuc.

Tach tu buoc 4-5 cua run_features_time() trong 02_1_features_time.py.

KHONG CO RO RI: moi dac trung o day chi suy ra tu cot timestamp, khong dung toi
target. Do la ly do co the dich chung sang T+h (cot _mt) ma van hop le.

VI SAO DUNG sin/cos: gio 23 va gio 0 cach nhau 1 tieng that, nhung ve so hoc lai
cach nhau 23. Ma hoa tuan hoan giu dung khoang cach do (23h va 0h nam canh nhau
tren vong tron).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.columns import SITE_COL, TIMESTAMP_COL

# Nam ban cau (Uc) - nguoc voi Bac ban cau
MUA_NAM_BAN_CAU = {
    12: "summer", 1: "summer", 2: "summer",
    3: "autumn", 4: "autumn", 5: "autumn",
    6: "winter", 7: "winter", 8: "winter",
    9: "spring", 10: "spring", 11: "spring",
}
MA_MUA = {"summer": 0, "autumn": 1, "winter": 2, "spring": 3}
PHUT_1_NGAY = 1440.0
NGAY_1_NAM = 365.25


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Tao dac trung lich va tuan hoan CHI tu timestamp."""
    out = df.copy()
    ts = pd.to_datetime(out[TIMESTAMP_COL], errors="coerce")
    phut_trong_ngay = ts.dt.hour * 60 + ts.dt.minute
    ngay_trong_nam = ts.dt.dayofyear

    out["minute_of_day"] = phut_trong_ngay
    out["hour_sin"] = np.sin(2 * np.pi * phut_trong_ngay / PHUT_1_NGAY)
    out["hour_cos"] = np.cos(2 * np.pi * phut_trong_ngay / PHUT_1_NGAY)
    out["doy_sin"] = np.sin(2 * np.pi * ngay_trong_nam / NGAY_1_NAM)
    out["doy_cos"] = np.cos(2 * np.pi * ngay_trong_nam / NGAY_1_NAM)
    out["month"] = ts.dt.month
    out["day_of_week"] = ts.dt.dayofweek
    out["is_weekend"] = out["day_of_week"].isin([5, 6]).astype("int8")
    out["season"] = out["month"].map(MUA_NAM_BAN_CAU).astype("string")
    out["season_code"] = out["season"].map(MA_MUA).astype("Int64")

    # Mot so mart dung hour = -1 de chi khoi gio TRUOC do. Giu ca ban goc lan ban
    # da sua de model khong hieu -1 la mot gia tri so binh thuong.
    if "hour" in out.columns:
        out["hour_bucket_raw"] = pd.to_numeric(out["hour"], errors="coerce")
        out["hour_bucket_model"] = out["hour_bucket_raw"].replace(-1, 23)
    return out


def continuous_history_mask(nhom: pd.DataFrame, so_buoc: int, freq_minutes: int) -> pd.Series:
    """True khi `so_buoc` khoang thoi gian lien truoc deu dung freq_minutes.

    VI SAO CAN: neu cua so lich su vat qua cho dut gay thoi gian thi lag_96 khong
    con la "24h truoc" nua ma la "cach do 96 dong bat ky". Gia tri tinh ra van co
    so, van chay, nhung SAI - va khong bao loi. Mat na nay danh dau cac dong do de
    gan NaN thay vi de gia tri sai lot vao model.
    """
    hieu = nhom[TIMESTAMP_COL].diff().dt.total_seconds().div(60.0)
    dung_khoang = hieu.eq(freq_minutes)
    return (
        dung_khoang.rolling(so_buoc, min_periods=so_buoc)
        .sum()
        .eq(so_buoc)
        .fillna(False)
    )


def bao_cao_dac_trung_thoi_gian(df: pd.DataFrame) -> dict:
    """Thong ke nhanh de kiem tra dac trung sinh ra co hop ly khong."""
    cot = ["hour_sin", "hour_cos", "doy_sin", "doy_cos"]
    co = [c for c in cot if c in df.columns]
    return {
        "so_dong": len(df),
        "so_site": int(df[SITE_COL].nunique()),
        "khoang_gia_tri": {
            c: (round(float(df[c].min()), 4), round(float(df[c].max()), 4)) for c in co
        },
        "phan_bo_season": df["season"].value_counts().to_dict() if "season" in df else {},
    }
