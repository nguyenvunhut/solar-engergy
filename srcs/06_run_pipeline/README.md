# BỘ ĐIỀU PHỐI ĐƯỜNG ỐNG DỮ LIỆU TẬP TRUNG (06_RUN_PIPELINE)

Phân hệ `srcs/06_run_pipeline/` cung cấp giao diện dòng lệnh (CLI Orchestrator) duy nhất để điều phối và thực thi tuần tự hoặc theo từng giai đoạn toàn bộ đường ống ETL, tiền xử lý, nạp kho dữ liệu và xây dựng Data Marts.

---

## 1. CÁC TÙY CHỌN ĐIỀU PHỐI (CLI OPTIONS)

Điểm nhập lệnh chính là tệp `main.py`:

```bash
python srcs/06_run_pipeline/main.py --stage <TÊN_GIAI_ĐOẠN> [TÙY_CHỌN]
```

### Danh mục `--stage` được hỗ trợ:
| Tham Số Giai Đoạn | Hành Động Thực Hiện |
| :--- | :--- |
| **`all`** | Chạy toàn bộ đường ống tuần tự từ Staging đến nạp Data Marts. |
| **`staging`** | Nạp dữ liệu thô vào tầng đệm schema `staging`. |
| **`imputation`** | Thực hiện điền khuyết nhân quả 4 cấp độ trên $1.536.000$ ô khuyết. |
| **`outlier`** | Áp dụng mô hình lai GMM-IF và 5 rào chắn vật lý ($104$ giờ ngoại lai). |
| **`load`** | Nạp dữ liệu sạch vào Lược đồ Thiên hà trong schema `datawarehouse`. |
| **`bimarts`** | Khởi tạo và nạp Materialized View `bi_mart.mv_bi_mart_hourly_measures`. |
| **`mlmarts`** | Xây dựng bảng cơ sở `ml_mart.ml_mart_base` phục vụ Machine Learning. |

---

## 2. CHẾ ĐỘ CHẠY THỬ NGHIỆM (DRY-RUN)

Đối với các giai đoạn biến đổi dữ liệu lớn (`transform`, `imputation`, `outlier`), có thể thêm cờ `--dry-run` để kiểm tra số lượng bản ghi và logic mà không làm thay đổi dữ liệu trong CSDL:

```bash
python srcs/06_run_pipeline/main.py --stage imputation --dry-run
```
