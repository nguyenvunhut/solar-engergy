"""Nghiep vu 3 - bao tri CBM va AI anomaly GMM-IF.

Cong thuc — brief muc 4.2, hang muc 3:

    delta_e(t) = max(0, e_expected - e_hourly)  khi gmm_if_outlier_flag = TRUE
               = 0                              khi FALSE
    delta_revenue(t) = delta_e * P_FIT

"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..core import config as cfg


def tinh(h: pd.DataFrame, gia: dict | None = None) -> pd.DataFrame:
    g = gia or cfg.GIA_TB_3_NAM
    co = h["gmm_if_outlier_flag"].fillna(False).to_numpy(dtype=bool)
    thieu_hut = (h["e_expected"].fillna(0.0).to_numpy(dtype=float)
                 - h["e_hourly"].fillna(0.0).to_numpy(dtype=float))
    delta_e = np.where(co, np.maximum(0.0, thieu_hut), 0.0)
    return pd.DataFrame({
        "delta_kwh": delta_e,
        "delta_revenue_aud": delta_e * g["fit"],
    }, index=h.index)
