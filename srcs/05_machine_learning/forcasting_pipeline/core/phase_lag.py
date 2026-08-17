"""Do do tre pha giua duong du bao va duong thuc te.

Copy NGUYEN SI tu do_tre_phut()/quet_do_tre() trong 04_x_train_*.py va
he_so_tre_phut() trong srcs/07_dashboard/dashboard_data.py (3 ban gan giong nhau).

VI SAO CAN: model cu bi tre 30 phut - du bao tai T khop nhat voi san luong that tai
T-30p, do la vi lag_1 mang san dap an va cay quyet dinh chep lai thay vi hoc quy luat.
Do tre PHAI do rieng khoi sai so bien do: du bao cao hay thap deu khong anh huong
chi so nay, no chi do LECH THOI DIEM.

LUU Y (yeu cau cua chu nhiem du an): KHONG dung RMSE/tuong quan tong hop lam bang
chung khi debug tre pha - phai do tren tung site x tung ngay, vi bug co the chi xay
ra o vai cho ma con so gop se che mat.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .columns import DAYLIGHT_COL, SITE_COL, TIMESTAMP_COL

SO_MAU_TOI_THIEU = 200   # duoi nguong nay thi he so hoi quy khong dang tin


def do_tre_phut(
    df: pd.DataFrame,
    cot_that: str,
    cot_du_bao: str,
    freq_minutes: int = 15,
) -> tuple[float, int]:
    """Do do tre theo DO DOC, tra ve (so_phut, so_diem_dung_de_do).

    Nguyen ly: neu du bao bi dich c buoc thi err ~ -c * doc, nen he so hoi quy cua
    err theo doc chinh la -c. Nhan freq_minutes de doi ra phut.
      duong = du bao di SAU thuc te (tre)
      am    = du bao di TRUOC thuc te (som)
    """
    x = df.sort_values([SITE_COL, TIMESTAMP_COL])
    g = x.groupby(SITE_COL, observed=True)[cot_that]
    doc = (g.shift(-1) - g.shift(1)) / 2
    err = x[cot_du_bao] - x[cot_that]

    m = doc.notna() & err.notna()
    if DAYLIGHT_COL in x.columns:
        m = m & x[DAYLIGHT_COL].fillna(False).astype(bool)

    a = doc[m].to_numpy(dtype=float)
    b = err[m].to_numpy(dtype=float)
    if a.size < SO_MAU_TOI_THIEU or (a**2).sum() == 0:
        return np.nan, 0
    return -float((a * b).sum() / (a * a).sum()) * freq_minutes, int(a.size)


def do_tre_theo_site(
    df: pd.DataFrame,
    cot_that: str,
    cot_du_bao: str,
    freq_minutes: int = 15,
) -> pd.DataFrame:
    """Do tre tach rieng TUNG SITE.

    Bat buoc phai co bang nay: 1 site tre nang cung la bug, con so tong the se che mat
    (vd tong the +0,0 phut nhung co site le +45 phut).
    """
    dong = []
    for site, nhom in df.groupby(SITE_COL, observed=True):
        tre, n = do_tre_phut(nhom, cot_that, cot_du_bao, freq_minutes)
        dong.append({SITE_COL: site, "tre_phut": tre, "so_diem": n})
    return pd.DataFrame(dong).sort_values("tre_phut", ascending=False)


def quet_do_tre(
    df: pd.DataFrame,
    cot_that: str,
    cot_du_bao: str,
    k_max: int = 3,
) -> dict[int, float]:
    """Voi moi do dich k, tinh sai so giua du_bao(T) va thuc_te(T - k buoc).

    k = 0 co sai so nho nhat nghia la KHONG tre. Neu k = 2 nho nhat thi du bao dang
    tre 2 buoc (30 phut) - dung tinh huong cua model cu.
    """
    v = df[df[DAYLIGHT_COL].fillna(False).astype(bool)].sort_values(
        [SITE_COL, TIMESTAMP_COL]
    )
    g = v.groupby(SITE_COL)[cot_that]
    ket = {}
    for k in range(0, k_max + 1):
        yt = g.shift(k)
        m = yt.notna()
        ket[k] = float(np.mean(np.abs(v[cot_du_bao][m] - yt[m])))
    return ket


def lech_dinh_moi_ngay(
    df: pd.DataFrame,
    cot_that: str,
    cot_du_bao: str,
) -> pd.DataFrame:
    """Lech thoi diem DINH cua tung (site, ngay) - do truc tiep, khong qua hoi quy.

    Day la bang chung "local" ma con so gop khong the che: moi dong la 1 site 1 ngay,
    xem duoc chinh xac ngay nao lech bao nhieu phut.
    """
    x = df.copy()
    x["_ngay"] = pd.to_datetime(x[TIMESTAMP_COL]).dt.date
    dong = []
    for (site, ngay), nhom in x.groupby([SITE_COL, "_ngay"], observed=True):
        if nhom[cot_that].isna().all() or nhom[cot_du_bao].isna().all():
            continue
        i_that = nhom[cot_that].idxmax()
        i_pred = nhom[cot_du_bao].idxmax()
        lech = (
            pd.to_datetime(nhom.loc[i_pred, TIMESTAMP_COL])
            - pd.to_datetime(nhom.loc[i_that, TIMESTAMP_COL])
        ).total_seconds() / 60.0
        dong.append({
            SITE_COL: site,
            "ngay": ngay,
            "gio_dinh_that": pd.to_datetime(nhom.loc[i_that, TIMESTAMP_COL]).time(),
            "gio_dinh_du_bao": pd.to_datetime(nhom.loc[i_pred, TIMESTAMP_COL]).time(),
            "dinh_that": float(nhom.loc[i_that, cot_that]),
            "dinh_du_bao": float(nhom.loc[i_pred, cot_du_bao]),
            "lech_phut": lech,
        })
    return pd.DataFrame(dong)
