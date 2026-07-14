"""Jira-aligned V2 Train + Validate + Explain pipeline.

Local only. No Supabase/cloud. No git. Test split is not used.

What this script does:
    1. Train LightGBM variants: L1, L2, Huber.
    2. Compare against lag_1 persistence baseline on validation.
    3. Run a small Optuna study on train/val samples for LightGBM guidance.
    4. Select best LightGBM by validation MAE.
    5. Explain best LightGBM with SHAP.
    6. Train Prophet baseline with its own per-site `ds`, `y`, regressor dataframe.

Prophet note:
    Prophet does not use the same feature table as LightGBM. It requires:
        - ds: timestamp
        - y: target
        - optional regressors added via add_regressor before fit
    Regressor values must also exist for the prediction dataframe.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
import shap
from prophet import Prophet

from v2_06_train_validate_lightgbm import (
    BASELINE_COL,
    FEATURE_COLS,
    MODEL_DIR,
    PROJECT_ROOT,
    REPORT_DIR as LGBM_REPORT_DIR,
    SITE_COL,
    TARGET_COL,
    TIMESTAMP_COL,
    TRAIN_PATH,
    VAL_PATH,
    build_training_mask,
    load_split,
    prepare_xy,
    regression_metrics,
)


REPORT_DIR = PROJECT_ROOT / "reports" / "ml_training_v2" / "jira_train_validate_explain"
MODEL_OUTPUT_DIR = MODEL_DIR / "jira_train_validate_explain"

PROPHET_REGRESSORS: tuple[str, ...] = (
    "shortwave_radiation",
    "direct_normal_irradiance",
    "diffuse_solar_radiation",
    "temperature_c",
    "cloud_cover_total",
    "wind_speed",
    "precipitation_mm",
    "sunshine_duration",
    "weather_is_day",
)


@dataclass(frozen=True)
class JiraTrainConfig:
    train_path: Path = TRAIN_PATH
    val_path: Path = VAL_PATH
    report_dir: Path = REPORT_DIR
    model_dir: Path = MODEL_OUTPUT_DIR
    n_estimators: int = 1000
    learning_rate: float = 0.04
    num_leaves: int = 63
    min_child_samples: int = 200
    early_stopping_rounds: int = 80
    random_state: int = 42
    optuna_trials: int = 6
    optuna_max_train_rows: int = 300_000
    optuna_max_val_rows: int = 120_000
    shap_sample_rows: int = 20_000
    shap_plot_rows: int = 5_000
    prophet_max_sites: int = 3


def make_lgbm_model(loss_name: str, config: JiraTrainConfig, **overrides: Any) -> lgb.LGBMRegressor:
    objective_by_loss = {
        "l1": "regression_l1",
        "l2": "regression_l2",
        "huber": "huber",
    }
    if loss_name not in objective_by_loss:
        raise ValueError(f"Unsupported loss_name={loss_name}")

    params = {
        "objective": objective_by_loss[loss_name],
        "n_estimators": config.n_estimators,
        "learning_rate": config.learning_rate,
        "num_leaves": config.num_leaves,
        "min_child_samples": config.min_child_samples,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "reg_alpha": 0.05,
        "reg_lambda": 0.2,
        "random_state": config.random_state,
        "n_jobs": -1,
        "verbosity": -1,
    }
    if loss_name == "huber":
        params["alpha"] = 0.9
    params.update(overrides)
    return lgb.LGBMRegressor(**params)


def train_one_lgbm_variant(
    *,
    loss_name: str,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_val: pd.DataFrame,
    y_val: pd.Series,
    config: JiraTrainConfig,
    model_dir: Path,
) -> tuple[lgb.LGBMRegressor, dict[str, Any], np.ndarray]:
    print(f"\nTraining LightGBM variant: {loss_name}")
    model = make_lgbm_model(loss_name, config)
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
    pred = model.predict(x_val, num_iteration=model.best_iteration_)
    metrics = regression_metrics(y_val, pred)
    metrics.update(
        {
            "model": f"lightgbm_{loss_name}",
            "loss": loss_name,
            "best_iteration": int(model.best_iteration_ or config.n_estimators),
        }
    )
    model_path = model_dir / f"v2_lightgbm_{loss_name}.pkl"
    joblib.dump(model, model_path)
    metrics["model_path"] = str(model_path)
    return model, metrics, pred


def run_optuna_lgbm(
    *,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_val: pd.DataFrame,
    y_val: pd.Series,
    config: JiraTrainConfig,
    output_dir: Path,
) -> pd.DataFrame:
    if config.optuna_trials <= 0:
        return pd.DataFrame()

    print(f"\nRunning Optuna study: {config.optuna_trials} trials")

    x_train_s = x_train
    y_train_s = y_train
    x_val_s = x_val
    y_val_s = y_val
    if len(x_train_s) > config.optuna_max_train_rows:
        idx = x_train_s.sample(config.optuna_max_train_rows, random_state=config.random_state).index
        x_train_s = x_train_s.loc[idx]
        y_train_s = y_train_s.loc[idx]
    if len(x_val_s) > config.optuna_max_val_rows:
        idx = x_val_s.sample(config.optuna_max_val_rows, random_state=config.random_state).index
        x_val_s = x_val_s.loc[idx]
        y_val_s = y_val_s.loc[idx]

    def objective(trial: optuna.Trial) -> float:
        loss_name = trial.suggest_categorical("loss", ["l1", "l2", "huber"])
        params = {
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.08),
            "num_leaves": trial.suggest_int("num_leaves", 31, 127),
            "min_child_samples": trial.suggest_int("min_child_samples", 80, 500),
            "subsample": trial.suggest_float("subsample", 0.75, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.75, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 0.5),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 1.0),
            "n_estimators": 500,
        }
        model = make_lgbm_model(loss_name, config, **params)
        model.fit(
            x_train_s,
            y_train_s,
            eval_set=[(x_val_s, y_val_s)],
            eval_metric="l1",
            callbacks=[lgb.early_stopping(40, verbose=False)],
        )
        pred = model.predict(x_val_s, num_iteration=model.best_iteration_)
        return regression_metrics(y_val_s, pred)["mae"]

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=config.optuna_trials, show_progress_bar=False)

    trials = study.trials_dataframe()
    trials.to_csv(output_dir / "v2_optuna_trials.csv", index=False)
    (output_dir / "v2_optuna_best_params.json").write_text(
        json.dumps(study.best_params, indent=2), encoding="utf-8"
    )
    print("Optuna best value:", study.best_value)
    print("Optuna best params:", study.best_params)
    return trials


def select_prophet_sites(val_clean: pd.DataFrame, max_sites: int) -> list[int]:
    """Pick representative sites with the highest validation row count."""

    sites = val_clean[SITE_COL].value_counts().head(max_sites).index.tolist()
    return [int(site) for site in sites]


def prepare_prophet_frame(df: pd.DataFrame, site_id: int) -> pd.DataFrame:
    cols = [SITE_COL, TIMESTAMP_COL, TARGET_COL, *PROPHET_REGRESSORS, "v2_exclude_from_loss_flag"]
    data = df[[col for col in cols if col in df.columns]].copy()
    data = data[data[SITE_COL].eq(site_id)]
    data = data[~data["v2_exclude_from_loss_flag"].fillna(False)]
    data = data.rename(columns={TIMESTAMP_COL: "ds", TARGET_COL: "y"})
    data["ds"] = pd.to_datetime(data["ds"], errors="coerce")
    for col in PROPHET_REGRESSORS:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["ds", "y", *[c for c in PROPHET_REGRESSORS if c in data.columns]])
    return data.sort_values("ds")


def train_prophet_baseline(
    *,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    sites: list[int],
    output_dir: Path,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    figures_dir = output_dir / "prophet_figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    for site_id in sites:
        print(f"\nTraining Prophet baseline for site {site_id}")
        train_p = prepare_prophet_frame(train_df, site_id)
        val_p = prepare_prophet_frame(val_df, site_id)
        regressors = [col for col in PROPHET_REGRESSORS if col in train_p.columns and col in val_p.columns]

        if len(train_p) < 1000 or len(val_p) < 100:
            rows.append({"site_id": site_id, "status": "skipped_insufficient_rows"})
            continue

        model = Prophet(
            growth="linear",
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            seasonality_mode="additive",
            interval_width=0.8,
            uncertainty_samples=0,
        )
        for regressor in regressors:
            model.add_regressor(regressor, standardize=True, mode="additive")
        model.fit(train_p[["ds", "y", *regressors]])

        forecast = model.predict(val_p[["ds", *regressors]])
        pred = forecast["yhat"].clip(lower=0).to_numpy()
        metrics = regression_metrics(val_p["y"], pred)
        rows.append(
            {
                "site_id": site_id,
                "status": "ok",
                "rows_train": len(train_p),
                "rows_val": len(val_p),
                "regressors": ",".join(regressors),
                **metrics,
            }
        )

        plot_df = val_p[["ds", "y"]].copy()
        plot_df["yhat"] = pred
        plot_df = plot_df.head(7 * 24 * 4)
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(plot_df["ds"], plot_df["y"], label="actual", linewidth=1.1)
        ax.plot(plot_df["ds"], plot_df["yhat"], label="prophet yhat", linewidth=1.1)
        ax.set_title(f"Prophet validation | site={site_id} | first 7 days")
        ax.set_xlabel("ds")
        ax.set_ylabel("energy_generated_kwh")
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(figures_dir / f"v2_prophet_site_{site_id}_actual_vs_pred.png")
        plt.close(fig)

        joblib.dump(model, output_dir / f"v2_prophet_site_{site_id}.pkl")

    result = pd.DataFrame(rows)
    result.to_csv(output_dir / "v2_prophet_metrics_by_site.csv", index=False)
    return result


def run_shap_explain(
    *,
    model: lgb.LGBMRegressor,
    x_val: pd.DataFrame,
    output_dir: Path,
    sample_rows: int,
    plot_rows: int,
    random_state: int,
) -> pd.DataFrame:
    print("\nRunning SHAP explain for best LightGBM")
    if len(x_val) > sample_rows:
        x_sample = x_val.sample(sample_rows, random_state=random_state)
    else:
        x_sample = x_val.copy()

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(x_sample)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    shap_importance = pd.DataFrame(
        {
            "feature": x_sample.columns,
            "mean_abs_shap": np.abs(shap_values).mean(axis=0),
            "mean_shap": shap_values.mean(axis=0),
        }
    ).sort_values("mean_abs_shap", ascending=False)
    shap_importance.to_csv(output_dir / "v2_shap_feature_importance.csv", index=False)

    top = shap_importance.head(30).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 9))
    ax.barh(top["feature"], top["mean_abs_shap"])
    ax.set_title("SHAP mean absolute contribution — top 30")
    ax.set_xlabel("mean(|SHAP value|)")
    fig.tight_layout()
    fig.savefig(output_dir / "figures" / "v2_shap_bar_top30.png")
    plt.close(fig)

    if len(x_sample) > plot_rows:
        x_plot = x_sample.sample(plot_rows, random_state=random_state)
        loc = x_sample.index.get_indexer(x_plot.index)
        shap_plot_values = shap_values[loc]
    else:
        x_plot = x_sample
        shap_plot_values = shap_values

    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_plot_values, x_plot, show=False, max_display=25)
    plt.tight_layout()
    plt.savefig(output_dir / "figures" / "v2_shap_summary_beeswarm.png")
    plt.close()

    return shap_importance


def plot_model_comparison(metrics_df: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    data = metrics_df.sort_values("mae")
    ax.bar(data["model"], data["mae"])
    ax.set_title("Validation MAE by model")
    ax.set_ylabel("MAE")
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "figures" / "v2_model_compare_mae.png")
    plt.close(fig)


def write_final_report(
    *,
    output_dir: Path,
    metrics_df: pd.DataFrame,
    best_model_name: str,
    prophet_df: pd.DataFrame,
    shap_importance: pd.DataFrame,
) -> None:
    report = output_dir / "v2_jira_train_validate_explain_report.md"
    text = f"""# V2 Jira Train + Validate + Explain Report

Local-only run. No cloud/database call. No git operation. Test split was not used.

## Scope matched to Jira

- Train LightGBM variants: L1, L2, Huber.
- Validation-only model selection.
- Optuna study on sampled train/validation rows.
- Prophet baseline with Prophet-specific `ds`, `y`, regressor dataframe.
- SHAP explanation for the best LightGBM model.

## Model comparison

```text
{metrics_df.to_string(index=False)}
```

Best validation model by MAE: `{best_model_name}`

## Prophet baseline

Prophet was trained per site using its own dataframe:

```text
ds, y, {", ".join(PROPHET_REGRESSORS)}
```

Prophet does not use LightGBM lag/rolling/site-code features.

```text
{prophet_df.to_string(index=False)}
```

## SHAP top 30

```text
{shap_importance.head(30).to_string(index=False)}
```

## Figures

- `figures/v2_model_compare_mae.png`
- `figures/v2_shap_bar_top30.png`
- `figures/v2_shap_summary_beeswarm.png`
- `prophet_figures/v2_prophet_site_*_actual_vs_pred.png`

## Technical interpretation

- If lag features dominate SHAP/importance, the model is a short-term autoregressive weather-assisted model.
- If the team wants a pure weather-to-power model, run an ablation without `v2_lag_*` and `v2_rolling_*` features.
- Rows crossing time gaps were already excluded from lag-based training through `v2_has_complete_history_features`.
- Outlier/missing-weather rows were excluded from loss through `v2_exclude_from_loss_flag`.
"""
    report.write_text(text, encoding="utf-8")


def run_pipeline(config: JiraTrainConfig) -> dict[str, Path]:
    output_dir = config.report_dir
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    config.model_dir.mkdir(parents=True, exist_ok=True)

    print("Loading train/val splits")
    train_df = load_split(config.train_path)
    val_df = load_split(config.val_path)
    x_train, y_train, train_clean = prepare_xy(train_df)
    x_val, y_val, val_clean = prepare_xy(val_df)

    feature_cols = [col for col in x_train.columns if col in x_val.columns]
    x_train = x_train[feature_cols]
    x_val = x_val[feature_cols]

    print(f"Train rows: {len(x_train):,}")
    print(f"Val rows  : {len(x_val):,}")
    print(f"Features  : {len(feature_cols):,}")

    run_optuna_lgbm(
        x_train=x_train,
        y_train=y_train,
        x_val=x_val,
        y_val=y_val,
        config=config,
        output_dir=output_dir,
    )

    metrics_rows: list[dict[str, Any]] = []
    models: dict[str, lgb.LGBMRegressor] = {}
    predictions: dict[str, np.ndarray] = {}
    for loss_name in ("l1", "l2", "huber"):
        model, metrics, pred = train_one_lgbm_variant(
            loss_name=loss_name,
            x_train=x_train,
            y_train=y_train,
            x_val=x_val,
            y_val=y_val,
            config=config,
            model_dir=config.model_dir,
        )
        models[metrics["model"]] = model
        predictions[metrics["model"]] = pred
        metrics_rows.append(metrics)

    baseline = val_clean[BASELINE_COL].astype("float64").to_numpy()
    baseline_metrics = regression_metrics(y_val, baseline)
    metrics_rows.append(
        {
            "model": "baseline_lag_1",
            "loss": "baseline",
            "best_iteration": 0,
            **baseline_metrics,
            "model_path": "",
        }
    )

    metrics_df = pd.DataFrame(metrics_rows)
    for col in ("mae", "rmse"):
        base_value = float(metrics_df.loc[metrics_df["model"].eq("baseline_lag_1"), col].iloc[0])
        metrics_df[f"skill_{col}_vs_lag1"] = 1.0 - metrics_df[col] / base_value

    metrics_df = metrics_df.sort_values("mae").reset_index(drop=True)
    metrics_df.to_csv(output_dir / "v2_model_comparison_metrics.csv", index=False)
    plot_model_comparison(metrics_df, output_dir)

    best_model_name = metrics_df[~metrics_df["model"].eq("baseline_lag_1")].iloc[0]["model"]
    best_model = models[best_model_name]
    joblib.dump(best_model, config.model_dir / "v2_best_lightgbm.pkl")

    shap_importance = run_shap_explain(
        model=best_model,
        x_val=x_val,
        output_dir=output_dir,
        sample_rows=config.shap_sample_rows,
        plot_rows=config.shap_plot_rows,
        random_state=config.random_state,
    )

    prophet_sites = select_prophet_sites(val_clean, config.prophet_max_sites)
    prophet_df = train_prophet_baseline(
        train_df=train_df,
        val_df=val_df,
        sites=prophet_sites,
        output_dir=output_dir,
    )

    (output_dir / "v2_jira_train_config.json").write_text(
        json.dumps(asdict(config), default=str, indent=2), encoding="utf-8"
    )
    write_final_report(
        output_dir=output_dir,
        metrics_df=metrics_df,
        best_model_name=str(best_model_name),
        prophet_df=prophet_df,
        shap_importance=shap_importance,
    )

    print("\n[DONE] Jira train/validate/explain pipeline completed")
    print(metrics_df.to_string(index=False))
    print("Best model:", best_model_name)
    print("Report:", output_dir / "v2_jira_train_validate_explain_report.md")
    return {
        "report": output_dir / "v2_jira_train_validate_explain_report.md",
        "metrics": output_dir / "v2_model_comparison_metrics.csv",
        "shap": output_dir / "v2_shap_feature_importance.csv",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run V2 Jira Train + Validate + Explain.")
    parser.add_argument("--optuna-trials", type=int, default=6)
    parser.add_argument("--prophet-max-sites", type=int, default=3)
    parser.add_argument("--shap-sample-rows", type=int, default=20_000)
    parser.add_argument("--n-estimators", type=int, default=1000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_pipeline(
        JiraTrainConfig(
            optuna_trials=args.optuna_trials,
            prophet_max_sites=args.prophet_max_sites,
            shap_sample_rows=args.shap_sample_rows,
            n_estimators=args.n_estimators,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
