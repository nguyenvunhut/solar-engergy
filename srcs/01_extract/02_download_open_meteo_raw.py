#!/usr/bin/env python3
"""Step 02: download historical hourly weather data from Open-Meteo."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
import time
from typing import Any

import pandas as pd
import requests
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = (
    PROJECT_ROOT
    / "config"
    / "01_extract"
    / "02_download_open_meteo_raw.yaml"
)


class ExtractError(RuntimeError):
    """Raised when weather extraction cannot complete safely."""


@dataclass(frozen=True)
class SiteColumns:
    site_id: str
    latitude: str
    longitude: str


@dataclass(frozen=True)
class RequestConfig:
    timeout_seconds: int
    delay_between_sites_seconds: float
    max_attempts: int
    retry_delay_seconds: float
    rate_limit_delay_seconds: float


@dataclass(frozen=True)
class ExpectedOutput:
    site_count: int
    rows_per_site: int
    total_rows: int


@dataclass(frozen=True)
class OpenMeteoConfig:
    endpoint: str
    input_file: Path
    output_file: Path
    overwrite: bool
    start_date: str
    end_date: str
    timezone: str
    source_timezone: str
    target_timezone: str
    site_columns: SiteColumns
    hourly_columns: tuple[str, ...]
    request: RequestConfig
    expected: ExpectedOutput


def project_path(path: str) -> Path:
    configured_path = Path(path)
    if configured_path.is_absolute():
        return configured_path
    return PROJECT_ROOT / configured_path


def read_config(config_path: Path) -> OpenMeteoConfig:
    """Read the complete step configuration from YAML."""
    if not config_path.is_file():
        raise ExtractError(f"Config file not found: {config_path}")

    content = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    try:
        config = content["open_meteo"]
        site_columns = config["site_columns"]
        timestamp_transform = config["timestamp_transform"]
        request = config["request"]
        expected = config["expected"]

        result = OpenMeteoConfig(
            endpoint=str(config["endpoint"]),
            input_file=project_path(str(config["input_file"])),
            output_file=project_path(str(config["output_file"])),
            overwrite=bool(config["overwrite"]),
            start_date=str(config["start_date"]),
            end_date=str(config["end_date"]),
            timezone=str(config["timezone"]),
            source_timezone=str(timestamp_transform["source_timezone"]),
            target_timezone=str(timestamp_transform["target_timezone"]),
            site_columns=SiteColumns(
                site_id=str(site_columns["id"]),
                latitude=str(site_columns["latitude"]),
                longitude=str(site_columns["longitude"]),
            ),
            hourly_columns=tuple(config["hourly_columns"]),
            request=RequestConfig(
                timeout_seconds=int(request["timeout_seconds"]),
                delay_between_sites_seconds=float(
                    request["delay_between_sites_seconds"]
                ),
                max_attempts=int(request["max_attempts"]),
                retry_delay_seconds=float(request["retry_delay_seconds"]),
                rate_limit_delay_seconds=float(
                    request["rate_limit_delay_seconds"]
                ),
            ),
            expected=ExpectedOutput(
                site_count=int(expected["site_count"]),
                rows_per_site=int(expected["rows_per_site"]),
                total_rows=int(expected["total_rows"]),
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ExtractError(
            "Invalid Open-Meteo configuration YAML"
        ) from exc

    if not result.hourly_columns:
        raise ExtractError("open_meteo.hourly_columns cannot be empty")
    if result.request.max_attempts < 1:
        raise ExtractError("request.max_attempts must be at least 1")

    return result


def read_sites(config: OpenMeteoConfig) -> pd.DataFrame:
    """Read and validate the site coordinates produced by extract step 01."""
    if not config.input_file.is_file():
        raise ExtractError(
            f"Input file not found: {config.input_file}. Run step 01 first."
        )

    sites = pd.read_csv(config.input_file)
    required_columns = {
        config.site_columns.site_id,
        config.site_columns.latitude,
        config.site_columns.longitude,
    }
    missing_columns = required_columns.difference(sites.columns)
    if missing_columns:
        raise ExtractError(
            f"Input file is missing columns: {sorted(missing_columns)}"
        )

    if sites[list(required_columns)].isnull().any().any():
        raise ExtractError("Site ID, latitude, or longitude contains null values")
    if sites[config.site_columns.site_id].duplicated().any():
        raise ExtractError("SiteKey values must be unique")
    if len(sites) != config.expected.site_count:
        raise ExtractError(
            f"Expected {config.expected.site_count} sites, found {len(sites)}"
        )

    return sites


def request_site_weather(
    *,
    session: requests.Session,
    config: OpenMeteoConfig,
    site_id: Any,
    latitude: float,
    longitude: float,
) -> pd.DataFrame:
    """Download and validate one site's hourly weather records."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": config.start_date,
        "end_date": config.end_date,
        "hourly": ",".join(config.hourly_columns),
        "timezone": config.timezone,
    }

    last_error = "unknown error"

    for attempt in range(1, config.request.max_attempts + 1):
        try:
            response = session.get(
                config.endpoint,
                params=params,
                timeout=config.request.timeout_seconds,
            )

            if response.status_code == 429:
                last_error = "Open-Meteo rate limit reached"
                if attempt < config.request.max_attempts:
                    time.sleep(config.request.rate_limit_delay_seconds)
                    continue

            response.raise_for_status()
            payload = response.json()
            hourly = payload.get("hourly")
            if not isinstance(hourly, dict) or "time" not in hourly:
                reason = payload.get("reason", "hourly data is missing")
                raise ExtractError(
                    f"SiteKey={site_id}: invalid API response: {reason}"
                )

            missing_columns = [
                column
                for column in config.hourly_columns
                if column not in hourly
            ]
            if missing_columns:
                raise ExtractError(
                    f"SiteKey={site_id}: API response is missing "
                    f"{missing_columns}"
                )

            site_data = pd.DataFrame(
                {
                    "timestamp": pd.to_datetime(hourly["time"]),
                    **{
                        column: hourly[column]
                        for column in config.hourly_columns
                    },
                }
            )
            
            # Gắn múi giờ UTC+7 (VN) và chuyển sang giờ Úc, sau đó cắt bỏ chuỗi múi giờ
            site_data["timestamp"] = site_data["timestamp"].dt.tz_localize(
                config.source_timezone
            )
            site_data["timestamp"] = site_data["timestamp"].dt.tz_convert(
                config.target_timezone
            )
            site_data["timestamp"] = site_data["timestamp"].dt.tz_localize(None).dt.strftime('%Y-%m-%d %H:%M:%S')

            site_data["SiteKey"] = site_id
            site_data["latitude"] = latitude
            site_data["longitude"] = longitude

            if len(site_data) != config.expected.rows_per_site:
                raise ExtractError(
                    f"SiteKey={site_id}: expected "
                    f"{config.expected.rows_per_site} rows, "
                    f"received {len(site_data)}"
                )

            return site_data

        except ExtractError:
            raise
        except (requests.RequestException, ValueError) as exc:
            last_error = str(exc)
            if attempt < config.request.max_attempts:
                time.sleep(config.request.retry_delay_seconds)

    raise ExtractError(
        f"SiteKey={site_id}: failed after "
        f"{config.request.max_attempts} attempts: {last_error}"
    )


def validate_final_output(
    weather: pd.DataFrame,
    config: OpenMeteoConfig,
) -> None:
    """Verify the crawl matches the known raw-data contract."""
    if len(weather) != config.expected.total_rows:
        raise ExtractError(
            f"Expected {config.expected.total_rows} rows, "
            f"collected {len(weather)}"
        )

    site_count = weather["SiteKey"].nunique()
    if site_count != config.expected.site_count:
        raise ExtractError(
            f"Expected {config.expected.site_count} sites, found {site_count}"
        )

    rows_per_site = weather.groupby("SiteKey").size()
    invalid_sites = rows_per_site[
        rows_per_site != config.expected.rows_per_site
    ]
    if not invalid_sites.empty:
        raise ExtractError(
            f"Unexpected rows per site: {invalid_sites.to_dict()}"
        )


def run_extract(config_path: Path, force: bool) -> None:
    """Execute Open-Meteo extraction and write one complete raw CSV."""
    config = read_config(config_path)

    if config.output_file.exists() and not (force or config.overwrite):
        print(f"[SKIP] Output already exists: {config.output_file}")
        return

    sites = read_sites(config)
    all_sites: list[pd.DataFrame] = []

    with requests.Session() as session:
        for position, row in sites.iterrows():
            site_id = row[config.site_columns.site_id]
            latitude = float(row[config.site_columns.latitude])
            longitude = float(row[config.site_columns.longitude])

            print(
                f"[{position + 1}/{len(sites)}] "
                f"SiteKey={site_id}",
                flush=True,
            )
            all_sites.append(
                request_site_weather(
                    session=session,
                    config=config,
                    site_id=site_id,
                    latitude=latitude,
                    longitude=longitude,
                )
            )
            time.sleep(config.request.delay_between_sites_seconds)

    weather = pd.concat(all_sites, ignore_index=True)
    validate_final_output(weather, config)

    config.output_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = config.output_file.with_suffix(".csv.tmp")
    weather.to_csv(
        temporary_output,
        index=False,
        encoding="utf-8-sig",
    )
    temporary_output.replace(config.output_file)

    print(
        f"[DONE] Step 02 completed: {config.output_file} "
        f"({len(weather)} rows)"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step 02: download Open-Meteo historical raw data."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace the existing output file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run_extract(
            config_path=args.config.expanduser().resolve(),
            force=args.force,
        )
    except ExtractError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[CANCELLED] Extract interrupted.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
