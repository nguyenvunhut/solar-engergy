create schema IF not exists staging;

-- 1. Bảng Staging: stg_calender
create table staging.stg_calender (
  date VARCHAR(255),
  is_holiday VARCHAR(255),
  is_semester VARCHAR(255),
  is_exam VARCHAR(255)
);

-- 2. Bảng Staging: stg_campus_meta
create table staging.stg_campus_meta (
  id VARCHAR(255),
  name VARCHAR(255),
  capicity VARCHAR(255)
);

-- 3. Bảng Staging: stg_open_meteo_weather_raw_2023
create table staging.stg_open_meteo_weather_raw_2023 (
  timestamp VARCHAR(255),
  shortwave_radiation VARCHAR(255),
  direct_radiation VARCHAR(255),
  diffuse_radiation VARCHAR(255),
  temperature_2m VARCHAR(255),
  weather_code VARCHAR(255),
  is_day VARCHAR(255),
  cloud_cover VARCHAR(255),
  cloud_cover_low VARCHAR(255),
  cloud_cover_mid VARCHAR(255),
  cloud_cover_high VARCHAR(255),
  wind_speed_10m VARCHAR(255),
  precipitation VARCHAR(255),
  sunshine_duration VARCHAR(255),
  SiteKey VARCHAR(255),
  latitude VARCHAR(255),
  longitude VARCHAR(255)
);

-- 4. Bảng Staging: stg_solar_energy_generation
create table staging.stg_solar_energy_generation (
  CampusKey VARCHAR(255),
  SiteKey VARCHAR(255),
  Timestamp VARCHAR(255),
  SolarGeneration VARCHAR(255)
);


-- 5. Bảng Staging: stg_solar_site_details
create table staging.stg_solar_site_details (
  CampusKey VARCHAR(255),
  SiteKey VARCHAR(255),
  kWp VARCHAR(255),
  Number_of_panels VARCHAR(255),
  Panel VARCHAR(255),
  Inverter VARCHAR(255),
  Optimizers VARCHAR(255),
  Metric VARCHAR(255),
  lat VARCHAR(255),
  Lon VARCHAR(255)
);

-- Phần 2: Tạo bảng đệm (MIRROR STAGING)
-- 1. Bảng Dim_Solar_Site (Giữ lại CampusKey và SiteKey)
CREATE TABLE staging.dim_solar_site (
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
CREATE TABLE staging.dim_geography (
    SiteKey VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    location_name VARCHAR(255)
);

-- 3. Bảng Dim_Date (Dùng full_date làm gốc)
CREATE TABLE staging.dim_date (
    full_date DATE,
    day INT,
    month INT,
    year INT,
    is_holiday VARCHAR(50),
    is_semester VARCHAR(50),
    is_exam VARCHAR(50)
);

-- 4. Bảng Dim_Time (Dùng time_string làm gốc)
CREATE TABLE staging.dim_time (
    time_string VARCHAR(50),
    hour INT,
    minute INT
);

-- 5. Bảng Dim_Weather_Type (Dùng weather_code và is_day làm gốc)
CREATE TABLE staging.dim_weather_type (
    weather_code INT,
    is_day INT,
    weather_condition VARCHAR(255),
    description VARCHAR(255)
);

-- 6. Bảng Fact_Solar_Energy_Gen
CREATE TABLE staging.fact_solar_energy_gen (
    SiteKey VARCHAR(255),
    timestamp TIMESTAMP,
    energy_generated_kwh FLOAT
);

-- 7. Bảng Fact_Weather
CREATE TABLE staging.fact_weather (
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