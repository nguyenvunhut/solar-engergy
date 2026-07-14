"""Run the complete local V2 ML preprocessing pipeline.

This script does not connect to Supabase/cloud. It only reads/writes local files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from v2_01_quality_preprocessing import QualityConfig, run_quality_preprocessing
from v2_02_feature_engineering import FeatureConfig, run_feature_engineering
from v2_03_split_train_val_test import SplitConfig, run_temporal_split
from v2_04_audit_preprocessing_outputs import AuditConfig, run_audit
from v2_05_feature_selection_audit import (
    FeatureSelectionAuditConfig,
    run_feature_selection_audit,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full local V2 ML preprocessing pipeline.")
    parser.add_argument(
        "--skip-feature-selection-audit",
        action="store_true",
        help="Skip correlation/missingness feature-selection audit.",
    )
    parser.add_argument(
        "--feature-audit-sample-rows",
        type=int,
        default=300_000,
        help="Number of rows sampled for feature-selection audit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("[1/5] Quality preprocessing")
    run_quality_preprocessing(QualityConfig())

    print("\n[2/5] Feature engineering")
    run_feature_engineering(FeatureConfig())

    print("\n[3/5] Temporal train/val/test split")
    run_temporal_split(SplitConfig())

    print("\n[4/5] Preprocessing audit report")
    run_audit(AuditConfig())

    if args.skip_feature_selection_audit:
        print("\n[5/5] Feature-selection audit skipped")
    else:
        print("\n[5/5] Feature-selection audit")
        run_feature_selection_audit(
            FeatureSelectionAuditConfig(sample_rows=args.feature_audit_sample_rows)
        )

    print("\n[DONE] Local V2 ML preprocessing pipeline completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
