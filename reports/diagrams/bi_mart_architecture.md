# Kiến Trúc Tầng BI Data Mart & Nguyên Tắc Thiết Kế UI/UX Gestalt (Slide 14)

Tài liệu kỹ thuật giải thích chi tiết sơ đồ kiến trúc chuyển đổi từ Data Warehouse sang Tầng BI Data Mart (Materialized Views), nguyên tắc thiết kế nhận thức Gestalt và bảng màu ngữ nghĩa đạt chuẩn WCAG 2.1 AA phục vụ 3 Dashboard trên Tableau.

---

## 1. Sơ đồ Kiến trúc Tổng quan (Mermaid Flowchart)

```mermaid
flowchart TD
    classDef dwhStyle fill:#eff6ff,stroke:#3b82f6,stroke-width:2px,color:#1e3a8a;
    classDef mvStyle fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#14532d;
    classDef tabStyle fill:#faf5ff,stroke:#8b5cf6,stroke-width:2px,color:#4c1d95;
    classDef uiStyle fill:#fdf2f8,stroke:#db2777,stroke-width:2px,color:#831843;

    subgraph DWH ["1. DATA WAREHOUSE LAYER [Schema: datawarehouse - 3.5M Dòng]"]
        FACT_GEN["fact_solar_energy_gen (2.731.946 dòng - Chu kỳ 15m)<br>• PK: gen_id | FK: site_id, geo_id, date_id, time_id<br>• energy_generated_kwh, gmm_if_outlier_flag"]:::dwhStyle
        FACT_W["fact_weather (850.752 dòng ERA5-Land - Chu kỳ 1h)<br>• PK: weather_id | FK: geo_id, date_id, time_id<br>• shortwave_radiation, temp_c, cloud_cover, wind_speed"]:::dwhStyle
        DIMS["5 Conformed Dimensions:<br>• dim_solar_site | dim_geography | dim_date | dim_time | dim_weather_type"]:::dwhStyle
    end

    subgraph BIMART ["2. BI DATA MART LAYER [Schema: bi_mart - Materialized Views Tối Ưu]"]
        MV1["<b>mv_bi_mart_hourly_measures (Cấp Giờ - 1h)</b><br>• Nén 15m → 1h (hourly_bucket) & Ghép nối Causal Join thời tiết<br>• Đo lường: e_hourly, shortwave_radiation, temp_c, t_cell<br>• Hiệu suất & Suy hao: e_stc_hourly, loss_temp, pr_actual, pr_adjusted, e_expected<br>• Tài chính & Môi trường: estimated_revenue (FiT 1.938 đ), cost_of_underperformance, co2_avoided<br>• Sự cố: gmm_if_outlier_flag, gmm_if_outlier_reason<br>• Index: idx_mv_hourly_unique (date_id, site_id, hourly_bucket)"]:::mvStyle
        MV2["<b>mv_bi_mart_daily_kpis (Cấp Ngày & Lũy Kế)</b><br>• Aggregation cấp ngày từ mv_hourly cho 42 trạm phát<br>• KPIs ngày: e_daily, e_stc_daily, daily_pr_actual, daily_pr_adjusted, capacity_factor, yield_ratio<br>• Time-Intelligence Window Functions: wtd_energy (Tuần), mtd_energy/revenue (Tháng), ytd_energy/revenue (Năm)<br>• Tự động làm mới: REFRESH MATERIALIZED VIEW CONCURRENTLY<br>• Index: idx_mv_daily_unique (date_id, site_id)"]:::mvStyle
    end

    subgraph SERVING ["3. APPLICATION SERVING LAYER [Tableau Native Pooler]"]
        TAB_CONN["Supabase Connection Pooler IPv4 (Port 5432 / TLS SSL)<br>• User Least Privilege: tableau_user (Read-only bi_mart)<br>• Tableau Relationships (1:N) triệt tiêu lỗi Fan-out<br>• Tốc độ phản hồi: < 100 ms (Zero Lag)"]:::tabStyle
        D1["Dashboard 1: Executive Overview<br>• BANs tổng quan, Campus Map, Lũy kế"]:::tabStyle
        D2["Dashboard 2: Efficiency & Loss Analysis<br>• Tổn thất nhiệt, Suy hao, Xếp hạng thiết bị"]:::tabStyle
        D3["Dashboard 3: Anomaly Detection & O&M<br>• Cờ GMM-IF, Dòng rò ban đêm E > 0"]:::tabStyle
    end

    subgraph GESTALT ["4. NGUYÊN TẮC UI/UX GESTALT & WCAG 2.1 AA"]
        G1["• Luật Gần Nhau (Proximity): Card-based Container viền #E2E8F0 gom cụm thông tin<br>• Luật Đồng Nhất (Similarity): Đồng nhất kiểu dáng, icon, màu sắc trạng thái<br>• Tối đa Tỷ số Data-Ink: Loại bỏ rác thị giác, làm mờ lưới phụ, tập trung vào đường cong & dị thường<br>• Bố cục F-Pattern: BANs dải trên cùng (18-24pt) → Bản đồ → Phân tích chi tiết"]:::uiStyle
        COLORS["<b>Bảng màu Ngữ nghĩa WCAG 2.1 AA (≥ 4.5:1):</b><br>🔵 Classic Teal (#4E79A7 / #76B7B2 | 7.2:1): Sản lượng chuẩn & BANs cốt lõi<br>🟡 Solar Orange (#F28E2B / #EDC948 | 4.8:1): Bức xạ mặt trời GHI & Tổn thất nhiệt<br>🔴 Danger Red (#E15759 | 5.1:1): Cờ ngoại lai GMM-IF & Dòng rò ban đêm (Độc quyền)<br>🟢 Eco Green (#59A14F | 4.9:1): Trạng thái tối ưu PR ≥ 75%, CF, Tín chỉ CO2<br>⚪ Slate Gray (#79706E / #E2E8F0 | 4.6:1): Reference Lines & Viền khung thẻ"]:::uiStyle
    end

    FACT_GEN -->|Nén 15m sang 1h & Causal Join| MV1
    FACT_W -->|Ghép nối thời tiết 1h| MV1
    DIMS -.->|Kế thừa thuộc tính| MV1
    MV1 -->|Tổng hợp cấp ngày & Window Functions| MV2
    MV1 -->|Phục vụ phân tích cấp giờ| TAB_CONN
    MV2 -->|Phục vụ phân tích cấp ngày & BANs| TAB_CONN
    TAB_CONN --> D1
    TAB_CONN --> D2
    TAB_CONN --> D3
    GESTALT -.->|Quy chuẩn thiết kế giao diện| SERVING
```

---

## 2. So Sánh Chiến Lược Kiến Trúc Tầng BI

| Tiêu Chí Đánh Giá | Standard View (View Thường) | Bảng Vật Lý Riêng (Physical Table) | PostgreSQL Materialized Views (Dự Án Chọn) |
| :--- | :--- | :--- | :--- |
| **Cơ chế hoạt động** | Truy vấn ảo, thực thi lại SQL JOIN mỗi khi mở Dashboard | Bảng vật lý độc lập được tạo bởi pipeline ETL | Lưu cache kết quả tiền tổng hợp (Pre-aggregated) vào đĩa |
| **Tốc độ phản hồi Tableau** | 🔴 Chậm (5 – 10 giây/lần lọc) | 🟢 Nhanh (< 100 ms) | 🟢 **Rất Nhanh (< 100 ms)** |
| **Tiêu thụ tài nguyên DB** | 🔴 Cao (Nghẽn CPU/RAM Supabase khi nhiều user query) | 🟡 Trung bình (Tốn dung lượng đĩa gấp đôi) | 🟢 **Tối ưu (Đọc trực tiếp từ Index đĩa)** |
| **Tính nhất quán dữ liệu** | 🟢 100% Realtime | 🔴 Dễ bị lệch sync nếu pipeline ETL bị gián đoạn | 🟢 **Nhất quán tuyệt đối qua REFRESH CONCURRENTLY** |
| **Hỗ trợ Index** | ❌ Không hỗ trợ Index trực tiếp trên View | 🟢 Có hỗ trợ Index | 🟢 **Tích hợp Unique Composite Index** |

---

## 3. Cấu Trúc Hai Materialized Views Cốt Lõi

### 3.1. `bi_mart.mv_bi_mart_hourly_measures` (Cấp Giờ - 1h Granularity)
* **Khóa chính / Unique Index:** `idx_mv_hourly_unique (date_id, site_id, hourly_bucket)`
* **Công thức Kỹ thuật Lõi:**
  * Nhiệt độ ô pin ($T_{\text{cell}}$):
    $$T_{\text{cell}} = T_{\text{ambient}} + \left(GHI \times 0.035\right)$$
  * Sản lượng danh định chuẩn STC ($E_{\text{stc}}$):
    $$E_{\text{stc}} = P_{\text{stc}} \times \left(\frac{GHI}{1000}\right) \quad (\text{khi } GHI \ge 100\,\text{W/m}^2)$$
  * Hệ số suy hao nhiệt độ ($\text{Loss}_{\text{temp}}$):
    $$\text{Loss}_{\text{temp}} = \max\left(0, (T_{\text{cell}} - 25) \times 0.004\right)$$
  * Hiệu suất thực tế ($PR_{\text{actual}}$) & Hiệu suất điều chỉnh ($PR_{\text{adjusted}}$):
    $$PR_{\text{actual}} = \frac{E_{\text{hourly}}}{E_{\text{stc}}}, \quad PR_{\text{adjusted}} = 0.78 \times \left(1 - \text{Loss}_{\text{temp}}\right)$$
  * Sản lượng kỳ vọng ($E_{\text{expected}}$):
    $$E_{\text{expected}} = E_{\text{stc}} \times PR_{\text{adjusted}}$$
  * Doanh thu FiT ($1.938\,\text{VNĐ/kWh}$) & Chi phí thiếu hụt công suất:
    $$\text{Revenue} = E_{\text{hourly}} \times 1.938, \quad \text{Cost}_{\text{underperformance}} = \max\left(0, E_{\text{expected}} - E_{\text{hourly}}\right) \times 1.938$$
  * Tín chỉ môi trường ($0.533\,\text{kg CO}_2\text{/kWh}$, $21.8\,\text{kg/cây}$):
    $$\text{CO}_{2\text{ avoided}} = E_{\text{hourly}} \times 0.533\,\text{kg}, \quad \text{Trees} = \frac{\text{CO}_{2\text{ avoided}}}{21.8}$$

### 3.2. `bi_mart.mv_bi_mart_daily_kpis` (Cấp Ngày & Time-Intelligence)
* **Khóa chính / Unique Index:** `idx_mv_daily_unique (date_id, site_id)`
* **Hàm cửa sổ lũy kế thời gian (Time-Intelligence Window Functions):**
  * `wtd_energy`: $\sum E_{\text{daily}}$ theo tuần (Week-to-Date).
  * `mtd_energy` & `mtd_revenue`: $\sum E_{\text{daily}}$ & $\sum \text{Revenue}$ theo tháng (Month-to-Date).
  * `ytd_energy` & `ytd_revenue`: $\sum E_{\text{daily}}$ & $\sum \text{Revenue}$ theo năm (Year-to-Date).
* **Chỉ số công suất:**
  $$\text{Capacity Factor (CF)} = \frac{E_{\text{daily}}}{P_{\text{stc}} \times 24\,\text{h}}, \quad \text{Specific Yield} = \frac{E_{\text{daily}}}{P_{\text{stc}}}$$

---

## 4. Bảng Màu Ngữ Nghĩa & Chuẩn Tương Phản WCAG 2.1 AA

| Tên Màu & Mã Hex | Mẫu Màu | Tỷ Lệ Tương Phản | Vai Trò & Ứng Dụng Trong Tableau Dashboard |
| :--- | :---: | :---: | :--- |
| **Classic Teal / Navy**<br>`#4E79A7` & `#76B7B2` | 🟦 | **7.2 : 1**<br>*(Đạt chuẩn AAA)* | Đường xu hướng sản lượng thực tế $e_{\text{hourly}}$, BANs tổng sản lượng, đường hiệu suất điều chỉnh nhiệt $PR_{\text{adjusted}}$. |
| **Solar Orange / Yellow**<br>`#F28E2B` & `#EDC948` | 🟧 | **4.8 : 1**<br>*(Đạt chuẩn AA)* | Bức xạ sóng ngắn $GHI$, nhiệt độ ô pin $T_{\text{cell}}$, cảnh báo suy giảm nhẹ ($50\% \le PR < 75\%$). |
| **Alert Danger Red**<br>`#E15759` | 🟥 | **5.1 : 1**<br>*(Đạt chuẩn AA)* | **Độc quyền** đánh dấu cờ bất thường GMM-IF, dòng rò ban đêm ($E > 0$), sụt giảm nặng ($PR < 50\%$). |
| **Eco Success Green**<br>`#59A14F` | 🟩 | **4.9 : 1**<br>*(Đạt chuẩn AA)* | Trạng thái tối ưu ($PR \ge 75\%$), Hệ số công suất CF, Tín chỉ xanh $\text{CO}_2$ & Cây xanh. |
| **Neutral Slate Gray**<br>`#79706E` & `#E2E8F0` | ⬜ | **4.6 : 1**<br>*(Đạt chuẩn AA)* | Trục tọa độ, Reference Lines chuẩn, khung viền Container thẻ Card, nhãn thông số phụ trợ. |
