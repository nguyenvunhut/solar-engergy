"""Direct long-horizon forecasting experiment for v2 preprocessing.

Local only. No cloud/database call. No test split.

This script trains separate LightGBM direct-forecast models:

- horizon 4 steps  = 1 hour ahead
- horizon 24 steps = 6 hours ahead
- horizon 96 steps = 24 hours ahead

Design:

- X(t): current site/time/weather features plus future timestamp features.
- y(t+h): future energy at the same site.
- No target lag/rolling features are used.
- Target rows marked by v2_exclude_from_loss_flag are excluded from training/eval.

Validation:

- Default uses the existing train/val temporal split.
- Optional ``--folds N`` runs additional blocked temporal folds inside the train split.
  This is not sklearn GroupKFold. For forecasting, random GroupKFold would leak time.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRAIN_PATH = PROJECT_ROOT / "data" / "model" / "train" / "v2_train.parquet"
VAL_PATH = PROJECT_ROOT / "data" / "model" / "val" / "v2_val.parquet"
REPORT_DIR = PROJECT_ROOT / "reports" / "ml_training_v2" / "direct_horizon"
MODEL_DIR = PROJECT_ROOT / "models" / "ml_training_v2" / "direct_horizon"

SITE_COL = "site_id"
TIMESTAMP_COL = "timestamp"
TARGET_COL = "energy_generated_kwh"
EXCLUDE_COL = "v2_exclude_from_loss_flag"
STEP_MINUTES = 15

BASE_FEATURES: tuple[str, ...] = (
    "v2_site_id_code",
    "v2_campus_name_code",
    "v2_location_name_code",
    "latitude",
    "longitude",
    "capacity_kw",
    "number_of_panels",
    "v2_capacity_per_panel",
    "v2_capacity_kw_missing_flag",
    "v2_number_of_panels_missing_flag",
    "v2_hour_sin",
    "v2_hour_cos",
    "v2_doy_sin",
    "v2_doy_cos",
    "v2_day_of_week",
    "v2_is_weekend",
    "v2_season_code",
    "shortwave_radiation",
    "direct_normal_irradiance",
    "diffuse_solar_radiation",
    "temperature_c",
    "cloud_cover_total",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "wind_speed",
    "precipitation_mm",
    "sunshine_duration",
    "weather_is_day",
    "weather_type_is_day",
    "v2_temp_x_shortwave",
    "v2_diffuse_ratio",
    "v2_dni_ratio",
    "v2_cloud_x_shortwave",
)

FUTURE_TIME_FEATURES: tuple[str, ...] = (
    "future_hour_sin",
    "future_hour_cos",
    "future_doy_sin",
    "future_doy_cos",
    "future_day_of_week",
    "future_is_weekend",
)


@dataclass(frozen=True)
class DirectHorizonConfig:
    train_path: Path = TRAIN_PATH
    val_path: Path = VAL_PATH
    report_dir: Path = REPORT_DIR
    model_dir: Path = MODEL_DIR
    horizons_steps: tuple[int, ...] = (4, 24, 96)
    n_estimators: int = 700
    learning_rate: float = 0.04
    num_leaves: int = 63
    min_child_samples: int = 200
    early_stopping_rounds: int = 80
    folds: int = 0
    random_state: int = 42


def load_split(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_parquet(path)
    required = [SITE_COL, TIMESTAMP_COL, TARGET_COL, EXCLUDE_COL]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")
    df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL], errors="coerce")
    return df.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)


def add_future_target_and_time(df: pd.DataFrame, horizon_steps: int) -> pd.DataFrame:
    out = df.copy()
    group = out.groupby(SITE_COL, observed=True)

    future_ts = group[TIMESTAMP_COL].shift(-horizon_steps)
    future_y = group[TARGET_COL].shift(-horizon_steps)
    future_exclude = group[EXCLUDE_COL].shift(-horizon_steps)
    future_gap_minutes = (future_ts - out[TIMESTAMP_COL]).dt.total_seconds() / 60.0
    expected_minutes = horizon_steps * STEP_MINUTES

    out["target_timestamp"] = future_ts
    out["target_energy_generated_kwh"] = future_y
    out["target_exclude_from_loss_flag"] = future_exclude.fillna(True).astype(bool)
    out["target_gap_minutes"] = future_gap_minutes
    out["target_is_continuous"] = future_gap_minutes.eq(expected_minutes)

    minute_of_day = future_ts.dt.hour * 60 + future_ts.dt.minute
    day_of_year = future_ts.dt.dayofyear
    out["future_hour_sin"] = np.sin(2 * np.pi * minute_of_day / 1440.0)
    out["future_hour_cos"] = np.cos(2 * np.pi * minute_of_day / 1440.0)
    out["future_doy_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    out["future_doy_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)
    out["future_day_of_week"] = future_ts.dt.dayofweek.astype("float64")
    out["future_is_weekend"] = out["future_day_of_week"].isin([5, 6]).astype("int8")
    return out


def build_xy(df: pd.DataFrame, horizon_steps: int) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, list[str]]:
    data = add_future_target_and_time(df, horizon_steps)
    current_exclude = data[EXCLUDE_COL].fillna(True).astype(bool)
    target_exclude = data["target_exclude_from_loss_flag"].fillna(True).astype(bool)
    mask = (
        data["target_is_continuous"].fillna(False)
        & data["target_energy_generated_kwh"].notna()
        & ~current_exclude
        & ~target_exclude
    )
    data = data.loc[mask].copy()

    feature_cols = [col for col in (*BASE_FEATURES, *FUTURE_TIME_FEATURES) if col in data.columns]
    x = data[feature_cols].copy()
    y = data["target_energy_generated_kwh"].astype("float64")
    return x, y, data, feature_cols


def regression_metrics(y_true: pd.Series, pred: np.ndarray) -> dict[str, float]:
    y = np.asarray(y_true, dtype="float64")
    p = np.asarray(pred, dtype="float64")
    denom = np.abs(y).sum()
    return {
        "mae": float(mean_absolute_error(y, p)),
        "rmse": float(mean_squared_error(y, p) ** 0.5),
        "r2": float(r2_score(y, p)),
        "wape": float(np.abs(y - p).sum() / denom) if denom > 0 else float("nan"),
    }


def make_model(config: DirectHorizonConfig) -> lgb.LGBMRegressor:
    return lgb.LGBMRegressor(
        objective="regression_l1",
        n_estimators=config.n_estimators,
        learning_rate=config.learning_rate,
        num_leaves=config.num_leaves,
        min_child_samples=config.min_child_samples,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_alpha=0.05,
        reg_lambda=0.2,
        random_state=config.random_state,
        n_jobs=-1,
        verbosity=-1,
    )


def train_model(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_val: pd.DataFrame,
    y_val: pd.Series,
    config: DirectHorizonConfig,
) -> lgb.LGBMRegressor:
    model = make_model(config)
    model.fit(
        x_train,
        y_train,
        eval_set=[(x_val, y_val)],
        eval_metric="l1",
        callbacks=[
            lgb.early_stopping(config.early_stopping_rounds, verbose=True),
            lgb.log_evaluation(period=100),
        ],
    )
    return model


def plot_horizon_window(eval_df: pd.DataFrame, horizon_label: str, output_dir: Path) -> None:
    site = eval_df[SITE_COL].value_counts().index[0]
    part = eval_df[eval_df[SITE_COL].eq(site)].sort_values("target_timestamp").copy()
    start = part["target_timestamp"].min()
    window = part[
        (part["target_timestamp"] >= start)
        & (part["target_timestamp"] < start + pd.Timedelta(days=10))
    ]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(window["target_timestamp"], window["target_energy_generated_kwh"], label="actual future", linewidth=1.1)
    ax.plot(window["target_timestamp"], window["prediction"], label=f"direct forecast {horizon_label}", linewidth=1.1)
    ax.set_title(f"Direct horizon forecast | {horizon_label} | site={site}")
    ax.set_xlabel("target timestamp")
    ax.set_ylabel(TARGET_COL)
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_dir / "figures" / f"v2_direct_{horizon_label}_actual_vs_pred.png")
    plt.close(fig)


def temporal_blocked_folds(df: pd.DataFrame, folds: int) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    if folds <= 1:
        return []
    unique_days = pd.Series(pd.to_datetime(df[TIMESTAMP_COL]).dt.normalize().dropna().unique()).sort_values()
    if len(unique_days) < folds + 1:
        return []
    blocks = np.array_split(unique_days.to_numpy(), folds + 1)
    windows: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for block in blocks[1:]:
        if len(block) == 0:
            continue
        windows.append((pd.Timestamp(block[0]), pd.Timestamp(block[-1]) + pd.Timedelta(days=1)))
    return windows


def run_blocked_cv(
    train_df: pd.DataFrame,
    horizon_steps: int,
    config: DirectHorizonConfig,
) -> pd.DataFrame:
    windows = temporal_blocked_folds(train_df, config.folds)
    rows: list[dict[str, Any]] = []
    if not windows:
        return pd.DataFrame(rows)

    horizon_label = f"{horizon_steps * STEP_MINUTES}min"
    for fold_idx, (val_start, val_end) in enumerate(windows, start=1):
        fold_train = train_df[train_df[TIMESTAMP_COL] < val_start].copy()
        fold_val = train_df[(train_df[TIMESTAMP_COL] >= val_start) & (train_df[TIMESTAMP_COL] < val_end)].copy()
        if fold_train.empty or fold_val.empty:
            continue
        x_train, y_train, _, train_cols = build_xy(fold_train, horizon_steps)
        x_val, y_val, _, val_cols = build_xy(fold_val, horizon_steps)
        common = [col for col in train_cols if col in val_cols]
        if x_train.empty or x_val.empty:
            continue
        model = train_model(x_train[common], y_train, x_val[common], y_val, config)
        pred = model.predict(x_val[common], num_iteration=model.best_iteration_)
        rows.append(
            {
                "horizon_label": horizon_label,
                "fold": fold_idx,
                "val_start": val_start,
                "val_end": val_end,
                "rows_train": len(x_train),
                "rows_val": len(x_val),
                **regression_metrics(y_val, pred),
            }
        )
    return pd.DataFrame(rows)


def run_direct_horizon(config: DirectHorizonConfig) -> dict[str, Path]:
    config.report_dir.mkdir(parents=True, exist_ok=True)
    (config.report_dir / "figures").mkdir(parents=True, exist_ok=True)
    config.model_dir.mkdir(parents=True, exist_ok=True)

    train_df = load_split(config.train_path)
    val_df = load_split(config.val_path)

    metric_rows: list[dict[str, Any]] = []
    importance_frames: list[pd.DataFrame] = []
    cv_frames: list[pd.DataFrame] = []

    for horizon_steps in config.horizons_steps:
        horizon_label = f"{horizon_steps * STEP_MINUTES}min"
        print(f"\nTraining direct horizon: {horizon_label}", flush=True)
        x_train, y_train, train_clean, train_cols = build_xy(train_df, horizon_steps)
        x_val, y_val, val_clean, val_cols = build_xy(val_df, horizon_steps)
        common = [col for col in train_cols if col in val_cols]
        x_train = x_train[common]
        x_val = x_val[common]
        print(f"rows train={len(x_train):,} val={len(x_val):,} features={len(common):,}", flush=True)

        model = train_model(x_train, y_train, x_val, y_val, config)
        pred = model.predict(x_val, num_iteration=model.best_iteration_)
        horizon_metrics = regression_metrics(y_val, pred)
        metric_rows.append(
            {
                "horizon_steps": horizon_steps,
                "horizon_minutes": horizon_steps * STEP_MINUTES,
                "horizon_label": horizon_label,
                "rows_train": len(x_train),
                "rows_val": len(x_val),
                "features": len(common),
                "best_iteration": int(model.best_iteration_ or config.n_estimators),
                **horizon_metrics,
            }
        )

        joblib.dump(model, config.model_dir / f"v2_direct_horizon_{horizon_label}.pkl")
        importance_frames.append(
            pd.DataFrame(
                {
                    "horizon_label": horizon_label,
                    "feature": common,
                    "importance_gain": model.booster_.feature_importance(importance_type="gain"),
                    "importance_split": model.booster_.feature_importance(importance_type="split"),
                }
            ).sort_values(["horizon_label", "importance_gain"], ascending=[True, False])
        )

        eval_df = val_clean[[SITE_COL, TIMESTAMP_COL, "target_timestamp", "target_energy_generated_kwh"]].copy()
        eval_df["prediction"] = pred
        eval_df["abs_error"] = (eval_df["target_energy_generated_kwh"] - eval_df["prediction"]).abs()
        eval_df.to_csv(config.report_dir / f"v2_direct_{horizon_label}_validation_predictions.csv", index=False)
        plot_horizon_window(eval_df, horizon_label, config.report_dir)

        if config.folds > 1:
            cv_frames.append(run_blocked_cv(train_df, horizon_steps, config))

    metrics_df = pd.DataFrame(metric_rows)
    importance_df = pd.concat(importance_frames, ignore_index=True)
    metrics_path = config.report_dir / "v2_direct_horizon_metrics.csv"
    importance_path = config.report_dir / "v2_direct_horizon_feature_importance.csv"
    metrics_df.to_csv(metrics_path, index=False)
    importance_df.to_csv(importance_path, index=False)

    cv_path = config.report_dir / "v2_direct_horizon_blocked_cv_metrics.csv"
    if cv_frames:
        cv_df = pd.concat(cv_frames, ignore_index=True)
        cv_df.to_csv(cv_path, index=False)
    else:
        cv_df = pd.DataFrame()

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(metrics_df["horizon_label"], metrics_df["mae"], marker="o", label="MAE")
    ax.plot(metrics_df["horizon_label"], metrics_df["rmse"], marker="o", label="RMSE")
    ax.set_title("Direct horizon validation error")
    ax.set_xlabel("Horizon")
    ax.set_ylabel("Error")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(config.report_dir / "figures" / "v2_direct_horizon_error.png")
    plt.close(fig)

    report = config.report_dir / "v2_direct_horizon_report.md"
    report.write_text(
        f"""# V2 Direct Long-Horizon Forecasting Report

Local-only. No cloud/database call. Test split was not used.

## Validation design

Main validation uses the existing temporal train/validation split.

This is not random `GroupKFold`. Random group folds are unsafe for forecasting because
they can train on future periods and validate on past periods. If `--folds` is set,
the script additionally runs blocked temporal folds inside the train split.

## Model design

For each row at time `t`, the model predicts future target `energy(t+h)`.

Features:

- current site/time/weather features;
- future timestamp cyclic features;
- no `v2_lag_*`;
- no `v2_rolling_*`;
- target continuity enforced: `target_timestamp - timestamp = horizon_steps * 15min`;
- current and target rows with `v2_exclude_from_loss_flag=true` are excluded.

Important limitation: this experiment uses current weather covariates. For a real
long-term operational forecast, these weather inputs should be replaced by weather
forecast features available at prediction time.

## Holdout validation metrics

```text
{metrics_df.to_string(index=False)}
```

## Blocked temporal CV metrics

```text
{cv_df.to_string(index=False) if not cv_df.empty else "Not run. Use --folds N to enable."}
```

## Top feature importance

```text
{importance_df.groupby("horizon_label").head(12).to_string(index=False)}
```

## Outputs

- `{metrics_path.relative_to(PROJECT_ROOT)}`
- `{importance_path.relative_to(PROJECT_ROOT)}`
- `{cv_path.relative_to(PROJECT_ROOT)}` if blocked CV is enabled
- `reports/ml_training_v2/direct_horizon/figures/`
- `models/ml_training_v2/direct_horizon/`
""",
        encoding="utf-8",
    )

    print("\n[DONE] Direct horizon forecasting completed", flush=True)
    print(metrics_df.to_string(index=False), flush=True)
    print("report:", report, flush=True)
    return {"report": report, "metrics": metrics_path, "importance": importance_path}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run direct long-horizon forecasting experiment.")
    parser.add_argument("--horizons", default="4,24,96", help="Comma-separated horizon steps; 15min per step.")
    parser.add_argument("--n-estimators", type=int, default=700)
    parser.add_argument("--folds", type=int, default=0, help="Optional blocked temporal CV folds inside train split.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    horizons = tuple(int(x.strip()) for x in args.horizons.split(",") if x.strip())
    run_direct_horizon(
        DirectHorizonConfig(
            horizons_steps=horizons,
            n_estimators=args.n_estimators,
            folds=args.folds,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
