"""Dieu phoi kich ban what-if theo dung dac ta brief muc 1-3.

Tham so nghiep vu doc tu core/config.py. Doanh thu quy doi theo bieu gia cua
nam duoc chon (config.doanh_thu_theo_nam).

Tinh lai tuc thi khi tich/huy checkbox: E, PR, CF, cac thanh phan ton that,
doanh thu, CO2, CapEx, payback, ROI.
"""
from __future__ import annotations

import pandas as pd

from ..core import config as cfg

HANG_MUC = {ma: (v["ten"], None) for ma, v in cfg.HANG_MUC_CAI_TIEN.items()}


def chay_kich_ban(bat: list[str] | None = None, nam: int | None = None) -> dict:
    """bat: ma cac hang muc duoc tich. nam: 2020/2021/2022 hoac None = TB 3 nam."""
    tat_ca = list(cfg.HANG_MUC_CAI_TIEN)
    bat = tat_ca if bat is None else [m for m in bat if m in cfg.HANG_MUC_CAI_TIEN]
    gia = cfg.BIEU_GIA_NEM[nam] if nam in cfg.BIEU_GIA_NEM else cfg.GIA_TB_3_NAM

    cs = cfg.CO_SO
    e0 = float(cs["e_baseline_kwh"])

    chi_tiet, tong_kwh, tong_aud, tong_capex = [], 0.0, 0.0, 0.0
    for ma in tat_ca:
        v = cfg.HANG_MUC_CAI_TIEN[ma]
        on = ma in bat
        aud = cfg.doanh_thu_theo_nam(ma, nam)
        capex = v["capex_aud"]
        if on:
            tong_kwh += v["kwh"]
            tong_aud += aud
            tong_capex += capex or 0
        chi_tiet.append({
            "ma": ma, "stt": v["stt"], "ten": v["ten"], "bat": on,
            "hieu_suat": v["hieu_suat"],
            "delta_kwh": float(v["kwh"]),
            "delta_revenue_aud": aud,
            "capex_aud": capex,
            "payback": v["payback"],
            "roi_%": (aud / capex * 100.0) if capex else None,
            "ton_that": v["ton_that"],
            "ty_le_tang_%": v["kwh"] / e0 * 100.0,
        })

    # Ton that: hang muc duoc bat thi khu thanh phan ton that tuong ung
    khu = {c["ton_that"] for c in chi_tiet if c["bat"] and c["ton_that"]}
    ton_that = [{
        "ma": k, "ten": v["ten"],
        "truoc_%": v["ty_le"] * 100.0,
        "sau_%": (v["sau"] if k in khu else v["ty_le"]) * 100.0,
        "truoc_kwh": float(v["kwh"]),
        "sau_kwh": float(v["kwh"]) * (v["sau"] / v["ty_le"]) if k in khu else float(v["kwh"]),
        "ap_dung": k in khu,
    } for k, v in cfg.TON_THAT_CO_SO.items()]

    e1 = e0 + tong_kwh
    he_so = e1 / e0
    # PR cong don theo diem phan tram (xem PR_DIEM_HANG_MUC trong config), khong
    # nhan theo ty le san luong — nhan se cho PR vuot 100%.
    pr1 = cs["pr_baseline"] * 100.0 + sum(cfg.PR_DIEM_HANG_MUC[m] for m in bat)
    return {
        "co_so": {
            "e_kwh": e0,
            "pr_%": cs["pr_baseline"] * 100.0,
            "cf_%": cs["cf_baseline"] * 100.0,
            "revenue_aud": float(cs["revenue_baseline_aud"]),
            "co2_kg": float(cs["co2_baseline_kg"]),
            "cong_suat_kwp": cs["cong_suat_dc_kwp"],
            "so_tram": cs["so_tram"],
            "yield_kwh_kwp": cs["yield_kwh_kwp"],
        },
        "sau_cai_tien": {
            "e_kwh": e1,
            "pr_%": pr1,
            "cf_%": cs["cf_baseline"] * he_so * 100.0,
            "revenue_aud": cs["revenue_baseline_aud"] + tong_aud,
            "co2_kg": e1 * cs["co2_kg_moi_kwh"],
            "yield_kwh_kwp": e1 / cs["cong_suat_dc_kwp"],
        },
        "delta": {
            "e_kwh": tong_kwh,
            "ty_le_%": tong_kwh / e0 * 100.0,
            "revenue_aud": tong_aud,
            "co2_kg": tong_kwh * cs["co2_kg_moi_kwh"],
            "capex_aud": tong_capex,
            "payback_nam": (tong_capex / tong_aud) if tong_aud else None,
            "so_hang_muc": len(bat),
        },
        "hang_muc": chi_tiet,
        "ton_that": ton_that,
        "bieu_gia": gia,
        "nam": nam,
        "campus": [{"ten": k, **v} for k, v in cfg.CAMPUS.items()],
    }


def bang_hang_muc(kq: dict) -> pd.DataFrame:
    return pd.DataFrame(kq["hang_muc"])
