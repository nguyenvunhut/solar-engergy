#!/usr/bin/env python3
"""Regenerate report-ready GMM-IF figures from current audit data.

Purpose
-------
The old rolling/condition figure folders contain many historical experiments.
This script rebuilds a clean figure set for the current GMM-IF pipeline, using
only numeric audit outputs from the configured GMM-IF report folder:

    reports/gmm_if_report/03_gmm_if_full_audit.csv
    reports/gmm_if_report/02_gmm_if_site_summary.csv
    reports/gmm_if_report/08_decision_tree_segment_r2_summary.log

It does not read old PNG files and does not touch the database.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "02_transform" / "01_generate_outliers.yaml"

with CONFIG_PATH.open(encoding="utf-8") as file:
    CONFIG = yaml.safe_load(file)

OUT_DIR = ROOT / CONFIG["paths"]["iqr_out_dir"]
PIC_ROOT = ROOT / CONFIG["paths"]["iqr_pic_dir"]
REPORT_DIR = PIC_ROOT / "report_figures_gmm_if"

FULL_AUDIT_CSV = OUT_DIR / "03_gmm_if_full_audit.csv"
SITE_SUMMARY_CSV = OUT_DIR / "02_gmm_if_site_summary.csv"
R2_LOG = OUT_DIR / "08_decision_tree_segment_r2_summary.log"
RUN_LOG = OUT_DIR / "10_regenerate_report_figures.log"

SEASON_LABELS = {
    0: "summer",
    1: "autumn",
    2: "winter",
    3: "spring",
}


def add_caption(fig: plt.Figure, text: str) -> None:
    """Add a presentation-friendly caption under a figure."""
    fig.text(
        0.5,
        0.015,
        text,
        ha="center",
        va="bottom",
        fontsize=9,
        color="#222222",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#f7f7f7", "edgecolor": "#cccccc", "alpha": 0.95},
    )


def site_sort_key(value: object) -> tuple[int, str]:
    text = str(value)
    return (int(text), text) if text.isdigit() else (10**9, text)


def ensure_inputs() -> None:
    missing = [
        str(path)
        for path in [FULL_AUDIT_CSV, SITE_SUMMARY_CSV, R2_LOG]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(
            "Missing required audit files. Run 02_gmm_if.py and "
            "04_validate_decision_tree_r2.py first.\n"
            + "\n".join(missing)
        )


def read_r2_log(path: Path) -> pd.DataFrame:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("sitekey") and "energy_r2_mean" in line:
            start = idx
            break
    if start is None:
        raise RuntimeError(f"Cannot parse R² table from {path}")

    table_lines = []
    for line in lines[start:]:
        if not line.strip():
            break
        table_lines.append(line)

    header = table_lines[0].split()
    rows = []
    for line in table_lines[1:]:
        parts = line.split()
        if len(parts) == len(header):
            rows.append(dict(zip(header, parts)))

    df = pd.DataFrame(rows)
    df["sitekey"] = pd.to_numeric(df["sitekey"], errors="raise").astype(int)
    df["rows_scored_daytime"] = pd.to_numeric(
        df["rows_scored_daytime"], errors="raise"
    ).astype(int)
    df["leaf_segments"] = pd.to_numeric(df["leaf_segments"], errors="raise").astype(int)
    df["energy_r2_mean"] = pd.to_numeric(df["energy_r2_mean"], errors="raise")
    return df.sort_values("sitekey").reset_index(drop=True)


def load_audit() -> pd.DataFrame:
    columns = [
        "sitekey",
        "timestamp",
        "hour",
        "month",
        "season",
        "energy_generated_kwh",
        "energy_generated_kwh_raw",
        "shortwave_radiation",
        "expected_energy_by_radiation",
        "residual_vs_expected",
        "neighbor_delta",
        "is_night_zero",
        "segment_id",
        "gmm_flag",
        "if_flag",
        "gmm_if_consensus_flag",
        "physical_rule_flag",
        "is_outlier",
    ]
    df = pd.read_csv(FULL_AUDIT_CSV, usecols=columns, parse_dates=["timestamp"])
    df["sitekey"] = df["sitekey"].astype(str)
    return df


def plot_site_segments(
    site_df: pd.DataFrame,
    site: str,
    out_dir: Path,
    r2_value: float | None,
    leaf_segments: int | None,
) -> Path:
    """Figure 8 replacement: Decision Tree segments by season/hour."""
    day = site_df[
        (~site_df["is_night_zero"].astype(bool))
        & site_df["energy_generated_kwh"].notna()
        & site_df["segment_id"].notna()
    ].copy()
    out = out_dir / f"Figure_8_GMMIF_DecisionTree_Segments_Site_{site}.png"
    if day.empty:
        return out

    fig, axes = plt.subplots(2, 2, figsize=(15, 9.8), sharex=True, sharey=True)
    axes = axes.flatten()
    segments = sorted(day["segment_id"].unique())
    cmap = plt.get_cmap("tab20", max(3, len(segments)))
    colors = {seg: cmap(i % cmap.N) for i, seg in enumerate(segments)}

    for season_id in range(4):
        ax = axes[season_id]
        season_df = day[day["season"] == season_id]
        for seg, seg_df in season_df.groupby("segment_id", sort=True):
            ax.scatter(
                seg_df["hour"],
                seg_df["energy_generated_kwh"],
                s=5,
                alpha=0.35,
                color=colors.get(seg),
                linewidths=0,
            )
        ax.set_title(
            f"{SEASON_LABELS.get(season_id, season_id)} | rows={len(season_df):,}"
        )
        ax.grid(alpha=0.25)

    for ax in axes[2:]:
        ax.set_xlabel("Hour of day")
    for ax in [axes[0], axes[2]]:
        ax.set_ylabel("Energy generated (kWh)")
    fig.suptitle(
        f"Figure 8 replacement — Site {site}: Decision Tree segments by season",
        fontsize=14,
    )
    caption = (
        "Chú thích: mỗi màu là một leaf/segment do Decision Tree tạo ra theo giờ, mùa và bức xạ. "
        f"Site {site} có {leaf_segments if leaf_segments is not None else 'NA'} segment; "
        f"Energy R²={r2_value:.3f}" if r2_value is not None else
        "Chú thích: mỗi màu là một leaf/segment do Decision Tree tạo ra theo giờ, mùa và bức xạ."
    )
    add_caption(fig, caption)
    fig.tight_layout(rect=(0, 0.06, 1, 0.96))
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_site_outliers(site_df: pd.DataFrame, site: str, out_dir: Path) -> Path:
    """Figure 9 replacement: full time-series normal vs final outliers."""
    df = site_df[site_df["energy_generated_kwh"].notna()].copy()
    normal = df[~df["is_outlier"].astype(bool)]
    outliers = df[df["is_outlier"].astype(bool)]
    out = out_dir / f"Figure_9_GMMIF_Final_Outliers_Site_{site}.png"

    fig, ax = plt.subplots(figsize=(16, 5.8))
    ax.scatter(
        normal["timestamp"],
        normal["energy_generated_kwh"],
        s=3,
        alpha=0.35,
        color="#1f4e8c",
        linewidths=0,
        label=f"Normal ({len(normal):,})",
    )
    ax.scatter(
        outliers["timestamp"],
        outliers["energy_generated_kwh"],
        s=18,
        alpha=0.95,
        color="#d62728",
        marker="x",
        linewidths=0.9,
        label=f"Final outliers ({len(outliers):,})",
    )
    ax.set_title(f"Figure 9 replacement — Site {site}: GMM-IF final outliers")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Energy generated (kWh)")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right")
    final_pct = len(outliers) / max(len(df), 1) * 100
    ax.text(
        0.01,
        0.95,
        f"Final outliers={len(outliers):,} / {len(df):,} rows ({final_pct:.3f}%)",
        transform=ax.transAxes,
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9},
    )
    add_caption(
        fig,
        "Chú thích: điểm xanh là dữ liệu giữ lại; dấu X đỏ là dòng được flag cuối cùng "
        "(GMM∩IF hoặc physical guardrail). Hình dùng để kiểm tra phân bố outlier theo thời gian.",
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_site_daily_example(site_df: pd.DataFrame, site: str, out_dir: Path) -> Path:
    """One-day review view: resembles old per-condition daily scatter."""
    outlier_days = (
        site_df[site_df["is_outlier"].astype(bool)]
        .assign(date=lambda x: x["timestamp"].dt.date)
        .groupby("date")
        .size()
        .sort_values(ascending=False)
    )
    if outlier_days.empty:
        day = site_df["timestamp"].dt.date.mode().iloc[0]
    else:
        day = outlier_days.index[0]

    df = site_df[site_df["timestamp"].dt.date == day].copy()
    normal = df[~df["is_outlier"].astype(bool)]
    outliers = df[df["is_outlier"].astype(bool)]
    out = out_dir / f"Figure_10_GMMIF_Daily_Review_Site_{site}.png"

    fig, ax1 = plt.subplots(figsize=(13, 5.8))
    ax1.scatter(
        normal["hour"],
        normal["energy_generated_kwh"],
        s=22,
        color="#1f4e8c",
        alpha=0.75,
        label="Normal",
    )
    ax1.scatter(
        outliers["hour"],
        outliers["energy_generated_kwh"],
        s=70,
        color="#d62728",
        marker="x",
        linewidths=1.8,
        label="Final outlier",
    )
    ax1.plot(
        df["hour"],
        df["expected_energy_by_radiation"],
        color="#2ca02c",
        linewidth=1.4,
        alpha=0.85,
        label="Expected by radiation",
    )
    ax1.set_title(f"Figure 10 — Site {site}: daily review on {day}")
    ax1.set_xlabel("Hour of day")
    ax1.set_ylabel("Energy generated (kWh)")
    ax1.grid(alpha=0.25)
    ax1.legend(loc="upper left")

    ax2 = ax1.twinx()
    ax2.plot(
        df["hour"],
        df["shortwave_radiation"],
        color="#ff7f0e",
        linewidth=1.2,
        alpha=0.65,
        label="Shortwave radiation",
    )
    ax2.set_ylabel("Shortwave radiation")
    add_caption(
        fig,
        "Chú thích: ngày được chọn là ngày có nhiều final outlier nhất của site. "
        "Đường xanh lá là mức phát điện kỳ vọng theo bức xạ; đường cam là shortwave radiation.",
    )
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def plot_summary_figures(
    site_summary: pd.DataFrame,
    r2: pd.DataFrame,
    out_dir: Path,
) -> list[Path]:
    site_summary = site_summary.copy()
    site_summary["sitekey"] = site_summary["sitekey"].astype(int)
    site_summary = site_summary.sort_values("sitekey")
    r2 = r2.sort_values("sitekey")
    outputs: list[Path] = []

    out = out_dir / "Figure_11_Step1_DecisionTree_Energy_R2_By_Site.png"
    fig, ax = plt.subplots(figsize=(15, 5.8))
    ax.bar(r2["sitekey"].astype(str), r2["energy_r2_mean"], color="#2f6f9f")
    ax.axhline(r2["energy_r2_mean"].mean(), color="#d62728", linestyle="--")
    ax.set_ylim(0, 1)
    ax.set_title("Step 1 — Decision Tree segmentation R² by site")
    ax.set_xlabel("SiteKey")
    ax.set_ylabel("Energy R² mean")
    ax.grid(axis="y", alpha=0.25)
    ax.text(
        0.01,
        0.95,
        f"mean={r2['energy_r2_mean'].mean():.3f}; min={r2['energy_r2_mean'].min():.3f}; max={r2['energy_r2_mean'].max():.3f}",
        transform=ax.transAxes,
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )
    add_caption(
        fig,
        "Chú thích: R² đo mức Decision Tree segments giải thích profile phát điện ban ngày. "
        "Chỉ số này kiểm chứng bước segmentation trước khi đưa vào GMM/IF.",
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(out, dpi=160)
    plt.close(fig)
    outputs.append(out)

    out = out_dir / "Figure_12_Step2_GMM_IF_Votes_By_Site.png"
    fig, ax = plt.subplots(figsize=(16, 6.8))
    x = np.arange(len(site_summary))
    ax.plot(x, site_summary["gmm_flags"], marker="o", label="GMM candidates")
    ax.plot(x, site_summary["if_flags"], marker="o", label="IF candidates")
    ax.plot(
        x,
        site_summary["gmm_if_consensus_flags"],
        marker="o",
        linewidth=2,
        label="GMM ∩ IF consensus",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(site_summary["sitekey"].astype(str))
    ax.set_title("Step 2 — Candidate votes by site")
    ax.set_xlabel("SiteKey")
    ax.set_ylabel("Rows flagged")
    ax.grid(alpha=0.25)
    ax.legend()
    ax.text(
        0.01,
        0.95,
        f"GMM={int(site_summary['gmm_flags'].sum()):,}; IF={int(site_summary['if_flags'].sum()):,}; consensus={int(site_summary['gmm_if_consensus_flags'].sum()):,}",
        transform=ax.transAxes,
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9},
    )
    add_caption(
        fig,
        "Chú thích: GMM bắt ứng viên theo phân phối trong từng segment; IF là bộ kiểm tra độc lập. "
        "Đường consensus là các dòng được cả hai mô hình đồng thuận.",
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(out, dpi=160)
    plt.close(fig)
    outputs.append(out)

    out = out_dir / "Figure_13_Step3_Final_Outliers_By_Site.png"
    fig, ax = plt.subplots(figsize=(16, 6.8))
    ax.bar(x, site_summary["outliers_final"], color="#8e44ad", label="Final outliers")
    ax.plot(
        x,
        site_summary["physical_rule_flags"],
        color="#e67e22",
        marker="o",
        label="Physical guardrail",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(site_summary["sitekey"].astype(str))
    ax.set_title("Step 3 — Final outliers and physical guardrail by site")
    ax.set_xlabel("SiteKey")
    ax.set_ylabel("Rows")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    ax.text(
        0.01,
        0.95,
        f"final={int(site_summary['outliers_final'].sum()):,}; physical={int(site_summary['physical_rule_flags'].sum()):,}",
        transform=ax.transAxes,
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9},
    )
    add_caption(
        fig,
        "Chú thích: final outlier = GMM∩IF hoặc physical guardrail. "
        "Physical guardrail bảo vệ các ca trái vật lý rõ ràng như phát điện cao khi bức xạ thấp.",
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(out, dpi=160)
    plt.close(fig)
    outputs.append(out)

    out = out_dir / "Figure_14_Final_Outlier_Pct_By_Site.png"
    fig, ax = plt.subplots(figsize=(16, 5.8))
    ax.bar(site_summary["sitekey"].astype(str), site_summary["outlier_pct_of_day"], color="#c0392b")
    ax.axhline(site_summary["outlier_pct_of_day"].mean(), color="#111", linestyle="--")
    ax.set_title("Final audit — Outlier percentage of daytime rows by site")
    ax.set_xlabel("SiteKey")
    ax.set_ylabel("Outlier % of daytime rows")
    ax.grid(axis="y", alpha=0.25)
    ax.text(
        0.01,
        0.95,
        f"mean={site_summary['outlier_pct_of_day'].mean():.3f}%",
        transform=ax.transAxes,
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )
    add_caption(
        fig,
        "Chú thích: tỷ lệ outlier theo dòng ban ngày giúp chứng minh thuật toán không flag tràn lan; "
        "trung bình dưới 1% daytime rows.",
    )
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(out, dpi=160)
    plt.close(fig)
    outputs.append(out)

    return outputs


def main() -> int:
    ensure_inputs()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    audit = load_audit()
    site_summary = pd.read_csv(SITE_SUMMARY_CSV)
    r2 = read_r2_log(R2_LOG)
    outputs: list[Path] = []

    sites = sorted(audit["sitekey"].unique(), key=site_sort_key)
    for site in sites:
        site_df = audit[audit["sitekey"] == site].copy()
        r2_row = r2[r2["sitekey"].astype(str) == str(site)]
        r2_value = None if r2_row.empty else float(r2_row["energy_r2_mean"].iloc[0])
        leaf_segments = None if r2_row.empty else int(r2_row["leaf_segments"].iloc[0])
        outputs.append(
            plot_site_segments(
                site_df,
                site,
                REPORT_DIR,
                r2_value=r2_value,
                leaf_segments=leaf_segments,
            )
        )
        outputs.append(plot_site_outliers(site_df, site, REPORT_DIR))
        outputs.append(plot_site_daily_example(site_df, site, REPORT_DIR))
        print(f"generated site {site}: 3 figures")

    outputs.extend(plot_summary_figures(site_summary, r2, REPORT_DIR))

    log_lines = [
        "REGENERATED GMM-IF REPORT FIGURES",
        "=" * 72,
        f"output_dir={REPORT_DIR}",
        f"site_count={len(sites)}",
        f"figure_count={len(outputs)}",
        "",
        "Generated files:",
    ]
    log_lines.extend(f"  - {path}" for path in outputs)
    RUN_LOG.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print("\n".join(log_lines[:6]))
    print(f"log={RUN_LOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
