"""V2 feature engineering for solar forecasting.

Input mặc định:
    data/preprocessing/v2_quality_checked.parquet

Output mặc định:
    data/features/v2_features.parquet

Nguyên tắc:
    - Feature thời gian dùng timestamp thật, không dùng raw ``hour=-1`` trực tiếp.
    - Lag/rolling luôn dùng ``shift(1)`` để tránh target leakage.
    - Lag/rolling được mask nếu cửa sổ lịch sử không liên tục theo 15 phút.
    - Encoder categorical fit trên dataset hiện tại ở bước FE. Khi làm train
      pipeline production, encoder phải fit trên train rồi transform val/test.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "preprocessing" / "v2_quality_checked.parquet"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "features" / "v2_features.parquet"

SITE_COL = "site_id"
TIMESTAMP_COL = "timestamp"
TARGET_COL = "energy_generated_kwh"

SOUTHERN_SEASON_MAP: dict[int, str] = {
    12: "summer",
    1: "summer",
    2: "summer",
    3: "autumn",
    4: "autumn",
    5: "autumn",
    6: "winter",
    7: "winter",
    8: "winter",
    9: "spring",
    10: "spring",
    11: "spring",
}

SEASON_CODE_MAP: dict[str, int] = {
    "summer": 0,
    "autumn": 1,
    "winter": 2,
    "spring": 3,
}

DEFAULT_LAGS: tuple[int, ...] = (1, 4, 96)
DEFAULT_ROLLING_WINDOWS: tuple[int, ...] = (4, 12)


@dataclass(frozen=True)
class FeatureConfig:
    """Configuration for v2 feature engineering."""

    input_path: Path = DEFAULT_INPUT
    output_path: Path = DEFAULT_OUTPUT
    expected_freq_minutes: int = 15
    lags: tuple[int, ...] = DEFAULT_LAGS
    rolling_windows: tuple[int, ...] = DEFAULT_ROLLING_WINDOWS


def _require_columns(df: pd.DataFrame, columns: list[str] | tuple[str, ...]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")


def load_quality_checked(path: str | Path = DEFAULT_INPUT) -> pd.DataFrame:
    """Load quality-checked parquet."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input parquet not found: {path}")
    df = pd.read_parquet(path)
    _require_columns(df, [SITE_COL, TIMESTAMP_COL, TARGET_COL])
    df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL], errors="coerce")
    return df.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add timestamp-based cyclic/calendar features."""

    out = df.copy()
    ts = pd.to_datetime(out[TIMESTAMP_COL], errors="coerce")

    minute_of_day = ts.dt.hour * 60 + ts.dt.minute
    day_of_year = ts.dt.dayofyear

    out["v2_minute_of_day"] = minute_of_day
    out["v2_hour_sin"] = np.sin(2 * np.pi * minute_of_day / 1440.0)
    out["v2_hour_cos"] = np.cos(2 * np.pi * minute_of_day / 1440.0)
    out["v2_doy_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    out["v2_doy_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)
    out["v2_month"] = ts.dt.month
    out["v2_day_of_week"] = ts.dt.dayofweek
    out["v2_is_weekend"] = out["v2_day_of_week"].isin([5, 6]).astype("int8")
    out["v2_season"] = out["v2_month"].map(SOUTHERN_SEASON_MAP).astype("string")
    out["v2_season_code"] = out["v2_season"].map(SEASON_CODE_MAP).astype("Int64")

    if "hour" in out.columns:
        out["v2_hour_bucket_raw"] = pd.to_numeric(out["hour"], errors="coerce")
        out["v2_hour_bucket_model"] = out["v2_hour_bucket_raw"].replace(-1, 23)

    return out


def add_metadata_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add safe metadata features and missing flags."""

    out = df.copy()

    for col in ("capacity_kw", "number_of_panels"):
        if col in out.columns:
            out[f"v2_{col}_missing_flag"] = out[col].isna().astype("int8")

    if {"capacity_kw", "number_of_panels"}.issubset(out.columns):
        out["v2_capacity_per_panel"] = out["capacity_kw"] / out["number_of_panels"]
        out.loc[~np.isfinite(out["v2_capacity_per_panel"]), "v2_capacity_per_panel"] = np.nan

    for col in ("site_id", "campus_name", "location_name", "site_metric"):
        if col in out.columns:
            codes = out[col].astype("string").fillna("__missing__").astype("category").cat.codes
            out[f"v2_{col}_code"] = codes.astype("int32")

    return out


def add_weather_domain_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add domain interaction features without using target future values."""

    out = df.copy()

    if {"shortwave_radiation", "temperature_c"}.issubset(out.columns):
        out["v2_temp_x_shortwave"] = out["temperature_c"] * out["shortwave_radiation"]

    if {"shortwave_radiation", "diffuse_solar_radiation"}.issubset(out.columns):
        denom = out["shortwave_radiation"].replace(0, np.nan)
        out["v2_diffuse_ratio"] = out["diffuse_solar_radiation"] / denom
        out["v2_diffuse_ratio"] = out["v2_diffuse_ratio"].clip(lower=0, upper=10)

    if {"direct_normal_irradiance", "shortwave_radiation"}.issubset(out.columns):
        denom = out["shortwave_radiation"].replace(0, np.nan)
        out["v2_dni_ratio"] = out["direct_normal_irradiance"] / denom
        out["v2_dni_ratio"] = out["v2_dni_ratio"].clip(lower=0, upper=10)

    if {"cloud_cover_total", "shortwave_radiation"}.issubset(out.columns):
        out["v2_cloud_x_shortwave"] = out["cloud_cover_total"] * out["shortwave_radiation"]

    return out


def _continuous_history_mask(
    group: pd.DataFrame,
    *,
    window_steps: int,
    expected_freq_minutes: int,
) -> pd.Series:
    """Return True where previous ``window_steps`` intervals are continuous."""

    diffs = group[TIMESTAMP_COL].diff().dt.total_seconds().div(60.0)
    is_expected_gap = diffs.eq(expected_freq_minutes)
    return (
        is_expected_gap.rolling(window_steps, min_periods=window_steps).sum()
        .eq(window_steps)
        .fillna(False)
    )


def add_lag_rolling_features(
    df: pd.DataFrame,
    *,
    lags: tuple[int, ...] = DEFAULT_LAGS,
    rolling_windows: tuple[int, ...] = DEFAULT_ROLLING_WINDOWS,
    expected_freq_minutes: int = 15,
) -> pd.DataFrame:
    """Add leakage-safe lag and rolling target features.

    All target-derived features are shifted by 1 before rolling. Features are
    nulled when the required historical window crosses a time gap.
    """

    out = df.copy()
    out = out.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)

    grouped = out.groupby(SITE_COL, group_keys=False, observed=True)

    for lag in lags:
        col = f"v2_lag_{lag}"
        out[col] = grouped[TARGET_COL].shift(lag)
        valid = grouped.apply(
            _continuous_history_mask,
            window_steps=lag,
            expected_freq_minutes=expected_freq_minutes,
        )
        out.loc[~valid.to_numpy(), col] = np.nan

    shifted_target = grouped[TARGET_COL].shift(1)

    for window in rolling_windows:
        valid = grouped.apply(
            _continuous_history_mask,
            window_steps=window,
            expected_freq_minutes=expected_freq_minutes,
        ).to_numpy()

        mean_col = f"v2_rolling_mean_{window}"
        std_col = f"v2_rolling_std_{window}"
        min_col = f"v2_rolling_min_{window}"
        max_col = f"v2_rolling_max_{window}"

        out[mean_col] = shifted_target.groupby(out[SITE_COL]).rolling(
            window, min_periods=window
        ).mean().reset_index(level=0, drop=True)
        out[std_col] = shifted_target.groupby(out[SITE_COL]).rolling(
            window, min_periods=window
        ).std().reset_index(level=0, drop=True)
        out[min_col] = shifted_target.groupby(out[SITE_COL]).rolling(
            window, min_periods=window
        ).min().reset_index(level=0, drop=True)
        out[max_col] = shifted_target.groupby(out[SITE_COL]).rolling(
            window, min_periods=window
        ).max().reset_index(level=0, drop=True)

        for col in (mean_col, std_col, min_col, max_col):
            out.loc[~valid, col] = np.nan

    target_feature_cols = [
        col for col in out.columns if col.startswith("v2_lag_") or col.startswith("v2_rolling_")
    ]
    out["v2_has_complete_history_features"] = ~out[target_feature_cols].isna().any(axis=1)

    return out


def build_v2_features(df: pd.DataFrame, config: FeatureConfig | None = None) -> pd.DataFrame:
    """Build all v2 features from a quality-checked dataframe."""

    config = config or FeatureConfig()
    _require_columns(df, [SITE_COL, TIMESTAMP_COL, TARGET_COL])

    out = df.copy()
    out[TIMESTAMP_COL] = pd.to_datetime(out[TIMESTAMP_COL], errors="coerce")
    out = out.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)

    out = add_time_features(out)
    out = add_metadata_features(out)
    out = add_weather_domain_features(out)
    out = add_lag_rolling_features(
        out,
        lags=config.lags,
        rolling_windows=config.rolling_windows,
        expected_freq_minutes=config.expected_freq_minutes,
    )
    return out


def feature_summary(df: pd.DataFrame) -> dict[str, int | float | str]:
    """Return feature engineering counters for logs/notebooks."""

    feature_cols = [col for col in df.columns if col.startswith("v2_")]
    summary: dict[str, int | float | str] = {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "v2_feature_columns": int(len(feature_cols)),
    }

    for col in ("v2_has_complete_history_features", "v2_missing_weather_flag", "v2_outlier_flag"):
        if col in df.columns:
            summary[col] = int(df[col].fillna(False).sum())

    return summary


def run_feature_engineering(config: FeatureConfig) -> pd.DataFrame:
    """Load quality parquet, build features, write parquet, return dataframe."""

    df = load_quality_checked(config.input_path)
    features = build_v2_features(df, config)

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(config.output_path, index=False)

    print("V2 feature engineering completed")
    print(f"input : {config.input_path}")
    print(f"output: {config.output_path}")
    for key, value in feature_summary(features).items():
        print(f"{key}: {value}")

    return features


def _parse_int_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(x.strip()) for x in value.split(",") if x.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v2 feature engineering.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expected-freq-minutes", type=int, default=15)
    parser.add_argument("--lags", type=_parse_int_tuple, default=DEFAULT_LAGS)
    parser.add_argument("--rolling-windows", type=_parse_int_tuple, default=DEFAULT_ROLLING_WINDOWS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = FeatureConfig(
        input_path=args.input,
        output_path=args.output,
        expected_freq_minutes=args.expected_freq_minutes,
        lags=args.lags,
        rolling_windows=args.rolling_windows,
    )
    run_feature_engineering(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
