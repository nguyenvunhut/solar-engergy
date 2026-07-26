"""Stage 07 — select safe model features.

Input:
    - Final candidate feature files from Stage 05.
    - Diagnostics from Stage 06.

Output:
    - ``selected_features.json`` per horizon under ``03_features/<run_id>/final``.
    - Feature-selection score CSVs under ``04_diagnostics/<run_id>``.

Important:
    - Uses sklearn mutual information only for feature scoring/selection, not
      for final forecasting model training.
    - Hard-denies target, future labels, provenance, outlier flags, IDs, and
      audit-only columns that would leak target information or create invalid
      shortcuts.
    - Feature selection uses rows eligible under the active sample-weight
      experiment, so rows with zero training weight do not steer feature choice.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_regression

from forecasting_common import add_common_cli, artifact_dir, load_config, write_json


def _load_neighbor(name: str):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


build_sample_weight = _load_neighbor("08_train_baselines.py").build_sample_weight


def eligible_feature_columns(df: pd.DataFrame, config, *, horizon_steps: int) -> list[str]:
    deny = set(config.raw["features"]["deny_list"])
    deny.update(
        {
            config.target_col,
            config.timestamp_col,
            "full_date",
            "weather_timestamp",
            "partition",
            "fold",
            "energy_source",
            "is_daylight",
            "is_daylight_scope",
            "is_daylight_physical",
            "daylight_source",
            "weather_daylight_disagreement",
            "solar_elevation_deg",
            "gmm_if_outlier_flag",
            "gmm_if_outlier_reason",
            "outlier_group",
            "exclude_from_training",
            "exclude_reason",
            "training_quality_reason",
            "after_source_gap_steps_remaining",
            "timestamp_was_inserted",
            "source_gap_id",
            "weather_is_observed",
            "gen_id",
            "date_id",
            "time_id",
            "weather_id",
            "weather_type_id",
        }
    )
    deny.update({c for c in df.columns if c.startswith("target_h") and c != f"target_h{horizon_steps}"})
    feature_cols: list[str] = []
    for col in df.columns:
        if col in deny or col == f"target_h{horizon_steps}":
            continue
        if col.startswith("lag_"):
            lag = int(col.split("_")[1])
            if lag < horizon_steps:
                raise AssertionError(f"{col} violates min_lag >= horizon_steps={horizon_steps}")
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_bool_dtype(df[col]):
            feature_cols.append(col)
    return feature_cols


def score_feature_columns(df: pd.DataFrame, config, *, horizon_steps: int) -> pd.DataFrame:
    target = f"target_h{horizon_steps}"
    cols = eligible_feature_columns(df, config, horizon_steps=horizon_steps)
    weight = build_sample_weight(df, config, horizon_steps=horizon_steps)
    mask = df[target].notna() & weight.gt(0)
    data = df.loc[mask, cols + [target]].copy()
    if data.empty or not cols:
        return pd.DataFrame(columns=["feature", "mi_score", "abs_corr", "null_pct", "selected"])

    sel_cfg = config.raw["features"].get("selection", {})
    sample_rows = int(sel_cfg.get("sample_rows", 100_000))
    seed = int(config.raw["training"]["lightgbm"]["random_seed"])
    if len(data) > sample_rows:
        data = data.sample(sample_rows, random_state=seed)

    x = data[cols].replace([np.inf, -np.inf], np.nan)
    medians = x.median(numeric_only=True).fillna(0.0)
    x = x.fillna(medians).astype(float)
    y = pd.to_numeric(data[target], errors="coerce").astype(float)
    valid = y.notna()
    x = x.loc[valid]
    y = y.loc[valid]
    if x.empty:
        return pd.DataFrame(columns=["feature", "mi_score", "abs_corr", "null_pct", "selected"])

    mi = mutual_info_regression(x, y, random_state=seed)
    corr = x.corrwith(y).abs().fillna(0.0)
    report = pd.DataFrame(
        {
            "feature": cols,
            "mi_score": mi,
            "abs_corr": [float(corr.get(c, 0.0)) for c in cols],
            "null_pct": [float(df[c].isna().mean() * 100.0) for c in cols],
        }
    ).sort_values(["mi_score", "abs_corr"], ascending=False)

    max_features = int(sel_cfg.get("max_features_per_horizon", len(report)))
    min_score = float(sel_cfg.get("min_score", 0.0))
    must_keep = [c for c in cols if c.startswith("lag_") or c.startswith("rolling_")]
    selected = report[report["mi_score"].ge(min_score)]["feature"].head(max_features).tolist()
    for col in must_keep:
        if col not in selected and col in cols and len(selected) < max_features:
            selected.append(col)
    report["selected"] = report["feature"].isin(selected)
    return report


def select_feature_columns(df: pd.DataFrame, config, *, horizon_steps: int) -> list[str]:
    sel_cfg = config.raw["features"].get("selection", {})
    eligible = eligible_feature_columns(df, config, horizon_steps=horizon_steps)
    if not bool(sel_cfg.get("enabled", True)):
        return eligible
    report = score_feature_columns(df, config, horizon_steps=horizon_steps)
    selected = report.loc[report["selected"], "feature"].tolist()
    return selected or eligible


def run_select_features(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    in_dir = artifact_dir(config, "03_features", rid) / "final"
    out_dir = artifact_dir(config, "04_diagnostics", rid)
    out_dir.mkdir(parents=True, exist_ok=True)
    selected: dict[str, list[str]] = {}
    paths: dict[str, Path] = {}
    for horizon in config.raw["time"]["horizon_steps"]:
        h = int(horizon)
        path = in_dir / f"h{h}" / "development_features.parquet"
        if path.exists():
            df = pd.read_parquet(path)
            report = score_feature_columns(df, config, horizon_steps=h)
            selected[f"h{h}"] = report.loc[report["selected"], "feature"].tolist()
            score_path = out_dir / f"h{h}_feature_selection_scores.csv"
            report.to_csv(score_path, index=False)
            paths[f"h{h}_feature_selection_scores"] = score_path
    out_path = out_dir / "selected_features.json"
    write_json({"run_id": rid, "selected_features": selected}, out_path)
    print("Feature selection complete")
    for key, cols in selected.items():
        print(f"{key}: {len(cols)} features")
    paths["selected_features"] = out_path
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select sklearn-compatible feature columns.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_select_features(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
