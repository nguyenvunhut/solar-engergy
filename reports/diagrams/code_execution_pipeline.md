# SƠ ĐỒ LUỒNG CHẠY PIPELINE MÃ NGUỒN (DATA EXECUTION PIPELINE DIAGRAM) - THE OUTLIERS

Tài liệu này mô tả chi tiết kiến trúc luồng dữ liệu và trình tự thi hành mã nguồn (Code Execution Pipeline) trong thư mục `srcs/` của dự án **Phân tích Hiệu suất và Dự báo Sản lượng Điện Mặt Trời (The Outliers - FPT Polytechnic)**.

---

## 1. MÃ MÀU VÀ NGUYÊN TẮC HÌNH KHỐI (COLOR CODING & SHAPES)

- **Main Orchestrator Header (`#1B2631` / `#2C3E50` - Dark Blue):** Thanh điều phối trung tâm `main.py` và các module tiện ích `00_utils/`.
- **Orange (`#D35400` / `#F39C12`):** DATA INGESTION (`srcs/01_extract`) - Hình Parallelogram đại diện cho các script download/crawl API.
- **Blue (`#1F618D` / `#2980B9`):** STAGING & BUFFER (`srcs/03_load` & `02_transform`) - Hình Cylinder đại diện cho PostgreSQL Staging DB.
- **Purple (`#512E5B` / `#8E44AD`):** IMPUTATION & OUTLIERS (`srcs/02_transform`) - Hình Rounded Rectangle đại diện cho các bước xử lý dữ liệu (Imputation, GMM+IF, Apply Flags).
- **Dark Teal (`#0E6251` / `#16A085`):** DATA WAREHOUSE (`srcs/03_load`) - Hình Cylinder đại diện cho Supabase PostgreSQL DWH (Galaxy Schema: 5 Dims + 2 Facts).
- **Green (`#145A32` / `#27AE60`):** DATA MARTS (`srcs/04_build_data_marts`) - Các khối build BI Mart (KPIs) và ML Mart.
- **Red (`#641E16` / `#E74C3C`):** DOWNSTREAM APPLICATIONS - Tableau Dashboards và Machine Learning Forecasting Pipeline.

---

## 2. BIỂU ĐỒ MERMAID CHI TIẾT (MERMAID DATA FLOW)

```mermaid
flowchart TD
    subgraph S0["🍊 ORANGE: DATA INGESTION (srcs/01_extract)"]
        A1[/"01_download_kaggle_raw.py\nin: Kaggle API\nout: Solar PV CSVs"/] --> A3[("Supabase S3 Storage\n(Raw Data Buckets)")]
        A2[/"02_download_open_meteo_raw.py\nin: Open-Meteo REST API\nout: Weather JSON/CSV"/] --> A3
    end

    subgraph ORCH["🔵 DARK BLUE: MAIN ORCHESTRATOR & UTILS (srcs/06_run_pipeline & srcs/00_utils)"]
        MAIN["main.py CLI Orchestrator\n(--stage all / staging / transform / imputation / generate_outliers / outlier / load / bimarts / mlmarts)"]
        U_DB["01_database.py\n(SQLAlchemy + psycopg2)"]
        U_ST["02_storage.py\n(S3 Storage Client)"]
    end

    MAIN -->|Step 1| STG1
    MAIN -->|Step 2| STG2
    MAIN -->|Step 3| STG3
    MAIN -->|Step 4| STG4
    MAIN -->|Step 5| STG5
    MAIN -->|Step 6| STG6
    MAIN -->|Step 7| STG7
    MAIN -->|Step 8| STG8

    subgraph STAGING["🔹 BLUE: STAGING & BUFFER (srcs/03_load & srcs/02_transform)"]
        STG1[/"[Stage 1] 01_run_load_staging.py\nin: S3 Buckets\nout: staging.stg_*"/]
        STG2[/"[Stage 2] 01_run_transform_buffers.py\nin: staging.stg_*\nout: staging buffer tables"/]
        DB_STG[("PostgreSQL Staging DB\n(staging.fact_* & stg_*)")]

        A3 --> STG1 --> STG2 --> DB_STG
    end

    subgraph PURPLE["🟣 PURPLE: IMPUTATION & OUTLIERS (srcs/02_transform)"]
        STG3["[Stage 3] 02_run_hybrid_imputation.py\nin: raw staging buffer\nout: imputed generation data"]
        STG4["[Stage 4] 02_generate_outliers/\nin: imputed buffer Parquet\nout: GMM+IF+Rolling CSV flags"]
        STG5["[Stage 5] 02_run_apply_outlier_flags.py\nin: verified outlier CSVs\nout: flagged staging buffer"]

        DB_STG --> STG3 --> STG4 --> STG5
    end

    subgraph DWH_SEC["🟢 DARK TEAL: DATA WAREHOUSE (srcs/03_load)"]
        STG6[/"[Stage 6] 01_run_load_datawarehouse.py\nin: flagged staging buffer\nout: DWH Dim & Fact tables"/]
        DB_DWH[("Supabase PostgreSQL DWH\nGalaxy Schema: 5 Dims + 2 Facts")]

        STG5 --> STG6 --> DB_DWH
    end

    subgraph MARTS["🌿 GREEN: DATA MARTS (srcs/04_build_data_marts)"]
        STG7["[Stage 7] 01_build_bi_mart.py & 03_build_bi_view.py\nin: DWH Facts & Dims\nout: BI views & BI mart (KPIs)"]
        STG8["[Stage 8] 02_build_ml_mart.py\nin: DWH Facts & Dims\nout: Denormalized ML Dataset"]

        DB_DWH --> STG7
        DB_DWH --> STG8
    end

    subgraph APPS["🔴 RED: DOWNSTREAM APPLICATIONS"]
        APP_TAB["Tableau Dashboards\n(Executive & Operational Views)"]
        APP_ML["ML Forecasting Pipeline\n(Forcasting_v3: LightGBM / Prophet / SHAP)"]

        STG7 --> APP_TAB
        STG8 --> APP_ML
    end

    classDef extract fill:#d35400,stroke:#a04000,color:#fff;
    classDef stg fill:#1f618d,stroke:#154360,color:#fff;
    classDef purp fill:#512e5b,stroke:#4a235a,color:#fff;
    classDef teal fill:#0e6251,stroke:#0b5345,color:#fff;
    classDef green fill:#145a32,stroke:#0e4b25,color:#fff;
    classDef red fill:#641e16,stroke:#4a148c,color:#fff;
    classDef orch fill:#1b2631,stroke:#0d1117,color:#fff;

    class A1,A2,A3 extract;
    class STG1,STG2,DB_STG stg;
    class STG3,STG4,STG5 purp;
    class STG6,DB_DWH teal;
    class STG7,STG8 green;
    class APP_TAB,APP_ML red;
    class MAIN,U_DB,U_ST orch;
```
