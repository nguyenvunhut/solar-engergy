"""Stage 10 — train final LightGBM models on the full development set.

Input:
    - Development feature files and selected feature lists.
    - Best params from Stage 09.

Output:
    - ``model.pkl`` and ``model_config.json`` under ``models/v3_final_cleaned``.

Important:
    - The sealed test set is not used here.
    - Final training uses sample weights from the active experiment, so
      physical-over-capacity/ETL/outlier groups are handled consistently with
      tuning and evaluation.
    - Best iterations discovered during CV are used as fixed ``n_estimators``.
    - ``model_config.json`` records params, selected features, medians, sample
      weight counts, and whether training was mock/full.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import importlib.util
import sys
from pathlib import Path

import pandas as pd

from forecasting_common import add_common_cli, artifact_dir, load_config, model_dir, write_json


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


def _lightgbm_base_params(config, *, mock: bool) -> dict[str, object]:
    lgb_cfg = config.raw["training"]["lightgbm"]
    params: dict[str, object] = {
        "objective": str(lgb_cfg.get("objective", "regression")),
        "metric": "rmse",
        "random_state": int(lgb_cfg["random_seed"]),
        "n_jobs": int(lgb_cfg["n_jobs"]),
        "verbosity": -1,
        "device": str(lgb_cfg.get("device", "cpu")),
        "gpu_platform_id": int(lgb_cfg.get("gpu_platform_id", 0)),
        "gpu_device_id": int(lgb_cfg.get("gpu_device_id", 0)),
    }
    if lgb_cfg.get("reg_alpha") is not None:
        params["reg_alpha"] = float(lgb_cfg.get("reg_alpha", 0.0))
    if lgb_cfg.get("reg_lambda") is not None:
        params["reg_lambda"] = float(lgb_cfg.get("reg_lambda", 0.0))
    if mock:
        mock_cfg = config.raw["training"].get("mock", {})
        params.update(
            {
                "n_estimators": int(mock_cfg.get("n_estimators", 25)),
                "learning_rate": 0.08,
                "num_leaves": int(mock_cfg.get("num_leaves", 31)),
                "min_child_samples": 50,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
            }
        )
    else:
        params.update(
            {
                "n_estimators": 500,
                "learning_rate": 0.05,
                "num_leaves": 63,
                "subsample": 0.9,
                "colsample_bytree": 0.9,
            }
        )
    return params


def _ensure_opencl_icd_for_nix() -> str | None:
    """Best-effort OpenCL ICD discovery for NixOS.

    LightGBM's OpenCL backend uses Boost.Compute. On NixOS, clinfo may see the
    NVIDIA ICD from the Nix store while the Python process still does not know
    where vendor ICD files live. Setting OCL_ICD_VENDORS is process-local and
    does not touch kernel/system driver state.
    """

    if os.name != "posix" or os.environ.get("OCL_ICD_VENDORS"):
        return os.environ.get("OCL_ICD_VENDORS")
    candidates = []
    candidates.extend(Path("/nix/store").glob("*nvidia*/etc/OpenCL/vendors"))
    candidates.extend(
        [
            Path("/run/opengl-driver/etc/OpenCL/vendors"),
            Path("/etc/OpenCL/vendors"),
        ]
    )
    for candidate in candidates:
        try:
            if candidate.exists() and (
                (candidate / "nvidia.icd").exists() or any(candidate.glob("*.icd"))
            ):
                os.environ["OCL_ICD_VENDORS"] = str(candidate)
                return str(candidate)
        except OSError:
            continue
    return None


def _load_best_params(config, rid: str, horizon: int) -> dict[str, object]:
    path = artifact_dir(config, "06_tuning", rid) / "best_params.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if "best_by_horizon" in payload:
        params = dict(payload.get("best_by_horizon", {}).get(f"h{horizon}", {}).get("params", {}))
    else:
        params = dict(payload.get("best_params", {}))
    for metadata_key in ["model", "metric", "optuna_n_estimators", "best_iteration_source"]:
        params.pop(metadata_key, None)
    return params


def _safe_sample(train: pd.DataFrame, *, max_rows: int, seed: int) -> pd.DataFrame:
    if max_rows <= 0 or len(train) <= max_rows:
        return train
    # Giữ phân bố site tương đối đều để mock không bị lệch về vài site lớn.
    per_site = max(1, max_rows // train["site_id"].nunique())
    sampled = pd.concat(
        [
            group.sample(n=min(len(group), per_site), random_state=seed)
            for _, group in train.groupby("site_id", observed=True)
        ],
        ignore_index=False,
    )
    return sampled.sample(n=min(max_rows, len(sampled)), random_state=seed).sort_index()


def _fit_lightgbm(
    x: pd.DataFrame,
    y: pd.Series,
    sample_weight: pd.Series,
    config,
    *,
    rid: str,
    horizon: int,
    mock: bool,
):
    params = _lightgbm_base_params(config, mock=mock)
    if not mock:
        params.update(_load_best_params(config, rid, horizon))

    opencl_icd_path = None
    if str(params.get("device")).lower() == "gpu":
        opencl_icd_path = _ensure_opencl_icd_for_nix()
        if opencl_icd_path:
            print(f"[INFO] OCL_ICD_VENDORS={opencl_icd_path}")

    try:
        from lightgbm import LGBMRegressor
    except Exception as exc:
        raise RuntimeError(
            "LightGBM chưa cài hoặc import lỗi. Pipeline không fallback sang sklearn. "
            "Cài bằng `pip install lightgbm` rồi chạy lại, hoặc giữ mock sau khi cài LightGBM."
        ) from exc

    force_cpu = bool(config.raw["training"]["lightgbm"].get("force_cpu_if_gpu_unavailable", True))
    try:
        model = LGBMRegressor(**params)
        model.fit(x, y, sample_weight=sample_weight)
        if opencl_icd_path:
            params["ocl_icd_vendors"] = opencl_icd_path
        return model, "lightgbm_gpu" if params.get("device") == "gpu" else "lightgbm_cpu", params
    except Exception as exc:
        if params.get("device") != "gpu" or not force_cpu:
            raise
        print(f"[WARN] LightGBM GPU fit failed, retry CPU safely: {exc}")
        params = {**params, "device": "cpu"}
        params.pop("gpu_platform_id", None)
        params.pop("gpu_device_id", None)
        model = LGBMRegressor(**params)
        model.fit(x, y, sample_weight=sample_weight)
        return model, "lightgbm_cpu_after_gpu_retry", params


def run_train_final(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    in_dir = artifact_dir(config, "03_features", rid) / "final"
    out_dir = model_dir(config, rid)
    out_dir.mkdir(parents=True, exist_ok=True)
    seed = int(config.raw["training"]["lightgbm"]["random_seed"])
    mock_cfg = config.raw["training"].get("mock", {})
    mock = bool(mock_cfg.get("enabled", False)) or str(config.raw["training"].get("mode", "")).lower().startswith("mock")
    if not mock and not bool(config.raw["training"].get("allow_full_train", False)):
        raise RuntimeError(
            "Full LightGBM training is disabled by config for CPU/RAM safety. "
            "Set training.mock.enabled=true for smoke test, or set training.allow_full_train=true intentionally."
        )
    max_rows = int(mock_cfg.get("max_train_rows_per_horizon", 0))
    experiment = active_experiment(config)
    paths: dict[str, Path] = {}
    for horizon in config.raw["time"]["horizon_steps"]:
        h = int(horizon)
        df = pd.read_parquet(in_dir / f"h{h}" / "development_features.parquet")
        target = f"target_h{h}"
        features = select_feature_columns(df, config, horizon_steps=h)
        weight_all = build_sample_weight(df, config, horizon_steps=h)
        label_mask = df[target].notna()
        mask = label_mask & weight_all.gt(0)
        train = df.loc[mask, features + [target]].copy()
        train_weight = weight_all.loc[train.index].astype(float)
        if train.empty:
            raise ValueError(f"No training rows for horizon {h}")
        train_rows_before_sample = int(len(train))
        if mock:
            train = _safe_sample(train, max_rows=max_rows, seed=seed)
            train_weight = train_weight.loc[train.index]
        medians = train[features].median(numeric_only=True).fillna(0.0)
        x_train = train[features].fillna(medians).astype(float)
        y_train = train[target].astype(float)
        model, backend, params = _fit_lightgbm(
            x_train,
            y_train,
            train_weight,
            config,
            rid=rid,
            horizon=h,
            mock=mock,
        )
        h_dir = out_dir / f"h{h}"
        h_dir.mkdir(parents=True, exist_ok=True)
        model_path = h_dir / "model.pkl"
        with model_path.open("wb") as f:
            pickle.dump(model, f)
        write_json(
            {
                "run_id": rid,
                "horizon_steps": h,
                "backend": backend,
                "training_mode": "mock_lightgbm_small_sample" if mock else "final_lightgbm_full_development",
                "active_experiment": experiment,
                "lightgbm_params": params,
                "features": features,
                "feature_medians": medians.to_dict(),
                "rows": int(len(train)),
                "rows_before_mock_sample": train_rows_before_sample,
                "rows_with_label_before_weight": int(label_mask.sum()),
                "rows_excluded_by_weight": int((label_mask & weight_all.le(0)).sum()),
                "sample_weight_sum": float(train_weight.sum()),
                "sample_weight_zero_rows": int(train_weight.eq(0).sum()),
                "sample_weight_min": float(train_weight.min()),
                "sample_weight_max": float(train_weight.max()),
                "mock_train": mock,
            },
            h_dir / "model_config.json",
        )
        paths[f"h{h}_model"] = model_path
        print(
            f"h{h}: trained {backend} | mode={'mock' if mock else 'final'} | "
            f"experiment={experiment} | rows={len(train):,}/{train_rows_before_sample:,} | "
            f"weight_sum={train_weight.sum():,.0f} | features={len(features)}"
        )
    print("Final model training complete")
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train final forecasting model.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_train_final(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
