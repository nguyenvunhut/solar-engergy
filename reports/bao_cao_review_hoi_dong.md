# BÁO CÁO TIẾN ĐỘ DỰ ÁN TỐT NGHIỆP - THE OUTLIERS
## HỆ THỐNG PHÂN TÍCH VÀ DỰ BÁO SẢN LƯỢNG ĐIỆN MẶT TRỜI

*(Tài liệu tuân thủ cấu trúc báo cáo của bộ môn Xử lý Dữ liệu và Quy trình phân tích 7 bước)*

---

## I. VẤN ĐỀ VÀ BỐI CẢNH THỰC TẾ (PROBLEM)

### Bước 1: Khởi tạo bối cảnh và Xác định câu hỏi kinh doanh

#### 1. Bối cảnh thực tế (Câu chuyện dữ liệu Unisolar)
Ngành công nghiệp năng lượng mặt trời (PV - Photovoltaic) tại Úc đang phát triển vũ bão, nhưng việc quản lý hiệu suất của các trạm điện phân tán lại là một thách thức lớn. Nguồn dữ liệu cốt lõi của dự án được trích xuất từ tập dữ liệu **Unisolar** - một hệ thống khổng lồ lưu trữ các bản ghi từ cảm biến IoT lắp đặt tại 42 trạm điện quang điện khác nhau. Hệ thống cảm biến của Unisolar liên tục phát tín hiệu và ghi nhận sản lượng điện (`energy_generated_kwh`) với độ chi tiết cứ mỗi 15 phút một lần.

Tuy nhiên, dữ liệu sản lượng thuần túy là chưa đủ để đánh giá hiệu năng trạm. Nhóm quyết định kết hợp thêm nguồn dữ liệu viễn thám từ **Open-Meteo API** (chứa thông tin bức xạ mặt trời, nhiệt độ, sức gió). Khó khăn bắt đầu nảy sinh khi hệ thống thời tiết chỉ cập nhật mỗi 1 giờ. Bài toán đặt ra là làm sao hợp nhất (Fuse) hai nguồn dữ liệu khác biệt về cả mặt không gian lẫn tần suất thời gian này thành một Kho dữ liệu (Data Warehouse) duy nhất để tạo ra những Insight có giá trị.

#### 2. Vấn đề cần giải quyết
Việc khám phá dữ liệu ban đầu cho thấy chất lượng dữ liệu thô của Unisolar gặp rất nhiều "vết thương":
- **Khuyết dữ liệu (Missing Data):** Các trạm điện thường nằm ở khu vực hẻo lánh, kết nối mạng IoT chập chờn gây ra các mảng dữ liệu trống kéo dài từ vài phút đến vài ngày.
- **Nhiễu rò rỉ điện (Night Leakage):** Có dòng điện rò rỉ và tín hiệu nhiễu hệ thống trong khung giờ từ 18:00 tối đến 05:00 sáng hôm sau - khoảng thời gian đáng lẽ sản lượng phải bằng 0.
- **Giá trị bất thường (Outliers):** Tồn tại các thời điểm bức xạ nắng cực gắt nhưng sản lượng lại tụt dốc không phanh. Nguyên nhân có thể do tấm pin bị bám bụi, bóng râm (shading) tạm thời hoặc Inverter hỏng.

#### 3. Mục tiêu và Câu hỏi kinh doanh (Business Questions)
Từ các vấn đề trên, nhóm đã đặt ra các câu hỏi kinh doanh sắc bén cần hệ thống Data Warehouse giải quyết:
1. **(Q1) Yếu tố nào chi phối hiệu suất:** Cường độ bức xạ (`shortwave_radiation`) hay nhiệt độ môi trường (`temperature_c`) tác động mạnh nhất đến chỉ số Performance Ratio (`pr_actual`)?
2. **(Q2) Phân loại sự cố:** Làm sao thuật toán có thể phân biệt được sự sụt giảm sản lượng do mây bay ngang qua (sự cố tạm thời) với việc Inverter bị hỏng hoặc tấm pin bám bẩn (sự cố vật lý cần bảo trì)?
3. **(Q3) Tối ưu vận hành:** Khung giờ nào và mùa nào trong năm các trạm đạt hiệu suất tối đa để hỗ trợ lên lịch bảo trì mà ít ảnh hưởng đến doanh thu nhất?
4. **(Q4) Dự báo tương lai:** Làm thế nào để dùng dữ liệu lịch sử dự báo được sản lượng điện cho ngày tiếp theo?
 
---

## II. GIẢI PHÁP TỔNG THỂ (SOLUTION)

### Bước 2: Đề xuất kiến trúc và Giải pháp
Để trả lời các câu hỏi kinh doanh trên, nhóm xây dựng mô hình **Data-driven Pipeline**:
- **Thiết kế Data Warehouse chuẩn mực:** Áp dụng kiến trúc đa chiều (Multi-dimensional) linh hoạt để giải quyết bài toán lệch pha thời gian (15p vs 1h).
- **Làm sạch tự động (ETL Orchestration):** Kết hợp Supabase, S3 Storage (quản lý bởi DVC) và Python (Pandas/Sklearn) để loại bỏ nhiễu ban đêm, nội suy điền khuyết (Hybrid Imputation) và quét Outlier bằng cửa sổ trượt (Rolling IQR).
- **Machine Learning & BI:** Xây dựng Data Mart riêng biệt phục vụ trực quan hóa (Tableau) và đào tạo mô hình dự báo (ARIMA/Prophet).

---

## III. THỰC THI (IMPLEMENTATION) - DATA WAREHOUSE & PIPELINE

### Bước 3: Thiết kế Kho dữ liệu (Data Warehouse Architecture)
Đây là "trái tim" của hệ thống. Quá trình thiết kế được nhóm đi qua 4 giai đoạn chuẩn mực một cách vô cùng chi tiết:

1. **Metadata & Data Dictionary:** Nhóm đã định nghĩa hệ thống Metadata chặt chẽ. Các trường dữ liệu quan trọng như `pr_actual` (Tỷ lệ hiệu suất), `delta_baseline` (Độ lệch chuẩn) được chuẩn hóa công thức tính toán từ ban đầu để thống nhất Business Logic.
2. **Conceptual Model (Mô hình khái niệm):** Nhóm xác định 4 thực thể (Entities) cốt lõi của hệ sinh thái Unisolar: (1) Sự kiện tạo ra điện, (2) Trạng thái khí hậu, (3) Thông tin Trạm điện và (4) Mốc Thời gian/Địa lý.
3. **Logical Model (Mô hình logic - Galaxy Schema):** 
   - *Vấn đề của Star Schema:* Nếu dùng mô hình Sao (Star Schema), việc ép dữ liệu thời tiết (1h) vào cùng một Fact table với sản lượng (15p) sẽ tạo ra quan hệ Many-to-Many hoặc phải duplicate dữ liệu thời tiết tới 4 lần, gây méo mó dữ liệu.
   - *Giải pháp Galaxy:* Nhóm quyết định sử dụng **Lược đồ Thiên hà (Galaxy Schema)**. Nhóm tách ra làm 2 bảng Fact độc lập nhưng cùng kết nối tới các Shared Dimensions chung là `dim_date`, `dim_time`, và `dim_geography`.
4. **Physical Model (Mô hình vật lý):** 
   - Triển khai thực tế trên PostgreSQL (Supabase).
   - Tối ưu hóa: Nhóm cài đặt Indexing trên các khóa ngoại (`site_id`, `date_id`, `time_id`), chọn kiểu dữ liệu `FLOAT` cho các measure để tiết kiệm dung lượng, và tận dụng connection pooler `pg8000` để chống quá tải kết nối.
   - *Minh chứng Code Physical (Trích từ `create_datawarehouse.sql`):*
     ```sql
     CREATE TABLE fact_solar_energy_gen (
         gen_id SERIAL PRIMARY KEY, site_id INT, geo_id INT, 
         date_id INT, time_id INT, energy_generated_kwh FLOAT
     );
     CREATE TABLE fact_weather (
         weather_id SERIAL PRIMARY KEY, geo_id INT, date_id INT, 
         time_id INT, shortwave_radiation FLOAT, temperature_c FLOAT
     );
     ```

### Bước 4: Làm sạch và xử lý dữ liệu (Data Pipeline)
Nhóm không dùng SQL thuần mà dùng Python Orchestrator kết hợp thư viện toán học.
**1. Thuật toán Điền khuyết (Hybrid Imputation - `02_run_hybrid_imputation.py`):**
Cấu trúc thành 4 lớp lọc (Filters):
- `Rule-based Night Zero`: Ép tất cả các khoảng trống từ 18:00 - 05:00 về `0`. Xóa sạch lỗi rò rỉ điện.
- `Linear Interpolation`: Nội suy tuyến tính nối 2 điểm gần nhất cho các lỗ hổng siêu nhỏ (< 3 dòng).
- `Cubic Interpolation`: Nội suy bậc 3 tạo đường cong mềm mại hình chuông cho các khoảng trống vừa, mô phỏng đúng tính chất quỹ đạo mặt trời.
- `Machine Learning Regression`: Dùng `sklearn.linear_model.LinearRegression` train trên `[shortwave_radiation, temperature_c]` để dự đoán các mảng dữ liệu bị đứt kết nối cả ngày.

**2. Phát hiện Dị thường (Outlier Detection - `02_iqr_rolling.py`):**
Sử dụng thuật toán **Rolling IQR** (Cửa sổ trượt). Quét các khoảng Tứ phân vị (Q1, Q3) theo khung thời gian động (Rolling Window) thay vì khung tĩnh, giúp phát hiện cực kỳ nhạy các pha sụt giảm sản lượng giữa trưa. Hiện nhóm cũng đang test song song mô hình `Gaussian Mixture Models (GMM)` và `Isolation Forest`.

---

## IV. KẾT QUẢ & MINH CHỨNG (RESULTS)

### Bước 5 & 6: Khám phá, Phân tích & Diễn giải Insight

**1. Minh chứng Kết quả Data Pipeline QA/QC:**
Hệ thống tự động đã quét sạch mớ dữ liệu thô của Unisolar và đưa ra kết quả log thực tế.
*Trích xuất log thực thi từ `qa_qc_eda_pipeline.log`:*
```log
2026-06-28 15:44:50 | INFO     | Đã kéo thành công 683385 dòng và 15 cột.
2026-06-28 15:44:50 | WARNING  | Chất lượng dữ liệu: CẢNH BÁO. Phát hiện 128700 giá trị bị thiếu!
2026-06-28 15:44:50 | WARNING  | Chi tiết cột thiếu dữ liệu: {'pr_actual': 128484, 'e_expected': 108...}
```
*Kết quả:* Nhờ phát hiện 128.700 lỗi này, thuật toán Hybrid Imputation đã được kích hoạt kịp thời, khôi phục lại tính toàn vẹn của Data Warehouse.

**2. Key Insights Trả lời Câu hỏi Kinh doanh:**
Dựa vào dữ liệu sạch (`pattern_discovery.ipynb`), nhóm đã rút ra kết luận mang tính bước ngoặt:
- **Trả lời Q1 (Suy hao do nhiệt):** Phân tích tương quan chứng minh hiệu suất tấm pin không đồng biến vô hạn với bức xạ. Cụ thể, khi nhiệt độ môi trường (temperature) vượt quá 25°C, mức sản lượng thực tế sụt giảm rõ rệt dù cường độ bức xạ đạt đỉnh điểm (Peak Irradiance).
- **Trả lời Q2 (Phân loại sự cố):** Bằng việc so sánh chỉ số `delta_baseline` (Độ lệch chuẩn thực tế vs kì vọng), thuật toán Rolling IQR đã đánh dấu chính xác những ngày bức xạ cao nhưng sản lượng tiệm cận 0 (Outlier = True). Đây là cảnh báo vật lý đáng tin cậy để điều phối bảo trì (Predictive Maintenance).

---

## V. THUẬN LỢI & KHÓ KHĂN (ADVANTAGES & CHALLENGES)

**1. Thuận lợi:**
- Việc đưa toàn bộ dữ liệu CSV thô của Unisolar lên Cloud Storage (S3) và quản lý bằng DVC ngay từ đầu đã giúp nhóm tránh được rủi ro quá tải ổ cứng và giới hạn 100MB của Github.
- Tách bạch quá trình tính toán Outlier phức tạp ra khỏi Database và giao cho Python Pandas (qua định dạng Parquet) đã tối ưu thời gian chạy pipeline nhanh gấp nhiều lần so với các câu truy vấn SQL Window Functions truyền thống.

**2. Khó khăn lớn nhất:**
- **Thiết kế Data Warehouse:** Quá trình Mapping từ Conceptual Model sang Logical Model cực kỳ đau đầu do sự bất đồng bộ giữa dữ liệu Unisolar (15p) và Open-Meteo (1h). Việc phải "đập đi xây lại" từ Star Schema sang Galaxy Schema làm tốn nhiều quỹ thời gian của nhóm.
- **Tuning thuật toán:** Việc xác định các ngưỡng ranh giới (Thresholds) cho thuật toán nội suy (Ví dụ: Định nghĩa lỗ hổng dài bao nhiêu thì dùng Linear, bao nhiêu thì dùng Regression) đòi hỏi phải thử nghiệm liên tục để không làm mất đi tính tự nhiên (Nature) của đồ thị sinh điện.
- **Làm việc nhóm:** Việc đồng bộ hóa dữ liệu DVC cùng với các File Jupyter Notebook khổng lồ gây ra nhiều xung đột (Merge Conflict) trong Git, đòi hỏi team phải quy hoạch lại nhánh (Branching) cẩn thận.

---

## VI. KẾT LUẬN & ĐỊNH HƯỚNG PHÁT TRIỂN (CONCLUSION)

### Bước 7: Theo dõi, Xác thực & Phát triển
- **Tổng kết:** Nhóm đã hoàn thành xuất sắc việc xây dựng nền móng dữ liệu vững chắc (Data Warehouse) cho tập dữ liệu phức tạp của Unisolar. Quá trình ETL đã chạy ổn định, các thuật toán Imputation và Outlier Detection đã đi vào quỹ đạo hoạt động thực tế với bằng chứng rõ ràng.
- **Hướng phát triển sắp tới:**
  1. **(Dashboard BI):** Chuyển giao các chỉ số KPIs từ BI Mart lên hệ thống Tableau để trực quan hóa, cung cấp góc nhìn tương tác cho người quản lý trạm.
  2. **(Machine Learning Forecast):** Bắt đầu sử dụng dữ liệu sạch tại ML Mart để huấn luyện các mô hình AI (như ARIMA, Prophet, XGBoost) nhằm giải quyết dứt điểm câu hỏi kinh doanh số 4 (Q4): Dự báo sản lượng điện cho tương lai.
