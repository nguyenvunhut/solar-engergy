# KIẾN TRÚC HỆ THỐNG DỮ LIỆU TẬP TRUNG (SYSTEM ARCHITECTURE)
**Dự án Tốt nghiệp — The Outliers | Chuyên ngành Xử lý Dữ liệu**

Tệp nguồn Draw.io: [`system_architecture.drawio`](system_architecture.drawio)  
Hình ảnh xuất bản: [`system_architecture.png`](../figures/system_architecture.png)

---

## 1. SƠ ĐỒ LUỒNG KIẾN TRÚC TỔNG QUAN (MERMAID DIAGRAM)

```mermaid
flowchart TB
    %% STYLING
    classDef rawStyle fill:#F8FAFC,stroke:#64748B,stroke-width:2px,color:#0F172A;
    classDef stgStyle fill:#FEF3C7,stroke:#D97706,stroke-width:2px,color:#78350F;
    classDef dwStyle fill:#EEF2FF,stroke:#4338CA,stroke-width:2px,color:#1E1B4B;
    classDef martStyle fill:#DCFCE7,stroke:#16A34A,stroke-width:2px,color:#14532D;
    classDef appStyle fill:#FCE7F3,stroke:#DB2777,stroke-width:2px,color:#831843;

    %% LAYER 1
    subgraph L1 [" 1. RAW DATA (Nguồn Dữ Liệu Thô) "]
        R_CSV[("📁 CSV Files<br/>• Solar_Energy_Gen (15m)<br/>• Site Details & Campus<br/>• Calendar")]:::rawStyle
        R_API[("🌐 Open-Meteo API<br/>• Hourly Meteorological")]:::rawStyle
        R_DVC["📦 DVC & S3 Storage<br/>(Version Control)"]:::rawStyle
    end

    %% LAYER 2
    subgraph L2 [" 2. STAGING & BUFFER (Schema: staging) "]
        STG_RAW[("📥 Raw String Tables<br/>stg_solar_energy_generation<br/>stg_open_meteo_weather_raw<br/>stg_solar_site_details")]:::stgStyle
        STG_ETL[["⚙️ Python ETL Transformation<br/>Type Casting • Imputation<br/>Night Filter • Outliers (Rolling IQR/GMM)"]]:::stgStyle
        STG_BUF[("📋 Mirror Buffer Tables<br/>staging.dim_* (5 Dims)<br/>staging.fact_solar_energy_gen<br/>staging.fact_weather")]:::stgStyle
        STG_RAW --> STG_ETL --> STG_BUF
    end

    %% LAYER 3
    subgraph L3 [" 3. DATA WAREHOUSE (Galaxy Schema - Schema: datawarehouse) "]
        DW_DIMS[("🏛️ Conformed Dimensions<br/>• dim_solar_site (42 sites)<br/>• dim_geography (Tọa độ)<br/>• dim_date (Lịch/Thi)<br/>• dim_time (Lưới 15p)<br/>• dim_weather_type (WMO)")]:::dwStyle
        DW_F_GEN[("⚡ fact_solar_energy_gen<br/>(Chu kỳ 15 phút)")]:::dwStyle
        DW_F_WEA[("⛅ fact_weather<br/>(Chu kỳ 1 giờ)")]:::dwStyle
        DW_DIMS -.-> DW_F_GEN
        DW_DIMS -.-> DW_F_WEA
    end

    %% LAYER 4
    subgraph L4 [" 4. DATA MART LAYER (Marts & Feature Store) "]
        M_BI[("📊 BI Mart (bi_mart)<br/>• fact_solar_performance_hourly<br/>• Materialized Views & KPIs<br/>(PR, CF, Tiền FIT, CO2 Offset)")]:::martStyle
        M_ML[("🤖 ML Mart (ml_mart / Parquet)<br/>• base_build & v3_final_cleaned<br/>• Causal Weather Floor Join<br/>• 40 Features (Solar Geo, Lags)")]:::martStyle
    end

    %% LAYER 5
    subgraph L5 [" 5. APPLICATION & CONSUMPTION "]
        APP_BI["📈 Tableau Dashboards<br/>1. Executive Overview<br/>2. Performance & Weather<br/>3. Outlier & Sensor Anomaly"]:::appStyle
        APP_ML["🧠 ML Models & Serving<br/>• LightGBM (Huber/MAE)<br/>• Baseline: Prophet & ARIMA<br/>• SHAP Explainability"]:::appStyle
    end

    %% CONNECTIONS
    R_CSV --> STG_RAW
    R_API --> STG_RAW
    R_DVC -.-> STG_ETL
    STG_BUF ==>|"Load DW"| L3
    DW_F_GEN --> M_BI
    DW_F_WEA --> M_BI
    DW_F_GEN --> M_ML
    DW_F_WEA --> M_ML
    M_BI --> APP_BI
    M_ML --> APP_ML
```

---

## 2. BẢNG PHÂN RÃ CÁC TẦNG KIẾN TRÚC

| Tầng | Đối tượng CSDL / Mã nguồn | Định dạng / Công nghệ | Mô tả chức năng |
|---|---|---|---|
| **1. Raw Data** | • `Solar_Energy_Generation.csv` (2.73M dòng)<br/>• `Solar_Site_Details.csv` (42 trạm)<br/>• `open_meteo_weather_raw.csv` (367K dòng) | Local CSV, Open-Meteo API, DVC, S3 Storage | Thu thập dữ liệu IoT giám sát PV và dữ liệu khí tượng viễn thám. |
| **2. Staging & Buffer** | • Schema `staging.stg_*`<br/>• `srcs/02_transform/`, `srcs/03_load/`<br/>• Schema `staging.dim_*`, `staging.fact_*` | PostgreSQL, Pandas, Scikit-learn | Chứa dữ liệu text thô, chạy pipeline ép kiểu, xử lý khuyết thiếu, lọc nhiễu ban đêm, gắn cờ outlier. |
| **3. Data Warehouse** | • Schema `datawarehouse`<br/>• 5 Conformed Dims: `dim_solar_site`, `dim_geography`, `dim_date`, `dim_time`, `dim_weather_type`<br/>• 2 Facts: `fact_solar_energy_gen` (15p), `fact_weather` (1h) | PostgreSQL (Supabase) | Lưu trữ theo mô hình **Galaxy Schema**, giải quyết bài toán lệch pha thời gian (15p vs 1h). |
| **4. Data Marts** | • **BI Mart (`bi_mart`):** `fact_solar_performance_hourly`, MV cấp Giờ/Ngày, KPIs (PR, CF, FIT, CO2)<br/>• **ML Mart (`ml_mart`):** `base_build`, `v3_final_cleaned.parquet`, Causal Floor Join, 40 Features | PostgreSQL, Parquet Storage | Tối ưu hóa truy vấn cho Tableau Dashboard và cung cấp Feature Store sạch cho Machine Learning. |
| **5. Applications** | • 3 Tableau Dashboards (`.twbx`)<br/>• `srcs/05_machine_learning/pipeline/` (LightGBM, Prophet, ARIMA, SHAP) | Tableau Desktop, LightGBM, Optuna, SHAP | Phân tích điều hành, tối ưu bảo trì (Predictive Maintenance) và dự báo sản lượng chính xác. |
