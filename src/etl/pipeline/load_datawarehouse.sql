-- ==============================================================================
-- BƯỚC 0: TẨY TRẮNG DỮ LIỆU CŨ TRÊN SCHEMA DATAWAREHOUSE
-- ==============================================================================
TRUNCATE TABLE datawarehouse.dim_date CASCADE;
TRUNCATE TABLE datawarehouse.dim_geography CASCADE;
TRUNCATE TABLE datawarehouse.dim_solar_site CASCADE;
TRUNCATE TABLE datawarehouse.dim_time CASCADE;
TRUNCATE TABLE datawarehouse.dim_weather_type CASCADE;
TRUNCATE TABLE datawarehouse.fact_solar_energy_gen CASCADE;
TRUNCATE TABLE datawarehouse.fact_weather CASCADE;

-- ==============================================================================
-- BƯỚC 1: NẠP DỮ LIỆU VÀO CÁC BẢNG DIMENSION (SCHEMA DATAWAREHOUSE)
-- ==============================================================================
-- 1. Nạp bảng datawarehouse.dim_solar_site
INSERT INTO datawarehouse.dim_solar_site(
      site_id, 
      campus_name, 
      capacity_kw, 
      number_of_panels, 
      panel, 
      inverter, 
      optimizers, 
      metric
)
SELECT 
      CAST(sitekey as INT),
      campus_name, 
      capacity_kw, 
      number_of_panels, 
      panel, 
      inverter, 
      optimizers,
      metric
FROM staging.dim_solar_site
ON CONFLICT (site_id) DO NOTHING;

-- 2. Nạp bảng datawarehouse.dim_weather_type
INSERT INTO datawarehouse.dim_weather_type(
      weather_type_id,
      weather_code, 
      is_day, 
      weather_condition, 
      description
)
SELECT
      ROW_NUMBER() OVER(ORDER BY weather_code, is_day) + (SELECT COALESCE(MAX(weather_type_id), 0) FROM datawarehouse.dim_weather_type),
      weather_code, 
      is_day, 
      weather_condition, 
      description
FROM staging.dim_weather_type
ON CONFLICT (weather_type_id) DO NOTHING;

-- 3. Nạp bảng datawarehouse.dim_geography
INSERT INTO datawarehouse.dim_geography(
      geo_id
      , latitude
      , longitude
      , location_name
)
SELECT
      CAST(sitekey as int)
      , latitude
      , longitude
      , location_name
FROM staging.dim_geography
ON CONFLICT (geo_id) DO NOTHING;

-- 4. Nạp bảng datawarehouse.dim_date
INSERT INTO datawarehouse.dim_date (
      date_id
      , full_date
      , day
      , month
      , year
)
SELECT 
      CAST(TO_CHAR(full_date,'YYYYMMDD') AS INT) AS date_id
      , full_date
      , day
      , month
      , year
FROM staging.dim_date
WHERE full_date IS NOT NULL
ON CONFLICT (date_id) DO NOTHING;

-- 5. Nạp bảng datawarehouse.dim_time
INSERT INTO datawarehouse.dim_time(
      time_id
      , time_string
      , hour
      , minute
)
SELECT DISTINCT
      (CAST(hour AS INT) * 100) + CAST(minute AS INT) AS time_id
      , time_string
      , CAST(hour AS INT) AS hour
      , CAST(minute AS INT) AS minute
FROM staging.dim_time
WHERE hour IS NOT NULL AND minute IS NOT NULL
ON CONFLICT (time_id) DO NOTHING;


-- ==============================================================================
-- BƯỚC 2: NẠP DỮ LIỆU VÀO CÁC BẢNG FACT (SCHEMA DATAWAREHOUSE)
-- ==============================================================================
-- 1. Nạp bảng dữ liệu Sản lượng điện mặt trời datawarehouse.fact_solar_energy_gen
-- 1. SET TIMEOUT 15 phút
SET statement_timeout = '15min';

-- 2. NẠP DỮ LIỆU THEO TỪNG THÁNG (Giả lập logic chia batch của Python)
-- Sử dụng WITH để xác định các dải thời gian (month_ranges)
WITH months AS (
    SELECT DISTINCT 
        date_trunc('month', timestamp)::timestamp AS month_start,
        (date_trunc('month', timestamp) + interval '1 month')::timestamp AS month_end
    FROM staging.fact_solar_energy_gen
    ORDER BY month_start
)
INSERT INTO datawarehouse.fact_solar_energy_gen (
    gen_id, site_id, geo_id, date_id, time_id, energy_generated_kwh, rolling_outlier_flag
)
SELECT
    -- Tính toán gen_id nối tiếp dựa trên tổng số dòng đã nạp của các tháng trước
    (SELECT COALESCE(SUM(c), 0) FROM (
        SELECT COUNT(*) as c FROM staging.fact_solar_energy_gen s2 
        WHERE s2.timestamp < m.month_start
    ) t) + row_number() OVER (ORDER BY s.timestamp, s.sitekey::int) AS gen_id,
    s.sitekey::int AS site_id,
    s.sitekey::int AS geo_id,
    dd.date_id,
    dt.time_id,
    s.energy_generated_kwh,
    COALESCE(s.rolling_outlier_flag, false) AS rolling_outlier_flag
FROM staging.fact_solar_energy_gen s
JOIN months m ON s.timestamp >= m.month_start AND s.timestamp < m.month_end
JOIN datawarehouse.dim_date dd ON dd.full_date = s.timestamp::date
JOIN datawarehouse.dim_time dt ON dt.time_string = to_char(s.timestamp, 'HH24:MI')
JOIN datawarehouse.dim_solar_site ds ON ds.site_id = s.sitekey::int
JOIN datawarehouse.dim_geography dg ON dg.geo_id = s.sitekey::int;

-- 4. VALIDATION (Kiểm tra lại sau khi nạp)
-- Nếu tổng dòng nạp vào không bằng tổng nguồn, câu lệnh sẽ tự báo lỗi
DO $$
DECLARE
    v_source_count BIGINT;
    v_target_count BIGINT;
BEGIN
    SELECT COUNT(*) INTO v_source_count FROM staging.fact_solar_energy_gen;
    SELECT COUNT(*) INTO v_target_count FROM datawarehouse.fact_solar_energy_gen;
    
    IF v_source_count != v_target_count THEN
        RAISE EXCEPTION 'Validation Failed: Source=%s, Target=%s', v_source_count, v_target_count;
    END IF;
END $$;

COMMIT;

-- 2. Nạp bảng dữ liệu Thời tiết datawarehouse.fact_weather
INSERT INTO datawarehouse.fact_weather (
      weather_id
      , geo_id
      , date_id
      , time_id
      , weather_type_id
      , is_day
      , shortwave_radiation
      , temperature_c
      , cloud_cover_total
      , cloud_cover_low
      , cloud_cover_mid
      , cloud_cover_high
      , diffuse_solar_radiation
      , direct_normal_irradiance
      , wind_speed
      , precipitation_mm
      , sunshine_duration
)
SELECT
      ROW_NUMBER() OVER(ORDER BY f.timestamp) + m.max_id AS weather_id
      , CAST(f.SiteKey AS INT) AS geo_id
      , CAST(TO_CHAR(f.timestamp, 'YYYYMMDD') AS INT) AS date_id
      , (EXTRACT(HOUR FROM f.timestamp) * 100 + EXTRACT(MINUTE FROM f.timestamp))::INT AS time_id
      , w.weather_type_id
      , f.is_day
      , f.shortwave_radiation
      , f.temperature_c
      , f.cloud_cover_total
      , f.cloud_cover_low
      , f.cloud_cover_mid
      , f.cloud_cover_high
      , f.diffuse_solar_radiation
      , f.direct_normal_irradiance
      , f.wind_speed
      , f.precipitation_mm
      , f.sunshine_duration
FROM staging.fact_weather f
INNER JOIN datawarehouse.dim_weather_type w 
    ON f.weather_code = w.weather_code 
    AND f.is_day = w.is_day
CROSS JOIN (
    SELECT COALESCE(MAX(weather_id), 0) AS max_id 
    FROM datawarehouse.fact_weather
) m
ON CONFLICT (weather_id) DO NOTHING;