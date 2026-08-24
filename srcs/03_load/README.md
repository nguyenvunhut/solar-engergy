# PHÂN HỆ NẠP DỮ LIỆU KHO (03_LOAD)

Phân hệ `srcs/03_load/` chịu trách nhiệm vận chuyển và nạp dữ liệu tuần tự qua 3 tầng: từ máy cục bộ lên S3 Object Storage, từ S3 vào tầng đệm Staging, và từ các bảng đệm sạch vào Kho Dữ liệu Chuẩn hóa (Galaxy Data Warehouse).

---

## 1. CÁC MODULE NẠP DỮ LIỆU

| Module | Chức Năng Kỹ Thuật | Tầng Dữ Liệu Đích |
| :--- | :--- | :--- |
| **`01_upload_raw_to_object_storage/`** | Đẩy toàn bộ tệp CSV thô viễn thám IoT và khí tượng lên Supabase Storage bucket `raw-data`. | S3 Object Storage |
| **`02_load_object_storage_to_staging/`** | Tải luồng dữ liệu từ S3 và nạp vào các bảng tạm không ràng buộc trong schema `staging`. | Schema `staging` |
| **`03_load_buffers_to_datawarehouse/`** | Nạp dữ liệu đã điền khuyết và lọc dị thường vào 5 bảng Dimension và 2 bảng Fact có ràng buộc toàn vẹn khóa. | Schema `datawarehouse` |

---

## 2. HƯỚNG DẪN THỰC THI

```bash
# Nạp dữ liệu sạch vào Kho Dữ liệu Galaxy DWH:
python srcs/06_run_pipeline/main.py --stage load
```
