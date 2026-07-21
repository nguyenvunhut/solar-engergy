"""Train and validate a V2 LightGBM forecasting model.

Local-only script. It does not connect to Supabase/cloud and does not touch the
test split. Test remains reserved for final evaluation after model selection.

Inputs:
    data/model/train/v2_train.parquet
    data/model/val/v2_val.parquet

Outputs:
    reports/ml_training_v2/lightgbm_v2/
        v2_lightgbm_validation_report.md
        v2_lightgbm_overall_metrics.csv
        v2_lightgbm_metrics_by_site.csv
        v2_lightgbm_metrics_by_hour.csv
        v2_lightgbm_feature_importance.csv
        figures/*.png
    models/ml_training_v2/v2_lightgbm.pkl
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRAIN_PATH = PROJECT_ROOT / "data" / "model" / "train" / "v2_train.parquet"
VAL_PATH = PROJECT_ROOT / "data" / "model" / "val" / "v2_val.parquet"
FOLDS_DIR = PROJECT_ROOT / "data" / "model" / "time_series_folds"
REPORT_DIR = PROJECT_ROOT / "reports" / "ml_training_v2" / "lightgbm_v2"
MODEL_DIR = PROJECT_ROOT / "models" / "ml_training_v2"

TARGET_COL = "energy_generated_kwh"
TIMESTAMP_COL = "timestamp"
SITE_COL = "site_id"
BASELINE_COL = "v2_lag_1"

FEATURE_COLS: tuple[str, ...] = (
    # site / spatial
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
    # time
    "v2_hour_sin",
    "v2_hour_cos",
    "v2_doy_sin",
    "v2_doy_cos",
    "v2_day_of_week",
    "v2_is_weekend",
    "v2_season_code",
    "v2_hour_bucket_model",
    # weather
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
    # weather interactions
    "v2_temp_x_shortwave",
    "v2_diffuse_ratio",
    "v2_dni_ratio",
    "v2_cloud_x_shortwave",
    # leakage-safe target history
    "v2_lag_1",
    "v2_lag_4",
    "v2_lag_96",
    "v2_rolling_mean_4",
    "v2_rolling_std_4",
    "v2_rolling_min_4",
    "v2_rolling_max_4",
    "v2_rolling_mean_12",
    "v2_rolling_std_12",
    "v2_rolling_min_12",
    "v2_rolling_max_12",
)


@dataclass(frozen=True)
class TrainConfig:
    train_path: Path = TRAIN_PATH
    val_path: Path = VAL_PATH
    folds_dir: Path = FOLDS_DIR
    report_dir: Path = REPORT_DIR
    model_dir: Path = MODEL_DIR
    validate_folds: bool = True
    max_train_rows: int | None = None
    random_state: int = 42
    n_estimators: int = 1200
    learning_rate: float = 0.04
    num_leaves: int = 63
    min_child_samples: int = 200
    subsample: float = 0.9
    colsample_bytree: float = 0.9
    reg_alpha: float = 0.05
    reg_lambda: float = 0.2
    early_stopping_rounds: int = 80


def _required_columns() -> list[str]:
    base = [
        SITE_COL,
        TIMESTAMP_COL,
        TARGET_COL,
        "v2_split",
        "v2_exclude_from_loss_flag",
        "v2_has_complete_history_features",
        "v2_outlier_flag",
        "v2_missing_weather_flag",
    ]
    return sorted(set(base + list(FEATURE_COLS)))


def load_split(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing split parquet: {path}")

    columns = _required_columns()
    df = pd.read_parquet(path, columns=[c for c in columns if c])
    df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL], errors="coerce")
    return df


def build_training_mask(df: pd.DataFrame) -> pd.Series:
    """Rows allowed in model loss/eval."""

    mask = df[TARGET_COL].notna()
    if "v2_exclude_from_loss_flag" in df.columns:
        mask &= ~df["v2_exclude_from_loss_flag"].fillna(False)
    if "v2_has_complete_history_features" in df.columns:
        mask &= df["v2_has_complete_history_features"].fillna(False)
    if BASELINE_COL in df.columns:
        mask &= df[BASELINE_COL].notna()
    return mask


def prepare_xy(
    df: pd.DataFrame,
    *,
    max_rows: int | None = None,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    mask = build_training_mask(df)
    clean = df.loc[mask].copy()

    if max_rows is not None and len(clean) > max_rows:
        clean = clean.sample(n=max_rows, random_state=random_state).sort_values(
            [TIMESTAMP_COL, SITE_COL]
        )

    available_features = [col for col in FEATURE_COLS if col in clean.columns]
    x = clean[available_features].copy()
    y = clean[TARGET_COL].astype("float64")
    return x, y, clean


def regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    y_true_arr = np.asarray(y_true, dtype="float64")
    y_pred_arr = np.asarray(y_pred, dtype="float64")
    mae = mean_absolute_error(y_true_arr, y_pred_arr)
    rmse = mean_squared_error(y_true_arr, y_pred_arr) ** 0.5
    r2 = r2_score(y_true_arr, y_pred_arr)
    denom = np.abs(y_true_arr).sum()
    wape = np.abs(y_true_arr - y_pred_arr).sum() / denom if denom > 0 else np.nan
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "wape": float(wape),
    }


def metrics_by_group(
    df: pd.DataFrame,
    *,
    y_col: str,
    pred_col: str,
    group_col: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for group_value, part in df.groupby(group_col, observed=True):
        if len(part) < 2:
            continue
        m = regression_metrics(part[y_col], part[pred_col].to_numpy())
        rows.append({"group": group_value, "rows": len(part), **m})
    return pd.DataFrame(rows).sort_values("mae", ascending=False)


def train_lightgbm(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_val: pd.DataFrame,
    y_val: pd.Series,
    config: TrainConfig,
) -> lgb.LGBMRegressor:
    model = lgb.LGBMRegressor(
        objective="regression_l1",
        n_estimators=config.n_estimators,
        learning_rate=config.learning_rate,
        num_leaves=config.num_leaves,
        min_child_samples=config.min_child_samples,
        subsample=config.subsample,
        colsample_bytree=config.colsample_bytree,
        reg_alpha=config.reg_alpha,
        reg_lambda=config.reg_lambda,
        random_state=config.random_state,
        n_jobs=-1,
        verbosity=-1,
    )
    model.fit(
        x_train,
        y_train,
        eval_set=[(x_val, y_val)],
        eval_metric="l1",
        callbacks=[
            lgb.early_stopping(config.early_stopping_rounds, verbose=True),
            lgb.log_evaluation(period=50),
        ],
    )
    return model


def plot_feature_importance(importance: pd.DataFrame, path: Path) -> None:
    top = importance.head(30).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 9))
    ax.barh(top["feature"], top["importance_gain"])
    ax.set_title("LightGBM feature importance by gain — top 30")
    ax.set_xlabel("Gain")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_actual_vs_pred(val_eval: pd.DataFrame, path: Path) -> None:
    # Choose site with most validation rows and plot first 7 days of that site.
    site = val_eval[SITE_COL].value_counts().index[0]
    local = val_eval[val_eval[SITE_COL].eq(site)].sort_values(TIMESTAMP_COL).copy()
    start = local[TIMESTAMP_COL].min()
    end = start + pd.Timedelta(days=7)
    local = local[(local[TIMESTAMP_COL] >= start) & (local[TIMESTAMP_COL] < end)]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(local[TIMESTAMP_COL], local[TARGET_COL], label="actual", linewidth=1.2)
    ax.plot(local[TIMESTAMP_COL], local["prediction"], label="prediction", linewidth=1.2)
    ax.plot(local[TIMESTAMP_COL], local[BASELINE_COL], label="baseline lag_1", linewidth=1.0, alpha=0.7)
    ax.set_title(f"Validation actual vs prediction | site={site} | first 7 days")
    ax.set_xlabel("timestamp")
    ax.set_ylabel(TARGET_COL)
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_residual_by_hour(val_eval: pd.DataFrame, path: Path) -> None:
    data = val_eval.copy()
    data["hour"] = data[TIMESTAMP_COL].dt.hour
    data["residual"] = data[TARGET_COL] - data["prediction"]
    hourly = data.groupby("hour", observed=True)["residual"].agg(["mean", "median", "std"]).reset_index()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(hourly["hour"], hourly["mean"], marker="o", label="mean residual")
    ax.plot(hourly["hour"], hourly["median"], marker="o", label="median residual")
    ax.fill_between(
        hourly["hour"],
        hourly["mean"] - hourly["std"],
        hourly["mean"] + hourly["std"],
        alpha=0.18,
        label="±1 std",
    )
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title("Validation residual by hour")
    ax.set_xlabel("Hour")
    ax.set_ylabel("actual - prediction")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_scatter_actual_pred(val_eval: pd.DataFrame, path: Path, *, max_points: int = 50_000) -> None:
    data = val_eval
    if len(data) > max_points:
        data = data.sample(n=max_points, random_state=42)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.scatter(data[TARGET_COL], data["prediction"], s=3, alpha=0.18)
    lim = max(float(data[TARGET_COL].max()), float(data["prediction"].max()))
    ax.plot([0, lim], [0, lim], color="red", linewidth=1)
    ax.set_title("Validation actual vs prediction scatter")
    ax.set_xlabel("actual")
    ax.set_ylabel("prediction")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_time_series_fold_metrics(fold_metrics: pd.DataFrame, path: Path) -> None:
    if fold_metrics.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(fold_metrics["fold"], fold_metrics["mae"], marker="o", label="MAE")
    ax.plot(fold_metrics["fold"], fold_metrics["rmse"], marker="o", label="RMSE")
    ax.set_title("TimeSeriesSplit validation metrics by fold")
    ax.set_xlabel("Fold")
    ax.set_ylabel("Error")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def discover_time_series_folds(folds_dir: Path) -> list[tuple[int, Path, Path]]:
    """Return available expanding-window TimeSeriesSplit fold paths."""

    if not folds_dir.exists():
        return []
    folds: list[tuple[int, Path, Path]] = []
    for train_path in sorted(folds_dir.glob("fold_*_train.parquet")):
        try:
            fold = int(train_path.stem.split("_")[1])
        except (IndexError, ValueError):
            continue
        val_path = folds_dir / f"fold_{fold}_val.parquet"
        if val_path.exists():
            folds.append((fold, train_path, val_path))
    return folds


def run_time_series_fold_validation(config: TrainConfig, figures_dir: Path) -> pd.DataFrame:
    """Train and validate the same short-term model on every time-series fold.

    This satisfies Jira's "Validate trên từng fold" requirement. Test split is
    not touched.
    """

    folds = discover_time_series_folds(config.folds_dir)
    rows: list[dict[str, object]] = []
    if not folds or not config.validate_folds:
        return pd.DataFrame(rows)

    print("\nRunning TimeSeriesSplit fold validation...")
    for fold, train_path, val_path in folds:
        print(f"\n[Fold {fold}] train={train_path.name} val={val_path.name}")
        fold_train_df = load_split(train_path)
        fold_val_df = load_split(val_path)
        x_train, y_train, train_clean = prepare_xy(
            fold_train_df,
            max_rows=config.max_train_rows,
            random_state=config.random_state,
        )
        x_val, y_val, val_clean = prepare_xy(
            fold_val_df,
            max_rows=None,
            random_state=config.random_state,
        )
        feature_cols = [col for col in x_train.columns if col in x_val.columns]
        x_train = x_train[feature_cols]
        x_val = x_val[feature_cols]
        print(f"[Fold {fold}] rows train={len(x_train):,} val={len(x_val):,} features={len(feature_cols):,}")

        model = train_lightgbm(x_train, y_train, x_val, y_val, config)
        pred = model.predict(x_val, num_iteration=model.best_iteration_)
        baseline = val_clean[BASELINE_COL].astype("float64").to_numpy()
        model_metrics = regression_metrics(y_val, pred)
        baseline_metrics = regression_metrics(y_val, baseline)
        rows.append(
            {
                "fold": fold,
                "train_start": train_clean[TIMESTAMP_COL].min(),
                "train_end": train_clean[TIMESTAMP_COL].max(),
                "val_start": val_clean[TIMESTAMP_COL].min(),
                "val_end": val_clean[TIMESTAMP_COL].max(),
                "rows_train": len(x_train),
                "rows_val": len(x_val),
                "feature_count": len(feature_cols),
                "best_iteration": int(model.best_iteration_ or config.n_estimators),
                **model_metrics,
                "baseline_mae": baseline_metrics["mae"],
                "baseline_rmse": baseline_metrics["rmse"],
                "forecast_skill_mae_vs_lag1": float(1.0 - model_metrics["mae"] / baseline_metrics["mae"])
                if baseline_metrics["mae"] > 0
                else float("nan"),
                "forecast_skill_rmse_vs_lag1": float(1.0 - model_metrics["rmse"] / baseline_metrics["rmse"])
                if baseline_metrics["rmse"] > 0
                else float("nan"),
            }
        )

    fold_metrics = pd.DataFrame(rows)
    plot_time_series_fold_metrics(
        fold_metrics,
        figures_dir / "v2_lightgbm_time_series_fold_metrics.png",
    )
    return fold_metrics


def write_report(
    *,
    config: TrainConfig,
    train_clean: pd.DataFrame,
    val_eval: pd.DataFrame,
    overall_metrics: pd.DataFrame,
    fold_metrics: pd.DataFrame,
    importance: pd.DataFrame,
    report_path: Path,
) -> None:
    best_iter = overall_metrics.loc[0, "best_iteration"]
    text = f"""# V2 LightGBM Validation Report

Local-only training. No cloud/database call. Test split was not used.

## Data handling

- Train rows after quality/history/outlier mask: {len(train_clean):,}
- Validation rows after quality/history/outlier mask: {len(val_eval):,}
- Excluded rows are controlled by `v2_exclude_from_loss_flag`.
- Rows crossing time gaps are not converted to outliers; their lag/rolling features are null and are excluded from this first lag-based model by `v2_has_complete_history_features`.

## Model

- Algorithm: LightGBM `LGBMRegressor`
- Objective: `regression_l1`
- Best iteration: {best_iter}
- Test set: not used

## TimeSeriesSplit fold validation

Expanding-window folds are generated by `v2_03_split_train_val_test.py`.
This replaces random K-Fold for the forecasting problem.

```text
{fold_metrics.to_string(index=False) if not fold_metrics.empty else "Fold validation not run."}
```

## Metrics

```text
{overall_metrics.to_string(index=False)}
```

## Top 30 feature importance by gain

```text
{importance.head(30).to_string(index=False)}
```

## Figures

- `figures/v2_lightgbm_feature_importance.png`
- `figures/v2_lightgbm_actual_vs_pred_site_window.png`
- `figures/v2_lightgbm_residual_by_hour.png`
- `figures/v2_lightgbm_actual_pred_scatter.png`
- `figures/v2_lightgbm_time_series_fold_metrics.png`
"""
    report_path.write_text(text, encoding="utf-8")


def run_training(config: TrainConfig) -> dict[str, Path]:
    config.report_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = config.report_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    config.model_dir.mkdir(parents=True, exist_ok=True)

    print("Loading train/val parquet...")
    train_df = load_split(config.train_path)
    val_df = load_split(config.val_path)

    x_train, y_train, train_clean = prepare_xy(
        train_df, max_rows=config.max_train_rows, random_state=config.random_state
    )
    x_val, y_val, val_clean = prepare_xy(val_df, max_rows=None, random_state=config.random_state)

    # Align feature columns in case a column is missing.
    feature_cols = [col for col in x_train.columns if col in x_val.columns]
    x_train = x_train[feature_cols]
    x_val = x_val[feature_cols]

    print(f"Train clean rows: {len(x_train):,}")
    print(f"Val clean rows  : {len(x_val):,}")
    print(f"Feature count   : {len(feature_cols):,}")

    print("Training LightGBM...")
    model = train_lightgbm(x_train, y_train, x_val, y_val, config)

    print("Predicting validation...")
    pred = model.predict(x_val, num_iteration=model.best_iteration_)
    baseline = val_clean[BASELINE_COL].astype("float64").to_numpy()

    model_metrics = regression_metrics(y_val, pred)
    baseline_metrics = regression_metrics(y_val, baseline)
    skill_mae = 1.0 - model_metrics["mae"] / baseline_metrics["mae"]
    skill_rmse = 1.0 - model_metrics["rmse"] / baseline_metrics["rmse"]

    overall_metrics = pd.DataFrame(
        [
            {
                "model": "lightgbm_l1",
                "rows_train": len(x_train),
                "rows_val": len(x_val),
                "feature_count": len(feature_cols),
                "best_iteration": int(model.best_iteration_ or config.n_estimators),
                **model_metrics,
                "baseline_mae": baseline_metrics["mae"],
                "baseline_rmse": baseline_metrics["rmse"],
                "baseline_r2": baseline_metrics["r2"],
                "forecast_skill_mae_vs_lag1": float(skill_mae),
                "forecast_skill_rmse_vs_lag1": float(skill_rmse),
            }
        ]
    )

    val_eval = val_clean[[SITE_COL, TIMESTAMP_COL, TARGET_COL, BASELINE_COL]].copy()
    val_eval["prediction"] = pred
    val_eval["residual"] = val_eval[TARGET_COL] - val_eval["prediction"]

    by_site = metrics_by_group(val_eval, y_col=TARGET_COL, pred_col="prediction", group_col=SITE_COL)
    val_eval["hour"] = val_eval[TIMESTAMP_COL].dt.hour
    by_hour = metrics_by_group(val_eval, y_col=TARGET_COL, pred_col="prediction", group_col="hour")

    booster = model.booster_
    importance = pd.DataFrame(
        {
            "feature": feature_cols,
            "importance_gain": booster.feature_importance(importance_type="gain"),
            "importance_split": booster.feature_importance(importance_type="split"),
        }
    ).sort_values("importance_gain", ascending=False)

    paths = {
        "overall_metrics": config.report_dir / "v2_lightgbm_overall_metrics.csv",
        "metrics_by_site": config.report_dir / "v2_lightgbm_metrics_by_site.csv",
        "metrics_by_hour": config.report_dir / "v2_lightgbm_metrics_by_hour.csv",
        "feature_importance": config.report_dir / "v2_lightgbm_feature_importance.csv",
        "time_series_fold_metrics": config.report_dir / "v2_lightgbm_time_series_fold_metrics.csv",
        "val_predictions_sample": config.report_dir / "v2_lightgbm_val_predictions_sample.csv",
        "model": config.model_dir / "v2_lightgbm.pkl",
        "model_config": config.report_dir / "v2_lightgbm_config.json",
        "report": config.report_dir / "v2_lightgbm_validation_report.md",
        "fig_feature_importance": figures_dir / "v2_lightgbm_feature_importance.png",
        "fig_actual_vs_pred": figures_dir / "v2_lightgbm_actual_vs_pred_site_window.png",
        "fig_residual_by_hour": figures_dir / "v2_lightgbm_residual_by_hour.png",
        "fig_scatter": figures_dir / "v2_lightgbm_actual_pred_scatter.png",
        "fig_fold_metrics": figures_dir / "v2_lightgbm_time_series_fold_metrics.png",
    }

    overall_metrics.to_csv(paths["overall_metrics"], index=False)
    by_site.to_csv(paths["metrics_by_site"], index=False)
    by_hour.to_csv(paths["metrics_by_hour"], index=False)
    importance.to_csv(paths["feature_importance"], index=False)
    val_eval.head(100_000).to_csv(paths["val_predictions_sample"], index=False)
    joblib.dump(model, paths["model"])
    paths["model_config"].write_text(json.dumps(config.__dict__, default=str, indent=2), encoding="utf-8")

    plot_feature_importance(importance, paths["fig_feature_importance"])
    plot_actual_vs_pred(val_eval, paths["fig_actual_vs_pred"])
    plot_residual_by_hour(val_eval, paths["fig_residual_by_hour"])
    plot_scatter_actual_pred(val_eval, paths["fig_scatter"])

    fold_metrics = run_time_series_fold_validation(config, figures_dir)
    fold_metrics.to_csv(paths["time_series_fold_metrics"], index=False)

    write_report(
        config=config,
        train_clean=train_clean,
        val_eval=val_eval,
        overall_metrics=overall_metrics,
        fold_metrics=fold_metrics,
        importance=importance,
        report_path=paths["report"],
    )

    print("Training completed.")
    print(overall_metrics.to_string(index=False))
    for key, path in paths.items():
        print(f"{key}: {path}")
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train V2 LightGBM and validate on val split.")
    parser.add_argument("--max-train-rows", type=int, default=None)
    parser.add_argument("--n-estimators", type=int, default=1200)
    parser.add_argument("--learning-rate", type=float, default=0.04)
    parser.add_argument("--num-leaves", type=int, default=63)
    parser.add_argument("--early-stopping-rounds", type=int, default=80)
    parser.add_argument("--skip-fold-validation", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_training(
        TrainConfig(
            max_train_rows=args.max_train_rows,
            n_estimators=args.n_estimators,
            learning_rate=args.learning_rate,
            num_leaves=args.num_leaves,
            early_stopping_rounds=args.early_stopping_rounds,
            validate_folds=not args.skip_fold_validation,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
