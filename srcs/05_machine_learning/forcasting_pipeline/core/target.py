"""Xay dung bien muc tieu va mask du dieu kien.

Copy NGUYEN SI logic tu them_muc_tieu()/mau_chuan_hoa()/eligibility_mask() trong
04_x_train_*.py (khop voi _label_series cua srcs/05_machine_learning/Forcasting_v3/
08_train_baselines.py). Doi logic o day = doi ket qua mo hinh.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .columns import (
    NHAN_SOURCE,
    SITE_COL,
    TARGET_COL,
    TARGET_SHIFTED,
    TIMESTAMP_COL,
    ten_cot_muc_tieu,
)
from .config import Cfg

# Cot phan loai can dich sang gia tri cua DONG NHAN y(T+h), kem gia tri mac dinh
# khi shift ra ngoai bien. Phai dich TRUOC khi dropna, neu khong shift bi lech.
COT_NHAN = {
    "energy_source": "",
    "outlier_group": "normal",
    "is_daylight": False,
    "exclude_from_training": False,
    "after_source_gap_steps_remaining": 0,
}


def mau_chuan_hoa(df: pd.DataFrame, eps_elev: float) -> np.ndarray:
    """Mau so chuan hoa muc tieu: quy mo tram nhan sin(goc cao mat troi).

    clip duoi bang eps_elev de khong chia cho ~0 luc binh minh/hoang hon.
    """
    return (df["site_scale"] * np.clip(df["sin_elevation"], eps_elev, None)).to_numpy()


def them_muc_tieu(df: pd.DataFrame, horizon_steps: int, cfg: Cfg) -> pd.DataFrame:
    """Muc tieu = san luong tai T + horizon_steps buoc (du bao that, khong phai nowcast).

    Dong thoi:
      1. Dich cac cot TAT DINH sang T+h thanh cot moi hau to _mt (GIU NGUYEN ban tai T).
         Khong phai leakage: vi tri mat troi/nhan thoi gian tai T+h la tinh toan thien van
         thuan tuy, dung o T da biet chinh xac. Thoi tiet thi KHONG dich (phai do moi biet).
      2. Dich cot phan loai sang gia tri cua DONG NHAN, dat tien to nhan_.
    """
    h = int(horizon_steps)
    freq = int(cfg.data["freq_minutes"])
    out = df.copy()
    out[TARGET_SHIFTED] = out.groupby(SITE_COL)[TARGET_COL].shift(-h)
    out["plot_timestamp"] = out[TIMESTAMP_COL] + pd.Timedelta(minutes=freq * h)
    g = out.groupby(SITE_COL)

    if cfg.features["them_dac_trung_muc_tieu"]:
        for c in [c for c in cfg.features["cot_tat_dinh"] if c in out.columns]:
            out[ten_cot_muc_tieu(c)] = g[c].shift(-h)

    for cot, mac_dinh in COT_NHAN.items():
        ten_nhan = f"nhan_{cot}"
        if cot in out.columns:
            out[ten_nhan] = g[cot].shift(-h).fillna(mac_dinh)
        else:
            out[ten_nhan] = mac_dinh
    return out.dropna(subset=[TARGET_SHIFTED])


def eligibility_mask(df: pd.DataFrame) -> pd.Series:
    """Dieu kien cung de 1 dong duoc dung, KHONG phu thuoc experiment.

    Chi giu dong ma NHAN cua no ve nguyen tac dung duoc: ban ngay, nguon la measured
    hoac etl_imputed, khong nam trong vung sau gap, khong bi exclude_from_training.
    Chinh sach outlier va etl_imputed do build_sample_weight() xu ly sau.
    """
    ban_ngay = df["nhan_is_daylight"].astype(bool)
    nguon = df[NHAN_SOURCE].astype(str)
    bi_loai = df["nhan_exclude_from_training"].astype(bool)
    sau_gap = (
        pd.to_numeric(df["nhan_after_source_gap_steps_remaining"], errors="coerce")
        .fillna(0)
        .gt(0)
    )
    m = ban_ngay & nguon.isin(["measured", "etl_imputed"]) & ~sau_gap & ~bi_loai
    return m & df[TARGET_SHIFTED].notna()


def k_target(df: pd.DataFrame, cfg: Cfg) -> np.ndarray:
    """Chuan hoa target ve ty le khong chieu k = y / (site_scale * sin_elevation).

    Model du bao k chu KHONG du bao thang kWh - de 42 tram quy mo khac nhau
    (vai kWp den MWp) chia se chung 1 mo hinh ma khong bi meo lech trong so.
    """
    eps = float(cfg.features["eps_elev"])
    k_raw = df[TARGET_SHIFTED].to_numpy() / mau_chuan_hoa(df, eps)
    return np.clip(k_raw, cfg.train["k_target_min"], nguong_cat(cfg))


def tinh_nguong_cat(df: pd.DataFrame, cfg: Cfg) -> float:
    """Suy nguong cat tu phan bo k tren tap TRAIN, dung phan vi clip_phan_vi.

    Notebook 06 dat CLIP_K = None roi goi tinh_clip_tu_train(): nguong KHONG duoc viet
    cung ma phai suy tu du lieu. Truoc day pipeline dung thang k_target_max = 1.5 trong
    train.yaml, tuc cat muc tieu huan luyen o mot nguong khac han notebook (1,3764) - hai
    ben train tren hai muc tieu khac nhau nen khong the ra cung ket qua.
    """
    eps = float(cfg.features["eps_elev"])
    k = pd.Series(df[TARGET_SHIFTED].to_numpy() / mau_chuan_hoa(df, eps))
    k = k.replace([np.inf, -np.inf], np.nan).dropna()
    return float(k.quantile(float(cfg.train["clip_phan_vi"])))


def dat_nguong_cat(cfg: Cfg, gia_tri: float) -> None:
    """Ghi nguong cat vao cfg de moi buoc sau dung chung DUNG mot con so."""
    cfg.train["clip_k"] = float(gia_tri)


def nguong_cat(cfg: Cfg) -> float:
    """Nguong cat dang hieu luc. Chua suy tu du lieu thi lui ve k_target_max."""
    gt = cfg.train.get("clip_k")
    return float(gt) if gt else float(cfg.train["k_target_max"])


def du_bao_ve_kwh(
    k_pred: np.ndarray, df: pd.DataFrame, cfg: Cfg, clip_k: float | None = None
) -> np.ndarray:
    """Nhan nguoc k_pred ve kWh that, chan tran cong suat, ep 0 khi troi toi.

    Bo qua buoc nay thi y_pred ra toan so 0..1,5 trong khi y_true la kWh (hang chuc)
    - dung bug "du bao duoi dat, thuc te tren troi" da gap truoc day.

    clip_k: tran chan k khi cham diem. De None thi dung train.k_target_max (= 1,5) -
    DUNG cach notebook 06_4 cham tap validation. Truyen vao thi dung con so do - dung
    cach notebook 07 cham tap TEST: no doc clip_k tu model_config.json cua chinh mo hinh
    thang cuoc, tuc chan bang DUNG nguong ma luc train da cat nhan (1,3764). Hai notebook
    that su khac nhau o diem nay, nen tham so phai de mo chu khong duoc chon cung mot ben:
    ep ca hai ve 1,5 thi tap test lech, ep ca hai ve clip_k thi tap validation lech.
    """
    eps = float(cfg.features["eps_elev"])
    tran = float(cfg.train["k_target_max"]) if clip_k is None else float(clip_k)
    k = np.clip(k_pred, cfg.train["k_target_min"], tran)
    y = k * mau_chuan_hoa(df, eps)
    if "tran_cong_suat" in df.columns:
        he_so = float(cfg.train["tran_cong_suat_he_so"])
        y = np.minimum(y, df["tran_cong_suat"].to_numpy() * he_so)
    return np.where(df["sin_elevation"].to_numpy() <= eps, 0.0, y)
