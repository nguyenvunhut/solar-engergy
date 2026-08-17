#!/usr/bin/env python3
"""Doi chieu ket qua pipeline moi (srcs/05_machine_learning/pipeline/) voi ket qua GOC cua notebook.

    python srcs/05_machine_learning/pipeline/checks/compare_with_notebook.py

CHI DOC - khong ghi de bat ky file ket qua nao.

BA TANG DAM BAO (xem docs/2026_08_07_Ke_Hoach_Refactor_Srcs_Pipeline.md muc 6):
  Tang 1 (s01-s07): bien doi du lieu thuan -> phai khop TUYET DOI.
  Tang 2 (s09-s11): nap lai model.pkl da co, khong train -> phai khop TUYET DOI.
  Tang 3 (s08 train): DA DO XONG (WP0, 2026-08-08) - xem checks/do_tinh_tai_lap_s08.py.
                      Ket qua: tren GPU thi KHONG BAO GIO tai lap duoc (3 lan chay ra 3
                      model khac nhau, lech toi 7,485e-02) vi LightGBM chi ho tro
                      deterministic tren CPU. Voi runtime.yaml hien tai (gpu.use_gpu =
                      false, lightgbm.deterministic = true) thi 3 lan chay ra DUNG MOT
                      file, khop tung byte -> Tang 3 cung phai khop TUYET DOI.
"""
from __future__ import annotations

import sys
from pathlib import Path

THU_MUC_PIPELINE = Path(__file__).resolve().parents[1]
if str(THU_MUC_PIPELINE) not in sys.path:
    sys.path.insert(0, str(THU_MUC_PIPELINE))

from core.config import load_config  # noqa: E402
from core.io import read_json  # noqa: E402
from core.metrics import PHAM_VI_CHINH_THUC  # noqa: E402
from core.paths import Paths  # noqa: E402

NGUONG_KHOP = 1e-9      # coi la khop TUYET DOI (chi con sai so dau phay dong)
NGUONG_BAO_CAO = 5e-5   # khop den chu so thu 4 - muc do chinh xac ma bao cao dung

# Con so CHINH THUC dang dung trong bao cao (pham vi measured_daylight).
# Ghi cung o day de script tu phat hien neu pipeline moi lam lech ket qua bao cao.
#
# CANH BAO 2026-08-08: hai con so nay sinh ra tu model train tren GPU, ma GPU KHONG tai
# lap duoc (do duoc: 3 lan chay ra 3 model khac nhau). Sau khi chuyen sang cau hinh tai
# lap duoc (CPU + deterministic) thi ket qua la 17,6011% (h1) va 21,3080% (h4).
# PHAI cap nhat hai con so nay - cung voi Section6.tex - ngay sau khi chay lai notebook 06.
CHUAN_BAO_CAO = {1: 17.571884381017092, 4: 21.313885611544970}

# ── Ghi chu ve sai so 6e-09 o h4 ──
# Hai notebook goc VON DA lech nhau, do ep kieu ma tran dac trung truoc khi predict:
#     notebook 06_2 (train)      : astype(float32) -> 21.3138856115450%
#     notebook 07  (final test)  : astype(float)   -> 21.3138856175704%   (= float64)
# Model duoc TRAIN tren float32, nen du bao cung bang float32 moi nhat quan. Pipeline
# nay dung float32 (runtime.yaml: dtype) va khop TUYET DOI voi 06_2. Chenh lech 6e-09
# khong anh huong bao cao (ca hai deu lam tron thanh 21,3139%).
DTYPE_NOTEBOOK_S09 = "float64"


def _wape(duong_dan: Path) -> float | None:
    if not duong_dan.exists():
        return None
    d = read_json(duong_dan)
    return d.get(PHAM_VI_CHINH_THUC, {}).get("wape")


def so_sanh_test(paths: Paths, horizons) -> list[dict]:
    """Tang 2: WAPE tren tap test cua pipeline moi vs notebook vs so bao cao."""
    dong = []
    for h in horizons:
        moi = _wape(paths.horizon_dir("s09_final_test", h) / "metrics_overall.json")
        goc = _wape(paths.stage_goc("s09_final_test") / f"h{h}" / "metrics_overall.json")
        chuan = CHUAN_BAO_CAO.get(h)
        dong.append({
            "horizon": f"h{h}", "moi": moi, "notebook": goc, "bao_cao": chuan,
            # notebook 07 predict bang float64 con model train bang float32, nen
            # doi chieu voi no chi doi khop den muc bao cao (4 chu so), khong bit-exact
            "khop_notebook": (moi is not None and goc is not None
                              and abs(moi - goc) < NGUONG_BAO_CAO),
            "khop_bao_cao": (moi is not None and chuan is not None
                             and abs(moi - chuan) < NGUONG_KHOP),
        })
    return dong


def so_sanh_chon_mo_hinh(paths: Paths) -> dict:
    """Kiem mo hinh vo dich cua pipeline moi co trung voi notebook khong."""
    def _doc(goc: Path) -> dict:
        f = goc / "best_loss.json"
        if not f.exists():
            return {}
        return {k: v.get("winning_loss") for k, v in read_json(f).items()}

    return {"moi": _doc(paths.stage("s09_final_test")),
            "notebook": _doc(paths.stage_goc("s09_final_test"))}


def main() -> int:
    cfg = load_config()
    paths = Paths(cfg)
    horizons = cfg.train["horizon_steps"]
    tat_dat = True

    print("=" * 76)
    print("TANG 2 - WAPE TREN TAP TEST (nap lai model da train, khong train lai)")
    print("=" * 76)
    for r in so_sanh_test(paths, horizons):
        if r["moi"] is None:
            print(f"  {r['horizon']}: pipeline moi chua co ket qua (chay stage s09 truoc)")
            continue
        print(f"  {r['horizon']}: moi = {r['moi']:.10f}%")
        for nhan, khoa, khop in (("notebook", "notebook", "khop_notebook"),
                                 ("bao cao ", "bao_cao", "khop_bao_cao")):
            if r[khoa] is None:
                print(f"       vs {nhan}: khong co so de doi chieu")
                continue
            lech = abs(r["moi"] - r[khoa])
            ghi_chu = ""
            if khoa == "notebook" and NGUONG_KHOP <= lech < NGUONG_BAO_CAO:
                ghi_chu = f"  (notebook 07 predict bang {DTYPE_NOTEBOOK_S09}, ta dung float32)"
            print(f"       vs {nhan}: {r[khoa]:.10f}%  lech = {lech:.2e}  "
                  f"{'KHOP' if r[khop] else '>>> LECH <<<'}{ghi_chu}")
            tat_dat &= r[khop]

    print()
    print("=" * 76)
    print("CHON MO HINH VO DICH (phai giong nhau)")
    print("=" * 76)
    ss = so_sanh_chon_mo_hinh(paths)
    if not ss["moi"]:
        print("  pipeline moi chua co best_loss.json (chay stage s09 truoc)")
    else:
        for h_label, loss_moi in sorted(ss["moi"].items()):
            loss_goc = ss["notebook"].get(h_label)
            khop = (loss_goc is None) or (loss_moi == loss_goc)
            tat_dat &= khop
            print(f"  {h_label}: moi = {loss_moi.upper():6s} | "
                  f"notebook = {(loss_goc or 'khong co').upper():8s} "
                  f"{'KHOP' if khop else '>>> KHAC <<<'}")

    print()
    print("=" * 76)
    print(f"KET LUAN: {'DAT - pipeline moi tai lap dung ket qua chinh thuc' if tat_dat else 'CHUA DAT - xem cac dong LECH o tren'}")
    print("=" * 76)
    print()
    print("Chua kiem o day (can chay rieng):")
    print("  - Tang 1 (s01-s07): chua viet, so parquet bang pd.testing.assert_frame_equal")
    print("  - Tang 3 (s08 train): phai do tinh tai lap truoc (WP0) moi ket luan duoc")
    return 0 if tat_dat else 1


if __name__ == "__main__":
    sys.exit(main())
