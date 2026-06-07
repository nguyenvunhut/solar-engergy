"""
upload_staging_data.py - Load dữ liệu CSV vào các bảng staging có sẵn trên Supabase
Cài: pip install pandas sqlalchemy psycopg2-binary python-dotenv
"""

import os
import logging
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Đường dẫn tuyệt đối từ vị trí file upload.py
BASE_DIR = os.path.dirname(os.getcwd())
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

def data(filename):
    """Trả về đường dẫn tuyệt đối đến file CSV trong thư mục data/raw/"""
    return os.path.join(DATA_DIR, filename)

# Kết nối 
SUPABASE_HOST     = os.getenv("DB_HOST")
SUPABASE_PORT     = os.getenv("DB_PORT", "5432")
SUPABASE_DB       = os.getenv("DB_NAME", "postgres")
SUPABASE_USER     = os.getenv("DB_USER")
SUPABASE_PASSWORD = os.getenv("DB_PASSWORD")
SCHEMA            = "staging"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger()


# Map CSV → bảng Supabase 
FILES =[
    # stg_solar_energy_generation 
    {
        "path":       data("Solar_Energy_Generation.csv"),
        "table":      "stg_solar_energy_generation",
        "columns":    ["CampusKey", "SiteKey", "Timestamp", "SolarGeneration"],
        "rename": {
            "CampusKey":       "campuskey",
            "SiteKey":         "sitekey",
            "Timestamp":       "timestamp",
            "SolarGeneration": "solargeneration",
        },
        "batch_size": 10000,
    },

    # stg_solar_site_details 
    {
        "path":    data("Solar_Site_Details.csv"),
        "table":   "stg_solar_site_details",
        "columns": ["CampusKey", "SiteKey", "kWp", "Number of panels",
                    "Panel", "Inverter", "Optimizers", "Metric", "lat", "Lon"],
        "rename": {
            "CampusKey":        "campuskey",
            "SiteKey":          "sitekey",
            "kWp":              "kwp",
            "Number of panels": "number_of_panels",
            "Panel":            "panel",
            "Inverter":         "inverter",
            "Optimizers":       "optimizers",
            "Metric":           "metric",
            "lat":              "lat",
            "Lon":              "lon",
        },
        "batch_size": 1000,
    },

    #  stg_open_meteo_weather 
    {
        "path":    data("open_meteo_weather_raw_2023.csv"),
        "encoding": "utf-8-sig",
        "table":   "stg_open_meteo_weather_raw_2023",
        "columns": [
            "timestamp", "shortwave_radiation", "direct_radiation",
            "diffuse_radiation", "temperature_2m", "weather_code", "is_day",
            "cloud_cover", "cloud_cover_low", "cloud_cover_mid",
            "cloud_cover_high", "wind_speed_10m", "precipitation",
            "sunshine_duration", "SiteKey", "latitude", "longitude",
        ],
        "rename": {
            "SiteKey": "sitekey",
        },
        "batch_size": 5000,
    },

    # stg_campus_meta
    {
        "path":    data("campus_meta.csv"),
        "table":   "stg_campus_meta",
        "columns": ["id","name","capacity"],
        "rename": {
            "id":  "id",
            "name": "name",
            "capacity": "capacity",
        },
        "batch_size": 1000,
    },
     # stg_calendar
    {
        "path":    data("calender.csv"),
        "table":   "stg_calender",
        "columns": ["date","is_holiday","is_semester","is_exam"],
        "rename": {
            "date": "date",
            "is_holiday": "is_holiday",
            "is_semester": "is_semester",
            "is_exam": "is_exam",
        },
        "batch_size": 1000,
    }
    ]


# Kết nối Supabase 
def get_engine():
    url = (
        f"postgresql+psycopg2://{SUPABASE_USER}:{SUPABASE_PASSWORD}"
        f"@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DB}"
        f"?sslmode=require"
    )
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    log.info("Kết nối Supabase thành công\n")
    return engine


# Lấy cột thực tế của bảng trên Supabase 
def get_table_columns(engine, table: str) -> list[str]:
    sql = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = :schema AND table_name = :table
        ORDER BY ordinal_position
    """)
    with engine.connect() as conn:
        result = conn.execute(sql, {"schema": SCHEMA, "table": table})
        return [row[0] for row in result]


# Upload 1 file CSV vào bảng staging tương ứng trên Supabase
def upload_file(cfg: dict, engine) -> bool:
    file_path  = Path(cfg["path"])
    table      = cfg["table"]
    columns    = cfg["columns"]
    rename     = cfg.get("rename", {})
    batch_size = cfg.get("batch_size", 5000)
    encoding   = cfg.get("encoding", "utf-8") 

    if not file_path.exists():
        log.warning(f"Không tìm thấy: {file_path.name}  →  bỏ qua\n")
        return False

    db_cols = get_table_columns(engine, table)
    log.info(f"{file_path.name}  →  {SCHEMA}.{table}")

    try:
        start = time.time()
        total = 0
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {SCHEMA}.{table} RESTART IDENTITY CASCADE;"))
        log.info(f"Đã dọn sạch (TRUNCATE) bảng {SCHEMA}.{table}")

        for chunk in pd.read_csv(
            file_path,
            dtype=str,
            usecols=columns,
            encoding=encoding,
            chunksize=batch_size,
            on_bad_lines="skip",
        ):
            chunk = chunk.rename(columns=rename)

            valid_cols = [c for c in chunk.columns if c in db_cols]
            chunk = chunk[valid_cols]
            chunk.dropna(how="all", inplace=True)

            chunk.to_sql(
                name      = table,
                con       = engine,
                schema    = SCHEMA,
                if_exists = "append",
                index     = False,
                method    = "multi",
            )

            total += len(chunk)
            log.info(f"   ↑ {total:,} dòng...")

        elapsed = time.time() - start
        log.info(f"Xong! {total:,} dòng  —  {elapsed:.1f}s\n")
        return True

    except Exception as e:
        log.error(f"Lỗi: {e}\n")
        return False


# Main 
def main():
    log.info("=" * 55)
    log.info("   SOLAR DATA → SUPABASE STAGING")
    log.info(f"   Data dir: {DATA_DIR}")
    log.info("=" * 55 + "\n")

    engine = get_engine()

    ok = fail = 0
    for cfg in FILES:
        if upload_file(cfg, engine):
            ok += 1
        else:
            fail += 1

    log.info("=" * 55)
    log.info(f"Hoàn thành: {ok} thành công  |  {fail} thất bại")
    engine.dispose()


if __name__ == "__main__":
    main()
