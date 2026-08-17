# Pipeline Dự báo Sản lượng Điện Mặt trời (v3)

Bản refactor của luồng notebook `notebooks/forcasting_v3_energy/` thành mã nguồn chạy được
bằng dòng lệnh. Pipeline này **tái lập đúng kết quả notebook**: lần đối chiếu ngày 08/08/2026
cho **105/105 tệp khớp từng byte** (parquet, JSON và CSV — tức khớp cả giá trị, thứ tự cột,
thứ tự dòng và thứ tự khoá JSON).

---

## 1. Chuẩn bị

Mọi lệnh dưới đây chạy từ **thư mục gốc kho mã** (`Du_An_Tot_Nghiep_v3/`), sau khi đã kích
hoạt môi trường ảo của dự án:

```bash
cd Du_An_Tot_Nghiep_v3
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

Kiểm tra nhanh môi trường:

```bash
python -u srcs/05_machine_learning/pipeline/run.py --list
```

Lệnh này liệt kê 11 giai đoạn và cho biết giai đoạn nào đã có mã. Nếu chạy được, môi trường
đã sẵn sàng.

---

## 2. Chạy pipeline

### Chạy toàn bộ

```bash
python -u srcs/05_machine_learning/pipeline/run.py --stage all
```

Thời gian tham khảo (Intel i5-12450HX, 6 luồng, CPU): khoảng **25 phút**, trong đó giai đoạn
huấn luyện `s08` chiếm 16 phút.

### Chạy từng giai đoạn

```bash
python -u srcs/05_machine_learning/pipeline/run.py --stage s01
python -u srcs/05_machine_learning/pipeline/run.py --stage s08 --loss huber --horizon 1
```

| Giai đoạn | Nội dung | Thời gian |
|---|---|---|
| `s01` | Dựng lưới 15 phút liên tục, ghép khí tượng nhân quả, điền khuyết, phân nhóm bất thường | 2,5 phút |
| `s02` | Tách Development/Test, chia 5 fold TimeSeriesSplit | 0,4 phút |
| `s03` | Đặc trưng thời gian: chu kỳ, lag, rolling | 1,0 phút |
| `s04` | Đặc trưng không gian: hình học mặt trời, downscale bức xạ, quy mô trạm | 0,9 phút |
| `s05` | Đặc trưng tương tác khí tượng, mã hoá biến phân loại | 0,9 phút |
| `s06` | Chẩn đoán VIF và tương quan | 0,2 phút |
| `s07` | Danh sách cấm + Mutual Information, chọn 40 đặc trưng | 1,1 phút |
| `s08` | Huấn luyện LightGBM: 3 hàm mất mát × 2 tầm dự báo | 16 phút |
| `s09` | Chọn mô hình trên tập validation, chấm điểm tập test | 0,3 phút |
| `s10` | Giải thích mô hình bằng SHAP | 0,8 phút |
| `s11` | Kiểm chứng độ trễ pha theo từng trạm và từng ngày | 0,1 phút |

### Nơi ghi kết quả

Pipeline ghi vào các thư mục có hậu tố `_new` (`data/model/v3/01_reindex_new/`,
`06_train_new/`, …), **không ghi đè kết quả của notebook**. Quy định ở khoá `output_suffix`
trong `config/05_machine_learning/pipeline/paths.yaml`.

Đặt `output_suffix: ""` sẽ khiến pipeline ghi thẳng lên thư mục kết quả chính thức. Khi đó
`run.py` in cảnh báo trước khi chạy. Chỉ đổi khi đã đối chiếu xong và có quyết định rõ ràng.

---

## 3. Kiểm chứng

### Đối chiếu với kết quả notebook

```bash
python -u srcs/05_machine_learning/pipeline/checks/so_sanh_toan_bo.py
python -u srcs/05_machine_learning/pipeline/checks/so_sanh_toan_bo.py --chi-tiet
```

So từng byte mọi tệp parquet/JSON/CSV giữa hai bên. Thêm `--chi-tiet` để biết tệp nào lệch
và lệch ở đâu (số dòng, danh sách cột, thứ tự cột, từng cột một). Kết quả mong đợi:
`105/105 tệp khớp TỪNG BYTE`.

### Tập test có được giữ kín đến `s09` không

```bash
python -u srcs/05_machine_learning/pipeline/checks/audit_test_sealed.py
```

Quét mã thực thi (đã bỏ chú thích và docstring) để xác nhận `s08` không chạm tập test, và
`s10`/`s11` chỉ dùng lại ảnh chụp do `s09` xuất ra.

### Huấn luyện có tái lập được không

```bash
python -u srcs/05_machine_learning/pipeline/checks/do_tinh_tai_lap_s08.py --so-lan 3
```

Huấn luyện cùng một cấu hình nhiều lần rồi so MD5. Với cấu hình hiện tại (CPU,
`lightgbm.deterministic = true`) cả 3 lần cho ra cùng một tệp.

### So ma trận huấn luyện với chính notebook

```bash
python -u srcs/05_machine_learning/pipeline/checks/so_sanh_ma_tran_train.py --loss huber --horizon 1
```

Thực thi trực tiếp các ô mã của notebook rồi so `X_dev`, `y_dev`, `w_dev` với kết quả của
`s08a`. Đây là phép kiểm mạnh nhất: cùng ma trận và cùng siêu tham số thì LightGBM ở chế độ
tất định cho ra cùng một mô hình.

---

## 4. Hành động ngoài luồng chuẩn

Hai việc dưới đây **không** nằm trong `--stage all`, chạy riêng khi cần:

```bash
# Tối ưu siêu tham số bằng Optuna, ghi ra config/.../best_params.json
python -u srcs/05_machine_learning/pipeline/actions/tune_optuna.py --loss huber --horizon 1 --trials 11

# Kiểm chứng lại việc chọn mô hình vô địch, không huấn luyện lại
python -u srcs/05_machine_learning/pipeline/actions/validate_model_selection.py

# Dựng mô hình đối chứng Prophet
python -u srcs/05_machine_learning/pipeline/actions/baseline_prophet.py
```

Tách Optuna ra khỏi luồng chuẩn để mỗi lần huấn luyện lại không phải chờ tìm kiếm siêu tham
số. Luồng chuẩn đọc `best_params.json`; khi tệp này chưa có thì dùng `default_params` trong
`train.yaml`, và `s08` in rõ nguồn siêu tham số đang dùng ở mỗi lần chạy.

---

## 5. Cấu hình

Toàn bộ tham số nằm ở `config/05_machine_learning/pipeline/`, không có giá trị nào viết cứng
trong mã:

| Tệp | Nội dung |
|---|---|
| `runtime.yaml` | Số luồng, thiết bị tính toán, tính tất định, kiểu dữ liệu ma trận |
| `paths.yaml` | Mọi đường dẫn vào/ra, hậu tố thư mục kết quả |
| `features.yaml` | Ngưỡng vật lý, phân vị, danh sách đặc trưng tất định, danh sách cấm |
| `train.yaml` | Ba biến thể hàm mất mát, siêu tham số mặc định, chính sách trọng số mẫu |
| `data.yaml` | Tần suất lưới, quy tắc tách tập, danh sách trạm loại trừ |
| `best_params.json` | Kết quả Optuna theo từng cặp (hàm mất mát, tầm dự báo) |

### Hai khoá quyết định tính tái lập

```yaml
gpu:
  use_gpu: false                 # runtime.yaml
lightgbm:
  deterministic: true
```

LightGBM chỉ hỗ trợ `deterministic` trên CPU (tài liệu: *"Used only with cpu device type"*).
Bật đồng thời `use_gpu` và `deterministic` sẽ khiến chương trình dừng ngay kèm thông báo,
thay vì âm thầm bỏ qua `deterministic` và cho ra kết quả không tái lập được.

Số đo trên `huber h1` (887.980 dòng × 54 đặc trưng), mỗi cấu hình huấn luyện nhiều lần liên
tiếp cùng máy cùng seed:

| Thiết bị | `gpu_use_dp` | `deterministic` | Các lần chạy | Chênh lệch lớn nhất | Thời gian |
|---|---|---|---|---|---|
| GPU | false | — | 3/3 khác nhau | 7,485e-02 | 24 giây |
| GPU | true | — | 3/3 khác nhau | 1,110e-16 | 24 giây |
| GPU | true | true | 4/6 trùng nhau | 6,939e-18 | 50 giây |
| CPU | — | false | 2/2 khác nhau | 2,220e-16 | 30 giây |
| **CPU** | — | **true** | **3/3 trùng khớp** | **0** | **31 giây** |

Cấu hình CPU vừa tái lập được vừa nhanh hơn cấu hình GPU tiến gần tái lập nhất (31 giây so
với 50 giây), nên không có đánh đổi giữa tốc độ và tính tái lập.

---

## 6. Cấu trúc thư mục

```
pipeline/
  run.py              Điểm chạy duy nhất
  core/               Cấu hình, đường dẫn, đọc/ghi, chỉ số, LightGBM, độ trễ pha
  stages/             s01 → s11, mỗi giai đoạn tách thành các bước con
  actions/            Optuna, kiểm chứng chọn mô hình, đối chứng Prophet
  checks/             Bốn công cụ kiểm chứng ở mục 3
```

Mỗi tệp giữ dưới 200 dòng và có docstring nêu rõ nguồn gốc từ ô mã nào của notebook, kèm lý
do cho những chỗ dễ bị sửa nhầm.

---

## 7. Xử lý sự cố

**`Khong tim thay CSV raw ...`** — giai đoạn `s01` cần tệp gốc để xác định dòng nào là số đo
thật. Kiểm tra khoá `raw_solar` trong `paths.yaml`.

**`Khong tim thay fold nao trong ...`** — chạy `s02` đến `s07` trước khi chạy `s08`.

**`Ma tran test thieu N dac trung`** — danh sách đặc trưng trong `model_config.json` không
khớp dữ liệu hiện có. Chạy lại từ `s07`.

**`runtime.yaml dang bat CA HAI ...`** — xem mục 5, chọn một trong hai chế độ.

**Kết quả lệch so với notebook** — chạy `so_sanh_toan_bo.py --chi-tiet` để biết tệp nào và
lệch ở đâu, rồi lần ngược về giai đoạn sinh ra tệp đó. Giai đoạn nào lệch thì mọi giai đoạn
sau đều lệch theo, nên sửa từ giai đoạn sớm nhất.
