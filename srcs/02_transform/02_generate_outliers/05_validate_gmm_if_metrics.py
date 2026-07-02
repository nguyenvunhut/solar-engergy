#!/usr/bin/env python3
"""Print operational validation metrics for the GMM-IF outlier stage.

This is not supervised model validation because the project does not have
human-labelled outlier ground truth. The goal is to expose defensible pipeline
metrics directly after `02_gmm_if.py`:

* how many rows each detector catches;
* how aggressively GMM and IF are filtered by consensus;
* how final flags distribute by site and hour;
* whether Isolation Forest scores separate flagged rows from normal rows.

The script is read-only. It writes a plain-text log and prints the same content
to stdout so pipeline logs contain the metrics.
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
SITE_SUMMARY_CSV = OUT_DIR / "02_gmm_if_site_summary.csv"
FULL_AUDIT_CSV = OUT_DIR / "03_gmm_if_full_audit.csv"
METRICS_LOG = OUT_DIR / "11_gmm_if_model_metrics.log"


def safe_div(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else float(numerator) / float(denominator)


def pct(numerator: float, denominator: float) -> float:
    return safe_div(numerator, denominator) * 100.0


def bool_series(series: pd.Series) -> pd.Series:
    """Handle bool columns read either as bools or strings."""
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .isin({"true", "t", "1", "yes", "y"})
    )


def read_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    missing = [
        str(path)
        for path in (SITE_SUMMARY_CSV, FULL_AUDIT_CSV)
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(
            "Missing required GMM-IF audit files. Run 02_gmm_if.py first.\n"
            + "\n".join(f"- {path}" for path in missing)
        )

    site_summary = pd.read_csv(SITE_SUMMARY_CSV)
    audit = pd.read_csv(
        FULL_AUDIT_CSV,
        usecols=[
            "sitekey",
            "hour",
            "month",
            "is_night_zero",
            "gmm_flag",
            "if_flag",
            "if_anomaly_score",
            "gmm_if_consensus_flag",
            "physical_rule_flag",
            "is_outlier",
        ],
    )

    for column in [
        "is_night_zero",
        "gmm_flag",
        "if_flag",
        "gmm_if_consensus_flag",
        "physical_rule_flag",
        "is_outlier",
    ]:
        audit[column] = bool_series(audit[column])

    audit["sitekey"] = audit["sitekey"].astype(str)
    site_summary["sitekey"] = site_summary["sitekey"].astype(str)
    return site_summary, audit


def build_site_metrics(site_summary: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    site_metrics = site_summary.copy()
    site_metrics["gmm_rate_day_pct"] = site_metrics.apply(
        lambda row: pct(row["gmm_flags"], row["rows_day"]),
        axis=1,
    )
    site_metrics["if_rate_day_pct"] = site_metrics.apply(
        lambda row: pct(row["if_flags"], row["rows_day"]),
        axis=1,
    )
    site_metrics["consensus_rate_day_pct"] = site_metrics.apply(
        lambda row: pct(row["gmm_if_consensus_flags"], row["rows_day"]),
        axis=1,
    )
    site_metrics["physical_rate_day_pct"] = site_metrics.apply(
        lambda row: pct(row["physical_rule_flags"], row["rows_day"]),
        axis=1,
    )
    site_metrics["final_rate_day_pct"] = site_metrics.apply(
        lambda row: pct(row["outliers_final"], row["rows_day"]),
        axis=1,
    )
    site_metrics["gmm_to_consensus_pct"] = site_metrics.apply(
        lambda row: pct(row["gmm_if_consensus_flags"], row["gmm_flags"]),
        axis=1,
    )
    site_metrics["if_to_consensus_pct"] = site_metrics.apply(
        lambda row: pct(row["gmm_if_consensus_flags"], row["if_flags"]),
        axis=1,
    )

    day = audit[~audit["is_night_zero"]].copy()
    if_score = (
        day.groupby("sitekey")["if_anomaly_score"]
        .agg(
            if_score_mean="mean",
            if_score_p95=lambda s: s.quantile(0.95),
            if_score_p99=lambda s: s.quantile(0.99),
        )
        .reset_index()
    )
    site_metrics = site_metrics.merge(if_score, on="sitekey", how="left")
    site_metrics["sitekey_sort"] = pd.to_numeric(site_metrics["sitekey"], errors="coerce")
    return site_metrics.sort_values(["sitekey_sort", "sitekey"]).drop(
        columns=["sitekey_sort"]
    )


def build_rate_table(audit: pd.DataFrame, group_col: str) -> pd.DataFrame:
    day = audit[~audit["is_night_zero"]].copy()
    rows = (
        day.groupby(group_col)
        .agg(
            rows_day=("is_outlier", "size"),
            gmm_flags=("gmm_flag", "sum"),
            if_flags=("if_flag", "sum"),
            consensus_flags=("gmm_if_consensus_flag", "sum"),
            physical_flags=("physical_rule_flag", "sum"),
            final_outliers=("is_outlier", "sum"),
        )
        .reset_index()
    )
    for col, base in [
        ("gmm_rate_pct", "gmm_flags"),
        ("if_rate_pct", "if_flags"),
        ("consensus_rate_pct", "consensus_flags"),
        ("physical_rate_pct", "physical_flags"),
        ("final_rate_pct", "final_outliers"),
    ]:
        rows[col] = rows.apply(lambda row: pct(row[base], row["rows_day"]), axis=1)
    return rows.sort_values(group_col)


def main() -> int:
    site_summary, audit = read_inputs()
    site_metrics = build_site_metrics(site_summary, audit)

    total_rows = int(site_summary["rows_total"].sum())
    rows_day = int(site_summary["rows_day"].sum())
    gmm_flags = int(site_summary["gmm_flags"].sum())
    if_flags = int(site_summary["if_flags"].sum())
    consensus_flags = int(site_summary["gmm_if_consensus_flags"].sum())
    physical_flags = int(site_summary["physical_rule_flags"].sum())
    final_outliers = int(site_summary["outliers_final"].sum())

    day = audit[~audit["is_night_zero"]]
    final_mask = day["is_outlier"]
    normal_mask = ~final_mask

    if_score_flagged_mean = float(day.loc[final_mask, "if_anomaly_score"].mean())
    if_score_normal_mean = float(day.loc[normal_mask, "if_anomaly_score"].mean())

    overall = {
        "site_count": int(site_summary["sitekey"].nunique()),
        "total_rows": total_rows,
        "rows_day": rows_day,
        "gmm_flags": gmm_flags,
        "if_flags": if_flags,
        "gmm_if_consensus_flags": consensus_flags,
        "physical_rule_flags": physical_flags,
        "final_outliers": final_outliers,
        "gmm_rate_day_pct": pct(gmm_flags, rows_day),
        "if_rate_day_pct": pct(if_flags, rows_day),
        "consensus_rate_day_pct": pct(consensus_flags, rows_day),
        "physical_rate_day_pct": pct(physical_flags, rows_day),
        "final_rate_day_pct": pct(final_outliers, rows_day),
        "gmm_to_consensus_pct": pct(consensus_flags, gmm_flags),
        "if_to_consensus_pct": pct(consensus_flags, if_flags),
        "if_score_day_p50": float(day["if_anomaly_score"].quantile(0.50)),
        "if_score_day_p95": float(day["if_anomaly_score"].quantile(0.95)),
        "if_score_day_p99": float(day["if_anomaly_score"].quantile(0.99)),
        "if_score_final_outliers_mean": if_score_flagged_mean,
        "if_score_normal_rows_mean": if_score_normal_mean,
        "if_score_mean_gap": if_score_flagged_mean - if_score_normal_mean,
    }

    public_site_metrics = site_metrics[
        [
            "sitekey",
            "rows_day",
            "gmm_rate_day_pct",
            "if_rate_day_pct",
            "consensus_rate_day_pct",
            "physical_rate_day_pct",
            "final_rate_day_pct",
            "gmm_to_consensus_pct",
            "if_to_consensus_pct",
            "if_score_p95",
            "if_score_p99",
        ]
    ].copy()

    hour_metrics = build_rate_table(audit, "hour")
    month_metrics = build_rate_table(audit, "month")

    lines = [
        "GMM-IF / PHYSICAL GUARDRAIL MODEL METRICS",
        "=" * 72,
        f"site_summary : {SITE_SUMMARY_CSV}",
        f"full_audit   : {FULL_AUDIT_CSV}",
        f"metrics_log  : {METRICS_LOG}",
        "",
        "Overall:",
    ]
    for key, value in overall.items():
        if isinstance(value, float):
            lines.append(f"  {key}: {value:.6f}")
        else:
            lines.append(f"  {key}: {value:,}")

    lines.extend(
        [
            "",
            "Per-site rates:",
            public_site_metrics.to_string(index=False, float_format=lambda x: f"{x:.6f}"),
            "",
            "Final outlier rate by hour:",
            hour_metrics[
                [
                    "hour",
                    "rows_day",
                    "gmm_rate_pct",
                    "if_rate_pct",
                    "consensus_rate_pct",
                    "physical_rate_pct",
                    "final_rate_pct",
                ]
            ].to_string(index=False, float_format=lambda x: f"{x:.6f}"),
            "",
            "Final outlier rate by month:",
            month_metrics[
                [
                    "month",
                    "rows_day",
                    "gmm_rate_pct",
                    "if_rate_pct",
                    "consensus_rate_pct",
                    "physical_rate_pct",
                    "final_rate_pct",
                ]
            ].to_string(index=False, float_format=lambda x: f"{x:.6f}"),
            "",
            "Interpretation:",
            "  - No human labels exist, so these are monitoring/defensibility metrics, not supervised loss/precision/recall.",
            "  - gmm_rate_day_pct and if_rate_day_pct show each detector's raw sensitivity on daytime rows.",
            "  - gmm_to_consensus_pct and if_to_consensus_pct show how much each detector survives the GMM ∧ IF filter.",
            "  - final_rate_day_pct is the actual business flag rate after GMM-IF consensus OR physical guardrail.",
            "  - IF anomaly scores are useful for separation monitoring; higher flagged-vs-normal gap is better.",
            "  - GMM BIC/AIC/log-likelihood is not available from the current audit because fitted GMM parameters were not persisted.",
        ]
    )

    text = "\n".join(lines)
    METRICS_LOG.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
