"""Stage 03 — point-in-time time features, lags, rolling windows, and labels.

Input:
    - Split parquet files from Stage 02.

Output:
    - Horizon-specific feature parquet files under ``03_features/<run_id>/h*``.
    - Feature manifest with horizon, lag, and rolling-window rules.

Important:
    - Label convention is ``target_h{h}(t) = energy(t + h)``.
    - Lag features must satisfy ``min_lag >= horizon`` to avoid future leakage.
    - Fold validation/test features are built with historical context from the
      preceding partition, then filtered back to validation/test rows.
    - Label provenance columns are shifted together with the target so sample
      weighting and metric scopes reflect the true label being predicted.
    - Current outlier/excluded rows are not allowed to contaminate lag/rolling
      source values used by later timestamps.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from forecasting_common import add_calendar_columns, add_common_cli, artifact_dir, load_config, write_json


def _add_cyclical(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["hour_sin"] = np.sin(2 * np.pi * out["minute_of_day"] / 1440.0)
    out["hour_cos"] = np.cos(2 * np.pi * out["minute_of_day"] / 1440.0)
    out["doy_sin"] = np.sin(2 * np.pi * out["day_of_year"] / 365.25)
    out["doy_cos"] = np.cos(2 * np.pi * out["day_of_year"] / 365.25)
    return out


def _safe_bool_series(df: pd.DataFrame, col: str, default: bool = False) -> pd.Series:
    if col not in df.columns:
        return pd.Series(default, index=df.index)
    return df[col].fillna(default).astype(bool)


def _target_feature_source(out: pd.DataFrame, config) -> tuple[pd.Series, dict[str, int]]:
    """Return target series allowed to feed lag/rolling features.

    Outlier rows are not allowed to become lag/rolling source for later rows.
    This avoids the common bug where the label row is excluded but its abnormal
    energy value still enters the model as lag_1/rolling_* on following rows.
    """

    target = config.target_col
    source = pd.to_numeric(out[target], errors="coerce")
    invalid = source.isna()
    invalid |= _safe_bool_series(out, "gmm_if_outlier_flag")
    invalid |= _safe_bool_series(out, "exclude_from_training")
    clean_source = source.mask(invalid)
    return clean_source, {
        "lag_source_null_rows": int(clean_source.isna().sum()),
        "lag_source_gmm_if_outlier_rows": int(_safe_bool_series(out, "gmm_if_outlier_flag").sum()),
        "lag_source_excluded_rows": int(_safe_bool_series(out, "exclude_from_training").sum()),
    }


def _future_label_valid_mask(out: pd.DataFrame, config, *, horizon_steps: int) -> tuple[pd.Series, dict[str, int]]:
    """Mask rows whose future y(t+h) is valid for supervised training/evaluation."""

    site = config.site_col
    grouped = out.groupby(site, observed=True, group_keys=False)
    valid = pd.Series(True, index=out.index)

    if "energy_source" in out.columns:
        future_source = grouped["energy_source"].shift(-horizon_steps)
        valid &= future_source.isin(["measured", "etl_imputed"]).fillna(False)
    if "exclude_from_training" in out.columns:
        future_excluded = grouped["exclude_from_training"].shift(-horizon_steps).fillna(False).astype(bool)
        valid &= ~future_excluded
    if "after_source_gap_steps_remaining" in out.columns:
        future_after_gap = pd.to_numeric(
            grouped["after_source_gap_steps_remaining"].shift(-horizon_steps),
            errors="coerce",
        ).fillna(0).gt(0)
        valid &= ~future_after_gap

    daylight_col = "is_daylight_scope" if "is_daylight_scope" in out.columns else "is_daylight"
    if daylight_col in out.columns:
        future_daylight = grouped[daylight_col].shift(-horizon_steps).fillna(False).astype(bool)
        valid &= future_daylight

    return valid, {
        "target_valid_rows": int(valid.sum()),
        "target_invalid_rows": int((~valid).sum()),
        "target_outlier_rows_left_for_weighting": int(
            grouped["gmm_if_outlier_flag"].shift(-horizon_steps).fillna(False).astype(bool).sum()
        )
        if "gmm_if_outlier_flag" in out.columns
        else 0,
        "target_etl_imputed_rows_left_for_weighting": int(
            grouped["energy_source"].shift(-horizon_steps).eq("etl_imputed").fillna(False).sum()
        )
        if "energy_source" in out.columns
        else 0,
    }


def _add_future_label_metadata(out: pd.DataFrame, config, *, horizon_steps: int) -> pd.DataFrame:
    """Attach provenance for the future label row y(t+h).

    Train/evaluate policy must be based on the timestamp that supplies
    ``target_h{h}``, not on the feature row at timestamp t.
    """

    grouped = out.groupby(config.site_col, observed=True, group_keys=False)
    for col in [
        "energy_source",
        "gmm_if_outlier_flag",
        "gmm_if_outlier_reason",
        "outlier_group",
        "exclude_from_training",
        "exclude_reason",
        "training_quality_reason",
        "after_source_gap_steps_remaining",
    ]:
        if col in out.columns:
            out[f"target_h{horizon_steps}_{col}"] = grouped[col].shift(-horizon_steps)

    daylight_col = "is_daylight_scope" if "is_daylight_scope" in out.columns else "is_daylight"
    if daylight_col in out.columns:
        out[f"target_h{horizon_steps}_is_daylight_scope"] = grouped[daylight_col].shift(-horizon_steps)
    return out


def build_time_features(df: pd.DataFrame, config, *, horizon_steps: int) -> tuple[pd.DataFrame, dict[str, object]]:
    target = config.target_col
    site = config.site_col
    ts_col = config.timestamp_col
    out = add_calendar_columns(df, config).sort_values([site, ts_col]).reset_index(drop=True)
    out = _add_cyclical(out)
    grouped = out.groupby(site, observed=True, group_keys=False)
    clean_target_source, source_manifest = _target_feature_source(out, config)
    grouped_clean_source = clean_target_source.groupby(out[site], observed=True)

    lags = [int(x) for x in config.raw["time"]["lag_steps"] if int(x) >= horizon_steps]
    rolling_windows = [int(x) for x in config.raw["time"]["rolling_windows"]]
    label_manifests: dict[str, dict[str, int]] = {}
    for h in config.raw["time"]["horizon_steps"]:
        h = int(h)
        out = _add_future_label_metadata(out, config, horizon_steps=h)
        label_valid, label_manifest = _future_label_valid_mask(out, config, horizon_steps=h)
        out[f"target_h{h}"] = grouped[target].shift(-h).where(label_valid)
        out[f"target_h{h}_valid_label"] = label_valid.astype("int8")
        label_manifests[f"h{h}"] = label_manifest

    for lag in lags:
        out[f"lag_{lag}"] = grouped_clean_source.shift(lag)

    shifted = grouped_clean_source.shift(horizon_steps)
    for window in rolling_windows:
        roll = shifted.groupby(out[site]).rolling(window, min_periods=max(2, min(window, 4)))
        out[f"rolling_mean_{window}"] = roll.mean().reset_index(level=0, drop=True)
        out[f"rolling_std_{window}"] = roll.std().reset_index(level=0, drop=True)
        out[f"rolling_min_{window}"] = roll.min().reset_index(level=0, drop=True)
        out[f"rolling_max_{window}"] = roll.max().reset_index(level=0, drop=True)

    out["horizon_steps"] = horizon_steps
    out["min_target_derived_lag_steps"] = min(lags) if lags else pd.NA
    manifest = {
        "horizon_steps": horizon_steps,
        "lag_steps": lags,
        "rolling_windows": rolling_windows,
        "min_target_derived_lag_steps": min(lags) if lags else None,
        "assert_min_lag_ge_horizon": bool(not lags or min(lags) >= horizon_steps),
        **source_manifest,
        "label_quality_by_horizon": label_manifests,
    }
    if lags and min(lags) < horizon_steps:
        raise AssertionError("min_target_derived_lag_steps must be >= horizon_steps")
    return out, manifest


def purge_fold_train_boundary(df: pd.DataFrame, config, *, horizon_steps: int) -> pd.DataFrame:
    """Drop the last horizon rows per site from fold_train artifacts.

    This is a conservative embargo: no training row at the fold boundary can
    use a target timestamp that belongs to the validation window.
    """

    site = config.site_col
    ordered = df.sort_values([site, config.timestamp_col]).copy()
    reverse_pos = ordered.groupby(site, observed=True).cumcount(ascending=False)
    return ordered[reverse_pos >= horizon_steps].copy()


def run_time_features(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    split_dir = artifact_dir(config, "02_splits", rid)
    out_dir = artifact_dir(config, "03_features", rid)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not split_dir.exists():
        raise FileNotFoundError(f"Split dir not found: {split_dir}")

    paths: dict[str, Path] = {}
    manifests: dict[str, object] = {"run_id": rid, "horizons": {}}
    development_df = pd.read_parquet(split_dir / "development.parquet")
    test_df = pd.read_parquet(split_dir / "test.parquet")
    for horizon in [int(x) for x in config.raw["time"]["horizon_steps"]]:
        h_dir = out_dir / f"h{horizon}"
        h_dir.mkdir(parents=True, exist_ok=True)
        development_features, manifest = build_time_features(development_df, config, horizon_steps=horizon)
        development_path = h_dir / "development_features.parquet"
        development_features.to_parquet(development_path, index=False)
        paths[f"h{horizon}_development"] = development_path
        manifests["horizons"][horizon] = manifest

        test_context = pd.concat([development_df, test_df], ignore_index=True, sort=False)
        test_features, _ = build_time_features(test_context, config, horizon_steps=horizon)
        test_features = test_features[test_features["partition"].eq("test")].copy()
        test_path = h_dir / "test_features.parquet"
        test_features.to_parquet(test_path, index=False)
        paths[f"h{horizon}_test"] = test_path
        fold_files = sorted(split_dir.glob("fold_*_train.parquet"))
        for train_path in fold_files:
            fold_name = train_path.name.replace("_train.parquet", "")
            val_path = split_dir / f"{fold_name}_val.parquet"
            train_df = pd.read_parquet(train_path)
            val_df = pd.read_parquet(val_path)
            context_val = pd.concat([train_df, val_df], ignore_index=True, sort=False)
            train_features, _ = build_time_features(train_df, config, horizon_steps=horizon)
            train_features = purge_fold_train_boundary(train_features, config, horizon_steps=horizon)
            val_features, _ = build_time_features(context_val, config, horizon_steps=horizon)
            val_features = val_features[val_features["partition"].eq("fold_val")].copy()
            train_features.to_parquet(h_dir / f"{fold_name}_train_features.parquet", index=False)
            val_features.to_parquet(h_dir / f"{fold_name}_val_features.parquet", index=False)
    manifest_path = out_dir / "time_feature_manifest.json"
    write_json(manifests, manifest_path)
    paths["manifest"] = manifest_path
    print("Time feature engineering complete")
    print(json.dumps(manifests, indent=2, default=str))
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build point-in-time time features.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_time_features(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
