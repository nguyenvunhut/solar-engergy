"""Stage 08 — persistence and seasonal-persistence baselines.

Target convention:
    target_h{h}(t) = energy(t + h)

Therefore the correct horizon persistence baseline is:
    y_hat(t + h) = energy(t)

It must not use lag_h, because lag_h is energy(t - h) and would make the
baseline artificially weak.

Input:
    - Selected feature files from Stage 07.

Output:
    - Baseline metrics under ``05_baselines/<run_id>``.

Important:
    - Baselines are the main defense against claiming artificial model gains.
    - ``persistence_current`` is expected to be very strong for h1 because PV
      output is highly autocorrelated over 15 minutes.
    - ``build_sample_weight`` defines which label rows are eligible for training
      and which outlier/provenance groups are excluded or down-weighted.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from forecasting_common import add_common_cli, artifact_dir, load_config, regression_metrics

EXPERIMENTS = {
    "measured_only_headline",
    "measured_plus_etl_imputed",
    "zero_weight_gmm_consensus",
    "zero_weight_all_flagged",
}


def _safe_bool_series(df: pd.DataFrame, col: str, default: bool = False) -> pd.Series:
    if col not in df.columns:
        return pd.Series(default, index=df.index)
    return df[col].fillna(default).astype(bool)


def active_experiment(config) -> str:
    name = str(config.raw["training"].get("active_experiment", "measured_only_headline"))
    if name not in EXPERIMENTS:
        raise ValueError(f"Unknown training.active_experiment={name!r}. Expected one of {sorted(EXPERIMENTS)}")
    return name


def _label_col(df: pd.DataFrame, base_col: str, horizon_steps: int | None) -> str | None:
    if horizon_steps is not None:
        shifted_col = f"target_h{horizon_steps}_{base_col}"
        if shifted_col in df.columns:
            return shifted_col
    return base_col if base_col in df.columns else None


def _label_series(
    df: pd.DataFrame,
    base_col: str,
    horizon_steps: int | None,
    default,
) -> pd.Series:
    col = _label_col(df, base_col, horizon_steps)
    if col is None:
        return pd.Series(default, index=df.index)
    return df[col].fillna(default)


def _label_bool_series(
    df: pd.DataFrame,
    base_col: str,
    horizon_steps: int | None,
    default: bool = False,
) -> pd.Series:
    return _label_series(df, base_col, horizon_steps, default).astype(bool)


def eligibility_mask(df: pd.DataFrame, *, horizon_steps: int | None = None) -> pd.Series:
    """Hard eligibility independent of experiment weighting.

    This keeps only rows whose future label is usable in principle. Outlier
    group and ETL-imputed policy are handled later by ``build_sample_weight``.
    """

    after_gap = pd.to_numeric(
        _label_series(df, "after_source_gap_steps_remaining", horizon_steps, 0),
        errors="coerce",
    ).fillna(0).gt(0)
    daylight = _label_bool_series(df, "is_daylight_scope", horizon_steps, default=False)
    source = _label_series(df, "energy_source", horizon_steps, "")
    excluded = _label_bool_series(df, "exclude_from_training", horizon_steps, default=False)
    mask = daylight & source.isin(["measured", "etl_imputed"]) & ~after_gap & ~excluded
    if horizon_steps is not None and f"target_h{horizon_steps}" in df.columns:
        mask &= df[f"target_h{horizon_steps}"].notna()
    return mask


def build_sample_weight(df: pd.DataFrame, config, *, horizon_steps: int | None = None) -> pd.Series:
    """Build train/eval weights from the experiment table in the v3 plan."""

    experiment = active_experiment(config)
    source = _label_series(df, "energy_source", horizon_steps, "")
    group = _label_series(df, "outlier_group", horizon_steps, "normal")
    weight = pd.Series(0.0, index=df.index)
    eligible = eligibility_mask(df, horizon_steps=horizon_steps)

    measured = source.eq("measured")
    etl = source.eq("etl_imputed")
    normal = group.eq("normal")
    physical = group.eq("physical_over_capacity")
    gmm = group.eq("gmm_if_consensus")
    other_or_multi = group.isin(["other_physical_rule", "multiple_rules"])

    weight.loc[eligible & measured & normal] = 1.0
    weight.loc[eligible & measured & other_or_multi] = 1.0

    if experiment in {"measured_only_headline", "measured_plus_etl_imputed"}:
        weight.loc[eligible & measured & gmm] = 1.0
    elif experiment == "zero_weight_gmm_consensus":
        weight.loc[eligible & measured & gmm] = 0.0
    elif experiment == "zero_weight_all_flagged":
        weight.loc[eligible & measured & (gmm | other_or_multi)] = 0.0

    if experiment == "measured_plus_etl_imputed":
        weight.loc[eligible & etl & normal] = 1.0

    # Physical over-capacity is impossible by the checked capacity ceiling and
    # is always excluded from objective/training in every experiment.
    weight.loc[physical] = 0.0
    return weight


def scope_masks(df: pd.DataFrame, *, horizon_steps: int | None = None) -> dict[str, pd.Series]:
    eligible = eligibility_mask(df, horizon_steps=horizon_steps)
    source = _label_series(df, "energy_source", horizon_steps, "")
    group = _label_series(df, "outlier_group", horizon_steps, "normal")
    return {
        "eligible_rows": eligible,
        "headline": eligible & source.eq("measured") & ~group.eq("physical_over_capacity"),
        "normal_rows": eligible & source.eq("measured") & group.eq("normal"),
        "etl_imputed_rows": eligible & source.eq("etl_imputed"),
        "gmm_if_consensus_rows": eligible & source.eq("measured") & group.eq("gmm_if_consensus"),
        "physical_over_capacity_rows": eligible & source.eq("measured") & group.eq("physical_over_capacity"),
        "other_physical_rule_rows": eligible & source.eq("measured") & group.eq("other_physical_rule"),
        "multiple_rules_rows": eligible & source.eq("measured") & group.eq("multiple_rules"),
    }


def headline_mask(df: pd.DataFrame, *, horizon_steps: int | None = None) -> pd.Series:
    return scope_masks(df, horizon_steps=horizon_steps)["headline"]


def _add_baseline_prediction(
    work: pd.DataFrame,
    *,
    model_name: str,
    target_col: str,
    horizon_steps: int,
) -> pd.Series:
    if model_name == "persistence_current":
        return work[target_col]
    if model_name == "seasonal_persistence_day":
        lag = f"lag_{96 - horizon_steps}"
        fallback = "lag_96"
        return work[lag] if lag in work.columns else work[fallback] if fallback in work.columns else pd.Series(pd.NA, index=work.index)
    if model_name == "seasonal_persistence_week":
        lag = f"lag_{672 - horizon_steps}"
        fallback = "lag_672"
        return work[lag] if lag in work.columns else work[fallback] if fallback in work.columns else pd.Series(pd.NA, index=work.index)
    raise ValueError(f"Unknown baseline: {model_name}")


def evaluate_baseline(df: pd.DataFrame, *, horizon_steps: int, target_col: str = "energy_generated_kwh") -> pd.DataFrame:
    y_col = f"target_h{horizon_steps}"
    work = df.copy()
    rows = []
    for model_name in ["persistence_current", "seasonal_persistence_day", "seasonal_persistence_week"]:
        pred_col = f"prediction_{model_name}"
        work[pred_col] = _add_baseline_prediction(
            work,
            model_name=model_name,
            target_col=target_col,
            horizon_steps=horizon_steps,
        )
        mask = headline_mask(work, horizon_steps=horizon_steps) & work[y_col].notna() & work[pred_col].notna()
        for site_id, group in work[mask].groupby("site_id", observed=True):
            m = regression_metrics(group[y_col], group[pred_col])
            rows.append(
                {
                    "site_id": site_id,
                    "horizon_steps": horizon_steps,
                    "model_name": model_name,
                    "scope": "headline",
                    "n_rows": int(len(group)),
                    **m,
                }
            )
        rows.append(
            {
                "site_id": "ALL",
                "horizon_steps": horizon_steps,
                "model_name": model_name,
                "scope": "headline",
                "n_rows": int(mask.sum()),
                **regression_metrics(work.loc[mask, y_col], work.loc[mask, pred_col]),
            }
        )
    return pd.DataFrame(rows)


def run_baselines(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    in_dir = artifact_dir(config, "03_features", rid) / "final"
    out_dir = artifact_dir(config, "05_baselines", rid)
    out_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for horizon in config.raw["time"]["horizon_steps"]:
        path = in_dir / f"h{int(horizon)}" / "development_features.parquet"
        if path.exists():
            reports.append(
                evaluate_baseline(
                    pd.read_parquet(path),
                    horizon_steps=int(horizon),
                    target_col=config.target_col,
                )
            )
    metrics = pd.concat(reports, ignore_index=True) if reports else pd.DataFrame()
    out_path = out_dir / "baseline_metrics.csv"
    metrics.to_csv(out_path, index=False)
    print("Baselines complete")
    print(metrics.tail(10).to_string(index=False) if len(metrics) else "No metrics")
    return {"baseline_metrics": out_path}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train/evaluate persistence baselines.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_baselines(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
