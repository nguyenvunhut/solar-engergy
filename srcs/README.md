# MÃ NGUỒN LÕI HỆ THỐNG (CORE SOURCE CODE)

Thư mục `srcs/` chứa toàn bộ mã nguồn xử lý trung tâm của hệ thống bao gồm đường ống ETL, tiền xử lý điền khuyết nhân quả, phát hiện dị thường lai, nạp kho dữ liệu Galaxy Schema, xây dựng tầng Data Marts phục vụ BI và huấn luyện mô hình Machine Learning dự báo sản lượng quang điện.

Hệ thống được phát triển bằng Python 3.10+ theo cấu trúc module hóa độc lập, tuân thủ nguyên tắc Single Responsibility và hỗ trợ điều phối tập trung.

---

## 1. TỔ CHỨC CÁC PHÂN HỆ MÃ NGUỒN

```
srcs/
├── 00_database/        # Kịch bản DDL SQL khởi tạo Schema (Staging, DWH, Data Marts) và quản lý kết nối
├── 00_utils/           # Thư viện tiện ích dùng chung: logger, kết nối S3/DB, công cụ vá dữ liệu nhân quả
├── 01_extract/         # Module thu thập dữ liệu viễn thám IoT và crawl thời tiết ERA5-Land
├── 02_transform/       # Module điền khuyết 4 cấp độ và phát hiện dị thường lai GMM-IF + 5 rào chắn vật lý
├── 03_load/            # Module nạp dữ liệu tuần tự vào Staging và Data Warehouse
├── 04_build_data_marts/# Module xây dựng Materialized View BI Mart (1h) và Feature Store ML Mart
├── 05_machine_learning/# Pipeline huấn luyện, tối ưu hóa siêu tham số và đánh giá mô hình LightGBM
├── 06_run_pipeline/    # Bộ điều phối tập trung (Orchestrator CLI) cho toàn bộ luồng ETL & DWH
└── 07_dashboard/       # Tầng ứng dụng giao diện phục vụ kết quả dự báo và API tích hợp
```

---

## 2. QUY TRÌNH THỰC THI TOÀN HỆ THỐNG (END-TO-END WORKFLOW)

### Bước 1: Khởi tạo và Kiểm tra Kết nối Hạ tầng
```bash
# Kích hoạt môi trường ảo Python
source .venv/bin/activate  # Trên Windows: .venv\Scripts\activate

# Kiểm tra kết nối CSDL PostgreSQL / Supabase
python tests/test_db_connection.py
```

### Bước 2: Vận hành Toàn bộ Đường ống ETL & Xây dựng Kho Dữ Liệu
```bash
# Thực thi toàn bộ các giai đoạn Extract -> Transform -> Load -> Build Data Marts:
python srcs/06_run_pipeline/main.py --stage all
```

*Các tùy chọn `--stage` đơn lẻ:*
- `extract`: Thu thập dữ liệu IoT và thời tiết.
- `staging`: Nạp dữ liệu thô vào tầng đệm Staging.
- `imputation`: Thực hiện điền khuyết nhân quả 4 cấp độ ($1.536.000$ ô khuyết).
- `outlier`: Nhận diện dị thường bằng mô hình lai GMM-IF và 5 rào chắn vật lý ($104$ giờ ngoại lai).
- `load`: Nạp dữ liệu sạch vào Lược đồ Thiên hà (2 Fact tables, 5 Dimension tables).
- `bimarts`: Khởi tạo Materialized View `bi_mart.mv_bi_mart_hourly_measures` (nén 1 giờ).
- `mlmarts`: Tạo bảng cơ sở `ml_mart.ml_mart_base` (52 đặc trưng).

### Bước 3: Căn chỉnh Nhân quả Khí tượng (Causal Weather Alignment)
Nhằm triệt tiêu tuyệt đối nguy cơ rò rỉ dữ liệu tương lai trước khi bước vào huấn luyện Machine Learning:
```bash
python srcs/00_utils/04_realign_mlmart_weather.py
```

### Bước 4: Huấn luyện và Đánh giá Mô hình Machine Learning
```bash
# Xem danh sách các giai đoạn của Pipeline ML:
python -u srcs/05_machine_learning/forcasting_pipeline/run.py --list

# Chạy toàn bộ 12 giai đoạn Pipeline ML:
python -u srcs/05_machine_learning/forcasting_pipeline/run.py --stage all
```

---

## 3. THÔNG SỐ VÀ KẾT QUẢ ĐẠT ĐƯỢC

- **Tập dữ liệu viễn thám:** $2.731.946$ bản ghi chu kỳ 15 phút từ 42 trạm phát ($P_{\text{stc}} = 2.428\,\text{kWp}$).
- **Tập dữ liệu khí tượng:** $850.752$ bản ghi chu kỳ 1 giờ từ ECMWF ERA5-Land.
- **Tỷ lệ điền khuyết:** $100\%$ hoàn tất trên $1.536.000$ ô khuyết bằng 4 cấp độ nhân quả.
- **Tỷ lệ dị thường vận hành:** $0{,}45\%$ ($104$ giờ ngoại lai) được phân loại và dán nhãn theo 5 nhóm nguyên nhân vật lý.
- **Hiệu năng Tầng BI Mart:** Nén dung lượng $<80\,\text{MB}$, thời gian phản hồi truy vấn $<100\,\text{ms}$.
- **Hiệu năng Dự báo LightGBM:**
  - Tầm $H_1$ ($T+15\text{ phút}$): WAPE = **$17{,}74\%$**, $R^2 = \mathbf{0{,}9243}$, MAE = $1{,}379\,\text{kWh}$.
  - Tầm $H_4$ ($T+60\text{ phút}$): WAPE = **$22{,}62\%$**, $R^2 = \mathbf{0{,}8864}$, MAE = $1{,}759\,\text{kWh}$.
  - Mức cải thiện: Giảm **$49{,}5\%$** sai số so với mô hình cơ sở Prophet.
