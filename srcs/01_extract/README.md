# PHÂN HỆ THU THẬP NGUỒN DỮ LIỆU (01_EXTRACT)

Phân hệ `srcs/01_extract/` chịu trách nhiệm thu thập và tải dữ liệu từ 2 nguồn chính của dự án về hệ thống cục bộ và đẩy lên kho lưu trữ đối tượng S3 Object Storage.

---

## 1. CÁC MODULE THU THẬP

| Tệp Xử Lý | Nguồn Dữ Liệu | Khối Lượng Bản Ghi | Đặc Điểm Kỹ Thuật |
| :--- | :--- | :---: | :--- |
| **`01_download_kaggle_raw.py`** | Kaggle Telemetry Dataset (La Trobe University) | $2.731.946$ dòng | Tự động tải và giải nén dữ liệu đo lường viễn thám chu kỳ 15 phút của 42 trạm phát qua Kaggle API. |
| **`02_download_open_meteo_raw.py`** | Open-Meteo REST API (Mô hình ERA5-Land) | $850.752$ dòng | Thu thập dữ liệu khí tượng tái phân tích cấp 1 giờ cho 5 tọa độ cơ sở trường học (Bundoora, Bendigo, Albury-Wodonga, Mildura, Shepparton). Tích hợp cơ chế Exponential Backoff để xử lý Rate Limit. |

---

## 2. HƯỚNG DẪN THỰC THI

```bash
# Tải dữ liệu viễn thám IoT 42 trạm phát từ Kaggle:
python srcs/01_extract/01_download_kaggle_raw.py

# Thu thập dữ liệu thời tiết ERA5-Land từ Open-Meteo:
python srcs/01_extract/02_download_open_meteo_raw.py
```
