"""Cac chi so danh gia. Copy NGUYEN SI tu compute_wape()/compute_metrics()/
metrics_3_pham_vi() trong utils.py + 04_x_train_*.py.

QUY UOC BAO CAO (khong duoc noi long):
  Con so cong bo (headline) CHI duoc tinh tren pham vi 'measured_daylight' -
  tuc energy_source == 'measured' VA is_daylight == True. Tinh tren 'all' se
  bao gom ca dong impute/ban dem -> so dep gia tao, khong dung su that.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error

from .columns import DAYLIGHT_COL, PRED_COL, SOURCE_COL, TARGET_SHIFTED

# Pham vi duy nhat duoc dung cho con so cong bo trong bao cao
PHAM_VI_CHINH_THUC = "measured_daylight"


def compute_wape(yt, yp) -> float:
    """WAPE = tong sai so tuyet doi / tong san luong that, don vi %.

    Dung nansum (bo qua NaN). Chon WAPE thay vi MAPE vi MAPE vo nghia khi y_true = 0
    (ban dem san luong = 0 -> chia cho 0).
    """
    mau = np.nansum(np.abs(yt))
    return float(np.nansum(np.abs(yt - yp)) / mau * 100.0) if mau > 0 else np.nan


def compute_metrics(yt, yp) -> dict:
    """Bo 4 chi so + so dong. Tra ve dict de ghi thang ra JSON."""
    return {
        "wape": compute_wape(yt, yp),
        "rmse": float(root_mean_squared_error(yt, yp)),
        "mae": float(mean_absolute_error(yt, yp)),
        "r2": float(r2_score(yt, yp)),
        "n": int(len(yt)),
    }


def _cot_loc(df: pd.DataFrame, ten_goc: str) -> pd.Series | None:
    """Tra ve cot dung de loc pham vi, UU TIEN ban tai T+h (tien to nhan_).

    VI SAO: nhan la y(T+h), nen "do that ban ngay" phai xet dong T+h chu khong phai
    dong dac trung tai T. Ban cu loc theo cot tai T nen van dem ca nhung dong ma NHAN
    do buoc dien khuyet ETL sinh ra. Do da: sai lech +0,11 diem WAPE o h1 va +0,34 o h4
    tren tap test (2026-08-09). them_muc_tieu() sinh san cac cot nhan_* nen o day chi
    can uu tien chung; neu khung khong co (vi du du lieu ngoai pipeline) thi lui ve
    cot tai T nhu cu de khong vo code goi.
    """
    ten_nhan = f"nhan_{ten_goc}"
    if ten_nhan in df.columns:
        return df[ten_nhan]
    if ten_goc in df.columns:
        return df[ten_goc]
    return None


def metrics_3_pham_vi(df: pd.DataFrame) -> dict:
    """Ba pham vi: all / measured / measured_daylight.

    Con so CHINH THUC dua vao bao cao la measured_daylight - hai pham vi kia chi de
    doi chieu, cho thay chenh lech giua "toan bo du lieu" va "du lieu do that ban ngay".
    """
    yt = df[TARGET_SHIFTED].values
    yp = df[PRED_COL].values
    res = {"all": compute_metrics(yt, yp)}

    cot_nguon = _cot_loc(df, SOURCE_COL)
    m = (
        (cot_nguon == "measured").to_numpy()
        if cot_nguon is not None
        else np.ones(len(df), bool)
    )
    if m.sum():
        res["measured"] = compute_metrics(yt[m], yp[m])

    cot_ngay = _cot_loc(df, DAYLIGHT_COL)
    if cot_ngay is not None:
        md = m & cot_ngay.fillna(False).astype(bool).to_numpy()
        if md.sum():
            res[PHAM_VI_CHINH_THUC] = compute_metrics(yt[md], yp[md])
    return res


def metrics_theo_site(df: pd.DataFrame, site_col: str = "site_id") -> pd.DataFrame:
    """Chi so tach rieng tung tram - de phat hien tram nao te bat thuong.

    Trung binh gop cua 42 tram co the che giau 1 tram hong hoan toan, nen bang nay
    la bat buoc khi bao cao.
    """
    dong = []
    for site, nhom in df.groupby(site_col, observed=True):
        dong.append({
            site_col: site,
            "rows": len(nhom),
            **compute_metrics(nhom[TARGET_SHIFTED].values, nhom[PRED_COL].values),
        })
    return pd.DataFrame(dong)


def skill_score(wape_model: float, wape_baseline: float) -> float:
    """SS = (1 - WAPE_model / WAPE_baseline) * 100%.

    SS > 0: model that su hoc duoc quy luat. SS <= 0: khong hon gi viec chep gia tri
    gan nhat. Phai ghi ro baseline nao khi bao cao - SS so voi persistence khac han
    SS so voi Prophet.
    """
    if not wape_baseline or wape_baseline <= 0 or np.isnan(wape_baseline):
        return float("nan")
    return float((1.0 - wape_model / wape_baseline) * 100.0)
