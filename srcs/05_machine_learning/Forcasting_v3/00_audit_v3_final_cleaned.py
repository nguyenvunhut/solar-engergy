"""Stage 00 — read-only audit for ``v3_final_cleaned`` before forecasting.

Input:
    - ``data/mlmart_base/v3_final_cleaned.parquet``: ETL-ready ML mart.
    - Raw solar CSV from config: used only to recover measured vs ETL-imputed
      target provenance.

Output:
    - Audit contract JSON/CSV under ``data/model/v3_final_cleaned/00_audit``.
    - Capacity-ceiling and alignment diagnostics for report/debugging.

Important:
    - This stage must not create training rows or mutate target values.
    - It is a fail-fast gate for duplicated keys, provenance coverage, daylight
      policy, gap statistics, and capacity/outlier sanity checks.
    - Outlier groups are audited here so later stages can decide whether to
      train with zero weight, report separately, or visualize them.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from forecasting_common import (
    add_calendar_columns,
    add_common_cli,
    add_daylight_columns,
    artifact_dir,
    classify_outlier_group,
    file_checksum,
    input_path,
    load_config,
    raw_solar_path,
    read_mlmart,
    read_raw_solar,
    write_json,
)


def attach_raw_provenance(df: pd.DataFrame, raw: pd.DataFrame, config) -> pd.DataFrame:
    cols = config.raw["columns"]
    key = raw[[cols["raw_site"], cols["raw_timestamp"], cols["raw_target"]]].rename(
        columns={
            cols["raw_site"]: config.site_col,
            cols["raw_timestamp"]: config.timestamp_col,
            cols["raw_target"]: "_raw_solar_generation",
        }
    )
    merged = df.merge(key, on=[config.site_col, config.timestamp_col], how="left", validate="one_to_one")
    merged["energy_source"] = merged["_raw_solar_generation"].notna().map(
        {True: "measured", False: "etl_imputed"}
    )
    if "gmm_if_outlier_flag" not in merged.columns:
        merged["gmm_if_outlier_flag"] = False
    if "gmm_if_outlier_reason" not in merged.columns:
        merged["gmm_if_outlier_reason"] = ""
    merged["outlier_group"] = classify_outlier_group(
        merged["gmm_if_outlier_flag"],
        merged["gmm_if_outlier_reason"],
    )
    return merged


def build_capacity_ceiling_audit(df: pd.DataFrame, config) -> pd.DataFrame:
    columns = [
        "site_id",
        "rows",
        "capacity_kw",
        "capacity_kw_is_missing",
        "capacity_kw_is_imputed_rows",
        "capacity_kw_is_imputed_pct",
        "physical_over_capacity_rows",
        "physical_over_capacity_pct",
        "direct_ceiling_violation_rows",
        "direct_ceiling_violation_pct",
        "ratio_median",
        "ratio_p90",
        "ratio_max",
    ]
    if "capacity_kw" not in df.columns:
        return pd.DataFrame(columns=columns)

    work = df.copy()
    energy = pd.to_numeric(work[config.target_col], errors="coerce")
    capacity = pd.to_numeric(work["capacity_kw"], errors="coerce")
    ceiling = capacity * 0.25
    valid_capacity = capacity.notna() & capacity.gt(0)
    direct_violation = valid_capacity & energy.notna() & energy.gt(ceiling)
    physical_group = work.get("outlier_group", pd.Series("normal", index=work.index)).eq("physical_over_capacity")
    if "capacity_kw_is_imputed" in work.columns:
        capacity_imputed = work["capacity_kw_is_imputed"].fillna(False).astype(bool)
    else:
        capacity_imputed = pd.Series(False, index=work.index)
    ratio = (energy / ceiling).where(direct_violation)

    rows: list[dict[str, object]] = []
    for site_id, idx in work.groupby(config.site_col, observed=True).groups.items():
        site_capacity = capacity.loc[idx].dropna()
        site_direct = direct_violation.loc[idx]
        site_physical = physical_group.loc[idx]
        site_capacity_imputed = capacity_imputed.loc[idx]
        site_ratio = ratio.loc[idx].dropna()
        n = len(idx)
        rows.append(
            {
                "site_id": site_id,
                "rows": int(n),
                "capacity_kw": float(site_capacity.mode().iloc[0]) if len(site_capacity) else float("nan"),
                "capacity_kw_is_missing": bool(len(site_capacity) == 0),
                "capacity_kw_is_imputed_rows": int(site_capacity_imputed.sum()),
                "capacity_kw_is_imputed_pct": float(site_capacity_imputed.sum() / max(n, 1) * 100.0),
                "physical_over_capacity_rows": int(site_physical.sum()),
                "physical_over_capacity_pct": float(site_physical.sum() / max(n, 1) * 100.0),
                "direct_ceiling_violation_rows": int(site_direct.sum()),
                "direct_ceiling_violation_pct": float(site_direct.sum() / max(n, 1) * 100.0),
                "ratio_median": float(site_ratio.median()) if len(site_ratio) else float("nan"),
                "ratio_p90": float(site_ratio.quantile(0.90)) if len(site_ratio) else float("nan"),
                "ratio_max": float(site_ratio.max()) if len(site_ratio) else float("nan"),
            }
        )
    out = pd.DataFrame(rows, columns=columns)
    return out.sort_values(["physical_over_capacity_rows", "direct_ceiling_violation_rows"], ascending=False)


def build_gap_events(df: pd.DataFrame, config) -> pd.DataFrame:
    freq = int(config.raw["time"]["frequency_minutes"])
    major = int(config.raw["gap"]["major_gap_hours"]) * 60
    rows: list[dict[str, object]] = []
    for site_id, group in df.sort_values([config.site_col, config.timestamp_col]).groupby(config.site_col, observed=True):
        diffs = group[config.timestamp_col].diff().dt.total_seconds().div(60)
        gap_mask = diffs.gt(freq)
        for idx in group.index[gap_mask.fillna(False)]:
            prev_ts = df.loc[idx - 1, config.timestamp_col] if idx - 1 in df.index else pd.NaT
            current_ts = df.loc[idx, config.timestamp_col]
            gap_minutes = float((current_ts - prev_ts).total_seconds() / 60.0) if pd.notna(prev_ts) else float("nan")
            missing_slots = max(int(gap_minutes // freq) - 1, 0) if pd.notna(gap_minutes) else 0
            rows.append(
                {
                    "site_id": site_id,
                    "prev_timestamp": prev_ts,
                    "next_timestamp": current_ts,
                    "gap_minutes": gap_minutes,
                    "missing_slots": missing_slots,
                    "is_major_gap": gap_minutes >= major if pd.notna(gap_minutes) else False,
                }
            )
    return pd.DataFrame(rows)


def build_peak_shift_audit(df: pd.DataFrame, config) -> pd.DataFrame:
    if "shortwave_radiation" not in df.columns:
        return pd.DataFrame(
            columns=[
                "site_id",
                "season_model",
                "energy_peak_hour",
                "shortwave_peak_hour",
                "peak_hour_shift",
                "is_shifted_ge_1h",
            ]
        )
    work = add_calendar_columns(df, config)
    work = work[
        work["energy_source"].eq("measured")
        & pd.to_numeric(work[config.target_col], errors="coerce").notna()
        & pd.to_numeric(work["shortwave_radiation"], errors="coerce").notna()
    ].copy()
    if work.empty:
        return pd.DataFrame()
    peak_hour_col = "hour" if "hour" in work.columns else "hour_of_day"
    hourly = (
        work.groupby([config.site_col, "season_model", peak_hour_col], observed=True)
        .agg(
            energy_mean=(config.target_col, "mean"),
            shortwave_mean=("shortwave_radiation", "mean"),
        )
        .reset_index()
    )
    rows: list[dict[str, object]] = []
    for (site_id, season), group in hourly.groupby([config.site_col, "season_model"], observed=True):
        energy_idx = group["energy_mean"].idxmax()
        shortwave_idx = group["shortwave_mean"].idxmax()
        energy_peak_hour = int(group.loc[energy_idx, peak_hour_col])
        shortwave_peak_hour = int(group.loc[shortwave_idx, peak_hour_col])
        shift = abs(energy_peak_hour - shortwave_peak_hour)
        rows.append(
            {
                "site_id": site_id,
                "season_model": season,
                "peak_hour_basis": peak_hour_col,
                "energy_peak_hour": energy_peak_hour,
                "shortwave_peak_hour": shortwave_peak_hour,
                "peak_hour_shift": shift,
                "is_shifted_ge_1h": shift >= 1,
            }
        )
    return pd.DataFrame(rows)


def build_energy_shortwave_lag_audit(df: pd.DataFrame, config) -> pd.DataFrame:
    """Cross-correlation check: does shortwave lead or lag energy per site?

    Replaces the fragile month/season argmax peak-hour comparison, which is
    noisy on near-flat PV curves (peak vs runner-up hour often <5% apart) and
    gets smeared across the October/April DST-transition months where a
    single calendar-month bucket mixes two different clock-to-sun regimes.

    Convention: correlate energy(t) against shortwave.shift(lag)(t) =
    shortwave(t - lag) for lag in [-max_lag, +max_lag] (15-minute steps).
    best_lag > 0 means past shortwave best explains current energy (normal:
    cause precedes effect, e.g. inverter/sensor smoothing). best_lag < 0
    means *future* shortwave best explains current energy — the direction
    that would indicate a genuine non-causal timestamp misalignment.
    """
    if "shortwave_radiation" not in df.columns:
        return pd.DataFrame(columns=["site_id", "best_lag", "best_corr", "corr_lag0", "n_rows"])
    max_lag = int(config.raw["daylight"].get("lag_check_max_steps", 4))
    work = df[
        df["energy_source"].eq("measured")
        & pd.to_numeric(df[config.target_col], errors="coerce").notna()
        & pd.to_numeric(df["shortwave_radiation"], errors="coerce").gt(10)
    ].copy()
    if work.empty:
        return pd.DataFrame(columns=["site_id", "best_lag", "best_corr", "corr_lag0", "n_rows"])
    work = work.sort_values(config.timestamp_col)
    rows: list[dict[str, object]] = []
    for site_id, g in work.groupby(config.site_col, observed=True):
        g = g.set_index(config.timestamp_col)
        e = pd.to_numeric(g[config.target_col], errors="coerce")
        s = pd.to_numeric(g["shortwave_radiation"], errors="coerce")
        corrs: dict[int, float] = {}
        for lag in range(-max_lag, max_lag + 1):
            aligned = pd.concat([e, s.shift(lag)], axis=1).dropna()
            if len(aligned) > 100:
                corrs[lag] = float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))
        if not corrs:
            continue
        best_lag = max(corrs, key=corrs.get)
        rows.append(
            {
                "site_id": site_id,
                "best_lag": best_lag,
                "best_corr": corrs[best_lag],
                "corr_lag0": corrs.get(0),
                "n_rows": int(len(g)),
            }
        )
    return pd.DataFrame(rows)


def assert_audit_gates(
    contract: dict[str, object],
    daylight_audit: pd.DataFrame,
    peak_shift: pd.DataFrame,
    lag_audit: pd.DataFrame,
    capacity_ceiling_audit: pd.DataFrame,
    config,
) -> None:
    failures: list[str] = []
    if int(contract["raw_rows"]) != int(contract["mlmart_rows"]):
        failures.append(f"raw_rows != mlmart_rows ({contract['raw_rows']} vs {contract['mlmart_rows']})")
    if int(contract["mlmart_target_null_rows"]) != 0:
        failures.append(f"mlmart_target_null_rows must be 0, got {contract['mlmart_target_null_rows']}")
    if int(contract["duplicate_key_rows"]) != 0:
        failures.append(f"duplicate_key_rows must be 0, got {contract['duplicate_key_rows']}")
    if int(contract["energy_source_null_rows"]) != 0:
        failures.append(f"energy_source_null_rows must be 0, got {contract['energy_source_null_rows']}")
    if int(contract["outlier_group_null_rows"]) != 0:
        failures.append(f"outlier_group_null_rows must be 0, got {contract['outlier_group_null_rows']}")

    clock_rows = int(daylight_audit.loc[daylight_audit["metric"].eq("clock_window_fallback_rows"), "value"].iloc[0])
    clock_pct = clock_rows / max(int(contract["mlmart_rows"]), 1) * 100.0
    max_clock_pct = float(config.raw["daylight"]["max_clock_fallback_pct"])
    if clock_pct > max_clock_pct:
        failures.append(f"clock_window_fallback_pct {clock_pct:.6f}% > {max_clock_pct}%")

    # peak_shift (argmax month/season peak-hour comparison) is diagnostic-only.
    # It is noisy on near-flat PV curves and gets smeared by the Oct/Apr
    # DST-transition months, so it must not gate the pipeline. See
    # energy_shortwave_lag_audit.csv for the enforced check below.
    _ = peak_shift

    if len(lag_audit):
        negative = lag_audit[lag_audit["best_lag"] < 0]
        negative_pct = float(len(negative) / len(lag_audit) * 100.0)
        max_negative_pct = float(config.raw["daylight"]["lag_check_fail_negative_site_pct"])
        if negative_pct >= max_negative_pct:
            failures.append(
                "energy/shortwave lag gate failed: future shortwave best explains "
                f"current energy on {negative_pct:.1f}% of sites "
                f"(threshold {max_negative_pct}%) — check weather join timestamp alignment"
            )

    if len(capacity_ceiling_audit):
        total_physical = int(capacity_ceiling_audit["physical_over_capacity_rows"].sum())
        if total_physical > 0:
            top2_share = float(
                capacity_ceiling_audit["physical_over_capacity_rows"].nlargest(2).sum()
                / total_physical
                * 100.0
            )
            if top2_share < 90.0:
                print(
                    "[WARN] physical_over_capacity no longer concentrated in top 2 sites: "
                    f"top2_share={top2_share:.2f}%",
                    flush=True,
                )
        cap_cfg = config.raw.get("capacity_audit", {})
        imputed_warn_pct = float(cap_cfg.get("imputed_capacity_pct_warn", 100.0))
        direct_warn_pct = float(cap_cfg.get("direct_ceiling_violation_pct_warn", 5.0))
        metadata_risk = capacity_ceiling_audit[
            capacity_ceiling_audit["capacity_kw_is_imputed_pct"].ge(imputed_warn_pct)
            & capacity_ceiling_audit["direct_ceiling_violation_pct"].ge(direct_warn_pct)
        ].copy()
        if len(metadata_risk):
            cols = [
                "site_id",
                "capacity_kw",
                "capacity_kw_is_imputed_pct",
                "direct_ceiling_violation_pct",
                "direct_ceiling_violation_rows",
                "physical_over_capacity_rows",
            ]
            print(
                "[WARN] direct ceiling violations on sites with imputed capacity. "
                "Treat as metadata-capacity risk, not confirmed energy outlier; "
                "do not zero-weight from direct_ceiling_violation alone.",
                flush=True,
            )
            print(metadata_risk[cols].to_string(index=False), flush=True)

    if failures:
        raise RuntimeError("Audit gates failed:\n- " + "\n- ".join(failures))


def run_audit(config_path: str | Path, *, run_id: str | None = None) -> dict[str, Path]:
    config = load_config(config_path)
    rid = run_id or config.run_id
    out_dir = artifact_dir(config, "00_audit", rid)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = read_mlmart(config)
    raw = read_raw_solar(config)
    audited = attach_raw_provenance(df, raw, config)
    audited = add_daylight_columns(audited, config)
    gaps = build_gap_events(audited, config)
    peak_shift = build_peak_shift_audit(audited, config)
    lag_audit = build_energy_shortwave_lag_audit(audited, config)
    capacity_ceiling_audit = build_capacity_ceiling_audit(audited, config)

    data_quality = (
        audited.groupby(config.site_col, observed=True)
        .agg(
            rows=(config.target_col, "size"),
            measured_rows=("energy_source", lambda s: int(s.eq("measured").sum())),
            etl_imputed_rows=("energy_source", lambda s: int(s.eq("etl_imputed").sum())),
            min_timestamp=(config.timestamp_col, "min"),
            max_timestamp=(config.timestamp_col, "max"),
            energy_null_rows=(config.target_col, lambda s: int(s.isna().sum())),
            daylight_rows=("is_daylight_scope", lambda s: int(s.fillna(False).sum())),
            outlier_group_null_rows=("outlier_group", lambda s: int(s.isna().sum())),
            physical_over_capacity_rows=("outlier_group", lambda s: int(s.eq("physical_over_capacity").sum())),
        )
        .reset_index()
    )

    daylight_audit = pd.DataFrame(
        {
            "metric": [
                "weather_is_day_0_measured_energy_positive_rows",
                "weather_is_day_0_measured_energy_positive_mean",
                "weather_is_day_0_measured_energy_positive_max",
                "clock_window_fallback_rows",
            ],
            "value": [
                int(((audited.get("weather_is_day") == 0) & (audited["energy_source"].eq("measured")) & (audited[config.target_col] > 0)).sum())
                if "weather_is_day" in audited.columns
                else 0,
                float(
                    audited.loc[
                        (audited.get("weather_is_day") == 0)
                        & audited["energy_source"].eq("measured")
                        & (audited[config.target_col] > 0),
                        config.target_col,
                    ].mean()
                )
                if "weather_is_day" in audited.columns
                else 0.0,
                float(
                    audited.loc[
                        (audited.get("weather_is_day") == 0)
                        & audited["energy_source"].eq("measured")
                        & (audited[config.target_col] > 0),
                        config.target_col,
                    ].max()
                )
                if "weather_is_day" in audited.columns
                else 0.0,
                int(audited["daylight_source"].eq("clock_window_fallback").sum()),
            ],
        }
    )

    contract = {
        "run_id": rid,
        "input_path": str(input_path(config)),
        "input_checksum": file_checksum(input_path(config)),
        "raw_solar_path": str(raw_solar_path(config)),
        "raw_rows": int(len(raw)),
        "mlmart_rows": int(len(df)),
        "raw_target_null_rows": int(raw[config.raw["columns"]["raw_target"]].isna().sum()),
        "mlmart_target_null_rows": int(df[config.target_col].isna().sum()),
        "measured_rows": int(audited["energy_source"].eq("measured").sum()),
        "etl_imputed_rows": int(audited["energy_source"].eq("etl_imputed").sum()),
        "energy_source_null_rows": int(audited["energy_source"].isna().sum()),
        "outlier_group_null_rows": int(audited["outlier_group"].isna().sum()),
        "duplicate_key_rows": int(audited.duplicated([config.site_col, config.timestamp_col]).sum()),
        "gap_events": int(len(gaps)),
        "major_gap_events": int(gaps["is_major_gap"].sum()) if len(gaps) else 0,
        "missing_slots": int(gaps["missing_slots"].sum()) if len(gaps) else 0,
        "physical_over_capacity_rows": int(audited["outlier_group"].eq("physical_over_capacity").sum()),
        "multiple_rules_rows": int(audited["outlier_group"].eq("multiple_rules").sum()),
    }
    paths = {
        "data_contract": out_dir / "data_contract.json",
        "data_quality_by_site": out_dir / "data_quality_by_site.csv",
        "daylight_policy_audit": out_dir / "daylight_policy_audit.csv",
        "peak_shift_audit": out_dir / "peak_shift_audit.csv",
        "energy_shortwave_lag_audit": out_dir / "energy_shortwave_lag_audit.csv",
        "capacity_ceiling_audit": out_dir / "capacity_ceiling_audit.csv",
        "observed_gap_events": out_dir / "observed_gap_events.parquet",
    }
    write_json(contract, paths["data_contract"])
    data_quality.to_csv(paths["data_quality_by_site"], index=False)
    daylight_audit.to_csv(paths["daylight_policy_audit"], index=False)
    peak_shift.to_csv(paths["peak_shift_audit"], index=False)
    lag_audit.to_csv(paths["energy_shortwave_lag_audit"], index=False)
    capacity_ceiling_audit.to_csv(paths["capacity_ceiling_audit"], index=False)
    gaps.to_parquet(paths["observed_gap_events"], index=False)

    assert_audit_gates(contract, daylight_audit, peak_shift, lag_audit, capacity_ceiling_audit, config)

    print("Audit complete")
    print(pd.Series(contract).to_string())
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit v3_final_cleaned forecasting input.")
    add_common_cli(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_audit(args.config, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
