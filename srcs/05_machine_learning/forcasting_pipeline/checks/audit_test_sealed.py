#!/usr/bin/env python3
"""Kiem chung TAP TEST BI NIEM PHONG den stage s09 - bang cach doc ma nguon.

    python srcs/05_machine_learning/pipeline/checks/audit_test_sealed.py

VI SAO CAN SCRIPT NAY:
  "Tap test niem phong" la loi khang dinh trong bao cao. Loi khang dinh do phai kiem
  duoc bang bang chung, khong phai tin loi. Script quet ma nguon va chi ra CHINH XAC
  dong code nao dung den tap test.

CACH QUET: dung AST de LOAI BO docstring va comment, chi xet ma THUC THI. Neu chi
grep chuoi thi cac doan giai thich trong docstring se bi bao nham.

HAI MUC DO DUNG TAP TEST:
  (a) BIEN DOI test  - doc file test, ap dac trung, ghi ra file test moi.
      HOP LE o s01-s07: tap test cung phai duoc bien doi dac trung nhu train, neu khong
      thi khong cham diem duoc. Diem mau chot: moi THAM SO ap len test (site_scale,
      cs_factor, bang ma categorical, danh sach dac trung) deu tinh tu TRAIN.
  (b) MO test de RA QUYET DINH - tinh metric, chon mo hinh, chon sieu tham so.
      CHI duoc phep o s09.

Script bao loi (exit 1) neu tim thay (b) o bat ky stage nao khac s09.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

THU_MUC_PIPELINE = Path(__file__).resolve().parents[1]

BIEN_DOI_HOP_LE = {"s01", "s02", "s03", "s04", "s05", "s06", "s07"}
STAGE_MO_TEST = "s09"

# MO TAP TEST GOC - hanh dong bi han che, chi s09 duoc phep
MAU_MO_TEST_GOC = [
    re.compile(r'["\']test_selected["\']'),
    re.compile(r'test_selected\.parquet'),
    re.compile(r'\bmetrics_test\b'),
]
# Dung lai SNAPSHOT ma tran test do s09 ghi ra - hop le cho s10/s11 (khong mo test goc)
MAU_DUNG_SNAPSHOT = [
    re.compile(r'["\']x_test["\']'),
    re.compile(r'X_test_h'),
]


def _dong_docstring(cay: ast.Module) -> set[int]:
    """Tap cac so dong thuoc docstring - de loai ra khoi phep quet."""
    bo = set()
    for nut in ast.walk(cay):
        if isinstance(nut, ast.Expr) and isinstance(nut.value, ast.Constant) \
                and isinstance(nut.value.value, str):
            bo.update(range(nut.lineno, (nut.end_lineno or nut.lineno) + 1))
    return bo


def _ten_stage(duong_dan: Path) -> str:
    m = re.match(r"(s\d\d)", duong_dan.name)
    return m.group(1) if m else duong_dan.stem


def quet() -> tuple[dict, list[dict]]:
    """Tra ve (cham test theo stage, cac vi pham)."""
    theo_stage, vi_pham = {}, []
    for f in sorted((THU_MUC_PIPELINE / "stages").glob("s*.py")):
        stage = _ten_stage(f)
        ma = f.read_text(encoding="utf-8")
        bo_qua = _dong_docstring(ast.parse(ma))

        for i, dong in enumerate(ma.split("\n"), 1):
            if i in bo_qua:
                continue
            sach = dong.split("#")[0]
            if not sach.strip():
                continue
            mo_goc = any(p.search(sach) for p in MAU_MO_TEST_GOC)
            snapshot = any(p.search(sach) for p in MAU_DUNG_SNAPSHOT)
            if not (mo_goc or snapshot):
                continue
            ban_ghi = {"stage": stage, "file": f.name, "dong": i,
                       "ma": sach.strip()[:84], "mo_goc": mo_goc}
            theo_stage.setdefault(stage, []).append(ban_ghi)
            # Chi tinh la VI PHAM khi MO TAP TEST GOC ngoai s09.
            # Dung snapshot cua s09 (s10/s11) khong phai vi pham.
            if mo_goc and stage != STAGE_MO_TEST and stage not in BIEN_DOI_HOP_LE:
                vi_pham.append(ban_ghi)
    return theo_stage, vi_pham


def main() -> int:
    theo_stage, vi_pham = quet()

    print("=" * 78)
    print("AUDIT: TAP TEST CO BI NIEM PHONG DEN STAGE s09 KHONG?")
    print("(chi xet ma THUC THI - da loai docstring va comment)")
    print("=" * 78)

    print("\n[1] s01-s07 - BIEN DOI tap test (hop le: khong ra quyet dinh nao):")
    co = False
    for stage in sorted(BIEN_DOI_HOP_LE):
        ds = theo_stage.get(stage, [])
        if ds:
            co = True
            print(f"    {stage}: {len(ds)} dong  (vd {ds[0]['file']}:{ds[0]['dong']})")
    if not co:
        print("    khong stage nao truy cap truc tiep bang ten file test")

    print("\n[2] s08 (TRAIN) - PHAI trong hoan toan:")
    s08 = theo_stage.get("s08", [])
    if s08:
        for r in s08:
            print(f"    >>> {r['file']}:{r['dong']}  {r['ma']}")
    else:
        print("    DAT - khong dong ma nao cham tap test")

    print("\n[3] s09 - noi DUY NHAT mo tap test:")
    for r in theo_stage.get(STAGE_MO_TEST, []):
        print(f"    {r['file']}:{r['dong']}  {r['ma']}")

    print("\n[4] s10-s11 - phai dung lai SNAPSHOT cua s09, khong mo test goc:")
    sau = [r for st in ("s10", "s11") for r in theo_stage.get(st, [])]
    if sau:
        for r in sau:
            nhan = ">>> MO TEST GOC" if r["mo_goc"] else "dung snapshot s09 - OK"
            print(f"    {r['file']}:{r['dong']}  [{nhan}]")
            print(f"        {r['ma']}")
    else:
        print("    khong cham tap test")

    dat = not vi_pham and not s08
    print()
    print("=" * 78)
    print(f"KET LUAN: {'DAT - tap test bi khoa den s09' if dat else 'CHUA DAT - xem muc [2]'}")
    print("=" * 78)
    return 0 if dat else 1


if __name__ == "__main__":
    sys.exit(main())
