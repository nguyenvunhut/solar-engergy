#!/usr/bin/env python3
"""Load step 01: upload raw files to Supabase object storage."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from dotenv import load_dotenv
import yaml

import importlib.util


def load_module(filename: str, module_name: str, folder: str = ""):
    if folder:
        module_path = PROJECT_ROOT / "srcs" / folder / filename
    else:
        module_path = Path(__file__).resolve().parent / filename
    
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

PROJECT_ROOT = Path(__file__).resolve().parents[3]

storage_connection = load_module(
    "02_storage.py",
    "storage_connection",
    folder="00_utils"
)
upload_files = load_module(
    "02_upload_files.py",
    "upload_files",
)
DEFAULT_CONFIG_PATH = (
    PROJECT_ROOT
    / "config"
    / "03_load"
    / "01_upload_raw_to_object_storage.yaml"
)
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


def read_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def run_load(config_path: Path = DEFAULT_CONFIG_PATH) -> None:
    load_dotenv(DEFAULT_ENV_PATH, override=True)
    config = read_config(config_path)

    source_config = config["source"]
    storage_config = config["object_storage"]

    data_dir = Path(source_config["directory"])
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir

    s3 = storage_connection.create_storage_client(storage_config)
    bucket = storage_connection.read_bucket_name(storage_config)

    upload_files.upload_raw_files(
        s3=s3,
        bucket=bucket,
        data_dir=data_dir,
        extension=source_config["extension"],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load step 01: upload raw files to object storage."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run_load(args.config.expanduser().resolve())
    except KeyboardInterrupt:
        print("\n[CANCELLED] Upload interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
