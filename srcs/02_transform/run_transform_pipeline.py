#!/usr/bin/env python3
"""Run the transform portion of the data pipeline independently.

Examples:
    python srcs/02_transform/run_transform_pipeline.py --step all
    python srcs/02_transform/run_transform_pipeline.py --step buffers --dry-run
    python srcs/02_transform/run_transform_pipeline.py --step imputation
    python srcs/02_transform/run_transform_pipeline.py --step generate_outliers
    python srcs/02_transform/run_transform_pipeline.py --step apply_outlier

The implementation delegates to the same runners used by
``srcs/06_run_pipeline/main.py`` so database and outlier logic stay in one place.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
import time

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER_DIR = PROJECT_ROOT / "srcs" / "06_run_pipeline"
if str(RUNNER_DIR) not in sys.path:
    sys.path.insert(0, str(RUNNER_DIR))

import main as pipeline_main  # noqa: E402


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("transform_pipeline")


STEPS = {
    "buffers": (
        "Raw Staging -> Buffer",
        lambda dry_run: pipeline_main.run_transform(dry_run=dry_run),
    ),
    "imputation": (
        "Hybrid Imputation",
        lambda dry_run: pipeline_main.run_imputation(dry_run=dry_run),
    ),
    "generate_outliers": (
        "Generate Outliers CSV",
        lambda dry_run: pipeline_main.run_generate_outliers(dry_run=dry_run),
    ),
    "apply_outlier": (
        "Apply Outlier Flags",
        lambda dry_run: pipeline_main.run_outlier(dry_run=dry_run),
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--step",
        choices=["all", *STEPS],
        default="all",
        help="Transform step to execute. Default: all.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run supported database steps without committing changes.",
    )
    return parser.parse_args()


def selected_steps(step: str) -> list[str]:
    if step == "all":
        return list(STEPS)
    return [step]


def run(step: str, *, dry_run: bool) -> None:
    names = selected_steps(step)
    for number, name in enumerate(names, start=1):
        title, runner = STEPS[name]
        started = time.perf_counter()
        log.info("[%s/%s] START | %s | mode=%s", number, len(names), title, "DRY-RUN" if dry_run else "EXECUTE")
        try:
            runner(dry_run)
        except Exception:
            log.exception("[%s/%s] FAILED | %s", number, len(names), title)
            raise
        log.info(
            "[%s/%s] SUCCESS | %s | %.2fs",
            number,
            len(names),
            title,
            time.perf_counter() - started,
        )


def main() -> int:
    args = parse_args()
    load_dotenv(pipeline_main.ENV_FILE, override=True)
    try:
        run(args.step, dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n[CANCELLED] Transform pipeline interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"\n[ERROR] Transform pipeline failed: {exc}", file=sys.stderr)
        return 1

    print("\n[DONE] Transform pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())