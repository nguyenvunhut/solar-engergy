"""
GMM-IF outlier detection for PV solar generation time series.

Replaces the old rolling-IQR approach with the segmented GMM + Isolation Forest
fusion algorithm proposed by:

  Xin Li et al., "Outlier Detection of Photovoltaic Power Generation System
  Data Based on GMM-IF Algorithm", IEEE Access, Vol. 13, 2025.

Three stages per site (matches Figure 1 of the paper):

  1. Data segmentation with a regression decision tree over the daily solar
     profile. Each leaf becomes a segment where the distribution of energy
     is approximately Gaussian.
  2. Fit a Gaussian Mixture Model on each segment. Points with very low
     posterior probability inside their segment become GMM candidates.
  3. Fit an Isolation Forest on the full time series of that site as an
     independent judge. A point is flagged as an outlier only if BOTH the
     GMM-per-segment vote and the Isolation Forest agree.

Output paths (`iqr_out_dir` / `iqr_pic_dir` in the yaml) are reused so that
`03_export_csv.py` continues to work unchanged.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import IsolationForest
from sklearn.mixture import GaussianMixture
from sklearn.tree import DecisionTreeRegressor

pd.set_option("display.max_columns", 120)
pd.set_option("display.width", 180)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / "config" / "02_transform" / "01_generate_outliers.yaml"

with DEFAULT_CONFIG.open(encoding="utf-8") as _f:
    _cfg = yaml.safe_load(_f)

SOLAR_PATH = ROOT / _cfg["paths"]["parquet_dir"] / "temp_fact_solar_energy_gen.parquet"
WEATHER_PATH = ROOT / _cfg["paths"]["parquet_dir"] / "temp_fact_weather.parquet"
SITE_PATH = ROOT / _cfg["paths"]["parquet_dir"] / "temp_dim_solar_site.parquet"
OUT_DIR = ROOT / _cfg["paths"]["iqr_out_dir"]
PIC_DIR = ROOT / _cfg["paths"]["iqr_pic_dir"]
PRIMARY_CANDIDATES_PATH = ROOT / _cfg["paths"].get(
    "primary_outlier_candidates_csv",
    "reports/final_rolling_compare/24_strict_physical_confirmed_outliers_v3.csv",
)

# GMM-IF hyperparameters — reasonable defaults for 15-minute PV data.
TREE_MAX_DEPTH = int(_cfg.get("algorithm", {}).get("gmm_if_tree_max_depth", 5))
TREE_MIN_LEAF = int(_cfg.get("algorithm", {}).get("gmm_if_tree_min_leaf", 500))
GMM_COMPONENTS = int(_cfg.get("algorithm", {}).get("gmm_if_components", 2))
GMM_PROB_THRESHOLD = float(_cfg.get("algorithm", {}).get("gmm_if_prob_threshold", 0.02))
IF_CONTAMINATION = float(_cfg.get("algorithm", {}).get("gmm_if_if_contamination", 0.03))
IF_N_ESTIMATORS = int(_cfg.get("algorithm", {}).get("gmm_if_if_estimators", 100))
RANDOM_STATE = 42

OUT_DIR.mkdir(parents=True, exist_ok=True)
PIC_DIR.mkdir(parents=True, exist_ok=True)


NIGHT_ENERGY_THRESHOLD = float(
    _cfg.get("algorithm", {}).get("gmm_if_night_threshold_kwh", 0.05)
)
NIGHT_START_HOUR = float(
    _cfg.get("algorithm", {}).get("gmm_if_night_start_hour", 18.5)
)
NIGHT_END_HOUR = float(
    _cfg.get("algorithm", {}).get("gmm_if_night_end_hour", 5.5)
)


def _season_from_month(month: int) -> int:
    """Southern-hemisphere season index (0=summer, 1=autumn, 2=winter, 3=spring).

    Bendigo/Sydney PV data has strong seasonal power profiles. Splitting the
    decision tree by season lets each GMM fit a much tighter Gaussian.
    """
    if month in (12, 1, 2):
        return 0  # summer
    if month in (3, 4, 5):
        return 1  # autumn
    if month in (6, 7, 8):
        return 2  # winter
    return 3  # spring


def _add_weather_and_physical_features(solar: pd.DataFrame) -> pd.DataFrame:
    """Add exogenous PV physics features.

    GMM-IF alone only sees the generation time series. That misses obvious PV
    contradictions such as strong sunshine with near-zero generation, or high
    generation when radiation/sunshine is almost absent. These features let the
    model work on residuals against expected generation under comparable
    radiation conditions.
    """
    solar = solar.copy()
    weather_cols = [
        "is_day",
        "shortwave_radiation",
        "diffuse_solar_radiation",
        "direct_normal_irradiance",
        "cloud_cover_total",
        "precipitation_mm",
        "sunshine_duration",
    ]
    if WEATHER_PATH.exists():
        weather = pd.read_parquet(
            WEATHER_PATH,
            columns=["sitekey", "timestamp", *weather_cols],
        )
        weather["sitekey"] = weather["sitekey"].astype(str)
        weather["timestamp"] = pd.to_datetime(weather["timestamp"])
        left = (
            solar.sort_values(["timestamp", "sitekey"])
            .reset_index()
            .rename(columns={"index": "_orig_idx"})
        )
        right = weather.sort_values(["timestamp", "sitekey"])
        joined = pd.merge_asof(
            left,
            right,
            on="timestamp",
            by="sitekey",
            direction="nearest",
            tolerance=pd.Timedelta("30min"),
        ).sort_values("_orig_idx")
        for col in weather_cols:
            solar[col] = joined[col].to_numpy()
        solar["weather_unmatched"] = joined["shortwave_radiation"].isna().to_numpy()
    else:
        for col in weather_cols:
            solar[col] = np.nan
        solar["weather_unmatched"] = True

    # Keep unmatched weather as NaN. Do not convert it to "no sun": imputation
    # happens upstream, and this stage must not invent weather values.
    for col in weather_cols:
        solar[col] = pd.to_numeric(solar[col], errors="coerce")

    site_stats = (
        solar.groupby("sitekey")["energy_generated_kwh"]
        .agg(
            site_p95=lambda s: s.quantile(0.95),
            site_p99=lambda s: s.quantile(0.99),
        )
        .reset_index()
    )
    solar = solar.merge(site_stats, on="sitekey", how="left")
    if SITE_PATH.exists():
        site_meta = pd.read_parquet(
            SITE_PATH,
            columns=["sitekey", "capacity_kw", "number_of_panels", "panel", "inverter"],
        )
        site_meta["sitekey"] = site_meta["sitekey"].astype(str)
        solar = solar.merge(site_meta, on="sitekey", how="left")
    else:
        solar["capacity_kw"] = np.nan
        solar["number_of_panels"] = np.nan
        solar["panel"] = np.nan
        solar["inverter"] = np.nan

    solar["capacity_reference_kw"] = solar["capacity_kw"].where(
        solar["capacity_kw"].notna() & (solar["capacity_kw"] > 0),
        solar["site_p95"],
    )
    solar["capacity_source"] = np.where(
        solar["capacity_kw"].notna() & (solar["capacity_kw"] > 0),
        "metadata_capacity_kw",
        "fallback_site_p95",
    )

    bins = [-1, 0, 25, 50, 100, 200, 350, 500, 700, 900, 1200]
    labels = [
        "zero",
        "r001_025",
        "r026_050",
        "r051_100",
        "r101_200",
        "r201_350",
        "r351_500",
        "r501_700",
        "r701_900",
        "r901_plus",
    ]
    solar["radiation_bin"] = pd.cut(
        solar["shortwave_radiation"],
        bins=bins,
        labels=labels,
        include_lowest=True,
    )
    solar["radiation_bin"] = solar["radiation_bin"].astype("object")
    solar.loc[solar["weather_unmatched"], "radiation_bin"] = "weather_unmatched"

    def q(v: float):
        return lambda s: s.quantile(v)

    keys1 = ["sitekey", "season", "radiation_bin"]
    keys2 = ["sitekey", "radiation_bin"]
    stats1 = (
        solar.groupby(keys1, observed=False)["energy_generated_kwh"]
        .agg(
            exp_count="count",
            exp_median="median",
            exp_q1=q(0.25),
            exp_q3=q(0.75),
        )
        .reset_index()
    )
    stats2 = (
        solar.groupby(keys2, observed=False)["energy_generated_kwh"]
        .agg(
            fb_count="count",
            fb_median="median",
            fb_q1=q(0.25),
            fb_q3=q(0.75),
        )
        .reset_index()
    )
    solar = solar.merge(stats1, on=keys1, how="left").merge(stats2, on=keys2, how="left")
    for primary, fallback in [
        ("exp_count", "fb_count"),
        ("exp_median", "fb_median"),
        ("exp_q1", "fb_q1"),
        ("exp_q3", "fb_q3"),
    ]:
        solar[primary] = solar[primary].where(solar["exp_count"] >= 50, solar[fallback])

    solar["expected_energy_by_radiation"] = solar["exp_median"]
    solar["radiation_iqr"] = solar["exp_q3"] - solar["exp_q1"]
    solar["residual_vs_expected"] = (
        solar["energy_generated_kwh"] - solar["expected_energy_by_radiation"]
    )
    solar["residual_ratio"] = solar["energy_generated_kwh"] / solar[
        "expected_energy_by_radiation"
    ].where(solar["expected_energy_by_radiation"] != 0)
    solar["residual_ratio"] = solar["residual_ratio"].replace([np.inf, -np.inf], np.nan)

    # Local temporal context, excluding the current row.
    #
    # Important: the source time series has real timestamp gaps. Do not compare
    # a row after a multi-day gap with the row before the gap as if they were
    # adjacent 15-minute observations; that would create false "jump" evidence.
    solar = solar.sort_values(["sitekey", "timestamp"]).reset_index(drop=True)
    expected_step = pd.Timedelta("15min")
    for lag in (1, 2, 3, 4):
        prev_ts = solar.groupby("sitekey")["timestamp"].shift(lag)
        next_ts = solar.groupby("sitekey")["timestamp"].shift(-lag)
        prev_energy = solar.groupby("sitekey")["energy_generated_kwh"].shift(lag)
        next_energy = solar.groupby("sitekey")["energy_generated_kwh"].shift(-lag)
        prev_is_contiguous = (solar["timestamp"] - prev_ts) == lag * expected_step
        next_is_contiguous = (next_ts - solar["timestamp"]) == lag * expected_step
        solar[f"prev{lag}_energy"] = prev_energy.where(prev_is_contiguous)
        solar[f"next{lag}_energy"] = next_energy.where(next_is_contiguous)
    neighbor_cols = [f"prev{i}_energy" for i in (1, 2, 3, 4)] + [
        f"next{i}_energy" for i in (1, 2, 3, 4)
    ]
    solar["near_time_gap"] = solar[neighbor_cols].isna().any(axis=1)
    solar["neighbor_median_2h"] = solar[neighbor_cols].median(axis=1, skipna=True)
    solar["neighbor_delta"] = solar["energy_generated_kwh"] - solar["neighbor_median_2h"]

    energy = solar["energy_generated_kwh"]
    valid_weather = ~solar["weather_unmatched"]
    site_p95 = solar["site_p95"].fillna(0)
    capacity_ref = solar["capacity_reference_kw"].fillna(site_p95).fillna(0)
    safe_iqr = np.maximum(solar["radiation_iqr"].fillna(0), np.maximum(0.03 * site_p95, 0.1))
    expected_high = solar["expected_energy_by_radiation"] >= 0.20 * site_p95

    solar["physical_high_energy_no_sun"] = (
        valid_weather
        &
        (solar["shortwave_radiation"] <= 25)
        & (solar["sunshine_duration"] <= 60)
        & (energy >= np.maximum(1.0, 0.20 * capacity_ref))
    )
    solar["physical_high_energy_low_rad"] = (
        valid_weather
        &
        (solar["shortwave_radiation"] <= 50)
        & (energy >= np.maximum(1.0, 0.20 * capacity_ref))
        & (energy >= solar["exp_q3"].fillna(0) + 4 * safe_iqr)
    )
    solar["physical_low_energy_strong_sun"] = (
        valid_weather
        &
        (solar["shortwave_radiation"] >= 700)
        & (solar["sunshine_duration"] >= 3000)
        & expected_high
        & (energy <= 0.05 * site_p95)
        & (energy <= solar["exp_q1"].fillna(0) - 2 * safe_iqr)
    )
    solar["physical_distribution_jump"] = (
        valid_weather
        &
        ~solar["hour"].isin([5, 6, 18])
        & (
            (energy >= solar["exp_q3"].fillna(0) + 4 * safe_iqr)
            | (energy <= solar["exp_q1"].fillna(0) - 4 * safe_iqr)
        )
        & (solar["neighbor_delta"].abs() >= np.maximum(0.15 * site_p95, 1.0))
    )
    physical_cols = [
        "physical_high_energy_no_sun",
        "physical_high_energy_low_rad",
        "physical_low_energy_strong_sun",
        "physical_distribution_jump",
    ]
    solar["physical_rule_flag"] = solar[physical_cols].any(axis=1)
    solar["physical_evidence_count"] = solar[physical_cols].sum(axis=1)
    return solar


def load_solar() -> pd.DataFrame:
    if not SOLAR_PATH.exists():
        raise FileNotFoundError(f"Missing solar parquet: {SOLAR_PATH}")
    solar = pd.read_parquet(
        SOLAR_PATH, columns=["sitekey", "timestamp", "energy_generated_kwh"]
    )
    solar["timestamp"] = pd.to_datetime(solar["timestamp"])
    solar["sitekey"] = solar["sitekey"].astype(str)
    solar = solar.sort_values(["sitekey", "timestamp"]).reset_index(drop=True)
    solar["hour"] = solar["timestamp"].dt.hour
    solar["minute"] = solar["timestamp"].dt.minute
    solar["decimal_hour"] = solar["hour"] + solar["minute"] / 60.0
    solar["month"] = solar["timestamp"].dt.month
    solar["season"] = solar["month"].map(_season_from_month).astype(int)
    solar["day_of_year"] = solar["timestamp"].dt.dayofyear
    # Night flag must be derived from exogenous information only.
    #
    # Do NOT use energy_generated_kwh to decide whether a row is night:
    # low day-time generation can itself be the anomaly we want to detect.
    # Keep the energy-threshold flag only as an audit/debug diagnostic.
    solar["is_night_by_hour"] = (
        (solar["decimal_hour"] >= NIGHT_START_HOUR)
        | (solar["decimal_hour"] < NIGHT_END_HOUR)
    )
    solar["is_night_by_energy"] = (
        solar["energy_generated_kwh"].fillna(0) <= NIGHT_ENERGY_THRESHOLD
    )
    solar["is_night_zero"] = solar["is_night_by_hour"]

    # Preserve raw value for auditing, then clamp positive readings only during
    # clock-defined night. Day-time rows are untouched.
    solar["energy_generated_kwh_raw"] = solar["energy_generated_kwh"]
    night_noise_mask = solar["is_night_zero"] & (
        solar["energy_generated_kwh"].fillna(0) > 0
    )
    solar["night_noise_clamped"] = night_noise_mask
    solar.loc[night_noise_mask, "energy_generated_kwh"] = 0.0
    solar = _add_weather_and_physical_features(solar)
    return solar


SEGMENT_FEATURES = [
    "decimal_hour",
    "season",
    "shortwave_radiation",
    "expected_energy_by_radiation",
]
NIGHT_SEGMENT_ID = -100  # reserved id so night rows never collide with tree leaves


def segment_with_decision_tree(sub: pd.DataFrame) -> np.ndarray:
    """Stage 1 — regression decision tree over (hour, season) → segment ids.

    Night rows (`is_night_zero`) are pulled out into a dedicated segment so the
    tree does not waste splits chasing the huge 0 kWh cluster. Only the
    day-time rows feed the tree, which then produces tight leaves per season
    and time-of-day band.
    """
    day_mask = ~sub["is_night_zero"].to_numpy()
    valid_mask = sub["energy_generated_kwh"].notna().to_numpy() & day_mask
    leaves = np.full(len(sub), fill_value=-1, dtype=int)
    leaves[~day_mask] = NIGHT_SEGMENT_ID

    if valid_mask.sum() < TREE_MIN_LEAF * 2:
        # Not enough day-time samples to segment; treat everything as one bucket.
        leaves[day_mask] = 0
        return leaves

    X = sub.loc[valid_mask, SEGMENT_FEATURES].to_numpy()
    y = sub.loc[valid_mask, "residual_vs_expected"].to_numpy()
    tree = DecisionTreeRegressor(
        max_depth=TREE_MAX_DEPTH,
        min_samples_leaf=TREE_MIN_LEAF,
        random_state=RANDOM_STATE,
    ).fit(X, y)
    leaves[valid_mask] = tree.apply(X)

    # NaN rows (imputation gaps) that are during day — route them into the
    # nearest leaf so downstream logic still has a segment.
    day_but_nan = day_mask & ~valid_mask
    if day_but_nan.any():
        fill_X = sub.loc[day_but_nan, SEGMENT_FEATURES].to_numpy()
        leaves[day_but_nan] = tree.apply(fill_X)
    return leaves


def gmm_flag_per_segment(sub: pd.DataFrame, segments: np.ndarray) -> np.ndarray:
    """Stage 2 — per-segment GMM, flag rows whose posterior probability is small.

    Night-zero rows are skipped entirely: a value of ~0 kWh at night is the
    physical normal state, not an anomaly. Only the day-time segments produced
    by the decision tree are modelled.
    """
    energy = sub["residual_vs_expected"].to_numpy()
    flag = np.zeros(len(sub), dtype=bool)
    for seg_id in np.unique(segments):
        if seg_id == NIGHT_SEGMENT_ID:
            continue  # night 0 kWh is expected — do not GMM-flag
        seg_mask = segments == seg_id
        y = energy[seg_mask]
        y = y[~np.isnan(y)]
        if len(y) < 30:
            continue
        y2d = y.reshape(-1, 1)
        n_comp = min(GMM_COMPONENTS, max(1, len(np.unique(np.round(y, 3)))))
        try:
            gmm = GaussianMixture(
                n_components=n_comp,
                covariance_type="full",
                random_state=RANDOM_STATE,
                reg_covar=1e-4,
                max_iter=200,
            ).fit(y2d)
        except Exception:
            continue
        seg_energy = energy[seg_mask]
        valid_local = ~np.isnan(seg_energy)
        prob = np.zeros_like(seg_energy, dtype=float)
        if valid_local.any():
            densities = np.exp(gmm.score_samples(seg_energy[valid_local].reshape(-1, 1)))
            max_d = densities.max() if densities.size else 1.0
            prob[valid_local] = densities / max_d if max_d > 0 else 0.0
        seg_flag = np.zeros_like(seg_energy, dtype=bool)
        seg_flag[valid_local] = prob[valid_local] < GMM_PROB_THRESHOLD
        flag[seg_mask] = seg_flag
    return flag


def isolation_forest_flag(sub: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Stage 3 — Isolation Forest on the whole site's DAY-TIME series.

    Fitting IF only on day-time rows keeps `contamination` meaningful: 3% of
    ~30k daytime rows is the anomaly budget the paper describes, versus 3% of
    the full 65k-row series which would be dominated by night 0-kWh points.
    """
    features = sub[
        [
            "energy_generated_kwh",
            "residual_vs_expected",
            "residual_ratio",
            "decimal_hour",
            "month",
            "shortwave_radiation",
            "sunshine_duration",
            "cloud_cover_total",
            "expected_energy_by_radiation",
        ]
    ].to_numpy()
    day = (~sub["is_night_zero"].to_numpy()) & (~np.isnan(features).any(axis=1))
    flag = np.zeros(len(sub), dtype=bool)
    score = np.zeros(len(sub), dtype=float)
    if day.sum() < 100:
        return flag, score
    iso = IsolationForest(
        n_estimators=IF_N_ESTIMATORS,
        contamination=IF_CONTAMINATION,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ).fit(features[day])
    pred = iso.predict(features[day])
    raw_score = -iso.score_samples(features[day])  # higher = more anomalous
    flag[day] = pred == -1
    score[day] = raw_score
    return flag, score


def run_gmm_if_per_site(sub: pd.DataFrame) -> pd.DataFrame:
    sub = sub.reset_index(drop=True).copy()
    sub["segment_id"] = segment_with_decision_tree(sub)
    sub["gmm_flag"] = gmm_flag_per_segment(sub, sub["segment_id"].to_numpy())
    if_flag, if_score = isolation_forest_flag(sub)
    sub["if_flag"] = if_flag
    sub["if_anomaly_score"] = if_score
    sub["gmm_if_consensus_flag"] = sub["gmm_flag"] & sub["if_flag"]
    sub["is_outlier"] = sub["gmm_if_consensus_flag"] | sub["physical_rule_flag"]
    return sub


def plot_site(sub: pd.DataFrame, site: str, out_dir: Path) -> None:
    """Figure 9 style — blue circles = normal, red crosses = outliers."""
    df = sub.dropna(subset=["energy_generated_kwh"]).copy()
    fig, ax = plt.subplots(figsize=(14, 5))
    normal = df.loc[~df["is_outlier"]]
    outliers = df.loc[df["is_outlier"]]
    ax.scatter(
        normal["timestamp"],
        normal["energy_generated_kwh"],
        s=6,
        alpha=0.55,
        c="#1f4e8c",
        marker="o",
        label="Normal points",
    )
    ax.scatter(
        outliers["timestamp"],
        outliers["energy_generated_kwh"],
        s=18,
        c="#d62728",
        marker="x",
        label=f"Outliers (n={len(outliers):,})",
    )
    ax.set_title(f"Site {site} — GMM-IF outlier detection")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Energy generated (kWh)")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / f"gmm_if_site_{site}.png", dpi=150)
    plt.close(fig)


SEASON_LABELS = {0: "summer", 1: "autumn", 2: "winter", 3: "spring"}


def plot_segmentation(sub: pd.DataFrame, site: str, out_dir: Path) -> None:
    """Figure 8 style — colored segments after decision-tree partition.

    One panel per season so anh can eyeball the seasonal shape of PV output
    in Bendigo (Southern-hemisphere summer peak in Dec-Feb, winter dip Jun-Aug).
    """
    df = sub.dropna(subset=["energy_generated_kwh"]).copy()
    df = df[df["segment_id"] != NIGHT_SEGMENT_ID]
    if df.empty:
        return
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), sharex=True, sharey=True)
    axes = axes.flatten()
    segments = np.unique(df["segment_id"])
    cmap = plt.get_cmap("tab20", max(3, len(segments)))
    seg_to_color = {seg: cmap(i) for i, seg in enumerate(segments)}
    for season_id in range(4):
        ax = axes[season_id]
        season_df = df[df["season"] == season_id]
        for seg in np.unique(season_df["segment_id"]):
            seg_df = season_df[season_df["segment_id"] == seg]
            ax.scatter(
                seg_df["decimal_hour"],
                seg_df["energy_generated_kwh"],
                s=6,
                alpha=0.5,
                color=seg_to_color[seg],
                label=f"seg {seg}",
            )
        ax.set_title(f"{SEASON_LABELS[season_id]} (n={len(season_df):,})")
        ax.grid(alpha=0.3)
        if season_df.shape[0]:
            ax.legend(loc="upper right", fontsize=7, ncol=2)
    for ax in axes[2:]:
        ax.set_xlabel("Hour of day")
    for i in (0, 2):
        axes[i].set_ylabel("Energy generated (kWh)")
    fig.suptitle(
        f"Site {site} — Decision-tree segments per season (Stage 1)",
        fontsize=13,
    )
    fig.tight_layout()
    fig.savefig(out_dir / f"gmm_if_segments_site_{site}.png", dpi=150)
    plt.close(fig)


def explain_outlier_row(row: pd.Series) -> str:
    """Return a compact human-readable explanation for one flagged row."""
    reasons: list[str] = []
    if bool(row.get("gmm_if_consensus_flag", False)):
        reasons.append("GMM_IF_CONSENSUS")
    if bool(row.get("physical_high_energy_no_sun", False)):
        reasons.append("PHYSICAL_HIGH_ENERGY_NO_SUN")
    if bool(row.get("physical_high_energy_low_rad", False)):
        reasons.append("PHYSICAL_HIGH_ENERGY_LOW_RADIATION")
    if bool(row.get("physical_low_energy_strong_sun", False)):
        reasons.append("PHYSICAL_LOW_ENERGY_STRONG_SUN")
    if bool(row.get("physical_distribution_jump", False)):
        reasons.append("PHYSICAL_DISTRIBUTION_JUMP")
    if not reasons:
        reasons.append("FINAL_FLAG")
    return "+".join(reasons)


def format_review_row(row: pd.Series, *, prefix: str) -> str:
    return " | ".join(
        [
            prefix,
            f"sitekey={row['sitekey']}",
            f"timestamp={row['timestamp']}",
            f"hour={int(row['hour']) if pd.notna(row['hour']) else 'NA'}",
            f"energy={row['energy_generated_kwh']:.6g}",
            f"raw_energy={row['energy_generated_kwh_raw']:.6g}",
            f"shortwave={row['shortwave_radiation']:.6g}",
            f"expected={row['expected_energy_by_radiation']:.6g}",
            f"residual={row['residual_vs_expected']:.6g}",
            f"neighbor_delta={row['neighbor_delta']:.6g}",
            f"gmm={bool(row['gmm_flag'])}",
            f"if={bool(row['if_flag'])}",
            f"physical={bool(row['physical_rule_flag'])}",
            f"near_gap={bool(row['near_time_gap'])}",
            f"reason={explain_outlier_row(row)}",
        ]
    )


def write_and_print_outlier_review(
    all_result: pd.DataFrame,
    candidates: pd.DataFrame,
    out_dir: Path,
    *,
    terminal_rows_per_site: int = 10,
    context_window: int = 2,
) -> None:
    """Persist full outlier log, print a bounded per-site review to terminal.

    Terminal output is capped at `terminal_rows_per_site` outliers per sitekey.
    If an outlier uses time-neighbor evidence, print +/- `context_window` rows
    from the same site so reviewers can see the local time context.
    """
    full_review_path = out_dir / "06_gmm_if_outlier_full_review.log"
    terminal_review_path = out_dir / "07_gmm_if_outlier_terminal_review.log"
    rows = candidates.sort_values(["sitekey", "timestamp"]).reset_index(drop=True)
    header = [
        "GMM-IF OUTLIER REVIEW",
        f"total_outlier_rows={len(rows):,}",
        (
            "columns: idx | sitekey | timestamp | hour | energy | raw_energy | "
            "shortwave | expected | residual | neighbor_delta | gmm | if | "
            "physical | near_gap | reason"
        ),
    ]
    full_lines = header.copy()
    for idx, row in rows.iterrows():
        full_lines.append(format_review_row(row, prefix=f"idx={idx + 1}"))

    terminal_lines = [
        "GMM-IF OUTLIER TERMINAL REVIEW",
        (
            f"showing up to {terminal_rows_per_site} outliers per sitekey; "
            f"time-context rows +/-{context_window} only for neighbor/time-gap evidence"
        ),
        f"total_outlier_rows={len(rows):,}",
    ]
    context_source = all_result.sort_values(["sitekey", "timestamp"]).reset_index(drop=True)
    for site, site_candidates in rows.groupby("sitekey", sort=True):
        site_candidates = site_candidates.sort_values("timestamp").head(terminal_rows_per_site)
        terminal_lines.append("")
        terminal_lines.append(f"sitekey={site} | printed_outliers={len(site_candidates)}")
        site_all = context_source[context_source["sitekey"].astype(str) == str(site)].reset_index(drop=True)
        for _, row in site_candidates.iterrows():
            reason = explain_outlier_row(row)
            terminal_lines.append(format_review_row(row, prefix="OUTLIER"))
            needs_time_context = bool(row.get("physical_distribution_jump", False)) or bool(
                row.get("near_time_gap", False)
            )
            if not needs_time_context:
                continue
            matches = site_all.index[
                site_all["timestamp"].astype(str) == str(row["timestamp"])
            ].tolist()
            if not matches:
                continue
            pos = matches[0]
            start = max(0, pos - context_window)
            end = min(len(site_all), pos + context_window + 1)
            for ctx_pos in range(start, end):
                ctx = site_all.iloc[ctx_pos]
                rel = ctx_pos - pos
                if rel == 0:
                    continue
                terminal_lines.append(
                    format_review_row(ctx, prefix=f"CTX{rel:+d} reason_context_for={reason}")
                )

    full_review_path.write_text("\n".join(full_lines) + "\n", encoding="utf-8")
    terminal_review_path.write_text("\n".join(terminal_lines) + "\n", encoding="utf-8")
    print()
    for line in terminal_lines:
        print(line)


def main() -> None:
    solar = load_solar()
    print(f"Loaded {len(solar):,} rows across {solar['sitekey'].nunique()} sites")

    load_audit = pd.DataFrame(
        [
            {
                "solar_rows": len(solar),
                "site_count": solar["sitekey"].nunique(),
                "min_timestamp": solar["timestamp"].min(),
                "max_timestamp": solar["timestamp"].max(),
                "energy_null_rows": int(solar["energy_generated_kwh"].isna().sum()),
                "energy_negative_rows": int((solar["energy_generated_kwh"] < 0).sum()),
            }
        ]
    )
    load_audit.to_csv(OUT_DIR / "01_load_audit.csv", index=False)
    print(load_audit.to_string(index=False))

    processed_frames = []
    per_site_summary = []
    plotted_sites = set()
    sites_sorted = sorted(
        solar["sitekey"].unique(),
        key=lambda x: int(x) if str(x).isdigit() else str(x),
    )
    for site in sites_sorted:
        sub = solar[solar["sitekey"] == site]
        result = run_gmm_if_per_site(sub)
        processed_frames.append(result)
        n_out = int(result["is_outlier"].sum())
        n_valid = int(result["energy_generated_kwh"].notna().sum())
        night_rows = int(result["is_night_zero"].sum())
        day_rows = n_valid - night_rows
        per_site_summary.append(
            {
                "sitekey": site,
                "rows_total": len(result),
                "rows_valid": n_valid,
                "rows_day": day_rows,
                "rows_night_zero": night_rows,
                "gmm_flags": int(result["gmm_flag"].sum()),
                "if_flags": int(result["if_flag"].sum()),
                "gmm_if_consensus_flags": int(result["gmm_if_consensus_flag"].sum()),
                "physical_rule_flags": int(result["physical_rule_flag"].sum()),
                "outliers_final": n_out,
                "outlier_pct_of_day": (
                    n_out / day_rows * 100 if day_rows else 0.0
                ),
            }
        )
        print(
            f"  site {site:>3} | rows_valid={n_valid:>7,} "
            f"| gmm={int(result['gmm_flag'].sum()):>5,} "
            f"| if={int(result['if_flag'].sum()):>5,} "
            f"| phys={int(result['physical_rule_flag'].sum()):>5,} "
            f"| out={n_out:>5,}"
        )
        # Plot the first 6 sites to mimic the paper figure layout.
        if len(plotted_sites) < 6:
            plot_site(result, site, PIC_DIR)
            plot_segmentation(result, site, PIC_DIR)
            plotted_sites.add(site)

    all_result = pd.concat(processed_frames, ignore_index=True)

    summary = pd.DataFrame(per_site_summary)
    summary.to_csv(OUT_DIR / "02_gmm_if_site_summary.csv", index=False)

    audit_cols = [
        "sitekey",
        "timestamp",
        "hour",
        "month",
        "season",
        "energy_generated_kwh",
        "energy_generated_kwh_raw",
        "shortwave_radiation",
        "sunshine_duration",
        "cloud_cover_total",
        "precipitation_mm",
        "weather_unmatched",
        "capacity_kw",
        "number_of_panels",
        "capacity_reference_kw",
        "capacity_source",
        "radiation_bin",
        "expected_energy_by_radiation",
        "residual_vs_expected",
        "residual_ratio",
        "near_time_gap",
        "neighbor_median_2h",
        "neighbor_delta",
        "is_night_by_hour",
        "is_night_by_energy",
        "is_night_zero",
        "night_noise_clamped",
        "segment_id",
        "gmm_flag",
        "if_flag",
        "if_anomaly_score",
        "gmm_if_consensus_flag",
        "physical_high_energy_no_sun",
        "physical_high_energy_low_rad",
        "physical_low_energy_strong_sun",
        "physical_distribution_jump",
        "physical_evidence_count",
        "physical_rule_flag",
        "is_outlier",
    ]
    all_result[audit_cols].to_csv(OUT_DIR / "03_gmm_if_full_audit.csv", index=False)

    candidates = all_result[all_result["is_outlier"]].copy()
    write_and_print_outlier_review(all_result, candidates, OUT_DIR)

    candidates_for_downstream = candidates[
        ["sitekey", "timestamp", "hour", "energy_generated_kwh"]
    ].sort_values(["sitekey", "timestamp"])
    PRIMARY_CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    candidates_for_downstream.to_csv(PRIMARY_CANDIDATES_PATH, index=False)

    method_summary = pd.DataFrame(
        [
            {
                "method": "gmm_if_stage1_decision_tree_segments",
                "flagged_rows": int(all_result["segment_id"].notna().sum()),
            },
            {
                "method": "gmm_if_stage2_gmm_low_probability",
                "flagged_rows": int(all_result["gmm_flag"].sum()),
            },
            {
                "method": "gmm_if_stage3_isolation_forest",
                "flagged_rows": int(all_result["if_flag"].sum()),
            },
            {
                "method": "gmm_if_consensus (GMM & IF)",
                "flagged_rows": int(all_result["gmm_if_consensus_flag"].sum()),
            },
            {
                "method": "physical_guardrail",
                "flagged_rows": int(all_result["physical_rule_flag"].sum()),
            },
            {
                "method": "final_outlier (GMM_IF OR physical_guardrail)",
                "flagged_rows": int(all_result["is_outlier"].sum()),
            },
        ]
    )
    method_summary["pct_of_total"] = (
        method_summary["flagged_rows"] / len(all_result) * 100
    )
    method_summary.to_csv(OUT_DIR / "09_method_candidate_summary.csv", index=False)
    print()
    print(method_summary.to_string(index=False))

    # Overall pipeline evaluation figure (Figure 11-style).
    fig, ax = plt.subplots(figsize=(12, 5))
    stage_names = [
        "GMM only",
        "IF only",
        "GMM ∧ IF",
        "Physical",
        "Final",
    ]
    stage_counts = [
        int(all_result["gmm_flag"].sum()),
        int(all_result["if_flag"].sum()),
        int(all_result["gmm_if_consensus_flag"].sum()),
        int(all_result["physical_rule_flag"].sum()),
        int(all_result["is_outlier"].sum()),
    ]
    ax.bar(stage_names, stage_counts, color=["#4c78a8", "#f58518", "#9d755d", "#e45756", "#54a24b"])
    for i, v in enumerate(stage_counts):
        ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("Rows flagged")
    ax.set_title("GMM-IF stage comparison — flagged rows across the whole dataset")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(PIC_DIR / "gmm_if_stage_comparison.png", dpi=150)
    plt.close(fig)

    print(f"\nWrote per-site figures + summary to {PIC_DIR}")
    print(f"CSV outputs in {OUT_DIR}")


if __name__ == "__main__":
    main()
