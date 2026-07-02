import os
import psycopg2
from dotenv import load_dotenv
import logging
from pathlib import Path
import yaml

log = logging.getLogger("pipeline.bi_mart")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BI_PARAMS_CONFIG = _REPO_ROOT / "config" / "04_machine_learning" / "01_bi_mart_params.yaml"

with _BI_PARAMS_CONFIG.open(encoding="utf-8") as _f:
    _bi_cfg = yaml.safe_load(_f)

_FIT_RATE       = _bi_cfg["financial"]["fit_rate_vnd_per_kwh"]
_CO2_FACTOR     = _bi_cfg["environmental"]["co2_emission_factor_kg_per_kwh"]
_TREES_FACTOR   = _bi_cfg["environmental"]["co2_per_tree_kg"]
_NOMINAL_PR     = _bi_cfg["performance"]["nominal_pr"]
_TEMP_COEFF     = _bi_cfg["performance"]["temp_coefficient_per_deg"]
_NOCT_FACTOR    = _bi_cfg["performance"]["noct_radiation_factor"]
_MIN_RADIATION  = _bi_cfg["performance"]["min_radiation_threshold_wm2"]
_SOURCE_SCHEMA  = _bi_cfg["database"]["source_schema"]
_TARGET_SCHEMA  = _bi_cfg["database"]["target_schema"]

load_dotenv()


def get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        sslmode="require"
    )


def setup_materialized_views():
    print("[Hệ thống] Đang khởi tạo 2 Materialized Views trên Supabase...")
    conn = get_db_connection()
    conn.autocommit = True
    cur = conn.cursor()

    sql_setup = f"""
    -- =========================================================================
    -- 1. MV CẤP GIỜ
    -- =========================================================================
    DROP MATERIALIZED VIEW IF EXISTS {_TARGET_SCHEMA}.mv_bi_mart_hourly_measures CASCADE;

    CREATE MATERIALIZED VIEW {_TARGET_SCHEMA}.mv_bi_mart_hourly_measures AS
    WITH Raw_Joined AS (
        SELECT
            gen.site_id,
            gen.geo_id,
            gen.date_id,
            gen.hourly_bucket,
            gen.total_energy            AS e_hourly,
            -- Outlier flags (đã aggregate sẵn bên trong subquery gen)
            -- gen.rolling_outlier_flag,
            gen.gmm_if_outlier_flag,
            -- gen.fill_null_algorithm,
            -- Thời tiết
            w.shortwave_radiation,
            w.temperature_c,
            w.cloud_cover_total,
            w.cloud_cover_low,
            w.cloud_cover_mid,
            w.cloud_cover_high,
            w.diffuse_solar_radiation,
            w.direct_normal_irradiance,
            w.wind_speed,
            w.precipitation_mm,
            w.sunshine_duration,
            -- Lịch
            d.is_holiday,
            d.is_semester,
            d.is_exam,
            CASE WHEN gen.hourly_bucket BETWEEN 6 AND 18 THEN true ELSE false END AS is_day,
            -- Thông số hệ thống
            COALESCE(site.capacity_kw, 0) AS p_stc
        FROM (
            -- FIX: aggregate outlier flags bên trong subquery cùng chỗ với SUM energy
            SELECT
                f.site_id,
                f.geo_id,
                f.date_id,
                t.hour                                                      AS hourly_bucket,
                SUM(f.energy_generated_kwh)                                 AS total_energy,
                -- bool_or(f.rolling_outlier_flag)                             AS rolling_outlier_flag,
                bool_or(f.gmm_if_outlier_flag)                              AS gmm_if_outlier_flag
                -- MODE() WITHIN GROUP (ORDER BY f.fill_null_algorithm)        AS fill_null_algorithm
            FROM {_SOURCE_SCHEMA}.fact_solar_energy_gen f
            JOIN {_SOURCE_SCHEMA}.dim_time t ON f.time_id = t.time_id
            GROUP BY f.site_id, f.geo_id, f.date_id, t.hour
        ) gen
        LEFT JOIN (
            SELECT * FROM (
                SELECT
                    fw.*,
                    dw.hour AS weather_hour,
                    ROW_NUMBER() OVER(
                        PARTITION BY fw.geo_id, fw.date_id, dw.hour
                        ORDER BY fw.weather_id
                    ) AS rn
                FROM {_SOURCE_SCHEMA}.fact_weather fw
                JOIN {_SOURCE_SCHEMA}.dim_time dw ON fw.time_id = dw.time_id
            ) sub WHERE rn = 1
        ) w ON gen.geo_id = w.geo_id AND gen.date_id = w.date_id AND gen.hourly_bucket = w.weather_hour
        LEFT JOIN {_SOURCE_SCHEMA}.dim_solar_site site ON gen.site_id = site.site_id
        LEFT JOIN {_SOURCE_SCHEMA}.dim_date d ON gen.date_id = d.date_id
    ),

    Calculated_Measures AS (
        SELECT *, {_FIT_RATE} AS fit_rate FROM Raw_Joined
    ),

    -- ① Tính nhiệt độ tế bào & PR thực tế
    Efficiency_Calc AS (
        SELECT *,
            (temperature_c + (shortwave_radiation * {_NOCT_FACTOR})) AS t_cell,
            CASE
                WHEN shortwave_radiation < {_MIN_RADIATION} THEN 0
                ELSE e_hourly / NULLIF(p_stc * (shortwave_radiation / 1000.0), 0)
            END AS pr_actual
        FROM Calculated_Measures
    ),

    -- ② Tính suy hao nhiệt
    Loss_Calc AS (
        SELECT *,
            CASE
                WHEN t_cell > 25 THEN (t_cell - 25) * {_TEMP_COEFF}
                ELSE 0
            END AS loss_temp
        FROM Efficiency_Calc
    ),

    -- ③ Tính PR điều chỉnh
    PR_Adj_Calc AS (
        SELECT *,
            CASE
                WHEN shortwave_radiation < {_MIN_RADIATION} THEN 0
                ELSE ({_NOMINAL_PR} * (1 - loss_temp))
            END AS pr_adjusted
        FROM Loss_Calc
    )

    -- ④ Output cuối
    SELECT
        -- === ĐỊNH DANH ===
        date_id, hourly_bucket, site_id, geo_id,

        -- === LỊCH ===
        is_holiday, is_semester, is_exam, is_day,

        -- === THỜI TIẾT (thô) ===
        shortwave_radiation, temperature_c,
        cloud_cover_total, cloud_cover_low, cloud_cover_mid, cloud_cover_high,
        diffuse_solar_radiation, direct_normal_irradiance,
        wind_speed, precipitation_mm, sunshine_duration,

        -- === THÔNG SỐ HỆ THỐNG ===
        p_stc, fit_rate,

        -- === OUTLIER FLAGS ===
        -- rolling_outlier_flag,
        gmm_if_outlier_flag,
        -- fill_null_algorithm,

        -- === MEASURES ĐÃ TÍNH ===
        t_cell,
        loss_temp,
        pr_actual,
        pr_adjusted,
        e_hourly,
        (p_stc * (shortwave_radiation / 1000.0) * pr_adjusted)                         AS e_expected,
        (e_hourly - (p_stc * (shortwave_radiation / 1000.0) * pr_adjusted))             AS delta_baseline,
        (e_hourly * fit_rate)                                                            AS estimated_revenue,
        CASE
            WHEN (p_stc * (shortwave_radiation / 1000.0) * pr_adjusted) > e_hourly
            THEN ((p_stc * (shortwave_radiation / 1000.0) * pr_adjusted) - e_hourly) * fit_rate
            ELSE 0
        END                                                                              AS cost_of_underperformance,
        (e_hourly * {_CO2_FACTOR})                                                       AS co2_avoided_kg,
        ((e_hourly * {_CO2_FACTOR}) / {_TREES_FACTOR})                                  AS equivalent_trees_planted

    FROM PR_Adj_Calc;

    CREATE UNIQUE INDEX idx_mv_hourly_unique
        ON {_TARGET_SCHEMA}.mv_bi_mart_hourly_measures(date_id, site_id, hourly_bucket);


    -- =========================================================================
    -- 2. MV CẤP NGÀY
    -- =========================================================================
    DROP MATERIALIZED VIEW IF EXISTS {_TARGET_SCHEMA}.mv_bi_mart_daily_kpis CASCADE;

    CREATE MATERIALIZED VIEW {_TARGET_SCHEMA}.mv_bi_mart_daily_kpis AS
    WITH daily_base AS (
        SELECT
            date_id,
            site_id,
            geo_id,

            -- Trường phân loại
            MAX(is_holiday::int)::boolean  AS is_holiday,
            MAX(is_semester::int)::boolean AS is_semester,
            MAX(is_exam::int)::boolean     AS is_exam,

            -- Thông số hệ thống
            MAX(p_stc) AS p_stc,

            -- Outlier: có bất kỳ giờ nào bị outlier trong ngày không
            -- bool_or(rolling_outlier_flag) AS has_rolling_outlier,
            bool_or(gmm_if_outlier_flag)  AS has_gmm_outlier,

            -- Sản lượng & doanh thu
            SUM(e_hourly)                 AS e_daily,
            SUM(e_expected)               AS e_target_daily,
            SUM(delta_baseline)           AS daily_delta_baseline,
            SUM(estimated_revenue)        AS daily_revenue,
            SUM(cost_of_underperformance) AS daily_cost_underperformance,

            -- Môi trường
            SUM(co2_avoided_kg)           AS daily_co2_avoided,
            SUM(equivalent_trees_planted) AS daily_trees_planted,

            -- Thời tiết trung bình/tổng
            AVG(temperature_c)            AS avg_temp_c,
            AVG(cloud_cover_total)        AS avg_cloud_cover,
            AVG(wind_speed)               AS avg_wind_speed,
            SUM(precipitation_mm)         AS daily_precipitation,
            SUM(shortwave_radiation)      AS daily_total_radiation,
            SUM(sunshine_duration)        AS daily_sunshine_duration,

            -- Hiệu suất trung bình
            AVG(pr_actual)                AS avg_pr_actual,
            AVG(pr_adjusted)              AS avg_pr_adjusted,
            AVG(loss_temp)                AS avg_loss_temp,
            AVG(t_cell)                   AS avg_t_cell

        FROM {_TARGET_SCHEMA}.mv_bi_mart_hourly_measures
        GROUP BY date_id, site_id, geo_id
    ),

    kpi_calc AS (
        SELECT
            *,
            -- KPI 1: Capacity Factor
            CASE WHEN p_stc > 0 THEN e_daily / (p_stc * 24) ELSE 0 END AS capacity_factor,

            -- KPI 2: Yield Fulfillment Ratio
            CASE WHEN e_target_daily > 0 THEN (e_daily / e_target_daily) ELSE 0 END AS yield_fulfillment_ratio,

            -- KPI 3: Specific Yield (kWh/kWp/ngày)
            CASE WHEN p_stc > 0 THEN e_daily / p_stc ELSE 0 END AS specific_yield,

            -- KPI 4: Time-Intelligence sản lượng
            SUM(e_daily) OVER (
                PARTITION BY site_id, DATE_TRUNC('week',  to_date(date_id::text, 'YYYYMMDD'))
                ORDER BY date_id
            ) AS wtd_energy,
            SUM(e_daily) OVER (
                PARTITION BY site_id, DATE_TRUNC('month', to_date(date_id::text, 'YYYYMMDD'))
                ORDER BY date_id
            ) AS mtd_energy,
            SUM(e_daily) OVER (
                PARTITION BY site_id, DATE_TRUNC('year',  to_date(date_id::text, 'YYYYMMDD'))
                ORDER BY date_id
            ) AS ytd_energy,

            -- KPI 5: Time-Intelligence doanh thu
            SUM(daily_revenue) OVER (
                PARTITION BY site_id, DATE_TRUNC('month', to_date(date_id::text, 'YYYYMMDD'))
                ORDER BY date_id
            ) AS mtd_revenue,
            SUM(daily_revenue) OVER (
                PARTITION BY site_id, DATE_TRUNC('year',  to_date(date_id::text, 'YYYYMMDD'))
                ORDER BY date_id
            ) AS ytd_revenue

        FROM daily_base
    )

    SELECT * FROM kpi_calc;

    CREATE UNIQUE INDEX idx_mv_daily_unique
        ON {_TARGET_SCHEMA}.mv_bi_mart_daily_kpis(date_id, site_id);
    """

    try:
        cur.execute(sql_setup)
        print("[Thành công] Đã đúc xong 2 Materialized Views (Cấp Giờ & Cấp Ngày)!")
    except Exception as e:
        print(f"[Lỗi] Khởi tạo thất bại: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    setup_materialized_views()