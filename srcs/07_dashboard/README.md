# HƯỚNG DẪN VẬN HÀNH DASHBOARD & API DỰ BÁO (07_DASHBOARD)

Thư mục `srcs/07_dashboard/` chứa ứng dụng giao diện trực quan hóa Streamlit và dịch vụ Backend FastAPI phục vụ kết quả dự báo sản lượng điện mặt trời từ mô hình Machine Learning.

---

## 1. KHỞI CHẠY HẠ TẦNG DỊCH VỤ

### 1.1. Khởi chạy FastAPI Backend (Cổng 8000)
Backend cung cấp các API suy luận và tích hợp dữ liệu thời tiết trực tiếp từ Open-Meteo REST API:

```bash
uvicorn api:app --port 8000 --app-dir srcs/07_dashboard
```
*Tài liệu Swagger UI kiểm thử trực quan: `http://127.0.0.1:8000/docs`*

### 1.2. Khởi chạy Streamlit Dashboard (Cổng 8501)
```bash
streamlit run srcs/07_dashboard/app.py
```
*Giao diện mở tại: `http://localhost:8501`*

---

## 2. BỐ CỤC 3 TRANG GIAO DIỆN CHUYÊN BIỆT

1. **Trang 1 — Chuỗi Thời Gian (`1_TimeSeries.py`):** Lọc theo từng trạm trong 42 trạm phát và khoảng thời gian quan sát; hiển thị biểu đồ đường dự báo đối chứng với thực tế, dải min-max theo giờ và bảng chỉ số WAPE, RMSE, MAE.
2. **Trang 2 — Giải Thích Mô Hình (`2_SHAP.py`):** Hiển thị tầm quan trọng đặc trưng toàn cục (Feature Importance), biểu đồ phân tán Beeswarm, tương tác giữa các cặp biến và biểu đồ thác nước Waterfall giải thích từng điểm dự báo cục bộ.
3. **Trang 3 — Dự Báo Tương Lai & What-if (`3_Du_Bao.py`):** Dự báo sản lượng tới cho các ngày tiếp theo bằng cách gọi dữ liệu dự báo thời tiết thời gian thực từ Open-Meteo API, hỗ trợ phân tích độ nhạy và thử nghiệm kịch bản thời tiết.

---

## 3. XỬ LÝ SỰ CỐ THƯỜNG GẶP

- **Thông báo thiếu dữ liệu:** Đảm bảo Pipeline ML đã chạy hoàn tất đến bước xuất kết quả test (`data/model/v4/07_final_test/`).
- **Trang SHAP chưa hiển thị:** Kiểm tra tệp giải thích mô hình trong `data/model/v4/08_explain/` (tương ứng giai đoạn `s10`).
- **Cổng 8501 bị chiếm dụng:** Khởi chạy với cổng khác: `streamlit run srcs/07_dashboard/app.py --server.port 8502`.
