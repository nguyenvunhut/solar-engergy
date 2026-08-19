#!/usr/bin/env python3
"""Run only the hybrid imputation step.

Examples:
    python srcs/02_transform/run_hybrid_imputation.py
    python srcs/02_transform/run_hybrid_imputation.py --dry-run

The database wrapper is reused from ``srcs/06_run_pipeline/main.py`` so the
standalone command has the same commit, rollback, and connection lifecycle as
the main pipeline.
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
log = logging.getLogger("hybrid_imputation_runner")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate imputation without committing database changes.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(pipeline_main.ENV_FILE, override=True)
    started = time.perf_counter()
    mode = "DRY-RUN" if args.dry_run else "EXECUTE"
    log.info("START | Hybrid Imputation | mode=%s", mode)

    try:
        pipeline_main.run_imputation(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n[CANCELLED] Hybrid imputation interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        log.exception("FAILED | Hybrid Imputation")
        print(f"\n[ERROR] Hybrid imputation failed: {exc}", file=sys.stderr)
        return 1

    log.info("SUCCESS | Hybrid Imputation | %.2fs", time.perf_counter() - started)
    print("\n[DONE] Hybrid imputation completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())