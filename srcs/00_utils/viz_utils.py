"""Reusable visualization helpers for solar-energy EDA and ML evaluation.

Design notes
------------
All plotting functions:
    - accept ``value_col`` where possible, so the same function can plot
      actual energy, predicted energy, residuals, outlier flags, etc.
    - use timestamps directly instead of assuming fixed 15-minute or hourly
      frequency.
    - return ``(fig, ax)`` and never call ``plt.show()``.
    - depend only on pandas/numpy/matplotlib so they work in local notebooks
      and Google Colab without extra plotting libraries.

Expected common columns:
    - timestamp column: default ``timestamp``.
    - site column: auto-detected from ``site_id``, ``sitekey``, ``site_key``.

Most functions expose ``timestamp_col`` and ``site_col`` as optional keyword
arguments so the module stays reusable when the dataset schema changes.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure


SeasonName = Literal["Summer", "Autumn", "Winter", "Spring"]
AggName = Literal["mean", "sum", "median", "count", "max", "min", "std"]

DEFAULT_TIMESTAMP_COL = "timestamp"
DEFAULT_SITE_COL_CANDIDATES: tuple[str, ...] = ("site_id", "sitekey", "site_key")

MONTH_TO_SEASON: dict[int, SeasonName] = {
    12: "Summer",
    1: "Summer",
    2: "Summer",
    3: "Autumn",
    4: "Autumn",
    5: "Autumn",
    6: "Winter",
    7: "Winter",
    8: "Winter",
    9: "Spring",
    10: "Spring",
    11: "Spring",
}

SEASON_ORDER: tuple[SeasonName, ...] = ("Summer", "Autumn", "Winter", "Spring")


def _copy_with_datetime_index(
    df: pd.DataFrame,
    *,
    timestamp_col: str = DEFAULT_TIMESTAMP_COL,
) -> pd.DataFrame:
    """Return a copy indexed by timestamp without mutating the caller's df."""

    if timestamp_col not in df.columns:
        raise KeyError(f"Missing timestamp column: {timestamp_col!r}")

    out = df.copy()
    out[timestamp_col] = pd.to_datetime(out[timestamp_col], errors="coerce")
    out = out.dropna(subset=[timestamp_col])
    out = out.sort_values(timestamp_col)
    out = out.set_index(timestamp_col, drop=False)
    return out


def _resolve_site_col(df: pd.DataFrame, site_col: str | None = None) -> str:
    """Resolve site column from explicit value or common project names."""

    if site_col is not None:
        if site_col not in df.columns:
            raise KeyError(f"Missing site column: {site_col!r}")
        return site_col

    for candidate in DEFAULT_SITE_COL_CANDIDATES:
        if candidate in df.columns:
            return candidate

    raise KeyError(
        "Cannot find site column. Pass site_col explicitly. "
        f"Tried: {DEFAULT_SITE_COL_CANDIDATES}"
    )


def _require_columns(df: pd.DataFrame, cols: Sequence[str]) -> None:
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")


def _add_time_features(
    df: pd.DataFrame,
    *,
    timestamp_col: str = DEFAULT_TIMESTAMP_COL,
) -> pd.DataFrame:
    """Add hour/month/season helper columns from timestamp."""

    out = df.copy()
    ts = pd.to_datetime(out[timestamp_col], errors="coerce")
    out["_viz_hour"] = ts.dt.hour + ts.dt.minute / 60.0
    out["_viz_month"] = ts.dt.month
    out["_viz_season"] = out["_viz_month"].map(MONTH_TO_SEASON)
    return out


def _aggregate(values: pd.core.groupby.generic.SeriesGroupBy, agg: AggName) -> pd.Series:
    if agg == "mean":
        return values.mean()
    if agg == "sum":
        return values.sum()
    if agg == "median":
        return values.median()
    if agg == "count":
        return values.count()
    if agg == "max":
        return values.max()
    if agg == "min":
        return values.min()
    if agg == "std":
        return values.std()
    raise ValueError(f"Unsupported agg={agg!r}")


def _normalize_resample_freq(freq: str) -> str:
    """Map old pandas offset aliases to aliases accepted by newer pandas.

    pandas 3.x rejects some historical aliases, for example ``"M"`` for
    month-end. Keeping this mapper lets older notebooks continue to pass
    familiar values while the actual resample call receives the new alias.
    """

    alias_map = {
        "M": "ME",  # month end
        "Q": "QE",  # quarter end
        "Y": "YE",  # year end
        "A": "YE",  # year end, older alias
    }
    return alias_map.get(freq, freq)


def plot_global_overview(
    df: pd.DataFrame,
    value_col: str,
    freq: str = "ME",
    *,
    timestamp_col: str = DEFAULT_TIMESTAMP_COL,
    agg: AggName = "mean",
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Plot global time overview aggregated by a pandas frequency.

    Example frequencies: ``"ME"`` monthly, ``"W"`` weekly, ``"D"`` daily.
    No fixed source frequency is assumed.
    """

    _require_columns(df, [timestamp_col, value_col])
    data = _copy_with_datetime_index(df, timestamp_col=timestamp_col)
    resolved_freq = _normalize_resample_freq(freq)
    series = _aggregate(data[value_col].resample(resolved_freq), agg)

    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 5))
    else:
        fig = ax.figure

    ax.plot(series.index, series.values, marker="o", linewidth=1.8)
    ax.set_title(f"Global overview: {value_col} ({agg} by {resolved_freq})")
    ax.set_xlabel("Time")
    ax.set_ylabel(value_col)
    ax.grid(True, alpha=0.25)
    fig.autofmt_xdate()
    return fig, ax


def plot_seasonal_profile(
    df: pd.DataFrame,
    site_id: int | str,
    value_col: str,
    *,
    timestamp_col: str = DEFAULT_TIMESTAMP_COL,
    site_col: str | None = None,
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Plot one site's average intraday profile, split by four seasons."""

    resolved_site_col = _resolve_site_col(df, site_col)
    _require_columns(df, [timestamp_col, resolved_site_col, value_col])

    data = df[df[resolved_site_col].astype(str) == str(site_id)].copy()
    data = _add_time_features(data, timestamp_col=timestamp_col)
    data = data.dropna(subset=["_viz_hour", "_viz_season", value_col])

    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 5))
    else:
        fig = ax.figure

    for season in SEASON_ORDER:
        season_data = data[data["_viz_season"] == season]
        if season_data.empty:
            continue
        profile = season_data.groupby("_viz_hour")[value_col].mean().sort_index()
        ax.plot(profile.index, profile.values, marker=".", linewidth=1.5, label=season)

    ax.set_title(f"Seasonal intraday profile | site={site_id} | {value_col}")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel(value_col)
    ax.set_xlim(0, 24)
    ax.grid(True, alpha=0.25)
    ax.legend(title="Season")
    return fig, ax


def plot_local_zoom(
    df: pd.DataFrame,
    site_id: int | str,
    start_date: str | pd.Timestamp,
    n_days: int,
    value_col: str,
    *,
    timestamp_col: str = DEFAULT_TIMESTAMP_COL,
    site_col: str | None = None,
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Plot one site's raw-resolution signal for a local date window."""

    if n_days <= 0:
        raise ValueError("n_days must be positive")

    resolved_site_col = _resolve_site_col(df, site_col)
    _require_columns(df, [timestamp_col, resolved_site_col, value_col])

    data = _copy_with_datetime_index(df, timestamp_col=timestamp_col)
    start = pd.Timestamp(start_date)
    end = start + pd.Timedelta(days=n_days)
    mask = (
        (data[resolved_site_col].astype(str) == str(site_id))
        & (data.index >= start)
        & (data.index < end)
    )
    local = data.loc[mask]

    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 5))
    else:
        fig = ax.figure

    ax.plot(local.index, local[value_col], marker=".", linewidth=1.0)
    ax.set_title(f"Local zoom | site={site_id} | {start.date()} + {n_days} days")
    ax.set_xlim(start, end)
    ax.set_xlabel("Timestamp")
    ax.set_ylabel(value_col)
    ax.grid(True, alpha=0.25)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%H:%M"))
    fig.autofmt_xdate()
    return fig, ax


def plot_actual_vs_pred(
    df: pd.DataFrame,
    site_id: int | str,
    start_date: str | pd.Timestamp,
    n_days: int,
    *,
    actual_col: str = "energy_actual",
    pred_col: str = "energy_pred",
    timestamp_col: str = DEFAULT_TIMESTAMP_COL,
    site_col: str | None = None,
) -> tuple[Figure, np.ndarray]:
    """Plot actual vs predicted energy plus residual bars for one local window."""

    if n_days <= 0:
        raise ValueError("n_days must be positive")

    resolved_site_col = _resolve_site_col(df, site_col)
    _require_columns(df, [timestamp_col, resolved_site_col, actual_col, pred_col])

    data = _copy_with_datetime_index(df, timestamp_col=timestamp_col)
    start = pd.Timestamp(start_date)
    end = start + pd.Timedelta(days=n_days)
    mask = (
        (data[resolved_site_col].astype(str) == str(site_id))
        & (data.index >= start)
        & (data.index < end)
    )
    local = data.loc[mask].copy()
    local["_viz_residual"] = local[actual_col] - local[pred_col]

    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(14, 7),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )
    ax_main, ax_resid = axes

    ax_main.plot(local.index, local[actual_col], label=actual_col, linewidth=1.5)
    ax_main.plot(local.index, local[pred_col], label=pred_col, linewidth=1.5)
    ax_main.set_title(f"Actual vs prediction | site={site_id}")
    ax_main.set_ylabel("Energy")
    ax_main.grid(True, alpha=0.25)
    ax_main.legend()

    residual = pd.to_numeric(local["_viz_residual"], errors="coerce").dropna()
    if residual.empty:
        residual_min = residual_max = residual_mae = residual_rmse = residual_p95 = np.nan
    else:
        residual_min = float(residual.min())
        residual_max = float(residual.max())
        residual_mae = float(residual.abs().mean())
        residual_rmse = float(np.sqrt(np.mean(residual**2)))
        residual_p95 = float(residual.abs().quantile(0.95))

    ax_resid.bar(local.index, local["_viz_residual"], width=0.01, alpha=0.7, label="residual")
    ax_resid.axhline(0, color="black", linewidth=0.8)
    if np.isfinite(residual_mae):
        ax_resid.axhspan(-residual_mae, residual_mae, color="green", alpha=0.10, label=f"±MAE {residual_mae:.3g}")
    if np.isfinite(residual_rmse):
        ax_resid.axhline(residual_rmse, color="orange", linestyle="--", linewidth=1.0, label=f"±RMSE {residual_rmse:.3g}")
        ax_resid.axhline(-residual_rmse, color="orange", linestyle="--", linewidth=1.0)
    if np.isfinite(residual_p95):
        ax_resid.axhline(residual_p95, color="red", linestyle=":", linewidth=1.2, label=f"±P95 |err| {residual_p95:.3g}")
        ax_resid.axhline(-residual_p95, color="red", linestyle=":", linewidth=1.2)
    ax_resid.set_xlim(start, end)
    ax_resid.set_title(
        "Residual range "
        f"min={residual_min:.3g}, max={residual_max:.3g}, "
        f"MAE={residual_mae:.3g}, RMSE={residual_rmse:.3g}, P95|err|={residual_p95:.3g}"
    )
    ax_resid.set_ylabel("Residual")
    ax_resid.set_xlabel("Timestamp")
    ax_resid.grid(True, alpha=0.25)
    ax_resid.legend(loc="upper right", fontsize=8, ncols=2)
    ax_resid.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%H:%M"))
    fig.autofmt_xdate()
    return fig, axes


def plot_temperature_relationship(
    df: pd.DataFrame,
    value_col: str,
    temp_col: str,
    *,
    sample_size: int | None = 50_000,
    random_state: int = 42,
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Scatter temperature vs value with a simple linear trend line."""

    _require_columns(df, [value_col, temp_col])
    data = df[[temp_col, value_col]].dropna()
    if sample_size is not None and len(data) > sample_size:
        data = data.sample(sample_size, random_state=random_state)

    x = pd.to_numeric(data[temp_col], errors="coerce")
    y = pd.to_numeric(data[value_col], errors="coerce")
    valid = x.notna() & y.notna()
    x = x[valid]
    y = y[valid]

    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 6))
    else:
        fig = ax.figure

    ax.scatter(x, y, s=8, alpha=0.25)

    if len(x) >= 2 and x.nunique() > 1:
        coef = np.polyfit(x.to_numpy(), y.to_numpy(), deg=1)
        trend_x = np.linspace(float(x.min()), float(x.max()), 100)
        trend_y = coef[0] * trend_x + coef[1]
        ax.plot(trend_x, trend_y, color="red", linewidth=2, label="linear trend")
        ax.legend()

    ax.set_title(f"Temperature relationship: {temp_col} vs {value_col}")
    ax.set_xlabel(temp_col)
    ax.set_ylabel(value_col)
    ax.grid(True, alpha=0.25)
    return fig, ax


def plot_error_by_temperature_bin(
    df: pd.DataFrame,
    y_true: str,
    y_pred: str,
    temp_col: str,
    *,
    bins: int | Sequence[float] = 10,
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Plot MAE and RMSE by temperature bin after model training."""

    _require_columns(df, [y_true, y_pred, temp_col])
    data = df[[y_true, y_pred, temp_col]].dropna().copy()
    data["_viz_error"] = data[y_true] - data[y_pred]
    data["_viz_abs_error"] = data["_viz_error"].abs()
    data["_viz_sq_error"] = data["_viz_error"] ** 2
    data["_viz_temp_bin"] = pd.cut(data[temp_col], bins=bins, include_lowest=True)

    metrics = (
        data.groupby("_viz_temp_bin", observed=True)
        .agg(
            mae=("_viz_abs_error", "mean"),
            rmse=("_viz_sq_error", lambda s: float(np.sqrt(np.mean(s)))),
            n=("_viz_error", "size"),
        )
        .reset_index()
    )
    metrics["_viz_temp_bin_label"] = metrics["_viz_temp_bin"].astype(str)

    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 5))
    else:
        fig = ax.figure

    x = np.arange(len(metrics))
    width = 0.38
    ax.bar(x - width / 2, metrics["mae"], width=width, label="MAE")
    ax.bar(x + width / 2, metrics["rmse"], width=width, label="RMSE")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics["_viz_temp_bin_label"], rotation=45, ha="right")
    ax.set_title(f"Error by temperature bin | temp={temp_col}")
    ax.set_xlabel("Temperature bin")
    ax.set_ylabel("Error")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    return fig, ax


def plot_distribution(
    df: pd.DataFrame,
    value_col: str,
    by: str | None = None,
    *,
    bins: int = 80,
    max_groups: int = 12,
    sample_size: int | None = 200_000,
    random_state: int = 42,
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Plot histogram + KDE for one value column, optionally grouped.

    ``by`` can be ``site_id``, ``season``, model version, outlier flag, etc.
    If too many groups exist, only the largest ``max_groups`` groups are shown.
    """

    needed = [value_col] if by is None else [value_col, by]
    _require_columns(df, needed)
    data = df[needed].dropna().copy()
    if sample_size is not None and len(data) > sample_size:
        data = data.sample(sample_size, random_state=random_state)

    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 5))
    else:
        fig = ax.figure

    if by is None:
        values = pd.to_numeric(data[value_col], errors="coerce").dropna()
        ax.hist(values, bins=bins, density=True, alpha=0.35, label="histogram")
        if len(values) > 1 and values.nunique() > 1:
            values.plot(kind="density", ax=ax, linewidth=2, label="KDE")
    else:
        top_groups = data[by].value_counts().head(max_groups).index
        for group_value in top_groups:
            group = pd.to_numeric(
                data.loc[data[by] == group_value, value_col],
                errors="coerce",
            ).dropna()
            if group.empty:
                continue
            ax.hist(group, bins=bins, density=True, alpha=0.18, label=str(group_value))
            if len(group) > 1 and group.nunique() > 1:
                group.plot(kind="density", ax=ax, linewidth=1.5)

    ax.set_title(f"Distribution: {value_col}" + (f" by {by}" if by else ""))
    ax.set_xlabel(value_col)
    ax.set_ylabel("Density")
    ax.grid(True, alpha=0.25)
    ax.legend(title=by, fontsize=8)
    return fig, ax


def plot_heatmap_site_hour(
    df: pd.DataFrame,
    value_col: str,
    agg: AggName = "mean",
    *,
    timestamp_col: str = DEFAULT_TIMESTAMP_COL,
    site_col: str | None = None,
    ax: Axes | None = None,
    cmap: str = "viridis",
) -> tuple[Figure, Axes]:
    """Plot Site x Hour heatmap for energy, outlier count, prediction error, etc."""

    resolved_site_col = _resolve_site_col(df, site_col)
    _require_columns(df, [timestamp_col, resolved_site_col, value_col])
    data = _add_time_features(df, timestamp_col=timestamp_col).dropna(
        subset=[resolved_site_col, "_viz_hour", value_col]
    )
    data["_viz_hour_int"] = np.floor(data["_viz_hour"]).astype(int)

    grouped = data.groupby([resolved_site_col, "_viz_hour_int"], observed=True)[value_col]
    matrix = _aggregate(grouped, agg).unstack("_viz_hour_int").sort_index()
    matrix = matrix.reindex(columns=range(24))

    if ax is None:
        fig, ax = plt.subplots(figsize=(13, max(5, len(matrix) * 0.18)))
    else:
        fig = ax.figure

    image = ax.imshow(matrix.to_numpy(), aspect="auto", cmap=cmap, interpolation="nearest")
    ax.set_title(f"Heatmap Site x Hour | {value_col} ({agg})")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel(resolved_site_col)
    ax.set_xticks(range(24))
    ax.set_xticklabels([str(h) for h in range(24)])
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels([str(v) for v in matrix.index])
    fig.colorbar(image, ax=ax, label=value_col)
    return fig, ax


def plot_correlation_heatmap(
    df: pd.DataFrame,
    cols: Sequence[str],
    *,
    method: Literal["pearson", "spearman", "kendall"] = "pearson",
    ax: Axes | None = None,
    cmap: str = "coolwarm",
    annotate: bool = True,
) -> tuple[Figure, Axes]:
    """Plot correlation heatmap for selected numeric columns."""

    _require_columns(df, list(cols))
    data = df.loc[:, list(cols)].apply(pd.to_numeric, errors="coerce")
    corr = data.corr(method=method)

    if ax is None:
        fig, ax = plt.subplots(figsize=(max(8, len(cols) * 0.8), max(6, len(cols) * 0.7)))
    else:
        fig = ax.figure

    image = ax.imshow(corr.to_numpy(), vmin=-1, vmax=1, cmap=cmap)
    ax.set_title(f"Correlation heatmap ({method})")
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.index)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.index)

    if annotate:
        for i in range(corr.shape[0]):
            for j in range(corr.shape[1]):
                value = corr.iat[i, j]
                if pd.isna(value):
                    label = "NA"
                    color = "black"
                else:
                    label = f"{value:.2f}"
                    color = "white" if abs(value) >= 0.6 else "black"
                ax.text(j, i, label, ha="center", va="center", fontsize=8, color=color)

    fig.colorbar(image, ax=ax, label="Correlation")
    return fig, ax


__all__ = [
    "plot_global_overview",
    "plot_seasonal_profile",
    "plot_local_zoom",
    "plot_actual_vs_pred",
    "plot_temperature_relationship",
    "plot_error_by_temperature_bin",
    "plot_distribution",
    "plot_heatmap_site_hour",
    "plot_correlation_heatmap",
]
