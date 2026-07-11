#!/usr/bin/env python3
"""
Export a read-only SQL query to one local Parquet file.

Default use case:
    ml_mart.base -> data/mlmart_base/v1_preprocessing.parquet

This script only runs SELECT queries. It sets the database transaction to
read-only before exporting, so it is safe to use against local Docker or
Supabase when the connection string points there.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys
from time import perf_counter

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_MODULE = PROJECT_ROOT / "srcs" / "00_utils" / "01_database.py"
DEFAULT_QUERY = "SELECT * FROM ml_mart.base"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "mlmart_base" / "v1_preprocessing.parquet"
DEFAULT_CHUNK_SIZE = 200_000

NULLABLE_INT_COLUMNS = (
    "gen_id",
    "site_id",
    "geo_id",
    "date_id",
    "time_id",
    "is_dst_repeat",
    "year",
    "month",
    "day",
    "day_of_week",
    "hour",
    "minute",
    "weather_id",
    "weather_type_id",
    "weather_is_day",
    "weather_code",
    "weather_type_is_day",
)

FLOAT_COLUMNS = (
    "energy_generated_kwh",
    "capacity_kw",
    "number_of_panels",
    "latitude",
    "longitude",
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
)

STRING_COLUMNS = (
    "campus_name",
    "panel",
    "inverter",
    "optimizers",
    "site_metric",
    "location_name",
    "weather_condition",
    "weather_description",
)


def load_database_module():
    spec = importlib.util.spec_from_file_location("pipeline_database", DATABASE_MODULE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load database module: {DATABASE_MODULE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["pipeline_database"] = module
    spec.loader.exec_module(module)
    return module


def normalize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Keep parquet schema stable across chunks."""
    for column in ("timestamp", "weather_timestamp", "full_date"):
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    for column in NULLABLE_INT_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")
    for column in FLOAT_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").astype("float64")
    for column in STRING_COLUMNS:
        if column in df.columns:
            df[column] = df[column].astype("string")
    if "gmm_if_outlier_flag" in df.columns:
        df["gmm_if_outlier_flag"] = df["gmm_if_outlier_flag"].astype("boolean")
    return df


def assert_select_only(query: str) -> None:
    normalized = query.strip().lower()
    if not normalized.startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")
    banned_tokens = (
        " insert ",
        " update ",
        " delete ",
        " drop ",
        " truncate ",
        " alter ",
        " create ",
        " grant ",
        " revoke ",
    )
    padded = f" {normalized} "
    matched = [token.strip() for token in banned_tokens if token in padded]
    if matched:
        raise ValueError(f"Query contains non-read-only token(s): {', '.join(matched)}")


def fetch_count(conn, query: str) -> int:
    count_query = f"SELECT COUNT(*) FROM ({query.rstrip(';')}) AS export_source"
    with conn.cursor() as cursor:
        cursor.execute(count_query)
        return int(cursor.fetchone()[0])


def iter_query_chunks(conn, query: str, chunk_size: int):
    """Stream query rows from PostgreSQL with a server-side cursor."""
    cursor = conn.cursor(name="query_to_parquet_export_cursor")
    cursor.itersize = chunk_size
    try:
        cursor.execute(query.rstrip(";"))
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
            if cursor.description is None:
                raise RuntimeError("Query did not return a result set. Only SELECT queries are supported.")
            columns = [desc[0] for desc in cursor.description]
            yield pd.DataFrame.from_records(rows, columns=columns)
    finally:
        cursor.close()


def export_query_to_parquet(
    *,
    query: str,
    output_path: Path,
    chunk_size: int,
    overwrite: bool,
) -> int:
    assert_select_only(query)

    if output_path.exists() and not overwrite:
        raise FileExistsError(f"{output_path} exists. Re-run with --overwrite to replace it.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    database = load_database_module()
    conn = database.get_psycopg2_connection()
    writer: pq.ParquetWriter | None = None
    rows_written = 0
    started = perf_counter()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SET default_transaction_read_only = on")
            cursor.execute("SET statement_timeout = '30min'")

        expected_rows = fetch_count(conn, query)
        print(f"Query rows expected: {expected_rows:,}")
        print(f"Output parquet     : {output_path}")
        print(f"Chunk size         : {chunk_size:,}")
        print("Mode               : DB read-only SELECT -> local parquet")

        for chunk_idx, chunk in enumerate(iter_query_chunks(conn, query, chunk_size), start=1):
            chunk = normalize_dtypes(chunk)
            table = pa.Table.from_pandas(chunk, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(output_path, table.schema, compression="snappy")
            writer.write_table(table)
            rows_written += len(chunk)
            print(
                f"  chunk={chunk_idx:>3} rows={len(chunk):>9,} "
                f"total={rows_written:>12,}",
                flush=True,
            )
    finally:
        if writer is not None:
            writer.close()
        conn.rollback()
        conn.close()

    size_mb = output_path.stat().st_size / (1024 * 1024)
    status = "PASS" if rows_written == expected_rows else "FAIL"
    print(
        f"\nDone: rows_written={rows_written:,} expected={expected_rows:,} "
        f"size={size_mb:.2f}MB status={status} elapsed={perf_counter() - started:.1f}s"
    )
    if status != "PASS":
        raise RuntimeError(f"Export row mismatch: wrote {rows_written:,}, expected {expected_rows:,}")
    return rows_written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--query",
        default=DEFAULT_QUERY,
        help=f"SELECT query to export. Default: {DEFAULT_QUERY}",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output parquet path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Rows per chunk. Default: {DEFAULT_CHUNK_SIZE:,}",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace output parquet if it already exists.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    export_query_to_parquet(
        query=args.query,
        output_path=Path(args.output).expanduser().resolve(),
        chunk_size=args.chunk_size,
        overwrite=args.overwrite,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
