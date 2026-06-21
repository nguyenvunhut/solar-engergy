#!/usr/bin/env python3
"""Step 01: download raw files using the matching YAML configuration."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = (
    PROJECT_ROOT
    / "config"
    / "01_extract"
    / "01_download_kaggle_raw.yaml"
)


class ExtractError(RuntimeError):
    """Raised when the extract step cannot complete."""


@dataclass(frozen=True)
class RawFile:
    name: str
    remote_path: str


@dataclass(frozen=True)
class KaggleConfig:
    dataset: str
    output_dir: Path
    files: tuple[RawFile, ...]
    overwrite: bool


def read_config(config_path: Path) -> KaggleConfig:
    """Read the Kaggle extract configuration from YAML."""
    if not config_path.is_file():
        raise ExtractError(f"Config file not found: {config_path}")

    content = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    try:
        source = content["kaggle"]
        dataset = source["dataset"]
        output_dir = source["output_dir"]
        files = source["files"]
        overwrite = source["overwrite"]
    except (KeyError, TypeError) as exc:
        raise ExtractError("Invalid Kaggle extract YAML configuration") from exc

    if not isinstance(files, list) or not files:
        raise ExtractError(
            "kaggle.files must be a non-empty list"
        )

    raw_files: list[RawFile] = []
    for file_config in files:
        try:
            raw_files.append(
                RawFile(
                    name=file_config["name"],
                    remote_path=file_config["remote_path"],
                )
            )
        except (KeyError, TypeError) as exc:
            raise ExtractError(
                "Each Kaggle file requires name and remote_path"
            ) from exc

    return KaggleConfig(
        dataset=dataset,
        output_dir=Path(output_dir),
        files=tuple(raw_files),
        overwrite=overwrite,
    )


def download_raw_file(
    *,
    kaggle_command: str,
    dataset: str,
    remote_path: str,
    download_dir: Path,
    overwrite: bool,
) -> None:
    """Download one exact file path from Kaggle."""
    command = [
        kaggle_command,
        "datasets",
        "download",
        dataset,
        "--file",
        remote_path,
        "--path",
        str(download_dir),
        "--quiet",
    ]
    if overwrite:
        command.append("--force")

    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ExtractError(f"Cannot download {remote_path}: {detail}")


def find_downloaded_file(
    download_dir: Path,
    filename: str,
    remote_path: str,
) -> Path:
    """Find a direct CSV or extract it from the archive returned by Kaggle."""
    matches = [
        path
        for path in download_dir.rglob(filename)
        if path.is_file()
    ]
    if matches:
        return matches[0]

    for archive_path in download_dir.rglob("*.zip"):
        with zipfile.ZipFile(archive_path) as archive:
            members = archive.namelist()

            if remote_path in members:
                member = remote_path
            else:
                matching_members = [
                    item
                    for item in members
                    if Path(item).name == filename
                ]
                if not matching_members:
                    continue
                member = matching_members[0]

            extracted_path = Path(
                archive.extract(member, path=download_dir)
            )
            if extracted_path.is_file():
                return extracted_path

    downloaded_items = sorted(
        str(path.relative_to(download_dir))
        for path in download_dir.rglob("*")
        if path.is_file()
    )
    raise ExtractError(
        f"Downloaded file not found: {filename}. "
        f"Kaggle returned: {downloaded_items or ['no files']}"
    )


def run_extract(config_path: Path, force: bool) -> None:
    """Execute Kaggle raw extraction in configured order."""
    config = read_config(config_path)
    kaggle_command = shutil.which("kaggle")
    if not kaggle_command:
        raise ExtractError(
            "Kaggle CLI not found. Activate .venv and install requirements.txt"
        )

    output_dir = config.output_dir
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    overwrite = force or config.overwrite

    with tempfile.TemporaryDirectory(prefix="kaggle-raw-") as temporary:
        download_dir = Path(temporary)

        for raw_file in config.files:
            destination = output_dir / raw_file.name
            if destination.exists() and not overwrite:
                print(f"[SKIP] {raw_file.name}")
                continue

            print(f"[GET]  {raw_file.remote_path}")
            download_raw_file(
                kaggle_command=kaggle_command,
                dataset=config.dataset,
                remote_path=raw_file.remote_path,
                download_dir=download_dir,
                overwrite=overwrite,
            )

            source = find_downloaded_file(
                download_dir,
                raw_file.name,
                raw_file.remote_path,
            )
            shutil.copy2(source, destination)
            print(f"[OK]   {destination}")

    print(f"[DONE] Step 01 completed: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step 01: download Kaggle raw files."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing raw files.",
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
