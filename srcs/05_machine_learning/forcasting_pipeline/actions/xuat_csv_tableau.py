#!/usr/bin/env python3
"""ACTION: xuat prediction_audit ra CSV cho Tableau.

    python -u srcs/05_machine_learning/pipeline/actions/xuat_csv_tableau.py

Sinh ra 2 file dung DUNG dinh dang ma nhom truong dang dung:
    reports/exports/prediction_audit_h1.csv
    reports/exports/prediction_audit_h4.csv

THU TU COT LA HOP DONG, KHONG DUOC DOI:
    site_id, timestamp, plot_timestamp_h{h}, energy_source, is_daylight,
    y_true_h{h}, y_pred_h{h}, residual_h{h},
    source_timestamp_h{h}, target_timestamp_h{h}, label_timestamp_h{h}
Ban Tableau da dung o nhom bam theo ten VA vi tri cot nay; them/bot/doi cho mot cot
la workbook ben kia hong. Neu can them cot (vi du du bao Prophet) thi them vao CUOI
va bao truoc cho nguoi dung Tableau.

Y NGHIA TRUC THOI GIAN (chi tiet o reports/exports/README_truc_thoi_gian.md):
  timestamp        = luc model nhan dac trung (INPUT)
  plot_timestamp   = moc ma y_true/y_pred cung mo ta (INPUT + h buoc)  <- ve bang cot nay
  Ve theo timestamp thay vi plot_timestamp se tao ra tre pha GIA.

KHONG GHI DE MU QUANG: neu file cu da ton tai, doi ten no thanh *_cu_<ngay>.csv
truoc khi ghi ban moi.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd

GOC_REPO = Path(__file__).resolve().parents[4]
AUDIT = GOC_REPO / "data/model/v4/07_final_test/prediction_audit.parquet"
RA = GOC_REPO / "reports/exports"

BUOC_PHUT = 15


def cot_theo_hop_dong(h: int) -> list[str]:
    return [
        "site_id", "timestamp", f"plot_timestamp_h{h}", "energy_source", "is_daylight",
        f"y_true_h{h}", f"y_pred_h{h}", f"residual_h{h}",
        f"source_timestamp_h{h}", f"target_timestamp_h{h}", f"label_timestamp_h{h}",
    ]


def dung_khung(au: pd.DataFrame, h: int) -> pd.DataFrame:
    """Dung dung 11 cot theo hop dong cho 1 horizon."""
    d = au[au[f"y_pred_h{h}"].notna()].copy()
    moc = d["timestamp"] + pd.Timedelta(minutes=BUOC_PHUT * h)
    # 3 cot duoi trung gia tri nhau nhung deu duoc giu lai: workbook Tableau ben nhom
    # truong dang tham chieu ca ba, bo bot la hong.
    d[f"plot_timestamp_h{h}"] = moc
    d[f"target_timestamp_h{h}"] = moc
    d[f"label_timestamp_h{h}"] = moc
    d[f"source_timestamp_h{h}"] = d["timestamp"]
    d[f"residual_h{h}"] = d[f"y_true_h{h}"] - d[f"y_pred_h{h}"]
    thieu = [c for c in cot_theo_hop_dong(h) if c not in d.columns]
    if thieu:
        raise SystemExit(f"h{h}: thieu cot {thieu} trong prediction_audit.")
    return d[cot_theo_hop_dong(h)].sort_values(["site_id", "timestamp"])


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--horizons", type=int, nargs="+", default=[1, 4])
    args = p.parse_args()

    if not AUDIT.exists():
        raise SystemExit(f"Khong tim thay {AUDIT}. Chay stage s09 truoc.")
    RA.mkdir(parents=True, exist_ok=True)

    au = pd.read_parquet(AUDIT)
    au["timestamp"] = pd.to_datetime(au["timestamp"])
    print(f"Doc {AUDIT.name}: {len(au):,} dong\n")

    for h in args.horizons:
        d = dung_khung(au, h)
        dich = RA / f"prediction_audit_h{h}.csv"
        if dich.exists():
            luu = dich.with_name(f"prediction_audit_h{h}_cu_{date.today():%Y_%m_%d}.csv")
            if not luu.exists():
                shutil.move(str(dich), str(luu))
                print(f"  [luu ban cu] {dich.name} -> {luu.name}")
        d.to_csv(dich, index=False, date_format="%Y-%m-%d %H:%M:%S")
        print(f"  [ghi] {dich.name}: {len(d):,} dong x {len(d.columns)} cot "
              f"({dich.stat().st_size / 1e6:.1f} MB)")
        print(f"        cot: {', '.join(d.columns)}")
        do = d[d['energy_source'].eq('measured') & d['is_daylight'].fillna(False)]
        wape = (do[f'y_true_h{h}'] - do[f'y_pred_h{h}']).abs().sum() / do[f'y_true_h{h}'].abs().sum() * 100
        print(f"        kiem tra: WAPE ban ngay/do that = {wape:.4f}% tren {len(do):,} dong\n")

    print(f"Da ghi vao: {RA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
