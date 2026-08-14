# MÃ NGUỒN LÕI (CORE SOURCE CODE)

Thư mục `srcs/` chứa toàn bộ mã nguồn xử lý trung tâm của hệ thống phân tích và dự báo sản
lượng điện mặt trời. Hệ thống được viết bằng Python 3.10+ theo tư duy hướng module để dễ dàng
mở rộng và bảo trì.

---

## LUỒNG HOẠT ĐỘNG (DATA FLOW)

Luồng hoạt động tuân theo triết lý Pipeline ETL (Extract – Transform – Load). Mỗi bước nằm
trong một thư mục riêng, đánh số theo đúng thứ tự chạy:

1. **`00_database/` và `00_utils/`** — kịch bản SQL khởi tạo Schema (Staging, BI Mart); công cụ
   kết nối Supabase bằng `psycopg2` và quản lý S3 Storage. **Cũng chứa bước vá thời tiết nhân
   quả — xem mục riêng bên dưới, đây là chỗ dễ sai nhất của cả dự án.**
2. **`01_extract/`** — tải dataset Kaggle và crawl thời tiết Open-Meteo, có cơ chế thử lại khi
   bị giới hạn truy cập.
3. **`02_transform/`** — làm sạch, điền khuyết, đồng bộ chu kỳ thời gian, dán nhãn bất thường.
4. **`03_load/`** — nạp dữ liệu sạch vào Supabase (bảng Dimension và Fact).
5. **`04_build_data_marts/`** — dựng **BI Mart** (Tableau) và **ML Mart** (đầu vào huấn luyện),
   tính KPI (Capacity Factor, YTD, MTD).
6. **`05_machine_learning/pipeline/`** — pipeline huấn luyện và đánh giá mô hình dự báo. Có CLI
   riêng, **không** chạy bằng `06_run_pipeline/main.py`.
7. **`06_run_pipeline/`** — Orchestrator cho các bước 1–4.
8. **`07_dashboard/`** — Streamlit + FastAPI phục vụ kết quả.

---

## CHUẨN BỊ MÔI TRƯỜNG

Mọi lệnh dưới đây chạy từ **thư mục gốc kho mã**:

```bash
cd Du_An_Tot_Nghiep_v3
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # điền DB_HOST/DB_USER/DB_PASSWORD, khoá S3...
```

Kiểm tra kết nối trước khi chạy bất cứ thứ gì:

```bash
python tests/test_db_connection.py
```

---

## PHẦN 1 — ETL (bước 1 đến 4)

```bash
# Chạy toàn bộ
python srcs/06_run_pipeline/main.py --stage all

# Hoặc từng bước
python srcs/06_run_pipeline/main.py --stage transform
```

Giá trị `--stage` hợp lệ: `all, staging, transform, imputation, generate_outliers, outlier,
outlier_to_mlmarts, load, bimarts, mlmarts, bi_view`.

`--dry-run` chỉ dùng được với `transform`, `imputation`, `outlier`, `outlier_to_mlmarts` —
nó đếm số dòng rồi rollback giao dịch, không đụng vào cơ sở dữ liệu.

Tham số của từng bước nằm ở `config/<thư-mục-tương-ứng>/`. Sửa YAML, đừng sửa cứng trong mã.

---

## PHẦN 2 — VÁ THỜI TIẾT NHÂN QUẢ (BẮT BUỘC, CHẠY GIỮA ETL VÀ ML)

> **Bỏ qua bước này thì mọi chỉ số phía sau đều vô giá trị.** Không có thông báo lỗi nào
> nhắc bạn — mô hình vẫn train, vẫn ra số đẹp, chỉ là số đó không dùng được.

### Vấn đề

Dữ liệu sản lượng ở lưới **15 phút**, dữ liệu thời tiết ở lưới **1 giờ**. Khi ghép hai bảng,
nếu ghép sai chiều thì một dòng lúc `09:15` có thể nhận thời tiết đo lúc `10:00` — tức là
**mô hình được nhìn thấy tương lai**. Đây là rò rỉ dữ liệu (data leakage) kinh điển và rất
khó phát hiện, vì nó làm kết quả *tốt lên* chứ không phải xấu đi.

### Cách vá

```bash
python srcs/00_utils/04_realign_mlmart_weather.py
```

Script lấy các dòng có **phút = 00** làm quan sát thời tiết chuẩn của giờ đó, rồi gán ngược
cho cả 4 dòng 15 phút trong giờ. Kết quả: `weather_timestamp` luôn **nhỏ hơn hoặc bằng**
`timestamp`, chênh lệch chỉ nhận `-45 / -30 / -15 / 0` phút.

Hai điểm cần biết:

- Script **ghi thẳng vào** `data/mlmart_base/v3_final_cleaned.parquet` (vá tại chỗ), và đánh
  dấu các dòng đã vá bằng `weather_join_method = "raw_hour_causal_manual"`.
- Script **idempotent** — chạy lại nhiều lần vẫn ra cùng kết quả, không hỏng gì.

### Kiểm chứng

```bash
jupyter notebook notebooks/forcasting_v3_energy/00_hotfix_join_causal_audit.ipynb
```

Số liệu đo ngày 08/08/2026 trên `v3_final_cleaned.parquet`: **2.730.100** dòng mang nhãn đã
vá, và **0/2.731.946** dòng dùng thời tiết tương lai.

### Cái bẫy khi chạy pipeline ML

Stage `s01d_weather_causal.py` chạy lại **đúng thuật toán trên** như một lưới an toàn, rồi
đổi nhãn từ `raw_hour_causal_manual` sang `hour_causal_floor`.

Việc đổi tên này **không phải cho đẹp**. Notebook `06_x` có rào chắn từ chối chạy nếu còn
dòng mang nhãn cũ — rào chắn đó viết đúng, vì lúc nó được viết thì nhãn cũ đồng nghĩa với
"chưa vá". Sau khi `04_realign` chạy thật thì nhãn cũ không còn nghĩa đó nữa.

> **Tuyệt đối không đổi tên nhãn vô điều kiện chỉ để đi qua rào chắn.** Trong `s01d`, việc đổi
> tên chỉ xảy ra **sau khi** đã đo `ro_ri_sau == 0`. Ai sửa chỗ này mà bỏ bước đo là tự tay
> gỡ mất cái chuông báo cháy duy nhất của toàn bộ pipeline.

Thứ tự trong `s01d` cũng có chủ đích: **kiểm tra rò rỉ chạy TRƯỚC, đổi nhãn chạy SAU.** Đảo
lại là mất ý nghĩa kiểm chứng.

---

## PHẦN 3 — PIPELINE HỌC MÁY

Pipeline này có CLI riêng, **không** nằm trong `06_run_pipeline/main.py`.

```bash
# Xem 11 giai đoạn
python -u srcs/05_machine_learning/pipeline/run.py --list

# Chạy toàn bộ (khoảng 25 phút trên Intel i5-12450HX, 6 luồng, CPU)
python -u srcs/05_machine_learning/pipeline/run.py --stage all

# Chạy một giai đoạn
python -u srcs/05_machine_learning/pipeline/run.py --stage s08 --loss huber --horizon 1
```

| Giai đoạn | Nội dung | Thời gian |
|---|---|---|
| `s01` | Lưới 15 phút liên tục, ghép khí tượng nhân quả, điền khuyết, phân nhóm bất thường | 2,5 phút |
| `s02` | Tách Development/Test, chia 5 fold TimeSeriesSplit | 0,4 phút |
| `s03` | Đặc trưng thời gian: chu kỳ, lag, rolling | 1,0 phút |
| `s04` | Đặc trưng không gian: hình học mặt trời, downscale bức xạ, quy mô trạm | 0,9 phút |
| `s05` | Đặc trưng tương tác khí tượng, mã hoá biến phân loại | 0,9 phút |
| `s06` | Chẩn đoán VIF và tương quan | 0,2 phút |
| `s07` | Danh sách cấm + Mutual Information, chọn 40 đặc trưng | 1,1 phút |
| `s08` | Huấn luyện LightGBM: 3 hàm mất mát × 2 tầm dự báo | 16 phút |
| `s09` | Chọn mô hình trên validation, chấm điểm tập test | 0,3 phút |
| `s10` | Giải thích mô hình bằng SHAP | 0,8 phút |
| `s11` | Kiểm chứng độ trễ pha theo từng trạm và từng ngày | 0,1 phút |

Chi tiết đầy đủ: `srcs/05_machine_learning/pipeline/README.md`.

### Hai khoá quyết định tính tái lập

```yaml
# config/05_machine_learning/pipeline/runtime.yaml
gpu:
  use_gpu: false
lightgbm:
  deterministic: true
```

LightGBM chỉ hỗ trợ `deterministic` trên CPU. Bật đồng thời cả hai, chương trình **dừng ngay
kèm thông báo** thay vì âm thầm bỏ qua `deterministic` rồi cho ra kết quả không tái lập được.
Cấu hình CPU vừa tái lập được vừa nhanh hơn (31 giây so với 50 giây).

### Nơi ghi kết quả

Pipeline ghi vào thư mục có hậu tố `_new` (`01_reindex_new/`, `06_train_new/`…), **không ghi
đè kết quả notebook**. Đổi ở khoá `output_suffix` trong `paths.yaml`.

---

## PHẦN 4 — CÁC LỆNH NGOÀI LUỒNG CHUẨN

Bốn việc dưới đây **không** nằm trong `--stage all`:

```bash
# Tối ưu siêu tham số bằng Optuna, ghi ra config/.../best_params.json
python -u srcs/05_machine_learning/pipeline/actions/tune_optuna.py --loss huber --horizon 1 --trials 11

# Kiểm chứng lại việc chọn mô hình vô địch, không huấn luyện lại
python -u srcs/05_machine_learning/pipeline/actions/validate_model_selection.py

# Đối chứng Prophet trên ĐÚNG tập test niêm phong (khoảng 9 phút, 40 trạm)
python -u srcs/05_machine_learning/pipeline/actions/baseline_prophet_test_set.py

# Xuất CSV cho Tableau, đúng 11 cột theo hợp đồng với nhóm trưởng
python -u srcs/05_machine_learning/pipeline/actions/xuat_csv_tableau.py
```

Tách Optuna ra khỏi luồng chuẩn để mỗi lần huấn luyện lại không phải chờ tìm siêu tham số.
Luồng chuẩn đọc `best_params.json`; khi tệp chưa có thì dùng `default_params` trong
`train.yaml`, và `s08` in rõ nguồn siêu tham số ở mỗi lần chạy.

> `baseline_prophet_test_set.py` có cờ `--gioi-han-site N` để chạy thử nhanh. Cờ này ghi ra
> thư mục riêng `08_baseline_prophet_test_thu_Nsite/`, không đụng kết quả thật — bản trước đó
> từng làm mất kết quả 40 trạm vì một lần chạy thử 3 trạm ghi đè lên đúng tên tệp.

---

## PHẦN 5 — DASHBOARD VÀ API

```bash
# Streamlit (3 trang)
python -m streamlit run app.py --server.port 8501 --app-dir srcs/07_dashboard

# FastAPI — tài liệu tự sinh ở http://127.0.0.1:8000/docs
python -m uvicorn api:app --port 8000 --app-dir srcs/07_dashboard
```

Toàn bộ logic dự báo nằm ở `srcs/07_dashboard/forecast_service.py`; Streamlit và API **gọi
chung một đường tính** nên không thể lệch kết quả. Tầng giao diện không gọi `model.predict()`
và không tự tính lại chỉ số — nó chỉ vẽ lại artifact pipeline đã ghi.

Ba trang tách theo **bản chất dữ liệu**, không theo chủ đề:

| Trang | Nội dung | Tốc độ |
|---|---|---|
| Time Series & Baseline | Hiệu năng **đã đo** trên tập test + đối chứng Prophet | Nhanh (đọc artifact) |
| Model Explainability | Mô hình học được gì (SHAP) | Nhanh (đọc artifact) |
| Dự báo tới & What-if | Dự báo **sẽ xảy ra** (gọi Open-Meteo) + phân tích độ nhạy | Chậm (gọi mạng) |

> Không gộp trang thứ ba vào trang đầu: đặt dự báo 14 ngày cạnh con số WAPE 17,64% khiến
> người xem đọc con số đó thành độ chính xác của dự báo dài hạn, trong khi nó đo năng lực
> **một bước** (15 phút).

---

## PHẦN 6 — KIỂM CHỨNG

```bash
# So từng byte kết quả pipeline với kết quả notebook (mong đợi: 105/105 khớp)
python -u srcs/05_machine_learning/pipeline/checks/so_sanh_toan_bo.py --chi-tiet

# Xác nhận tập test được giữ kín đến s09
python -u srcs/05_machine_learning/pipeline/checks/audit_test_sealed.py

# Huấn luyện nhiều lần rồi so MD5 — kiểm tra tính tái lập
python -u srcs/05_machine_learning/pipeline/checks/do_tinh_tai_lap_s08.py --so-lan 3

# So ma trận huấn luyện trực tiếp với notebook
python -u srcs/05_machine_learning/pipeline/checks/so_sanh_ma_tran_train.py --loss huber --horizon 1
```

---

## THỨ TỰ CHẠY TỪ ĐẦU ĐẾN CUỐI

```
1. python srcs/06_run_pipeline/main.py --stage all           # ETL, dựng ML Mart
2. python srcs/00_utils/04_realign_mlmart_weather.py         # VÁ THỜI TIẾT — không được bỏ
3. notebook 00_hotfix_join_causal_audit.ipynb                # kiểm chứng đã vá đúng
4. python -u srcs/05_machine_learning/pipeline/run.py --stage all
5. python -u srcs/05_machine_learning/pipeline/actions/baseline_prophet_test_set.py
6. python -u srcs/05_machine_learning/pipeline/checks/so_sanh_toan_bo.py --chi-tiet
7. python -m streamlit run app.py --server.port 8501 --app-dir srcs/07_dashboard
```

Bước 2 và 3 là chỗ duy nhất trong cả quy trình mà **bỏ qua vẫn chạy trót lọt nhưng kết quả
sai hoàn toàn**. Mọi bước khác nếu thiếu điều kiện sẽ báo lỗi và dừng.

---

## XỬ LÝ SỰ CỐ

| Thông báo | Nguyên nhân |
|---|---|
| `Khong tim thay CSV raw ...` | `s01` cần tệp gốc để biết dòng nào là số đo thật — kiểm tra khoá `raw_solar` trong `paths.yaml` |
| `Khong tim thay fold nao trong ...` | Chạy `s02` đến `s07` trước khi chạy `s08` |
| `Ma tran test thieu N dac trung` | Danh sách đặc trưng trong `model_config.json` không khớp dữ liệu — chạy lại từ `s07` |
| `runtime.yaml dang bat CA HAI ...` | Đang bật đồng thời `use_gpu` và `deterministic` — chọn một |
| `con N dong mang nhan join CU` | Chưa chạy `04_realign_mlmart_weather.py` — quay lại Phần 2 |
| Kết quả lệch so với notebook | Chạy `so_sanh_toan_bo.py --chi-tiet`, sửa từ giai đoạn lệch **sớm nhất** (giai đoạn nào lệch thì mọi giai đoạn sau đều lệch theo) |

---

## LƯU Ý VỀ DỮ LIỆU VÀ ARTIFACT

`data/raw/*`, `data/processed/*` và các thư mục artifact lớn nằm ngoài Git (xem `.gitignore`)
— chúng thuộc về DVC và Supabase Storage.

Mô hình đã huấn luyện được đẩy lên bucket **`model_artifacts_v3`** để người sau **không phải
train lại**:

```
model_artifacts_v3/
├── models/     12 tệp  ← 3 hàm mất mát × 2 tầm dự báo × (model.pkl + model_config.json)
├── metrics/     5 tệp  ← best_loss, metrics_overall h1/h4, đối chứng Prophet
└── config/      8 tệp  ← best_params, quy_mo_tram, selected_features + 5 YAML pipeline
```

Bucket **không chứa tệp CSV/parquet dự báo thô** — có model rồi thì sinh lại trong vài giây,
không đáng chiếm dung lượng.
