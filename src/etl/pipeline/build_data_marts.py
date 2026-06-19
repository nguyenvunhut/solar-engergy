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
    log.info(">> Bắt đầu build ML Mart...")

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS ml_mart"))

        duplicate_weather_keys = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT fw.geo_id, fw.date_id, dt.hour
                    FROM datawarehouse.fact_weather fw
                    JOIN datawarehouse.dim_time dt
                      ON dt.time_id = fw.time_id
                    GROUP BY fw.geo_id, fw.date_id, dt.hour
                    HAVING COUNT(*) > 1
                ) duplicated
                """
            )
        ).scalar_one()
        if duplicate_weather_keys:
            raise RuntimeError(
                "Không thể build ML Mart: fact_weather bị trùng "
                f"{duplicate_weather_keys} khóa (geo_id, date_id, hour)"
            )

        conn.execute(text("DROP TABLE IF EXISTS ml_mart.base_build"))
        conn.execute(
            text(
                """
                CREATE TABLE ml_mart.base_build AS
                SELECT
                    -- Audit keys: giữ trong mart để truy vết, không đưa thẳng vào X.
                    f.gen_id,
                    f.site_id,
                    f.geo_id,
                    f.date_id,
                    f.time_id,
                    d.full_date + make_time(t.hour, t.minute, 0) AS timestamp,

                    -- Calendar context.
                    d.full_date,
                    d.year,
                    d.month,
                    d.day,
                    EXTRACT(DOW FROM d.full_date)::smallint AS day_of_week,
                    t.hour,
                    t.minute,

                    -- Endogenous target source.
                    f.energy_generated_kwh,
                    COALESCE(f.rolling_outlier_flag, false)
                        AS rolling_outlier_flag,

                    -- Static site and geography context.
                    s.campus_name,
                    s.capacity_kw,
                    s.number_of_panels,
                    s.panel,
                    s.inverter,
                    s.optimizers,
                    s.metric AS site_metric,
                    geo.location_name,
                    geo.latitude,
                    geo.longitude,

                    -- Weather audit keys and observation time.
                    w.weather_id,
                    w.weather_type_id,
                    d.full_date
                        + make_time(w.weather_hour, w.weather_minute, 0)
                        AS weather_timestamp,

                    -- Raw exogenous weather variables.
                    w.is_day AS weather_is_day,
                    w.shortwave_radiation,
                    w.direct_normal_irradiance,
                    w.diffuse_solar_radiation,
                    w.temperature_c,
                    w.cloud_cover_total,
                    w.cloud_cover_low,
                    w.cloud_cover_mid,
                    w.cloud_cover_high,
                    w.wind_speed,
                    w.precipitation_mm,
                    w.sunshine_duration,

                    -- Human-readable weather context.
                    wt.weather_code,
                    wt.is_day AS weather_type_is_day,
                    wt.weather_condition,
                    wt.description AS weather_description
                FROM datawarehouse.fact_solar_energy_gen f
                JOIN datawarehouse.dim_time t
                  ON t.time_id = f.time_id
                JOIN datawarehouse.dim_date d
                  ON d.date_id = f.date_id
                LEFT JOIN datawarehouse.dim_solar_site s
                  ON s.site_id = f.site_id
                LEFT JOIN datawarehouse.dim_geography geo
                  ON geo.geo_id = f.geo_id
                LEFT JOIN (
                    SELECT
                        fw.*,
                        weather_time.hour AS weather_hour,
                        weather_time.minute AS weather_minute
                    FROM datawarehouse.fact_weather fw
                    JOIN datawarehouse.dim_time weather_time
                      ON weather_time.time_id = fw.time_id
                ) w
                  ON w.geo_id = f.geo_id
                 AND w.date_id = f.date_id
                 AND w.weather_hour = t.hour
                LEFT JOIN datawarehouse.dim_weather_type wt
                  ON wt.weather_type_id = w.weather_type_id
                """
            )
        )

        source_rows = conn.execute(
            text("SELECT COUNT(*) FROM datawarehouse.fact_solar_energy_gen")
        ).scalar_one()
        mart_rows = conn.execute(
            text("SELECT COUNT(*) FROM ml_mart.base_build")
        ).scalar_one()
        duplicate_gen_ids = conn.execute(
            text(
                """
                SELECT COUNT(*) - COUNT(DISTINCT gen_id)
                FROM ml_mart.base_build
                """
            )
        ).scalar_one()
        duplicate_site_timestamps = conn.execute(
            text(
                """
                SELECT COUNT(*) - COUNT(DISTINCT (site_id, timestamp))
                FROM ml_mart.base_build
                """
            )
        ).scalar_one()

        if mart_rows != source_rows:
            raise RuntimeError(
                "ML Mart sai row count: "
                f"source={source_rows:,}, mart={mart_rows:,}"
            )
        if duplicate_gen_ids:
            raise RuntimeError(
                f"ML Mart có {duplicate_gen_ids:,} gen_id bị trùng"
            )
        if duplicate_site_timestamps:
            raise RuntimeError(
                "ML Mart có "
                f"{duplicate_site_timestamps:,} khóa (site_id, timestamp) bị trùng"
            )

        conn.execute(text("DROP TABLE IF EXISTS ml_mart.base CASCADE"))
        conn.execute(
            text("ALTER TABLE ml_mart.base_build RENAME TO base")
        )
        conn.execute(
            text(
                """
                ALTER TABLE ml_mart.base
                ADD CONSTRAINT pk_ml_mart_base PRIMARY KEY (gen_id)
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX ux_ml_base_site_timestamp
                ON ml_mart.base (site_id, timestamp)
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX ix_ml_base_timestamp
                ON ml_mart.base (timestamp)
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX ix_ml_base_geo_timestamp
                ON ml_mart.base (geo_id, timestamp)
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE OR REPLACE VIEW ml_mart.v_model_input_1h AS
                WITH target_windows AS (
                    SELECT
                        b.*,
                        LEAD(timestamp, 4) OVER (
                            PARTITION BY site_id
                            ORDER BY timestamp
                        ) AS target_end_timestamp,
                        COUNT(energy_generated_kwh) OVER (
                            PARTITION BY site_id
                            ORDER BY timestamp
                            ROWS BETWEEN 1 FOLLOWING AND 4 FOLLOWING
                        ) AS target_window_rows,
                        SUM(energy_generated_kwh) OVER (
                            PARTITION BY site_id
                            ORDER BY timestamp
                            ROWS BETWEEN 1 FOLLOWING AND 4 FOLLOWING
                        ) AS target_energy_next_1h_kwh
                    FROM ml_mart.base b
                )
                SELECT
                    *,
                    SIN(2 * pi() * hour / 24.0) AS hour_sin,
                    COS(2 * pi() * hour / 24.0) AS hour_cos,
                    SIN(2 * pi() * month / 12.0) AS month_sin,
                    COS(2 * pi() * month / 12.0) AS month_cos
                FROM target_windows
                WHERE target_window_rows = 4
                  AND target_end_timestamp = timestamp + interval '1 hour'
                """
            )
        )

        missing_weather_rows = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM ml_mart.base
                WHERE weather_id IS NULL
                """
            )
        ).scalar_one()

        log.info(
            ">> ML Mart audit: rows=%s, duplicate_gen_id=0, "
            "duplicate_site_timestamp=0, missing_weather=%s",
            f"{mart_rows:,}",
            f"{missing_weather_rows:,}",
        )

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
