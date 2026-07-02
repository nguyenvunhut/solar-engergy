#!/usr/bin/env python3
"""Validate Decision Tree segmentation quality from GMM-IF audit output.

This script does not change the pipeline or database. It reads the generated
GMM-IF full audit CSV and computes how well each site's tree segments explain
the daytime residual distribution.

R² definitions used here:
    energy_r2:
        y     = energy_generated_kwh
        y_hat = mean/median energy of the row's own segment_id

    residual_r2:
        y     = residual_vs_expected
        y_hat = mean/median residual of the row's own segment_id

This is an audit of segment coherence, not supervised model validation.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "02_transform" / "01_generate_outliers.yaml"

with CONFIG_PATH.open(encoding="utf-8") as file:
    CONFIG = yaml.safe_load(file)

OUT_DIR = ROOT / CONFIG["paths"]["iqr_out_dir"]
FULL_AUDIT_CSV = OUT_DIR / "03_gmm_if_full_audit.csv"
SUMMARY_LOG = OUT_DIR / "08_decision_tree_segment_r2_summary.log"

NIGHT_SEGMENT_ID = -100


def _r2_score(y: np.ndarray, y_hat: np.ndarray) -> float:
    ss_res = float(np.square(y - y_hat).sum())
    ss_tot = float(np.square(y - y.mean()).sum())
    return 0.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot


def validate_site(site_df: pd.DataFrame) -> dict[str, float | int | str]:
    sitekey = str(site_df["sitekey"].iloc[0])
    daytime = site_df[
        (~site_df["is_night_zero"].astype(bool))
        & site_df["residual_vs_expected"].notna()
        & site_df["segment_id"].notna()
        & (site_df["segment_id"] != NIGHT_SEGMENT_ID)
    ].copy()

    if len(daytime) < 2:
        return {
            "sitekey": sitekey,
            "rows_total": len(site_df),
            "rows_scored_daytime": len(daytime),
            "leaf_segments": 0,
            "energy_r2_median": 0.0,
            "energy_r2_mean": 0.0,
            "residual_r2_median": 0.0,
            "residual_r2_mean": 0.0,
        }

    def segment_r2(column: str, agg: str) -> float:
        y = daytime[column].to_numpy(dtype=float)
        y_hat = (
            daytime.groupby("segment_id")[column]
            .transform(agg)
            .to_numpy(dtype=float)
        )
        return _r2_score(y, y_hat)

    return {
        "sitekey": sitekey,
        "rows_total": len(site_df),
        "rows_scored_daytime": len(daytime),
        "leaf_segments": int(daytime["segment_id"].nunique()),
        "energy_r2_median": segment_r2("energy_generated_kwh", "median"),
        "energy_r2_mean": segment_r2("energy_generated_kwh", "mean"),
        "residual_r2_median": segment_r2("residual_vs_expected", "median"),
        "residual_r2_mean": segment_r2("residual_vs_expected", "mean"),
    }


def main() -> int:
    if not FULL_AUDIT_CSV.exists():
        raise FileNotFoundError(
            f"Missing {FULL_AUDIT_CSV}. Run 02_gmm_if.py first."
        )

    columns = [
        "sitekey",
        "is_night_zero",
        "segment_id",
        "energy_generated_kwh",
        "residual_vs_expected",
    ]
    audit = pd.read_csv(FULL_AUDIT_CSV, usecols=columns)

    rows = []
    for _, site_df in audit.groupby("sitekey", sort=True):
        rows.append(validate_site(site_df))

    summary = pd.DataFrame(rows)
    summary["sitekey_sort"] = pd.to_numeric(summary["sitekey"], errors="coerce")
    summary = summary.sort_values(["sitekey_sort", "sitekey"]).drop(
        columns=["sitekey_sort"]
    )

    public_summary = summary[
        [
            "sitekey",
            "rows_scored_daytime",
            "leaf_segments",
            "energy_r2_mean",
        ]
    ].copy()

    overall = {
        "site_count": int(len(summary)),
        "rows_scored_daytime": int(summary["rows_scored_daytime"].sum()),
        "leaf_segments_min": int(summary["leaf_segments"].min()),
        "leaf_segments_mean": float(summary["leaf_segments"].mean()),
        "leaf_segments_max": int(summary["leaf_segments"].max()),
        "energy_r2_mean_min": float(summary["energy_r2_mean"].min()),
        "energy_r2_mean_mean": float(summary["energy_r2_mean"].mean()),
        "energy_r2_mean_max": float(summary["energy_r2_mean"].max()),
        "residual_r2_mean_min": float(summary["residual_r2_mean"].min()),
        "residual_r2_mean_mean": float(summary["residual_r2_mean"].mean()),
        "residual_r2_mean_max": float(summary["residual_r2_mean"].max()),
    }

    lines = [
        "DECISION TREE SEGMENT R2 VALIDATION",
        "=" * 72,
        f"source        : {FULL_AUDIT_CSV}",
        f"summary_log   : {SUMMARY_LOG}",
        "",
        "Overall:",
    ]
    lines.extend(f"  {key}: {value}" for key, value in overall.items())
    lines.extend(
        [
            "",
            "Per-site:",
            public_summary.to_string(index=False),
            "",
            "Note:",
            "  energy_r2 validates whether tree segments explain the raw PV generation profile.",
            "  This validates segment coherence, not final outlier precision/recall.",
        ]
    )
    text = "\n".join(lines)
    SUMMARY_LOG.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
