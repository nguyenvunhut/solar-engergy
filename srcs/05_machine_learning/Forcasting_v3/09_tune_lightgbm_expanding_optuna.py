"""Stage 09 — tune LightGBM with expanding-window CV and Optuna.

Input:
    - Final candidate features and selected feature lists.
    - Expanding fold definitions from Stage 02.

Output:
    - ``best_params.json`` and ``optuna_trials.csv`` under ``06_tuning/<run_id>``.

Important:
    - Final model is LightGBM, not sklearn.
    - Each trial trains on fold-train and evaluates on later fold-val only.
    - Objective is pooled weighted WAPE across folds, not row-count-averaged WAPE.
    - Early stopping is applied inside each fold using the validation set; the
      median best iteration is carried forward as final ``n_estimators``.
    - GPU params are passed through when configured, with CPU fallback controlled
      by config.
"""

from __future__ import annotations

import argparse
import importlib.util
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from forecasting_common import add_common_cli, artifact_dir, load_config, wape, write_json


def _load_neighbor(name: str):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


select_feature_columns = _load_neighbor("07_select_features_sklearn.py").select_feature_columns
baseline_policy = _load_neighbor("08_train_baselines.py")
active_experiment = baseline_policy.active_experiment
build_sample_weight = baseline_policy.build_sample_weight


def _default_lightgbm_params(config) -> dict[str, object]:
    lgb_cfg = config.raw["training"]["lightgbm"]
    return {
        "model": "lightgbm",
        "objective": str(lgb_cfg.get("objective", "regression")),
        "metric": "pooled_wape",
        "random_state": int(lgb_cfg["random_seed"]),
        "n_estimators": int(config.raw["training"].get("mock", {}).get("n_estimators", 25)),
        "learning_rate": 0.08,
        "num_leaves": int(config.raw["training"].get("mock", {}).get("num_leaves", 31)),
        "reg_alpha": float(lgb_cfg.get("reg_alpha", 0.0)),
        "reg_lambda": float(lgb_cfg.get("reg_lambda", 0.0)),
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "n_jobs": int(lgb_cfg["n_jobs"]),
        "device": str(lgb_cfg.get("device", "cpu")),
        "gpu_platform_id": int(lgb_cfg.get("gpu_platform_id", 0)),
        "gpu_device_id": int(lgb_cfg.get("gpu_device_id", 0)),
    }


def run_tuning(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    out_dir = artifact_dir(config, "06_tuning", rid)
    out_dir.mkdir(parents=True, exist_ok=True)
    mock = bool(config.raw["training"].get("mock", {}).get("enabled", False)) or str(config.raw["training"].get("mode", "")).lower().startswith("mock")
    if mock:
        path = out_dir / "best_params.json"
        best_params = _default_lightgbm_params(config)
        write_json(
            {
                "run_id": rid,
                "status": "mock_train_enabled_skip_optuna",
                "best_params": best_params,
                "note": "Optuna skipped intentionally. Mock train fits LightGBM on a capped sample only.",
            },
            path,
        )
        print("Tuning stage complete: mock_train_enabled_skip_optuna")
        return {"best_params": path}

    try:
        from lightgbm import LGBMRegressor, early_stopping, log_evaluation
        import optuna

        status = "optuna_completed"
    except Exception as exc:  # pragma: no cover - depends on local env
        best_params = _default_lightgbm_params(config)
        best_params.update({"n_estimators": 500, "learning_rate": 0.05, "num_leaves": 63})
        status = f"optional_dependency_missing: {exc}"
        path = out_dir / "best_params.json"
        write_json({"run_id": rid, "status": status, "best_params": best_params}, path)
        print(f"Tuning stage complete: {status}")
        return {"best_params": path}

    feature_dir = artifact_dir(config, "03_features", rid) / "final"
    seed = int(config.raw["training"]["lightgbm"]["random_seed"])
    n_trials = int(config.raw["training"]["lightgbm"]["n_trials"])
    timeout = int(config.raw["training"]["lightgbm"]["timeout_minutes"]) * 60
    objective_name = str(config.raw["training"]["lightgbm"].get("objective", "regression"))
    fixed_reg_alpha = config.raw["training"]["lightgbm"].get("reg_alpha")
    fixed_reg_lambda = config.raw["training"]["lightgbm"].get("reg_lambda")
    experiment = active_experiment(config)
    early_stopping_rounds = int(config.raw["training"]["lightgbm"].get("early_stopping_rounds", 100))
    log_period = int(config.raw["training"]["lightgbm"].get("log_evaluation_period", 200))
    trials: list[dict[str, object]] = []
    best_by_horizon: dict[str, dict[str, object]] = {}

    for horizon in [int(x) for x in config.raw["time"]["horizon_steps"]]:
        fold_train_files = sorted((feature_dir / f"h{horizon}").glob("fold_*_train_features.parquet"))
        if not fold_train_files:
            continue
        first = pd.read_parquet(fold_train_files[-1])
        features = select_feature_columns(first, config, horizon_steps=horizon)
        target = f"target_h{horizon}"
        cached_folds: list[dict[str, object]] = []
        for fold_idx, train_path in enumerate(fold_train_files, start=1):
            val_path = train_path.with_name(train_path.name.replace("_train_features", "_val_features"))
            train_df = pd.read_parquet(train_path)
            val_df = pd.read_parquet(val_path)
            train_weight_all = build_sample_weight(train_df, config, horizon_steps=horizon)
            val_weight_all = build_sample_weight(val_df, config, horizon_steps=horizon)
            train_mask = train_df[target].notna() & train_weight_all.gt(0)
            val_mask = val_df[target].notna() & val_weight_all.gt(0)
            train = train_df.loc[train_mask, features + [target]].copy()
            val = val_df.loc[val_mask, features + [target]].copy()
            if train.empty or val.empty:
                continue
            medians = train[features].median(numeric_only=True).fillna(0.0)
            cached_folds.append(
                {
                    "fold": fold_idx,
                    "x_train": train[features].fillna(medians).astype(np.float32),
                    "y_train": train[target].astype(np.float32),
                    "w_train": train_weight_all.loc[train.index].astype(np.float32),
                    "x_val": val[features].fillna(medians).astype(np.float32),
                    "y_val": val[target].astype(np.float32),
                    "w_val": val_weight_all.loc[val.index].astype(np.float32),
                }
            )
        if not cached_folds:
            continue
        print(
            "Tuning LightGBM",
            f"horizon={horizon}",
            f"folds={len(cached_folds)}",
            f"features={len(features)}",
            f"device={config.raw['training']['lightgbm'].get('device', 'cpu')}",
            f"objective={objective_name}",
            f"experiment={experiment}",
            f"early_stopping_rounds={early_stopping_rounds}",
            f"reg_alpha={fixed_reg_alpha if fixed_reg_alpha is not None else 'tune'}",
            f"reg_lambda={fixed_reg_lambda if fixed_reg_lambda is not None else 'tune'}",
            f"gpu_platform_id={config.raw['training']['lightgbm'].get('gpu_platform_id', 0)}",
            f"gpu_device_id={config.raw['training']['lightgbm'].get('gpu_device_id', 0)}",
            flush=True,
        )

        def objective(trial):
            params = {
                "objective": objective_name,
                "n_estimators": trial.suggest_int("n_estimators", 200, int(config.raw["training"]["lightgbm"]["max_estimators"])),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
                "num_leaves": trial.suggest_int("num_leaves", 31, 127),
                "min_child_samples": trial.suggest_int("min_child_samples", 20, 200),
                "subsample": trial.suggest_float("subsample", 0.7, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 1.0),
                "reg_alpha": float(fixed_reg_alpha)
                if fixed_reg_alpha is not None
                else trial.suggest_float("reg_alpha", 0.0, 10.0),
                "reg_lambda": float(fixed_reg_lambda)
                if fixed_reg_lambda is not None
                else trial.suggest_float("reg_lambda", 0.0, 10.0),
                "random_state": seed,
                "n_jobs": int(config.raw["training"]["lightgbm"]["n_jobs"]),
                "device": str(config.raw["training"]["lightgbm"].get("device", "cpu")),
                "gpu_platform_id": int(config.raw["training"]["lightgbm"].get("gpu_platform_id", 0)),
                "gpu_device_id": int(config.raw["training"]["lightgbm"].get("gpu_device_id", 0)),
                "metric": "l1",
                "verbosity": 1,
            }
            abs_err_sum = 0.0
            abs_y_sum = 0.0
            fold_best_iterations: list[int] = []
            for fold_payload in cached_folds:
                model = LGBMRegressor(**params)
                model.fit(
                    fold_payload["x_train"],
                    fold_payload["y_train"],
                    sample_weight=fold_payload["w_train"],
                    eval_set=[(fold_payload["x_val"], fold_payload["y_val"])],
                    eval_sample_weight=[fold_payload["w_val"]],
                    eval_metric="l1",
                    callbacks=[
                        early_stopping(
                            stopping_rounds=early_stopping_rounds,
                            first_metric_only=True,
                            verbose=False,
                        ),
                        log_evaluation(period=log_period),
                    ],
                )
                best_iteration = int(getattr(model, "best_iteration_", None) or params["n_estimators"])
                fold_best_iterations.append(best_iteration)
                pred = model.predict(fold_payload["x_val"], num_iteration=best_iteration)
                y_val = fold_payload["y_val"].to_numpy(dtype=float)
                w_val = fold_payload["w_val"].to_numpy(dtype=float)
                abs_err_sum += float((abs(y_val - pred) * w_val).sum())
                abs_y_sum += float((abs(y_val) * w_val).sum())
            if fold_best_iterations:
                trial.set_user_attr("best_iteration_median", int(statistics.median(fold_best_iterations)))
                trial.set_user_attr("best_iteration_mean", float(statistics.mean(fold_best_iterations)))
                trial.set_user_attr("best_iteration_max", int(max(fold_best_iterations)))
            return abs_err_sum / abs_y_sum * 100.0 if abs_y_sum else float("inf")

        study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed))
        study.optimize(objective, n_trials=n_trials, timeout=timeout)
        best_params = dict(study.best_params)
        best_iteration = study.best_trial.user_attrs.get("best_iteration_median")
        if best_iteration:
            best_params["optuna_n_estimators"] = best_params.get("n_estimators")
            best_params["n_estimators"] = int(best_iteration)
            best_params["best_iteration_source"] = "median_cv_early_stopping"
        best_by_horizon[f"h{horizon}"] = {
            "value": study.best_value,
            "params": best_params,
            "best_iteration_median": best_iteration,
            "best_iteration_mean": study.best_trial.user_attrs.get("best_iteration_mean"),
            "best_iteration_max": study.best_trial.user_attrs.get("best_iteration_max"),
        }
        for trial in study.trials:
            trials.append(
                {
                    "horizon": horizon,
                    "number": trial.number,
                    "value": trial.value,
                    "best_iteration_median": trial.user_attrs.get("best_iteration_median"),
                    "best_iteration_mean": trial.user_attrs.get("best_iteration_mean"),
                    "best_iteration_max": trial.user_attrs.get("best_iteration_max"),
                    **trial.params,
                }
            )

    pd.DataFrame(trials).to_csv(out_dir / "optuna_trials.csv", index=False)
    path = out_dir / "best_params.json"
    write_json({"run_id": rid, "status": status, "active_experiment": experiment, "best_by_horizon": best_by_horizon}, path)
    print(f"Tuning stage complete: {status}")
    return {"best_params": path, "optuna_trials": out_dir / "optuna_trials.csv"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tune LightGBM with expanding folds.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_tuning(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
