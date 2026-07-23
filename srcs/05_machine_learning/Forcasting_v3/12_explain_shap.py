"""Stage 12 — generate SHAP explainability artifacts.

Input:
    - Final LightGBM models from Stage 10.
    - Test features and prediction audit from Stage 11.

Output:
    - SHAP global bar/beeswarm plots.
    - Local waterfall/force plots and row-level SHAP samples.
    - SHAP manifest/summary under ``pictures/.../04_explainability``.

Important:
    - SHAP is run after final test metrics are locked.
    - Global SHAP explains which features drive the model overall.
    - Local SHAP examples explain individual high-residual predictions, useful
      for report discussion and dashboard drill-down.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from forecasting_common import add_common_cli, artifact_dir, load_config, model_dir, picture_dir, write_json


def _load_neighbor(name: str):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


build_sample_weight = _load_neighbor("08_train_baselines.py").build_sample_weight


def _load_model_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _select_shap_rows(df: pd.DataFrame, config, *, horizon: int, max_rows: int, seed: int) -> pd.DataFrame:
    target = f"target_h{horizon}"
    weight = build_sample_weight(df, config, horizon_steps=horizon)
    work = df[df[target].notna() & weight.gt(0)].copy()
    if work.empty:
        return work
    if len(work) <= max_rows:
        return work
    per_site = max(1, max_rows // max(int(work["site_id"].nunique()), 1))
    sampled = pd.concat(
        [
            group.sample(n=min(len(group), per_site), random_state=seed + int(site_id) + horizon)
            for site_id, group in work.groupby("site_id", observed=True)
        ],
        ignore_index=False,
    )
    if len(sampled) > max_rows:
        sampled = sampled.sample(n=max_rows, random_state=seed + horizon)
    return sampled.sort_values(["site_id", config.timestamp_col])


def _as_2d_shap(values) -> np.ndarray:
    if isinstance(values, list):
        values = values[0]
    arr = np.asarray(values)
    if arr.ndim == 3:
        arr = arr[:, :, 0]
    return arr


def _expected_value(explainer) -> float:
    value = explainer.expected_value
    if isinstance(value, (list, tuple, np.ndarray)):
        return float(np.asarray(value).ravel()[0])
    return float(value)


def run_shap(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    out_dir = picture_dir(config, rid) / "04_explainability"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import shap
    except Exception as exc:
        path = out_dir / "shap_manifest.json"
        write_json({"run_id": rid, "status": f"optional_dependency_missing: {exc}"}, path)
        print(f"SHAP stage complete: optional_dependency_missing: {exc}")
        return {"manifest": path}

    feature_dir = artifact_dir(config, "03_features", rid) / "final"
    metrics_dir = artifact_dir(config, "07_metrics", rid)
    prediction_audit_path = metrics_dir / "prediction_audit.parquet"
    prediction_audit = pd.read_parquet(prediction_audit_path) if prediction_audit_path.exists() else pd.DataFrame()

    shap_cfg = config.raw.get("explainability", {}).get("shap", {})
    max_rows = int(shap_cfg.get("sample_rows", 2000))
    max_display = int(shap_cfg.get("max_display", 20))
    seed = int(config.raw["training"]["lightgbm"]["random_seed"])
    written: dict[str, str] = {}
    summary_rows: list[dict[str, object]] = []

    for horizon in [int(x) for x in config.raw["time"]["horizon_steps"]]:
        h_dir = model_dir(config, rid) / f"h{horizon}"
        model_path = h_dir / "model.pkl"
        model_config_path = h_dir / "model_config.json"
        test_features_path = feature_dir / f"h{horizon}" / "test_features.parquet"
        if not (model_path.exists() and model_config_path.exists() and test_features_path.exists()):
            continue

        with model_path.open("rb") as f:
            model = pickle.load(f)
        model_config = _load_model_config(model_config_path)
        features = list(model_config["features"])
        medians = pd.Series(model_config["feature_medians"], dtype=float)
        test_df = pd.read_parquet(test_features_path)
        sample = _select_shap_rows(test_df, config, horizon=horizon, max_rows=max_rows, seed=seed)
        if sample.empty:
            continue

        x = sample[features].fillna(medians).astype(float)
        y_col = f"target_h{horizon}"
        y_true = sample[y_col].astype(float)
        y_pred = model.predict(x)
        explainer = shap.TreeExplainer(model)
        shap_values = _as_2d_shap(explainer.shap_values(x))
        base_value = _expected_value(explainer)
        shap_df = pd.DataFrame(shap_values, columns=[f"shap_{c}" for c in features], index=sample.index)
        meta = sample[["site_id", config.timestamp_col]].copy()
        meta["horizon"] = horizon
        meta["y_true"] = y_true.to_numpy(dtype=float)
        meta["y_pred"] = y_pred
        meta["base_value"] = base_value
        row_level = pd.concat([meta.reset_index(drop=True), shap_df.reset_index(drop=True)], axis=1)
        shap_values_path = out_dir / f"shap_values_sample_h{horizon}.parquet"
        row_level.to_parquet(shap_values_path, index=False)
        written[f"h{horizon}_row_level_shap"] = str(shap_values_path)

        mean_abs = np.abs(shap_values).mean(axis=0)
        importance = (
            pd.DataFrame({"feature": features, "mean_abs_shap": mean_abs})
            .sort_values("mean_abs_shap", ascending=False)
            .reset_index(drop=True)
        )
        importance_path = out_dir / f"shap_global_importance_h{horizon}.csv"
        importance.to_csv(importance_path, index=False)
        written[f"h{horizon}_global_importance_csv"] = str(importance_path)

        plt.figure(figsize=(10, 7))
        shap.summary_plot(shap_values, x, feature_names=features, max_display=max_display, show=False)
        beeswarm_path = out_dir / f"shap_global_beeswarm_h{horizon}.png"
        plt.tight_layout()
        plt.savefig(beeswarm_path, dpi=180, bbox_inches="tight")
        plt.close()
        written[f"h{horizon}_global_beeswarm_png"] = str(beeswarm_path)

        plt.figure(figsize=(9, 6))
        shap.summary_plot(shap_values, x, feature_names=features, plot_type="bar", max_display=max_display, show=False)
        bar_path = out_dir / f"shap_global_bar_h{horizon}.png"
        plt.tight_layout()
        plt.savefig(bar_path, dpi=180, bbox_inches="tight")
        plt.close()
        written[f"h{horizon}_global_bar_png"] = str(bar_path)

        # Pick a concrete local example: largest absolute residual from the
        # scored audit when available, otherwise largest sample residual.
        local_idx = int(np.argmax(np.abs(y_true.to_numpy(dtype=float) - y_pred)))
        if len(prediction_audit):
            scored_h = prediction_audit[prediction_audit["horizon"].eq(horizon)].copy()
            if "scope_headline" in scored_h.columns:
                scored_h = scored_h[scored_h["scope_headline"].fillna(False).astype(bool)]
            if len(scored_h):
                scored_h["abs_residual"] = pd.to_numeric(scored_h["residual"], errors="coerce").abs()
                row = scored_h.sort_values("abs_residual", ascending=False).iloc[0]
                same_row = (
                    sample["site_id"].eq(row["site_id"])
                    & pd.to_datetime(sample[config.timestamp_col]).eq(pd.to_datetime(row["timestamp"]))
                )
                if same_row.any():
                    local_idx = int(np.flatnonzero(same_row.to_numpy())[0])

        local_feature_values = x.iloc[local_idx]
        local_shap_values = shap_values[local_idx]
        local_meta = meta.iloc[local_idx].to_dict()
        local_meta.update(
            {
                "horizon": horizon,
                "y_true": float(y_true.iloc[local_idx]),
                "y_pred": float(y_pred[local_idx]),
                "residual": float(y_true.iloc[local_idx] - y_pred[local_idx]),
                "base_value": base_value,
            }
        )
        local_top = (
            pd.DataFrame(
                {
                    "feature": features,
                    "feature_value": local_feature_values.to_numpy(dtype=float),
                    "shap_value": local_shap_values,
                    "abs_shap": np.abs(local_shap_values),
                }
            )
            .sort_values("abs_shap", ascending=False)
            .head(max_display)
        )
        local_csv_path = out_dir / f"shap_local_example_h{horizon}.csv"
        local_top.to_csv(local_csv_path, index=False)
        local_json_path = out_dir / f"shap_local_example_h{horizon}.json"
        write_json(local_meta, local_json_path)
        written[f"h{horizon}_local_example_csv"] = str(local_csv_path)
        written[f"h{horizon}_local_example_json"] = str(local_json_path)

        explanation = shap.Explanation(
            values=local_shap_values,
            base_values=base_value,
            data=local_feature_values.to_numpy(dtype=float),
            feature_names=features,
        )
        plt.figure(figsize=(10, 7))
        shap.plots.waterfall(explanation, max_display=max_display, show=False)
        waterfall_path = out_dir / f"shap_local_waterfall_h{horizon}.png"
        plt.tight_layout()
        plt.savefig(waterfall_path, dpi=180, bbox_inches="tight")
        plt.close()
        written[f"h{horizon}_local_waterfall_png"] = str(waterfall_path)

        force_path = out_dir / f"shap_local_force_h{horizon}.html"
        force_plot = shap.force_plot(
            base_value,
            local_shap_values,
            local_feature_values,
            feature_names=features,
            matplotlib=False,
        )
        shap.save_html(str(force_path), force_plot)
        written[f"h{horizon}_local_force_html"] = str(force_path)

        summary_rows.append(
            {
                "horizon": horizon,
                "sample_rows": int(len(sample)),
                "base_value": base_value,
                "local_site_id": local_meta.get("site_id"),
                "local_timestamp": local_meta.get(config.timestamp_col),
                "local_y_true": local_meta["y_true"],
                "local_y_pred": local_meta["y_pred"],
                "local_abs_residual": abs(local_meta["residual"]),
                "top_feature": str(importance.iloc[0]["feature"]) if len(importance) else None,
                "top_mean_abs_shap": float(importance.iloc[0]["mean_abs_shap"]) if len(importance) else None,
            }
        )

    summary_path = out_dir / "shap_summary.csv"
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)
    written["summary_csv"] = str(summary_path)
    manifest_path = out_dir / "shap_manifest.json"
    write_json(
        {
            "run_id": rid,
            "status": "shap_plots_generated" if summary_rows else "no_shap_rows",
            "sample_rows_per_horizon": max_rows,
            "max_display": max_display,
            "artifacts": written,
        },
        manifest_path,
    )
    print("SHAP stage complete:", "shap_plots_generated" if summary_rows else "no_shap_rows")
    print(pd.DataFrame(summary_rows).to_string(index=False) if summary_rows else "No SHAP rows")
    return {"manifest": manifest_path}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SHAP artifacts.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_shap(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
