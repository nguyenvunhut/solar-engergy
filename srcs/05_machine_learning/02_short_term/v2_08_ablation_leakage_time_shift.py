"""Ablation audit for leakage risk and time-shift behavior.

Local only. No cloud, no git, no test split.

Compares:
    - full_features
    - no_lag_no_rolling
    - weather_time_site_only

Purpose:
    Check whether high validation score and +15min phase lag are caused by
    target-history features such as v2_lag_1.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from v2_06_train_validate_lightgbm import (
    BASELINE_COL,
    FEATURE_COLS,
    PROJECT_ROOT,
    SITE_COL,
    TARGET_COL,
    TIMESTAMP_COL,
    TRAIN_PATH,
    VAL_PATH,
    load_split,
    prepare_xy,
    regression_metrics,
)


REPORT_DIR = PROJECT_ROOT / "reports" / "ml_training_v2" / "ablation_leakage_time_shift"
MODEL_DIR = PROJECT_ROOT / "models" / "ml_training_v2" / "ablation_leakage_time_shift"

TARGET_HISTORY_PREFIXES = ("v2_lag_", "v2_rolling_")
WEATHER_COLS = {
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
}
TIME_COLS = {
    "v2_hour_sin",
    "v2_hour_cos",
    "v2_doy_sin",
    "v2_doy_cos",
    "v2_day_of_week",
    "v2_is_weekend",
    "v2_season_code",
    "v2_hour_bucket_model",
}
SITE_COLS = {
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
}


@dataclass(frozen=True)
class AblationConfig:
    train_path: Path = TRAIN_PATH
    val_path: Path = VAL_PATH
    report_dir: Path = REPORT_DIR
    model_dir: Path = MODEL_DIR
    n_estimators: int = 700
    learning_rate: float = 0.04
    num_leaves: int = 63
    min_child_samples: int = 200
    early_stopping_rounds: int = 80
    random_state: int = 42
    max_train_rows: int | None = None


def feature_set(name: str, available: list[str]) -> list[str]:
    if name == "full_features":
        return list(available)
    if name == "no_lag_no_rolling":
        return [
            col
            for col in available
            if not any(col.startswith(prefix) for prefix in TARGET_HISTORY_PREFIXES)
        ]
    if name == "weather_time_site_only":
        allowed = WEATHER_COLS | TIME_COLS | SITE_COLS
        return [col for col in available if col in allowed]
    raise ValueError(f"Unknown ablation name: {name}")


def train_model(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_val: pd.DataFrame,
    y_val: pd.Series,
    config: AblationConfig,
) -> lgb.LGBMRegressor:
    model = lgb.LGBMRegressor(
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


def time_shift_audit_for_model(
    eval_df: pd.DataFrame,
    *,
    model_name: str,
    output_dir: Path,
    selected_sites: list[int],
    max_lag_steps: int = 8,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    for site in selected_sites:
        part = eval_df[eval_df[SITE_COL].eq(site)].sort_values(TIMESTAMP_COL).copy()
        if len(part) < 100:
            continue

        actual = part[TARGET_COL].reset_index(drop=True)
        prediction = part["prediction"].reset_index(drop=True)
        baseline = part[BASELINE_COL].reset_index(drop=True)

        corr_rows = []
        for lag in range(-max_lag_steps, max_lag_steps + 1):
            if lag < 0:
                a = actual.iloc[-lag:].reset_index(drop=True)
                p = prediction.iloc[:lag].reset_index(drop=True)
                b = baseline.iloc[:lag].reset_index(drop=True)
            elif lag > 0:
                a = actual.iloc[:-lag].reset_index(drop=True)
                p = prediction.iloc[lag:].reset_index(drop=True)
                b = baseline.iloc[lag:].reset_index(drop=True)
            else:
                a = actual
                p = prediction
                b = baseline

            corr_rows.append(
                {
                    "model": model_name,
                    "site_id": site,
                    "lag_steps_15min": lag,
                    "lag_minutes": lag * 15,
                    "corr_prediction": float(a.corr(p)),
                    "corr_baseline_lag1": float(a.corr(b)),
                }
            )

        corr = pd.DataFrame(corr_rows)
        best = corr.loc[corr["corr_prediction"].idxmax()]
        rows.extend(corr_rows)

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(corr["lag_minutes"], corr["corr_prediction"], marker="o", label=model_name)
        ax.plot(corr["lag_minutes"], corr["corr_baseline_lag1"], marker="o", label="baseline lag_1", alpha=0.65)
        ax.axvline(0, color="black", linewidth=1)
        ax.set_title(f"Time-shift corr | {model_name} | site={site} | best lag={int(best.lag_minutes)} min")
        ax.set_xlabel("Prediction shifted by lag minutes")
        ax.set_ylabel("corr(actual, shifted prediction)")
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(fig_dir / f"v2_time_shift_corr_{model_name}_site_{site}.png")
        plt.close(fig)

        start = part[TIMESTAMP_COL].min()
        window = part[(part[TIMESTAMP_COL] >= start) & (part[TIMESTAMP_COL] < start + pd.Timedelta(days=7))]
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(window[TIMESTAMP_COL], window[TARGET_COL], label="actual", linewidth=1.1)
        ax.plot(window[TIMESTAMP_COL], window["prediction"], label=model_name, linewidth=1.1)
        ax.plot(window[TIMESTAMP_COL], window[BASELINE_COL], label="baseline lag_1", linewidth=0.8, alpha=0.65)
        ax.set_title(f"Actual vs prediction | {model_name} | site={site}")
        ax.set_xlabel("timestamp")
        ax.set_ylabel(TARGET_COL)
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(fig_dir / f"v2_actual_vs_pred_{model_name}_site_{site}.png")
        plt.close(fig)

    return pd.DataFrame(rows)


def plot_metric_comparison(metrics: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    data = metrics.sort_values("mae")
    ax.bar(data["model"], data["mae"])
    ax.set_title("Ablation validation MAE")
    ax.set_ylabel("MAE")
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "figures" / "v2_ablation_mae_compare.png")
    plt.close(fig)


def run_ablation(config: AblationConfig) -> dict[str, Path]:
    config.report_dir.mkdir(parents=True, exist_ok=True)
    (config.report_dir / "figures").mkdir(parents=True, exist_ok=True)
    config.model_dir.mkdir(parents=True, exist_ok=True)

    train_df = load_split(config.train_path)
    val_df = load_split(config.val_path)
    x_train_all, y_train, train_clean = prepare_xy(
        train_df, max_rows=config.max_train_rows, random_state=config.random_state
    )
    x_val_all, y_val, val_clean = prepare_xy(val_df)

    available = [col for col in FEATURE_COLS if col in x_train_all.columns and col in x_val_all.columns]
    selected_sites = [28, 32, 7, 11, 27, 25]
    selected_sites = [s for s in selected_sites if s in set(val_clean[SITE_COL].unique())]

    metrics_rows: list[dict[str, Any]] = []
    all_shift_rows: list[pd.DataFrame] = []
    importance_rows: list[pd.DataFrame] = []

    for model_name in ("full_features", "no_lag_no_rolling", "weather_time_site_only"):
        cols = feature_set(model_name, available)
        print(f"\nTraining ablation: {model_name} | features={len(cols)}")
        x_train = x_train_all[cols]
        x_val = x_val_all[cols]
        model = train_model(x_train, y_train, x_val, y_val, config)
        pred = model.predict(x_val, num_iteration=model.best_iteration_)
        baseline = val_clean[BASELINE_COL].astype("float64").to_numpy()
        m = regression_metrics(y_val, pred)
        b = regression_metrics(y_val, baseline)
        metrics_rows.append(
            {
                "model": model_name,
                "features": len(cols),
                "best_iteration": int(model.best_iteration_ or config.n_estimators),
                **m,
                "baseline_mae": b["mae"],
                "baseline_rmse": b["rmse"],
                "skill_mae_vs_lag1": 1.0 - m["mae"] / b["mae"],
                "skill_rmse_vs_lag1": 1.0 - m["rmse"] / b["rmse"],
            }
        )

        joblib.dump(model, config.model_dir / f"v2_ablation_{model_name}.pkl")
        imp = pd.DataFrame(
            {
                "model": model_name,
                "feature": cols,
                "importance_gain": model.booster_.feature_importance(importance_type="gain"),
                "importance_split": model.booster_.feature_importance(importance_type="split"),
            }
        ).sort_values(["model", "importance_gain"], ascending=[True, False])
        importance_rows.append(imp)

        eval_df = val_clean[[SITE_COL, TIMESTAMP_COL, TARGET_COL, BASELINE_COL]].copy()
        eval_df["prediction"] = pred
        shift = time_shift_audit_for_model(
            eval_df,
            model_name=model_name,
            output_dir=config.report_dir,
            selected_sites=selected_sites,
        )
        all_shift_rows.append(shift)

    metrics = pd.DataFrame(metrics_rows).sort_values("mae").reset_index(drop=True)
    shifts = pd.concat(all_shift_rows, ignore_index=True)
    importances = pd.concat(importance_rows, ignore_index=True)

    best_shift = shifts.loc[shifts.groupby(["model", "site_id"])["corr_prediction"].idxmax()].copy()
    best_shift = best_shift.sort_values(["model", "site_id"]).reset_index(drop=True)
    shift_summary = (
        best_shift.assign(best_lag_is_zero=best_shift["lag_steps_15min"].eq(0))
        .groupby("model", observed=True)
        .agg(
            sites_checked=("site_id", "nunique"),
            sites_best_lag_zero=("best_lag_is_zero", "sum"),
            sites_best_lag_nonzero=("best_lag_is_zero", lambda s: int((~s).sum())),
            median_best_lag_minutes=("lag_minutes", "median"),
            max_abs_best_lag_minutes=("lag_minutes", lambda s: int(s.abs().max())),
        )
        .reset_index()
    )

    metrics.to_csv(config.report_dir / "v2_ablation_metrics.csv", index=False)
    shifts.to_csv(config.report_dir / "v2_ablation_time_shift_correlations.csv", index=False)
    best_shift.to_csv(config.report_dir / "v2_ablation_best_lag_by_site.csv", index=False)
    shift_summary.to_csv(config.report_dir / "v2_ablation_time_shift_summary.csv", index=False)
    importances.to_csv(config.report_dir / "v2_ablation_feature_importance.csv", index=False)
    plot_metric_comparison(metrics, config.report_dir)

    report = config.report_dir / "v2_ablation_leakage_time_shift_report.md"
    report.write_text(
        f"""# V2 Ablation Leakage / Time-shift Report

Local-only. No cloud/database call. Test split was not used.

## Why this audit exists

The previous best LightGBM used `v2_lag_1` heavily and showed +15 minute phase lag in correlation audit.
This ablation checks whether removing target-history features reduces the phase lag.

## Validation metrics

```text
{metrics.to_string(index=False)}
```

## Time-shift summary

```text
{shift_summary.to_string(index=False)}
```

## Best lag by site

```text
{best_shift.to_string(index=False)}
```

## Top feature importance per model

```text
{importances.groupby("model").head(15).to_string(index=False)}
```

## Interpretation guide

- If `full_features` has better MAE but non-zero best lag, lag/rolling features improve accuracy but introduce phase lag.
- If `no_lag_no_rolling` has worse MAE but best lag closer to 0, it is cleaner for weather-to-power interpretation.
- If `weather_time_site_only` performs similarly to `no_lag_no_rolling`, target-history features are the main reason for the previous accuracy jump.
""",
        encoding="utf-8",
    )

    print("\n[DONE] Ablation completed")
    print(metrics.to_string(index=False))
    print(shift_summary.to_string(index=False))
    print("report:", report)
    return {
        "report": report,
        "metrics": config.report_dir / "v2_ablation_metrics.csv",
        "time_shift_summary": config.report_dir / "v2_ablation_time_shift_summary.csv",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run V2 leakage/time-shift ablation.")
    parser.add_argument("--max-train-rows", type=int, default=None)
    parser.add_argument("--n-estimators", type=int, default=700)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_ablation(AblationConfig(max_train_rows=args.max_train_rows, n_estimators=args.n_estimators))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
