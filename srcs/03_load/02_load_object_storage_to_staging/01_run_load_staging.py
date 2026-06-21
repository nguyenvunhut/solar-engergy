"""Load objects into PostgreSQL staging using manager-provided dependencies."""

from __future__ import annotations

import time

import pandas as pd
from sqlalchemy import text


def get_table_columns(engine: any, schema: str, table: str) -> list[str]:
    sql = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = :schema AND table_name = :table
        ORDER BY ordinal_position
    """)
    with engine.connect() as conn:
        result = conn.execute(sql, {"schema": schema, "table": table})
        return [row[0] for row in result]


def apply_configured_transforms(chunk: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Apply only the source-format patches declared in this step's YAML."""
    date_format = cfg.get("transforms", {}).get("date_format")
    if not date_format:
        return chunk

    column = date_format["column"]
    chunk[column] = pd.to_datetime(
        chunk[column],
        format=date_format["input_format"],
        errors="raise",
    ).dt.strftime(date_format["output_format"])
    return chunk


def upload_file(cfg: dict, engine: any, s3_client: any, bucket: str, schema: str) -> bool:
    file_name = cfg["file_name"]
    table = cfg["table"]
    columns = cfg["columns"]
    rename = cfg.get("rename", {})
    batch_size = cfg.get("batch_size", 5000)

    # Lấy Presigned URL từ S3 để pandas có thể đọc trực tiếp
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": file_name},
        ExpiresIn=3600
    )

    db_cols = get_table_columns(engine, schema, table)
    if not db_cols:
        print(f"[ERROR] Table {schema}.{table} does not exist in DB!")
        return False

    print(f"\n[INFO] {file_name}  →  {schema}.{table}")

    try:
        with engine.begin() as conn:
            conn.execute(
                text(f"TRUNCATE TABLE {schema}.{table} RESTART IDENTITY CASCADE")
            )
        print(f"[OK] Truncated {schema}.{table}")
        
        start = time.time()
        total = 0

        for chunk in pd.read_csv(
            url,
            dtype=str,
            sep=",",
            usecols=columns,
            encoding="utf-8",
            chunksize=batch_size,
            on_bad_lines="skip",
        ):
            chunk.columns = chunk.columns.str.strip()

            available = [c for c in columns if c in chunk.columns]
            chunk = chunk[available]
            chunk = apply_configured_transforms(chunk, cfg)
            chunk = chunk.rename(columns=rename)

            valid_cols = [c for c in chunk.columns if c in db_cols]
            chunk = chunk[valid_cols]
            chunk.dropna(how="all", inplace=True)

            chunk.to_sql(
                name=table,
                con=engine,
                schema=schema,
                if_exists="append",
                index=False,
                method="multi",
            )

            total += len(chunk)
            print(f"   ↑ {total:,} rows...", end="\r")

        elapsed = time.time() - start
        print(f"\n[DONE] {total:,} rows inserted in {elapsed:.1f}s")
        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to process {file_name}: {e}")
        return False


def load_object_storage_to_staging(
    *,
    engine: any,
    s3_client: any,
    bucket: str,
    config: dict,
) -> None:
    """Load all configured objects into raw staging tables."""
    schema = config["database"]["schema"]
    files = config.get("files", [])

    print("=" * 55)
    print("   OBJECT STORAGE → SUPABASE STAGING")
    print("=" * 55)

    ok = fail = 0
    for cfg in files:
        if upload_file(cfg, engine, s3_client, bucket, schema):
            ok += 1
        else:
            fail += 1

    print("=" * 55)
    print(f"Completed: {ok} success  |  {fail} failed")

    if fail:
        raise RuntimeError(f"{fail} staging file(s) failed to load")
