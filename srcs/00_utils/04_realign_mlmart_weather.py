#!/usr/bin/env python3
"""Realign hourly weather to 15-minute ML-mart rows without future weather."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "data/mlmart_base/v3_preprocessing.parquet"
WEATHER_COLUMNS = (
    "weather_id",
    "weather_type_id",
    "weather_timestamp",
    "weather_is_day",
    "shortwave_radiation",
    "direct_normal_irradiance",
    "diffuse_solar_radiation",
    "temperature_c",
    "cloud_cover_total",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "wind_speed",
    "precipitation_mm",
    "sunshine_duration",
    "weather_code",
    "weather_type_is_day",
    "weather_condition",
    "weather_description",
)
LOOKUP_KEY = ("site_id", "_weather_hour")


def load_hourly_lookup(parquet_path: Path) -> pd.DataFrame:
    """Use rows at minute 00 as the authoritative hourly weather observations."""
    parquet = pq.ParquetFile(parquet_path)
    columns = ["site_id", "timestamp", "minute", *WEATHER_COLUMNS]
    chunks: list[pd.DataFrame] = []

    for batch in parquet.iter_batches(batch_size=250_000, columns=columns):
        frame = batch.to_pandas()
        frame = frame.loc[frame["minute"].eq(0)].copy()
        if frame.empty:
            continue
        frame["_weather_hour"] = pd.to_datetime(frame["timestamp"], errors="raise")
        chunks.append(frame[[*LOOKUP_KEY, *WEATHER_COLUMNS]])

    if not chunks:
        raise RuntimeError("No minute-00 weather rows found in input parquet")

    lookup = pd.concat(chunks, ignore_index=True)
    lookup = lookup.sort_values([*LOOKUP_KEY, "weather_id"], kind="stable")
    lookup = lookup.drop_duplicates(list(LOOKUP_KEY), keep="first")
    lookup = lookup.set_index(list(LOOKUP_KEY))
    return lookup


def realign_batch(frame: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
    """Replace weather with the latest hourly row available at source timestamp."""
    timestamp = pd.to_datetime(frame["timestamp"], errors="raise")
    keys = pd.MultiIndex.from_arrays(
        [frame["site_id"].to_numpy(), timestamp.dt.floor("h").to_numpy()],
        names=LOOKUP_KEY,
    )
    aligned = lookup.reindex(keys).reset_index(drop=True)

    # Preserve the old interval bucket for audit, but restore real clock hour.
    frame["interval_hour"] = frame["hour"]
    frame["hour"] = timestamp.dt.hour.astype(frame["hour"].dtype)

    for column in WEATHER_COLUMNS:
        frame[column] = aligned[column].to_numpy()

    matched = frame["weather_id"].notna()
    frame["weather_join_method"] = np.where(
        matched,
        "raw_hour_causal_manual",
        "missing_weather",
    )
    return frame


def audit_output(path: Path, expected_rows: int) -> dict[str, int | bool]:
    parquet = pq.ParquetFile(path)
    rows = parquet.metadata.num_rows
    future_weather = 0
    hour_mismatch = 0
    missing_weather = 0

    for batch in parquet.iter_batches(
        batch_size=250_000,
        columns=["timestamp", "weather_timestamp", "hour", "weather_id"],
    ):
        frame = batch.to_pandas()
        timestamp = pd.to_datetime(frame["timestamp"], errors="raise")
        weather_timestamp = pd.to_datetime(
            frame["weather_timestamp"], errors="coerce"
        )
        future_weather += int((weather_timestamp > timestamp).sum())
        hour_mismatch += int((frame["hour"] != timestamp.dt.hour).sum())
        missing_weather += int(frame["weather_id"].isna().sum())

    return {
        "rows": rows,
        "row_count_ok": rows == expected_rows,
        "future_weather_rows": future_weather,
        "clock_hour_mismatch_rows": hour_mismatch,
        "missing_weather_rows": missing_weather,
    }


def run(input_path: Path, output_path: Path, replace_input: bool) -> None:
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    if input_path == output_path:
        raise ValueError("Output must be a temporary path, not the input path")

    source = pq.ParquetFile(input_path)
    expected_rows = source.metadata.num_rows
    lookup = load_hourly_lookup(input_path)
    writer: pq.ParquetWriter | None = None
    rows_written = 0

    try:
        for row_group in range(source.num_row_groups):
            frame = source.read_row_group(row_group).to_pandas()
            frame = realign_batch(frame, lookup)
            table = pa.Table.from_pandas(frame, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(
                    output_path,
                    table.schema,
                    compression="snappy",
                )
            writer.write_table(table)
            rows_written += len(frame)
            print(
                f"row_group={row_group + 1}/{source.num_row_groups} "
                f"rows_written={rows_written:,}",
                flush=True,
            )
    finally:
        if writer is not None:
            writer.close()

    audit = audit_output(output_path, expected_rows)
    print(f"Audit: {audit}")
    if (
        not audit["row_count_ok"]
        or audit["future_weather_rows"] != 0
        or audit["clock_hour_mismatch_rows"] != 0
    ):
        raise RuntimeError(f"Causal weather audit failed: {audit}")

    if replace_input:
        os.replace(output_path, input_path)
        print(f"Replaced input atomically: {input_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_INPUT.with_name("v3_preprocessing_causal_tmp.parquet"),
    )
    parser.add_argument(
        "--replace-input",
        action="store_true",
        help="Atomically replace --input after the output passes audit.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.input, args.output, args.replace_input)
