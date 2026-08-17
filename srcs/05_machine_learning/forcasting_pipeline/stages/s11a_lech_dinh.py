"""Stage 11a: cac phep do LECH DINH - copy nguyen si tu notebook 09_kiem_chung_tre_pha.

VI SAO DO LECH DINH CHU KHONG DUNG RMSE/tuong quan gop:
  Con so gop tren toan bo 42 site x 127 ngay co the dep trong khi MOT site le tre 45 phut -
  trung binh se che mat bug do. Nen moi phep o day deu do LOCAL: tung (site, ngay) mot,
  roi bao cao phan bo, khong gop lai thanh mot con so duy nhat.

QUY UOC DAU: lech_phut DUONG = du bao den SAU thuc te (tre / dich phai). AM = den som.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.columns import SITE_COL, TIMESTAMP_COL


def lech_dinh_moi_ngay(d: pd.DataFrame) -> pd.DataFrame:
    """Voi MOI (site, ngay), tim gio dinh cua thuc te va cua du bao, tra ve do lech phut.

    Chi xet dong BAN NGAY. Bo qua ngay co duoi 4 diem hoac thuc te toan 0 (dem/hong).
    """
    w = d[d["is_daylight"].fillna(False).astype(bool)].copy()
    w["ngay"] = w[TIMESTAMP_COL].dt.date
    dong = []
    for (s, ngay), g in w.groupby([SITE_COL, "ngay"]):
        if len(g) < 4 or g["thuc_te"].max() <= 0:
            continue
        t_thuc = g.loc[g["thuc_te"].idxmax(), TIMESTAMP_COL]
        t_du_bao = g.loc[g["du_bao"].idxmax(), TIMESTAMP_COL]
        dong.append({
            "site_id": s,
            "ngay": ngay,
            "gio_dinh_thuc_te": t_thuc.strftime("%H:%M"),
            "gio_dinh_du_bao": t_du_bao.strftime("%H:%M"),
            # vi tri trong gio nguon (0-59): dung de kiem gia thuyet "thoi tiet theo gio
            # lam dinh cuoi gio bi tre" - xem theo_vi_tri_trong_gio()
            "phut_trong_gio": int(t_thuc.minute),
            "lech_phut": (t_du_bao - t_thuc).total_seconds() / 60.0,
            "thuc_te_dinh": float(g["thuc_te"].max()),
            "du_bao_dinh": float(g["du_bao"].max()),
        })
    return pd.DataFrame(dong)


def theo_vi_tri_trong_gio(df_lech: pd.DataFrame) -> pd.DataFrame:
    """Lech dinh co lien quan toi VI TRI TRONG GIO ma dinh xay ra khong?

    Neu do gioi han thoi tiet theo gio: dinh cang xay ra GAN CUOI gio thi lech cang lon,
    vi model chua kip nhan thong tin cua gio moi. Khong thay xu huong nay thi lech KHONG
    phai do thoi tiet - phai tim bug o cho khac.
    """
    nhom = pd.cut(df_lech["phut_trong_gio"], bins=[-1, 14, 29, 44, 59],
                  labels=["0-14", "15-29", "30-44", "45-59"])
    bang = (
        df_lech.groupby(nhom, observed=True)["lech_phut"]
        .agg(so_ngay="count", lech_trung_vi="median")
        .reset_index()
    )
    bang.columns = ["phut_trong_gio_nhom", "so_ngay", "lech_trung_vi_phut"]
    return bang


def theo_site(df_lech: pd.DataFrame) -> pd.DataFrame:
    """Lech dinh gom theo tung site, site tre nang nhat len dau."""
    bang = (
        df_lech.groupby(SITE_COL)["lech_phut"]
        .agg(
            so_ngay="count",
            lech_trung_vi="median",
            lech_trung_binh="mean",
            so_ngay_dich_phai=lambda x: int((x > 0).sum()),
            ca_lech_nang_nhat="max",
        )
        .reset_index()
    )
    bang["ty_le_dich_phai_%"] = (
        bang["so_ngay_dich_phai"] / bang["so_ngay"] * 100
    ).round(1)
    return bang.sort_values("lech_trung_vi", ascending=False).reset_index(drop=True)


def theo_gio_dinh(df_lech: pd.DataFrame) -> pd.DataFrame:
    """Lech dinh gom theo KHUNG GIO ma dinh xay ra."""
    w = df_lech.copy()
    w["gio_dinh"] = pd.to_datetime(w["gio_dinh_thuc_te"], format="%H:%M").dt.hour
    bang = (
        w.groupby("gio_dinh")["lech_phut"]
        .agg(
            so_ngay="count",
            lech_trung_vi="median",
            lech_trung_binh="mean",
            so_ngay_dich_phai=lambda x: int((x > 0).sum()),
        )
        .reset_index()
    )
    bang["ty_le_dich_phai_%"] = (
        bang["so_ngay_dich_phai"] / bang["so_ngay"] * 100
    ).round(1)
    return bang


def _mae(x: pd.DataFrame) -> float:
    return float(np.mean(np.abs(x["du_bao"] - x["thuc_te"])))


def outlier_theo_site(df: pd.DataFrame) -> pd.DataFrame:
    """Sai so tai diem OUTLIER so voi diem binh thuong, theo tung site.

    tuong_quan_tai_outlier CAO nghia la model dang bam theo ca cac diem outlier - dau hieu
    xau, vi outlier la nhieu do/su co chu khong phai quy luat can hoc.
    """
    dong = []
    for s, d in df.groupby(SITE_COL):
        d_ol = d[d["la_outlier"]]
        d_nm = d[~d["la_outlier"]]
        if len(d_ol) == 0:
            continue
        du = (round(float(np.corrcoef(d_ol["du_bao"], d_ol["thuc_te"])[0, 1]), 5)
              if len(d_ol) > 2 and d_ol["thuc_te"].std() > 0 else np.nan)
        dong.append({
            "site_id": s,
            "so_outlier": len(d_ol),
            "ty_le_outlier_%": round(len(d_ol) / len(d) * 100, 3),
            "mae_tai_outlier": round(_mae(d_ol), 4),
            "mae_tai_binh_thuong": round(_mae(d_nm), 4) if len(d_nm) else np.nan,
            "tuong_quan_tai_outlier": du,
            "thuc_te_max_outlier": round(float(d_ol["thuc_te"].max()), 3),
            "du_bao_max_outlier": round(float(d_ol["du_bao"].max()), 3),
        })
    return (pd.DataFrame(dong)
            .sort_values("so_outlier", ascending=False)
            .reset_index(drop=True))
