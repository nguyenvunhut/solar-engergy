"""Stage 01 — build a continuous 15-minute ML grid.

Input:
    - ``v3_final_cleaned`` rows from the ETL ML mart.
    - Raw solar provenance mapped in Stage 00.

Output:
    - ``continuous_full.parquet`` under ``01_continuous/<run_id>``.
    - Continuous-grid audit/manifest with energy-source counts.

Important:
    - Only inserted timestamp gaps are filled by the ML-stage causal cascade.
    - Existing target values from ``v3_final_cleaned`` are not rewritten here.
    - Weather fill is causal only: forward-fill from past observations, never
      back-fill from the future.
    - Static metadata is not invented; missing metadata is kept as missing so
      the model can treat it through explicit missing-value behavior/medians.
    - Physical-over-capacity and GMM/IF information is materialized as
      ``outlier_group`` for sample weighting and report scopes.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from forecasting_common import (
    add_calendar_columns,
    add_common_cli,
    add_daylight_columns,
    artifact_dir,
    classify_outlier_group,
    load_config,
    read_mlmart,
    read_raw_solar,
    write_json,
)


def attach_energy_source(df: pd.DataFrame, raw: pd.DataFrame, config) -> pd.DataFrame:
    cols = config.raw["columns"]
    key = raw[[cols["raw_site"], cols["raw_timestamp"], cols["raw_target"]]].rename(
        columns={
            cols["raw_site"]: config.site_col,
            cols["raw_timestamp"]: config.timestamp_col,
            cols["raw_target"]: "_raw_solar_generation",
        }
    )
    merged = df.merge(key, on=[config.site_col, config.timestamp_col], how="left", validate="one_to_one")
    merged["energy_source"] = np.where(merged["_raw_solar_generation"].notna(), "measured", "etl_imputed")
    merged["timestamp_was_inserted"] = False
    merged["exclude_from_training"] = False
    merged["exclude_reason"] = ""
    merged["training_quality_reason"] = ""
    merged["source_gap_id"] = pd.NA
    merged["after_source_gap_steps_remaining"] = 0
    if "gmm_if_outlier_flag" not in merged.columns:
        merged["gmm_if_outlier_flag"] = False
    if "gmm_if_outlier_reason" not in merged.columns:
        merged["gmm_if_outlier_reason"] = ""
    merged["outlier_group"] = classify_outlier_group(
        merged["gmm_if_outlier_flag"],
        merged["gmm_if_outlier_reason"],
    )
    return merged.drop(columns=["_raw_solar_generation"])


def build_site_grid(site_df: pd.DataFrame, config) -> pd.DataFrame:
    freq = f"{int(config.raw['time']['frequency_minutes'])}min"
    ts_col = config.timestamp_col
    site_col = config.site_col
    site_id = site_df[site_col].iloc[0]
    idx = pd.date_range(site_df[ts_col].min(), site_df[ts_col].max(), freq=freq)
    base = pd.DataFrame({ts_col: idx})
    merged = base.merge(site_df, on=ts_col, how="left", sort=True)
    merged[site_col] = merged[site_col].fillna(site_id).astype(site_df[site_col].dtype)
    merged["timestamp_was_inserted"] = merged["timestamp_was_inserted"].fillna(True).astype(bool)
    weather_cols = {
        "weather_is_day",
        "shortwave_radiation",
        "direct_normal_irradiance",
        "diffuse_solar_radiation",
        "temperature_c",
        "cloud_cover_total",
        "cloud_cover_low",
        "cloud_cover_mid",
        "cloud_cover_high",
        "wind_speed",
        "precipitation_mm",
        "sunshine_duration",
        "weather_code",
        "weather_condition",
        "weather_description",
    }
    existing_weather_cols = [c for c in weather_cols if c in merged.columns]
    if existing_weather_cols:
        merged["weather_is_observed"] = (
            ~merged["timestamp_was_inserted"]
            & merged[existing_weather_cols].notna().any(axis=1)
        )
    else:
        merged["weather_is_observed"] = False
    static_cols = {
        site_col,
        "site_id",
    }
    provenance_defaults = {
        "energy_source": "",
        "exclude_from_training": False,
        "exclude_reason": "",
        "training_quality_reason": "",
        "source_gap_id": pd.NA,
        "after_source_gap_steps_remaining": 0,
        "gmm_if_outlier_flag": False,
        "gmm_if_outlier_reason": "",
        "outlier_group": "normal",
    }
    for col in site_df.columns:
        if col in (ts_col, config.target_col):
            continue
        if col not in merged.columns:
            continue
        if col in provenance_defaults:
            merged[col] = merged[col].fillna(provenance_defaults[col])
        elif col in weather_cols:
            # Causal only: allow past weather to carry forward across inserted
            # source gaps, but never pull future weather backward.
            merged[col] = merged[col].ffill()
        elif col in static_cols:
            # Only the site key is structural to the reindexed grid.
            # Do not forward/backward-fill metadata such as capacity/panel/location:
            # if it is missing in v3_final_cleaned, keep it missing and expose it
            # through missing indicators in the spatial feature stage.
            continue
    return merged


def fill_inserted_energy(site_df: pd.DataFrame, config) -> pd.DataFrame:
    out = site_df.sort_values(config.timestamp_col).reset_index(drop=True).copy()
    target = config.target_col
    freq_min = int(config.raw["time"]["frequency_minutes"])
    major_slots = int(config.raw["gap"]["major_gap_hours"] * 60 // freq_min)
    max_lag = int(config.raw["time"]["max_lag_steps"])
    measured_values: dict[pd.Timestamp, float] = {}
    profile: dict[tuple[int, str], list[float]] = defaultdict(list)
    inserted = out["timestamp_was_inserted"].astype(bool)
    run_id = inserted.ne(inserted.shift(fill_value=False)).cumsum()
    run_lengths = inserted.groupby(run_id).transform("sum").where(inserted, 0).astype(int)
    out["_inserted_run_len"] = run_lengths
    gap_id = 0
    current_gap_active = False

    out["energy_source"] = out["energy_source"].fillna("")
    out["exclude_from_training"] = out["exclude_from_training"].fillna(False).astype(bool)
    out["exclude_reason"] = out["exclude_reason"].fillna("")
    out["training_quality_reason"] = out["training_quality_reason"].fillna("")
    out["source_gap_id"] = out["source_gap_id"].astype("object")

    for i, row in out.iterrows():
        ts = pd.Timestamp(row[config.timestamp_col])
        key = (int(row["quarter_hour"]), str(row["season_model"]))
        if not bool(row["timestamp_was_inserted"]):
            if row["energy_source"] == "measured" and pd.notna(row[target]):
                val = float(row[target])
                measured_values[ts] = val
                profile[key].append(val)
            if current_gap_active:
                end = min(i + max_lag, len(out))
                out.loc[i:end - 1, "after_source_gap_steps_remaining"] = np.maximum(
                    out.loc[i:end - 1, "after_source_gap_steps_remaining"].astype(int),
                    np.arange(max_lag, max_lag - (end - i), -1),
                )
                current_gap_active = False
            continue

        if not current_gap_active:
            gap_id += 1
            current_gap_active = True
        out.at[i, "source_gap_id"] = gap_id
        current_gap_len = int(out.at[i, "_inserted_run_len"])
        daylight = bool(row["is_daylight"])

        if current_gap_len >= major_slots:
            out.at[i, target] = 0.0
            out.at[i, "energy_source"] = "machine_failure_zero"
            out.at[i, "exclude_from_training"] = True
            out.at[i, "exclude_reason"] = "MACHINE_FAILURE_DATA_GAP"
            out.at[i, "training_quality_reason"] = "SOURCE_GAP_MAJOR_OUTAGE+MACHINE_FAILURE_DATA_GAP"
            continue

        if not daylight:
            out.at[i, target] = 0.0
            out.at[i, "energy_source"] = "night_zero"
            out.at[i, "training_quality_reason"] = "SOURCE_GAP_SHORT_IMPUTED"
            continue

        day_ts = ts - pd.Timedelta(minutes=freq_min * 96)
        week_ts = ts - pd.Timedelta(minutes=freq_min * 672)
        if day_ts in measured_values:
            out.at[i, target] = measured_values[day_ts]
            out.at[i, "energy_source"] = "causal_day_persistence"
        elif week_ts in measured_values:
            out.at[i, target] = measured_values[week_ts]
            out.at[i, "energy_source"] = "causal_week_persistence"
        elif profile.get(key):
            out.at[i, target] = float(np.median(profile[key]))
            out.at[i, "energy_source"] = "causal_profile_median"
        else:
            out.at[i, target] = 0.0
            out.at[i, "energy_source"] = "fallback_zero"
        out.at[i, "training_quality_reason"] = "SOURCE_GAP_SHORT_IMPUTED"
    return out.drop(columns=["_inserted_run_len"])


def run_build_continuous(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    out_dir = artifact_dir(config, "01_continuous", rid)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = read_mlmart(config)
    raw = read_raw_solar(config)
    df = attach_energy_source(df, raw, config)
    df = add_calendar_columns(df, config)
    df = add_daylight_columns(df, config)

    continuous_parts = []
    for _, site_df in df.groupby(config.site_col, observed=True, sort=True):
        site_grid = build_site_grid(site_df, config)
        site_grid = add_calendar_columns(site_grid, config)
        site_grid = add_daylight_columns(site_grid, config)
        continuous_parts.append(fill_inserted_energy(site_grid, config))
    continuous = pd.concat(continuous_parts, ignore_index=True).sort_values(
        [config.site_col, config.timestamp_col]
    )
    energy_null_rows = int(continuous[config.target_col].isna().sum())
    energy_source_null_rows = int(continuous["energy_source"].isna().sum())
    if energy_null_rows or energy_source_null_rows:
        raise RuntimeError(
            "Continuous grid gate failed: "
            f"energy_null_rows={energy_null_rows}, energy_source_null_rows={energy_source_null_rows}"
        )

    audit = (
        continuous.groupby(config.site_col, observed=True)
        .agg(
            rows=(config.target_col, "size"),
            inserted_rows=("timestamp_was_inserted", "sum"),
            target_null_rows=(config.target_col, lambda s: int(s.isna().sum())),
            measured_rows=("energy_source", lambda s: int(s.eq("measured").sum())),
            etl_imputed_rows=("energy_source", lambda s: int(s.eq("etl_imputed").sum())),
            synthetic_rows=("timestamp_was_inserted", "sum"),
            after_gap_rows=("after_source_gap_steps_remaining", lambda s: int(pd.to_numeric(s, errors="coerce").gt(0).sum())),
            exclude_rows=("exclude_from_training", "sum"),
        )
        .reset_index()
    )
    source_counts = continuous["energy_source"].value_counts(dropna=False).rename_axis("energy_source").reset_index(name="rows")

    paths = {
        "continuous_full": out_dir / "continuous_full.parquet",
        "continuous_grid_audit": out_dir / "continuous_grid_audit.csv",
        "energy_source_counts": out_dir / "energy_source_counts.csv",
        "manifest": out_dir / "continuous_grid_manifest.json",
    }
    continuous.to_parquet(paths["continuous_full"], index=False)
    audit.to_csv(paths["continuous_grid_audit"], index=False)
    source_counts.to_csv(paths["energy_source_counts"], index=False)
    write_json(
        {
            "run_id": rid,
            "rows": int(len(continuous)),
            "source_rows": int(len(df)),
            "inserted_rows": int(continuous["timestamp_was_inserted"].sum()),
            "energy_null_rows": energy_null_rows,
            "energy_source_null_rows": energy_source_null_rows,
            "max_lag_steps": int(config.raw["time"]["max_lag_steps"]),
        },
        paths["manifest"],
    )
    print("Continuous grid complete")
    print(source_counts.to_string(index=False))
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build continuous ML-derived forecasting grid.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_build_continuous(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
