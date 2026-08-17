#!/usr/bin/env python3
"""Diem chay duy nhat cua pipeline ML.

    python srcs/05_machine_learning/pipeline/run.py --stage s08                      # ca 3 loss x 2 horizon
    python srcs/05_machine_learning/pipeline/run.py --stage s08 --loss huber --horizon 1
    python srcs/05_machine_learning/pipeline/run.py --stage all
    python srcs/05_machine_learning/pipeline/run.py --list                           # xem cac stage

KHAC BAN CU (srcs/05_machine_learning/forcasting_ml/run_pipeline.py):
  - Khong dung importlib.spec_from_file_location nua: ten file da hop le
    (s08_train.py thay vi 04_2_train_huber.py) nen import binh thuong.
  - Khong gan builtins.display = print nua: code moi khong goi display() cua Jupyter.
  - Optuna KHONG nam trong bat ky stage nao. Muon tune thi chay rieng:
        python srcs/05_machine_learning/pipeline/actions/tune_optuna.py
    Pipeline chuan doc sieu tham so tu best_params.json (hoac default_params).
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

THU_MUC = Path(__file__).resolve().parent
if str(THU_MUC) not in sys.path:
    sys.path.insert(0, str(THU_MUC))


def _dat_thread_som() -> int:
    """Dat so thread cua BLAS/OpenMP TRUOC KHI numpy duoc import lan dau.

    BAT BUOC phai lam o day, khong duoc de trong core.lgbm: cac bien OMP_NUM_THREADS /
    OPENBLAS_NUM_THREADS chi co tac dung neu duoc dat TRUOC khi thu vien so hoc nap.
    Neu import core.* truoc roi moi dat thi numpy da nap xong -> viec dat thanh vo hieu.

    HAU QUA THUC TE cua bug nay (da gap 2026-08-07): so thread khac nhau lam LAPACK cong
    theo thu tu khac nhau. Voi ma tran gan suy bien (VIF toi 4.524, tuc R2 ~ 0,99978) thi
    sai so do bi khuech dai, VIF lech toi 42 don vi so voi ban goc. Doc yaml bang thu vien
    yaml thuan (khong keo theo numpy) nen an toan.
    """
    import yaml

    duong = (THU_MUC.parents[2] / "config" / "05_machine_learning" / "pipeline"
             / "runtime.yaml")
    with open(duong, encoding="utf-8") as f:
        rt = yaml.safe_load(f)["threads"]
    n = str(rt["n_jobs"])
    for bien in rt["env_vars"]:
        os.environ[bien] = n
    return int(n)


N_JOBS = _dat_thread_som()

from core.config import load_config  # noqa: E402
from core.lgbm import dat_env_opencl  # noqa: E402

# Ten stage -> (module, ham). Them stage moi thi khai o day va tao file trong stages/.
STAGE = {
    # s00 dien khuyet: doc paths.mlmart_raw -> ghi paths.mlmart_base. Cac stage sau
    # chi doc mlmart_base nen chay s00 mot lan la du, khong can chay lai moi lan.
    "s00": ("stages.s00_fill_null", "run_s00"),
    "s01": ("stages.s01_reindex", "run_s01"),
    "s02": ("stages.s02_split", "run_s02"),
    "s03": ("stages.s03_features_time", "run_s03"),
    "s04": ("stages.s04_features_spatial", "run_s04"),
    "s05": ("stages.s05_features_aggregate", "run_s05"),
    "s06": ("stages.s06_vif_diagnostics", "run_s06"),
    "s07": ("stages.s07_select_features", "run_s07"),
    "s08": ("stages.s08_train", "run_s08"),
    "s09": ("stages.s09_final_test", "run_s09"),
    "s10": ("stages.s10_explain_shap", "run_s10"),
    "s11": ("stages.s11_phase_lag", "run_s11"),
}
THU_TU = list(STAGE)


def _nap(ten_stage: str):
    ten_module, ten_ham = STAGE[ten_stage]
    try:
        module = __import__(ten_module, fromlist=[ten_ham])
    except ModuleNotFoundError as loi:
        raise SystemExit(
            f"Stage '{ten_stage}' chua duoc viet ({ten_module}.py). "
            f"Xem tien do trong docs/2026_08_07_Ke_Hoach_Refactor_Srcs_Pipeline.md"
        ) from loi
    return getattr(module, ten_ham)


def chay_stage(ten_stage: str, **kwargs) -> None:
    ham = _nap(ten_stage)
    print("=" * 78)
    print(f"STAGE {ten_stage}")
    print("=" * 78)
    t0 = time.time()
    ham(**kwargs)
    print(f"[{ten_stage}] xong sau {(time.time() - t0) / 60:.1f} phut\n")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--stage",
        default="all",
        choices=["all", *THU_TU],
        help="Chay 1 stage, hoac 'all' de chay tuan tu tu s01 den s11.",
    )
    p.add_argument(
        "--loss",
        nargs="*",
        default=None,
        help="Chi dinh loss cho s08 (mac dinh: ca 3 loss trong train.yaml).",
    )
    p.add_argument(
        "--horizon",
        nargs="*",
        type=int,
        default=None,
        help="Chi dinh horizon cho s08 (mac dinh: ca 1 va 4).",
    )
    p.add_argument("--list", action="store_true", help="Liet ke stage roi thoat.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.list:
        for ten in THU_TU:
            module, _ = STAGE[ten]
            co = (THU_MUC / f"{module.replace('.', '/')}.py").exists()
            print(f"  {ten}  {module:34s} {'da co' if co else 'CHUA VIET'}")
        return 0

    cfg = load_config()
    # So thread da duoc dat o _dat_thread_som() TRUOC moi import - xem docstring ham do
    icd = dat_env_opencl(cfg)
    print(
        f"n_jobs = {cfg.runtime['threads']['n_jobs']}"
        + (f" | OpenCL ICD = {icd}" if icd else " | khong tim thay OpenCL ICD")
    )

    suffix = cfg.paths.get("output_suffix", "")
    if suffix:
        print(
            f"output_suffix = '{suffix}' -> ghi ra thu muc RIENG, "
            f"khong dung toi ket qua goc."
        )
    else:
        print(
            "[CANH BAO] output_suffix rong -> se GHI DE len ket qua goc cua notebook!"
        )
    print()

    cac_stage = THU_TU if args.stage == "all" else [args.stage]
    for ten in cac_stage:
        kwargs = {}
        if ten == "s08":
            kwargs = {"losses": args.loss, "horizons": args.horizon}
        chay_stage(ten, **kwargs)

    print("Hoan tat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
