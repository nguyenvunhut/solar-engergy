import os
import logging
import ssl
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# 1. CẤU HÌNH HỆ THỐNG

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger()

SUPABASE_HOST = os.getenv("DB_HOST")
SUPABASE_PORT = os.getenv("DB_PORT", "5432")
SUPABASE_DB = os.getenv("DB_NAME", "postgres")
SUPABASE_USER = os.getenv("DB_USER")
SUPABASE_PASSWORD = os.getenv("DB_PASSWORD")

def get_engine() -> any:
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


# 2. HÀM KHỞI TẠO BI MART (BÁO CÁO TABLEAU)

def build_bi_mart(engine):
    sql_script = """
    CREATE SCHEMA IF NOT EXISTS bi_mart;

    -- Dọn dẹp cấu trúc cũ
    DROP VIEW IF EXISTS bi_mart.vw_dim_solar_site CASCADE;
    DROP VIEW IF EXISTS bi_mart.vw_dim_geography CASCADE;
    DROP VIEW IF EXISTS bi_mart.vw_dim_date CASCADE;
    DROP VIEW IF EXISTS bi_mart.vw_dim_weather_type CASCADE;

    DROP TABLE IF EXISTS bi_mart.fact_solar_performance_hourly CASCADE;
    DROP TABLE IF EXISTS bi_mart.dim_solar_site CASCADE;
    DROP TABLE IF EXISTS bi_mart.dim_geography CASCADE;
    DROP TABLE IF EXISTS bi_mart.dim_date CASCADE;
    DROP TABLE IF EXISTS bi_mart.dim_weather_type CASCADE;
    DROP TABLE IF EXISTS bi_mart.obt_solar_performance_hourly CASCADE;

    -- Tạo Dimension vật lý & Khóa chính
    CREATE TABLE bi_mart.dim_solar_site AS SELECT * FROM public.dim_solar_site;
    ALTER TABLE bi_mart.dim_solar_site ADD PRIMARY KEY (site_id);

    CREATE TABLE bi_mart.dim_geography AS SELECT * FROM public.dim_geography;
    ALTER TABLE bi_mart.dim_geography ADD PRIMARY KEY (geo_id);

    CREATE TABLE bi_mart.dim_date AS SELECT * FROM public.dim_date;
    ALTER TABLE bi_mart.dim_date ADD PRIMARY KEY (date_id);

    CREATE TABLE bi_mart.dim_weather_type AS SELECT * FROM public.dim_weather_type;
    ALTER TABLE bi_mart.dim_weather_type ADD PRIMARY KEY (weather_type_id);

    -- Tạo Bảng FACT (Kết hợp Sản lượng 15p sạch + Thời tiết 1h)
    CREATE TABLE bi_mart.fact_solar_performance_hourly AS
    WITH Clean_Hourly_Gen AS (
        SELECT 
            f.site_id, f.geo_id, f.date_id, t.hour AS hourly_bucket,
            SUM(f.energy_generated_kwh) AS total_energy
        FROM public.fact_solar_energy_gen f
        JOIN public.dim_time t ON f.time_id = t.time_id
        JOIN public.dim_date d ON f.date_id = d.date_id
        
        -- Nối xuyên môi trường (ép kiểu varchar -> int, bóc tách timestamp)
        LEFT JOIN staging.fact_solar_energy_gen_rolling_outlier_flags o
            ON f.site_id = o.sitekey::INT 
           AND d.full_date = o.timestamp::date 
           AND t.hour = EXTRACT(HOUR FROM o.timestamp)
           AND t.minute = EXTRACT(MINUTE FROM o.timestamp)

        WHERE COALESCE(o.rolling_outlier_flag, false) = false
        GROUP BY f.site_id, f.geo_id, f.date_id, t.hour
    )
    SELECT 
        gen.site_id, gen.geo_id, gen.date_id, gen.hourly_bucket, gen.total_energy,
        w.shortwave_radiation, w.temperature_c, w.cloud_cover_total, w.precipitation_mm
    FROM Clean_Hourly_Gen gen
    LEFT JOIN (
        SELECT fw.*, dw.hour as weather_hour 
        FROM public.fact_weather fw
        JOIN public.dim_time dw ON fw.time_id = dw.time_id
    ) w 
    ON gen.geo_id = w.geo_id AND gen.date_id = w.date_id AND gen.hourly_bucket = w.weather_hour;

    -- Bổ sung Khóa ngoại thời tiết và vẽ sơ đồ liên kết (ERD)
    ALTER TABLE bi_mart.fact_solar_performance_hourly ADD COLUMN weather_type_id int4;
    
    UPDATE bi_mart.fact_solar_performance_hourly fct
    SET weather_type_id = w.weather_type_id
    FROM public.fact_weather w
    JOIN public.dim_time dw ON w.time_id = dw.time_id
    WHERE fct.geo_id = w.geo_id AND fct.date_id = w.date_id AND fct.hourly_bucket = dw.hour;

    ALTER TABLE bi_mart.fact_solar_performance_hourly ADD CONSTRAINT fk_bi_fact_site FOREIGN KEY (site_id) REFERENCES bi_mart.dim_solar_site(site_id);
    ALTER TABLE bi_mart.fact_solar_performance_hourly ADD CONSTRAINT fk_bi_fact_geo FOREIGN KEY (geo_id) REFERENCES bi_mart.dim_geography(geo_id);
    ALTER TABLE bi_mart.fact_solar_performance_hourly ADD CONSTRAINT fk_bi_fact_date FOREIGN KEY (date_id) REFERENCES bi_mart.dim_date(date_id);
    ALTER TABLE bi_mart.fact_solar_performance_hourly ADD CONSTRAINT fk_bi_fact_weather FOREIGN KEY (weather_type_id) REFERENCES bi_mart.dim_weather_type(weather_type_id);

    -- Đánh Composite Index tối ưu truy vấn
    CREATE INDEX idx_fact_fk_site_date ON bi_mart.fact_solar_performance_hourly (site_id, date_id);
    CREATE INDEX idx_fact_fk_geo_date ON bi_mart.fact_solar_performance_hourly (geo_id, date_id);
    """
    log.info(">> Bắt đầu build BI Mart (Star Schema & Fact Table)...")
    with engine.begin() as conn:
        for statement in [s.strip() for s in sql_script.split(';') if s.strip()]:
            conn.execute(text(statement))
    log.info(">> BI Mart hoàn tất!\n")


# 3. HÀM KHỞI TẠO ML MART (MACHINE LEARNING)

def build_ml_mart(engine):
    sql_script = """
    CREATE SCHEMA IF NOT EXISTS ml_mart;
    DROP TABLE IF EXISTS ml_mart.base CASCADE;

    CREATE TABLE ml_mart.base AS
    SELECT 
        f.energy_generated_kwh,
        t.hour, d.day, d.month, d.year,
        w.shortwave_radiation, w.temperature_c, w.cloud_cover_total, w.precipitation_mm,
        COALESCE(o.rolling_outlier_flag, false) AS is_outlier
    FROM public.fact_solar_energy_gen f
    JOIN public.dim_time t ON f.time_id = t.time_id
    JOIN public.dim_date d ON f.date_id = d.date_id

    -- Nối Cờ Outlier
    LEFT JOIN staging.fact_solar_energy_gen_rolling_outlier_flags o
        ON f.site_id = o.sitekey::INT 
       AND d.full_date = o.timestamp::date
       AND t.hour = EXTRACT(HOUR FROM o.timestamp)
       AND t.minute = EXTRACT(MINUTE FROM o.timestamp)

    -- Nối Thời tiết
    LEFT JOIN (
        SELECT fw.*, dw.hour as weather_hour 
        FROM public.fact_weather fw
        JOIN public.dim_time dw ON fw.time_id = dw.time_id
    ) w 
    ON f.geo_id = w.geo_id AND f.date_id = w.date_id AND t.hour = w.weather_hour;
    """
    log.info(">> Bắt đầu build ML Mart (Flat Feature Table)...")
    with engine.begin() as conn:
        for statement in [s.strip() for s in sql_script.split(';') if s.strip()]:
            conn.execute(text(statement))
    log.info(">> ML Mart hoàn tất!\n")


# 4. CHẠY PIPELINE TỔNG

if __name__ == "__main__":
    log.info("==== KHỞI ĐỘNG DATA PIPELINE TẠO MART ====\n")
    try:
        db_engine = get_engine()
        
        # Chạy tuần tự 2 luồng
        build_bi_mart(db_engine)
        build_ml_mart(db_engine)
        
        log.info("==== PIPELINE THÀNH CÔNG  ====")
        
    except Exception as error:
        log.error(f"PIPELINE THẤT BẠI: {error}")