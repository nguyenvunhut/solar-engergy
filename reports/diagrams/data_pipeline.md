# HỆ THỐNG SƠ ĐỒ KIẾN TRÚC & ĐƯỜNG ỐNG DỮ LIỆU TOÀN DỰ ÁN
## Comprehensive Architecture, ETL Pipelines, Data Modeling & ML Workflows

> **Dự án:** Hệ thống Xử lý Dữ liệu, Nhận diện Dị thường Vận hành và Dự báo Sản lượng 42 Trạm Điện Mặt Trời tại Úc  
> **Nhóm thực hiện:** The Outliers — Chuyên ngành Xử lý Dữ liệu  
> **Tài liệu tham chiếu:** [`README.md`](../../README.md), [`DATN_REPORT_FINAL_02.tex`](../DATN_REPORT_FINAL_02.tex)

---

## MỤC LỤC SƠ ĐỒ
1. [Sơ đồ 1: Kiến Trúc Đường Ống Dữ Liệu Tổng Thể 6 Lớp](#sơ-đồ-1-kiến-trúc-đường-ống-dữ-liệu-tổng-thể-6-lớp)
2. [Sơ đồ 2: Luồng Điền Khuyết Nhân Quả Đa Tầng](#sơ-đồ-2-luồng-điền-khuyết-nhân-quả-đa-tầng)
3. [Sơ đồ 3: Mô Hình Hóa Kho Dữ Liệu Lược Đồ Thiên Hà](#sơ-đồ-3-mô-hình-hóa-kho-dữ-liệu-lược-đồ-thiên-hà)
4. [Sơ đồ 4: Kiến Trúc Nhận Diện Dị Thường Lai GMM-IF & 5 Rào Chắn Vật Lý](#sơ-đồ-4-kiến-trúc-nhận-diện-dị-thường-lai-gmm-if--5-rào-chắn-vật-lý)
5. [Sơ đồ 5: Kiến Trúc Tầng Phục Vụ BI Mart & Đồng Bộ Tableau Desktop](#sơ-đồ-5-kiến-trúc-tầng-phục-vụ-bi-mart--đồng-bộ-tableau-desktop)
6. [Sơ đồ 6: Đường Ống Huấn Luyện & Suy Luận Machine Learning](#sơ-đồ-6-đường-ống-huấn-luyện--suy-luận-machine-learning)

---

## Sơ đồ 1: Kiến Trúc Đường Ống Dữ Liệu Tổng Thể 6 Lớp

```mermaid
flowchart LR
    %% Bảng màu trực quan chuẩn hóa cho các tầng kiến trúc
    classDef l1 fill:#E1F5FE,stroke:#0288D1,stroke-width:1.5px,color:#01579B,rx:6px,ry:6px;
    classDef l2 fill:#F1F5F9,stroke:#64748B,stroke-width:1.5px,color:#0F172A,rx:6px,ry:6px;
    classDef l3 fill:#EDE7F6,stroke:#5E35B1,stroke-width:1.5px,color:#311B92,rx:6px,ry:6px;
    classDef l4 fill:#E8F5E9,stroke:#2E7D32,stroke-width:1.5px,color:#1B5E20,rx:6px,ry:6px;
    classDef bi fill:#FCE4EC,stroke:#C2185B,stroke-width:1.5px,color:#880E4F,rx:6px,ry:6px;
    classDef ml fill:#FFF3E0,stroke:#EF6C00,stroke-width:1.5px,color:#BF360C,rx:6px,ry:6px;
    classDef db fill:#FFFFFF,stroke:#37474F,stroke-width:1.5px,color:#263238,rx:4px,ry:4px;

    %% 1. INGESTION LAYER
    subgraph L1 ["<b>1. INGESTION</b>"]
        direction TB
        S1["<b>IoT 42 Sites</b><br/>2.73M dòng • 15p"]:::l1
        S2["<b>ERA5 Weather</b><br/>850k dòng • 1h"]:::l1
        S3[("<b>Raw S3 Lake</b><br/>DVC Storage")]:::db
        S1 --> S3
        S2 --> S3
    end

    %% 2. STAGING LAYER
    subgraph L2 ["<b>2. STAGING</b>"]
        direction TB
        ST1["<b>Staging Tables</b><br/>VARCHAR Buffer"]:::l2
        ST2["<b>Grid Resampling</b><br/>Lưới chuẩn 15p"]:::l2
        ST3["<b>QA/QC Integrity</b><br/>MD5 Checksum"]:::l2
        ST1 --> ST2 --> ST3
    end

    %% 3. TRANSFORM & CLEANING
    subgraph L3 ["<b>3. TRANSFORM</b>"]
        direction TB
        T1["<b>Cascade Impute</b><br/>4 cấp (1.54M ô)"]:::l3
        T2["<b>Floor-Hour</b><br/>Khớp nối nhân quả"]:::l3
        T3["<b>GMM-IF + 5 Rules</b><br/>Lọc dị thường O&M"]:::l3
        T1 --> T2 --> T3
    end

    %% 4. DWH CORE (GALAXY SCHEMA)
    subgraph L4 ["<b>4. DWH CORE (GALAXY)</b>"]
        direction TB
        D1[("<b>fact_solar_energy_gen</b><br/>2.73M dòng • 15 phút")]:::l4
        D2[("<b>fact_weather</b><br/>850k dòng • 1 giờ")]:::l4
        D3[("<b>5 Dim Tables</b><br/>Site • Geo • Date<br/>Time • WeatherType")]:::db
        D3 -.-> D1
        D3 -.-> D2
    end

    %% NHÁNH 1: BI DATA MART & TABLEAU
    subgraph BI_Branch ["<b>NHÁNH BI DATA MART & DASHBOARDS</b>"]
        direction TB
        M_BI[("<b>bi_mart.mv_bi_mart_hourly_measures</b><br/>Nén 1h • Tiền tính PR & Loss Temp")]:::bi
        A_BI["<b>Tableau Dashboard Suite</b><br/>DB1 Executive • DB2 Loss • DB3 CBM"]:::bi
        M_BI ==> A_BI
    end

    %% NHÁNH 2: ML DATA MART & MACHINE LEARNING
    subgraph ML_Branch ["<b>NHÁNH ML DATA MART & MACHINE LEARNING</b>"]
        direction TB
        M_ML[("<b>ml_mart.ml_mart_base</b><br/>Feature Store 52 biến trễ & vật lý")]:::ml
        A_ML["<b>LightGBM Regressor</b><br/>Dự báo Đa bước H1 (15p) &rarr; H4 (60p)"]:::ml
        M_ML ==> A_ML
    end

    %% PIPELINE FLOW CONNECTIONS
    S3 ==> ST1
    ST3 ==> T1
    T3 ==> D1
    T2 ==> D2

    %% TÁCH NHÁNH SONG SONG TỪ DWH CORE
    D1 ==>|Aggregate & Pre-calc| M_BI
    D2 ==>|Join Weather 1h| M_BI

    D1 ==>|Lag Features & Normalization| M_ML
    D2 ==>|Weather Features| M_ML
```

---

## Sơ đồ 2: Luồng Điền Khuyết Nhân Quả Đa Tầng

```mermaid
flowchart TD
    classDef l1 fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1,rx:6px,ry:6px;
    classDef l2 fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20,rx:6px,ry:6px;
    classDef l3 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c,rx:6px,ry:6px;
    classDef l4 fill:#fff8e1,stroke:#f57f17,stroke-width:2px,color:#e65100,rx:6px,ry:6px;
    classDef l5 fill:#fbe9e7,stroke:#d84315,stroke-width:2px,color:#bf360c,rx:6px,ry:6px;
    classDef l6 fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#004d40,rx:6px,ry:6px;
    classDef cond fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17,rx:6px,ry:6px;

    Start(["Chuỗi Dữ liệu Chuỗi Thời gian có Ô Khuyết"]):::l1 --> CondNight{"Khung giờ ban đêm?<br/>alpha &le; -0.833° HOẶC GHI &le; 20 W/m²"}:::cond
    
    CondNight -- Đúng --> ActNight["<b>CẤP 1: CƯỠNG BỨC GÁN E = 0.0 kWh</b><br/>Xử lý 1,383,493 ô khuyết (90.05%)"]:::l3
    CondNight -- Sai --> CondLinear{"Độ dài khoảng khuyết<br/>Gap &le; 30 phút (&le; 2 bước)?"}:::cond
    
    CondLinear -- Đúng --> ActLinear["<b>CẤP 2: NỘI SUY TUYẾN TÍNH (LINEAR)</b><br/>Xử lý 53,684 ô khuyết (3.49%)"]:::l2
    CondLinear -- Sai --> CondPchip{"Độ dài khoảng khuyết<br/>45 phút &le; Gap &le; 2 giờ (3 - 8 bước)?"}:::cond
    
    CondPchip -- Đúng --> ActPchip["<b>CẤP 3: PCHIP CUBIC HERMITE SPLINE</b><br/>Bảo toàn tính đơn điệu, không vọt âm<br/>Xử lý 50,704 ô khuyết (3.30%)"]:::l4
    CondPchip -- Sai --> ActKNN["<b>CẤP 4: KHUNG MẪU LỊCH SỬ KNN KHÍ TƯỢNG</b><br/>Truy hồi ngày quá khứ cùng cụm thời tiết<br/>Xử lý 48,519 ô khuyết (3.16%)"]:::l5

    ActNight --> FloorHour["<b>CĂN CHỈNH KHÍ QUYỂN SÀN GIỜ (FLOOR-HOUR LOOKUP)</b><br/>Khớp t_gen với t_weather = floor(t_gen, 1h)<br/>Triệt tiêu 100% rò rỉ dữ liệu tương lai"]:::l6
    ActLinear --> FloorHour
    ActPchip --> FloorHour
    ActKNN --> FloorHour
    FloorHour --> EndData(["Chuỗi Dữ Liệu Sạch Hoàn Toàn 100%"]):::l2
```

---

## Sơ đồ 3: Mô Hình Hóa Kho Dữ Liệu Lược Đồ Thiên Hà

```mermaid
erDiagram
    fact_solar_energy_gen {
        bigint gen_id PK
        int site_id FK
        int geo_id FK
        int date_id FK
        int time_id FK
        float energy_generated_kwh "Sản lượng phát thực tế"
        float expected_energy_kwh "Sản lượng kỳ vọng"
        float pr_actual "Hệ số hiệu suất thô"
        float loss_temp_ratio "Tỷ lệ suy hao nhiệt"
        int anomaly_flag "Cờ dị thường (0/1)"
        string outlier_reason "Nguyên nhân ngoại lai"
    }

    fact_weather {
        bigint weather_id PK
        int geo_id FK
        int date_id FK
        int time_id FK
        float ghi_wm2 "Bức xạ tổng cộng GHI"
        float dni_wm2 "Bức xạ trực tiếp DNI"
        float dhi_wm2 "Bức xạ tán xạ DHI"
        float temperature_c "Nhiệt độ môi trường"
        float cloud_cover_pct "Độ che phủ mây (%)"
        float wind_speed_ms "Tốc độ gió (m/s)"
    }

    dim_solar_site {
        int site_id PK
        string site_name "Tên trạm phát"
        string campus "Cơ sở trực thuộc"
        float capacity_kwp "Công suất danh định"
        float tilt_angle_deg "Góc nghiêng tấm pin"
        float azimuth_deg "Hướng đặt tấm pin"
    }

    dim_geography {
        int geo_id PK
        string campus_name "Tên khuôn viên"
        float latitude "Vĩ độ địa lý"
        float longitude "Kinh độ địa lý"
        float elevation_m "Độ cao so với mực nước biển"
    }

    dim_date {
        int date_id PK
        date full_date "Ngày quan trắc"
        int year "Năm"
        int quarter "Quý"
        int month "Tháng"
        boolean is_weekend "Cờ cuối tuần"
    }

    dim_time {
        int time_id PK
        time full_time "Mốc thời gian"
        int hour_24 "Khung giờ (0-23)"
        int minute_15 "Mốc phút (0,15,30,45)"
        int time_bucket_15m "Mã định danh 15p"
    }

    dim_solar_site ||--o{ fact_solar_energy_gen : "phát điện tại"
    dim_geography ||--o{ fact_solar_energy_gen : "tọa độ trạm"
    dim_geography ||--o{ fact_weather : "tọa độ trạm thời tiết"
    dim_date ||--o{ fact_solar_energy_gen : "ngày vận hành"
    dim_date ||--o{ fact_weather : "ngày quan trắc"
    dim_time ||--o{ fact_solar_energy_gen : "mốc 15 phút"
    dim_time ||--o{ fact_weather : "mốc giờ"
```

---

## Sơ đồ 4: Kiến Trúc Nhận Diện Dị Thường Lai GMM-IF & 5 Rào Chắn Vật Lý

```mermaid
flowchart TD
    classDef l1 fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1,rx:6px,ry:6px;
    classDef l2 fill:#ede7f6,stroke:#512da8,stroke-width:2px,color:#311b92,rx:6px,ry:6px;
    classDef l3 fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20,rx:6px,ry:6px;
    classDef l4 fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#bf360c,rx:6px,ry:6px;
    classDef l5 fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#880e4f,rx:6px,ry:6px;
    classDef cond fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17,rx:6px,ry:6px;
    classDef rStyle fill:#ffebee,stroke:#c62828,stroke-width:1px,color:#b71c1c,rx:4px,ry:4px;

    RawInput["<b>Dữ liệu Vận hành Thực tế</b><br/>(E_act, GHI, DNI, DHI, Temp)"]:::l1 --> CART["<b>TẦNG 1: PHÂN ĐOẠN KHÔNG GIAN THỜI TIẾT CART</b><br/>(Decision Tree max_depth=5, min_samples=500)<br/>Triệt tiêu tính phi tuyến, gom cụm vi khí hậu (R² ~ 0.758)"]:::l2

    CART --> LeafClusters["Các Cụm Lá Cục Bộ Đồng Nhất"]:::l2
    LeafClusters --> GMM["<b>TẦNG 2: MÔ HÌNH HỖN HỢP GAUSS CỤC BỘ (GMM)</b><br/>(K=2 components tối ưu theo BIC)<br/>Đánh dấu cờ dị thường cục bộ: p(x) &lt; 0.02"]:::l3

    RawInput --> IF["<b>TẦNG 3: RỪNG CÔ LẬP TOÀN CỤC (ISOLATION FOREST)</b><br/>(n_estimators=100, contamination=0.03)<br/>Phát hiện các điểm bất thường nằm ở đuôi phân bố"]:::l4

    GMM --> MergeFlags["Tổng Hợp Cờ Ứng Viên Dị Thường<br/>(gmm_flag OR if_flag)"]:::l5
    IF --> MergeFlags

    MergeFlags --> PhysicsRules{"<b>TẦNG 4: HỆ THỐNG 5 RÀO CHẮN VẬT LÝ</b><br/>(Physical Boundaries & Validation)"}:::cond

    PhysicsRules -- Rule 1 --> R1["<b>PHYSICAL_NIGHT_POSITIVE</b><br/>alpha &le; -0.833° &amp; E &gt; 0.05 kWh<br/>&rarr; Gán cờ lỗi rò rỉ CT cảm biến"]:::rStyle
    PhysicsRules -- Rule 2 --> R2["<b>PHYSICAL_OVER_CAPACITY</b><br/>E &gt; P_stc * 0.25 * 1.20<br/>&rarr; Gán cờ lỗi vượt trần dung sai"]:::rStyle
    PhysicsRules -- Rule 3 --> R3["<b>PHYSICAL_ZERO_DAYLIGHT</b><br/>GHI &ge; 100 W/m² &amp; E == 0<br/>&rarr; Gán cờ lỗi mất phát ban ngày"]:::rStyle
    PhysicsRules -- Rule 4 --> R4["<b>PHYSICAL_LOW_ENERGY_STRONG_SUN</b><br/>GHI &ge; 700 &amp; E &lt; 5% P95<br/>&rarr; Gán cờ lỗi Inverter ngắt quá nhiệt"]:::rStyle
    PhysicsRules -- Rule 5 --> R5["<b>PHYSICAL_DISTRIBUTION_JUMP</b><br/>Nhảy &gt; 4*IQR &amp; delta &ge; 15% P95<br/>&rarr; Gán cờ lỗi truyền thông SCADA"]:::rStyle

    R1 --> SafeDB["<b>Cập nhật Nhãn Dị thường An toàn 4 Bước lên Data Warehouse</b><br/>(104 Giờ Ngoại lai - Tỷ lệ 0.45% Toàn mạng lưới)"]:::l3
    R2 --> SafeDB
    R3 --> SafeDB
    R4 --> SafeDB
    R5 --> SafeDB
```

---

## Sơ đồ 5: Kiến Trúc Tầng Phục Vụ BI Mart & Đồng Bộ Tableau Desktop

```mermaid
flowchart LR
    classDef dwh fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b,rx:6px,ry:6px;
    classDef mart fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#880e4f,rx:6px,ry:6px;
    classDef tab fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20,rx:6px,ry:6px;

    subgraph DWH["PostgreSQL Data Warehouse (Supabase)"]
        FactGen["fact_solar_energy_gen<br/>(2.73M bản ghi 15p)"]:::dwh
        FactWeather["fact_weather<br/>(850k bản ghi 1h)"]:::dwh
        DimSite["dim_solar_site"]:::dwh
    end

    subgraph BIMart["Serving Layer (Materialized Views)"]
        MVHourly["<b>mv_bi_mart_hourly_measures</b><br/>- Nén độ hạt: 15 phút &rarr; 1 giờ<br/>- Tiền tính: PR actual, PR adjusted, Loss Temp<br/>- Dung lượng: &lt; 80 MB (RAM Cached)<br/>- Độ trễ: &lt; 100 ms"]:::mart
        MVDaily["<b>mv_bi_mart_daily_kpis</b><br/>- Cấp ngày: Total kWh, CF, Yield, CO2, Revenue"]:::mart
    end

    subgraph TableauSuite["Bộ 3 Dashboard Tableau Desktop (&lt; 2s Load Time)"]
        DB1["<b>Dashboard 1: Executive Overview</b><br/>(Ban Quản trị: BANs, CF 28 tháng, Tỷ trọng 5 cơ sở)"]:::tab
        DB2["<b>Dashboard 2: Efficiency & Loss</b><br/>(Kỹ sư Năng lượng: PR, Suy hao nhiệt, Kỹ thuật lắp đặt)"]:::tab
        DB3["<b>Dashboard 3: Anomaly Detection & CBM</b><br/>(Kỹ sư O&M: Điểm đỏ Outlier, Ma trận chẩn đoán 30s)"]:::tab
    end

    FactGen -->|Refresh View| MVHourly
    FactWeather -->|Join Khớp giờ| MVHourly
    DimSite -->|Star Schema| MVHourly
    MVHourly -->|Rollup Ngày| MVDaily

    MVHourly -->|Direct Connect| DB2
    MVHourly -->|Direct Connect| DB3
    MVDaily -->|Direct Connect| DB1
```

---

## Sơ đồ 6: Đường Ống Huấn Luyện & Suy Luận Machine Learning

```mermaid
flowchart TD
    classDef l1 fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1,rx:6px,ry:6px;
    classDef l2 fill:#ede7f6,stroke:#512da8,stroke-width:2px,color:#311b92,rx:6px,ry:6px;
    classDef l3 fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20,rx:6px,ry:6px;
    classDef l4 fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#bf360c,rx:6px,ry:6px;
    classDef l5 fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#880e4f,rx:6px,ry:6px;
    classDef l6 fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#004d40,rx:6px,ry:6px;

    DataIn["<b>Dữ liệu Sạch Lớp 3 &amp; Feature Store</b>"]:::l1 --> TargetNorm["<b>CHUẨN HÓA MỤC TIÊU VẬT LÝ</b><br/>k(t) = E(t) / [P_stc * sin(alpha(t))]<br/>Triệt tiêu quỹ đạo hình sin tự nhiên"]:::l1
    
    TargetNorm --> FeatEng["<b>KỸ NGHỆ 40 ĐẶC TRƯNG VẬT LÝ &amp; TRỄ</b><br/>- Khí tượng: GHI, DNI, DHI, Temp, Gió, Mây<br/>- Thiên văn: Góc nâng alpha, Góc thiên đỉnh, Air Mass AM1.5<br/>- Chuỗi thời gian: Lags (15p, 30p, 1h, 24h), Rolling Mean/Std<br/>- Không gian: Tọa độ, Độ cao, Dung lượng trạm"]:::l2

    FeatEng --> VIFDiag["<b>SÀNG LỌC ĐA CỘNG TUYẾN (VIF DIAGNOSTICS)</b><br/>Loại bỏ biến VIF &ge; 10 &rarr; Giữ lại tập đặc trưng tối ưu"]:::l3

    VIFDiag --> TrainLGBM["<b>HUẤN LUYỆN LIGHTGBM REGRESSOR</b><br/>- Hàm mất mát: Huber Loss (delta = 1.0)<br/>- Tối ưu siêu tham số: Optuna Bayesian TPE<br/>- 5-Fold Time-Series Cross Validation"]:::l4

    TrainLGBM --> Inference["<b>SUY LUẬN ĐA TẦM DỰ BÁO (MULTI-HORIZON)</b><br/>- H1: T + 15 phút (WAPE = 17.46%, R² = 0.9293)<br/>- H4: T + 60 phút (WAPE = 21.60%, R² = 0.8953)"]:::l5

    Inference --> InverseTrans["<b>BIẾN ĐỔI NGƯỢC VỀ ĐƠN VỊ KWH</b><br/>E_pred(t) = k_pred(t) * P_stc * sin(alpha(t))<br/>Kẹp trần an toàn [0, max_physical_kwh]"]:::l6

    InverseTrans --> FinalMetrics["<b>Kiểm định Khả năng Giải thích (SHAP &amp; XAI)</b><br/>Xuất kết quả phục vụ điều độ phụ tải và vận hành Pin lưu trữ BESS"]:::l3
```

---

<div align="center">
  <i>Tài liệu sơ đồ kỹ thuật được chuẩn hóa bởi <b>The Outliers Team</b> — Đồ án Tốt nghiệp Chuyên ngành Xử lý Dữ liệu</i>
</div>


