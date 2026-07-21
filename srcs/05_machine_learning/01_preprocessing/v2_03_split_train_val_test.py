"""V2 time-series train/validation/test split.

Input mặc định:
    data/features/v2_features.parquet

Output mặc định:
    data/model/train/v2_train.parquet
    data/model/val/v2_val.parquet
    data/model/test/v2_test.parquet
    data/model/v2_split_summary.csv

Rule:
    - Không random split.
    - Test là đoạn thời gian cuối cùng, chỉ dùng cho đánh giá cuối.
    - Train/Val chính lấy từ fold cuối của expanding-window TimeSeriesSplit
      trên vùng train+validation.
    - Đồng thời xuất toàn bộ fold để validate từng fold theo Jira.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "features" / "v2_features.parquet"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "model"

SITE_COL = "site_id"
TIMESTAMP_COL = "timestamp"
TARGET_COL = "energy_generated_kwh"

SplitName = Literal["train", "val", "test"]


@dataclass(frozen=True)
class SplitConfig:
    """Configuration for v2 time-series splitting."""

    input_path: Path = DEFAULT_INPUT
    output_dir: Path = DEFAULT_OUTPUT_DIR
    train_ratio: float = 0.70  # kept for backward-compatible CLI/reporting
    val_ratio: float = 0.15  # kept for backward-compatible CLI/reporting
    test_ratio: float = 0.15
    n_splits: int = 5
    drop_rows_without_history: bool = False
    drop_rows_excluded_from_loss: bool = False


def _require_columns(df: pd.DataFrame, columns: list[str] | tuple[str, ...]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")


def load_features(path: str | Path = DEFAULT_INPUT) -> pd.DataFrame:
    """Load feature parquet."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input parquet not found: {path}")

    df = pd.read_parquet(path)
    _require_columns(df, [SITE_COL, TIMESTAMP_COL, TARGET_COL])
    df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL], errors="coerce")
    return df.sort_values([TIMESTAMP_COL, SITE_COL]).reset_index(drop=True)


def validate_split_config(test_ratio: float, n_splits: int) -> None:
    if not 0 < test_ratio < 1:
        raise ValueError(f"test_ratio must be between 0 and 1, got {test_ratio}")
    if n_splits < 2:
        raise ValueError(f"n_splits must be >= 2, got {n_splits}")


def _build_expanding_fold_boundaries(
    timestamps: pd.Series,
    *,
    test_ratio: float,
    n_splits: int,
) -> tuple[pd.Timestamp, list[dict[str, object]]]:
    """Build expanding-window fold boundaries on the pre-test time range.

    This is the time-series replacement for random K-Fold:

    - the final ``test_ratio`` of unique timestamps is held out as test;
    - the remaining timestamps are split into ``n_splits + 1`` ordered blocks;
    - fold i trains on all blocks before i and validates on block i.
    """

    validate_split_config(test_ratio, n_splits)
    if timestamps.empty:
        raise ValueError("No valid timestamps found")

    n_total = len(timestamps)
    test_start_idx = int(n_total * (1.0 - test_ratio))
    test_start_idx = min(max(test_start_idx, n_splits + 1), n_total - 1)
    test_start_ts = timestamps.iloc[test_start_idx]

    train_val_ts = timestamps.iloc[:test_start_idx]
    n_train_val = len(train_val_ts)
    if n_train_val < n_splits + 1:
        raise ValueError(
            f"Not enough timestamps for n_splits={n_splits}: "
            f"train_val timestamps={n_train_val}"
        )

    block_size = n_train_val // (n_splits + 1)
    if block_size <= 0:
        raise ValueError(f"Invalid block_size={block_size}")

    folds: list[dict[str, object]] = []
    for fold in range(1, n_splits + 1):
        val_start_idx = block_size * fold
        if fold == n_splits:
            val_end_idx = n_train_val - 1
        else:
            val_end_idx = block_size * (fold + 1) - 1

        folds.append(
            {
                "fold": fold,
                "train_start_ts": train_val_ts.iloc[0],
                "train_end_ts": train_val_ts.iloc[val_start_idx - 1],
                "val_start_ts": train_val_ts.iloc[val_start_idx],
                "val_end_ts": train_val_ts.iloc[val_end_idx],
            }
        )
    return test_start_ts, folds


def add_time_series_split_columns(
    df: pd.DataFrame,
    *,
    test_ratio: float = 0.15,
    n_splits: int = 5,
) -> pd.DataFrame:
    """Add ``v2_split`` using the last expanding-window fold.

    The final fold becomes the canonical train/val split used by existing
    training scripts. All fold membership is also stored in ``v2_time_series_fold``.
    """

    out = df.copy()
    timestamps = pd.Series(out[TIMESTAMP_COL].dropna().sort_values().unique())
    test_start_ts, folds = _build_expanding_fold_boundaries(
        timestamps,
        test_ratio=test_ratio,
        n_splits=n_splits,
    )
    final_fold = folds[-1]
    train_end_ts = final_fold["train_end_ts"]
    val_end_ts = final_fold["val_end_ts"]

    out["v2_split"] = "test"
    out.loc[out[TIMESTAMP_COL] <= train_end_ts, "v2_split"] = "train"
    out.loc[
        (out[TIMESTAMP_COL] > train_end_ts)
        & (out[TIMESTAMP_COL] <= val_end_ts)
        & (out[TIMESTAMP_COL] < test_start_ts),
        "v2_split",
    ] = "val"
    out.loc[out[TIMESTAMP_COL] >= test_start_ts, "v2_split"] = "test"

    out["v2_time_series_fold"] = pd.NA
    out["v2_fold_role"] = pd.NA
    for fold_info in folds:
        fold = int(fold_info["fold"])
        train_mask = (
            (out[TIMESTAMP_COL] >= fold_info["train_start_ts"])
            & (out[TIMESTAMP_COL] <= fold_info["train_end_ts"])
        )
        val_mask = (
            (out[TIMESTAMP_COL] >= fold_info["val_start_ts"])
            & (out[TIMESTAMP_COL] <= fold_info["val_end_ts"])
        )
        out.loc[train_mask, "v2_time_series_fold"] = fold
        out.loc[train_mask, "v2_fold_role"] = "train"
        out.loc[val_mask, "v2_time_series_fold"] = fold
        out.loc[val_mask, "v2_fold_role"] = "val"

    out["v2_n_time_series_splits"] = n_splits
    out["v2_train_end_timestamp"] = train_end_ts
    out["v2_val_end_timestamp"] = val_end_ts
    out["v2_test_start_timestamp"] = test_start_ts
    return out


def add_temporal_split_column(
    df: pd.DataFrame,
    *,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> pd.DataFrame:
    """Backward-compatible wrapper.

    The old fixed 70/15/15 holdout is intentionally replaced by TimeSeriesSplit
    style folds. ``train_ratio`` and ``val_ratio`` are accepted so older calls do
    not break, but the canonical split now comes from the last expanding fold.
    """

    _ = (train_ratio, val_ratio)
    return add_time_series_split_columns(df, test_ratio=test_ratio, n_splits=5)


def apply_split_filters(
    df: pd.DataFrame,
    *,
    drop_rows_without_history: bool = False,
    drop_rows_excluded_from_loss: bool = False,
) -> pd.DataFrame:
    """Optionally filter training-ready rows.

    Defaults keep rows for audit. If the team wants model-ready files only,
    enable filters explicitly.
    """

    out = df.copy()
    if drop_rows_without_history and "v2_has_complete_history_features" in out.columns:
        out = out[out["v2_has_complete_history_features"].fillna(False)]

    if drop_rows_excluded_from_loss and "v2_exclude_from_loss_flag" in out.columns:
        out = out[~out["v2_exclude_from_loss_flag"].fillna(False)]

    return out.reset_index(drop=True)


def build_split_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build split-level audit summary."""

    rows: list[dict[str, object]] = []
    for split_name, part in df.groupby("v2_split", observed=True):
        row: dict[str, object] = {
            "split": split_name,
            "rows": int(len(part)),
            "site_count": int(part[SITE_COL].nunique()),
            "min_timestamp": part[TIMESTAMP_COL].min(),
            "max_timestamp": part[TIMESTAMP_COL].max(),
            "target_null_rows": int(part[TARGET_COL].isna().sum()),
        }
        for col in (
            "v2_missing_weather_flag",
            "v2_outlier_flag",
            "v2_exclude_from_loss_flag",
            "v2_has_complete_history_features",
            "v2_gap_after_prev_flag",
        ):
            if col in part.columns:
                row[col] = int(part[col].fillna(False).sum())
        rows.append(row)

    summary = pd.DataFrame(rows)
    split_order = pd.CategoricalDtype(["train", "val", "test"], ordered=True)
    summary["split"] = summary["split"].astype(split_order)
    return summary.sort_values("split").reset_index(drop=True)


def build_fold_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build fold-level audit summary for the canonical final fold columns."""

    rows: list[dict[str, object]] = []
    fold_df = df[df["v2_time_series_fold"].notna()].copy()
    for (fold, role), part in fold_df.groupby(["v2_time_series_fold", "v2_fold_role"], observed=True):
        rows.append(
            {
                "fold": int(fold),
                "role": role,
                "rows": int(len(part)),
                "site_count": int(part[SITE_COL].nunique()),
                "min_timestamp": part[TIMESTAMP_COL].min(),
                "max_timestamp": part[TIMESTAMP_COL].max(),
                "target_null_rows": int(part[TARGET_COL].isna().sum()),
                "v2_exclude_from_loss_flag": int(part.get("v2_exclude_from_loss_flag", pd.Series(dtype=bool)).fillna(False).sum())
                if "v2_exclude_from_loss_flag" in part.columns
                else 0,
                "v2_has_complete_history_features": int(part.get("v2_has_complete_history_features", pd.Series(dtype=bool)).fillna(False).sum())
                if "v2_has_complete_history_features" in part.columns
                else 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["fold", "role"]).reset_index(drop=True)


def _summarize_part(
    *,
    fold: int,
    role: str,
    part: pd.DataFrame,
) -> dict[str, object]:
    return {
        "fold": fold,
        "role": role,
        "rows": int(len(part)),
        "site_count": int(part[SITE_COL].nunique()),
        "min_timestamp": part[TIMESTAMP_COL].min(),
        "max_timestamp": part[TIMESTAMP_COL].max(),
        "target_null_rows": int(part[TARGET_COL].isna().sum()),
        "v2_exclude_from_loss_flag": int(part["v2_exclude_from_loss_flag"].fillna(False).sum())
        if "v2_exclude_from_loss_flag" in part.columns
        else 0,
        "v2_has_complete_history_features": int(part["v2_has_complete_history_features"].fillna(False).sum())
        if "v2_has_complete_history_features" in part.columns
        else 0,
    }


def write_time_series_fold_files(df: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    """Write all expanding-window fold parquet files.

    A row can belong to the train side of multiple folds, so fold files cannot be
    represented faithfully by a single ``v2_time_series_fold`` column on ``df``.
    This function recomputes the fold boundaries and writes each fold explicitly.
    """

    n_splits = int(df["v2_n_time_series_splits"].dropna().iloc[0])
    test_start_ts = pd.Timestamp(df["v2_test_start_timestamp"].dropna().iloc[0])
    timestamps = pd.Series(df[TIMESTAMP_COL].dropna().sort_values().unique())
    train_val_timestamps = timestamps[timestamps < test_start_ts].reset_index(drop=True)
    if len(train_val_timestamps) < n_splits + 1:
        raise ValueError(
            f"Not enough train/val timestamps for n_splits={n_splits}: "
            f"{len(train_val_timestamps)}"
        )

    block_size = len(train_val_timestamps) // (n_splits + 1)
    folds_dir = output_dir / "time_series_folds"
    folds_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for fold in range(1, n_splits + 1):
        val_start_idx = block_size * fold
        val_end_idx = len(train_val_timestamps) - 1 if fold == n_splits else block_size * (fold + 1) - 1
        train_start_ts = train_val_timestamps.iloc[0]
        train_end_ts = train_val_timestamps.iloc[val_start_idx - 1]
        val_start_ts = train_val_timestamps.iloc[val_start_idx]
        val_end_ts = train_val_timestamps.iloc[val_end_idx]

        train_part = df[
            (df[TIMESTAMP_COL] >= train_start_ts)
            & (df[TIMESTAMP_COL] <= train_end_ts)
        ].copy()
        val_part = df[
            (df[TIMESTAMP_COL] >= val_start_ts)
            & (df[TIMESTAMP_COL] <= val_end_ts)
        ].copy()
        train_part["v2_cv_fold"] = fold
        train_part["v2_cv_role"] = "train"
        val_part["v2_cv_fold"] = fold
        val_part["v2_cv_role"] = "val"

        train_part.to_parquet(folds_dir / f"fold_{fold}_train.parquet", index=False)
        val_part.to_parquet(folds_dir / f"fold_{fold}_val.parquet", index=False)
        rows.append(_summarize_part(fold=fold, role="train", part=train_part))
        rows.append(_summarize_part(fold=fold, role="val", part=val_part))

    return pd.DataFrame(rows).sort_values(["fold", "role"]).reset_index(drop=True)


def write_split_files(df: pd.DataFrame, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
    """Write train/val/test parquet files, time-series folds, and summaries."""

    output_dir = Path(output_dir)
    paths = {
        "train": output_dir / "train" / "v2_train.parquet",
        "val": output_dir / "val" / "v2_val.parquet",
        "test": output_dir / "test" / "v2_test.parquet",
    }

    for split_name, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        df[df["v2_split"] == split_name].to_parquet(path, index=False)

    summary = build_split_summary(df)
    summary_path = output_dir / "v2_split_summary.csv"
    summary.to_csv(summary_path, index=False)

    fold_summary = write_time_series_fold_files(df, output_dir)
    fold_summary_path = output_dir / "v2_time_series_fold_summary.csv"
    fold_summary.to_csv(fold_summary_path, index=False)

    print("V2 TimeSeriesSplit completed")
    for split_name, path in paths.items():
        print(f"{split_name}: {path}")
    print(f"summary: {summary_path}")
    print(summary.to_string(index=False))
    print(f"fold_summary: {fold_summary_path}")
    print(fold_summary.to_string(index=False))


def run_temporal_split(config: SplitConfig) -> pd.DataFrame:
    """Load features, split, optionally filter, write outputs."""

    df = load_features(config.input_path)
    df = add_time_series_split_columns(
        df,
        test_ratio=config.test_ratio,
        n_splits=config.n_splits,
    )
    df = apply_split_filters(
        df,
        drop_rows_without_history=config.drop_rows_without_history,
        drop_rows_excluded_from_loss=config.drop_rows_excluded_from_loss,
    )
    write_split_files(df, config.output_dir)
    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v2 temporal train/val/test split.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--drop-rows-without-history", action="store_true")
    parser.add_argument("--drop-rows-excluded-from-loss", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = SplitConfig(
        input_path=args.input,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        n_splits=args.n_splits,
        drop_rows_without_history=args.drop_rows_without_history,
        drop_rows_excluded_from_loss=args.drop_rows_excluded_from_loss,
    )
    run_temporal_split(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
