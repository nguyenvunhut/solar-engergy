# Phân tích Hiệu suất và Dự báo Sản lượng Hệ thống Điện Mặt Trời

> [!NOTE]
> Dự án tốt nghiệp Chuyên ngành Xử lý Dữ liệu — Trường Cao đẳng FPT Polytechnic (Cơ sở TP. Hồ Chí Minh).  
> **Nhóm thực hiện:** **The Outliers**  
> **Giảng viên hướng dẫn:** Văn Công Khanh

---

## 1. Giới thiệu Dự án
Dự án nhằm mục đích xây dựng một hệ thống phân tích và xử lý dữ liệu toàn diện để phát hiện, xử lý các bất thường và dự báo sản lượng phát điện của 42 trạm điện quang điện (PV) tại Úc. Bằng cách tích hợp dữ liệu vận hành thực tế cùng dữ liệu khí tượng viễn thám từ Open-Meteo, dự án hỗ trợ các nhà quản lý tối ưu hóa hiệu suất vận hành, lên kế hoạch bảo trì chủ động và giảm thiểu rủi ro tài chính.

### Mục tiêu cốt lõi:
1. **Thiết kế Kho dữ liệu đa chiều (Data Warehouse)** tích hợp đồng bộ dữ liệu thời tiết và sản lượng.
2. **Xây dựng Pipeline ETL tự động** làm sạch, lọc nhiễu ban đêm, xử lý dữ liệu khuyết thiếu và giải quyết lệch pha tần suất dữ liệu (Granularity Mismatch).
3. **Khám phá Dữ liệu (EDA) và Phân tích Insight** về tác động của thời tiết (nhiệt độ, mây che phủ) đến hiệu suất tấm pin.
4. **Huấn luyện các mô hình dự báo Baseline** (ARIMA, Prophet) phục vụ bảo trì dự đoán.
5. **Trực quan hóa Dashboard** trực quan sinh động trên Tableau.

---

## 2. Kiến trúc Kho dữ liệu (Data Warehouse)
Hệ thống lưu trữ trên nền tảng **Supabase (PostgreSQL)** sử dụng kiến trúc **Lược đồ Thiên hà (Galaxy Schema / Fact Constellation)** để đồng thời phục vụ hai bảng sự kiện có tần suất dữ liệu khác nhau (Sản lượng: 15 phút, Thời tiết: 1 giờ).

Sơ đồ bảng chi tiết xem tại file thiết kế hệ thống [create_table.sql](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/ultils/create_table.sql).

### Bảng Dimension (Chiều dùng chung):
* [dim_solar_site](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/ultils/create_table.sql#L7-L16): Thông tin kỹ thuật trạm (Số tấm pin, Inverter, Công suất cực đại kWp...).
* [dim_geography](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/ultils/create_table.sql#L18-L25): Tọa độ địa lý (Vĩ độ, kinh độ, tên khu vực).
* [dim_date](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/ultils/create_table.sql#L27-L37): Trục ngày (ngày, tháng, năm, cờ ngày lễ/học kỳ/kỳ thi).
* [dim_time](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/ultils/create_table.sql#L39-L45): Trục giờ (chu kỳ 15 phút).
* [dim_weather_type](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/ultils/create_table.sql#L47-L54): Phân loại mã thời tiết WMO và ngày/đêm.

### Bảng Fact (Sự kiện):
* [fact_solar_energy_gen](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/ultils/create_table.sql#L61-L75): Đo lường sản lượng điện thực tế phát ra (`energy_generated_kwh`).
* [fact_weather](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/ultils/create_table.sql#L77-L103): Lưu trữ các thông số thời tiết (nhiệt độ, bức xạ sóng ngắn, mây che phủ, lượng mưa, tốc độ gió...).

---

## 3. Quy trình ETL và Chuẩn hóa Dữ liệu

### Bước 1: Trích xuất (Extract)
* Dữ liệu sản lượng trạm được đọc từ các tệp CSV gốc.
* Dữ liệu thời tiết được gọi tự động từ **Open-Meteo Archive API** sử dụng tọa độ của 42 trạm. Mã nguồn tích hợp cơ chế bắt lỗi giới hạn lượt truy cập (Rate Limit - HTTP 429) tự dừng 60 giây và thử lại để đảm bảo pipeline ổn định.

### Bước 2: Biến đổi (Transform)
* **Xử lý lệch pha dữ liệu:** Quy trình tự động gom cụm dữ liệu sản lượng (từ 15 phút lên 1 giờ) để đồng bộ hóa hoàn toàn với dữ liệu thời tiết phục vụ mô hình học máy.
* **Lọc nhiễu ban đêm (Night Noise Filter):** Loại bỏ sản lượng điện ảo ghi nhận vào ban đêm do rò rỉ dòng điện hoặc nhiễu thiết bị cảm biến (khi bức xạ mặt trời = 0).
* **Nội suy (Interpolation):** Sử dụng phương pháp nội suy tuyến tính để điền các khoảng trống dữ liệu thời tiết bị khuyết thiếu.
* **Phát hiện bất thường (Outliers):** Áp dụng phương pháp khoảng tứ phân vị (IQR) để loại bỏ các điểm đột biến nhiễu của cảm biến.

### Bước 3: Nạp (Load)
* Dữ liệu sau khi làm sạch được nạp vào Supabase thông qua thư viện kết nối **`pg8000`** (Pure Python, giúp chạy ổn định trên mọi môi trường và hệ điều hành).
* Sử dụng kết nối qua **Supabase Connection Pooler** giúp quản lý luồng tải đồng thời hiệu quả từ nhiều thành viên nhóm mà không bị quá tải kết nối.

---

## 4. Các Insight Kinh doanh và Phân tích chuyên sâu (Business Insights)

* **Hiện tượng suy hao do nhiệt (Thermal Degradation):** Dữ liệu cho thấy khi nhiệt độ môi trường vượt quá $25^\circ\text{C}$, hiệu suất chuyển đổi của các tấm pin PV bị suy giảm mạnh. Đây là lý do tại sao công suất buổi trưa có bức xạ cao nhất nhưng sản lượng điện thực tế đôi khi không đạt đỉnh kỳ vọng.
* **Độ nhiễu ban đêm và Dòng rò (Night Noise):** Phát hiện dòng điện rò rỉ nhẹ tại một số trạm vào khung giờ đêm ($18\text{h} - 5\text{h}$). Nếu không lọc bỏ trong pha ETL, tổng sản lượng báo cáo hàng năm sẽ bị sai lệch lũy kế.
* **Dự báo Baseline để Bảo trì Dự đoán (Predictive Maintenance):** Sử dụng mô hình ARIMA và Prophet để thiết lập sản lượng dự kiến (đường cơ sở). Nếu sản lượng thực tế sụt giảm đáng kể so với baseline trong khi bức xạ vẫn cao, hệ thống sẽ tự động phát tín hiệu cảnh báo tấm pin bị bám bụi bẩn nặng hoặc Inverter bị lỗi để cử đội kỹ thuật xử lý.

---

## 5. Cấu trúc Thư mục Dự án

```
datn_outlier_hs_nlmt/
├── data/
│   ├── raw/                  <- Dữ liệu gốc thu thập ban đầu
│   ├── interim/              <- Dữ liệu trung gian đang xử lý
│   ├── processed/            <- Dữ liệu sạch đầu ra
│   └── external/             <- Dữ liệu phụ từ bên ngoài
├── notebooks/                <- Jupyter notebooks nghiên cứu và vẽ biểu đồ
├── models/                   <- Lưu trữ các mô hình học máy đã huấn luyện
├── reports/                  <- Báo cáo tốt nghiệp & Hình ảnh biểu đồ
│   ├── DATN_OUTLIERS_REPORT.pdf  <- File báo cáo PDF chính thức
│   ├── DATN_OUTLIERS_REPORT.tex  <- File nguồn LaTeX cấu trúc báo cáo
│   └── figures/              <- Các biểu đồ báo cáo
├── du_an_tot_nghiep/         <- Package Python lõi của dự án
│   ├── config.py             <- Cấu hình tham số dự án
│   ├── database.py           <- Kết nối và truy vấn CSDL
│   ├── dataset.py            <- Tiền xử lý tập dữ liệu cho mô hình
│   ├── features.py           <- Tạo đặc trưng huấn luyện
│   ├── plots.py              <- Vẽ biểu đồ trực quan
│   └── modeling/
│       ├── train.py          <- Huấn luyện mô hình
│       └── predict.py        <- Dự báo sản lượng điện
├── ultils/                   <- Các công cụ và mã nguồn ETL phụ trợ
│   ├── Crawl_data_Updatev2.ipynb <- Notebook crawl dữ liệu thời tiết tự động
│   ├── commit_helper.py      <- Script hỗ trợ kiểm tra định dạng Git commit
│   ├── create_table.sql      <- Lược đồ khởi tạo bảng trên Supabase
│   ├── test_create_table.py  <- Script python kiểm tra kết nối & tạo bảng
│   ├── test_insert_csv.py    <- Script test import dữ liệu
│   └── script/
│       ├── supabase_storage.py   <- Công cụ đồng bộ lưu trữ tệp lên cloud storage
│       ├── etl/
│       │   ├── load_01_dims.py   <- ETL tải dữ liệu vào các bảng Dimension
│       │   ├── load_02_facts.py  <- ETL tải dữ liệu vào các bảng Fact
│       │   └── load_03_verify.py <- Kiểm tra và xác thực dữ liệu sau nạp
│       └── upload_dataraw/
│           ├── check_mapping.py  <- Kiểm tra đối xạ ánh xạ cột dữ liệu
│           ├── check_null.py     <- Thống kê tỷ lệ dữ liệu khuyết thiếu
│           ├── upload_raw.py     <- Tải dữ liệu thô lên Cloud
│           └── verify_upload.py  <- Xác thực tính toàn vẹn tệp tải lên
├── requirements.txt          <- Danh sách các thư viện cần cài đặt
└── pyproject.toml            <- Cấu hình cài đặt package dự án
```

---

## 6. Hướng dẫn Cài đặt & Sử dụng

> [!IMPORTANT]
> Dự án yêu cầu phiên bản **Python 3.11+** được cấu hình sẵn trên máy.

### Bước 1: Tạo môi trường ảo (Virtual Environment)

**Windows:**
```powershell
py -m venv .venv
```

**Linux / macOS:**
```bash
python3 -m venv .venv
```

### Bước 2: Kích hoạt môi trường ảo

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```
*Lưu ý: Nếu PowerShell báo lỗi phân quyền, chạy lệnh sau trước rồi kích hoạt lại:*
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

Khi kích hoạt thành công, bạn sẽ thấy ký hiệu `(.venv)` ở đầu dòng lệnh.

### Bước 3: Cài đặt các thư viện phụ thuộc

Cài đặt tất cả các gói thư viện bao gồm các thư viện ETL, CSDL, máy học, và chế độ gói tự chỉnh sửa (`-e .`):
```bash
pip install -r requirements.txt
```

### Bước 4: Chạy Pipeline ETL nạp dữ liệu vào Supabase
1. Tạo tệp cấu hình `.env` dựa trên [env.example](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/.env.example) và điền thông tin kết nối Supabase của bạn.
2. Khởi tạo cấu trúc các bảng dữ liệu:
   ```bash
   python ultils/test_create_table.py
   ```
3. Chạy ETL tải các bảng Dimension:
   ```bash
   python ultils/script/etl/load_01_dims.py
   ```
4. Chạy ETL tải các bảng Fact:
   ```bash
   python ultils/script/etl/load_02_facts.py
   ```
5. Chạy xác thực dữ liệu:
   ```bash
   python ultils/script/etl/load_03_verify.py
   ```

### Bước 5: Hủy kích hoạt môi trường ảo (khi hoàn thành)
```bash
deactivate
```

---

## 7. Quy tắc Commit Git & Quản lý Dự án
Nhóm áp dụng quy tắc commit nghiêm ngặt theo định dạng Angular commit convention:
```
<type>(<scope>): [JIRA-KEY] <subject>
```

**Ví dụ:** `feat(db): [SCRUM-40] add local ETL pipeline and supabase storage connector`

*Bạn có thể sử dụng bộ hỗ trợ commit tích hợp sẵn tại file [commit_helper.py](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/ultils/commit_helper.py) để kiểm tra tính hợp lệ trước khi đẩy mã nguồn lên GitHub.*
