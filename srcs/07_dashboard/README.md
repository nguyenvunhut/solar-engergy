# Hướng Dẫn Chạy Dashboard & API Dự Báo Quang Điện

Dashboard đọc kết quả mô hình từ `data/model/v4/`. Cần chạy xong pipeline học máy
(`srcs/05_machine_learning/forcasting_pipeline/`) trước khi mở dashboard.

## 1. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

## 2. Khởi chạy FastAPI Backend (cổng 8000)

Từ thư mục gốc repository (`Du_An_Tot_Nghiep_v3`):

```bash
uvicorn api:app --port 8000 --app-dir srcs/07_dashboard
```

Swagger UI: `http://127.0.0.1:8000/docs`

Muốn chạy nền:

```bash
nohup uvicorn api:app --port 8000 --app-dir srcs/07_dashboard > api.log 2>&1 &
```

## 3. Khởi chạy Streamlit Dashboard

Mở terminal mới, cũng từ gốc repository:

```bash
streamlit run srcs/07_dashboard/app.py
```

Dashboard mở tại `http://localhost:8501`.

### Chỉ định phiên bản dữ liệu

Mặc định dashboard đọc `data/model/v4/`. Đổi bằng biến môi trường `DASHBOARD_VERSION`:

```bash
# Doc du lieu v4 (mac dinh, khong can dat gi)
streamlit run srcs/07_dashboard/app.py

# Doc mot phien ban khac
DASHBOARD_VERSION=v4_tai_lap streamlit run srcs/07_dashboard/app.py
```

Nếu API chạy ở cổng khác, đặt thêm `DASHBOARD_API_URL`:

```bash
DASHBOARD_API_URL=http://127.0.0.1:9000 streamlit run srcs/07_dashboard/app.py
```

## 4. Ba trang của Dashboard

**Trang 1 - Chuỗi Thời Gian (`1_TimeSeries.py`)**
Lọc theo trạm và khoảng thời gian, xem biểu đồ dự báo so với thực tế, dải min-max theo
giờ, sản lượng cộng dồn, và các chỉ số WAPE / RMSE / MAE.

**Trang 2 - Giải Thích Mô Hình (`2_SHAP.py`)**
Tầm quan trọng đặc trưng toàn cục, biểu đồ beeswarm, dependency plot hai đặc trưng, và
giải thích cục bộ dạng waterfall cho từng dòng dự báo.

**Trang 3 - Dự Báo Tới & What-if (`3_Du_Bao.py`)**
Dự báo cho những ngày phía trước bằng dữ liệu khí tượng lấy trực tiếp từ Open-Meteo, kèm
công cụ thử kịch bản. Tách riêng khỏi trang 1 vì trang 1 chỉ hiển thị số đo được trên tập
test, còn trang này là dự báo cho tương lai.

## 5. Xử lý sự cố

**Dashboard báo không tìm thấy dữ liệu**: kiểm tra `data/model/v4/07_final_test/` đã có
`prediction_audit.parquet` chưa. Chưa có thì chạy pipeline tới giai đoạn `s09`.

**Trang SHAP trống**: cần `data/model/v4/08_explain/`. Chạy giai đoạn `s10`.

**Trang 3 không gọi được Open-Meteo**: kiểm tra kết nối mạng và xem API backend đã chạy chưa.

**Cổng 8501 đã bị chiếm**: `streamlit run srcs/07_dashboard/app.py --server.port 8502`
