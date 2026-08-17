"""Trong so mau va tam pham vi bao cao.

Copy NGUYEN SI tu build_sample_weight()/scope_masks() trong 04_x_train_*.py.
Nguyen tac cua srcs/05_machine_learning/Forcasting_v3: KHONG xoa dong outlier ma dat
weight = 0 - dong do khong tham gia ham muc tieu nhung VAN GIU trong du lieu de bao cao
(nho vay moi ve duoc bieu do actual-vs-predict chung minh model khong hoc theo outlier).
"""
from __future__ import annotations

import pandas as pd

from .columns import NHAN_OUTLIER, NHAN_SOURCE, TARGET_SHIFTED
from .config import Cfg
from .target import eligibility_mask, mau_chuan_hoa, nguong_cat

# Cac experiment coi gmm_if_consensus la du lieu dung duoc
_GIU_GMM = {"measured_only_headline", "measured_plus_etl_imputed", "tran_theo_du_lieu"}


def build_sample_weight(df: pd.DataFrame, cfg: Cfg) -> pd.Series:
    """Trong so mau theo bang experiment trong train.yaml.

    Binh thuong weight chi la 1.0 hoac 0.0; khi he_so_trong_so_dinh > 0 thi dong ban ngay
    duoc nhan them trong so theo k de model hoc ky vung dinh (THU NGHIEM 2).
    """
    experiment = cfg.train["experiment"]
    nguon = df[NHAN_SOURCE].astype(str)
    nhom = df[NHAN_OUTLIER].astype(str)
    w = pd.Series(0.0, index=df.index)
    el = eligibility_mask(df)

    measured = nguon.eq("measured")
    etl = nguon.eq("etl_imputed")
    normal = nhom.eq("normal")
    physical = nhom.eq("physical_over_capacity")
    gmm = nhom.eq("gmm_if_consensus")
    other_or_multi = nhom.isin(["other_physical_rule", "multiple_rules"])

    w.loc[el & measured & normal] = 1.0
    w.loc[el & measured & other_or_multi] = 1.0

    if experiment in _GIU_GMM:
        w.loc[el & measured & gmm] = 1.0
    elif experiment == "zero_weight_gmm_consensus":
        w.loc[el & measured & gmm] = 0.0
    elif experiment == "zero_weight_all_flagged":
        w.loc[el & measured & (gmm | other_or_multi)] = 0.0

    if experiment == "measured_plus_etl_imputed":
        w.loc[el & etl & normal] = 1.0

    # Vuot tran cong suat vat ly la bat kha thi nen phai loai. Nhung co
    # physical_over_capacity duoc gan tu capacity_kw METADATA, ma metadata nay sai o
    # 11/42 tram (site 19 vuot tran metadata 4,89 lan) nen dang loai oan du lieu do that.
    # Experiment 'tran_theo_du_lieu' doi sang tran tinh TU DU LIEU (cot tran_cong_suat,
    # sinh o stage s04 tu phan vi 99,9 cua tap TRAIN) - chi loai dong that su vuot.
    if experiment == "tran_theo_du_lieu" and "tran_cong_suat" in df.columns:
        he_so = float(cfg.train["tran_cong_suat_he_so"])
        vuot_tran_that = df[TARGET_SHIFTED] > df["tran_cong_suat"] * he_so
        w.loc[el & measured & physical & ~vuot_tran_that] = 1.0
        w.loc[vuot_tran_that] = 0.0
    else:
        w.loc[physical] = 0.0

    # THU NGHIEM 2: tang trong so vung dinh. k cang gan tran thi trong so cang lon.
    # Tran cua k o day PHAI la nguong cat dang hieu luc (nguong_cat), tuc phan vi 99 suy
    # tu chinh tap train - dung con so ma k_target dung. Truoc day cho nay ghi cung 1.5:
    # moi dong co k > nguong (dung 1% quan sat) nhan trong so toi 2,5 trong khi notebook
    # chi cho toi 1 + 1,3764 = 2,3764. Lech trong so o vung dinh keo WAPE kiem dinh lech
    # 0,01 - 0,09 diem du du lieu vao hai ben giong het nhau tung byte.
    he_so_dinh = float(cfg.train["he_so_trong_so_dinh"])
    if he_so_dinh > 0:
        eps = float(cfg.features["eps_elev"])
        k = (df[TARGET_SHIFTED] / mau_chuan_hoa(df, eps)).clip(0, nguong_cat(cfg)).fillna(0.0)
        w = w * (1.0 + he_so_dinh * k)
    return w


def scope_masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Tam pham vi bao cao, giong scope_masks cua srcs/Forcasting_v3.

    'headline' la pham vi duy nhat duoc dung cho con so cong bo: measured + du dieu kien,
    bo physical_over_capacity. TUYET DOI khong noi long de "co them du lieu".
    """
    el = eligibility_mask(df)
    nguon = df[NHAN_SOURCE].astype(str)
    nhom = df[NHAN_OUTLIER].astype(str)
    do_thay = nguon.eq("measured")
    return {
        "eligible_rows": el,
        "headline": el & do_thay & ~nhom.eq("physical_over_capacity"),
        "normal_rows": el & do_thay & nhom.eq("normal"),
        "etl_imputed_rows": el & nguon.eq("etl_imputed"),
        "gmm_if_consensus_rows": el & do_thay & nhom.eq("gmm_if_consensus"),
        "physical_over_capacity_rows": el & do_thay & nhom.eq("physical_over_capacity"),
        "other_physical_rule_rows": el & do_thay & nhom.eq("other_physical_rule"),
        "multiple_rules_rows": el & do_thay & nhom.eq("multiple_rules"),
    }
