# Hướng Dẫn Chạy Pipeline

## Thứ tự chạy từng bước (local trước, cloud sau)

**Bước 0a: Download raw data từ Kaggle** ← Chạy 1 lần duy nhất
```bash
python srcs/01_extract/01_download_kaggle_raw.py
```

**Bước 0b: Download dữ liệu thời tiết Open Meteo** ← Chạy 1 lần duy nhất
```bash
python srcs/01_extract/02_download_open_meteo_raw.py
```

**Bước 0c: Upload raw data lên Object Storage** ← Chạy 1 lần duy nhất
```bash
python srcs/03_load/01_upload_raw_to_object_storage/01_run_upload.py
```

**Bước 1: Staging**
```bash
python srcs/06_run_pipeline/main.py --stage staging
```

**Bước 2: Transform**
```bash
python srcs/06_run_pipeline/main.py --stage transform
```

**Bước 3: Imputation** ← Điền giá trị NULL trong `staging.fact_solar_energy_gen`
```bash
python srcs/06_run_pipeline/main.py --stage imputation
```
> Validate sau bước này: `null = 0`, `energy sum ≈ 9,205,528.60`

**Bước 4: Generate Outliers**
```bash
python srcs/06_run_pipeline/main.py --stage generate_outliers
```

**Bước 5: Apply Outlier Flags**
```bash
python srcs/06_run_pipeline/main.py --stage outlier
```
> Validate sau bước này: `outlier count ≈ 100,822`

**Bước 6: Load Data Warehouse**
```bash
python srcs/06_run_pipeline/main.py --stage load
```

**Bước 7: Build Data Marts**
```bash
python srcs/06_run_pipeline/main.py --stage marts
```

---

## Chạy tất cả 1 lệnh (sau khi đã validate local xong)
```bash
python srcs/06_run_pipeline/main.py --stage all
```

---

## Lưu ý
- Chạy và validate **local trước**, đảm bảo số liệu khớp Cloud mới deploy lên Cloud.
- Giữa các bước khi chạy `--stage all` hệ thống tự nghỉ (sleep) để nhả RAM và Connection Pool, tránh sập DB Cloud.
- Thay đổi sleep time tại: `config/05_run_pipeline/pipeline.yaml`
- Thay đổi thông số nghiệp vụ BI tại: `config/04_machine_learning/01_bi_mart_params.yaml`
- Thay đổi thông số outlier tại: `config/02_transform/01_generate_outliers.yaml`
