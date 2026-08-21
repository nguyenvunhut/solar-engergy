"""Stage 07b: cham diem dac trung bang Mutual Information + chon Top-K.

Tach tu buoc 5-8 cua run_select_features() trong 03_feature_selection.py.

VI SAO DUNG MUTUAL INFORMATION: no bat duoc quan he PHI TUYEN giua dac trung va target
(khac he so tuong quan Pearson chi bat quan he tuyen tinh). Buc xa - san luong la quan he
phi tuyen (bao hoa khi cham tran inverter) nen Pearson se danh gia thap oan.

NHOM BAO VE: mot so dac trung co diem MI thap nhung BAT BUOC phai giu vi ly do vat ly.
Vi du doy_sin/doy_cos: gio dinh thuc te dich toi ~1,75 tieng giua cac thang (thang 12 la
14:30, thang 4 la 12:45) - khong the giai thich bang rieng goc mat troi (chi lech ~16
phut ca nam theo phuong trinh thoi gian). MI xep hang thap nen bi Top-K cat, phai bao ve.
"""
from __future__ import annotations

import pandas as pd

from core.columns import SITE_COL, TIMESTAMP_COL

TOP_K = 35
CO_MAU_MI = 100_000
SEED = 42
# Tam dich nhan khi cham diem MI. Notebook 05 dung HORIZON_MI = 1 (15 phut).
HORIZON_MI = 1
BUOC_PHUT = 15

# Dac trung PHAI giu du diem MI thap - deu co ly do vat ly ro rang.
# Xem docs/2026_07_30_Khu_Tre_Pha_Du_Bao_15_Phut.md
BAO_VE = [
    # hinh hoc mat troi va buc xa troi quang
    "solar_elevation", "solar_azimuth", "azimuth_sin", "azimuth_cos",
    "sin_elevation", "ghi_cs", "cs_factor", "clearsky_proxy", "rad_x_sinelev",
    # quy mo va tran cong suat tram
    # (site_scale, con_cach_tran bi cam do cong tuyen cau truc - xem s07a)
    "tran_cong_suat", "ky_vong", "ty_le_bao_hoa",
    # buc xa da downscale - dau vao chinh
    "shortwave_radiation", "direct_normal_irradiance", "diffuse_solar_radiation",
    "temperature_c",
    # lich su 1 ngay, khong gay tre pha
    # rolling_min_96 DA BO khoi danh sach bao ve (2026-08-16): cua so 96 buoc = dung 24 gio
    # nen luon trum qua ban dem, ma ban dem san luong = 0 -> gia tri nho nhat luon bang 0.
    # Do lai tren tap train: cua so ngheo so 0 nhat trong ca 42 tram van chua 36 buoc bang 0,
    # tram nhieu nhat 41 buoc. Cot hang so: phuong sai 0, diem MI 0, s07a gan nhan CONSTANT.
    "lag_96", "rolling_mean_96", "rolling_max_96", "rolling_std_96",
    # mua vu - xem docstring dau file
    "doy_sin", "doy_cos",
]


def cham_diem_mi(df: pd.DataFrame, ung_vien: list[str], target: str) -> pd.DataFrame:
    """Tinh Mutual Information giua tung ung vien va NHAN TAI T+h, tren mau.

    SUA 2026-08-22: cham diem voi nhan tai T+h chu KHONG phai tai T. Day la bai toan
    du bao nen cau hoi dung la "dac trung nay cho biet gi ve san luong h buoc NUA",
    khong phai "ve san luong NGAY BAY GIO". Xep hang theo y(T) thien vi cac dac trung
    mo ta hien tai (rolling ngan, buc xa dang do) hon cac dac trung co suc tien doan.
    Notebook 05 da lam dung tu truoc (cell 9: y_muc_tieu qua merge moc_nhan); ban .py
    nay sot lai nen chon ra bo dac trung khac notebook o vi tri sat nguong Top-K.
    """
    from sklearn.feature_selection import mutual_info_regression

    # Dich nhan sang T+h bang phep TRA THEO MOC THOI GIAN (khong shift theo dong):
    # shift dem theo vi tri dong nen thung luoi mot moc la vo phai dong ke tiep.
    d = df.sort_values([SITE_COL, TIMESTAMP_COL]).copy()
    d["_moc_nhan"] = d[TIMESTAMP_COL] + pd.Timedelta(minutes=BUOC_PHUT * HORIZON_MI)
    _tra = d[[SITE_COL, TIMESTAMP_COL, target]].rename(
        columns={TIMESTAMP_COL: "_moc_nhan", target: "_y_muc_tieu"})
    d = d.merge(_tra, on=[SITE_COL, "_moc_nhan"], how="left")
    d = d.dropna(subset=["_y_muc_tieu"])

    # Loc theo dong DAT SAU khi da dich nhan - loc truoc se duc lo hong tren luoi.
    sach = (d[d["exclude_from_training"] == False]  # noqa: E712
            if "exclude_from_training" in d.columns else d)
    mau = sach.sample(n=min(CO_MAU_MI, len(sach)), random_state=SEED).copy()

    X = mau[ung_vien].copy()
    y = mau["_y_muc_tieu"].values
    # Cot chuoi (season, season_model...) phai ma hoa sang so truoc khi tinh MI
    for c in X.columns:
        if not pd.api.types.is_numeric_dtype(X[c]):
            X[c] = pd.factorize(X[c])[0]
    X = X.fillna(X.median())

    diem = mutual_info_regression(X.values, y, random_state=SEED)
    return (
        pd.DataFrame({"feature": ung_vien, "mi_score": diem})
        .sort_values("mi_score", ascending=False)
        .reset_index(drop=True)
    )


def gop_voi_chan_doan(df_diem: pd.DataFrame, df_diag: pd.DataFrame | None) -> pd.DataFrame:
    """Ghep diem MI voi bang chan doan cua stage s06 (vif, nan_pct...)."""
    if df_diag is None or df_diag.empty:
        return df_diem.copy()
    cot = [c for c in ("feature", "vif", "nan_pct", "flag", "duplicate_of")
           if c in df_diag.columns]
    return pd.merge(df_diem, df_diag[cot], on="feature", how="left")


def chon_top_k(df_gop: pd.DataFrame, top_k: int = TOP_K) -> tuple[pd.DataFrame, dict]:
    """Lay Top-K theo diem MI, roi BO SUNG lai nhom bao ve neu bi cat."""
    co_bao_ve = [c for c in BAO_VE if c in df_gop["feature"].values]
    thieu_bao_ve = [c for c in BAO_VE if c not in df_gop["feature"].values]

    chon = df_gop.head(top_k).copy()
    bi_cat = [c for c in co_bao_ve if c not in set(chon["feature"])]
    if bi_cat:
        chon = pd.concat(
            [chon, df_gop[df_gop["feature"].isin(bi_cat)]], ignore_index=True
        )

    return chon, {
        "top_k": top_k,
        "so_bao_ve_co_mat": len(co_bao_ve),
        "bao_ve_thieu_trong_du_lieu": thieu_bao_ve,
        "bao_ve_bi_top_k_cat_da_bu_lai": bi_cat,
        "so_dac_trung_cuoi": len(chon),
    }


def bao_cao_mi_cao_vif_cao(df_gop: pd.DataFrame, nguong_vif: float = 10.0) -> pd.DataFrame:
    """Dac trung vua co MI cao vua co VIF cao - can xem ky truoc khi giu.

    MI cao nghia la lien quan manh toi target; VIF cao nghia la suy ra duoc tu dac trung
    khac. Ca hai cung cao thuong la dau hieu cot do trung thong tin voi cot khac.
    """
    if "vif" not in df_gop.columns:
        return pd.DataFrame()
    m = df_gop["vif"].notna() & (df_gop["vif"] > nguong_vif)
    return df_gop.loc[m, ["feature", "mi_score", "vif"]].sort_values(
        "mi_score", ascending=False
    )
