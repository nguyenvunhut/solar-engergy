#!/usr/bin/env python3
"""So MA TRAN TRAIN cua pipeline voi ma tran train do CHINH NOTEBOOK 06 sinh ra.

    python srcs/05_machine_learning/pipeline/checks/so_sanh_ma_tran_train.py
    python srcs/05_machine_learning/pipeline/checks/so_sanh_ma_tran_train.py --loss mae --horizon 4

CHI DOC - khong ghi bat ky file ket qua nao.

VI SAO PHEP THU NAY LA PHEP THU QUYET DINH:
  Ca notebook lan pipeline gio deu train bang CPU + deterministic = true, tuc la
  LightGBM DAM BAO cung dau vao thi cung dau ra. Vay nen:

      ma tran train giong nhau  +  sieu tham so giong nhau  =>  model giong nhau

  Nghia la chi can so ma tran train va bo tham so la du ket luan, KHONG can train lai
  roi so model.pkl. Va neu ma tran lech thi loi nam o code chuan bi du lieu - phep thu
  nay chi thang ra cot nao lech, lech bao nhieu dong.

CACH LAM: chay THANG cac o code cua notebook (khong chep lai, khong dien giai lai) den
het o dung X_dev/y_dev/w_dev, roi so voi ket qua cua stages/s08a_prepare.py.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

THU_MUC_PIPELINE = Path(__file__).resolve().parents[1]
REPO = THU_MUC_PIPELINE.parents[2]
if str(THU_MUC_PIPELINE) not in sys.path:
    sys.path.insert(0, str(THU_MUC_PIPELINE))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from core.config import load_config  # noqa: E402
from core.context import Ctx  # noqa: E402
from core.paths import Paths  # noqa: E402

NB_DIR = REPO / "notebooks" / "forcasting_v3_energy"
NB_THEO_LOSS = {"mae": "06_1_train_mae.ipynb",
                "huber": "06_2_train_huber.ipynb",
                "mse": "06_3_train_mse.ipynb"}
# O code cuoi cung can chay: o dung X_dev/y_dev/w_dev cho h1. Cac o sau do la Optuna
# va train - khong can, va rat cham.
O_CUOI_H1 = 15


def chay_notebook_den_ma_tran(ten_nb: str, horizon: int) -> dict:
    """Chay cac o code cua notebook trong mot khong gian ten rieng, tra ve bien cua no."""
    nb = json.loads((NB_DIR / ten_nb).read_text(encoding="utf-8"))
    o_code = [(i, "".join(c["source"])) for i, c in enumerate(nb["cells"])
              if c["cell_type"] == "code"]

    ns: dict = {"__name__": "__notebook__", "display": lambda *a, **k: None}
    cwd = os.getcwd()
    os.chdir(NB_DIR)  # notebook dung duong dan tuong doi '../../data/...'
    try:
        for i, src in o_code:
            if i > O_CUOI_H1:
                break
            exec(compile(src, f"<{ten_nb} cell {i}>", "exec"), ns)  # noqa: S102
        if horizon != 1:
            # o 45 dung lai ma tran cho h4 (gan lai HORIZON_STEPS roi lap lai o 15)
            for i, src in o_code:
                if i in (43, 44, 45):
                    exec(compile(src, f"<{ten_nb} cell {i}>", "exec"), ns)  # noqa: S102
    finally:
        os.chdir(cwd)
    return ns


def _so_khung(a: pd.DataFrame, b: pd.DataFrame, ten: str) -> bool:
    """So 2 khung: so dong, thu tu cot, kieu du lieu, roi tung o."""
    if list(a.columns) != list(b.columns):
        chi_a = [c for c in a.columns if c not in b.columns]
        chi_b = [c for c in b.columns if c not in a.columns]
        print(f"  {ten}: LECH DANH SACH COT - notebook {len(a.columns)} vs "
              f"pipeline {len(b.columns)}")
        if chi_a:
            print(f"      chi notebook co : {chi_a[:8]}")
        if chi_b:
            print(f"      chi pipeline co : {chi_b[:8]}")
        if sorted(a.columns) == sorted(b.columns):
            print("      (cung tap cot nhung KHAC THU TU - van tinh la lech)")
        return False
    if len(a) != len(b):
        print(f"  {ten}: LECH SO DONG - notebook {len(a):,} vs pipeline {len(b):,}")
        return False

    lech = []
    for c in a.columns:
        x, y = a[c].to_numpy(), b[c].to_numpy()
        if x.dtype != y.dtype:
            lech.append((c, f"kieu {x.dtype} vs {y.dtype}"))
            continue
        khac = ~((x == y) | (pd.isna(x) & pd.isna(y)))
        if khac.any():
            lech.append((c, f"{int(khac.sum()):,} o khac, lech lon nhat "
                            f"{np.nanmax(np.abs(x[khac] - y[khac])):.3e}"))
    if lech:
        print(f"  {ten}: LECH {len(lech)}/{len(a.columns)} cot")
        for c, mo_ta in lech[:10]:
            print(f"      {c}: {mo_ta}")
        return False
    print(f"  {ten}: KHOP TUNG BIT ({len(a):,} dong x {len(a.columns)} cot)")
    return True


def _so_chuoi(a: pd.Series, b: pd.Series, ten: str) -> bool:
    if len(a) != len(b):
        print(f"  {ten}: LECH SO DONG - notebook {len(a):,} vs pipeline {len(b):,}")
        return False
    x, y = a.to_numpy(), b.to_numpy()
    if x.dtype != y.dtype:
        print(f"  {ten}: LECH KIEU - {x.dtype} vs {y.dtype}")
        return False
    khac = ~((x == y) | (pd.isna(x) & pd.isna(y)))
    if khac.any():
        print(f"  {ten}: LECH {int(khac.sum()):,}/{len(x):,} gia tri, lon nhat "
              f"{np.nanmax(np.abs(x[khac] - y[khac])):.3e}")
        return False
    print(f"  {ten}: KHOP TUNG BIT ({len(a):,} gia tri)")
    return True


def so_sanh(loss_name: str, horizon: int) -> int:
    from stages import s08a_prepare

    print("=" * 78)
    print(f"SO MA TRAN TRAIN: notebook {NB_THEO_LOSS[loss_name]} vs pipeline s08a "
          f"({loss_name} h{horizon})")
    print("=" * 78)

    print("\n[1/3] Chay cac o code cua notebook...")
    ns = chay_notebook_den_ma_tran(NB_THEO_LOSS[loss_name], horizon)
    for ten in ("X_dev", "y_dev", "w_dev"):
        if ten not in ns:
            raise SystemExit(f"Notebook khong tao ra bien '{ten}' - kiem lai O_CUOI_H1.")

    print("\n[2/3] Chay stages/s08a_prepare.chuan_bi()...")
    cfg = load_config()
    ctx = Ctx(cfg=cfg, paths=Paths(cfg), loss_name=loss_name, horizon_steps=horizon)
    s08a_prepare.chuan_bi(ctx)

    print("\n[3/3] Doi chieu:")
    dat = True
    if list(ns["FEATURES"]) != list(ctx.features):
        print(f"  FEATURES: LECH - notebook {len(ns['FEATURES'])} vs pipeline "
              f"{len(ctx.features)} dac trung")
        chi_nb = [c for c in ns["FEATURES"] if c not in ctx.features]
        chi_pl = [c for c in ctx.features if c not in ns["FEATURES"]]
        print(f"      chi notebook co: {chi_nb[:8]}\n      chi pipeline co: {chi_pl[:8]}")
        dat = False
    else:
        print(f"  FEATURES: KHOP ke ca THU TU ({len(ctx.features)} dac trung)")

    dat &= _so_khung(ns["X_dev"], ctx.X_dev, "X_dev ")
    dat &= _so_chuoi(ns["y_dev"], ctx.y_dev, "y_dev ")
    dat &= _so_chuoi(ns["w_dev"], ctx.w_dev, "w_dev ")

    print()
    print("=" * 78)
    if dat:
        print("KET LUAN: DAT - ma tran train giong het notebook.")
        print("Ca hai deu train bang CPU + deterministic nen cung ma tran + cung tham so")
        print("=> cung model. Khong can train lai de kiem.")
    else:
        print("KET LUAN: CHUA DAT - co cho lech o tren. Day LA loi code, phai sua.")
    print("=" * 78)
    return 0 if dat else 1


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--loss", default="huber", choices=sorted(NB_THEO_LOSS))
    p.add_argument("--horizon", type=int, default=1)
    a = p.parse_args()
    return so_sanh(a.loss, a.horizon)


if __name__ == "__main__":
    sys.exit(main())
