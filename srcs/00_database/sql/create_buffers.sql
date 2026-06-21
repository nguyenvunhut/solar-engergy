-- Phần 2: Tạo bảng đệm (MIRROR STAGING / BUFFERS)

-- 1. Bảng Dim_Solar_Site (Giữ lại CampusKey và SiteKey)
CREATE TABLE IF NOT EXISTS staging.dim_solar_site (
    CampusKey VARCHAR(255),
    SiteKey VARCHAR(255),
    campus_name VARCHAR(255),
    capacity_kw FLOAT,
    Number_of_panels INT,
    Panel VARCHAR(255),
    Inverter VARCHAR(255),
    Optimizers VARCHAR(255),
    Metric VARCHAR(50)
);

-- 2. Bảng Dim_Geography (Dùng SiteKey làm mốc tọa độ)
CREATE TABLE IF NOT EXISTS staging.dim_geography (
    SiteKey VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    location_name VARCHAR(255)
);

-- 3. Bảng Dim_Date (Dùng full_date làm gốc)
CREATE TABLE IF NOT EXISTS staging.dim_date (
    full_date DATE,
    day INT,
    month INT,
    year INT,
    is_holiday VARCHAR(50),
    is_semester VARCHAR(50),
    is_exam VARCHAR(50)
);

-- 4. Bảng Dim_Time (Dùng time_string làm gốc)
CREATE TABLE IF NOT EXISTS staging.dim_time (
    time_string VARCHAR(50),
    hour INT,
    minute INT
);

-- 5. Bảng Dim_Weather_Type (Dùng weather_code và is_day làm gốc)
CREATE TABLE IF NOT EXISTS staging.dim_weather_type (
    weather_code INT,
    is_day INT,
    weather_condition VARCHAR(255),
    description VARCHAR(255)
);

-- 6. Bảng Fact_Solar_Energy_Gen
CREATE TABLE IF NOT EXISTS staging.fact_solar_energy_gen (
    SiteKey VARCHAR(255),
    Timestamp TIMESTAMP,
    Energy_Generated_kWh DOUBLE PRECISION,
    rolling_outlier_flag BOOLEAN DEFAULT false,
    PRIMARY KEY (SiteKey, Timestamp)
);

-- 7. Bảng Fact_Weather
CREATE TABLE IF NOT EXISTS staging.fact_weather (
    SiteKey VARCHAR(255),
    timestamp TIMESTAMP,
    weather_code INT,
    is_day INT,
    shortwave_radiation INT,
    temperature_c FLOAT,
    cloud_cover_total FLOAT,
    cloud_cover_low FLOAT,
    cloud_cover_mid FLOAT,
    cloud_cover_high FLOAT,
    Diffuse_Solar_Radiation INT,
    Direct_Normal_Irradiance INT,
    wind_speed FLOAT,
    precipitation_mm FLOAT,
    Sunshine_Duration FLOAT
);
