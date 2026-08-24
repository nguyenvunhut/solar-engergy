# PHÂN HỆ CƠ SỞ DỮ LIỆU & LƯỢC ĐỒ (00_DATABASE)

Phân hệ `srcs/00_database/` quản lý toàn bộ các kịch bản DDL SQL khởi tạo cấu trúc CSDL trên PostgreSQL / Supabase, định nghĩa các schema logic và cung cấp các hàm khởi tạo hạ tầng dữ liệu.

---

## 1. CÁC SCHEMA CHÍNH TRONG CƠ SỞ DỮ LIỆU

1. **`staging`**: Tầng đệm lưu trữ dữ liệu thô ban đầu, hỗ trợ tiếp nhận dữ liệu không đồng nhất từ viễn thông IoT và API khí tượng.
2. **`datawarehouse`**: Kho dữ liệu trung tâm chuẩn hóa theo **Lược đồ Thiên hà (Galaxy Schema / Fact Constellation)**:
   - **2 Bảng Fact:** `fact_solar_energy_gen` ($2.73\text{M}$ dòng 15p) và `fact_weather` ($850\text{k}$ dòng 1h).
   - **5 Bảng Dimension Conformed:** `dim_solar_site`, `dim_geography`, `dim_date`, `dim_time`, `dim_weather_type`.
3. **`bi_mart`**: Tầng phục vụ Business Intelligence, chứa Materialized View `mv_bi_mart_hourly_measures` nén về độ hạt 1 giờ và tiền tính toán các chỉ số $PR_{\text{actual}}$, $PR_{\text{adjusted}}$, $Loss_{\text{temp}}$.
4. **`ml_mart`**: Tầng phục vụ Machine Learning, chứa bảng `ml_mart_base` tích hợp 52 đặc trưng trễ, thiên văn và tương tác vi khí hậu.

---

## 2. DANH MỤC TỆP SQL NGUỒN

- **`sql/create_staging.sql`**: Tạo các bảng tạm và bảng đệm buffer trong schema `staging`.
- **`sql/create_datawarehouse.sql`**: Tạo toàn bộ cấu trúc 5 bảng Dimension và 2 bảng Fact có đầy đủ ràng buộc khóa chính (PK) và khóa ngoại (FK) trong schema `datawarehouse`.
- **`sql/create_buffers.sql`**: Tạo các bảng đệm trung gian phục vụ quy trình ETL phân đoạn.
