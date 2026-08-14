"""Stage 01 (buoc 0): gan energy_source - dong nao DO THAT, dong nao ETL dien.

Tach tu buoc 3 cua run_reindex_mask_outlier() trong 01_data_preprocessing.py.
Logic goc: attach_energy_source() trong srcs/05_machine_learning/Forcasting_v3/
01_build_continuous_grid.py.

VI SAO DAY LA BUOC QUAN TRONG NHAT CUA CA STAGE 01:
  File mlmart_base (dau vao) da qua ETL nen KHONG con phan biet duoc gia tri nao do
  that, gia tri nao ETL dien vao. Phai doi chieu voi CSV raw goc moi biet.

  Toan bo con so cong bo trong bao cao chi tinh tren energy_source == 'measured'.
  Neu gan sai cot nay thi WAPE se duoc tinh ca tren du lieu bia ra -> con so vo nghia.
  Do la ly do stage nay bao loi ngay neu thieu file raw, thay vi chay tiep voi mac dinh.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.columns import SITE_COL, TIMESTAMP_COL
from core.config import Cfg
from core.paths import Paths

# Cot provenance khoi tao cho MOI dong goc (dong moi chen se duoc gan lai o s01a).
# THU TU trong dict la thu tu cot duoc them vao khung -> phai GIU DUNG thu tu cua
# notebook 01 cell 4, vi thu tu cot anh huong diem Mutual Information o stage s07.
KHOI_TAO = {
    "timestamp_was_inserted": False,
    "exclude_from_training": False,
    "exclude_reason": "",
    "training_quality_reason": "",
    "source_gap_id": pd.NA,
    "after_source_gap_steps_remaining": 0,
}


def gan_energy_source(df: pd.DataFrame, cfg: Cfg, paths: Paths) -> pd.DataFrame:
    """Doi chieu voi CSV raw: co trong raw va khong NaN -> 'measured', con lai 'etl_imputed'."""
    duong_raw = paths.raw_solar
    if not duong_raw.exists():
        raise FileNotFoundError(
            f"Khong tim thay CSV raw {duong_raw}. Khong co file nay thi khong xac dinh "
            f"duoc dong nao do that - moi con so bao cao se sai. Kiem paths.yaml: raw_solar"
        )

    ten = paths.raw_cot
    raw = pd.read_csv(duong_raw, usecols=[ten["site"], ten["timestamp"], ten["target"]])
    raw[ten["timestamp"]] = pd.to_datetime(raw[ten["timestamp"]], errors="coerce")
    raw = raw.rename(columns={
        ten["site"]: SITE_COL,
        ten["timestamp"]: TIMESTAMP_COL,
        ten["target"]: "_raw_gen",
    }).drop_duplicates(subset=[SITE_COL, TIMESTAMP_COL])

    out = df.merge(raw, on=[SITE_COL, TIMESTAMP_COL], how="left")
    out["energy_source"] = np.where(out["_raw_gen"].notna(), "measured", "etl_imputed")
    return out.drop(columns=["_raw_gen"])


def khoi_tao_provenance(df: pd.DataFrame) -> pd.DataFrame:
    """Khoi tao cac cot provenance con lai. Chi dat neu chua co, khong ghi de."""
    out = df.copy()
    for cot, gia_tri in KHOI_TAO.items():
        out[cot] = gia_tri
    for cot, gia_tri in (("gmm_if_outlier_flag", False), ("gmm_if_outlier_reason", "")):
        if cot not in out.columns:
            out[cot] = gia_tri
    return out


def chuan_bi_dau_vao(df: pd.DataFrame, cfg: Cfg, paths: Paths) -> pd.DataFrame:
    """Gan energy_source + khoi tao provenance. Goi truoc moi thao tac khac cua s01."""
    out = df.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)
    out = gan_energy_source(out, cfg, paths)
    out = khoi_tao_provenance(out)

    bang = out["energy_source"].value_counts()
    print("  Phan bo energy_source ban dau (doi chieu CSV raw):")
    for k, v in bang.items():
        print(f"     {k:<26} {v:>10,}  ({v / len(out) * 100:.1f}%)")
    if "measured" not in bang.index:
        raise ValueError(
            "Khong co dong nao duoc gan 'measured'. Kiem lai CSV raw co dung file khong, "
            "va ten cot trong paths.yaml: raw_cot co khop khong."
        )
    return out
