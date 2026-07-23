"""Stage 13 — long-term Prophet branch placeholder.

Input:
    - Evaluation/test artifacts from the forecasting run.

Output:
    - Prophet manifest and optional long-term prediction audit under
      ``07_metrics/<run_id>``.

Important:
    - Prophet is treated as a separate long-term/hourly reference branch, not
      the main 15-minute site-level model.
    - Current output may only prove that Prophet is available; do not claim
      Prophet beats LightGBM unless this stage writes real y_true/y_pred metrics.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from forecasting_common import add_common_cli, artifact_dir, load_config, write_json


def run_prophet(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    out_dir = artifact_dir(config, "07_metrics", rid)
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        from prophet import Prophet  # noqa: F401

        status = "prophet_available"
    except Exception as exc:
        status = f"optional_dependency_missing: {exc}"
    audit_path = out_dir / "prediction_audit_long_term.parquet"
    pd.DataFrame(columns=["site_id", "timestamp", "granularity", "horizon", "y_true", "y_pred", "model_name"]).to_parquet(audit_path, index=False)
    manifest_path = out_dir / "prophet_long_term_manifest.json"
    write_json({"run_id": rid, "status": status, "granularity": config.raw["prophet"]["granularity"]}, manifest_path)
    print(f"Prophet stage complete: {status}")
    return {"prediction_audit_long_term": audit_path, "manifest": manifest_path}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train long-term Prophet branch.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_prophet(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
