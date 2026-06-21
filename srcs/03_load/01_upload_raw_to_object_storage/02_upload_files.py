"""Upload raw CSV files using the original upload behavior."""

from __future__ import annotations

import os
from pathlib import Path


def upload_raw_files(
    *,
    s3,
    bucket: str,
    data_dir: Path,
    extension: str,
) -> None:
    existing = [item["Name"] for item in s3.list_buckets()["Buckets"]]
    if bucket not in existing:
        s3.create_bucket(Bucket=bucket)
        print(f"[OK] Created bucket: {bucket}")
    else:
        print(f"[OK] Bucket already exists: {bucket}")

    existing_files = {
        item["Key"]
        for item in s3.list_objects_v2(Bucket=bucket).get("Contents", [])
    }

    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith(extension):
            continue

        path = data_dir / filename
        size = os.path.getsize(path) / (1024 * 1024)

        if filename in existing_files:
            s3.delete_object(Bucket=bucket, Key=filename)
            print(f"  Deleted existing: {filename}")

        print(
            f"  Uploading {filename} ({size:.1f} MB)...",
            end=" ",
            flush=True,
        )
        s3.upload_file(str(path), bucket, filename)
        print("done")

    print("\n[DONE] All files uploaded to object storage")
