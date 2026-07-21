"""V2 quality preprocessing for ``ml_mart.base`` exports.

Input mặc định:
    data/mlmart_base/v2_preprocessing.parquet

Output mặc định:
    data/preprocessing/v2_quality_checked.parquet

Thiết kế:
    - Không sửa dữ liệu gốc.
    - Không drop outlier; chỉ tạo cờ để training/evaluation quyết định.
    - Không fit bất kỳ statistic nào có nguy cơ leakage.
    - Xử lý các vấn đề đã audit từ EDA: weather missing, metadata missing,
      hour=-1, duplicate key, time gap.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "mlmart_base" / "v2_preprocessing.parquet"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "preprocessing" / "v2_quality_checked.parquet"

SITE_COL = "site_id"
TIMESTAMP_COL = "timestamp"
TARGET_COL = "energy_generated_kwh"
OUTLIER_COL = "gmm_if_outlier_flag"
OUTLIER_REASON_COL = "gmm_if_outlier_reason"

WEATHER_CORE_COLS: tuple[str, ...] = (
    "shortwave_radiation",
    "direct_normal_irradiance",
    "diffuse_solar_radiation",
    "temperature_c",
    "cloud_cover_total",
    "wind_speed",
    "precipitation_mm",
    "sunshine_duration",
)

KEY_COLS: tuple[str, ...] = (SITE_COL, TIMESTAMP_COL, "is_dst_repeat")


@dataclass(frozen=True)
class QualityConfig:
    """Configuration for v2 quality preprocessing."""

    input_path: Path = DEFAULT_INPUT
    output_path: Path = DEFAULT_OUTPUT
    expected_freq_minutes: int = 15
    drop_duplicate_keys: bool = False
    drop_missing_target: bool = True
    drop_missing_weather: bool = False


def _require_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")


def load_v2_base(path: str | Path = DEFAULT_INPUT) -> pd.DataFrame:
    """Load v2 mlmart parquet and normalize timestamp sort order."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input parquet not found: {path}")

    df = pd.read_parquet(path)
    _require_columns(df, [SITE_COL, TIMESTAMP_COL, TARGET_COL])
    df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL], errors="coerce")
    df = df.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)
    return df


def add_quality_flags(
    df: pd.DataFrame,
    *,
    expected_freq_minutes: int = 15,
) -> pd.DataFrame:
    """Add non-destructive quality/audit flags.

    Important columns added:
        - ``v2_duplicate_key_flag``
        - ``v2_missing_weather_flag``
        - ``v2_missing_capacity_kw_flag``
        - ``v2_missing_number_of_panels_flag``
        - ``v2_exclude_from_loss_flag``
        - ``v2_gap_from_prev_minutes``
        - ``v2_gap_after_prev_flag``
        - ``v2_hour_bucket_raw``
        - ``v2_hour_bucket_model``
        - ``v2_timestamp_hour``
        - ``v2_minute_of_day``
    """

    out = df.copy()
    _require_columns(out, [SITE_COL, TIMESTAMP_COL, TARGET_COL])

    out[TIMESTAMP_COL] = pd.to_datetime(out[TIMESTAMP_COL], errors="coerce")
    out = out.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)

    existing_key_cols = [col for col in KEY_COLS if col in out.columns]
    out["v2_duplicate_key_flag"] = out.duplicated(existing_key_cols, keep=False)

    if "weather_join_method" in out.columns:
        missing_join = out["weather_join_method"].astype("string").eq("missing_weather")
    else:
        missing_join = pd.Series(False, index=out.index)

    existing_weather_cols = [col for col in WEATHER_CORE_COLS if col in out.columns]
    if existing_weather_cols:
        missing_weather_values = out[existing_weather_cols].isna().any(axis=1)
    else:
        missing_weather_values = pd.Series(False, index=out.index)

    if "weather_id" in out.columns:
        missing_weather_id = out["weather_id"].isna()
    else:
        missing_weather_id = pd.Series(False, index=out.index)

    out["v2_missing_weather_flag"] = (
        missing_join | missing_weather_values | missing_weather_id
    ).astype(bool)

    out["v2_missing_target_flag"] = out[TARGET_COL].isna()

    out["v2_missing_capacity_kw_flag"] = (
        out["capacity_kw"].isna() if "capacity_kw" in out.columns else False
    )
    out["v2_missing_number_of_panels_flag"] = (
        out["number_of_panels"].isna() if "number_of_panels" in out.columns else False
    )

    if OUTLIER_COL in out.columns:
        out["v2_outlier_flag"] = out[OUTLIER_COL].fillna(False).astype(bool)
    else:
        out["v2_outlier_flag"] = False

    out["v2_exclude_from_loss_flag"] = (
        out["v2_outlier_flag"]
        | out["v2_missing_weather_flag"]
        | out["v2_missing_target_flag"]
    ).astype(bool)

    prev_ts = out.groupby(SITE_COL, observed=True)[TIMESTAMP_COL].shift(1)
    out["v2_gap_from_prev_minutes"] = (
        (out[TIMESTAMP_COL] - prev_ts).dt.total_seconds() / 60.0
    )
    out["v2_gap_after_prev_flag"] = (
        out["v2_gap_from_prev_minutes"].notna()
        & (out["v2_gap_from_prev_minutes"] != expected_freq_minutes)
    )

    if "hour" in out.columns:
        out["v2_hour_bucket_raw"] = pd.to_numeric(out["hour"], errors="coerce")
        out["v2_hour_bucket_model"] = out["v2_hour_bucket_raw"].replace(-1, 23)
    else:
        out["v2_hour_bucket_raw"] = np.nan
        out["v2_hour_bucket_model"] = np.nan

    ts = out[TIMESTAMP_COL]
    out["v2_timestamp_hour"] = ts.dt.hour
    out["v2_timestamp_minute"] = ts.dt.minute
    out["v2_minute_of_day"] = out["v2_timestamp_hour"] * 60 + out["v2_timestamp_minute"]
    out["v2_month"] = ts.dt.month
    out["v2_day_of_year"] = ts.dt.dayofyear
    out["v2_year"] = ts.dt.year

    return out


def apply_quality_filters(
    df: pd.DataFrame,
    *,
    drop_duplicate_keys: bool = False,
    drop_missing_target: bool = True,
    drop_missing_weather: bool = False,
) -> pd.DataFrame:
    """Apply only explicit row filters.

    Defaults are conservative:
        - drop missing target because supervised training cannot use it;
        - keep missing weather rows and outliers with flags for audit.
    """

    out = df.copy()

    if drop_duplicate_keys and "v2_duplicate_key_flag" in out.columns:
        existing_key_cols = [col for col in KEY_COLS if col in out.columns]
        out = out.drop_duplicates(existing_key_cols, keep="first")

    if drop_missing_target and "v2_missing_target_flag" in out.columns:
        out = out[~out["v2_missing_target_flag"]]

    if drop_missing_weather and "v2_missing_weather_flag" in out.columns:
        out = out[~out["v2_missing_weather_flag"]]

    return out.reset_index(drop=True)


def quality_summary(df: pd.DataFrame) -> dict[str, int | float | str]:
    """Return key audit counters for logs/notebooks."""

    summary: dict[str, int | float | str] = {
        "rows": int(len(df)),
        "sites": int(df[SITE_COL].nunique()) if SITE_COL in df.columns else 0,
        "min_timestamp": str(df[TIMESTAMP_COL].min()) if TIMESTAMP_COL in df.columns else "",
        "max_timestamp": str(df[TIMESTAMP_COL].max()) if TIMESTAMP_COL in df.columns else "",
    }

    for col in (
        "v2_duplicate_key_flag",
        "v2_missing_weather_flag",
        "v2_missing_target_flag",
        "v2_missing_capacity_kw_flag",
        "v2_missing_number_of_panels_flag",
        "v2_outlier_flag",
        "v2_exclude_from_loss_flag",
        "v2_gap_after_prev_flag",
    ):
        if col in df.columns:
            summary[col] = int(df[col].fillna(False).sum())

    if "v2_gap_from_prev_minutes" in df.columns:
        max_gap = df["v2_gap_from_prev_minutes"].max()
        summary["v2_max_gap_minutes"] = float(max_gap) if pd.notna(max_gap) else 0.0

    return summary


def run_quality_preprocessing(config: QualityConfig) -> pd.DataFrame:
    """Load, flag, filter, write parquet, and return processed dataframe."""

    df = load_v2_base(config.input_path)
    df = add_quality_flags(df, expected_freq_minutes=config.expected_freq_minutes)
    df = apply_quality_filters(
        df,
        drop_duplicate_keys=config.drop_duplicate_keys,
        drop_missing_target=config.drop_missing_target,
        drop_missing_weather=config.drop_missing_weather,
    )

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(config.output_path, index=False)

    print("V2 quality preprocessing completed")
    print(f"input : {config.input_path}")
    print(f"output: {config.output_path}")
    for key, value in quality_summary(df).items():
        print(f"{key}: {value}")

    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v2 quality preprocessing.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expected-freq-minutes", type=int, default=15)
    parser.add_argument("--drop-duplicate-keys", action="store_true")
    parser.add_argument("--keep-missing-target", action="store_true")
    parser.add_argument("--drop-missing-weather", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = QualityConfig(
        input_path=args.input,
        output_path=args.output,
        expected_freq_minutes=args.expected_freq_minutes,
        drop_duplicate_keys=args.drop_duplicate_keys,
        drop_missing_target=not args.keep_missing_target,
        drop_missing_weather=args.drop_missing_weather,
    )
    run_quality_preprocessing(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
