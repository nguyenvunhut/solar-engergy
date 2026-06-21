create schema IF not exists staging;

-- 1. Bảng Staging: stg_calender
create table IF NOT EXISTS staging.stg_calender (
  date VARCHAR(255),
  is_holiday VARCHAR(255),
  is_semester VARCHAR(255),
  is_exam VARCHAR(255)
);

-- 2. Bảng Staging: stg_campus_meta
create table IF NOT EXISTS staging.stg_campus_meta (
  id VARCHAR(255),
  name VARCHAR(255),
  capicity VARCHAR(255)
);

-- 3. Bảng Staging: stg_open_meteo_weather_raw
create table IF NOT EXISTS staging.stg_open_meteo_weather_raw (
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
create table IF NOT EXISTS staging.stg_solar_energy_generation (
  CampusKey VARCHAR(255),
  SiteKey VARCHAR(255),
  Timestamp VARCHAR(255),
  SolarGeneration VARCHAR(255)
);


-- 5. Bảng Staging: stg_solar_site_details
create table IF NOT EXISTS staging.stg_solar_site_details (
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
