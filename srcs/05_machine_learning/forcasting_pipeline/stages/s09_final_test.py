"""Stage 09: chon mo hinh vo dich roi cham diem tap test niem phong (dieu phoi).

    python srcs/05_machine_learning/pipeline/run.py --stage s09

HAI BUOC, KHONG DUOC DAO THU TU:
  s09a: chon mo hinh vo dich - CHI dua tren metrics_val.json (tap validation).
  s09b: cham diem mo hinh da chon tren tap test - DUY NHAT 1 LAN, chi de bao cao.

Neu dao thu tu (cham test truoc roi chon theo test) thi tap test khong con niem phong.
"""
from __future__ import annotations

from core.config import Cfg, load_config
from core.io import write_json
from core.paths import Paths
from stages import s09a_chon_mo_hinh, s09b_cham_diem_test


def run_s09(cfg: Cfg | None = None) -> dict:
    cfg = cfg or load_config()
    paths = Paths(cfg)

    print("BUOC 1/2: chon mo hinh vo dich TREN TAP VALIDATION")
    print("(tuyet doi khong doc metrics_test.json o buoc nay)\n")
    vo_dich = s09a_chon_mo_hinh.chon_vo_dich(cfg, paths)
    if not vo_dich:
        raise FileNotFoundError(
            "Khong tim thay metrics_val.json cua model nao. Chay stage s08 truoc:\n"
            "    python srcs/05_machine_learning/pipeline/run.py --stage s08"
        )

    thu_muc = paths.stage("s09_final_test")
    thu_muc.mkdir(parents=True, exist_ok=True)
    # Loai khoa noi bo truoc khi ghi: notebook 07 khong co 'thu_muc_model' (no suy ra
    # duong dan tu folder_name), de lai la best_loss.json lech byte. Ban trong bo nho
    # van giu khoa nay de s09b biet nap model.pkl o dau.
    write_json(
        {h: {k: v for k, v in d.items() if k not in s09a_chon_mo_hinh.KHOA_NOI_BO}
         for h, d in vo_dich.items()},
        thu_muc / "best_loss.json",
    )
    print(f"Da luu lua chon mo hinh: {thu_muc / 'best_loss.json'}\n")

    print("BUOC 2/2: cham diem tren TAP TEST NIEM PHONG (duy nhat 1 lan)\n")
    s09b_cham_diem_test.run_cham_diem(cfg, paths, vo_dich)
    return vo_dich
