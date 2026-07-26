"""Stage 11 — evaluate final models on the sealed test set.

Input:
    - Final model artifacts from Stage 10.
    - Test feature files from Stage 03/05.
    - Baseline metrics from Stage 08.

Output:
    - ``metrics_overall.json``, ``metrics_by_site.csv``, and
      ``prediction_audit.parquet`` under ``07_metrics/<run_id>``.

Important:
    - This is the first stage that scores the sealed test set.
    - Metrics are reported by horizon, site, and scope so outlier/capacity/ETL
      effects are visible instead of hidden inside one aggregate score.
    - Model-vs-persistence improvement is calculated on the same scope to avoid
      comparing incompatible row sets.
"""

from __future__ import annotations

import argparse
import json
import importlib.util
import pickle
from pathlib import Path

import pandas as pd

from forecasting_common import add_common_cli, artifact_dir, load_config, model_dir, regression_metrics, write_json


def _load_neighbor(name: str):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


baseline_policy = _load_neighbor("08_train_baselines.py")
build_sample_weight = baseline_policy.build_sample_weight
scope_masks = baseline_policy.scope_masks


BASELINES = ["persistence_current", "seasonal_persistence_day", "seasonal_persistence_week"]


def _load_model_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _baseline_prediction(
    df: pd.DataFrame,
    *,
    model_name: str,
    target_col: str,
    horizon_steps: int,
) -> pd.Series:
    if model_name == "persistence_current":
        return df[target_col]
    if model_name == "seasonal_persistence_day":
        lag = f"lag_{96 - horizon_steps}"
        fallback = "lag_96"
        return df[lag] if lag in df.columns else df[fallback] if fallback in df.columns else pd.Series(pd.NA, index=df.index)
    if model_name == "seasonal_persistence_week":
        lag = f"lag_{672 - horizon_steps}"
        fallback = "lag_672"
        return df[lag] if lag in df.columns else df[fallback] if fallback in df.columns else pd.Series(pd.NA, index=df.index)
    raise ValueError(f"Unknown baseline: {model_name}")


def run_evaluate(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    feature_dir = artifact_dir(config, "03_features", rid) / "final"
    out_dir = artifact_dir(config, "07_metrics", rid)
    out_dir.mkdir(parents=True, exist_ok=True)
    audits = []
    metric_rows = []
    mock_any = False
    for horizon in config.raw["time"]["horizon_steps"]:
        h = int(horizon)
        h_model_dir = model_dir(config, rid) / f"h{h}"
        with (h_model_dir / "model.pkl").open("rb") as f:
            model = pickle.load(f)
        model_config = _load_model_config(h_model_dir / "model_config.json")
        mock_any = mock_any or bool(model_config.get("mock_train"))
        features = list(model_config["features"])
        medians = pd.Series(model_config["feature_medians"], dtype=float)
        df = pd.read_parquet(feature_dir / f"h{h}" / "test_features.parquet")
        target = f"target_h{h}"
        scored = df[df[target].notna()].copy()
        if model_config.get("mock_train"):
            max_eval_rows = int(config.raw["training"].get("mock", {}).get("max_eval_rows_per_horizon", 0))
            if max_eval_rows > 0 and len(scored) > max_eval_rows:
                per_site = max(1, max_eval_rows // scored["site_id"].nunique())
                sampled = pd.concat(
                    [
                        group.sample(n=min(len(group), per_site), random_state=42 + h)
                        for _, group in scored.groupby("site_id", observed=True)
                    ],
                    ignore_index=False,
                )
                scored = sampled.sample(n=min(max_eval_rows, len(sampled)), random_state=42 + h).sort_index()
        scored = scored.copy()
        scored["y_true"] = scored[target]
        scored["y_pred"] = model.predict(scored[features].fillna(medians).astype(float))
        scored["residual"] = scored["y_true"] - scored["y_pred"]
        scored["model_name"] = f"short_term_h{h}"
        scored["horizon"] = h
        for base_col in [
            "energy_source",
            "gmm_if_outlier_flag",
            "gmm_if_outlier_reason",
            "outlier_group",
            "exclude_from_training",
            "exclude_reason",
            "training_quality_reason",
            "after_source_gap_steps_remaining",
            "is_daylight_scope",
        ]:
            shifted_col = f"target_h{h}_{base_col}"
            if shifted_col in scored.columns:
                scored[f"label_{base_col}"] = scored[shifted_col]
                scored[base_col] = scored[shifted_col]
        scored["active_experiment"] = model_config.get(
            "active_experiment",
            config.raw["training"].get("active_experiment", "measured_only_headline"),
        )
        scored["sample_weight"] = build_sample_weight(scored, config, horizon_steps=h)
        masks = scope_masks(scored, horizon_steps=h)
        for scope_name, scope_mask in masks.items():
            scored[f"scope_{scope_name}"] = scope_mask
        scored["scope_headline"] = scored["scope_headline"].astype(bool)
        audit_cols = [
            "site_id",
            "timestamp",
            "horizon",
            "model_name",
            "active_experiment",
            "y_true",
            "y_pred",
            "residual",
            "sample_weight",
            "is_daylight",
            "energy_source",
            "gmm_if_outlier_flag",
            "gmm_if_outlier_reason",
            "outlier_group",
            "exclude_from_training",
            "exclude_reason",
            "training_quality_reason",
            "after_source_gap_steps_remaining",
            "label_energy_source",
            "label_gmm_if_outlier_flag",
            "label_gmm_if_outlier_reason",
            "label_outlier_group",
            "label_exclude_from_training",
            "label_after_source_gap_steps_remaining",
            "label_is_daylight_scope",
            *[f"scope_{name}" for name in masks],
        ]
        for col in audit_cols:
            if col not in scored.columns:
                scored[col] = pd.NA
        audits.append(scored[audit_cols])
        model_metrics_by_scope: dict[str, dict[str, float]] = {}
        for scope_name, mask in masks.items():
            mask = mask & scored["y_true"].notna() & scored["y_pred"].notna()
            model_metrics_all = regression_metrics(scored.loc[mask, "y_true"], scored.loc[mask, "y_pred"])
            model_metrics_by_scope[scope_name] = model_metrics_all
            metric_rows.append(
                {
                    "site_id": "ALL",
                    "horizon": h,
                    "model_name": f"short_term_h{h}",
                    "scope": scope_name,
                    "active_experiment": scored["active_experiment"].iloc[0] if len(scored) else None,
                    "n_rows": int(mask.sum()),
                    **model_metrics_all,
                }
            )
            for site_id, group in scored.loc[mask].groupby("site_id", observed=True):
                metric_rows.append(
                    {
                        "site_id": site_id,
                        "horizon": h,
                        "model_name": f"short_term_h{h}",
                        "scope": scope_name,
                        "active_experiment": scored["active_experiment"].iloc[0] if len(scored) else None,
                        "n_rows": int(len(group)),
                        **regression_metrics(group["y_true"], group["y_pred"]),
                    }
                )
        for baseline_name in BASELINES:
            pred = _baseline_prediction(
                scored,
                model_name=baseline_name,
                target_col=config.target_col,
                horizon_steps=h,
            )
            for scope_name, mask in masks.items():
                baseline_mask = mask & scored["y_true"].notna() & pred.notna()
                baseline_metrics_all = regression_metrics(scored.loc[baseline_mask, "y_true"], pred.loc[baseline_mask])
                model_metrics_all = model_metrics_by_scope.get(scope_name, {})
                improvement = (
                    float((baseline_metrics_all["wape"] - model_metrics_all["wape"]) / baseline_metrics_all["wape"] * 100.0)
                    if baseline_metrics_all["wape"]
                    and pd.notna(baseline_metrics_all["wape"])
                    and pd.notna(model_metrics_all.get("wape"))
                    else float("nan")
                )
                metric_rows.append(
                    {
                        "site_id": "ALL",
                        "horizon": h,
                        "model_name": baseline_name,
                        "scope": scope_name,
                        "active_experiment": scored["active_experiment"].iloc[0] if len(scored) else None,
                        "n_rows": int(baseline_mask.sum()),
                        "model_wape_for_improvement": model_metrics_all.get("wape"),
                        "model_improvement_vs_baseline_wape_pct": improvement,
                        **baseline_metrics_all,
                    }
                )
                for site_id, group in scored.loc[baseline_mask].assign(_baseline_pred=pred.loc[baseline_mask]).groupby(
                    "site_id",
                    observed=True,
                ):
                    metric_rows.append(
                        {
                            "site_id": site_id,
                            "horizon": h,
                            "model_name": baseline_name,
                            "scope": scope_name,
                            "active_experiment": scored["active_experiment"].iloc[0] if len(scored) else None,
                            "n_rows": int(len(group)),
                            **regression_metrics(group["y_true"], group["_baseline_pred"]),
                        }
                    )
    audit = pd.concat(audits, ignore_index=True) if audits else pd.DataFrame()
    metrics = pd.DataFrame(metric_rows)
    paths = {
        "prediction_audit": out_dir / "prediction_audit.parquet",
        "metrics_by_site": out_dir / "metrics_by_site.csv",
        "metrics_overall": out_dir / "metrics_overall.json",
    }
    audit.to_parquet(paths["prediction_audit"], index=False)
    metrics.to_csv(paths["metrics_by_site"], index=False)
    write_json(
        {
            "run_id": rid,
            "is_mock": bool(mock_any),
            "rows_scored": int(len(audit)),
            "headline_rows": int(audit.get("scope_headline", pd.Series(dtype=bool)).sum()),
            "metrics": metrics[metrics["site_id"].eq("ALL")].to_dict("records"),
        },
        paths["metrics_overall"],
    )
    print("Evaluation complete")
    if mock_any:
        print("[WARN] MOCK TRAIN/EVAL: metrics are smoke-test only, not final model quality.")
    print(metrics[metrics["site_id"].eq("ALL")].to_string(index=False))
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate final forecasting model.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_evaluate(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
