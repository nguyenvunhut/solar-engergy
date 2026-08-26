"""Phan ra ket qua tung hang muc theo campus, theo thang va theo mua.

Ty trong thang lay tu du lieu thuc te cua mv_bi_mart_hourly_measures; ty trong
campus lay theo cong suat kWp trong brief muc 2 (materialized view khong co cot
campus, chi co site_id/geo_id).
"""
from __future__ import annotations

import pandas as pd

from ..core import config as cfg
from ..repositories import bimart_repo as repo

# Nam Ban cau — mua he thang 12-2, mua dong thang 6-8
MUA = {12: "Hè", 1: "Hè", 2: "Hè", 3: "Thu", 4: "Thu", 5: "Thu",
       6: "Đông", 7: "Đông", 8: "Đông", 9: "Xuân", 10: "Xuân", 11: "Xuân"}
TEN_THANG = ["Th1", "Th2", "Th3", "Th4", "Th5", "Th6",
             "Th7", "Th8", "Th9", "Th10", "Th11", "Th12"]


def _ho_so_thang() -> pd.DataFrame:
    """San luong va buc xa trung binh theo thang, tu du lieu that."""
    h = repo.doc_hourly()
    d = h.assign(thang=h["date_id"] // 100 % 100)
    g = (d.groupby("thang")
           .agg(kwh=("e_hourly", "sum"), buc_xa=("shortwave_radiation", "mean"))
           .reindex(range(1, 13)).fillna(0.0).reset_index())
    g["ty_trong"] = g["kwh"] / g["kwh"].sum()
    g["ten"] = [TEN_THANG[i - 1] for i in g["thang"]]
    g["mua"] = g["thang"].map(MUA)
    return g


def ho_so_campus() -> pd.DataFrame:
    """San luong that cua tung khuon vien, gop tu 42 tram theo anh xa campus."""
    h = repo.doc_hourly()
    d = h.assign(campus=h["site_id"].map(cfg.SITE_TOI_CAMPUS))
    g = (d.groupby("campus")
           .agg(so_tram=("site_id", "nunique"), kwh_that=("e_hourly", "sum"))
           .reset_index())
    g["ty_trong"] = g["kwh_that"] / g["kwh_that"].sum()
    return g.sort_values("kwh_that", ascending=False).reset_index(drop=True)


def theo_campus(ma: str) -> pd.DataFrame:
    """Phan bo san luong thu hoi cho 5 khuon vien theo TY TRONG SAN LUONG THAT.

    Khong dung ty trong kWp vi cot p_stc chi co gia tri o mot phan cac tram.
    """
    g = ho_so_campus()
    kwh = cfg.HANG_MUC_CAI_TIEN[ma]["kwh"]
    aud = cfg.HANG_MUC_CAI_TIEN[ma]["aud"]
    g["kwh"] = kwh * g["ty_trong"]
    g["aud"] = aud * g["ty_trong"]
    return g


def theo_thang(ma: str) -> pd.DataFrame:
    """Phan bo san luong thu hoi theo 12 thang, kem buc xa trung binh."""
    g = _ho_so_thang()
    kwh = cfg.HANG_MUC_CAI_TIEN[ma]["kwh"]
    g["thu_hoi_kwh"] = kwh * g["ty_trong"]
    return g[["thang", "ten", "mua", "buc_xa", "kwh", "ty_trong", "thu_hoi_kwh"]]


def tilt_theo_mua() -> pd.DataFrame:
    """Hang muc 4: mua dong tang, mua he giam nhe — brief muc 3 hang muc 4."""
    return pd.DataFrame([
        {"mua": "Mùa đông (T6–T8)", "kwh": 44_436, "ghi_chu": "Góc 15° đón nắng thấp"},
        {"mua": "Mùa hè (T12–T2)", "kwh": -8_924, "ghi_chu": "Giảm nhẹ do nắng đứng"},
        {"mua": "Tự rửa trôi bùn", "kwh": 18_500, "ghi_chu": "Dốc thoát nước viền đáy"},
    ])


def clip_ton_that_thang() -> pd.DataFrame:
    """Ton that cat ngon quy ve kWh theo thang (khong phai ty le)."""
    g = _ho_so_thang()
    g["ton_that_kwh"] = cfg.E_CLIP_NAM * g["ty_trong"]
    g["thu_hoi_kwh"] = g["ton_that_kwh"] * cfg.ETA_RTE
    g["con_lai_kwh"] = g["ton_that_kwh"] - g["thu_hoi_kwh"]
    return g[["thang", "ten", "buc_xa", "ton_that_kwh", "thu_hoi_kwh", "con_lai_kwh"]]


# ══════════════════════════════════════════════════════════════════════════════
#  Phan ra rieng cho tung co che — tinh tren du lieu that
# ══════════════════════════════════════════════════════════════════════════════

def outlier_theo_ma_loi() -> pd.DataFrame:
    """Hang muc 3 — di thuong van hanh: dem va san luong hut theo tung ma nguyen nhan.

    Mot dong co the mang nhieu ma (STRING_AGG noi bang dau '+' va '; '), nen tach
    ra dem theo tung ma rieng.
    """
    h = repo.doc_hourly()
    d = h[h["gmm_if_outlier_flag"].fillna(False)].copy()
    d["hut_kwh"] = (d["e_expected"].fillna(0.0) - d["e_hourly"].fillna(0.0)).clip(lower=0.0)

    ban_ghi = []
    for ly_do, hut in zip(d["gmm_if_outlier_reason"].fillna("KHONG_RO"), d["hut_kwh"]):
        ma_list = {m.strip() for phan in str(ly_do).split(";") for m in phan.split("+") if m.strip()}
        for m in ma_list:
            ban_ghi.append({"ma_loi": m, "so_dong": 1, "hut_kwh": hut / len(ma_list)})

    g = (pd.DataFrame(ban_ghi).groupby("ma_loi", as_index=False)
           .agg(so_dong=("so_dong", "sum"), hut_kwh=("hut_kwh", "sum"))
           .sort_values("hut_kwh", ascending=False).reset_index(drop=True))
    g["ty_trong"] = g["hut_kwh"] / g["hut_kwh"].sum() if g["hut_kwh"].sum() else 0.0
    return g


def outlier_theo_thang() -> pd.DataFrame:
    """Hang muc 3 — so dong bi gan co va san luong hut, theo 12 thang."""
    h = repo.doc_hourly()
    d = h.assign(thang=h["date_id"] // 100 % 100)
    d["co"] = d["gmm_if_outlier_flag"].fillna(False)
    d["hut_kwh"] = (d["e_expected"].fillna(0.0) - d["e_hourly"].fillna(0.0)).clip(lower=0.0) * d["co"]
    g = (d.groupby("thang").agg(so_co=("co", "sum"), hut_kwh=("hut_kwh", "sum"))
           .reindex(range(1, 13)).fillna(0.0).reset_index())
    g["ten"] = [TEN_THANG[i - 1] for i in g["thang"]]
    return g


def nhiet_cell_theo_thang() -> pd.DataFrame:
    """Hang muc 2 — chenh lech nhiet do cell giua ap mai va thong gio, theo thang."""
    import numpy as np
    h = repo.doc_hourly()
    d = h.assign(thang=h["date_id"] // 100 % 100)
    t, bx, gio = d["temperature_c"], d["shortwave_radiation"], d["wind_speed"]
    flush = t + bx * np.exp(cfg.SAPM_FLUSH["a"] + cfg.SAPM_FLUSH["b"] * gio) + bx / 1000 * cfg.SAPM_DELTA_T
    mo = t + bx * np.exp(cfg.SAPM_OPEN["a"] + cfg.SAPM_OPEN["b"] * gio) + bx / 1000 * cfg.SAPM_DELTA_T
    d["t_flush"], d["t_open"] = flush, mo
    d["delta_t"] = (flush - mo).clip(lower=0.0)
    ban_ngay = d[d["shortwave_radiation"] > 50]
    g = (ban_ngay.groupby("thang")
           .agg(t_flush=("t_flush", "mean"), t_open=("t_open", "mean"), delta_t=("delta_t", "mean"))
           .reindex(range(1, 13)).fillna(0.0).reset_index())
    g["ten"] = [TEN_THANG[i - 1] for i in g["thang"]]
    return g


def gio_derating_theo_thang() -> pd.DataFrame:
    """Hang muc 5 — so gio inverter co nguy co giam tai: nhiet >= 35C va buc xa >= 800."""
    h = repo.doc_hourly()
    d = h.assign(thang=h["date_id"] // 100 % 100)
    d["nong"] = (d["temperature_c"] >= 35) & (d["shortwave_radiation"] >= 800)
    d["cham_nguong"] = (d["temperature_c"] >= 30) & (d["shortwave_radiation"] >= 700)
    g = (d.groupby("thang").agg(gio_derating=("nong", "sum"), gio_canh_bao=("cham_nguong", "sum"))
           .reindex(range(1, 13)).fillna(0).reset_index())
    g["ten"] = [TEN_THANG[i - 1] for i in g["thang"]]
    return g


def chuoi_kho_theo_thang() -> pd.DataFrame:
    """Hang muc 6 — luong mua va so ngay kho theo thang (nguong 5 mm/ngay)."""
    d = repo.doc_daily().copy()
    d["thang"] = d["date_id"] // 100 % 100
    d["ngay_kho"] = d["daily_precipitation"].fillna(0.0) < 5.0
    g = (d.groupby("thang").agg(mua_mm=("daily_precipitation", "mean"),
                                ty_le_ngay_kho=("ngay_kho", "mean"))
           .reindex(range(1, 13)).fillna(0.0).reset_index())
    g["ten"] = [TEN_THANG[i - 1] for i in g["thang"]]
    g["ty_le_ngay_kho"] *= 100.0
    return g


def loi_ich_nhiet_topcon() -> pd.DataFrame:
    """Hang muc 7 — loi ich he so nhiet TOPCon theo dai nhiet do cell."""
    import numpy as np
    h = repo.doc_hourly()
    d = h[h["shortwave_radiation"] > 50].copy()
    d["dai"] = pd.cut(d["t_cell"], [-10, 25, 35, 45, 55, 100],
                      labels=["≤25°C", "25–35°C", "35–45°C", "45–55°C", ">55°C"])
    d["loi_ich"] = 0.0008 * np.maximum(0.0, d["t_cell"] - 25) * d["e_hourly"].fillna(0.0)
    g = (d.groupby("dai", observed=True)
           .agg(so_gio=("t_cell", "size"), kwh=("e_hourly", "sum"), loi_ich_kwh=("loi_ich", "sum"))
           .reset_index())
    return g
