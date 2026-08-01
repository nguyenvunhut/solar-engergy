# Hướng Dẫn Chạy Dashboard & API Dự Báo Quang Điện

## 1. Cài đặt các thư viện cần thiết
```bash
pip install streamlit fastapi uvicorn requests plotly shap pandas numpy
```

## 2. Khởi chạy FastAPI Backend Server (Cổng 8000)
Từ thư mục gốc của repository (`Du_An_Tot_Nghiep_v3`):
```bash

```
API Swagger UI sẽ sẵn sàng tại: `http://127.0.0.1:8000/docs`

## 3. Khởi chạy Giao diện Streamlit Dashboard
Mở một cửa sổ terminal mới từ gốc repository và chạy:
```bash
streamlit run srcs/07_dashboard/app.py
```
Dashboard sẽ hiển thị trên trình duyệt tại: `http://localhost:8501`

---
### Các Trang Dashboard:
1. **Chuỗi Thời Gian & Dự Báo (`1_TimeSeries.py`):** Lọc theo trạm, thời gian, xem biểu đồ dự báo vs thực tế, min-max band theo giờ, sản lượng cộng dồn, và chỉ số hiệu năng WAPE/RMSE/MAE.
2. **Giải Thích Mô Hình (`2_SHAP.py`):** Tầm quan trọng đặc trưng global, phân bố beeswarm scatter, dependency plot 2 đặc trưng, giải thích cục bộ waterfall cho từng dòng dự báo.
