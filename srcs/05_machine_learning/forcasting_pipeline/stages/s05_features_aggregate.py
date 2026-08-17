"""Stage 05: dac trung tuong tac thoi tiet + ma hoa categorical (dieu phoi).

    python srcs/05_machine_learning/pipeline/run.py --stage s05

Dau vao : data/model/v3/03_2_features_spatial<suffix>/
Dau ra  : data/model/v3/03_3_features_aggregate<suffix>/

BANG MA CATEGORICAL FIT THEO TUNG CAP (chong ro ri):
  development -> test        : bang ma fit tren development
  train       -> val         : bang ma fit tren train
  fold_n_train -> fold_n_val : bang ma fit rieng cho tung fold
Khong dung 1 bang ma chung cho tat ca, vi nhu vay bang ma se chua thong tin cua
cac hang muc chi xuat hien o tap danh gia.
"""
from __future__ import annotations

import gc

from core.columns import VERSION
from core.config import Cfg, load_config
from core.io import read_parquet, write_json, write_parquet
from core.paths import Paths
from stages import s05a_weather_interaction, s05b_categorical_encode


def _xu_ly_cap(duong_train, duong_khac, ra_train, ra_khac) -> tuple[dict, dict]:
    """Xu ly 1 cap (train, khac): tao dac trung roi ma hoa bang bang ma fit tren train."""
    tr = s05a_weather_interaction.add_weather_domain_features(read_parquet(duong_train))
    kh = s05a_weather_interaction.add_weather_domain_features(read_parquet(duong_khac))

    tr, kh, bang_ma = s05b_categorical_encode.encode_train_and_other(tr, kh)
    write_parquet(tr, ra_train)
    write_parquet(kh, ra_khac)

    tk = {
        "train": (len(tr), tr.shape[1]),
        "khac": (len(kh), kh.shape[1]),
        "so_bang_ma": len(bang_ma),
        "gia_tri_la": s05b_categorical_encode.bao_cao_gia_tri_la(kh),
        "qa_inf": s05a_weather_interaction.kiem_khong_inf(tr),
    }
    del tr, kh
    gc.collect()
    return tk, bang_ma


def run_s05(cfg: Cfg | None = None):
    cfg = cfg or load_config()
    paths = Paths(cfg)
    vao = paths.stage_doc("s04_spatial")
    ra = paths.stage("s05_aggregate")
    if not vao.exists():
        raise FileNotFoundError(
            f"Khong tim thay {vao}. Chay stage s04 truoc:\n"
            f"    python srcs/05_machine_learning/pipeline/run.py --stage s04"
        )
    ra.mkdir(parents=True, exist_ok=True)
    tat_ca_bang_ma = {}

    print("[1/3] development -> test (bang ma fit tren development)")
    tk, bm = _xu_ly_cap(
        vao / f"{VERSION}_development_spatial.parquet",
        vao / f"{VERSION}_test_spatial.parquet",
        ra / f"{VERSION}_development_features.parquet",
        ra / f"{VERSION}_test_features.parquet",
    )
    tat_ca_bang_ma["development_to_test"] = bm
    print(f"      development: {tk['train'][0]:>9,} dong x {tk['train'][1]} cot")
    print(f"      test       : {tk['khac'][0]:>9,} dong x {tk['khac'][1]} cot")
    print(f"      {tk['so_bang_ma']} bang ma | gia tri la o test: {tk['gia_tri_la'] or 'khong'}")
    print(f"      QA khong co inf: {tk['qa_inf']['dat']}\n")

    print("[2/3] train -> val (bang ma fit tren train)")
    tk, bm = _xu_ly_cap(
        vao / f"{VERSION}_train_spatial.parquet",
        vao / f"{VERSION}_val_spatial.parquet",
        ra / f"{VERSION}_train_features.parquet",
        ra / f"{VERSION}_val_features.parquet",
    )
    tat_ca_bang_ma["train_to_val"] = bm
    print(f"      train: {tk['train'][0]:>9,} dong | val: {tk['khac'][0]:>9,} dong\n")

    print("[3/3] 5 fold (bang ma fit rieng tung fold)")
    thu_muc_fold = vao / "time_series_folds"
    ra_fold = ra / "time_series_folds"
    ra_fold.mkdir(parents=True, exist_ok=True)
    for f in sorted(thu_muc_fold.glob("fold_*_train_spatial.parquet")):
        goc = f.name.replace("_train_spatial.parquet", "")
        duong_val = thu_muc_fold / f"{goc}_val_spatial.parquet"
        if not duong_val.exists():
            raise FileNotFoundError(f"Thieu file val cua fold: {duong_val}")
        tk, bm = _xu_ly_cap(
            f, duong_val,
            ra_fold / f"{goc}_train_features.parquet",
            ra_fold / f"{goc}_val_features.parquet",
        )
        tat_ca_bang_ma[f"{goc}_train_to_val"] = bm
        print(f"      {goc:<8}: train {tk['train'][0]:>9,} dong | "
              f"val {tk['khac'][0]:>9,} dong | {tk['train'][1]} cot")

    write_json(tat_ca_bang_ma, ra / f"{VERSION}_category_maps.json")
    print(f"\nDa ghi vao: {ra}")
    print(f"  {len(tat_ca_bang_ma)} bo bang ma categorical -> {VERSION}_category_maps.json")
    return ra
