"""Nghiep vu 1 - BESS 5 campus va thu hoi inverter clipping.

Cong thuc — brief muc 4.2, hang muc 1:

    P_AC_max(t)        = p_stc / ILR                        ILR = 1,25
    delta_clip(t)      = max(0, e_stc_hourly * pr_adjusted - 0,80 * p_stc * 1h)
    delta_thu_hoi(t)   = delta_clip * ETA_RTE               ETA_RTE = 0,88
    delta_revenue(t)   = delta_thu_hoi * (P_Peak - P_FIT)   khi hourly_bucket in [17,21]
                       = delta_thu_hoi * P_FIT              khung gio khac

Dong co p_stc <= 0 duoc bo qua vi P_AC_max khong xac dinh.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..core import config as cfg


def tinh(h: pd.DataFrame, gia: dict | None = None) -> pd.DataFrame:
    """Tra ve DataFrame cung chi so voi `h`, them 3 cot delta_*.

    gia: dict bieu gia mot nam (khoa 'fit', 'tou_peak'). De None thi dung TB 3 nam.
    """
    g = gia or cfg.GIA_TB_3_NAM
    p_stc = h["p_stc"].fillna(0.0).to_numpy(dtype=float)
    hop_le = p_stc > 0

    tiem_nang = (h["e_stc_hourly"].fillna(0.0).to_numpy(dtype=float)
                 * h["pr_adjusted"].fillna(0.0).to_numpy(dtype=float))
    tran_ac = (1.0 / cfg.ILR) * p_stc          # = 0,80 * p_stc voi ILR = 1,25

    delta_clip = np.where(hop_le, np.maximum(0.0, tiem_nang - tran_ac), 0.0)
    delta_thu_hoi = delta_clip * cfg.ETA_RTE

    lo, hi = cfg.GIO_CAO_DIEM
    trong_khung = h["hourly_bucket"].between(lo, hi).to_numpy()
    don_gia = np.where(trong_khung, g["tou_peak"] - g["fit"], g["fit"])

    return pd.DataFrame({
        "delta_clip_kwh": delta_clip,
        "delta_kwh": delta_thu_hoi,
        "delta_revenue_aud": delta_thu_hoi * don_gia,
    }, index=h.index)
