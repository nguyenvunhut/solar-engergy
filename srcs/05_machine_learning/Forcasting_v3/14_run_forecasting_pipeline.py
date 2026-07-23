"""Stage 14 — CLI runner for the v3_final_cleaned forecasting pipeline.

Input:
    - Forecasting YAML config.
    - Optional ``--stage`` and ``--run-id`` arguments.

Output:
    - Executes one stage or the ordered end-to-end pipeline.

Important:
    - The runner resolves one stable run_id and passes it through every stage.
    - Running stages manually requires the same run_id if a later stage depends
      on artifacts created by an earlier stage.
    - Stage order preserves the forecasting contract: audit → continuous grid
      → split → features → diagnostics/selection → baselines/tuning → final
      train → sealed test evaluation → SHAP/long-term branch.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path
from typing import Callable

from forecasting_common import DEFAULT_CONFIG, load_config


STAGE_FILES: dict[str, tuple[str, str]] = {
    "audit": ("00_audit_v3_final_cleaned.py", "run_audit"),
    "continuous": ("01_build_continuous_grid.py", "run_build_continuous"),
    "split": ("02_split_time_series_data.py", "run_split"),
    "features_time": ("03_feature_engineering_time_series.py", "run_time_features"),
    "features_spatial": ("04_feature_engineering_spatial.py", "run_spatial_features"),
    "features_aggregate": ("05_feature_engineering_aggregate.py", "run_aggregate_features"),
    "diagnostics": ("06_vif_pls_diagnostics.py", "run_diagnostics"),
    "select": ("07_select_features_sklearn.py", "run_select_features"),
    "baselines": ("08_train_baselines.py", "run_baselines"),
    "tune": ("09_tune_lightgbm_expanding_optuna.py", "run_tuning"),
    "train_final": ("10_train_final_train_validation.py", "run_train_final"),
    "evaluate": ("11_evaluate_final_test.py", "run_evaluate"),
    "shap": ("12_explain_shap.py", "run_shap"),
    "prophet": ("13_train_prophet_long_term.py", "run_prophet"),
}

ALL_STAGES = [
    "audit",
    "continuous",
    "split",
    "features_time",
    "features_spatial",
    "features_aggregate",
    "diagnostics",
    "select",
    "baselines",
    "tune",
    "train_final",
    "evaluate",
    "shap",
    "prophet",
]


GPU_STAGES = {"all", "tune", "train_final"}


def _find_nix_opencl_vendor_path() -> str | None:
    if os.name != "posix":
        return None
    candidates = list(Path("/nix/store").glob("*nvidia*/etc/OpenCL/vendors"))
    candidates.extend(
        [
            Path("/run/opengl-driver/etc/OpenCL/vendors"),
            Path("/etc/OpenCL/vendors"),
        ]
    )
    for candidate in candidates:
        try:
            if candidate.exists() and (
                (candidate / "nvidia.icd").exists() or any(candidate.glob("*.icd"))
            ):
                return str(candidate)
        except OSError:
            continue
    return None


def _find_nix_opencl_library_paths() -> list[str]:
    if os.name != "posix":
        return []
    paths: list[Path] = [Path("/run/opengl-driver/lib"), Path("/run/opengl-driver-32/lib")]
    paths.extend(Path("/nix/store").glob("*ocl-icd*/lib"))
    return [str(path) for path in paths if path.exists()]


def _reexec_with_opencl_env_if_needed(config_path: Path, stage: str) -> None:
    if stage not in GPU_STAGES:
        return
    if os.environ.get("OCL_ICD_VENDORS") or os.environ.get("FORECASTING_OPENCL_REEXEC") == "1":
        return
    config = load_config(config_path)
    lgb_cfg = config.raw.get("training", {}).get("lightgbm", {})
    wants_opencl_gpu = str(lgb_cfg.get("device", "")).lower() == "gpu"
    if not wants_opencl_gpu:
        return
    vendor_path = _find_nix_opencl_vendor_path()
    if not vendor_path:
        return
    env = os.environ.copy()
    env["OCL_ICD_VENDORS"] = vendor_path
    lib_paths = _find_nix_opencl_library_paths()
    if lib_paths:
        existing = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = ":".join([*lib_paths, existing] if existing else lib_paths)
        env["NIX_LD_LIBRARY_PATH"] = env["LD_LIBRARY_PATH"]
    env["FORECASTING_OPENCL_REEXEC"] = "1"
    print(f"[INFO] Re-exec with OCL_ICD_VENDORS={vendor_path}", flush=True)
    os.execvpe(sys.executable, [sys.executable, *sys.argv], env)


def load_stage(file_name: str, function_name: str) -> Callable:
    path = Path(__file__).with_name(file_name)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load stage: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return getattr(module, function_name)


def run_pipeline(config_path: str | Path = DEFAULT_CONFIG, *, stage: str = "all", run_id: str | None = None) -> None:
    config = load_config(config_path)
    rid = run_id or config.run_id
    stages = ALL_STAGES if stage == "all" else [stage]
    print(f"Forecasting pipeline start | run_id={rid} | stage={stage}")
    for stage_name in stages:
        file_name, function_name = STAGE_FILES[stage_name]
        print(f"\n[{stage_name}] {file_name}")
        fn = load_stage(file_name, function_name)
        fn(config_path, run_id=rid)
    print(f"\nForecasting pipeline completed | run_id={rid}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v3_final_cleaned forecasting pipeline.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stage", choices=["all", *STAGE_FILES.keys()], default="all")
    parser.add_argument("--run-id", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _reexec_with_opencl_env_if_needed(args.config, args.stage)
    run_pipeline(args.config, stage=args.stage, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
