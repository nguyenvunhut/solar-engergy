# BỘ KIỂM THỬ VÀ KIỂM TOÁN CHẤT LƯỢNG HỆ THỐNG (TEST SUITE)

Thư mục `tests/` chứa các kịch bản kiểm thử tự động phục vụ việc xác minh tính toàn vẹn dữ liệu, kiểm tra kết nối cơ sở dữ liệu và đánh giá chất lượng đường ống xử lý từ đầu đến cuối.

---

## 1. CÁC HẠNG MỤC KIỂM THỬ CHÍNH

| Tệp Kiểm Thử | Mục Tiêu và Phạm Vi Kiểm Định |
| :--- | :--- |
| **`test_db_connection.py`** | Kiểm tra kết nối tới Supabase PostgreSQL Connection Pooler và xác thực quyền truy cập các schema (`staging`, `datawarehouse`, `bi_mart`, `ml_mart`). |
| **`test_etl_referential_integrity.py`** | Kiểm toán tính toàn vẹn tham chiếu (Referential Integrity) giữa 2 bảng Fact và 5 bảng Dimension trong Lược đồ Thiên hà. |
| **`run_warehouse_tests.py`** | Kiểm thử tự động tổng thể chất lượng dữ liệu kho: đếm số lượng bản ghi ($2.73\text{M}$ dòng 15p, $850\text{k}$ dòng 1h), kiểm tra giá trị null ngoài ý muốn và kiểm tra định dạng dữ liệu. |
| **`PIPELINE_AND_DB_INTEGRATION_TESTS.md`** | Báo cáo chi tiết kết quả thực thi các bài kiểm thử tích hợp giữa đường ống ETL và cơ sở dữ liệu. |

---

## 2. HƯỚNG DẪN CHẠY KIỂM THỬ

```bash
# 1. Kiểm tra kết nối Database & quyền truy cập
python tests/test_db_connection.py

# 2. Kiểm toán tính toàn vẹn tham chiếu kho dữ liệu
python tests/test_etl_referential_integrity.py

# 3. Chạy toàn bộ bộ kiểm thử Data Warehouse
python tests/run_warehouse_tests.py
```
