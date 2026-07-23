"""Shared utilities for the v3_final_cleaned forecasting pipeline.

Purpose:
    - Centralize config loading, artifact paths, metrics, daylight policy,
      provenance classification, and reusable feature helpers.
    - Keep stage scripts importable from both CLI and notebooks.

Important:
    - Business logic should live in callable functions; ``main()`` is only for
      CLI argument handling.
    - Daylight/solar-elevation utilities are shared so training, evaluation,
      and audit use the same physical definition.
    - ``classify_outlier_group`` is the single source of truth for outlier
      buckets used by audit, continuous-grid materialization, sample weighting,
      metrics, and plots.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "05_machine_learning" / "forecasting_v3_final_cleaned.yaml"


@dataclass(frozen=True)
class PipelineConfig:
    raw: dict[str, Any]
    path: Path
    project_root: Path = PROJECT_ROOT

    @property
    def version(self) -> str:
        return str(self.raw["run"]["version"])

    @property
    def run_id(self) -> str:
        configured = self.raw["run"].get("run_id")
        if configured:
            return str(configured)
        resolved = self.raw["run"].get("_resolved_run_id")
        if resolved:
            return str(resolved)
        checksum = file_checksum(input_path(self), length=8)
        return f"{self.version}_{checksum}"

    @property
    def site_col(self) -> str:
        return str(self.raw["columns"]["site"])

    @property
    def timestamp_col(self) -> str:
        return str(self.raw["columns"]["timestamp"])

    @property
    def target_col(self) -> str:
        return str(self.raw["columns"]["target"])


def resolve_path(path: str | Path, *, root: Path = PROJECT_ROOT) -> Path:
    p = Path(path)
    return p if p.is_absolute() else root / p


def load_config(path: str | Path = DEFAULT_CONFIG) -> PipelineConfig:
    cfg_path = resolve_path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config not found: {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    raw.setdefault("run", {})
    if not raw["run"].get("run_id"):
        checksum = file_checksum(resolve_path(raw["input"]["mlmart_path"]), length=8)
        raw["run"]["_resolved_run_id"] = f"{raw['run']['version']}_{checksum}"
    return PipelineConfig(raw=raw, path=cfg_path)


def input_path(config: PipelineConfig) -> Path:
    return resolve_path(config.raw["input"]["mlmart_path"])


def raw_solar_path(config: PipelineConfig) -> Path:
    return resolve_path(config.raw["input"]["raw_solar_path"])


def artifact_dir(config: PipelineConfig, stage: str, run_id: str | None = None) -> Path:
    rid = run_id or config.run_id
    return resolve_path(config.raw["output"]["base_dir"]) / stage / rid


def model_dir(config: PipelineConfig, run_id: str | None = None) -> Path:
    return resolve_path(config.raw["output"]["model_dir"]) / (run_id or config.run_id)


def picture_dir(config: PipelineConfig, run_id: str | None = None) -> Path:
    return resolve_path(config.raw["output"]["picture_dir"]) / (run_id or config.run_id)


def report_dir(config: PipelineConfig, run_id: str | None = None) -> Path:
    return resolve_path(config.raw["output"]["report_dir"]) / (run_id or config.run_id)


def file_checksum(path: Path, *, length: int = 12) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:length]


def write_json(obj: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def require_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")


def read_mlmart(config: PipelineConfig) -> pd.DataFrame:
    df = pd.read_parquet(input_path(config))
    require_columns(df, [config.site_col, config.timestamp_col, config.target_col])
    df[config.timestamp_col] = pd.to_datetime(df[config.timestamp_col], errors="coerce")
    return df.sort_values([config.site_col, config.timestamp_col]).reset_index(drop=True)


def read_raw_solar(config: PipelineConfig) -> pd.DataFrame:
    path = raw_solar_path(config)
    if not path.exists():
        raise FileNotFoundError(f"Raw solar CSV not found: {path}")
    cols = config.raw["columns"]
    raw = pd.read_csv(path, usecols=[cols["raw_site"], cols["raw_timestamp"], cols["raw_target"]])
    raw[cols["raw_timestamp"]] = pd.to_datetime(raw[cols["raw_timestamp"]], errors="coerce")
    return raw


def classify_outlier_group(flag: pd.Series, reason: pd.Series) -> pd.Series:
    """Map upstream outlier flag/reason into stable reporting groups."""

    is_flagged = flag.fillna(False).astype(bool)
    reason_text = reason.fillna("").astype(str)
    rule_count = reason_text.str.count(r"\+") + reason_text.ne("").astype(int)
    out = pd.Series("normal", index=reason.index, dtype="object")
    one_rule = is_flagged & rule_count.eq(1)
    multi_rule = is_flagged & rule_count.ge(2)
    out.loc[one_rule & reason_text.eq("GMM_IF_CONSENSUS")] = "gmm_if_consensus"
    out.loc[one_rule & reason_text.eq("PHYSICAL_OVER_CAPACITY")] = "physical_over_capacity"
    out.loc[one_rule & ~reason_text.isin(["GMM_IF_CONSENSUS", "PHYSICAL_OVER_CAPACITY"])] = "other_physical_rule"
    out.loc[multi_rule] = "multiple_rules"
    return out


def southern_season(month: pd.Series) -> pd.Series:
    return month.map(
        {
            12: "summer",
            1: "summer",
            2: "summer",
            3: "autumn",
            4: "autumn",
            5: "autumn",
            6: "winter",
            7: "winter",
            8: "winter",
            9: "spring",
            10: "spring",
            11: "spring",
        }
    )


def solar_elevation_deg(
    timestamp: pd.Series,
    latitude: pd.Series,
    longitude: pd.Series,
    timezone: str = "Australia/Sydney",
) -> pd.Series:
    """Approximate solar elevation in degrees for local civil timestamps.

    This NOAA-style approximation is sufficient for daylight classification.
    It intentionally avoids a heavy astronomy dependency.
    """

    ts = pd.to_datetime(timestamp, errors="coerce")
    tz = ZoneInfo(timezone)
    lat = pd.to_numeric(latitude, errors="coerce").astype(float)
    lon = pd.to_numeric(longitude, errors="coerce").astype(float)
    day = ts.dt.dayofyear.astype(float)
    hour = ts.dt.hour + ts.dt.minute / 60.0 + ts.dt.second / 3600.0
    gamma = 2.0 * math.pi / 365.0 * (day - 1.0 + (hour - 12.0) / 24.0)
    decl = (
        0.006918
        - 0.399912 * np.cos(gamma)
        + 0.070257 * np.sin(gamma)
        - 0.006758 * np.cos(2 * gamma)
        + 0.000907 * np.sin(2 * gamma)
        - 0.002697 * np.cos(3 * gamma)
        + 0.00148 * np.sin(3 * gamma)
    )
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * np.cos(gamma)
        - 0.032077 * np.sin(gamma)
        - 0.014615 * np.cos(2 * gamma)
        - 0.040849 * np.sin(2 * gamma)
    )
    timezone_hours = ts.map(
        lambda value: (
            value.to_pydatetime().replace(tzinfo=tz).utcoffset().total_seconds() / 3600.0
            if pd.notna(value)
            else np.nan
        )
    ).astype(float)
    time_offset = eqtime + 4.0 * lon - 60.0 * timezone_hours
    true_solar_minutes = hour * 60.0 + time_offset
    hour_angle = np.deg2rad(true_solar_minutes / 4.0 - 180.0)
    lat_rad = np.deg2rad(lat)
    elevation = np.arcsin(
        np.sin(lat_rad) * np.sin(decl)
        + np.cos(lat_rad) * np.cos(decl) * np.cos(hour_angle)
    )
    return pd.Series(np.rad2deg(elevation), index=timestamp.index)


def add_daylight_columns(df: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    out = df.copy()
    threshold = float(config.raw["daylight"]["solar_elevation_threshold_deg"])
    eps = float(config.raw["daylight"]["energy_epsilon"])
    has_geo = {"latitude", "longitude"}.issubset(out.columns)
    if has_geo:
        elev = solar_elevation_deg(
            out[config.timestamp_col],
            out["latitude"],
            out["longitude"],
            timezone=str(config.raw["time"]["timezone"]),
        )
        physical = elev.gt(threshold)
        out["solar_elevation_deg"] = elev
        out["is_daylight_physical"] = physical
        out["daylight_source"] = "solar_elevation_15min"
    elif "weather_is_day" in out.columns:
        out["is_daylight_physical"] = pd.to_numeric(out["weather_is_day"], errors="coerce").eq(1)
        out["daylight_source"] = "weather_is_day_hourly_fallback"
    else:
        ts = pd.to_datetime(out[config.timestamp_col], errors="coerce")
        minute = ts.dt.hour * 60 + ts.dt.minute
        out["is_daylight_physical"] = ~((minute >= 18 * 60 + 30) | (minute < 5 * 60 + 30))
        out["daylight_source"] = "clock_window_fallback"

    out["is_daylight_scope"] = out["is_daylight_physical"].fillna(False).astype(bool)
    if "energy_source" in out.columns:
        measured_positive = out["energy_source"].eq("measured") & pd.to_numeric(
            out[config.target_col], errors="coerce"
        ).gt(eps)
        out.loc[measured_positive, "is_daylight_scope"] = True
    out["is_daylight"] = out["is_daylight_scope"]
    if "weather_is_day" in out.columns:
        weather_day = pd.to_numeric(out["weather_is_day"], errors="coerce")
        out["weather_daylight_disagreement"] = weather_day.notna() & weather_day.ne(
            out["is_daylight_physical"].fillna(False).astype(int)
        )
    return out


def add_calendar_columns(df: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    out = df.copy()
    ts = pd.to_datetime(out[config.timestamp_col], errors="coerce")
    out["minute_of_day"] = ts.dt.hour * 60 + ts.dt.minute
    out["quarter_hour"] = out["minute_of_day"] // 15
    out["hour_of_day"] = ts.dt.hour
    out["day_of_week_model"] = ts.dt.dayofweek
    out["month_model"] = ts.dt.month
    out["day_of_year"] = ts.dt.dayofyear
    out["season_model"] = southern_season(ts.dt.month)
    return out


def wape(y_true: pd.Series | np.ndarray, y_pred: pd.Series | np.ndarray) -> float:
    y = np.asarray(y_true, dtype=float)
    pred = np.asarray(y_pred, dtype=float)
    denom = np.nansum(np.abs(y))
    if denom == 0:
        return float("nan")
    return float(np.nansum(np.abs(y - pred)) / denom * 100.0)


def regression_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    y = pd.to_numeric(y_true, errors="coerce")
    pred = pd.to_numeric(y_pred, errors="coerce")
    mask = y.notna() & pred.notna()
    if not mask.any():
        return {"mae": np.nan, "rmse": np.nan, "wape": np.nan, "smape": np.nan, "r2": np.nan, "bias": np.nan}
    e = pred[mask] - y[mask]
    denom = (y[mask].abs() + pred[mask].abs()).to_numpy(dtype=float)
    numer = (2.0 * e.abs()).to_numpy(dtype=float)
    smape_terms = np.zeros_like(numer, dtype=float)
    np.divide(numer, denom, out=smape_terms, where=denom != 0.0)
    ss_res = float(np.square(e).sum())
    ss_tot = float(np.square(y[mask] - y[mask].mean()).sum())
    return {
        "mae": float(e.abs().mean()),
        "rmse": float(np.sqrt(np.square(e).mean())),
        "wape": wape(y[mask], pred[mask]),
        "smape": float(np.nanmean(smape_terms) * 100.0),
        "r2": float(1.0 - ss_res / ss_tot) if ss_tot else np.nan,
        "bias": float(e.mean()),
    }


def add_common_cli(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--overwrite", action="store_true")
