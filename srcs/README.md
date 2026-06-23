# MÃ NGUỒN LÕI (CORE SOURCE CODE)

Thư mục `srcs/` chứa toàn bộ mã nguồn xử lý trung tâm của hệ thống phân tích và dự báo sản lượng điện mặt trời. Hệ thống được viết bằng Python 3.10+ theo tư duy hướng module để dễ dàng mở rộng và bảo trì.

---

## LUỒNG HOẠT ĐỘNG (DATA FLOW)

Luồng hoạt động của hệ thống được tuân theo triết lý Pipeline ETL (Extract - Transform - Load). Mỗi bước (stage) nằm trong một thư mục riêng:

1. **`00_database/` và `00_utils/`**:
   - Chứa kịch bản SQL khởi tạo các Schema (Staging, BI Mart).
   - Chứa công cụ kết nối Database (Supabase) bằng `psycopg2` và quản lý S3 Storage (DVC / MinIO / Supabase Storage).

2. **`01_extract/`**:
   - Trích xuất dữ liệu gốc (Extract). Bao gồm script tải dataset từ Kaggle và script crawl dữ liệu thời tiết qua API của Open-Meteo. Có cơ chế tự thử lại (Retry) khi gặp lỗi giới hạn truy cập.

3. **`02_transform/`**:
   - Biến đổi và làm sạch (Transform).
   - Nội suy các dữ liệu bị thiếu hụt, đồng bộ chu kỳ thời gian (ví dụ: chuyển 15 phút thành 1 giờ).
   - Phát hiện và dán nhãn các điểm dữ liệu bất thường (Outliers), lọc nhiễu hệ thống vào ban đêm.

4. **`03_load/`**:
   - Nạp (Load) dữ liệu đã làm sạch vào cơ sở dữ liệu Supabase (vào các bảng Dimension và Fact).

5. **`04_build_data_marts/`**:
   - Xây dựng tầng trình diễn dữ liệu. Tập hợp dữ liệu Fact và Dimension để tạo ra các **BI Mart** (phục vụ vẽ biểu đồ trên Tableau) và **ML Mart** (đầu vào cho huấn luyện mô hình máy học).
   - Tính toán các KPI (Capacity Factor, YTD, MTD).

6. **`05_machine_learning/`**:
   - Chứa mã huấn luyện (Train) mô hình dự báo Baseline (như ARIMA, Prophet) dựa trên dữ liệu từ ML Mart, hỗ trợ nghiệp vụ Bảo trì Dự đoán (Predictive Maintenance).

7. **`06_run_pipeline/`**:
   - **ĐÂY LÀ TRÁI TIM CỦA HỆ THỐNG.** File `main.py` đóng vai trò Orchestrator (người điều phối). Thay vì phải chạy tay từng file ở các thư mục trên, bạn chỉ cần gọi file `main.py` và truyền tham số `--stage`. Script này sẽ quản lý trình tự chạy và ghi log.

---

## CÁCH CHẠY CODE

Để điều khiển luồng code một cách an toàn nhất, bạn đứng ở thư mục gốc (root folder) và chạy:

```bash
# Chạy toàn bộ luồng
python srcs/06_run_pipeline/main.py --stage all

# Hoặc chạy từng luồng nếu bạn chỉ muốn kiểm tra phần Transform
python srcs/06_run_pipeline/main.py --stage transform
```
