"""Stage 07a: danh sach CAM (deny list) - chan ro ri nhan va cong tuyen cau truc.

Tach tu buoc 4 cua run_select_features() trong 03_feature_selection.py.

DAY LA HANG RAO CHONG RO RI QUAN TRONG NHAT CUA CA PIPELINE. Bo sot 1 cot o day thi
model dat R2 rat cao tren train/val nhung HOAN TOAN THAT BAI khi du bao that.
"""
from __future__ import annotations

import pandas as pd

# ── 1. Chinh bien muc tieu ──
DENY_TARGET = ["energy_generated_kwh"]

# ── 2. Provenance / outlier ──
# BANG CHUNG tu du lieu tho:
#   - Khi exclude_from_training == True thi san luong = 0.0 o 100.00% truong hop
#     (36.847 dong trong tap train, deu la machine_failure_zero do gap >= 24h).
#   - Nhom outlier_group == physical_over_capacity co san luong trung binh 19,43 kWh,
#     vuot xa nhom normal (2,75 kWh).
# HAU QUA NEU DUA VAO MODEL: cac cot nay duoc tao SAU KHI da do va kiem tra target.
# Model chi can tra bang "thay co thi doan 0" -> diem cuc cao tren train/val nhung
# THAT BAI khi du bao tuong lai (luc do chua co du lieu do de gan co).
# VAI TRO DUNG cua chung: (1) loc dong khoi train, (2) gan trong so mau,
# (3) khoanh vung tinh metric theo nhom. KHONG duoc lam dac trung dau vao.
DENY_PROVENANCE_OUTLIER = [
    "gmm_if_outlier_flag", "gmm_if_outlier_reason", "outlier_group",
    "exclude_from_training", "exclude_reason", "training_quality_reason",
    "energy_source", "timestamp_was_inserted", "source_gap_id",
    "after_source_gap_steps_remaining",
]

# ── 3. Co ban ngay / audit ──
DENY_DAYLIGHT_AUDIT = [
    "is_daylight", "weather_is_day", "sunshine_duration", "weather_is_observed",
]

# ── 4. Khoa ID - tranh model hoc vet index thay vi hoc dac tinh vat ly ──
DENY_IDS = [
    "gen_id", "site_id", "geo_id", "date_id", "time_id", "weather_id", "weather_type_id",
]

# ── 5. Categorical tho (da duoc ma hoa thanh *_enc o stage s05) ──
DENY_RAW_CATEGORICAL = [
    "site_id", "campus_name", "location_name", "site_metric", "panel",
    "inverter", "optimizers", "weather_join_method",
    "weather_condition", "weather_description",
]

# ── 6. Thoi gian tho ──
# 'year' bi cam vi TANG DON DIEU, khong tuan hoan:
#   train year = {2020, 2021} | test year = {2021, 2022}
#   -> 455.616 dong test (89%) co year = 2022 CHUA TUNG xuat hien luc train.
#   Cay quyet dinh tach theo 'year <= 2021' se ap quy tac hoc tu gia tri chua he thay.
# Khac han month / day_of_year / doy_sin / doy_cos: nhung cai do TUAN HOAN, lap hang nam.
DENY_RAW_TIME = ["timestamp", "time_diff", "full_date", "weather_timestamp", "year"]

# ── 7. Cong tuyen CAU TRUC (khong phai tuong quan ngau nhien) ──
# dni_ratio: VIF vo cuc tren mau ban ngay. Giu diffuse_ratio (y nghia vat ly ro: ty le
#   may mu), bo dni_ratio.
# con_cach_tran = tran_cong_suat - ky_vong: to hop tuyen tinh CHINH XAC cua 2 cot con lai,
#   khong mang thong tin moi.
# site_scale va tran_cong_suat deu la hang so theo site (phan vi 99 va 99,9 cua CUNG mot
#   phan phoi) nen tuong quan gan tuyet doi; giu tran_cong_suat (dang dung truc tiep trong
#   ty_le_bao_hoa/con_cach_tran), bo site_scale khoi tap dac trung train.
DENY_STRUCTURAL_COLLINEAR = ["dni_ratio", "con_cach_tran", "site_scale"]

# ── 8. Metadata cua buoc split (do stage s02 gan) ──
# KHONG cam ca tien to 'v3_' vi cac dac trung that cung dung tien to nay.
SPLIT_META = [
    "v3_holdout_split", "v3_test_start_timestamp", "v3_split_strategy",
    "v3_n_time_series_splits", "v3_split", "v3_cv_fold", "v3_cv_role",
]


def dung_deny_list(df: pd.DataFrame, df_diag: pd.DataFrame | None = None) -> tuple[set, dict]:
    """Gop toan bo deny list. Tra ve (tap cam, chi tiet tung nhom de bao cao)."""
    cam = set(
        DENY_TARGET + DENY_PROVENANCE_OUTLIER + DENY_DAYLIGHT_AUDIT
        + DENY_IDS + DENY_RAW_TIME + DENY_RAW_CATEGORICAL + DENY_STRUCTURAL_COLLINEAR
    )
    cam.update(c for c in SPLIT_META if c in df.columns)
    # Moi cot co chua 'timestamp' trong ten: thoi gian tho tang don dieu, model se hoc
    # theo do lon cua timestamp va khong ngoai suy duoc sang tuong lai.
    cam.update(c for c in df.columns if "timestamp" in c.lower())

    trung_lap = set()
    if df_diag is not None and "duplicate_of" in df_diag.columns:
        trung_lap = set(df_diag.loc[df_diag["duplicate_of"].notna(), "feature"])
        cam.update(trung_lap)

    chi_tiet = {
        "target": len(DENY_TARGET),
        "provenance_outlier": len(DENY_PROVENANCE_OUTLIER),
        "daylight_audit": len(DENY_DAYLIGHT_AUDIT),
        "ids": len(DENY_IDS),
        "raw_time": len(DENY_RAW_TIME),
        "raw_categorical": len(DENY_RAW_CATEGORICAL),
        "structural_collinear": len(DENY_STRUCTURAL_COLLINEAR),
        "trung_lap_tu_s06": len(trung_lap),
        "tong_cam": len(cam),
    }
    return cam, chi_tiet


def dac_trung_ung_vien(df: pd.DataFrame, cam: set) -> list[str]:
    return [c for c in df.columns if c not in cam]
