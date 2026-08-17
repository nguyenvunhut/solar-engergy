"""Stage 01c: phan loai outlier_group + kiem chung du lieu (QA/QC).

Tach tu muc 8-9 cua run_reindex_mask_outlier() trong 01_data_preprocessing.py.
Logic goc: classify_outlier_group() trong srcs/05_machine_learning/Forcasting_v3/
forecasting_common.py.

Cot outlier_group KHONG dung de xoa dong - no dung de dat SAMPLE WEIGHT (xem
core/weights.py). Dong bi gan co van nam trong du lieu de con ve duoc bieu do
chung minh model khong hoc theo outlier.
"""
from __future__ import annotations

import pandas as pd

from core.columns import SITE_COL, TARGET_COL, TIMESTAMP_COL
from core.config import Cfg

# Ly do -> ten nhom. Ly do khac 2 cai nay ma chi co 1 luat thi vao other_physical_rule.
LY_DO_SANG_NHOM = {
    "GMM_IF_CONSENSUS": "gmm_if_consensus",
    "PHYSICAL_OVER_CAPACITY": "physical_over_capacity",
}


def phan_loai_outlier(df: pd.DataFrame) -> pd.DataFrame:
    """Gan cot outlier_group tu gmm_if_outlier_flag va gmm_if_outlier_reason.

    So luat vi pham dem bang so dau '+' trong chuoi ly do (cac luat noi bang '+').
    Vi pham >= 2 luat thi xep vao multiple_rules - nhom nay dang ngo nhat.
    """
    out = df.copy()
    co = out["gmm_if_outlier_flag"].fillna(False).astype(bool)
    ly_do = out["gmm_if_outlier_reason"].fillna("").astype(str)
    so_luat = ly_do.str.count(r"\+") + ly_do.ne("").astype(int)

    out["outlier_group"] = "normal"
    mot_luat = co & so_luat.eq(1)
    nhieu_luat = co & so_luat.ge(2)

    for ten_ly_do, ten_nhom in LY_DO_SANG_NHOM.items():
        out.loc[mot_luat & ly_do.eq(ten_ly_do), "outlier_group"] = ten_nhom
    out.loc[
        mot_luat & ~ly_do.isin(list(LY_DO_SANG_NHOM)), "outlier_group"
    ] = "other_physical_rule"
    out.loc[nhieu_luat, "outlier_group"] = "multiple_rules"
    return out


def qa_qc(df: pd.DataFrame, cfg: Cfg | None = None) -> dict:
    """Kiem chung toan ven du lieu sau khi dung luoi. Tra ve dict de stage tu in.

    Bon dieu kien phai dung, sai bat ky cai nao la du lieu hong:
      1. Khong con target NaN (cascade phai dien het)
      2. Khong co (site, timestamp) trung lap
      3. Khoang cach giua 2 dong lien tiep trong 1 site luon = freq_minutes
      4. energy_source chi chua cac gia tri hop le trong data.yaml
    """
    ket = {}
    ket["so_dong"] = len(df)
    ket["so_site"] = int(df[SITE_COL].nunique())
    ket["target_nan"] = int(df[TARGET_COL].isna().sum())
    ket["trung_lap"] = int(df.duplicated([SITE_COL, TIMESTAMP_COL]).sum())

    hieu = df.groupby(SITE_COL)[TIMESTAMP_COL].diff().dropna()
    if len(hieu):
        phut = hieu.dt.total_seconds() / 60
        ket["buoc_thoi_gian_khac_nhau"] = sorted(phut.unique().tolist())[:5]
        ket["luoi_deu"] = bool(phut.nunique() == 1)
    else:
        ket["luoi_deu"] = True

    ket["phan_bo_energy_source"] = df["energy_source"].value_counts().to_dict()
    ket["phan_bo_outlier_group"] = df["outlier_group"].value_counts().to_dict()

    if cfg is not None:
        hop_le = set(cfg.data["energy_source_values"])
        la = sorted(set(df["energy_source"].dropna().unique()) - hop_le - {""})
        ket["energy_source_la"] = la

    ket["dat"] = (
        ket["target_nan"] == 0
        and ket["trung_lap"] == 0
        and ket.get("luoi_deu", False)
        and not ket.get("energy_source_la")
    )
    return ket


def in_qa_qc(ket: dict) -> None:
    print("--- KIEM CHUNG TOAN VEN DU LIEU (QA/QC) ---")
    print(f"  So dong        : {ket['so_dong']:,} | so site: {ket['so_site']}")
    print(f"  Target NaN     : {ket['target_nan']:,} (phai = 0)")
    print(f"  (site,ts) trung: {ket['trung_lap']:,} (phai = 0)")
    print(f"  Luoi deu       : {ket.get('luoi_deu')} "
          f"(cac buoc: {ket.get('buoc_thoi_gian_khac_nhau')})")
    if ket.get("energy_source_la"):
        print(f"  [LOI] energy_source la: {ket['energy_source_la']}")
    print("  Phan bo energy_source:")
    for k, v in ket["phan_bo_energy_source"].items():
        print(f"     {k or '(rong)':<26} {v:>10,}")
    print("  Phan bo outlier_group:")
    for k, v in ket["phan_bo_outlier_group"].items():
        print(f"     {k:<26} {v:>10,}")
    print(f"  KET LUAN: {'DAT' if ket['dat'] else '>>> CHUA DAT - xem cac dong tren <<<'}")
