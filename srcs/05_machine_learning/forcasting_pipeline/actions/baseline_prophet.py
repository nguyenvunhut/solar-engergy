#!/usr/bin/env python3
"""ACTION (khong nam trong pipeline chuan): baseline Facebook Prophet de doi chieu.

    python srcs/05_machine_learning/pipeline/actions/baseline_prophet.py

VI SAO LA ACTION CHU KHONG PHAI STAGE:
  Prophet khong sinh ra dau vao cho bat ky stage nao - no chi la MOC DOI CHIEU de tinh
  Skill Score. Chay 1 lan roi giu ket qua, khong can chay lai moi lan train LightGBM.

DIEU KIEN SO SANH CONG BANG (quan trong khi bao cao):
  Prophet CHI hoc tu chinh lich su san luong + seasonality ngay/tuan cua no, KHONG duoc
  dua bat ky feature thoi tiet nao vao. Do la ban chat cua 1 baseline time-series thuan
  tuy - doi lap co chu dich voi LightGBM co day du feature thoi tiet.
  Ca hai deu do tren cung tap du lieu va cung pham vi 'measured'.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

THU_MUC_PIPELINE = Path(__file__).resolve().parents[1]
if str(THU_MUC_PIPELINE) not in sys.path:
    sys.path.insert(0, str(THU_MUC_PIPELINE))

from core.columns import SITE_COL, SOURCE_COL, TARGET_SHIFTED, TIMESTAMP_COL  # noqa: E402
from core.config import load_config  # noqa: E402
from core.io import write_csv, write_json  # noqa: E402
from core.metrics import compute_wape, skill_score  # noqa: E402
from core.paths import Paths  # noqa: E402

TY_LE_TRAIN = 0.8        # 80% dau chuoi thoi gian moi site de train, 20% cuoi de do
MIN_DONG_MOI_SITE = 200
MIN_DONG_TEST = 20


def train_prophet_1_site(d: pd.DataFrame) -> dict | None:
    """Train Prophet tren 80% dau chuoi thoi gian cua 1 site, du bao 20% cuoi.

    Cat theo THOI GIAN (iloc tren chuoi da sap xep), khong random - du lieu chuoi thoi
    gian ma cat ngau nhien la ro ri tuong lai vao qua khu.
    """
    from prophet import Prophet

    d = d.sort_values("ds")
    if len(d) < MIN_DONG_MOI_SITE:
        return None
    cat = int(len(d) * TY_LE_TRAIN)
    train, test = d.iloc[:cat][["ds", "y"]], d.iloc[cat:][["ds", "y"]]
    if len(test) < MIN_DONG_TEST:
        return None

    model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
    model.fit(train)
    du_bao = model.predict(test[["ds"]])

    y_pred = du_bao["yhat"].clip(lower=0).to_numpy()
    y_true = test["y"].to_numpy()
    return {
        "n_train": len(train), "n_test": len(test),
        "y_true": y_true, "y_pred": y_pred,
        "wape": compute_wape(y_true, y_pred),
    }


def chay_prophet(duong_audit: Path) -> tuple[pd.DataFrame, float]:
    """Chay Prophet cho tung site, tra ve (bang theo site, pooled WAPE)."""
    df = pd.read_parquet(duong_audit)
    print(f"Doc audit tu: {duong_audit} ({len(df):,} dong)")

    # Chi lay dong measured - dung pham vi headline chinh thuc cua du an
    if SOURCE_COL in df.columns:
        df = df[df[SOURCE_COL] == "measured"].copy()
    df["ds"] = pd.to_datetime(df[TIMESTAMP_COL])
    df["y"] = df[TARGET_SHIFTED] if TARGET_SHIFTED in df.columns else df["y_true"]

    sites = sorted(df[SITE_COL].unique())
    print(f"So site: {len(sites)} | so dong measured: {len(df):,}")

    t0 = time.time()
    dong, tong_loi, tong_thuc, loi_chay = [], 0.0, 0.0, []
    for i, s in enumerate(sites, 1):
        try:
            r = train_prophet_1_site(df[df[SITE_COL] == s])
        except Exception as e:  # noqa: BLE001 - Prophet co the loi tren site du lieu xau
            loi_chay.append({"site_id": s, "loi": str(e)[:120]})
            continue
        if r is None:
            continue
        tong_loi += float(np.abs(r["y_true"] - r["y_pred"]).sum())
        tong_thuc += float(np.abs(r["y_true"]).sum())
        dong.append({"site_id": s, "n_train": r["n_train"], "n_test": r["n_test"],
                     "wape": round(r["wape"], 4)})
        print(f"   [{i:>2}/{len(sites)}] site {s}: WAPE {r['wape']:.2f}% "
              f"({(time.time() - t0) / 60:.1f} phut)")

    if loi_chay:
        print(f"[CANH BAO] {len(loi_chay)} site loi khi chay Prophet: "
              f"{[x['site_id'] for x in loi_chay]}")
    gop = tong_loi / tong_thuc * 100.0 if tong_thuc > 0 else float("nan")
    return pd.DataFrame(dong), gop


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--loss", default="huber",
                   help="Loss cua model LightGBM dung de doi chieu Skill Score.")
    p.add_argument("--horizon", type=int, default=1)
    args = p.parse_args()

    cfg = load_config()
    paths = Paths(cfg)
    h = args.horizon
    duong_audit = paths.model_dir(args.loss, h) / f"prediction_audit_h{h}.parquet"
    if not duong_audit.exists():
        duong_audit = (paths.stage_goc("s08_train") / args.loss / f"h{h}"
                       / f"prediction_audit_h{h}.parquet")
    if not duong_audit.exists():
        raise SystemExit(f"Khong tim thay file audit de doi chieu: {duong_audit}. "
                         f"Chay stage s08 truoc.")

    bang, gop = chay_prophet(duong_audit)
    thu_muc = paths.action("baseline")
    thu_muc.mkdir(parents=True, exist_ok=True)
    write_csv(bang, thu_muc / f"prophet_baseline_by_site_h{h}.csv")

    # Skill Score cua LightGBM so voi Prophet - phai ghi ro baseline nao khi bao cao,
    # vi SS so voi Prophet khac han SS so voi persistence.
    ket = {"baseline": "prophet", "horizon_steps": h, "loss_doi_chieu": args.loss,
           "prophet_pooled_wape": gop, "so_site": int(len(bang))}
    duong_kq = paths.model_dir(args.loss, h) / "ket_qua_h%d.json" % h
    if duong_kq.exists():
        from core.io import read_json
        m = read_json(duong_kq).get("metrics_test", {}).get("measured_daylight", {})
        if "wape" in m:
            ket["lightgbm_wape"] = m["wape"]
            ket["skill_score_%"] = skill_score(m["wape"], gop)

    write_json(ket, thu_muc / f"prophet_summary_h{h}.json")
    print(f"\nProphet pooled WAPE = {gop:.4f}% tren {len(bang)} site")
    if "skill_score_%" in ket:
        print(f"LightGBM ({args.loss}) WAPE = {ket['lightgbm_wape']:.4f}% "
              f"-> Skill Score = {ket['skill_score_%']:+.2f}%")
    print(f"Da ghi vao: {thu_muc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
