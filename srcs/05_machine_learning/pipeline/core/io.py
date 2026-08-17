"""Doc/ghi parquet + json. Gop tu utils.py va cac ham doc_du_lieu()/doc_fold()
lap lai o 02_1, 02_2, 02_3, 04_1, 04_2, 04_3 (moi file mot ban gan giong nhau).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from .columns import SITE_COL, TARGET_COL, TIMESTAMP_COL, require_columns


def read_parquet(
    path: str | Path,
    columns: list[str] | None = None,
    sap_xep: tuple[str, ...] | None = (SITE_COL, TIMESTAMP_COL),
) -> pd.DataFrame:
    """Doc parquet, kiem cot bat buoc, ep kieu timestamp va sap xep.

    Mac dinh sap theo (site, time): moi phep shift()/rolling() sau do deu gia dinh du
    lieu da sap theo thoi gian trong TUNG site. Doc xong khong sap la sai ket qua ngam.

    Dat sap_xep khac neu stage do can thu tu khac. Vi du stage s02 phai sap theo
    (timestamp, site) de khop dung thu tu dong ma notebook 02 ghi ra - thu tu dong tren
    dia anh huong den .sample(random_state=...) o cac buoc sau, nen khong duoc tuy tien.
    Dat None de giu nguyen thu tu goc cua file.
    """
    df = pd.read_parquet(path, columns=columns)
    require_columns(df, [TIMESTAMP_COL, SITE_COL, TARGET_COL])
    df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL], errors="coerce")
    if sap_xep is None:
        return df.reset_index(drop=True)
    return df.sort_values(list(sap_xep)).reset_index(drop=True)


def read_parquet_loc_cot(path: str | Path, cot_muon: list[str]) -> pd.DataFrame:
    """Chi doc cac cot co THAT trong file - tranh loi khi schema thay doi giua cac lan chay."""
    co_san = set(pq.ParquetFile(str(path)).schema_arrow.names)
    lay = [c for c in dict.fromkeys(cot_muon) if c in co_san]
    return read_parquet(path, columns=lay)


def cot_co_san(path: str | Path) -> set[str]:
    """Doc schema thoi, khong nap du lieu - dung de kiem tra truoc khi chay."""
    return set(pq.ParquetFile(str(path)).schema_arrow.names)


def write_parquet(df: pd.DataFrame, path: str | Path) -> Path:
    """Ghi parquet, tu tao thu muc cha neu chua co."""
    duong_dan = Path(path)
    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(duong_dan, index=False)
    return duong_dan


def _json_an_toan(o):
    """Ep kieu numpy ve kieu Python de json.dump khong bao loi.

    np.float32/int64 khong phai kieu JSON hop le - truoc day phai .item() thu cong
    o tung cho, sot 1 cho la vo ca file ket qua.
    """
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, (pd.Timestamp,)):
        return o.isoformat()
    raise TypeError(f"Khong biet cach chuyen {type(o)} sang JSON")


def write_json(du_lieu, path: str | Path) -> Path:
    duong_dan = Path(path)
    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    with open(duong_dan, "w", encoding="utf-8") as f:
        json.dump(du_lieu, f, ensure_ascii=False, indent=2, default=_json_an_toan)
    return duong_dan


def read_json(path: str | Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_csv(df: pd.DataFrame, path: str | Path) -> Path:
    duong_dan = Path(path)
    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(duong_dan, index=False)
    return duong_dan
