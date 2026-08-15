"""Dung lai ban kiem toan GMM-IF hoan toan tren may, khong ket noi Supabase.

Vi sao can file nay
-------------------
Bao cao trich mot so con so tu ban kiem toan GMM-IF cua tang ETL (`03_gmm_if_full_audit.csv`):
so ung vien cua GMM, so ung vien cua Isolation Forest, so dong qua duoc phep giao, va diem
co lap trung binh cua hai nhom. Nhung tep do nam trong `reports/final_rolling_compare/`, la
thu muc ket qua cuc bo khong duoc theo doi bang git, nen nguoi doc bao cao khong tai lap
duoc con so.

Duong chay goc `02_gmm_if.py` doc ba tep dem do `01_export_parquet.py` KET XUAT TU DATABASE.
Chay lai duong do doi hoi ket noi Supabase. Script nay thay buoc do bang mot buoc doc tep
Parquet co san tren may: `data/mlmart_base/v4_preprocessing.parquet` - chinh la ban ket xuat
cua ML Mart v4, da chua du san luong, khi tuong va sieu du lieu tram.

Nguyen tac
----------
- CHI doc/ghi tren o dia cuc bo. Khong mo ket noi database, khong goi Supabase Storage,
  khong upload gi.
- KHONG viet lai thuat toan. Script dung lai `02_gmm_if.py` nguyen ban qua importlib, chi
  cung cap dau vao cho no. Nho vay con so sinh ra dung bang thuat toan ma tang ETL da dung.
- Khong sua tep nguon nao khac.

Cach chay
---------
    python srcs/02_transform/02_generate_outliers/07_local_gmm_if_audit.py

Ket qua
-------
    reports/final_rolling_compare/03_gmm_if_full_audit.csv   (ban kiem toan day du)
    reports/final_rolling_compare/07_local_gmm_if_summary.json (bon con so bao cao trich)
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
NGUON = ROOT / "data" / "mlmart_base" / "v4_preprocessing.parquet"
THU_MUC_DEM = ROOT / "data" / "processed" / "temp_staging_buffers"
THU_MUC_RA = ROOT / "reports" / "final_rolling_compare"
GMM_IF_PY = Path(__file__).with_name("02_gmm_if.py")

# Ba tep dem ma 02_gmm_if.py doc, kem dung danh sach cot no yeu cau.
COT_SOLAR = ["sitekey", "timestamp", "energy_generated_kwh"]
COT_WEATHER = [
    "sitekey",
    "timestamp",
    "is_day",
    "shortwave_radiation",
    "diffuse_solar_radiation",
    "direct_normal_irradiance",
    "cloud_cover_total",
    "precipitation_mm",
    "sunshine_duration",
]
COT_SITE = ["sitekey", "capacity_kw", "number_of_panels", "panel", "inverter"]


def dung_ba_tep_dem() -> None:
    """Tach `v4_preprocessing.parquet` thanh ba tep dem ma `02_gmm_if.py` mong doi."""
    if not NGUON.exists():
        raise FileNotFoundError(
            f"Khong thay tep nguon cuc bo: {NGUON}\n"
            "Tep nay do buoc ket xuat ML Mart v4 sinh ra. Keo ve bang `dvc pull` truoc."
        )

    print(f"Doc nguon cuc bo : {NGUON}")
    df = pd.read_parquet(NGUON)
    print(f"  {len(df):,} dong x {df.shape[1]} cot")

    df = df.rename(columns={"site_id": "sitekey", "weather_is_day": "is_day"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    THU_MUC_DEM.mkdir(parents=True, exist_ok=True)

    solar = df[COT_SOLAR].copy()
    solar.to_parquet(THU_MUC_DEM / "temp_fact_solar_energy_gen.parquet", index=False)
    print(f"  -> temp_fact_solar_energy_gen.parquet ({len(solar):,} dong)")

    # Khi tuong ghi theo gio, ML Mart da ghep san sang tung buoc 15 phut. Bo trung lap de
    # tep dem giu dung mot dong cho moi (tram, moc) giong bang fact_weather goc.
    weather = df[COT_WEATHER].drop_duplicates(subset=["sitekey", "timestamp"]).copy()
    weather.to_parquet(THU_MUC_DEM / "temp_fact_weather.parquet", index=False)
    print(f"  -> temp_fact_weather.parquet ({len(weather):,} dong)")

    site = (
        df[COT_SITE]
        .drop_duplicates(subset=["sitekey"])
        .sort_values("sitekey")
        .reset_index(drop=True)
    )
    site.to_parquet(THU_MUC_DEM / "temp_dim_solar_site.parquet", index=False)
    print(f"  -> temp_dim_solar_site.parquet ({len(site):,} tram)")


def nap_module_gmm_if():
    """Nap `02_gmm_if.py` bang importlib vi ten tep bat dau bang so."""
    spec = importlib.util.spec_from_file_location("gmm_if_goc", GMM_IF_PY)
    module = importlib.util.module_from_spec(spec)
    sys.modules["gmm_if_goc"] = module
    spec.loader.exec_module(module)
    return module


def tom_tat_ban_kiem_toan() -> dict:
    """Doc lai ban kiem toan vua sinh va tinh dung bon con so bao cao trich."""
    duong_dan = THU_MUC_RA / "03_gmm_if_full_audit.csv"
    if not duong_dan.exists():
        raise FileNotFoundError(f"Khong thay ban kiem toan sau khi chay: {duong_dan}")

    audit = pd.read_csv(duong_dan)
    gmm = audit["gmm_flag"].astype(bool)
    iso = audit["if_flag"].astype(bool)
    dong_thuan = audit["gmm_if_consensus_flag"].astype(bool)
    la_ngoai_lai = audit["is_outlier"].astype(bool)
    diem = pd.to_numeric(audit["if_anomaly_score"], errors="coerce")

    tom_tat = {
        "tep_nguon_cuc_bo": str(NGUON.relative_to(ROOT)),
        "tong_so_dong": int(len(audit)),
        "ung_vien_gmm": int(gmm.sum()),
        "ung_vien_isolation_forest": int(iso.sum()),
        "qua_duoc_phep_giao": int(dong_thuan.sum()),
        "ty_le_song_sot_gmm_pct": round(float(dong_thuan.sum()) / max(int(gmm.sum()), 1) * 100, 2),
        "ty_le_song_sot_if_pct": round(float(dong_thuan.sum()) / max(int(iso.sum()), 1) * 100, 2),
        "diem_co_lap_tb_dong_bi_gan_co": round(float(diem[la_ngoai_lai].mean()), 4),
        "diem_co_lap_tb_dong_binh_thuong": round(float(diem[~la_ngoai_lai].mean()), 4),
        "so_dong_bi_gan_co_cuoi_cung": int(la_ngoai_lai.sum()),
    }
    tom_tat["chenh_diem_co_lap"] = round(
        tom_tat["diem_co_lap_tb_dong_bi_gan_co"]
        - tom_tat["diem_co_lap_tb_dong_binh_thuong"],
        4,
    )
    return tom_tat


def main() -> None:
    print("=" * 78)
    print("KIEM CHUNG GMM-IF TREN MAY - KHONG KET NOI SUPABASE / CLOUD")
    print("=" * 78)

    dung_ba_tep_dem()

    print("\nChay lai `02_gmm_if.py` nguyen ban tren ba tep dem vua dung...")
    module = nap_module_gmm_if()
    module.main()

    tom_tat = tom_tat_ban_kiem_toan()

    THU_MUC_RA.mkdir(parents=True, exist_ok=True)
    duong_dan_tom_tat = THU_MUC_RA / "07_local_gmm_if_summary.json"
    with duong_dan_tom_tat.open("w", encoding="utf-8") as f:
        json.dump(tom_tat, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 78)
    print("BON CON SO BAO CAO TRICH")
    print("=" * 78)
    print(f"Ung vien GMM                      : {tom_tat['ung_vien_gmm']:,}")
    print(f"Ung vien Isolation Forest         : {tom_tat['ung_vien_isolation_forest']:,}")
    print(f"Qua duoc phep giao (ca hai dong y) : {tom_tat['qua_duoc_phep_giao']:,}")
    print(f"  ty le song sot cua GMM          : {tom_tat['ty_le_song_sot_gmm_pct']}%")
    print(f"  ty le song sot cua IF           : {tom_tat['ty_le_song_sot_if_pct']}%")
    print(f"Diem co lap TB - dong bi gan co   : {tom_tat['diem_co_lap_tb_dong_bi_gan_co']}")
    print(f"Diem co lap TB - dong binh thuong : {tom_tat['diem_co_lap_tb_dong_binh_thuong']}")
    print(f"  chenh                           : {tom_tat['chenh_diem_co_lap']}")
    print(f"\nDa ghi: {duong_dan_tom_tat}")


if __name__ == "__main__":
    main()
