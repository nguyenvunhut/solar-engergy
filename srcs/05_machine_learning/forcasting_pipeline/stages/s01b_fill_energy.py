"""Stage 01b: dien target cho cac slot moi chen bang cascade CAUSAL.

Tach tu muc 7 cua run_reindex_mask_outlier() trong 01_data_preprocessing.py.

NGUYEN TAC CAUSAL (quan trong nhat o day): moi gia tri dien vao chi duoc lay tu
QUA KHU cua chinh site do. Khong noi suy giua 2 diem, khong lay trung binh cua ca
chuoi, khong dung gia tri gio sau. Vi vay vong lap phai chay TUAN TU theo thoi gian
va tich luy dan `measured_vals`/`profile` - khong vector hoa duoc.

THU TU CASCADE (dung dau tien khop):
  1. gap >= 24h        -> machine_failure_zero  + loai khoi training
  2. ban dem           -> night_zero
  3. hom qua cung gio  -> causal_day_persistence
  4. tuan truoc cung gio -> causal_week_persistence
  5. trung vi profile  -> causal_profile_median
  6. het cach          -> fallback_zero

Cot `energy_source` ghi lai NGUON goc cua tung gia tri. Day la cot provenance duy nhat
cho target - metric headline chi tinh tren energy_source == 'measured'.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd

from core.columns import SITE_COL, TARGET_COL, TIMESTAMP_COL
from core.config import Cfg

# Ban dem theo phut trong ngay khi khong co cot weather_is_day (18:30 -> 05:30)
PHUT_TOI = 1110
PHUT_SANG = 330


def xac_dinh_ban_ngay(df: pd.DataFrame) -> pd.Series:
    """Uu tien weather_is_day (da ffill); khong co thi dung khung gio co dinh."""
    if "weather_is_day" in df.columns:
        return pd.to_numeric(df["weather_is_day"], errors="coerce").eq(1).fillna(False)
    phut = df[TIMESTAMP_COL].dt.hour * 60 + df[TIMESTAMP_COL].dt.minute
    return ~((phut >= PHUT_TOI) | (phut < PHUT_SANG))


def _dien_1_site(site_df: pd.DataFrame, cfg: Cfg) -> pd.DataFrame:
    """Chay cascade cho 1 site. Vong lap tuan tu de dam bao tinh causal."""
    freq = int(cfg.data["freq_minutes"])
    max_lag = int(cfg.data["max_lag_steps"])
    slot_gap_lon = int(cfg.data["major_gap_hours"] * 60 / freq)
    slot_1_ngay = int(24 * 60 / freq)          # 96 slot
    slot_1_tuan = slot_1_ngay * 7              # 672 slot

    out = site_df.sort_values(TIMESTAMP_COL).reset_index(drop=True).copy()
    chen = out["timestamp_was_inserted"].astype(bool)
    nhom_run = chen.ne(chen.shift(fill_value=False)).cumsum()
    do_dai_run = chen.groupby(nhom_run).transform("sum").where(chen, 0).astype(int)
    out["source_gap_id"] = out.get("source_gap_id", pd.Series(index=out.index, dtype=object))
    out["source_gap_id"] = out["source_gap_id"].astype("object")

    gia_tri_do = {}                 # {timestamp: gia tri do that}
    profile = defaultdict(list)     # {(quarter_hour, season): [cac gia tri]}
    ma_gap, dang_trong_gap = 0, False

    for i, dong in out.iterrows():
        ts = pd.Timestamp(dong[TIMESTAMP_COL])
        khoa = (int(dong["quarter_hour"]), str(dong["season_model"]))

        if not bool(dong["timestamp_was_inserted"]):
            # Dong goc: thu thap gia tri do that de dung cho cac slot SAU no
            if dong["energy_source"] == "measured" and pd.notna(dong[TARGET_COL]):
                v = float(dong[TARGET_COL])
                gia_tri_do[ts] = v
                profile[khoa].append(v)
            if dang_trong_gap:
                # Danh dau vung sau gap: lag/rolling o day van con "nhiem" gia tri dien
                het = min(i + max_lag, len(out))
                out.loc[i:het - 1, "after_source_gap_steps_remaining"] = np.maximum(
                    out.loc[i:het - 1, "after_source_gap_steps_remaining"].astype(int),
                    np.arange(max_lag, max_lag - (het - i), -1),
                )
                dang_trong_gap = False
            continue

        if not dang_trong_gap:
            ma_gap += 1
            dang_trong_gap = True
        out.at[i, "source_gap_id"] = ma_gap

        if int(do_dai_run.iloc[i]) >= slot_gap_lon:
            out.at[i, TARGET_COL] = 0.0
            out.at[i, "energy_source"] = "machine_failure_zero"
            out.at[i, "exclude_from_training"] = True
            out.at[i, "exclude_reason"] = "MACHINE_FAILURE_DATA_GAP"
            out.at[i, "training_quality_reason"] = (
                "SOURCE_GAP_MAJOR_OUTAGE+MACHINE_FAILURE_DATA_GAP"
            )
            continue

        if not bool(dong["is_daylight"]):
            out.at[i, TARGET_COL] = 0.0
            out.at[i, "energy_source"] = "night_zero"
            out.at[i, "training_quality_reason"] = "SOURCE_GAP_SHORT_IMPUTED"
            continue

        ts_hom_qua = ts - pd.Timedelta(minutes=freq * slot_1_ngay)
        ts_tuan_truoc = ts - pd.Timedelta(minutes=freq * slot_1_tuan)
        if ts_hom_qua in gia_tri_do:
            out.at[i, TARGET_COL] = gia_tri_do[ts_hom_qua]
            out.at[i, "energy_source"] = "causal_day_persistence"
        elif ts_tuan_truoc in gia_tri_do:
            out.at[i, TARGET_COL] = gia_tri_do[ts_tuan_truoc]
            out.at[i, "energy_source"] = "causal_week_persistence"
        elif profile.get(khoa):
            out.at[i, TARGET_COL] = float(np.median(profile[khoa]))
            out.at[i, "energy_source"] = "causal_profile_median"
        else:
            out.at[i, TARGET_COL] = 0.0
            out.at[i, "energy_source"] = "fallback_zero"
        out.at[i, "training_quality_reason"] = "SOURCE_GAP_SHORT_IMPUTED"

    return out


def dien_target(df: pd.DataFrame, cfg: Cfg) -> pd.DataFrame:
    """Ap cascade cho tung site roi gop lai."""
    out = df.copy()
    out["is_daylight"] = xac_dinh_ban_ngay(out)
    phan = [
        _dien_1_site(nhom, cfg)
        for _, nhom in out.groupby(SITE_COL, observed=True, sort=True)
    ]
    gop = pd.concat(phan, ignore_index=True)
    return gop.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)
