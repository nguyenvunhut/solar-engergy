"""Stage 05 — aggregate/exogenous feature pass.

Input:
    - Spatial-enhanced feature files from Stage 04.

Output:
    - Final candidate feature parquet files under ``03_features/<run_id>/final``.

Important:
    - Adds weather/radiation interaction features useful for PV forecasting.
    - Does not create future-looking aggregates.
    - Feature selection in Stage 07 remains responsible for denying leakage
      columns and choosing the final model feature set.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from forecasting_common import add_common_cli, artifact_dir, load_config, write_json


def add_aggregate_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if {"shortwave_radiation", "capacity_kw"}.issubset(out.columns):
        out["radiation_per_capacity"] = out["shortwave_radiation"] / out["capacity_kw"].replace(0, pd.NA)
    if {"diffuse_solar_radiation", "shortwave_radiation"}.issubset(out.columns):
        out["diffuse_ratio"] = out["diffuse_solar_radiation"] / out["shortwave_radiation"].replace(0, pd.NA)
    if {"cloud_cover_total", "shortwave_radiation"}.issubset(out.columns):
        out["cloud_x_shortwave"] = out["cloud_cover_total"] * out["shortwave_radiation"]
    return out


def run_aggregate_features(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    in_dir = artifact_dir(config, "03_features", rid) / "spatial"
    out_dir = artifact_dir(config, "03_features", rid) / "final"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for path in sorted(in_dir.glob("h*/*_features.parquet")):
        rel = path.relative_to(in_dir)
        out_path = out_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        add_aggregate_features(pd.read_parquet(path)).to_parquet(out_path, index=False)
        paths[str(rel)] = out_path
    write_json({"run_id": rid, "files": len(paths), "source": str(in_dir)}, out_dir / "aggregate_feature_manifest.json")
    print(f"Aggregate feature pass complete: {len(paths)} files")
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build aggregate forecasting features.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_aggregate_features(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
