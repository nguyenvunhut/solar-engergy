"""Tang REPOSITORY - cua DUY NHAT cham vao du lieu BI Mart.

Doi tu parquet sang doc thang Supabase (hay nguoc lai) thi CHI sua file nay,
tang service khong biet gi.

NGUON
  bi_mart.mv_bi_mart_hourly_measures   683.665 dong x 36 cot · 42 tram
  bi_mart.mv_bi_mart_daily_kpis         28.677 dong x 35 cot · 42 tram
  Khoang thoi gian: 2020-01-01 -> 2022-04-23

Doc tu parquet cuc bo. Thieu tep thi bao loi kem lenh trich xuat lai.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[5]
THU_MUC = _REPO_ROOT / "data" / "bimart_base"
TEP_HOURLY = THU_MUC / "mv_bi_mart_hourly_measures.parquet"
TEP_DAILY = THU_MUC / "mv_bi_mart_daily_kpis.parquet"

_LENH_KEO = (
    "python srcs/00_utils/03_convert_query_to_parquet.py "
    '--query "SELECT * FROM bi_mart.{ten}" '
    "--output data/bimart_base/{ten}.parquet --overwrite --chunk-size 1000000"
)


def _doc(tep: Path, ten_mv: str) -> pd.DataFrame:
    if not tep.exists():
        raise FileNotFoundError(
            f"Khong thay {tep}. Keo ve bang:\n    {_LENH_KEO.format(ten=ten_mv)}"
        )
    return pd.read_parquet(tep)


@lru_cache(maxsize=1)
def doc_hourly() -> pd.DataFrame:
    """Bang cap GIO. Cache nen chi doc dia mot lan moi tien trinh."""
    return _doc(TEP_HOURLY, "mv_bi_mart_hourly_measures")


@lru_cache(maxsize=1)
def doc_daily() -> pd.DataFrame:
    """Bang cap NGAY."""
    return _doc(TEP_DAILY, "mv_bi_mart_daily_kpis")


def nam_tu_date_id(s: pd.Series) -> pd.Series:
    """date_id dang 20200101 -> nam 2020. Dung de tra bieu gia theo nam."""
    return (s // 10000).astype("Int64")


def tom_tat_pham_vi() -> dict:
    """Thong tin pham vi cua bo du lieu, dung cho phan chu thich nguon."""
    h = doc_hourly()
    return {
        "so_dong": int(len(h)),
        "so_tram": int(h["site_id"].nunique()),
        "date_id_min": int(h["date_id"].min()),
        "date_id_max": int(h["date_id"].max()),
    }
