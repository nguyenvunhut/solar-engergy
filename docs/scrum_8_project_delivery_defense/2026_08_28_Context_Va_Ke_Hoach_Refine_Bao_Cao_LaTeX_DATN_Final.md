# TÀI LIỆU CONTEXT & KẾ HOẠCH TOÀN DIỆN PHỤC VỤ REFINE BÁO CÁO TỐT NGHIỆP LATEX (`DATN_REPORT_FINAL_02.tex`)

> **Dự án:** Hệ thống Xử lý Dữ liệu, Nhận diện Dị thường Vận hành và Dự báo Sản lượng 42 Trạm Điện Mặt Trời Áp mái (Đại học La Trobe, Úc)  
> **Nhóm thực hiện:** The Outliers — Chuyên ngành Phân tích & Xử lý Dữ liệu (Data Analytics)  
> **Tài liệu mục tiêu xử lý chính thức:** [`reports/DATN_REPORT_FINAL_03.tex`](file:///d:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/reports/DATN_REPORT_FINAL_03.tex) ($5.406$ dòng, $386\,\text{KB}$)  
> **Tài liệu gốc lưu trữ an toàn (Backup):** [`reports/DATN_REPORT_FINAL_02.tex`](file:///d:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/reports/DATN_REPORT_FINAL_02.tex)  
> **Tài liệu tham chiếu chuẩn:**  
> - [`docs/scrum_8_project_delivery_defense/2026_08_28_Bao_Cao_Tong_Hop_Toan_Dien_Domain_Data_AI_Defense_Master.md`](file:///d:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/docs/scrum_8_project_delivery_defense/2026_08_28_Bao_Cao_Tong_Hop_Toan_Dien_Domain_Data_AI_Defense_Master.md)  
> - [`docs/scrum_8_project_delivery_defense/2026_08_25_Bao_Cao_Dinh_Luong_Chi_Tiet_Insights_Va_De_Xuat_Cai_Tien_Audited.md`](file:///d:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/docs/scrum_8_project_delivery_defense/2026_08_25_Bao_Cao_Dinh_Luong_Chi_Tiet_Insights_Va_De_Xuat_Cai_Tien_Audited.md)  
> - [`docs/scrum_8_project_delivery_defense/2026_08_26_Brief_Thiet_Ke_Streamlit_What_If_Optimization_Dashboard.md`](file:///d:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/docs/scrum_8_project_delivery_defense/2026_08_26_Brief_Thiet_Ke_Streamlit_What_If_Optimization_Dashboard.md)  
> - DDL SQL Kho Dữ liệu: [`srcs/00_database/sql/create_datawarehouse.sql`](file:///d:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/srcs/00_database/sql/create_datawarehouse.sql)

---

## 1. BỘ SỐ LIỆU KIỂM TOÁN CHUẨN CỦA DỰ ÁN (100% AUDITED GROUND TRUTH)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              BỘ SỐ LIỆU KIỂM TOÁN CHUẨN XUYÊN SUỐT TOÀN DỰ ÁN                          │
├────────────────────────────────┬───────────────────────────────────────────────────────────────────────┤
│ Quy mô danh mục trạm           │ 42 trạm áp mái độc lập tại 5 Campus Đại học La Trobe, Victoria, Úc     │
│ Phân bổ công suất theo Campus  │ Bundoora: 1.540 kWp (26 trạm) | Bendigo: 510 kWp (8 trạm)             │
│                                │ Albury-Wodonga: 240 kWp (4 trạm) | Shepparton: 78 kWp (2 trạm)        │
│                                │ Mildura: 60 kWp (2 trạm)                                              │
│ Cụm trạm lắp phẳng mái bằng 0° │ 970 kWp (Chịu suy hao đọng bùn viền nhôm đáy và góc chiếu mùa đông)  │
│ Tổng công suất danh định DC    │ P_STC = 2.428 kWp (2,43 MWp theo chuẩn IEC 60904-3)                  │
├────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
│ Dữ liệu viễn thám thực tế 28th │ 2.731.946 dòng SCADA 15 phút (01/01/2020 - 30/04/2022)                │
│ Dữ liệu khí tượng ERA5 1 giờ   │ 850.752 dòng (GHI, DNI, DHI, Temp, Wind, Cloud, Rain, Sunshine)       │
│ Dữ liệu BI Mart MV Cấp giờ     │ 683.665 dòng (bi_mart.mv_bi_mart_hourly_measures)                     │
├────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
│ SỐ LIỆU NGOẠI LAI THỰC TẾ DB   │ • fact_solar_energy_gen (15m): 7.431 dòng dị thường (0,2720%)         │
│ (Kiểm toán trực tiếp Supabase) │ • bi_mart.mv_bi_mart_hourly_measures (1h): 5.638 giờ dị thường (0,825%)│
│                                │ • GMM_IF_CONSENSUS: 5.556 dòng | PHYSICAL_DISTRIBUTION_JUMP: 1.211 dòng│
├────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
│ ĐƯỜNG CƠ SỞ VẬN HÀNH 12 THÁNG  │ • Sản lượng phát cơ sở: 3.447.760 kWh/năm (3,45 GWh/năm)               │
│ (12-Month Normalized Baseline) │ • Hệ số hiệu suất danh định: PR_baseline = 75,40% (Class B)           │
│ [Mốc quy chiếu tính toán What- │ • Hệ số công suất tải: CF_baseline = 16,21%                           │
│  If, Doanh thu và Hoàn vốn]    │ • Năng suất riêng: Specific Yield = 1.420 kWh/kWp/năm                 │
│                                │ • Doanh thu / Tiết kiệm tiền điện: 700.000 AUD/năm                    │
│                                │ • Cắt giảm phát thải Scope 2 NGA: 2.827 tấn CO2/năm (0,82 kg/kWh)     │
├────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
│ KẾT QUẢ MÔ HÌNH HỌC MÁY        │ • LightGBM Regressor trên đại lượng k(t) = E / [P_stc * sin(elev)]    │
│ (Kiểm định tập test niêm phong)│ • WAPE (measured_daylight): 17,73% (h1: T+15m) | 22,58% (h4: T+60m)   │
│                                │ • Hệ số xác định R²: 0,9283 (h1) | 0,8964 (h4)                        │
│                                │ • Skill Score vượt trội Prophet: +48,73% (h1) | +35,89% (h4)          │
│                                │ • XAI TreeSHAP: Bức xạ GHI và sin(elevation) chiếm > 67,3% trọng số  │
├────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
│ KẾT QUẢ MÔ PHỎNG WHAT-IF       │ • Sản lượng sau tối ưu: 4.695.534 kWh/năm (4,70 GWh/năm, +36,18%)     │
│ (Tổng hợp 6 đề xuất kỹ thuật)  │ • Hệ số hiệu suất hệ thống: PR tăng lên 88,62% (Class A Quốc tế)      │
│                                │ • Doanh thu / Tiết kiệm ròng: 1.151.509 AUD/năm (+451.509 AUD/năm)   │
│                                │ • Cắt giảm phát thải khí nhà kính: 3.850 tấn CO2/năm (+1.023 tấn CO2) │
│                                │ • Tổng vốn đầu tư (CapEx): 1.300.280 AUD (BESS: 1.25M AUD, Khác: 50.2k)│
│                                │ • Thời gian hoàn vốn có trọng số (Payback): 3,15 NĂM (ROI > 270%)     │
└────────────────────────────────┴───────────────────────────────────────────────────────────────────────┘
```

---

## 2. KIẾN TRÚC LAKEHOUSE 6 LỚP THEO TẦNG CHỨC NĂNG (FUNCTIONAL LAYERS)

> **Quy chuẩn:** Tuyệt đối không dùng tên kim loại (Bronze, Silver, Gold), mà sử dụng định danh 6 Tầng Chức Năng:

1. **Layer 1 -- Tầng Thu Nạp Nguồn Dữ Liệu (Data Source / Ingestion Layer):**
   * 5 tệp CSV gốc ($158\,\text{MB}$): $2.731.946$ dòng Solar SCADA 15p, $850.752$ dòng Open-Meteo ERA5 1h, 42 trạm Metadata, Lịch Calendar, Campus Meta.
   * Lưu trữ bất biến (*Immutable Append-Only*) trên MinIO Object Storage (Local Docker) và Supabase S3 Storage (Cloud).
2. **Layer 2 -- Tầng Đệm Tiếp Nhận (Staging Buffer Layer):**
   * Schema `staging.stg_*` định dạng $100\%$ trường sang `VARCHAR(255)` để tiếp nhận an toàn, chống lỗi ép kiểu (*Type Cast Failure*), kiểm định toàn vẹn bằng MD5 Checksum.
3. **Layer 3 -- Tầng Chuyển Đổi & Làm Sạch (Transformation Buffer Layer):**
   * Schema `staging` buffer (`staging.dim_*`, `staging.fact_*`).
   * Thuật toán **Floor-Hour Causal Lookup** ($\Delta t = t_{\text{weather}} - t_{\text{solar}} \le 0$) chống rò rỉ thông tin tương lai (*Data Leakage*).
   * Chuỗi điền khuyết **Causal Cascade Hybrid Imputation 4 cấp độ** ($1.383.493$ ô ban đêm gán $0\,\text{kWh}$ theo góc nâng $\alpha \le -0{,}833^\circ$, nội suy tuyến tính, PCHIP Spline Hermite, hồi quy tương quan không gian).
   * Mô hình nhận diện dị thường lai **GMM-IF kết hợp 5 Rào chắn Vật lý**.
4. **Layer 4 -- Tầng Kho Dữ Liệu Trung Tâm (Data Warehouse Core Layer):**
   * Schema `datawarehouse` theo **Lược đồ Thiên hà (Galaxy Schema / Fact Constellation)**:
     - 2 Facts: `fact_solar_energy_gen` ($2.731.946$ dòng 15p), `fact_weather` ($850.752$ dòng 1h).
     - 4 Conformed Dims: `dim_geography` (5 campuses), `dim_date` (2.312 ngày), `dim_time` (96 mốc 15p), `dim_weather_type` (22 mã WMO).
     - 1 Specific Dim: `dim_solar_site` (42 trạm).
     - Phân vùng bảng theo năm: `PARTITION BY RANGE (date_id)` [2020, 2021, 2022] với Partition Pruning giảm $66\%$ quét đĩa, hạ độ trễ từ $1.850\,\text{ms} \to 42\,\text{ms}$.
5. **Layer 5 -- Tầng Phục Vụ Siêu Thị Dữ Liệu (Serving Data Marts Layer):**
   * `bi_mart`: Các Materialized Views (`mv_bi_mart_hourly_measures`, `mv_bi_mart_daily_kpis`) tối ưu hóa tính toán trước các chỉ số PR, Specific Yield, CF, chi phí tổn thất, kết nối qua cổng điều phối kết nối **PgBouncer port 6543**.
   * `ml_mart`: Lưu trữ dưới định dạng Parquet nén Snappy làm Feature Store 52 đặc trưng phục vụ huấn luyện mô hình học máy.
6. **Layer 6 -- Tầng Ứng Dụng & Hành Động (Action & Operational BI Layer):**
   * Hệ thống 3 Dashboard Tableau Desktop phân tích quản trị và vận hành O&M.
   * Ứng dụng tương tác Streamlit 2 Trang (`pages/1_ML.py` và `pages/2_What_If.py`).
   * Hệ thống điều động bảo trì tự động CMMS theo chuẩn CBM ISO 13374.

---

## 3. TRI THỨC MIỀN NGHIỆP VỤ (DOMAIN FUNDAMENTALS & 5 AD-HOC CASES)

### 3.1. Domain Fundamentals (Nền tảng Vật lý Quang điện)
* **Hiệu ứng Quang điện P-N:** Chuyển đổi photon ánh sáng thành cặp electron-lỗ trống tạo dòng điện một chiều DC.
* **Suy hao Nhiệt độ Cell ($\gamma = -0{,}38\%/^\circ\text{C}$):** Khi trời nắng to, nhiệt độ bề mặt tấm pin tăng vọt lên $68^\circ\text{C} - 72^\circ\text{C}$ ($T_{\text{cell}} = T_{\text{ambient}} + GHI \times 0{,}03$). Mỗi $1^\circ\text{C}$ vượt mốc tiêu chuẩn $25^\circ\text{C}$ làm suy giảm $-0{,}38\%$ công suất phát $\implies Loss_{\text{temp}} = 14{,}80\%$ toàn trạm ($510.268\,\text{kWh/năm}$).
* **Cắt ngọn Biến tần (Inverter Clipping $\text{ILR} = 1{,}25$):** Tỷ lệ công suất mảng pin DC lớn hơn định mức AC của biến tần khiến biến tần tự dịch điểm làm việc $V_{\text{mpp}} \to V_{\text{oc}}$ để ghìm công suất đỉnh phẳng (Flat-top) $\implies Loss_{\text{clip}} = 2{,}30\%$ ($79.298\,\text{kWh/năm}$).

### 3.2. Năm Dị Thường Ad-hoc Thực Địa Được Bóc Tách Trong Pipeline (Chương 4)
1. **Case 1 (Cắt đêm vật lý - Night Zero):** Hiện tượng trôi điểm 0 cảm biến dòng CT ban đêm hoặc dòng rò vi xử lý biến tần $\implies$ Cắt đêm vật lý $E = 0\,\text{kWh}$ khi góc nâng mặt trời $\alpha \le -0{,}833^\circ$ hoặc $GHI \le 20\,\text{W/m}^2$ (xử lý $1.383.493$ ô khuyết, $90{,}05\%$).
2. **Case 2 (Ngắt quá áp lưới trưa hè - AS/NZS 4777.2):** Tiêu chuẩn hòa lưới điện Úc quy định biến tần ngắt mạch khẩn cấp trong $0{,}2\,\text{giây}$ khi điện áp lưới hạ thế vượt ngưỡng $V_{10\text{min}} \ge 258\,\text{V}$ $\implies$ Bóc tách cờ `PHYSICAL_LOW_ENERGY_STRONG_SUN` (trời nắng gắt $GHI \ge 700\,\text{W/m}^2$ nhưng trạm mất điện đột ngột).
3. **Case 3 (Đứt cầu chì chuỗi DC / Hỏng diode bypass):** Một chuỗi pin bị hở mạch hoặc đứt cầu chì tủ Combiner Box khiến công suất trạm sụt giảm cục bộ $33\% - 66\%$ $\implies$ Bóc tách cờ `PHYSICAL_DISTRIBUTION_JUMP` ($1.211$ bản ghi).
4. **Case 4 (Cường hóa mép mây - Cloud Enhancement):** Hiện tượng phản xạ ánh sáng từ rìa mây tích làm bức xạ $GHI$ vọt tức thời vượt hằng số mặt trời ($> 1.300\,\text{W/m}^2$) $\implies$ Kẹp trần công suất an toàn $E_{\text{max}} = P_{\text{stc}} \times 0{,}25 \times 1{,}20$ và bóc tách cờ `PHYSICAL_OVER_CAPACITY`.
5. **Case 5 (Đọng bùn viền nhôm $970\,\text{kWp}$ mái bằng $0^\circ$ - Soiling Dams):** Mái bằng không có độ dốc tự làm sạch, nước mưa đọng bùn tại gờ nhôm đáy tấm pin che khuất hàng cell dưới cùng, kích hoạt diode bypass làm sụt $33\%$ công suất chuỗi $\implies$ Luận cứ cho đề xuất nâng khung chữ A $15^\circ$.

---

## 4. KHUNG CHỈ SỐ BI (IEC 61724-1) & BỐ TRÍ TRỰC QUAN HÓA

### 4.1. Bộ Ba Biến Thể PR (PR Triple-Metrics) & Chống Baseline Contamination
* **1. $PR_{\text{actual}}$ (Nominal PR đo thực tế):** $\text{PR} = \frac{E_{\text{actual}}}{P_{\text{stc}} \cdot (GHI/1000) \cdot \Delta t} \times 100\%$ (Baseline $75{,}40\%$, tự động lọc mốc $GHI < 100\,\text{W/m}^2$).
* **2. $PR_{\text{corr}}$ (Chuẩn hóa nhiệt độ IEC 61724-1 Annex B):** $PR_{\text{corr}} = \frac{PR_{\text{actual}}}{1 + \gamma \cdot (T_{\text{cell}} - 25^\circ\text{C})}$ (Khử biến thiên mùa vụ, phát hiện thoái hóa phần cứng $<0{,}5\%/\text{năm}$).
* **3. $PR_{\text{adjusted}}$ (Đường chuẩn kỳ vọng BI Mart):**
  $$T_{\text{cell}} = T_{\text{ambient}} + (GHI \times 0{,}03)$$
  $$Loss_{\text{temp}} = 0{,}0038 \times \max(0, T_{\text{cell}} - 25^\circ\text{C})$$
  $$PR_{\text{adjusted}} = 0{,}85 \times (1 - Loss_{\text{temp}})$$
  * **Luận cứ:** Sử dụng hằng số thiết kế danh định STC **$0{,}85$** (đã khấu trừ $15\%$ tổn thất cố định về inverter, cáp, quang học kính, dung sai module) để **phòng chống triệt để Lỗi Ô nhiễm Đường Cơ sở (Baseline Contamination) và lỗi vòng lặp logic (Circular Logic)** khi trạm bị hỏng hóc nặng ($PR=30\%$).

### 4.2. Phân Tách Trực Quan Hóa: Tableau (Chương 5) & Streamlit (Chương 6)
* **Chương 5 — Hệ Thống 3 Dashboard Tableau Desktop (`bi_mart`):**
  - **Tab 1: Executive Overview:** BANs tổng sản lượng ($3{,}45\,\text{GWh}$), doanh thu ($700.000\,\text{AUD}$), cắt giảm $\text{CO}_2$ ($2.827\,\text{tấn}$), bản đồ địa lý 5 Campus, cơ cấu tự dùng $82\%$ vs xuất lưới $18\%$.
  - **Tab 2: Operational Efficiency & Loss Analysis:** Biểu đồ thác nước PV Loss Tree ($Loss_{\text{temp}} = 14{,}80\%$, $Loss_{\text{clip}} = 2{,}30\%$, $Loss_{\text{soiling}} = 1{,}80\%$, $Loss_{\text{anomaly}} = 2{,}04\%$), phân rã $PR_{\text{actual}}$ vs $PR_{\text{adjusted}}$ theo mùa.
  - **Tab 3: AI Anomaly Diagnostic & CBM Maintenance:** Ma trận 6 mã cờ dị thường GMM-IF, Heatmap giờ-ngày và bảng điều độ bảo trì CBM Dispatcher tự động.
* **Chương 6 (Mục 6.7) — Ứng Dụng Streamlit 2 Trang (`srcs/07_dashboard/streamlit_app/`):**
  - **Trang 1 (`pages/1_ML.py`):** Giám sát chuỗi thời gian dự báo LightGBM (T+15m, T+60m) kèm dải tin cậy sai số & Giải thích mô hình SHAP (Global Beeswarm Plot 52 đặc trưng & Local Waterfall Plot).
  - **Trang 2 (`pages/2_What_If.py`):** Dự báo và Phân tích Mô phỏng Giả định (Interactive What-If Scenario Simulation & Optimization Dashboard) với các ô Checkbox cho 6 hạng mục đề xuất kỹ thuật.

---

## 5. CHI TIẾT 6 ĐỀ XUẤT CẢI TIẾN KỸ THUẬT & WHAT-IF SIMULATOR (CHƯƠNG 7)

```
┌────┬────────────────────────────────────────────┬──────────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ STT│ Hạng Mục Đề Xuất Kỹ Thuật (Audited)        │ Tỷ Lệ Cải Thiện  │ Điện Thu Hồi │ Giá Trị Kinh │ CapEx Đầu Tư │ Hoàn Vốn     │
│    │ (Streamlit Reactive Checkbox)              │ (% Hiệu Suất)    │ (kWh / Năm)  │ Tế (AUD/Năm) │ (AUD)        │ (Payback TB) │
├────┼────────────────────────────────────────────┼──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ 1  │ Hệ thống Pin BESS 5 Campus (1MW/2.5MWh)    │ Thu hồi cắt ngọn │ 712.182 kWh  │ 323.164 AUD  │ 1.250.000 AUD│ 3,87 Năm     │
│ 2  │ Khe hở thông gió mái 10–15 cm (AS/NZS 5033)│ Hạ cell -8,0°C   │ 117.224 kWh  │ 23.445 AUD   │ 24.280 AUD   │ 1,04 Năm     │
│ 3  │ Quy trình Bảo trì CBM & AI Anomaly (GMM-IF)│ MTTD < 1h        │ 70.330 kWh   │ 29.066 AUD   │ 8.000 AUD/năm│ < 4 Tháng    │
│ 4  │ Khung nghiêng chữ A 15° cho 970 kWp mái bằn│ Tăng nắng đông   │ 71.850 kWh   │ 14.670 AUD   │ 18.000 AUD   │ 1,68 Năm     │
│ 5  │ Lịch rửa pin thông minh theo chuỗi mưa     │ Xóa bám bụi khô  │ 62.060 kWh   │ 18.412 AUD   │ 0 AUD (Quy t)│ Tức thì      │
│ 6  │ Nâng cấp TOPCon trong kỳ đại tu (Tùy chọn) │ Hiệu suất 22,5%  │ 213.761 kWh  │ 42.752 AUD   │ Kỳ đại tu    │ Tích hợp     │
└────┴────────────────────────────────────────────┴──────────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

```
┌───────────────────────────────────────────────┬───────────────────────────────┬───────────────────────────────┬───────────────────────────────┐
│ CHỈ SỐ TOÀN DANH MỤC (FLEET KPIS)             │ HIỆN TRẠNG (BASELINE)         │ SAU TỐI ƯU HÓA (OPTIMIZED)    │ MỨC CẢI THIỆN RÒNG (DELTA)    │
├───────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────┼───────────────────────────────┤
│ Tổng Sản Lượng Điện Phát Hàng Năm             │ 3,45 GWh/năm (3.447.760 kWh)  │ 4,70 GWh/năm (4.695.534 kWh)  │ +1,25 GWh/năm (+36,18%)       │
│ Hệ Số Hiệu Suất Hệ Thống (Performance Ratio)  │ 75,40% (Class B)              │ 88,62% (Class A Quốc Tế)      │ +13,22 điểm % (+17,54%)       │
│ Hệ Số Khai Thác Công Suất (Capacity Factor)   │ 16,21%                        │ 22,07%                        │ +5,86 điểm % (+36,18%)        │
│ Doanh Thu Tiết Kiệm & Dòng Tiền Hàng Năm      │ 700.000 AUD/năm               │ 1.151.509 AUD/năm             │ +451.509 AUD/năm (+64,50%)    │
│ Khối Lượng Cắt Giảm Phát Thải Khí Nhà Kính    │ 2.827 tấn CO2/năm             │ 3.850 tấn CO2/năm             │ +1.023 tấn CO2/năm (+36,18%)  │
├───────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────┼───────────────────────────────┤
│ TỔNG VỐN ĐẦU TƯ TOÀN DANH MỤC (CapEx)         │ —                             │ ~1.300.280 AUD                │ BESS: 1.25M AUD; Khác: 50.2k  │
│ THỜI GIAN HOÀN VỐN CÓ TRỌNG SỐ (Payback)      │ —                             │ 3,15 NĂM                      │ Tỷ suất sinh lời ROI > 270%   │
└───────────────────────────────────────────────┴───────────────────────────────┴───────────────────────────────┴───────────────────────────────┘
```

---

## 6. LỘ TRÌNH THỰC THI REFINE CHO BUỔI SAU (6-AGENT EXECUTION ROADMAP)

Khi người dùng yêu cầu bắt đầu thực thi refine báo cáo `reports/DATN_REPORT_FINAL_02.tex`, nhóm sẽ kích hoạt **6 Agent chuyên trách** theo trình tự sau:

1. **Agent 1 (Chương 1 & 2):**
   - Cập nhật số liệu Baseline 12 tháng kiểm toán ($3{,}45\,\text{GWh/năm}$, $700.000\,\text{AUD/năm}$, $2.827\,\text{tấn CO}_2\text{/năm}$).
   - Bổ sung Domain Fundamentals (~1.5 trang) và 3 bài toán vật lý thực địa.
   - Cập nhật Mục 2.3 thành Kiến trúc Lakehouse 6 Tầng Chức Năng (Layer 1 đến Layer 6).
2. **Agent 2 (Chương 3 & 4):**
   - Đối soát cấu trúc Galaxy Schema DWH với DDL `create_datawarehouse.sql`.
   - Bổ sung sâu 3 luận cứ khoa học Galaxy Schema và cơ chế Partition Pruning theo `date_id`.
   - Cập nhật $7.431$ cờ dị thường 15p ($0{,}272\%$) và $5.638$ cờ dị thường 1h ($0{,}825\%$), tích hợp 5 dị thường Ad-hoc thực địa.
3. **Agent 3 (Chương 5 & 6):**
   - Bổ sung Khung PR Triple-Metrics ($PR_{\text{actual}}$, $PR_{\text{corr}}$, $PR_{\text{adjusted}} = 0{,}85 \times (1 - Loss_{\text{temp}})$) và cơ chế chống Lỗi Ô nhiễm Đường Cơ sở Baseline Contamination.
   - Trình bày sâu 3 Dashboard Tableau Desktop (`bi_mart`).
   - Cập nhật kết quả kiểm định LightGBM WAPE $17{,}73\% / 22{,}58\%$, $R^2 = 0{,}9283$ và Mục 6.7 Streamlit 2 Trang (`pages/1_ML.py` và `pages/2_What_If.py`). Tinh chỉnh Mục 6.8 để khử trùng lặp với Chương 7.
4. **Agent 4 (Chương 7 & Phụ lục):**
   - Xây dựng toàn diện Chương 7 (~450 dòng học thuật): Bóc tách 6 điểm nghẽn vận hành, Chi tiết 6 đề xuất cải tiến kỹ thuật đã kiểm toán, Bảng ma trận What-If Simulator (+36,18% sản lượng, hoàn vốn $3{,}15\,\text{năm}$), và Định hướng tương lai NEM AEMO 5p, Carbon ACCUs, MLOps O&M.
   - Kiểm tra và đồng bộ Phụ lục A, B, C, D.
5. **Agent 5 (Data Auditor):**
   - Chạy script kiểm toán đối soát $100\%$ tính nhất quán của toàn bộ số liệu xuyên suốt 7 chương.
6. **Agent 6 (QA & LaTeX Formatter):**
   - Rà soát logic chuyển tiếp văn phong học thuật.
   - Quét regex $100\%$ tuân thủ quy chuẩn `latex-fpt-writer` (không còn dấu ngoặc kép thẳng `"`, escape `\%`, `\_` trong text mode, cân bằng môi trường bảng/hình).
