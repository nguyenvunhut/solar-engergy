# TÀI LIỆU KỸ THUẬT VÀ QUẢN LÝ DỰ ÁN (DOCUMENTATION HUB)

Thư mục `docs/` chứa toàn bộ hồ sơ thiết kế kiến trúc, nghiên cứu miền nghiệp vụ (Solar Domain), hệ thống công thức toán học, quy chuẩn kỹ thuật và báo cáo tiến độ theo chu kỳ Scrum của dự án.

---

## 1. TỔ CHỨC CÁC THƯ MỤC CHUYÊN ĐỀ

### `configurations_and_setups/`
Tài liệu hướng dẫn cấu hình hạ tầng và quy chuẩn phát triển:
- **`supabase_connection.md`**: Hướng dẫn kết nối cơ sở dữ liệu PostgreSQL (Supabase Connection Pooler) và quản lý lưu trữ S3 Object Storage qua `boto3` / `pg8000`.
- **`HUONG_DAN_CHAY_CLOUD.md`**: Cấu hình và điều phối triển khai hệ thống trên hạ tầng Cloud / Docker.
- **`WINDOWS_SETUP.md`**: Quy trình thiết lập môi trường phát triển cục bộ trên hệ điều hành Windows (Python 3.10+, Virtualenv, DVC).

### `scrum_5_pipeline_foundation/`
Hồ sơ kỹ thuật giai đoạn xây dựng nền tảng dữ liệu:
- Báo cáo thu thập dữ liệu viễn thám IoT 42 trạm phát và dữ liệu tái phân tích khí tượng ERA5-Land (8 biến WMO).
- Cơ chế nạp dữ liệu tầng đệm Staging và kiểm tra tính toàn vẹn (MD5 Checksum, Resampling 15 phút).

### `scrum_6_business_logic_eda/`
Hồ sơ kỹ thuật giai đoạn mô hình hóa và định nghĩa logic nghiệp vụ:
- **`2026_06_17_BI_Mart_Measures.md`**: Quy chuẩn tính toán các chỉ số kinh doanh và hiệu năng vận hành ($PR_{\text{actual}}$, $PR_{\text{adjusted}}$, $Loss_{\text{temp}}$, $CF$, $Y_f$).
- Thiết kế Lược đồ Thiên hà (Galaxy Schema / Fact Constellation) gồm 2 bảng sự kiện (`fact_solar_energy_gen`, `fact_weather`) và 5 bảng chiều (`dim_solar_site`, `dim_geography`, `dim_date`, `dim_time`, `dim_weather_type`).
- Cơ sở thuật toán Điền khuyết Nhân quả 4 cấp độ và Bộ lọc Dị thường Lai GMM-IF kết hợp 5 rào chắn vật lý.

### `scrum_7_visualization_forecasting/`
Hồ sơ kỹ thuật giai đoạn trực quan hóa và mô hình hóa học máy:
- **`tableau_visualization_guidelines.md`**: Quy chuẩn thiết kế Bộ 3 Dashboard Tableau Desktop (Executive Overview, Operational Efficiency & Loss, Anomaly Detection & CBM).
- Thiết kế luồng trích xuất 52 đặc trưng chuỗi thời gian, khí tượng và vật lý phục vụ tầng Feature Store.

### `scrum_8_project_delivery_defense/`
Hồ sơ đóng gói sản phẩm và nghiên cứu chuyên sâu phục vụ bảo vệ đồ án:
- **`HP1_Solar_Domain_Mastery.md`**: Tổng quan toàn diện về vật lý bán dẫn quang điện, cơ chế suy hao nhiệt ($\gamma = -0{,}38\%/^\circ\text{C}$), góc đặt tấm pin và vi khí hậu bang Victoria.
- **`2026_08_23_BI_Metrics_PR_Analysis_Framework.md`**: Khung phân tích chuyên sâu 3 biến thể Hệ số Hiệu suất PR ($PR_{\text{actual}}$, $PR_{\text{adjusted}}$, $PR_{\text{correct}}$) theo chuẩn quốc tế **IEC 61724-1**.
- **`2026_08_23_Tong_Hop_Hang_So_Va_Ty_Le_Chung_Du_An.md`**: Bảng tra cứu chuẩn hóa toàn bộ 30 hằng số và tham số kỹ thuật của dự án.
- **`2026_08_20_Tong_Hop_Toan_Bo_Cong_Thuc_Bao_Cao_Final_02.md`**: Tổng hợp toàn bộ công thức toán học, vật lý quang điện và hàm mất mát áp dụng trong hệ thống.
- **`notebook_ml_v5/`**: Chuỗi 20 tài liệu kỹ thuật thực nghiệm chi tiết cho Pipeline Machine Learning LightGBM Multi-Horizon.

---

## 2. BẢNG THAM SỐ VÀ HẰNG SỐ KỸ THUẬT CỐT LÕI

| Tham số | Giá trị Chuẩn | Ý nghĩa Kỹ thuật / Vật lý |
| :--- | :---: | :--- |
| **Quy mô Hệ thống** | 42 Trạm / 5 Cơ sở | Phân tán tại Bundoora, Bendigo, Albury-Wodonga, Mildura, Shepparton |
| **Tổng Công suất ($P_{\text{stc}}$)** | $2.428\,\text{kWp}$ ($2{,}43\,\text{MWp}$) | Tổng công suất danh định ở điều kiện tiêu chuẩn STC ($1000\,\text{W/m}^2$, $25^\circ\text{C}$) |
| **Dung lượng Dữ liệu Telemetry** | $2.731.946$ bản ghi | Chu kỳ 15 phút, thu thập liên tục 28 tháng (01/2020 – 04/2022) |
| **Dữ liệu Khí tượng ERA5-Land** | $850.752$ bản ghi | Chu kỳ 1 giờ, 8 biến quan sát chuẩn WMO từ ECMWF |
| **Hệ số Suy hao Nhiệt ($\gamma$)** | $-0{,}38\%/^\circ\text{C}$ | Mức giảm công suất phát khi nhiệt độ cell vượt ngưỡng $25^\circ\text{C}$ |
| **Góc Hoàng hôn / Cắt đêm ($\alpha$)** | $\le -0{,}833^\circ$ | Góc nâng mặt trời thiên văn tính đến hiện tượng khúc xạ khí quyển |
| **Tỷ lệ Khuyết thiếu Điền sẵn** | $1.536.000$ ô ($35{,}99\%$) | Xử lý bằng 4 cấp: Cắt đêm ($90{,}05\%$), Tuyến tính ($3{,}49\%$), PCHIP ($3{,}30\%$), KNN ($3{,}16\%$) |
| **Tỷ lệ Dị thường Vận hành** | $104$ giờ ($0{,}45\%$) | Phát hiện bằng GMM ($p < 0{,}02$) + Isolation Forest ($3\%$) + 5 Rào chắn vật lý |
| **Sai số Dự báo LightGBM (H1)** | WAPE = $17{,}74\%$ | Tầm dự báo 15 phút, $R^2 = 0{,}9243$, tối ưu hóa bằng Huber Loss ($\delta = 1{,}0$) |
| **Sai số Dự báo LightGBM (H4)** | WAPE = $22{,}62\%$ | Tầm dự báo 60 phút, $R^2 = 0{,}8864$, giảm $49{,}5\%$ sai số so với Baseline Prophet |
