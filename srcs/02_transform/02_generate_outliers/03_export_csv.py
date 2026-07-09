#!/usr/bin/env python3
"""
Export final outlier flag CSVs for review before any Supabase upload.

Input is the promoted candidate CSV from the configured outlier detector.
The output column is `gmm_if_outlier_flag`, the only outlier flag persisted by
the refactored pipeline.

This script does not write to Supabase.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / "config" / "02_transform" / "01_generate_outliers.yaml"

with DEFAULT_CONFIG.open(encoding="utf-8") as _f:
    _cfg = yaml.safe_load(_f)

SOLAR_PATH = ROOT / _cfg["paths"]["parquet_dir"] / "temp_fact_solar_energy_gen.parquet"
PRIMARY_CANDIDATES_PATH = ROOT / _cfg["paths"]["primary_outlier_candidates_csv"]
OUT_DIR = ROOT / _cfg["paths"]["outlier_out_dir"]

KEY_COLS = ["sitekey", "timestamp"]


def normalize_keys(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["sitekey"] = df["sitekey"].astype(str)
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def read_candidate_keys(path: Path, flag_name: str, reason_col_name: str | None = None) -> pd.DataFrame:
    if not path.exists():
        cols = KEY_COLS + [flag_name]
        if reason_col_name:
            cols.append(reason_col_name)
        return pd.DataFrame(columns=cols)
    usecols = set(KEY_COLS + (["outlier_reason"] if reason_col_name else []))
    df = pd.read_csv(path, usecols=lambda c: c in usecols)
    df = normalize_keys(df).drop_duplicates(KEY_COLS)
    df[flag_name] = True
    if reason_col_name and "outlier_reason" in df.columns:
        df = df.rename(columns={"outlier_reason": reason_col_name})
    elif reason_col_name:
        df[reason_col_name] = "UNKNOWN"
    return df


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    solar = pd.read_parquet(SOLAR_PATH, columns=["sitekey", "timestamp", "energy_generated_kwh"])
    solar = normalize_keys(solar)
    solar["hour"] = pd.to_datetime(solar["timestamp"]).dt.hour

    candidate_frames = [
        read_candidate_keys(PRIMARY_CANDIDATES_PATH, "gmm_if_outlier_flag", "gmm_if_outlier_reason"),
    ]

    flags = solar
    for frame in candidate_frames:
        flags = flags.merge(frame, on=KEY_COLS, how="left")

    flag_cols = ["gmm_if_outlier_flag"]
    for col in flag_cols:
        flags[col] = flags[col].fillna(False).astype(bool)
        
    if "gmm_if_outlier_reason" in flags.columns:
        flags["gmm_if_outlier_reason"] = flags["gmm_if_outlier_reason"].fillna("")

    full_path = ROOT / _cfg["paths"]["full_outlier_csv"]
    candidates_path = ROOT / _cfg["paths"]["sparse_outlier_csv"]
    summary_path = OUT_DIR / "03_gmm_if_flag_summary.csv"
    overlap_path = OUT_DIR / "04_gmm_if_flag_overlap_matrix.csv"
    manifest_path = OUT_DIR / "05_gmm_if_rule_manifest.csv"
    checksums_path = OUT_DIR / "99_sha256_checksums.csv"

    write_csv(flags, full_path)
    write_csv(flags[flags["gmm_if_outlier_flag"]].copy(), candidates_path)

    total_rows = len(flags)
    summary_rows = []
    for col in flag_cols:
        n = int(flags[col].sum())
        summary_rows.append(
            {
                "flag": col,
                "rows": n,
                "pct_of_total": n / total_rows * 100,
            }
        )
    keep_rows = int((~flags["gmm_if_outlier_flag"]).sum())
    summary_rows.append(
        {
            "flag": "keep_raw",
            "rows": keep_rows,
            "pct_of_total": keep_rows / total_rows * 100,
        }
    )
    summary = pd.DataFrame(summary_rows)
    write_csv(summary, summary_path)

    overlap_records = []
    for left in flag_cols:
        for right in flag_cols:
            overlap_records.append(
                {
                    "left_flag": left,
                    "right_flag": right,
                    "overlap_rows": int((flags[left] & flags[right]).sum()),
                }
            )
    write_csv(pd.DataFrame(overlap_records), overlap_path)

    manifest = pd.DataFrame(
        [
            {
                "flag": "gmm_if_outlier_flag",
                "source_file": str(PRIMARY_CANDIDATES_PATH.relative_to(ROOT)),
                "rule": "GMM-IF with radiation/weather residual features OR strict physical guardrail",
                "role": "main verified 15-minute generation outlier flag",
            },
        ]
    )
    write_csv(manifest, manifest_path)

    checksum_rows = []
    for path in [full_path, candidates_path, summary_path, overlap_path, manifest_path]:
        checksum_rows.append(
            {
                "file": str(path.relative_to(ROOT)),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    write_csv(pd.DataFrame(checksum_rows), checksums_path)

    print("Outlier flag export complete")
    print(f"rows={total_rows:,}")
    print(summary.to_string(index=False))
    print(f"output_dir={OUT_DIR}")


if __name__ == "__main__":
    main()
