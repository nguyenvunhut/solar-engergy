"""Audit V2 preprocessing outputs.

Reads local parquet files only. No database/cloud connection.

Outputs:
    reports/ml_preprocessing_v2/v2_audit_report.md
    reports/ml_preprocessing_v2/v2_gap_events.csv
    reports/ml_preprocessing_v2/v2_weather_missing_summary.csv
    reports/ml_preprocessing_v2/v2_outlier_summary_by_split.csv
    reports/ml_preprocessing_v2/v2_hour_minus_one_summary.csv
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


PROJECT_ROOT = Path(__file__).resolve().parents[3]
QUALITY_PATH = PROJECT_ROOT / "data" / "preprocessing" / "v2_quality_checked.parquet"
FEATURE_PATH = PROJECT_ROOT / "data" / "features" / "v2_features.parquet"
SPLIT_SUMMARY_PATH = PROJECT_ROOT / "data" / "model" / "v2_split_summary.csv"
TRAIN_PATH = PROJECT_ROOT / "data" / "model" / "train" / "v2_train.parquet"
VAL_PATH = PROJECT_ROOT / "data" / "model" / "val" / "v2_val.parquet"
TEST_PATH = PROJECT_ROOT / "data" / "model" / "test" / "v2_test.parquet"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports" / "ml_preprocessing_v2"

SITE_COL = "site_id"
TIMESTAMP_COL = "timestamp"
TARGET_COL = "energy_generated_kwh"


@dataclass(frozen=True)
class AuditConfig:
    quality_path: Path = QUALITY_PATH
    feature_path: Path = FEATURE_PATH
    split_summary_path: Path = SPLIT_SUMMARY_PATH
    train_path: Path = TRAIN_PATH
    val_path: Path = VAL_PATH
    test_path: Path = TEST_PATH
    report_dir: Path = DEFAULT_REPORT_DIR


def _read_parquet(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_parquet(path, columns=columns)


def _bool_sum(df: pd.DataFrame, col: str) -> int:
    if col not in df.columns:
        return 0
    return int(df[col].fillna(False).sum())


def build_gap_events(df: pd.DataFrame) -> pd.DataFrame:
    data = df[[SITE_COL, TIMESTAMP_COL, "v2_gap_from_prev_minutes", "v2_gap_after_prev_flag"]].copy()
    data[TIMESTAMP_COL] = pd.to_datetime(data[TIMESTAMP_COL], errors="coerce")
    data = data.sort_values([SITE_COL, TIMESTAMP_COL])
    data["gap_from_timestamp"] = data.groupby(SITE_COL, observed=True)[TIMESTAMP_COL].shift(1)
    gap = data[data["v2_gap_after_prev_flag"].fillna(False)].copy()
    gap["estimated_missing_15min_slots"] = (
        (gap["v2_gap_from_prev_minutes"] / 15.0 - 1).round().clip(lower=0).astype("int64")
    )
    return gap[
        [
            SITE_COL,
            "gap_from_timestamp",
            TIMESTAMP_COL,
            "v2_gap_from_prev_minutes",
            "estimated_missing_15min_slots",
        ]
    ].rename(columns={TIMESTAMP_COL: "gap_to_timestamp"})


def build_weather_missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data[TIMESTAMP_COL] = pd.to_datetime(data[TIMESTAMP_COL], errors="coerce")
    data["month"] = data[TIMESTAMP_COL].dt.to_period("M").astype(str)
    if "weather_join_method" not in data.columns:
        data["weather_join_method"] = "<missing_column>"

    summary = (
        data.groupby(["month", "weather_join_method"], dropna=False, observed=True)
        .agg(
            rows=(SITE_COL, "size"),
            missing_weather_rows=("v2_missing_weather_flag", lambda s: int(s.fillna(False).sum())),
        )
        .reset_index()
    )
    summary["missing_weather_pct"] = summary["missing_weather_rows"] / summary["rows"] * 100
    return summary


def build_hour_minus_one_summary(df: pd.DataFrame) -> pd.DataFrame:
    if "v2_hour_bucket_raw" not in df.columns:
        return pd.DataFrame()
    data = df[df["v2_hour_bucket_raw"].eq(-1)].copy()
    if data.empty:
        return pd.DataFrame(
            [{"rows": 0, "positive_energy_rows": 0, "energy_sum": 0.0, "outlier_rows": 0}]
        )
    return pd.DataFrame(
        [
            {
                "rows": int(len(data)),
                "min_timestamp": data[TIMESTAMP_COL].min(),
                "max_timestamp": data[TIMESTAMP_COL].max(),
                "positive_energy_rows": int((data[TARGET_COL].fillna(0) > 0).sum()),
                "energy_sum": float(data[TARGET_COL].fillna(0).sum()),
                "outlier_rows": _bool_sum(data, "v2_outlier_flag"),
            }
        ]
    )


def build_night_clamp_summary(df: pd.DataFrame) -> pd.DataFrame:
    data = df[[TIMESTAMP_COL, TARGET_COL]].copy()
    data[TIMESTAMP_COL] = pd.to_datetime(data[TIMESTAMP_COL], errors="coerce")
    hour = data[TIMESTAMP_COL].dt.hour
    minute = data[TIMESTAMP_COL].dt.minute
    strict_night = (hour >= 19) | (hour < 5) | ((hour == 5) & (minute < 30))
    night = data[strict_night]
    return pd.DataFrame(
        [
            {
                "strict_night_rows": int(len(night)),
                "strict_night_positive_rows": int((night[TARGET_COL].fillna(0) > 0).sum()),
                "strict_night_energy_sum": float(night[TARGET_COL].fillna(0).sum()),
                "strict_night_max_energy": float(night[TARGET_COL].max()) if len(night) else 0.0,
            }
        ]
    )


def build_outlier_summary_by_split(paths: dict[str, Path]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for split, path in paths.items():
        df = _read_parquet(
            path,
            columns=[
                SITE_COL,
                TIMESTAMP_COL,
                TARGET_COL,
                "v2_outlier_flag",
                "gmm_if_outlier_reason",
                "v2_exclude_from_loss_flag",
            ],
        )
        df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL], errors="coerce")
        outliers = df["v2_outlier_flag"].fillna(False)
        rows.append(
            {
                "split": split,
                "rows": int(len(df)),
                "site_count": int(df[SITE_COL].nunique()),
                "outlier_rows": int(outliers.sum()),
                "outlier_pct": float(outliers.mean() * 100),
                "exclude_from_loss_rows": _bool_sum(df, "v2_exclude_from_loss_flag"),
                "reason_distinct": int(df.loc[outliers, "gmm_if_outlier_reason"].nunique(dropna=True)),
            }
        )
    return pd.DataFrame(rows)


def write_report(
    *,
    config: AuditConfig,
    quality: pd.DataFrame,
    feature: pd.DataFrame,
    split_summary: pd.DataFrame,
    gap_events: pd.DataFrame,
    weather_summary: pd.DataFrame,
    hour_minus_one: pd.DataFrame,
    night_summary: pd.DataFrame,
    outlier_summary: pd.DataFrame,
) -> Path:
    report_path = config.report_dir / "v2_audit_report.md"

    def table(df: pd.DataFrame) -> str:
        if df.empty:
            return "_No rows._"
        return "```text\n" + df.to_string(index=False) + "\n```"

    max_gap = float(gap_events["v2_gap_from_prev_minutes"].max()) if len(gap_events) else 0.0
    missing_slots = int(gap_events["estimated_missing_15min_slots"].sum()) if len(gap_events) else 0
    weather_missing = _bool_sum(quality, "v2_missing_weather_flag")
    outlier_rows = _bool_sum(quality, "v2_outlier_flag")
    complete_history = _bool_sum(feature, "v2_has_complete_history_features")
    feature_schema_names = pq.read_schema(config.feature_path).names
    feature_total_columns = len(feature_schema_names)
    feature_v2_columns = len([name for name in feature_schema_names if name.startswith("v2_")])

    text = f"""# V2 ML Preprocessing Audit Report

Generated from local files only. No cloud/database call.

## Input / Output files

- Quality input/output: `{config.quality_path}`
- Feature output: `{config.feature_path}`
- Split summary: `{config.split_summary_path}`

## Overall quality

- Rows: {len(quality):,}
- Sites: {quality[SITE_COL].nunique():,}
- Time range: {quality[TIMESTAMP_COL].min()} → {quality[TIMESTAMP_COL].max()}
- Duplicate key rows: {_bool_sum(quality, "v2_duplicate_key_flag"):,}
- Missing weather rows: {weather_missing:,}
- Missing target rows: {_bool_sum(quality, "v2_missing_target_flag"):,}
- Outlier rows: {outlier_rows:,}
- Exclude-from-loss rows: {_bool_sum(quality, "v2_exclude_from_loss_flag"):,}

## Time gap audit

- Gap events: {len(gap_events):,}
- Affected sites: {gap_events[SITE_COL].nunique() if len(gap_events) else 0:,}
- Max gap minutes: {max_gap:,.1f}
- Estimated missing 15-minute slots: {missing_slots:,}

Interpretation:

- Gaps are not filled by this pipeline.
- Lag/rolling features are set to null when the required history crosses a gap.
- Training code should either drop rows without complete lag/rolling history or use models/features that do not require those columns.

## Night clamp audit

{table(night_summary)}

Interpretation:

- If `strict_night_positive_rows = 0`, night generation has already been clamped to zero.

## Hour -1 audit

{table(hour_minus_one)}

Interpretation:

- `hour = -1` comes from hourly bucket shift for 00:00.
- Do not use raw `hour=-1` as ordinal feature. Use cyclic timestamp features or `v2_hour_bucket_model` where -1 is mapped to 23.

## Feature engineering

- Total feature dataframe columns: {feature_total_columns:,}
- V2-prefixed feature columns: {feature_v2_columns:,}
- Rows with complete leakage-safe lag/rolling history: {complete_history:,}

## Split summary

{table(split_summary)}

## Outlier summary by split

{table(outlier_summary)}

## Generated CSV files

- `v2_gap_events.csv`
- `v2_weather_missing_summary.csv`
- `v2_outlier_summary_by_split.csv`
- `v2_hour_minus_one_summary.csv`
- `v2_night_clamp_summary.csv`
"""
    report_path.write_text(text, encoding="utf-8")
    return report_path


def run_audit(config: AuditConfig) -> dict[str, Path]:
    config.report_dir.mkdir(parents=True, exist_ok=True)

    quality_cols = [
        SITE_COL,
        TIMESTAMP_COL,
        TARGET_COL,
        "weather_join_method",
        "v2_missing_weather_flag",
        "v2_missing_target_flag",
        "v2_duplicate_key_flag",
        "v2_outlier_flag",
        "v2_exclude_from_loss_flag",
        "v2_gap_from_prev_minutes",
        "v2_gap_after_prev_flag",
        "v2_hour_bucket_raw",
    ]
    quality = _read_parquet(config.quality_path, columns=quality_cols)
    quality[TIMESTAMP_COL] = pd.to_datetime(quality[TIMESTAMP_COL], errors="coerce")

    feature = _read_parquet(
        config.feature_path,
        columns=[SITE_COL, TIMESTAMP_COL, "v2_has_complete_history_features"],
    )
    feature[TIMESTAMP_COL] = pd.to_datetime(feature[TIMESTAMP_COL], errors="coerce")

    split_summary = pd.read_csv(config.split_summary_path)
    gap_events = build_gap_events(quality)
    weather_summary = build_weather_missing_summary(quality)
    hour_minus_one = build_hour_minus_one_summary(quality)
    night_summary = build_night_clamp_summary(quality)
    outlier_summary = build_outlier_summary_by_split(
        {"train": config.train_path, "val": config.val_path, "test": config.test_path}
    )

    paths = {
        "gap_events": config.report_dir / "v2_gap_events.csv",
        "weather_missing": config.report_dir / "v2_weather_missing_summary.csv",
        "outlier_by_split": config.report_dir / "v2_outlier_summary_by_split.csv",
        "hour_minus_one": config.report_dir / "v2_hour_minus_one_summary.csv",
        "night_clamp": config.report_dir / "v2_night_clamp_summary.csv",
    }
    gap_events.to_csv(paths["gap_events"], index=False)
    weather_summary.to_csv(paths["weather_missing"], index=False)
    outlier_summary.to_csv(paths["outlier_by_split"], index=False)
    hour_minus_one.to_csv(paths["hour_minus_one"], index=False)
    night_summary.to_csv(paths["night_clamp"], index=False)

    report_path = write_report(
        config=config,
        quality=quality,
        feature=feature,
        split_summary=split_summary,
        gap_events=gap_events,
        weather_summary=weather_summary,
        hour_minus_one=hour_minus_one,
        night_summary=night_summary,
        outlier_summary=outlier_summary,
    )
    paths["report"] = report_path

    print("V2 preprocessing audit completed")
    for key, path in paths.items():
        print(f"{key}: {path}")
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit local V2 preprocessing outputs.")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_audit(AuditConfig(report_dir=args.report_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
