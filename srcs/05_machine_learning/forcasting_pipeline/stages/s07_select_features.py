"""Stage 07: chon dac trung bang Mutual Information + deny list (dieu phoi).

    python srcs/05_machine_learning/pipeline/run.py --stage s07

Dau vao : data/model/v3/03_3_features_aggregate<suffix>/
          data/model/v3/04_diagnostics<suffix>/feature_diagnostics.csv
Dau ra  : data/model/v3/05_selected<suffix>/
            selected_features.json | feature_scores.csv | *_selected.parquet

BA LOP LOC, theo dung thu tu:
  1. DENY LIST  (s07a) - cam tuyet doi: ro ri nhan, khoa ID, thoi gian tho, cong tuyen
                         cau truc. Day la hang rao chong ro ri quan trong nhat.
  2. TOP-K MI   (s07b) - trong so con lai, giu 35 dac trung co Mutual Information cao nhat.
  3. BAO VE     (s07b) - bo sung lai cac dac trung co ly do vat ly du diem MI thap.

CHAM DIEM CHI TREN TAP TRAIN. Val/test khong duoc gop vao - neu khong thi danh sach
dac trung da mang thong tin cua tap danh gia.
"""
from __future__ import annotations

import gc

import pandas as pd

from core.columns import TARGET_COL, VERSION
from core.config import Cfg, load_config
from core.io import read_json, write_csv, write_json, write_parquet
from core.paths import Paths
from stages import s07a_deny_list, s07b_mutual_info

# Cot khong phai dac trung nhung PHAI mang theo cho cac stage sau dung.
# site_scale va pv_clr_lonij deu bi cam lam dau vao model (xem s07a_deny_list) nhung van
# phai giu trong tep: chung la MAU SO chuan hoa muc tieu, thieu thi buoc cham diem khong
# nhan nguoc duoc tu k ve kWh. pv_clr_lonij la mau so cua Lonij et al. (2012), giu de doi
# chieu hai cach chuan hoa.
GIU_THEM = [
    TARGET_COL, "site_id", "timestamp",
    "energy_source", "exclude_from_training", "outlier_group",
    "has_complete_history_features", "is_daylight", "site_scale", "pv_clr_lonij",
]


def run_s07(cfg: Cfg | None = None):
    cfg = cfg or load_config()
    paths = Paths(cfg)
    vao = paths.stage_doc("s05_aggregate")
    ra = paths.stage("s07_selected")
    duong_train = vao / f"{VERSION}_train_features.parquet"
    if not duong_train.exists():
        raise FileNotFoundError(
            f"Khong tim thay {duong_train}. Chay stage s05 truoc."
        )

    duong_diag = paths.stage_doc("s06_diagnostics") / "feature_diagnostics.csv"
    df_diag = pd.read_csv(duong_diag) if duong_diag.exists() else None
    if df_diag is None:
        print(f"[CANH BAO] Khong co {duong_diag} - bo qua buoc loai cot trung lap. "
              f"Nen chay stage s06 truoc.")

    print("[1/4] Ap DENY LIST")
    df_train = pd.read_parquet(duong_train)
    cam, chi_tiet = s07a_deny_list.dung_deny_list(df_train, df_diag)
    ung_vien = s07a_deny_list.dac_trung_ung_vien(df_train, cam)
    for k, v in chi_tiet.items():
        print(f"      {k:24s} {v}")
    print(f"      con {len(ung_vien)} ung vien tren {df_train.shape[1]} cot\n")

    print(f"[2/4] Cham diem Mutual Information (mau {s07b_mutual_info.CO_MAU_MI:,} dong)")
    df_diem = s07b_mutual_info.cham_diem_mi(df_train, ung_vien, TARGET_COL)
    df_gop = s07b_mutual_info.gop_voi_chan_doan(df_diem, df_diag)
    print(df_gop.head(10).to_string(index=False))
    print()

    print(f"[3/4] Chon Top-{s07b_mutual_info.TOP_K} + bo sung nhom BAO VE")
    chon, tk = s07b_mutual_info.chon_top_k(df_gop)
    for k, v in tk.items():
        print(f"      {k:28s} {v}")
    danh_sach = chon["feature"].tolist()
    print()

    ra.mkdir(parents=True, exist_ok=True)
    write_json({
        "version": VERSION,
        "top_k": s07b_mutual_info.TOP_K,
        "selected_features": danh_sach,
        "deny_list_count": len(cam),
        "bao_ve": [c for c in s07b_mutual_info.BAO_VE if c in df_gop["feature"].values],
        "bao_ve_bi_top_k_cat": tk["bao_ve_bi_top_k_cat_da_bu_lai"],
        "so_dac_trung_cuoi": len(danh_sach),
    }, ra / "selected_features.json")
    write_csv(df_gop, ra / "feature_scores.csv")
    del df_train
    gc.collect()

    print("[4/4] Ghi lai cac tap chi giu dac trung da chon")
    giu = list(dict.fromkeys(danh_sach + GIU_THEM))
    nguon = [(vao / f"{VERSION}_{t}_features.parquet",
              ra / f"{VERSION}_{t}_selected.parquet")
             for t in ("train", "val", "test", "development")]
    thu_muc_fold = vao / "time_series_folds"
    if thu_muc_fold.is_dir():
        (ra / "time_series_folds").mkdir(parents=True, exist_ok=True)
        nguon += [(f, ra / "time_series_folds" / f.name.replace("_features.", "_selected."))
                  for f in sorted(thu_muc_fold.glob("*_features.parquet"))]

    for src, dst in nguon:
        if not src.exists():
            print(f"      [BO QUA] khong co {src.name}")
            continue
        d = pd.read_parquet(src)
        co = [c for c in giu if c in d.columns]
        write_parquet(d[co], dst)
        print(f"      {dst.name:44s} {len(d):>9,} dong x {len(co)} cot")
        del d
        gc.collect()

    print(f"\nDa ghi vao: {ra}")
    return danh_sach
