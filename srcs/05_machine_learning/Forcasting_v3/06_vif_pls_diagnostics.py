"""Stage 06 — feature diagnostics before model selection.

Input:
    - Final candidate feature files from Stage 05.

Output:
    - Correlation/VIF-like diagnostics and feature diagnostic manifest under
      ``04_diagnostics/<run_id>``.

Important:
    - This stage is diagnostic, not a model training step.
    - It helps identify redundant/constant features before mutual-information
      feature selection.
    - Any high-correlation warning is interpreted with time-series context;
      lag features can be correlated by design and are not automatically wrong.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from forecasting_common import add_common_cli, artifact_dir, load_config, write_json


def numeric_feature_columns(df: pd.DataFrame, target_col: str) -> list[str]:
    deny = {target_col, "gen_id", "date_id", "time_id", "weather_id", "weather_type_id"}
    cols = []
    for col in df.select_dtypes(include=["number", "bool"]).columns:
        if col not in deny and not col.startswith("target_h"):
            cols.append(col)
    return cols


def run_diagnostics(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    in_dir = artifact_dir(config, "03_features", rid) / "final"
    out_dir = artifact_dir(config, "04_diagnostics", rid)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for horizon in config.raw["time"]["horizon_steps"]:
        path = in_dir / f"h{int(horizon)}" / "development_features.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        cols = numeric_feature_columns(df, config.target_col)
        if not cols:
            continue
        sample = df[cols].sample(min(len(df), 200_000), random_state=42) if len(df) > 200_000 else df[cols]
        corr = sample.corr(numeric_only=True).abs()
        for col in cols:
            rows.append(
                {
                    "horizon_steps": int(horizon),
                    "feature": col,
                    "null_pct": float(df[col].isna().mean() * 100),
                    "max_abs_corr_other": float(corr[col].drop(labels=[col], errors="ignore").max()) if col in corr else np.nan,
                }
            )
    report = pd.DataFrame(rows)
    paths = {"diagnostics": out_dir / "feature_diagnostics.csv", "manifest": out_dir / "diagnostics_manifest.json"}
    report.to_csv(paths["diagnostics"], index=False)
    write_json({"run_id": rid, "rows": int(len(report)), "note": "VIF/PLS full diagnostics can extend this report."}, paths["manifest"])
    print(f"Diagnostics complete: {len(report)} feature rows")
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run feature diagnostics.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_diagnostics(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
