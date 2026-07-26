"""Stage 02 — chronological train/test split and expanding CV folds.

Input:
    - ``01_continuous/<run_id>/continuous_full.parquet``.

Output:
    - Development/test parquet files under ``02_splits/<run_id>``.
    - Expanding-window fold files used by Optuna tuning.
    - Split summary and manifest for reporting.

Important:
    - Forecasting uses time-based splits only; no random split is allowed.
    - Test is sealed until Stage 11 evaluation.
    - Expanding folds preserve temporal order so validation rows are always
      later than their corresponding training rows.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from forecasting_common import add_common_cli, artifact_dir, load_config, write_json


def _window(df: pd.DataFrame, ts_col: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df[ts_col] >= start) & (df[ts_col] <= end)].copy()


def run_split(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    in_path = artifact_dir(config, "01_continuous", rid) / "continuous_full.parquet"
    out_dir = artifact_dir(config, "02_splits", rid)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not in_path.exists():
        raise FileNotFoundError(f"Continuous grid not found: {in_path}")

    df = pd.read_parquet(in_path).sort_values([config.timestamp_col, config.site_col])
    timestamps = pd.Series(pd.to_datetime(df[config.timestamp_col]).dropna().sort_values().unique())
    test_ratio = float(config.raw["split"]["test_ratio"])
    n_splits = int(config.raw["split"]["n_splits"])
    test_start_idx = min(max(int(len(timestamps) * (1 - test_ratio)), n_splits + 2), len(timestamps) - 1)
    development_ts = timestamps.iloc[:test_start_idx].reset_index(drop=True)
    test_ts = timestamps.iloc[test_start_idx:].reset_index(drop=True)
    test_start = pd.Timestamp(test_ts.iloc[0])

    development = df[df[config.timestamp_col] < test_start].copy()
    test = df[df[config.timestamp_col] >= test_start].copy()
    development["partition"] = "development"
    test["partition"] = "test"

    paths: dict[str, Path] = {
        "development": out_dir / "development.parquet",
        "test": out_dir / "test.parquet",
        "manifest": out_dir / "split_manifest.json",
        "summary": out_dir / "split_summary.csv",
    }
    development.to_parquet(paths["development"], index=False)
    test.to_parquet(paths["test"], index=False)

    splitter = TimeSeriesSplit(n_splits=n_splits)
    fold_rows: list[dict[str, object]] = []
    for fold, (train_idx, val_idx) in enumerate(splitter.split(development_ts), start=1):
        train_ts = development_ts.iloc[train_idx]
        val_ts = development_ts.iloc[val_idx]
        fold_train = _window(df, config.timestamp_col, pd.Timestamp(train_ts.iloc[0]), pd.Timestamp(train_ts.iloc[-1]))
        fold_val = _window(df, config.timestamp_col, pd.Timestamp(val_ts.iloc[0]), pd.Timestamp(val_ts.iloc[-1]))
        fold_train["partition"] = "fold_train"
        fold_val["partition"] = "fold_val"
        fold_train["fold"] = fold
        fold_val["fold"] = fold
        fold_train_path = out_dir / f"fold_{fold}_train.parquet"
        fold_val_path = out_dir / f"fold_{fold}_val.parquet"
        fold_train.to_parquet(fold_train_path, index=False)
        fold_val.to_parquet(fold_val_path, index=False)
        fold_rows.extend(
            [
                {
                    "fold": fold,
                    "role": "train",
                    "rows": int(len(fold_train)),
                    "min_timestamp": fold_train[config.timestamp_col].min(),
                    "max_timestamp": fold_train[config.timestamp_col].max(),
                },
                {
                    "fold": fold,
                    "role": "val",
                    "rows": int(len(fold_val)),
                    "min_timestamp": fold_val[config.timestamp_col].min(),
                    "max_timestamp": fold_val[config.timestamp_col].max(),
                },
            ]
        )

    summary = pd.DataFrame(
        [
            {"partition": "development", "rows": int(len(development)), "min_timestamp": development[config.timestamp_col].min(), "max_timestamp": development[config.timestamp_col].max()},
            {"partition": "test", "rows": int(len(test)), "min_timestamp": test[config.timestamp_col].min(), "max_timestamp": test[config.timestamp_col].max()},
        ]
        + fold_rows
    )
    summary.to_csv(paths["summary"], index=False)
    write_json(
        {
            "run_id": rid,
            "source": str(in_path),
            "test_start_timestamp": str(test_start),
            "n_splits": n_splits,
            "test_ratio": test_ratio,
            "splitter": "sklearn.model_selection.TimeSeriesSplit on unique timestamps",
        },
        paths["manifest"],
    )
    print("Split complete")
    print(summary.to_string(index=False))
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create forecasting chronological splits.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_split(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
