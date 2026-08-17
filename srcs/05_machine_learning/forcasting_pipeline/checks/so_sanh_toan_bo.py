#!/usr/bin/env python3
"""Doi chieu TOAN BO artifact cua pipeline voi ket qua notebook, theo tung byte.

    python srcs/05_machine_learning/pipeline/checks/so_sanh_toan_bo.py
    python srcs/05_machine_learning/pipeline/checks/so_sanh_toan_bo.py --chi-tiet

CHI DOC - khong ghi de bat ky file nao.

So bang MD5 tung file nen bat duoc CA BA loai lech cung luc: gia tri, THU TU COT, va
THU TU DONG. So bang pandas rieng le de bo sot thu tu cot - da tung xay ra that
(feature_diagnostics.csv doi cho vif/duplicate_of va flag/pls_vip, phat hien 2026-08-08).

Voi file KHAC nhau thi mo ra doi chieu tiep de biet lech o dau:
  - parquet: so so dong, danh sach cot, thu tu cot, roi tung cot mot
  - json   : so khoa, so gia tri, va THU TU khoa
  - csv    : so dong dau de thay ngay cau truc co giong khong
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

THU_MUC_PIPELINE = Path(__file__).resolve().parents[1]
if str(THU_MUC_PIPELINE) not in sys.path:
    sys.path.insert(0, str(THU_MUC_PIPELINE))

from core.config import load_config  # noqa: E402
from core.paths import Paths  # noqa: E402

# Stage nao sinh ra file so sanh duoc. s06 ghi chung vao thu muc s06_diagnostics.
TEN_STAGE = ["s01_reindex", "s02_split", "s03_features", "s04_spatial", "s05_aggregate",
             "s06_diagnostics", "s07_selected", "s08_train", "s09_final_test",
             "s10_explain", "s11_phase_lag"]
DUOI_SO = (".parquet", ".json", ".csv")

# model.pkl khong so byte duoc mot cach co nghia: pickle nhung ca doi tuong Python, nen
# doi phien ban thu vien la doi byte du model y het. So bang du bao (checks/... rieng).
BO_QUA = {"model.pkl"}

# File TAN DU cua bug ro ri da sua, KHONG duoc coi la thieu.
# Ban cu cua notebook 06_x ghi X_test_h{n}.parquet ngay trong buoc train - tuc la da MO
# tap test truoc khi chon mo hinh. Lenh ghi do da bi bo khoi notebook (kiem 2026-08-08:
# ca 3 notebook khong con 'X_test_h' + to_parquet), nhung 6 file cu tu 31/07 - 06/08 van
# nam lai trong 06_train/. Pipeline KHONG ghi chung la DUNG. Snapshot ma tran test gio
# do stage s09 xuat ra 07_final_test/h{n}/, va notebook 08 doc tu do.
BO_QUA_MAU = ("X_test_h",)


def md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for khoi in iter(lambda: f.read(1 << 20), b""):
            h.update(khoi)
    return h.hexdigest()


def _chi_tiet_parquet(a: Path, b: Path) -> list[str]:
    import pandas as pd
    import pyarrow.parquet as pq

    ma, mb = pq.ParquetFile(a), pq.ParquetFile(b)
    ca, cb = list(ma.schema_arrow.names), list(mb.schema_arrow.names)
    if ma.metadata.num_rows != mb.metadata.num_rows:
        return [f"so dong: notebook {ma.metadata.num_rows:,} vs pipeline {mb.metadata.num_rows:,}"]
    if ca != cb:
        if sorted(ca) == sorted(cb):
            lech = next(f"vi tri {i}: '{x}' vs '{y}'"
                        for i, (x, y) in enumerate(zip(ca, cb)) if x != y)
            return [f"CUNG tap cot nhung KHAC THU TU - {lech}"]
        return [f"chi notebook co {[c for c in ca if c not in cb][:5]} | "
                f"chi pipeline co {[c for c in cb if c not in ca][:5]}"]

    da, db = pd.read_parquet(a), pd.read_parquet(b)
    ra = []
    for c in ca:
        x, y = da[c].to_numpy(), db[c].to_numpy()
        khac = ~((x == y) | (pd.isna(x) & pd.isna(y)))
        if khac.any():
            ra.append(f"cot '{c}': {int(khac.sum()):,} o khac")
    return ra[:8] or ["gia tri giong nhau (khac o metadata parquet, khong anh huong)"]


def _chi_tiet_json(a: Path, b: Path) -> list[str]:
    ja, jb = json.loads(a.read_text()), json.loads(b.read_text())
    if not (isinstance(ja, dict) and isinstance(jb, dict)):
        return ["noi dung khac (khong phai dict de so tung khoa)"]
    ra = []
    if list(ja) != list(jb):
        if sorted(ja) == sorted(jb):
            ra.append("cung tap khoa nhung KHAC THU TU")
        else:
            ra.append(f"chi notebook co {[k for k in ja if k not in jb][:5]} | "
                      f"chi pipeline co {[k for k in jb if k not in ja][:5]}")
    for k in ja:
        if k in jb and ja[k] != jb[k]:
            ra.append(f"khoa '{k}': {str(ja[k])[:60]} vs {str(jb[k])[:60]}")
    return ra[:8]


def _chi_tiet_csv(a: Path, b: Path) -> list[str]:
    da = a.read_text(encoding="utf-8", errors="replace").splitlines()
    db = b.read_text(encoding="utf-8", errors="replace").splitlines()
    if da[:1] != db[:1]:
        return [f"dong tieu de KHAC:", f"  notebook: {da[0][:110]}", f"  pipeline: {db[0][:110]}"]
    if len(da) != len(db):
        return [f"so dong: notebook {len(da):,} vs pipeline {len(db):,}"]
    lech = [i for i, (x, y) in enumerate(zip(da, db)) if x != y]
    return [f"{len(lech):,} dong khac, dong dau tien la dong {lech[0]}"] if lech else []


def chi_tiet(a: Path, b: Path) -> list[str]:
    try:
        if a.suffix == ".parquet":
            return _chi_tiet_parquet(a, b)
        if a.suffix == ".json":
            return _chi_tiet_json(a, b)
        return _chi_tiet_csv(a, b)
    except Exception as loi:  # noqa: BLE001 - chi de bao cao, khong duoc lam dung script
        return [f"(khong doc duoc de so chi tiet: {loi})"]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--chi-tiet", action="store_true",
                   help="voi file khac nhau thi mo ra so tiep de biet lech o dau")
    args = p.parse_args()

    paths = Paths(load_config())
    tong = khop = thieu = khac = 0
    ds_khac: list[tuple[Path, Path, str]] = []

    print("=" * 78)
    print("DOI CHIEU TUNG BYTE: ket qua notebook  vs  pipeline")
    print("=" * 78)
    for ten in TEN_STAGE:
        goc, moi = paths.stage_goc(ten), paths.stage(ten)
        if goc == moi:
            print(f"  {ten:16s} BO QUA - output_suffix rong, hai ben cung mot thu muc")
            continue
        if not goc.exists():
            print(f"  {ten:16s} khong co ket qua notebook ({goc.name})")
            continue
        # s01_reindex khai bao trong paths.yaml la duong dan FILE, khong phai thu muc -
        # rglob tren file tra ve rong nen phai xu ly rieng.
        nguon = [goc] if goc.is_file() else sorted(goc.rglob("*"))
        n_t = n_k = n_x = 0
        for a in nguon:
            if not a.is_file() or a.suffix not in DUOI_SO or a.name in BO_QUA:
                continue
            if any(m in a.name for m in BO_QUA_MAU):
                continue
            b = moi / a.relative_to(goc)
            tong += 1
            if not b.exists():
                thieu += 1; n_x += 1; continue
            if md5(a) == md5(b):
                khop += 1; n_t += 1
            else:
                khac += 1; n_k += 1; ds_khac.append((a, b, ten))
        trang_thai = "KHOP HET" if (n_k == 0 and n_x == 0) else f"{n_k} khac, {n_x} thieu"
        print(f"  {ten:16s} {n_t + n_k + n_x:>3} file  ->  {trang_thai}")

    if ds_khac:
        print()
        print("=" * 78)
        print("CAC FILE KHAC NHAU")
        print("=" * 78)
        for a, b, ten in ds_khac:
            print(f"\n  [{ten}] {a.name}")
            print(f"     notebook: {a}")
            if args.chi_tiet:
                for d in chi_tiet(a, b):
                    print(f"     {d}")

    print()
    print("=" * 78)
    print(f"KET QUA: {khop}/{tong} file khop TUNG BYTE | {khac} khac | {thieu} thieu")
    if khac == 0 and thieu == 0 and tong > 0:
        print("=> DAT - pipeline tai lap dung ket qua notebook.")
    elif not args.chi_tiet and ds_khac:
        print("=> Chay lai voi --chi-tiet de biet lech o dau.")
    print("=" * 78)
    return 0 if (khac == 0 and thieu == 0 and tong > 0) else 1


if __name__ == "__main__":
    sys.exit(main())
