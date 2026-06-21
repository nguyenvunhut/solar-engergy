"""Create the S3-compatible client used by the legacy upload flow."""

from __future__ import annotations

import os

import boto3
from botocore.client import Config


def create_storage_client(storage_config: dict):
    endpoint = os.getenv(storage_config["endpoint_env"])
    access_key = os.getenv(storage_config["access_key_env"])
    secret_key = os.getenv(storage_config["secret_key_env"])

    kwargs = {
        "service_name": "s3",
        "endpoint_url": endpoint,
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "config": Config(signature_version="s3v4"),
    }
    if storage_config.get("region") and storage_config["region"] != "local":
        kwargs["region_name"] = storage_config["region"]

    return boto3.client(**kwargs)


def read_bucket_name(storage_config: dict) -> str:
    return os.getenv(storage_config["bucket_env"], "raw-data")
