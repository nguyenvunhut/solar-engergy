"""Nghiep vu 2 - khoang ho thong gio mai 10-15 cm, ha nhiet do cell.

Cong thuc — brief muc 4.2, hang muc 2:

    T_flush(t) = temperature_c + shortwave * exp(a_f + b_f * wind_speed)
                 + shortwave/1000 * 3,0            a_f = -2,98  b_f = -0,0471
    T_open(t)  = temperature_c + shortwave * exp(a_o + b_o * wind_speed)
                 + shortwave/1000 * 3,0            a_o = -3,56  b_o = -0,0750

    delta_T(t)         = max(0, T_flush - T_open)
    delta_loss_temp(t) = HE_SO_NHIET * delta_T
    delta_e(t)         = e_hourly * delta_loss_temp / (1 - loss_temp)
    delta_revenue(t)   = delta_e * P_FIT

He so nhiet mac dinh 0,0038 theo brief; doi duoc bang tham so `he_so_nhiet`.

CHAN: chi tinh o dong co loss_temp khong rong va < 1 (mau so khac 0).
      Do duoc 307.927/683.665 dong (45,0%) co loss_temp.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..core import config as cfg


def _t_cell_sapm(temp: np.ndarray, buc_xa: np.ndarray, gio: np.ndarray,
                 he_so: dict) -> np.ndarray:
    return (temp + buc_xa * np.exp(he_so["a"] + he_so["b"] * gio)
            + buc_xa / 1000.0 * cfg.SAPM_DELTA_T)


def tinh(h: pd.DataFrame, gia: dict | None = None,
         he_so_nhiet: float | None = None) -> pd.DataFrame:
    g = gia or cfg.GIA_TB_3_NAM
    k_nhiet = cfg.HE_SO_NHIET_BRIEF if he_so_nhiet is None else float(he_so_nhiet)

    temp = h["temperature_c"].to_numpy(dtype=float)
    buc_xa = h["shortwave_radiation"].to_numpy(dtype=float)
    gio = h["wind_speed"].to_numpy(dtype=float)
    loss = h["loss_temp"].to_numpy(dtype=float)
    e = h["e_hourly"].fillna(0.0).to_numpy(dtype=float)

    t_flush = _t_cell_sapm(temp, buc_xa, gio, cfg.SAPM_FLUSH)
    t_open = _t_cell_sapm(temp, buc_xa, gio, cfg.SAPM_OPEN)
    delta_t = np.maximum(0.0, t_flush - t_open)
    delta_loss = k_nhiet * delta_t

    hop_le = np.isfinite(loss) & (loss < 1.0) & np.isfinite(delta_t)
    delta_e = np.where(hop_le, e * delta_loss / np.where(hop_le, 1.0 - loss, 1.0), 0.0)

    return pd.DataFrame({
        "delta_t_cell": np.where(hop_le, delta_t, 0.0),
        "delta_kwh": delta_e,
        "delta_revenue_aud": delta_e * g["fit"],
    }, index=h.index)
