"""V2 feature selection audit.

This is an audit, not the final feature selection decision.

Reads local feature parquet and writes:
    reports/ml_preprocessing_v2/v2_feature_missing_summary.csv
    reports/ml_preprocessing_v2/v2_high_correlation_pairs.csv
    reports/ml_preprocessing_v2/v2_feature_target_correlation.csv
    reports/ml_preprocessing_v2/v2_feature_selection_audit.md

No cloud/database connection.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "features" / "v2_features.parquet"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports" / "ml_preprocessing_v2"

TARGET_COL = "energy_generated_kwh"
TIMESTAMP_COL = "timestamp"
SITE_COL = "site_id"


@dataclass(frozen=True)
class FeatureSelectionAuditConfig:
    input_path: Path = DEFAULT_INPUT
    report_dir: Path = DEFAULT_REPORT_DIR
    sample_rows: int = 300_000
    correlation_threshold: float = 0.90
    random_state: int = 42


def load_feature_sample(config: FeatureSelectionAuditConfig) -> pd.DataFrame:
    if not config.input_path.exists():
        raise FileNotFoundError(f"Missing feature parquet: {config.input_path}")

    df = pd.read_parquet(config.input_path)
    if len(df) > config.sample_rows:
        df = df.sample(n=config.sample_rows, random_state=config.random_state)
    return df.reset_index(drop=True)


def numeric_feature_columns(df: pd.DataFrame) -> list[str]:
    numeric_cols = df.select_dtypes(include=["number", "bool", "boolean"]).columns.tolist()
    blocked = {
        "gen_id",
        "geo_id",
        "date_id",
        "time_id",
        "weather_id",
        "weather_type_id",
    }
    return [col for col in numeric_cols if col not in blocked]


def build_missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        missing = int(df[col].isna().sum())
        rows.append(
            {
                "column": col,
                "dtype": str(df[col].dtype),
                "missing_rows": missing,
                "missing_pct": missing / len(df) * 100 if len(df) else 0.0,
                "nunique": int(df[col].nunique(dropna=True)),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["missing_pct", "column"], ascending=[False, True]
    )


def build_high_correlation_pairs(
    df: pd.DataFrame,
    *,
    threshold: float,
) -> pd.DataFrame:
    cols = numeric_feature_columns(df)
    if TARGET_COL in cols:
        cols.remove(TARGET_COL)

    numeric = df[cols].astype("float64", copy=False)
    corr = numeric.corr(method="pearson").abs()
    pairs: list[dict[str, object]] = []

    columns = corr.columns.to_list()
    for i, left in enumerate(columns):
        for right in columns[i + 1 :]:
            value = corr.at[left, right]
            if pd.notna(value) and value >= threshold:
                pairs.append({"feature_a": left, "feature_b": right, "abs_corr": float(value)})

    return pd.DataFrame(pairs).sort_values("abs_corr", ascending=False)


def build_target_correlation(df: pd.DataFrame) -> pd.DataFrame:
    cols = numeric_feature_columns(df)
    if TARGET_COL not in df.columns:
        return pd.DataFrame()

    rows = []
    target = pd.to_numeric(df[TARGET_COL], errors="coerce")
    for col in cols:
        if col == TARGET_COL:
            continue
        series = pd.to_numeric(df[col], errors="coerce")
        corr = series.corr(target)
        rows.append(
            {
                "feature": col,
                "pearson_corr_with_target": float(corr) if pd.notna(corr) else np.nan,
                "abs_corr_with_target": float(abs(corr)) if pd.notna(corr) else np.nan,
                "missing_pct": float(series.isna().mean() * 100),
                "nunique": int(series.nunique(dropna=True)),
            }
        )
    return pd.DataFrame(rows).sort_values("abs_corr_with_target", ascending=False)


def write_feature_selection_report(
    *,
    config: FeatureSelectionAuditConfig,
    df: pd.DataFrame,
    missing_summary: pd.DataFrame,
    high_corr: pd.DataFrame,
    target_corr: pd.DataFrame,
) -> Path:
    report_path = config.report_dir / "v2_feature_selection_audit.md"

    def table(df: pd.DataFrame) -> str:
        if df.empty:
            return "_No rows._"
        return "```text\n" + df.to_string(index=False) + "\n```"

    constant_cols = missing_summary[missing_summary["nunique"] <= 1]["column"].tolist()
    very_missing = missing_summary[missing_summary["missing_pct"] >= 30][
        ["column", "missing_pct"]
    ].head(30)

    text = f"""# V2 Feature Selection Audit

This report is generated from local `v2_features.parquet`.

It is an audit artifact, not a final feature-selection decision.

## Scope

- Input: `{config.input_path}`
- Rows read for audit: {len(df):,}
- Correlation threshold: {config.correlation_threshold}
- Target: `{TARGET_COL}`

## Important interpretation

- High correlation does not automatically mean a feature must be removed.
- For tree-based models such as LightGBM, multicollinearity is usually less harmful than for linear regression.
- Remove a feature only when multiple signals agree: high correlation, high missingness or low usefulness, low model importance, weak SHAP contribution, and domain redundancy.
- Lag/rolling features must be interpreted carefully because they can dominate forecasting models and produce lagging predictions if overused.

## Constant or near-empty columns

Columns with `nunique <= 1` in the audit sample:

{constant_cols}

## Top high-missing columns

{table(very_missing)}

## High-correlation pairs

- Number of pairs with abs(corr) >= {config.correlation_threshold}: {len(high_corr):,}
- Full list: `v2_high_correlation_pairs.csv`

Top 30:

{table(high_corr.head(30)) if len(high_corr) else "No high-correlation pairs found."}

## Target correlation

Full list: `v2_feature_target_correlation.csv`

Top 30 by absolute Pearson correlation:

{table(target_corr.head(30)) if len(target_corr) else "No target correlation computed."}

## Recommendation for next stage

1. Keep all original columns in the feature parquet for audit.
2. For first LightGBM run, exclude obvious ID columns and raw text columns.
3. Use validation metrics + SHAP before removing weather features.
4. Do not use test set for feature selection.
"""
    report_path.write_text(text, encoding="utf-8")
    return report_path


def run_feature_selection_audit(config: FeatureSelectionAuditConfig) -> dict[str, Path]:
    config.report_dir.mkdir(parents=True, exist_ok=True)
    df = load_feature_sample(config)

    missing_summary = build_missing_summary(df)
    high_corr = build_high_correlation_pairs(df, threshold=config.correlation_threshold)
    target_corr = build_target_correlation(df)

    paths = {
        "missing_summary": config.report_dir / "v2_feature_missing_summary.csv",
        "high_correlation_pairs": config.report_dir / "v2_high_correlation_pairs.csv",
        "target_correlation": config.report_dir / "v2_feature_target_correlation.csv",
    }
    missing_summary.to_csv(paths["missing_summary"], index=False)
    high_corr.to_csv(paths["high_correlation_pairs"], index=False)
    target_corr.to_csv(paths["target_correlation"], index=False)

    report_path = write_feature_selection_report(
        config=config,
        df=df,
        missing_summary=missing_summary,
        high_corr=high_corr,
        target_corr=target_corr,
    )
    paths["report"] = report_path

    print("V2 feature selection audit completed")
    for key, path in paths.items():
        print(f"{key}: {path}")
    print(f"sample_rows: {len(df):,}")
    print(f"high_corr_pairs: {len(high_corr):,}")
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run V2 feature selection audit.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--sample-rows", type=int, default=300_000)
    parser.add_argument("--correlation-threshold", type=float, default=0.90)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_feature_selection_audit(
        FeatureSelectionAuditConfig(
            input_path=args.input,
            report_dir=args.report_dir,
            sample_rows=args.sample_rows,
            correlation_threshold=args.correlation_threshold,
            random_state=args.random_state,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
