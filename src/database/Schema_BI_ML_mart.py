import os
import logging
import ssl
import argparse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

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

def build_bi_mart(engine):
    sql_script = """
    CREATE SCHEMA IF NOT EXISTS bi_mart;

    DROP TABLE IF EXISTS bi_mart.dim_solar_site CASCADE;
    DROP TABLE IF EXISTS bi_mart.dim_geography CASCADE;
    DROP TABLE IF EXISTS bi_mart.dim_date CASCADE;
    DROP TABLE IF EXISTS bi_mart.dim_weather_type CASCADE;

    DROP VIEW IF EXISTS bi_mart.dim_solar_site CASCADE;
    DROP VIEW IF EXISTS bi_mart.dim_geography CASCADE;
    DROP VIEW IF EXISTS bi_mart.dim_date CASCADE;
    DROP VIEW IF EXISTS bi_mart.dim_weather_type CASCADE;

    DROP TABLE IF EXISTS bi_mart.fact_solar_performance_hourly CASCADE;

    CREATE OR REPLACE VIEW bi_mart.dim_solar_site AS SELECT * FROM public.dim_solar_site;
    CREATE OR REPLACE VIEW bi_mart.dim_geography AS SELECT * FROM public.dim_geography;
    CREATE OR REPLACE VIEW bi_mart.dim_date AS SELECT * FROM public.dim_date;
    CREATE OR REPLACE VIEW bi_mart.dim_weather_type AS SELECT * FROM public.dim_weather_type;

    CREATE TABLE bi_mart.fact_solar_performance_hourly AS
    WITH Clean_Hourly_Gen AS (
        SELECT 
            f.site_id, f.geo_id, f.date_id, t.hour AS hourly_bucket,
            SUM(f.energy_generated_kwh) AS total_energy
        FROM public.fact_solar_energy_gen f
        JOIN public.dim_time t ON f.time_id = t.time_id
        WHERE COALESCE(f.rolling_outlier_flag, false) = false
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

    ALTER TABLE bi_mart.fact_solar_performance_hourly ADD COLUMN weather_type_id int4;
    
    UPDATE bi_mart.fact_solar_performance_hourly fct
    SET weather_type_id = w.weather_type_id
    FROM public.fact_weather w
    JOIN public.dim_time dw ON w.time_id = dw.time_id
    WHERE fct.geo_id = w.geo_id AND fct.date_id = w.date_id AND fct.hourly_bucket = dw.hour;

    ALTER TABLE bi_mart.fact_solar_performance_hourly ADD CONSTRAINT fk_bi_fact_site FOREIGN KEY (site_id) REFERENCES public.dim_solar_site(site_id);
    ALTER TABLE bi_mart.fact_solar_performance_hourly ADD CONSTRAINT fk_bi_fact_geo FOREIGN KEY (geo_id) REFERENCES public.dim_geography(geo_id);
    ALTER TABLE bi_mart.fact_solar_performance_hourly ADD CONSTRAINT fk_bi_fact_date FOREIGN KEY (date_id) REFERENCES public.dim_date(date_id);
    ALTER TABLE bi_mart.fact_solar_performance_hourly ADD CONSTRAINT fk_bi_fact_weather FOREIGN KEY (weather_type_id) REFERENCES public.dim_weather_type(weather_type_id);

    CREATE INDEX idx_fact_fk_site_date ON bi_mart.fact_solar_performance_hourly (site_id, date_id);
    CREATE INDEX idx_fact_fk_geo_date ON bi_mart.fact_solar_performance_hourly (geo_id, date_id);
    """
    log.info(">> Bắt đầu build BI Mart...")
    with engine.begin() as conn:
        for statement in [s.strip() for s in sql_script.split(';') if s.strip()]:
            conn.execute(text(statement))
    log.info(">> BI Mart hoàn tất!\n")

def build_ml_mart(engine):
    sql_script = """
    CREATE SCHEMA IF NOT EXISTS ml_mart;
    DROP TABLE IF EXISTS ml_mart.base CASCADE;

    CREATE TABLE ml_mart.base AS
    SELECT 
        f.energy_generated_kwh,
        t.hour, d.day, d.month, d.year,
        w.shortwave_radiation, w.temperature_c, w.cloud_cover_total, w.precipitation_mm,
        COALESCE(f.rolling_outlier_flag, false) AS is_outlier
    FROM public.fact_solar_energy_gen f
    JOIN public.dim_time t ON f.time_id = t.time_id
    JOIN public.dim_date d ON f.date_id = d.date_id
    LEFT JOIN (
        SELECT fw.*, dw.hour as weather_hour 
        FROM public.fact_weather fw
        JOIN public.dim_time dw ON fw.time_id = dw.time_id
    ) w 
    ON f.geo_id = w.geo_id AND f.date_id = w.date_id AND t.hour = w.weather_hour;
    """
    log.info(">> Bắt đầu build ML Mart...")
    with engine.begin() as conn:
        for statement in [s.strip() for s in sql_script.split(';') if s.strip()]:
            conn.execute(text(statement))
    log.info(">> ML Mart hoàn tất!\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Marts Builder")
    parser.add_argument('--target', type=str, choices=['all', 'bi', 'ml'], default='bi')
    args = parser.parse_args()

    log.info(f"==== KHỞI ĐỘNG PIPELINE ({args.target.upper()}) ====\n")
    try:
        db_engine = get_engine()
        
        if args.target in ['all', 'bi']:
            build_bi_mart(db_engine)
            
        if args.target in ['all', 'ml']:
            build_ml_mart(db_engine)
            
        log.info("==== PIPELINE THÀNH CÔNG ====")
        
    except Exception as error:
        log.error(f"PIPELINE THẤT BẠI: {error}")