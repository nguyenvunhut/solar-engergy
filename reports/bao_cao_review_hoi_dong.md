# BÁO CÁO TIẾN ĐỘ DỰ ÁN TỐT NGHIỆP - THE OUTLIERS
## HỆ THỐNG PHÂN TÍCH VÀ DỰ BÁO SẢN LƯỢNG ĐIỆN MẶT TRỜI

*(Tài liệu tuân thủ nghiêm ngặt cấu trúc báo cáo của bộ môn Xử lý Dữ liệu và Quy trình phân tích 7 bước)*

---

## I. VẤN ĐỀ (PROBLEM)

### 1. Bối cảnh thực tế
Ngành năng lượng mặt trời tại Úc đang đối mặt với lượng dữ liệu khổng lồ sinh ra từ các trạm PV (PhotoVoltaic). Tại 42 trạm điện quang điện thuộc phạm vi dự án, đối tượng sử dụng dữ liệu chính là người quản lý trạm và kỹ sư vận hành. Nguồn dữ liệu hiện tại được phân mảnh: dữ liệu sản lượng từ trạm lưu trữ định dạng CSV mỗi 15 phút, trong khi dữ liệu thời tiết viễn thám kéo từ API Open-Meteo cập nhật mỗi 1 giờ.

### 2. Vấn đề cần giải quyết & Hệ quả
- **Đứt gãy dữ liệu (Missing Data):** Các cảm biến trên lưới điện thường xuyên rớt mạng, gây ra các khoảng trống dữ liệu khổng lồ.
- **Nhiễu rò rỉ điện (Night Leakage):** Có dòng điện rò rỉ rải rác trong khung giờ từ 18:00 tối đến 05:00 sáng hôm sau dù không hề có bức xạ mặt trời.
- **Lệch pha chu kỳ:** Dữ liệu 15 phút vs 1 giờ khiến mô hình Star Schema truyền thống thất bại do bùng nổ dữ liệu trùng lặp (Duplicate) khi Join.
- **Hệ quả:** Nếu không giải quyết, hệ thống sẽ tính toán sai doanh thu thực tế lũy kế, đồng thời không phát hiện kịp thời các tấm pin bị hỏng hóc hoặc bám bẩn (Outliers) để bảo trì, dẫn đến giảm tuổi thọ hệ thống.

---

## II. GIẢI PHÁP (SOLUTION)

### 1. Mục tiêu dự án
- **Mục tiêu 1:** Xây dựng Data Warehouse với kiến trúc Galaxy Schema nhằm giải quyết triệt để sự lệch pha dữ liệu.
- **Mục tiêu 2:** Tự động hóa Pipeline làm sạch (ETL), loại bỏ nhiễu ban đêm và điền khuyết tự động (Hybrid Imputation).
- **Mục tiêu 3 & 4 (Đang phát triển):** Huấn luyện mô hình học máy (ARIMA/Prophet) để dự báo và xây dựng Dashboard BI để theo dõi.

### 2. Giải pháp tổng thể
Dự án vận hành theo mô hình Data-driven. Dữ liệu thô từ Kaggle & API được đẩy lên Supabase (PostgreSQL & S3 Storage) thông qua công cụ quản lý phiên bản DVC. Quy trình xử lý lỗi (Missing/Outliers) được tính toán hoàn toàn bằng Python (Pandas/Scikit-learn) bên ngoài trước khi nạp lại vào Data Warehouse nhằm tránh quá tải Database.

---

## III. THỰC THI (IMPLEMENTATION) - THEO QUY TRÌNH PHÂN TÍCH

### Bước 1: Xác định mục tiêu và câu hỏi kinh doanh
Tập dữ liệu cần trả lời được các câu hỏi: 
- Khung giờ nào hiệu suất trạm đạt đỉnh? Nhiệt độ môi trường ảnh hưởng thế nào đến sản lượng?
- Làm sao phân biệt được sản lượng sụt giảm do mây che hay do tấm pin bị hỏng?

### Bước 2: Thu thập dữ liệu
Hệ thống lấy dữ liệu sản lượng và thời tiết, tải thẳng lên Supabase S3. 
*Minh chứng - Code thực thi kết nối Supabase S3 bằng boto3 (Trích từ dự án):*
```python
s3 = boto3.client(
    "s3", endpoint_url=f"https://{PROJECT_ID}.supabase.co/storage/v1/s3",
    aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY,
    region_name="ap-southeast-1", config=Config(signature_version="s3v4")
)
# Đọc thẳng CSV vào pandas DataFrame mà không cần tải file về local
obj = s3.get_object(Bucket="raw-data", Key="solar_gen.csv")
df = pd.read_csv(io.BytesIO(obj["Body"].read()))
```

### Bước 3: Làm sạch và xử lý dữ liệu
Nhóm không dùng SQL thuần mà dùng Python Orchestrator để chạy thuật toán làm sạch phức tạp.
**Minh chứng 1: Thuật toán Điền khuyết (Hybrid Imputation - `02_run_hybrid_imputation.py`)**
Dự án thực thi tuần tự 4 bước nội suy:
1. `Rule-based Night Zero`: Ép tất cả missing data trong khoảng 18:00 - 05:00 về `0` để cắt nhiễu rò rỉ.
2. `Linear`: Nội suy tuyến tính cho các lỗ hổng dưới 3 dòng (tức < 45 phút).
3. `Cubic`: Nội suy bậc 3 để mô phỏng hình chuông cong của ánh sáng mặt trời đối với các lỗ hổng vừa.
4. `Machine Learning Regression`: Dùng `sklearn.linear_model.LinearRegression` train trên đặc trưng `[shortwave_radiation, temperature_c]` để nội suy các lỗ hổng mất mạng kéo dài cả ngày.

**Minh chứng 2: Phát hiện Dị thường (Outlier Detection - `02_iqr_rolling.py`)**
Nhóm chạy thuật toán **Rolling IQR** (Cửa sổ trượt). Bằng cách quét tứ phân vị (Q1, Q3) theo khung thời gian động, thuật toán bắt được các giọt sụt sản lượng bất ngờ giữa trưa nắng mà thuật toán IQR tĩnh truyền thống thường bỏ sót. (Hiện nhóm đang thử nghiệm thêm GMM và Isolation Forest).

### Bước 4: Thiết kế Database & Pipeline (Khám phá cấu trúc)
*Minh chứng kiến trúc - Galaxy Schema (Trích từ `create_datawarehouse.sql`)*
Thay vì Star Schema, nhóm tạo 2 Fact tables độc lập nhưng chia sẻ chung Dimensions:
```sql
CREATE TABLE fact_solar_energy_gen (
    gen_id SERIAL PRIMARY KEY, site_id INT, geo_id INT, date_id INT, time_id INT,
    energy_generated_kwh FLOAT
);
CREATE TABLE fact_weather (
    weather_id SERIAL PRIMARY KEY, geo_id INT, date_id INT, time_id INT,
    shortwave_radiation FLOAT, temperature_c FLOAT
);
-- dim_date và dim_time được dùng chung để giải quyết lệch pha 15p - 1h.
```

---

## IV. KẾT QUẢ (RESULTS)

### Bước 5: Trực quan hóa & Khám phá Dữ liệu (EDA)
Trong quá trình Pipeline QA/QC chạy, hệ thống đã quét và ghi nhận kết quả thực tế qua log.
*Minh chứng - Kết quả chạy thực tế từ file `qa_qc_eda_pipeline.log`:*
```log
2026-06-28 15:44:36 | INFO     | Đang thực thi truy vấn kéo dữ liệu từ view: bi_mart.mv_bi_mart_hourly_measures
2026-06-28 15:44:50 | INFO     | Đã kéo thành công 683385 dòng và 15 cột.
2026-06-28 15:44:50 | WARNING  | Chất lượng dữ liệu: CẢNH BÁO. Phát hiện 128700 giá trị bị thiếu!
2026-06-28 15:44:50 | WARNING  | Chi tiết cột thiếu dữ liệu: {'pr_actual': 128484, 'e_expected': 108, 'delta_baseline': 108}
2026-06-28 15:44:50 | INFO     | Đã xuất báo cáo thống kê mô tả ra file: thong_ke_mo_ta_san_luong.csv
```
Log minh chứng quá trình Data Quality Check đã phát hiện hơn 128.000 dòng lỗi trước khi đưa vào thuật toán làm sạch, đảm bảo độ chuẩn xác cho Data Warehouse.

### Bước 6: Diễn giải kết quả và Đưa ra Insight
Từ dữ liệu đã làm sạch (`thong_ke_mo_ta.ipynb` và `pattern_discovery.ipynb`), nhóm rút ra 2 Key Insights quan trọng nhất:
1. **Suy hao do nhiệt (Thermal Degradation):** Hiệu suất của tấm pin không đồng biến với bức xạ. Khi nhiệt độ vượt quá 25°C, mức sản lượng kwh thực tế sụt giảm rõ rệt dù cường độ bức xạ đạt đỉnh điểm (Peak Irradiance). 
2. **Cảnh báo Bảo trì (Predictive Maintenance):** Thuật toán Rolling IQR cắm cờ (Flag) chính xác vào các thời điểm bức xạ nắng rất cao nhưng chỉ số `pr_actual` tiệm cận 0. Đây là minh chứng rõ ràng nhất cho việc tấm pin bị che khuất / bám bẩn hoặc biến tần Inverter bị sập, giúp quản lý trạm điều phối bảo trì kịp thời.

---

## V. KẾT LUẬN & MỞ RỘNG (CONCLUSION)

### Bước 7: Theo dõi, Xác thực & Tổng kết bài học
- **Đánh giá Mục tiêu:** Nhóm đã hoàn thành 100% mục tiêu xây dựng Data Warehouse với Galaxy Schema và tự động hóa Pipeline xử lý Missing/Outliers siêu tốc độ với Python Parquet + DVC. Sự đánh đổi là quá trình cấu hình phức tạp và tốn thời gian tuning thuật toán.
- **Theo dõi KPIs:** Các chỉ số KPI như `pr_actual` (Performance Ratio) và `delta_baseline` (Độ lệch chuẩn) hiện đang được đẩy vào BI Mart và giám sát tự động.
- **Hướng phát triển (Mở rộng):** Nhóm đang trong quá trình chuẩn bị dữ liệu tại ML Mart để thực hiện mô hình dự báo học máy (Forecast bằng ARIMA/Prophet) và hoàn thiện Dashboard (Tableau) nhằm báo cáo cho người dùng cuối trong các Scrum bảo vệ sắp tới.
