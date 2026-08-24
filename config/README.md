# QUẢN LÝ CẤU HÌNH HỆ THỐNG (CONFIGURATION MANAGEMENT)

Thư mục `config/` chứa toàn bộ các tệp cấu hình tham số dạng YAML và JSON phục vụ điều phối các giai đoạn ETL, nạp cơ sở dữ liệu và huấn luyện mô hình Machine Learning.

---

## 1. CẤU TRÚC PHÂN CẤP CẤU HÌNH

```
config/
├── 01_extract/          # Cấu hình tham số thu thập dữ liệu
│   └── extract_config.yaml # Endpoint API Open-Meteo, tọa độ 5 cơ sở, số lượt thử lại
├── 02_transform/        # Cấu hình các thuật toán tiền xử lý & phát hiện dị thường
│   ├── imputation.yaml  # Ngưỡng góc nâng mặt trời (-0.833°), cửa sổ nội suy tuyến tính & PCHIP
│   └── outlier.yaml     # Tham số CART (max_depth=5), GMM (K=2), Isolation Forest (contamination=0.03)
├── 03_load/             # Cấu hình ánh xạ bảng CSDL
│   └── load_config.yaml # Tên schema (staging, datawarehouse), quy tắc mapping khóa chính/khóa ngoại
├── 04_machine_learning/ # Cấu hình thử nghiệm ML v4
└── 05_machine_learning/ # Cấu hình Pipeline Machine Learning Production v5
    └── pipeline/
        ├── paths.yaml          # Đường dẫn tệp đầu vào/đầu ra và hậu tố phiên bản
        ├── runtime.yaml        # Cấu hình thiết bị (CPU/GPU) và cờ deterministic
        ├── split.yaml          # Cấu hình tỷ lệ phân chia Train/Validation/Test và 5-Fold TimeSeriesSplit
        ├── features.yaml       # Danh sách biến loại trừ và cấu hình kỹ nghệ đặc trưng
        ├── train.yaml          # Siêu tham số mặc định LightGBM (Huber Loss, learning rate, num_leaves)
        └── best_params.json    # Siêu tham số tối ưu tìm được bởi Optuna Bayesian Optimization
```

---

## 2. NGUYÊN TẮC CẤU HÌNH

1. **Không Hardcode Tham số trong Mã nguồn:** Toàn bộ hằng số kỹ thuật, ngưỡng rào chắn vật lý và siêu tham số mô hình được quản lý tập trung tại `config/`.
2. **Tính Tái lập Nghiêm ngặt:** Tệp `runtime.yaml` thiết lập `deterministic: true` trên môi trường CPU để đảm bảo kết quả huấn luyện hoàn toàn nhất quán giữa các lần thực thi.
