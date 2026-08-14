"""Hang so ten cot va cac ham kiem tra cot bat buoc.

Truoc day cac hang so nay duoc khai bao lai o dau moi file .py (SITE_COL, TARGET_COL...
lap lai 9 lan), va COT_TAT_DINH duoc copy nguyen si vao ca 3 file train.
"""
from __future__ import annotations

import pandas as pd
import pyarrow.parquet as pq

from .config import Cfg

# ── Cot khoa - co dinh, khong dua vao YAML vi doi la vo toan bo schema ──
VERSION = "v3"
SITE_COL = "site_id"
TIMESTAMP_COL = "timestamp"
TARGET_COL = "energy_generated_kwh"
TARGET_SHIFTED = "y_true"          # target sau khi shift(-h)
PRED_COL = "y_pred"

# Cot provenance DUY NHAT cho target. Metric headline chi tinh tren 'measured'.
SOURCE_COL = "energy_source"
DAYLIGHT_COL = "is_daylight"
OUTLIER_COL = "outlier_group"

# Ten cot sau khi dich sang thoi diem muc tieu T+h (xem features.yaml)
HAU_TO_MUC_TIEU = "_mt"

# Cot nhan cua DONG MUC TIEU y(T+h) - khac cot cua dong dac trung tai T.
# Trong so mau phai xet nhom cua dong NHAN, khong phai dong dac trung.
NHAN_SOURCE = "nhan_energy_source"
NHAN_OUTLIER = "nhan_outlier_group"


def ten_cot_muc_tieu(ten_cot: str) -> str:
    """solar_elevation -> solar_elevation_mt"""
    return f"{ten_cot}{HAU_TO_MUC_TIEU}"


def cot_goc_cua_muc_tieu(ten_cot: str) -> str:
    """solar_elevation_mt -> solar_elevation (tra ve nguyen ten neu khong co hau to)"""
    return ten_cot[: -len(HAU_TO_MUC_TIEU)] if ten_cot.endswith(HAU_TO_MUC_TIEU) else ten_cot


def require_columns(df: pd.DataFrame, columns) -> None:
    """Bao loi som neu thieu cot bat buoc, thay vi de KeyError mo ho o sau."""
    thieu = [c for c in columns if c not in df.columns]
    if thieu:
        raise KeyError(f"Thieu cot bat buoc: {thieu}")


def kiem_cot_bat_buoc(duong_dan_parquet, cfg: Cfg) -> None:
    """Kiem file parquet co du cot de chuan hoa muc tieu va chan tran cong suat.

    Doc schema thoi (khong nap ca file) - nhanh, dung truoc khi train de fail som
    thay vi chay 20 phut roi moi bao loi.
    """
    co_san = set(pq.ParquetFile(str(duong_dan_parquet)).schema_arrow.names)
    thieu = [c for c in cfg.features["cot_bat_buoc"] if c not in co_san]
    if thieu:
        raise KeyError(
            f"Thieu cot bat buoc {thieu} trong {duong_dan_parquet}. "
            f"Hay chay lai stage s04 (spatial) -> s07 (select) truoc khi train."
        )


def bao_cao_nhom_dac_trung(duong_dan_parquet, cfg: Cfg) -> dict:
    """Dem xem tung nhom dac trung dien mat troi co du cot khong.

    Tra ve dict de stage tu quyet dinh in ra hay khong - ham nay khong tu print.
    """
    co_san = set(pq.ParquetFile(str(duong_dan_parquet)).schema_arrow.names)
    ket_qua = {}
    for ten_nhom in ("nhom_mat_troi", "nhom_quy_mo"):
        nhom = cfg.features[ten_nhom]
        ket_qua[ten_nhom] = {
            "co": [c for c in nhom if c in co_san],
            "thieu": [c for c in nhom if c not in co_san],
            "tong": len(nhom),
        }
    # lag/rolling ngan mang gia tri T-30 phut -> gay tre pha, phai canh bao
    lag = sorted(c for c in co_san if c.startswith(("lag_", "rolling_")))
    ket_qua["lag_rolling"] = {"tat_ca": lag, "ngan": [c for c in lag if "96" not in c]}
    return ket_qua


def tach_dac_trung_ngan(selected_features: list[str], cfg: Cfg) -> tuple[list[str], list[str]]:
    """Tach danh sach dac trung thanh (giu_lai, bo_di). Copy nguyen si tu 04_x_train_*.py.

    Quy tac: bo cot mang gia tri T-30 phut, GIU nhom '96' (lich su 1 ngay truoc, khong
    gay tre) va giu cac ngoai le da kiem chung (lag_4, rolling_*_4).

    lag_1 -> bo (audit: 39/40 site vuot nguong tre pha).
    lag_4 -> giu (audit PASS sach 0/40 site) du no khop bo_prefix_ngan - vi vay moi can
             danh sach giu_lai_ngoai_le, khong the chi dua vao prefix.
    """
    prefix_cam = tuple(cfg.features["bo_prefix_ngan"])
    ngoai_le = set(cfg.features["giu_lai_ngoai_le"])
    cam = set(cfg.features["deny_list"])

    bo_di = [
        c for c in selected_features
        if c in cam
        or (
            (c.startswith(prefix_cam) or c.startswith("rolling_"))
            and "96" not in c
            and c not in ngoai_le
        )
    ]
    giu_lai = [c for c in selected_features if c not in bo_di]
    return giu_lai, bo_di
