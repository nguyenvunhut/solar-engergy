# BÁO CÁO TIẾN ĐỘ DỰ ÁN TỐT NGHIỆP - THE OUTLIERS
## HỆ THỐNG PHÂN TÍCH VÀ DỰ BÁO SẢN LƯỢNG ĐIỆN MẶT TRỜI

---

## I. VẤN ĐỀ ĐẶT RA VÀ BỐI CẢNH DỰ ÁN (BUSINESS & DOMAIN LOGIC)

Trong quá trình tiếp cận bài toán phân tích 42 trạm điện năng lượng mặt trời (PV) tại Úc, nhóm đã khai phá dữ liệu (EDA) thông qua các notebook phân tích chuyên sâu (minh chứng: [notebooks/pattern_discovery.ipynb](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/notebooks/pattern_discovery.ipynb) và [notebooks/v1_ACF_PACF.ipynb](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/notebooks/v1_ACF_PACF.ipynb)). Kết quả EDA chỉ ra những "nỗi đau" (pain points) lớn đối với doanh nghiệp vận hành:

1. **Khác biệt tần suất thu thập:** Dữ liệu sản lượng được ghi nhận mỗi 15 phút, trong khi dữ liệu thời tiết (Open-Meteo) là mỗi 1 giờ. Sự lệch pha này phá vỡ các mô hình Relational Database thông thường (như Star Schema), dẫn tới bùng nổ dữ liệu trùng lặp.
2. **Missing Data và Nhiễu rò rỉ:** Dữ liệu thực tế thường xuyên bị đứt đoạn do rớt mạng cảm biến. Đáng chú ý, nhóm phát hiện dòng điện rò rỉ và nhiễu tín hiệu bất thường trong khoảng thời gian không có nắng (18:00 tối đến 05:00 sáng) – một lỗi phổ biến của Inverter mà nếu không làm sạch sẽ gây sai lệch doanh thu lũy kế.
3. **Giá trị bất thường (Outliers) đa dạng:** Có những thời điểm cường độ bức xạ cực cao nhưng sản lượng lại tiệm cận 0 (dấu hiệu tấm pin bị hỏng, bám bẩn hoặc bóng râm che khuất).

---

## II. GIẢI PHÁP VÀ KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)

Thay vì xử lý thủ công, nhóm triển khai một **Data Engineering Pipeline** tự động hoàn toàn, kết hợp giữa Cloud Database, Object Storage và Python Orchestrator. 

**Kiến trúc công nghệ thực tế (Minh chứng tại [docs/configurations_and_setups/supabase_connection.md](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/docs/configurations_and_setups/supabase_connection.md)):**
- **Lưu trữ:** Sử dụng **Supabase (PostgreSQL)** với Connection Pooler (`pg8000`) để xử lý đa luồng, và **S3-compatible Storage** để lưu file `.csv`/`.parquet` dung lượng lớn.
- **Quản lý phiên bản dữ liệu (Data Version Control):** Áp dụng `DVC` để tracking các file dữ liệu trung gian, kết hợp `boto3` để đọc file thẳng từ S3 vào Pandas DataFrame mà không cần tải về ổ cứng cục bộ.

---

## III. THỰC THI PIPELINE VÀ THUẬT TOÁN (IMPLEMENTATION & ALGORITHMS)

### 1. Data Modeling: Galaxy Schema
Thay vì Star Schema, nhóm đã thiết kế Lược đồ Thiên hà (Galaxy Schema) để xử lý triệt để sự lệch pha thời gian. 
*Tham chiếu Code:* [srcs/00_database/sql/create_datawarehouse.sql](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/srcs/00_database/sql/create_datawarehouse.sql).
- Hai bảng Fact tồn tại song song: `fact_solar_energy_gen` (15 phút) và `fact_weather` (1 giờ).
- Chia sẻ chung các Dimensions: `dim_geography`, `dim_date`, `dim_time`, `dim_solar_site`. Thiết kế này giúp khi join dữ liệu không bị nhân bản (duplicate) các dòng thời tiết cho mỗi 15 phút.

### 2. Thuật toán Điền khuyết dữ liệu (Hybrid Imputation)
Thuật toán được nhóm lập trình trực tiếp bằng Python kết hợp thư viện `scikit-learn` và `pandas`.
*Tham chiếu Code:* [srcs/02_transform/02_run_hybrid_imputation.py](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/srcs/02_transform/02_run_hybrid_imputation.py).

Thuật toán hoạt động theo chuỗi ưu tiên (Pipeline logic):
1. **Rule-based Night Zero:** Nhận diện các khoảng thời gian ban đêm (`is_night` hoặc bức xạ ngắn = 0) dựa vào giờ `NIGHT_START` đến `NIGHT_END`. Thuật toán sẽ chủ động gán toàn bộ Missing Data trong khung giờ này về `0` để loại bỏ nhiễu rò rỉ điện.
2. **Linear & Cubic Interpolation:** Nội suy tuyến tính (`linear`) cho các khoảng khuyết nhỏ, và nội suy bậc 3 (`cubic`) cho các khoảng khuyết cong, mô phỏng đúng hình chuông của sản lượng mặt trời trong ngày.
3. **Machine Learning Regression:** Đối với các khoảng mất dữ liệu quá dài, sử dụng thuật toán Hồi quy tuyến tính đa biến (`LinearRegression` từ `sklearn`) dựa vào bức xạ mặt trời và nhiệt độ (`shortwave_radiation`, `temperature_c`) để dự phóng giá trị khuyết.

### 3. Phát hiện điểm bất thường (Outlier Detection)
*Tham chiếu Code:* [srcs/02_transform/02_generate_outliers/02_iqr_rolling.py](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/srcs/02_transform/02_generate_outliers/02_iqr_rolling.py) và [02_gmm_if.py](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/srcs/02_transform/02_generate_outliers/02_gmm_if.py).

Việc xử lý Outliers bằng SQL thuần rất chậm do phải tính toán Window Functions nặng nề. Nhóm đã tối ưu bằng cách:
- Xuất dữ liệu từ Database ra file `Parquet`.
- **Áp dụng Rolling IQR:** Thuật toán tính toán Tứ phân vị (Q1, Q3) trượt theo một khung cửa sổ thời gian (Rolling Window) thay vì cố định. Điều này giúp phát hiện chính xác các giọt sụt sản lượng bất ngờ giữa trưa nắng mà không bị ảnh hưởng bởi chu kỳ lên xuống tự nhiên của mặt trời.
- *(Đang nghiên cứu thêm):* Nhóm cũng đang chạy thử nghiệm các thuật toán phát hiện bất thường bằng Machine Learning tiên tiến hơn như **Gaussian Mixture Models (GMM)** và **Isolation Forest** để đánh giá hiệu quả so với Rolling IQR.
- Cuối cùng, kết quả (các cờ Outlier Flags) được nạp ngược lại vào Data Warehouse.

---

## IV. KẾT QUẢ THỰC TẾ & MINH CHỨNG (ACTUAL RESULTS & EVIDENCE)

**1. Kết quả Kỹ thuật đã đạt được (100%):**
- Đã khởi tạo thành công Staging, Buffer, và Data Warehouse (Tham chiếu các file `.sql` trong `srcs/00_database/sql/`).
- Pipeline hoàn chỉnh đã tự động hóa việc đẩy dữ liệu từ S3, chạy qua script `02_run_hybrid_imputation.py` và `02_iqr_rolling.py` thành công. Log thực tế minh chứng hệ thống có thể xử lý lượng dữ liệu khổng lồ của 42 trạm điện mà không quá tải ổ cứng nhờ DVC và Parquet.

**2. Insight Kinh doanh đã kiểm chứng:**
- **Suy hao do nhiệt (Thermal Degradation):** Các biểu đồ trong [thong_ke_mo_ta.ipynb](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/notebooks/thong_ke_mo_ta.ipynb) chứng minh rõ: Khi nhiệt độ môi trường vượt quá 25°C, hiệu suất các tấm pin suy giảm đáng kể dù cường độ bức xạ đạt đỉnh (Peak Irradiance).
- **Cảnh báo Bảo trì:** Thuật toán Rolling IQR đã xác định được những ngày bức xạ cao nhưng flag Outlier bị bật (Sản lượng tiệm cận 0). Đây là bằng chứng thực tế chỉ điểm chính xác các trạm đang gặp sự cố hỏng hóc hoặc bị phủ mây dày/bụi bẩn cục bộ.

---

## V. THUẬN LỢI, KHÓ KHĂN & ĐỊNH HƯỚNG MỞ RỘNG

**1. Thuận lợi & Khó khăn:**
- *Thuận lợi:* Việc chia nhỏ Data Pipeline ra thành các thư mục `01_extract`, `02_transform`, `03_load` kết hợp Python Orchestrator giúp module hóa code, dễ dàng test và debug. Sức mạnh của Pandas giúp tính toán Rolling IQR nhanh gấp nhiều lần so với truy vấn SQL.
- *Khó khăn:* Việc áp dụng `Galaxy Schema` mất rất nhiều công sức thiết kế và viết lệnh join truy vấn phức tạp. Sự xuất hiện của quá nhiều thuật toán làm sạch (Linear, Cubic, Regression) đòi hỏi nhóm phải tinh chỉnh cấu hình (như `gap_linear_max_rows` hay ngưỡng `NIGHT_TOLERANCE` trong file YAML) cực kỳ cẩn thận để tránh làm bóp méo dữ liệu tự nhiên.

**2. Định hướng tiếp theo (Next Steps):**
- **Xây dựng Data Mart & Trực quan hóa:** Số liệu sạch hiện tại sẽ được tổng hợp thành BI Mart để kết nối trực tiếp vào Tableau/PowerBI, cung cấp giao diện Dashboard tương tác cho người vận hành (Scrum 7).
- **Forecast (Machine Learning):** Sử dụng dữ liệu ML Mart để bắt đầu huấn luyện các mô hình dự báo sản lượng (ARIMA, Prophet) nhằm dự đoán năng lực cung cấp điện năng của 42 trạm cho ngày hôm sau.

---
*Báo cáo cung cấp góc nhìn sâu sát vào mã nguồn và thuật toán thực tế, chuẩn bị cho buổi Review Hội đồng.*
