import logging
import os

from dotenv import find_dotenv, load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text

# 1. CẤU HÌNH HỆ THỐNG
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

load_dotenv(find_dotenv())


# 2. CÁC HÀM XỬ LÝ (FUNCTIONS)
def get_engine() -> any:
    """Hàm khởi tạo kết nối tới Supabase bằng SQLAlchemy"""
    SUPABASE_USER = os.getenv("DB_USER", "postgres")
    SUPABASE_PASSWORD = os.getenv("DB_PASSWORD", "your_password")
    SUPABASE_HOST = os.getenv("DB_HOST", "your_host.supabase.co")
    SUPABASE_PORT = os.getenv("DB_PORT", "5432")
    SUPABASE_DB = os.getenv("DB_NAME", "postgres")

    url = (
        f"postgresql+psycopg2://{SUPABASE_USER}:{SUPABASE_PASSWORD}"
        f"@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DB}"
        f"?sslmode=require"
    )

    engine = create_engine(url, pool_pre_ping=True)

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    log.info("Kết nối Supabase thành công!")

    return engine


def run_quality_check(engine: any) -> None:
    """Hàm chạy câu truy vấn kiểm tra Null và Duplicate cho các bảng Dim/Fact trong Staging"""

    sql_query = """
    SELECT
        t.table_name,
        t.row_count,
        COALESCE(d.duplicate_count, 0) AS duplicate_pks,
        t.null_pk_count,
        CASE
            WHEN COALESCE(d.duplicate_count, 0) = 0 AND t.null_pk_count = 0 THEN 'OK'
            ELSE 'CẦN KIỂM TRA'
        END AS status
    FROM (
        SELECT 'dim_date' AS table_name, COUNT(*) AS row_count, COUNT(*) FILTER (WHERE full_date IS NULL) AS null_pk_count FROM staging.dim_date
        UNION ALL
        SELECT 'dim_solar_site', COUNT(*), COUNT(*) FILTER (WHERE sitekey IS NULL) FROM staging.dim_solar_site
        UNION ALL
        SELECT 'dim_geography', COUNT(*), COUNT(*) FILTER (WHERE sitekey IS NULL) FROM staging.dim_geography
        UNION ALL
        SELECT 'dim_time', COUNT(*), COUNT(*) FILTER (WHERE time_string IS NULL) FROM staging.dim_time
        UNION ALL
        SELECT 'dim_weather_type', COUNT(*), COUNT(*) FILTER (WHERE weather_code IS NULL) FROM staging.dim_weather_type
        UNION ALL
        SELECT 'fact_weather', COUNT(*), COUNT(*) FILTER (WHERE sitekey IS NULL OR timestamp IS NULL) FROM staging.fact_weather
    ) t
    LEFT JOIN (
        SELECT 'dim_date' AS table_name, SUM(dup_count) AS duplicate_count 
            FROM (SELECT COUNT(*) AS dup_count FROM staging.dim_date GROUP BY full_date HAVING COUNT(*) > 1) a
        UNION ALL
        SELECT 'dim_solar_site', SUM(dup_count) 
            FROM (SELECT COUNT(*) AS dup_count FROM staging.dim_solar_site GROUP BY sitekey HAVING COUNT(*) > 1) b
        UNION ALL
        SELECT 'dim_geography', SUM(dup_count) 
            FROM (SELECT COUNT(*) AS dup_count FROM staging.dim_geography GROUP BY sitekey HAVING COUNT(*) > 1) c
        UNION ALL
        SELECT 'dim_time', SUM(dup_count) 
            FROM (SELECT COUNT(*) AS dup_count FROM staging.dim_time GROUP BY time_string HAVING COUNT(*) > 1) e
        UNION ALL
        SELECT 'dim_weather_type', SUM(dup_count) 
            FROM (SELECT COUNT(*) AS dup_count FROM staging.dim_weather_type GROUP BY weather_code, is_day HAVING COUNT(*) > 1) f
        UNION ALL
        SELECT 'fact_weather', SUM(dup_count) 
            FROM (SELECT COUNT(*) AS dup_count FROM staging.fact_weather GROUP BY sitekey, timestamp HAVING COUNT(*) > 1) g
    ) d ON t.table_name = d.table_name
    ORDER BY t.table_name;
    """

    log.info("Đang kiểm tra chất lượng dữ liệu trong Staging (Null/Duplicate)...")
    df = pd.read_sql_query(sql_query, engine)

    log.info("\n=== KẾT QUẢ KIỂM TRA CHẤT LƯỢNG DỮ LIỆU ===")
    log.info("\n" + df.to_string(index=False))
    log.info("===========================================\n")


def compare_staging_vs_dw(engine: any) -> None:
    """Hàm đối chiếu số lượng dòng (Row Count) giữa Staging và Data Warehouse"""

    sql_query = """
    SELECT
        stg.table_name,
        stg.staging_rows,
        COALESCE(dw.dw_rows, 0) AS dw_rows,
        (stg.staging_rows - COALESCE(dw.dw_rows, 0)) AS row_diff,
        CASE
            WHEN stg.staging_rows = COALESCE(dw.dw_rows, 0) THEN 'KHỚP'
            ELSE 'LỆCH'
        END AS status
    FROM (
        -- Đếm số dòng trong schema STAGING
        SELECT 'dim_date' AS table_name, COUNT(*) AS staging_rows FROM staging.dim_date UNION ALL
        SELECT 'dim_solar_site', COUNT(*) FROM staging.dim_solar_site UNION ALL
        SELECT 'dim_geography', COUNT(*) FROM staging.dim_geography UNION ALL
        SELECT 'dim_time', COUNT(*) FROM staging.dim_time UNION ALL
        SELECT 'dim_weather_type', COUNT(*) FROM staging.dim_weather_type UNION ALL
        SELECT 'fact_weather', COUNT(*) FROM staging.fact_weather
    ) stg
    LEFT JOIN (
        -- Đếm số dòng trong schema PUBLIC (Data Warehouse)
        SELECT 'dim_date' AS table_name, COUNT(*) AS dw_rows FROM public.dim_date UNION ALL
        SELECT 'dim_solar_site', COUNT(*) FROM public.dim_solar_site UNION ALL
        SELECT 'dim_geography', COUNT(*) FROM public.dim_geography UNION ALL
        SELECT 'dim_time', COUNT(*) FROM public.dim_time UNION ALL
        SELECT 'dim_weather_type', COUNT(*) FROM public.dim_weather_type UNION ALL
        SELECT 'fact_weather', COUNT(*) FROM public.fact_weather
    ) dw ON stg.table_name = dw.table_name
    ORDER BY stg.table_name;
    """

    log.info("Đang đối chiếu số lượng dữ liệu giữa Staging và DW...")
    df = pd.read_sql_query(sql_query, engine)

    log.info("\n=== ĐỐI CHIẾU DỮ LIỆU STAGING vs DATA WAREHOUSE ===")
    log.info("\n" + df.to_string(index=False))
    log.info("=====================================================\n")


# 3. HÀM MAIN (ĐIỀU PHỐI)
def main() -> None:
    STORAGE_BASE_URL = os.getenv("STORAGE_BASE_URL", "Local/Cloud")

    log.info("=" * 55)
    log.info("   SOLAR DATA → SUPABASE STAGING & DW CHECK")
    log.info(f"   Storage: {STORAGE_BASE_URL}")
    log.info("=" * 55 + "\n")

    try:
        # Bước 1: Khởi tạo kết nối DB
        engine = get_engine()

        # Bước 2: Chạy kiểm tra chất lượng dữ liệu Null/Duplicate trong Staging
        run_quality_check(engine)

        # Bước 3: Đối chiếu số lượng records giữa Staging và DW
        compare_staging_vs_dw(engine)

    except Exception as e:
        log.error(f"\nLỗi hệ thống: {e}")


# KÍCH HOẠT CHƯƠNG TRÌNH
if __name__ == "__main__":
    main()
