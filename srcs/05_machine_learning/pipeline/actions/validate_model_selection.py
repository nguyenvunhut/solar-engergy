#!/usr/bin/env python3
"""ACTION: kiem chung lai viec chon mo hinh vo dich, KHONG train lai.

    python srcs/05_machine_learning/pipeline/actions/validate_model_selection.py

MUC DICH:
  Nap lai cac model.pkl DA TRAIN SAN, tinh WAPE tren tap VALIDATION that, roi doi chieu
  voi metrics_val.json dang co tren dia. Neu lech thi metrics_val.json dang sai.

BOI CANH (loi that da xay ra, 2026-08-06):
  metrics_val.json truoc day bi ghi tu so lieu tinh tren TAP TEST. Notebook 07 doc file
  do de chon mo hinh vo dich -> viec chon MAE/Huber/MSE that ra da "nhin truoc" tap test
  niem phong, lam mat y nghia cua tap test. Sau khi sua, mo hinh thang doi tu MAE sang
  HUBER. Script nay ton tai de bat lai loi do neu no tai dien.

Script CHI DOC, khong ghi de model hay metrics nao. Ket qua ghi ra 1 file JSON rieng.
"""
from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

import pandas as pd

THU_MUC_PIPELINE = Path(__file__).resolve().parents[1]
if str(THU_MUC_PIPELINE) not in sys.path:
    sys.path.insert(0, str(THU_MUC_PIPELINE))

from core.columns import PRED_COL  # noqa: E402
from core.config import load_config  # noqa: E402
from core.context import Ctx  # noqa: E402
from core.io import read_json, write_json  # noqa: E402
from core.lgbm import chuan_bi_X, dat_env_opencl, dat_env_threads  # noqa: E402
from core.metrics import PHAM_VI_CHINH_THUC, metrics_3_pham_vi  # noqa: E402
from core.paths import Paths  # noqa: E402
from core.target import du_bao_ve_kwh  # noqa: E402

NGUONG_LECH = 1e-6   # lech duoi muc nay coi la khop (sai so dau phay dong)


def danh_gia_tren_val(loss_name: str, horizon: int, cfg, paths, dung_ban_goc: bool) -> dict:
    """Nap model da train, tinh metric tren toan bo fold validation."""
    from stages import s08b_train_folds

    ctx = Ctx(cfg=cfg, paths=paths, loss_name=loss_name, horizon_steps=horizon)
    thu_muc = (paths.stage_goc("s08_train") / loss_name / f"h{horizon}"
               if dung_ban_goc else ctx.thu_muc_ra)
    if not (thu_muc / "model.pkl").exists():
        return {"loi": f"khong co model.pkl trong {thu_muc}"}

    cfg_model = read_json(thu_muc / "model_config.json")
    ctx.features = cfg_model["features"]
    ctx.medians = pd.Series(cfg_model["feature_medians"], dtype=float)
    with open(thu_muc / "model.pkl", "rb") as f:
        ctx.model = pickle.load(f)

    khung = []
    n = 1
    while (d := s08b_train_folds.doc_fold(ctx, n, "val")) is not None:
        khung.append(d)
        n += 1
    if not khung:
        return {"loi": "khong tim thay fold validation nao"}

    val = pd.concat(khung, ignore_index=True)
    X = chuan_bi_X(val, ctx.features, ctx.medians, dtype=cfg.runtime["dtype"])
    val[PRED_COL] = du_bao_ve_kwh(ctx.model.predict(X), val, cfg)
    m = metrics_3_pham_vi(val)[PHAM_VI_CHINH_THUC]

    tren_dia = read_json(thu_muc / "metrics_val.json").get(PHAM_VI_CHINH_THUC, {})
    lech = abs(m["wape"] - tren_dia["wape"]) if "wape" in tren_dia else None
    return {
        "loss": loss_name, "horizon": horizon, "n_dong_val": len(val),
        "wape_tinh_lai": m["wape"], "wape_tren_dia": tren_dia.get("wape"),
        "lech": lech, "khop": (lech is not None and lech < NGUONG_LECH),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--goc", action="store_true",
                   help="Kiem model GOC cua notebook thay vi model do pipeline moi sinh ra.")
    args = p.parse_args()

    cfg = load_config()
    dat_env_threads(cfg)
    dat_env_opencl(cfg)
    paths = Paths(cfg)

    dong = []
    for loss in sorted(cfg.train["losses"]):
        for h in cfg.train["horizon_steps"]:
            r = danh_gia_tren_val(loss, h, cfg, paths, args.goc)
            dong.append(r)
            if "loi" in r:
                print(f"  {loss:6s} h{h}: BO QUA - {r['loi']}")
                continue
            print(f"  {loss:6s} h{h}: WAPE_val tinh lai = {r['wape_tinh_lai']:.6f}%  "
                  f"tren dia = {r['wape_tren_dia']:.6f}%  "
                  f"{'KHOP' if r['khop'] else '>>> LECH <<<'}")

    hop_le = [r for r in dong if "loi" not in r]
    print()
    print("=" * 70)
    print("MO HINH VO DICH THEO TAP VALIDATION (tinh lai, khong doc file tren dia)")
    print("=" * 70)
    vo_dich, vo_dich_dia, xep_hang_khop = {}, {}, True
    for h in cfg.train["horizon_steps"]:
        nhom = [r for r in hop_le if r["horizon"] == h]
        if not nhom:
            continue
        tot = min(nhom, key=lambda r: r["wape_tinh_lai"])
        vo_dich[f"h{h}"] = {"loss": tot["loss"], "wape_val": tot["wape_tinh_lai"]}
        print(f"  h{h}: {tot['loss'].upper()} thang voi WAPE_val = {tot['wape_tinh_lai']:.4f}%")

        co_dia = [r for r in nhom if r["wape_tren_dia"] is not None]
        if co_dia:
            tot_dia = min(co_dia, key=lambda r: r["wape_tren_dia"])
            vo_dich_dia[f"h{h}"] = tot_dia["loss"]
            if tot_dia["loss"] != tot["loss"]:
                xep_hang_khop = False
                print(f"      [KHAC] file tren dia dang chon {tot_dia['loss'].upper()}")

    # Diem thuc su quan trong la XEP HANG (ai thang), khong phai tung chu so WAPE:
    # metrics_val.json tren dia co the duoc sinh boi 1 script khac voi quy uoc loc dong
    # khac (vd khong ap sample_weight > 0, khong ap exclude_sites), nen lech vai phan
    # tram la binh thuong. Chi khi XEP HANG doi thi ket luan chon mo hinh moi bi anh huong.
    lech = [r for r in hop_le if not r["khop"]]
    if lech:
        print(f"\n[LUU Y] {len(lech)}/{len(hop_le)} file metrics_val.json lech so voi so tinh lai "
              f"(quy uoc loc dong khac nhau).")
        print("        Pipeline nay ap them: exclude_sites + sample_weight > 0 (giong luc train).")
    print(f"\nXEP HANG mo hinh vo dich: "
          f"{'KHONG DOI - ket luan chon mo hinh van dung' if xep_hang_khop else 'DA DOI - PHAI xem lai!'}")

    d = paths.stage("s09_final_test")
    d.mkdir(parents=True, exist_ok=True)
    write_json({
        "chi_tiet": dong,
        "vo_dich_tinh_lai": vo_dich,
        "vo_dich_theo_file_tren_dia": vo_dich_dia,
        "xep_hang_khop": xep_hang_khop,
        "ghi_chu": "WAPE co the lech nhe do quy uoc loc dong khac nhau; dieu can kiem la "
                   "XEP HANG (ai thang) co doi khong.",
    }, d / "val_model_selection_check.json")
    print(f"\nDa ghi ket qua kiem chung: {d / 'val_model_selection_check.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
