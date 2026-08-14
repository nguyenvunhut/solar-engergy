#!/usr/bin/env python3
"""WP0 - do xem buoc train (s08) co tai lap duoc tung bit hay khong.

    python srcs/05_machine_learning/pipeline/checks/do_tinh_tai_lap_s08.py
    python srcs/05_machine_learning/pipeline/checks/do_tinh_tai_lap_s08.py --thiet-bi cpu

CHI DOC du lieu, ghi model tam vao thu muc tam roi xoa - khong dung toi artifact nao.

VI SAO PHAI DO TRUOC KHI KET LUAN:
  compare_with_notebook.py chi dam bao khop tuyet doi cho s01-s07 (bien doi du lieu
  thuan) va s09-s11 (nap lai model co san). Rieng s08 thi train that, ma LightGBM chay
  n_jobs > 1 hoac device = gpu KHONG dam bao tai lap. Neu khong do ma cu hua "khop tung
  bit" thi den luc bao ve se khong giai thich duoc tai sao chay lai ra so khac.

CACH DO: train DUNG MOT cau hinh HAI LAN lien tiep tren cung may, cung du lieu, cung
sieu tham so, cung seed. Neu hai lan do da khac nhau thi khoang cach voi notebook khong
phai loi refactor - do la muc nhieu san co cua chinh cong cu train.
"""
from __future__ import annotations

import argparse
import hashlib
import pickle
import sys
import tempfile
import time
from pathlib import Path

THU_MUC_PIPELINE = Path(__file__).resolve().parents[1]
if str(THU_MUC_PIPELINE) not in sys.path:
    sys.path.insert(0, str(THU_MUC_PIPELINE))

import numpy as np  # noqa: E402

from core.config import load_config  # noqa: E402
from core.context import Ctx  # noqa: E402
from core.lgbm import (  # noqa: E402
    dat_env_opencl,
    fit_an_toan,
    kiem_tra_gpu,
    them_tham_so_gpu,
)
from core.paths import Paths  # noqa: E402


def _md5_model(model) -> str:
    """Bam model sau khi pickle - dung dung cach ma s08d ghi ra dia."""
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=True) as f:
        pickle.dump(model, f)
        f.flush()
        return hashlib.md5(Path(f.name).read_bytes()).hexdigest()


def train_mot_lan(ctx: Ctx, gpu: bool):
    """Train dung 1 lan bang y het duong di cua s08c_train_final.train()."""
    tho, nguon = ctx.cfg.sieu_tham_so(ctx.loss_name, ctx.horizon_steps)
    params = them_tham_so_gpu(tho, ctx.cfg, gpu)
    model, lui_cpu = fit_an_toan(
        params, ctx.X_dev, ctx.y_dev, sample_weight=ctx.w_dev, cfg=ctx.cfg
    )
    return model, nguon, lui_cpu


def do(loss_name: str, horizon: int, thiet_bi: str, so_lan: int,
       deterministic: bool = False, n_jobs: int | None = None) -> int:
    from stages import s08a_prepare

    cfg = load_config()
    if thiet_bi == "cpu":
        cfg.runtime["gpu"]["use_gpu"] = False
    elif thiet_bi == "gpu":
        cfg.runtime["gpu"]["use_gpu"] = True
    if n_jobs is not None:
        cfg.runtime["threads"]["n_jobs"] = n_jobs
    cfg.runtime["lightgbm"]["deterministic"] = bool(deterministic)
    dat_env_opencl(cfg)

    ctx = Ctx(cfg=cfg, paths=Paths(cfg), loss_name=loss_name, horizon_steps=horizon)
    s08a_prepare.chuan_bi(ctx)

    gpu, loi = kiem_tra_gpu(cfg, cho_phep_thu_nghiem=True)
    print()
    print("=" * 76)
    print(f"WP0 - DO TINH TAI LAP CUA s08: {loss_name} h{horizon}")
    print("=" * 76)
    print(f"Thiet bi     : {'GPU' if gpu else 'CPU'}" + (f"  ({loi})" if loi else ""))
    print(f"n_jobs       : {cfg.runtime['threads']['n_jobs']}")
    print(f"deterministic: {cfg.runtime['lightgbm'].get('deterministic')}")
    print(f"Ma tran train: {ctx.X_dev.shape[0]:,} dong x {ctx.X_dev.shape[1]} dac trung")
    print(f"So lan train : {so_lan} (cung du lieu, cung seed, cung sieu tham so)")
    print()

    bam, du_bao = [], []
    for lan in range(1, so_lan + 1):
        t0 = time.time()
        model, nguon, lui_cpu = train_mot_lan(ctx, gpu)
        giay = time.time() - t0
        if lan == 1:
            print(f"Nguon sieu tham so: {nguon}")
            if lui_cpu:
                print("[CANH BAO] GPU loi giua chung, da lui ve CPU - ket qua do khong con y nghia")
        bam.append(_md5_model(model))
        du_bao.append(model.predict(ctx.X_dev))
        print(f"  lan {lan}: md5(model.pkl) = {bam[-1]}  ({giay:.0f} giay)")
        del model

    print()
    giong_nhau = len(set(bam)) == 1
    if giong_nhau:
        print("KET LUAN: TAI LAP DUOC - moi lan train ra dung mot file, khop tung byte.")
        print("          => co the doi hoi s08 khop tung bit voi notebook.")
        return 0

    # Khong khop -> do xem lech BAO NHIEU, de biet co anh huong con so bao cao khong
    goc = du_bao[0]
    print("KET LUAN: KHONG TAI LAP DUOC - cung mot lenh chay hai lan ra hai model khac nhau.")
    print()
    print("Muc nhieu san co cua chinh cong cu train (tren thang do k, truoc khi nhan nguoc):")
    for lan in range(2, so_lan + 1):
        d = np.abs(du_bao[lan - 1] - goc)
        print(f"  lan 1 vs lan {lan}: lech lon nhat {d.max():.3e} | trung binh {d.mean():.3e} "
              f"| so o khac {int((d > 0).sum()):,}/{len(d):,}")
    print()
    print("Nghia la: khoang cach giua pipeline va notebook o buoc s08 KHONG chung minh")
    print("duoc code sai - cung mot file code chay hai lan da ra hai ket qua.")
    print()
    print("Cac nut bam da do (2026-08-08, huber h1, 887.980 dong):")
    print("  GPU 32-bit, 6 thread          : lech 7,485e-02, khac CA 887.980 dong | 24 giay")
    print("  GPU 64-bit, 6 thread          : lech 1,110e-16, khac 7.421 dong      | 24 giay")
    print("  GPU 64-bit, 1 thread          : lech 6,939e-18, khac 41 dong         | 50 giay")
    print("  GPU 64-bit, 1 thread, determ. : 4/6 lan giong nhau                   | 50 giay")
    print("  CPU 6 thread, deterministic   : 3/3 lan GIONG HET, lech 0            | 31 giay")
    print()
    print("Da thu HET moi nut LightGBM co cho GPU - van hong 2/6 lan. Va cau hinh GPU tien")
    print("gan tai lap nhat lai CHAM HON CPU + deterministic (50 vs 31 giay), nen khong co")
    print("ly do gi de chon GPU. Dat runtime.yaml: gpu.use_gpu = false.")
    return 1


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--loss", default="huber", help="mae | huber | mse")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--thiet-bi", default="mac_dinh", choices=["mac_dinh", "cpu", "gpu"],
                   help="ep dung CPU hay GPU, bo qua runtime.yaml")
    p.add_argument("--so-lan", type=int, default=2)
    p.add_argument("--deterministic", action="store_true",
                   help="bat lightgbm.deterministic (tai lieu: chi co tac dung tren CPU)")
    p.add_argument("--n-jobs", type=int, default=None,
                   help="ep so thread CPU. Dat 1 de xem nhieu con lai co phai do thread khong.")
    a = p.parse_args()
    return do(a.loss, a.horizon, a.thiet_bi, a.so_lan, a.deterministic, a.n_jobs)


if __name__ == "__main__":
    sys.exit(main())
