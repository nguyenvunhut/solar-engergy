"""Stage 03b: dac trung lag va rolling suy tu target - CHONG RO RI.

Tach tu buoc 6-7 cua run_features_time() trong 02_1_features_time.py.

BA QUY TAC CHONG RO RI, sai bat ky cai nao la model "nhin trom" dap an:
  1. Moi dac trung suy tu target deu phai shift() - khong duoc dung gia tri tai T.
  2. Rolling phai tinh tren target DA shift(1) - neu khong, rolling_mean tai T da
     bao gom chinh y(T) can du bao.
  3. Cua so vat qua cho dut gay thoi gian -> gan NaN (xem continuous_history_mask).

VE lag_1: da bi LOAI khoi cau hinh (features.yaml: lags = [4, 96]). lag_1 mang gia
tri T-15p, tuong quan 99% voi muc tieu, khien cay quyet dinh CHEP lai thay vi hoc
quy luat -> du bao tre 1 buoc. Audit doc lap 2026-07-31: 39/40 site vuot nguong.

BACKWARD CONTEXT: khi sinh dac trung cho tap val/test, phai noi them phan cuoi cua
tap truoc do vao DAU (context), tinh xong roi CHI xuat cac dong thuoc tap dich. Neu
khong, cac dong dau tap val se khong co du 96 buoc lich su -> mat oan du lieu.
Context chi di TU QUA KHU sang, nen khong phai ro ri.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.columns import SITE_COL, TARGET_COL, TIMESTAMP_COL
from core.config import Cfg
from stages.s03a_time_cyclical import add_time_features, continuous_history_mask


def add_lag_rolling_features(df: pd.DataFrame, cfg: Cfg) -> pd.DataFrame:
    """Tao lag va rolling an toan ve ro ri."""
    lags = list(cfg.features["lags"])
    cua_so = list(cfg.features["rolling_windows"])
    freq = int(cfg.data["freq_minutes"])

    out = df.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)
    nhom = out.groupby(SITE_COL, group_keys=False, observed=True)

    for lag in lags:
        cot = f"lag_{lag}"
        out[cot] = nhom[TARGET_COL].shift(lag)
        hop_le = nhom.apply(continuous_history_mask, so_buoc=lag, freq_minutes=freq)
        out.loc[~hop_le.to_numpy(), cot] = np.nan

    # shift(1) TRUOC khi rolling - day la dong quan trong nhat cua ca file
    target_da_shift = nhom[TARGET_COL].shift(1)

    for w in cua_so:
        hop_le = nhom.apply(
            continuous_history_mask, so_buoc=w, freq_minutes=freq
        ).to_numpy()
        r = target_da_shift.groupby(out[SITE_COL]).rolling(w, min_periods=w)
        for cot, gia_tri in (
            (f"rolling_mean_{w}", r.mean()),
            (f"rolling_std_{w}", r.std()),
            (f"rolling_min_{w}", r.min()),
            (f"rolling_max_{w}", r.max()),
        ):
            out[cot] = gia_tri.reset_index(level=0, drop=True)
            out.loc[~hop_le, cot] = np.nan

    cot_target = [c for c in out.columns if c.startswith(("lag_", "rolling_"))]
    out["has_complete_history_features"] = ~out[cot_target].isna().any(axis=1)
    return out


def build_features_with_backward_context(
    context_df: pd.DataFrame | None,
    target_df: pd.DataFrame,
    output_role: str,
    cfg: Cfg,
) -> pd.DataFrame:
    """Noi context vao dau target, tinh dac trung tren phan gop, CHI xuat dong target."""
    target = target_df.copy()
    target["_feature_export_row"] = True
    target["_feature_output_role"] = output_role

    khung = []
    if context_df is not None and len(context_df):
        ctx = context_df.copy()
        ctx["_feature_export_row"] = False
        ctx["_feature_output_role"] = "history_context"
        khung.append(ctx)
    khung.append(target)

    gop = pd.concat(khung, ignore_index=True, sort=False)
    gop[TIMESTAMP_COL] = pd.to_datetime(gop[TIMESTAMP_COL], errors="coerce")
    gop = gop.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)

    gop = add_time_features(gop)
    gop = add_lag_rolling_features(gop, cfg)

    xuat = gop[gop["_feature_export_row"].astype(bool)].drop(columns=["_feature_export_row"])
    return xuat.reset_index(drop=True)


def so_cot_se_tao(cfg: Cfg) -> int:
    return len(cfg.features["lags"]) + len(cfg.features["rolling_windows"]) * 4
