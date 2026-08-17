"""Stage 05b: ma hoa bien phan loai - bang ma fit CHI tren phia train.

Tach tu buoc 5 cua run_features_aggregate() trong 02_3_features_aggregate.py.

VI SAO KHONG DUNG cat.codes: pandas gan ma theo thu tu xuat hien trong TUNG frame, nen
cung 1 gia tri se co ma khac nhau giua cac fold -> model hoc mot bang ma roi duoc cham
diem bang bang ma khac. Loi nay khong bao gi ca, chi lam ket qua te di mot cach kho hieu.

QUY UOC MA:
    thieu (__MISSING__)          -> 0
    hang muc da biet luc fit     -> 1..N (theo thu tu alphabet, on dinh giua cac lan chay)
    gia tri LA luc transform     -> -1  (kem co *_unknown_flag = 1)

CHONG RO RI: fit tren train, ap cho val/test. Neu fit tren toan bo du lieu thi bang ma
da chua thong tin ve cac hang muc chi xuat hien o tap test.
"""
from __future__ import annotations

import pandas as pd

MA_THIEU = "__MISSING__"
MA_LA = -1

# Cot phan loai co the co. Cot nao khong co trong du lieu thi tu dong bo qua.
COT_PHAN_LOAI = (
    "site_id", "campus_name", "location_name", "site_metric", "panel",
    "inverter", "optimizers", "weather_join_method",
    "weather_condition", "weather_description",
)


def cot_phan_loai_co_that(df: pd.DataFrame) -> list[str]:
    return [c for c in COT_PHAN_LOAI if c in df.columns]


def fit_category_maps(train_df: pd.DataFrame) -> dict[str, dict]:
    """Fit bang ma thu tu on dinh, CHI tren du lieu phia train."""
    bang = {}
    for cot in cot_phan_loai_co_that(train_df):
        gia_tri = (
            train_df[cot].astype("string").fillna(MA_THIEU)
            .drop_duplicates().sort_values().tolist()
        )
        anh_xa = {MA_THIEU: 0}
        ma = 1
        for v in gia_tri:
            if v == MA_THIEU:
                continue
            anh_xa[v] = ma
            ma += 1
        bang[cot] = anh_xa
    return bang


def apply_category_maps(df: pd.DataFrame, bang: dict[str, dict]) -> pd.DataFrame:
    """Bien doi cot phan loai bang bang ma da fit tren train."""
    out = df.copy()
    for cot, anh_xa in bang.items():
        if cot not in out.columns:
            continue
        gia_tri = out[cot].astype("string").fillna(MA_THIEU)
        ma = gia_tri.map(anh_xa).fillna(MA_LA).astype("int32")
        out[f"{cot}_enc"] = ma
        # Co nay cho model biet "day la gia tri chua tung thay luc train" - quan trong
        # hon la de no doan mo tren ma -1.
        out[f"{cot}_unknown_flag"] = ma.eq(MA_LA).astype("int8")
    return out


def encode_train_and_other(
    train_df: pd.DataFrame, other_df: pd.DataFrame | None
) -> tuple[pd.DataFrame, pd.DataFrame | None, dict]:
    """Fit tren train_df roi transform ca hai. Dung cho cap (train, val) hoac (dev, test)."""
    bang = fit_category_maps(train_df)
    return (
        apply_category_maps(train_df, bang),
        apply_category_maps(other_df, bang) if other_df is not None else None,
        bang,
    )


def bao_cao_gia_tri_la(df: pd.DataFrame) -> dict:
    """Dem gia tri la o tung cot - ty le cao nghia la train khong bao phu du hang muc."""
    ket = {}
    for cot in df.columns:
        if not cot.endswith("_unknown_flag"):
            continue
        n = int(df[cot].sum())
        if n:
            ket[cot.replace("_unknown_flag", "")] = {
                "so_dong_la": n,
                "ty_le_%": round(n / len(df) * 100, 3),
            }
    return ket
