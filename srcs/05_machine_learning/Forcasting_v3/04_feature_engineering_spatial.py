"""Stage 04 — spatial/static feature pass.

Input:
    - Horizon feature files from Stage 03.

Output:
    - Spatial-enhanced parquet files under ``03_features/<run_id>/spatial``.

Important:
    - Adds only defensible static/site-level numeric features and simple ratios.
    - Does not encode target-derived outlier/provenance columns as model inputs.
    - String metadata may be kept for audit/reporting, but final feature
      selection only permits safe numeric/bool columns.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from forecasting_common import add_common_cli, artifact_dir, load_config, write_json


def add_spatial_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if {"capacity_kw", "number_of_panels"}.issubset(out.columns):
        out["capacity_per_panel"] = out["capacity_kw"] / out["number_of_panels"].replace(0, pd.NA)
    metadata_cols = [
        "geo_id",
        "campus_name",
        "capacity_kw",
        "number_of_panels",
        "panel",
        "inverter",
        "optimizers",
        "site_metric",
        "location_name",
        "latitude",
        "longitude",
    ]
    for col in metadata_cols:
        if col in out.columns:
            out[f"{col}_missing"] = out[col].isna().astype("int8")
    return out


def run_spatial_features(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    in_dir = artifact_dir(config, "03_features", rid)
    out_dir = artifact_dir(config, "03_features", rid) / "spatial"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for path in sorted(in_dir.glob("h*/*_features.parquet")):
        rel = path.relative_to(in_dir)
        out_path = out_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        add_spatial_features(pd.read_parquet(path)).to_parquet(out_path, index=False)
        paths[str(rel)] = out_path
    write_json({"run_id": rid, "files": len(paths), "source": str(in_dir)}, out_dir / "spatial_feature_manifest.json")
    print(f"Spatial feature pass complete: {len(paths)} files")
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build spatial/static forecasting features.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_spatial_features(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
