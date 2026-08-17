# Pipeline Dự báo Sản lượng Điện Mặt trời

Bản vận hành của luồng học máy: chạy toàn bộ quy trình bằng dòng lệnh, từ điền khuyết
dữ liệu tới giải thích mô hình.

> Thư mục `notebooks/forcasting_v4_energy/` là phần khảo sát, giữ nguyên để tra cứu.
> Không script nào ở đây gọi hay chạy lại notebook.

---

## 1. Chuẩn bị

Mọi lệnh chạy từ **thư mục gốc kho mã**:

```bash
cd Du_An_Tot_Nghiep_v3
source .venv/bin/activate

# Kiem tra moi truong: liet ke cac giai doan
python -u srcs/05_machine_learning/forcasting_pipeline/run.py --list
```

Thư viện đã có đủ trong `requirements.txt`, gồm cả `optuna`, `shap`, `prophet`.

---

## 2. Mười hai giai đoạn

| Giai đoạn | Nội dung | Notebook tương ứng |
|---|---|---|
| `s00` | Điền khuyết siêu dữ liệu và biến khí tượng | `00_fill_null_imputation` |
| `s01` | Lưới 15 phút liên tục, thời tiết nhân quả, nhãn ngoại lai | `01_reindex_mask_outlier` |
| `s02` | Tách Development/Test, chia 3 fold cửa sổ mở rộng | `02_split_time_series` |
| `s03` | Đặc trưng thời gian: chu kỳ, lag, rolling | `03_1_features_time` |
| `s04` | Hình học mặt trời, Haurwitz, quy mô trạm | `03_2_features_spatial` |
| `s05` | Tương tác khí tượng, mã hoá phân loại | `03_3_features_aggregate` |
| `s06` | Chẩn đoán đa cộng tuyến (VIF) | `04_vif_diagnostics` |
| `s07` | Danh sách cấm + Mutual Information, chọn 39 đặc trưng | `05_select_features` |
| `s08` | Huấn luyện LightGBM: 3 hàm mất mát × 2 tầm | `06_1` `06_2` `06_3` |
| `s09` | Chọn mô hình trên validation, chấm tập test | `06_4` `07_final_test` |
| `s10` | Giải thích mô hình bằng SHAP | `08_explainable_ai` |
| `s11` | Đo độ trễ pha theo từng trạm và từng ngày | `09_kiem_chung_tre_pha` |

### Bảy notebook thực nghiệm

Không sinh mô hình, không nằm trong 12 giai đoạn trên. Chúng là các phép thử để chứng minh
những lựa chọn trong luồng chính là hợp lý. Bỏ qua thì mô hình vẫn ra đúng, chỉ thiếu phần
số liệu cho báo cáo.

| Notebook | Việc | Đọc từ | Chạy được sau |
|---|---|---|---|
| `05c_thuc_nghiem_mau_so_chuan_hoa` | Quét mẫu số chuẩn hoá mục tiêu | `05_selected` | `05_select_features` |
| `05d_thuc_nghiem_rao_chan_vat_ly` | Quét hệ số `safe_IQR`, đối chiếu cờ ngoại lai | dữ liệu thô | `01_reindex_mask_outlier` |
| `05e_kiem_chung_con_so_bao_cao` | Đo lại các con số đưa vào báo cáo | `05_selected` | `05_select_features` |
| `11_hop_le_hoa_tham_so_hardcode` | Hợp lệ hoá tham số viết cứng | `03_2_features_spatial` | `03_2_features_spatial` |
| `05b_thuc_nghiem_tham_so_hardcode` | Quét 4 tham số cố định, mỗi mức huấn luyện lại | `05_selected`, `06_train` | `06_1/06_2/06_3` |
| `09_kiem_chung_tre_pha` | Đo độ trễ pha theo trạm và ngày | `07_final_test` | `07_final_test` |
| `10_compare_optuna_current` | Cổng kiểm chéo việc chọn mô hình | `07_final_test`, `08_baseline_prophet_test` | `06_0b_baseline_prophet` |

Bốn notebook đầu chạy được ngay sau bước chọn đặc trưng. Ba notebook cuối phải chờ train
xong vì đọc `06_train` và `07_final_test`.

`05b` nặng nhất: huấn luyện lại **18 lần** (4 tham số × nhiều mức), mỗi lần khoảng 38 giây.
Để cuối cùng. Muốn thử nhanh đường chạy thì giảm số mức trong ô cấu hình đầu notebook.

---

### Chạy

```bash
# Toan bo
python -u srcs/05_machine_learning/forcasting_pipeline/run.py --stage all

# Tung giai doan - NEN DUNG CACH NAY de he dieu hanh thu hoi RAM sau moi buoc
python -u srcs/05_machine_learning/forcasting_pipeline/run.py --stage s00
python -u srcs/05_machine_learning/forcasting_pipeline/run.py --stage s01
...

# Mot cau hinh cu the cua s08
python -u srcs/05_machine_learning/forcasting_pipeline/run.py --stage s08 --loss mae --horizon 1
```

`s10` tính SHAP trên toàn bộ 475.599 dòng nên chạy rất lâu. Nên chạy nền:

```bash
nohup python -u srcs/05_machine_learning/forcasting_pipeline/run.py --stage s10 > s10.log 2>&1 &
```

---

## 3. Nơi ghi kết quả (hai gốc tách rời)

`config/05_machine_learning/pipeline/paths.yaml` khai **hai** gốc, không được gộp:

```yaml
root:     data/model/v4_tai_lap    # NOI GHI cua lan chay hien tai
root_goc: data/model/v4            # KET QUA DA CHOT - CHI DOC, khong ghi de
```

- Mọi lệnh ghi đi qua `paths.stage()` → rơi vào `root`.
- `paths.stage_goc()` trỏ vào `root_goc`, **chỉ dùng để đọc** khi đối chiếu.


Đầu vào cũng tách riêng:

```yaml
mlmart_raw:  data/mlmart_base/v4_tai_lap/v4_preprocessing.parquet   # doc, s00
mlmart_base: data/mlmart_base/v4_tai_lap/v4_final_cleaned.parquet   # s00 ghi, s01+ doc
```

`s00` có chốt chặn: nếu tệp đích đã tồn tại thì dừng với `FileExistsError` chứ không ghi đè.

---

## 4. Siêu tham số và Optuna

Pipeline đọc siêu tham số từ `config/05_machine_learning/pipeline/best_params.json`. Đây là
**bộ đã chốt**, trích từ notebook `06_1/06_2/06_3`, là nền của mọi con số trong báo cáo.
Mỗi lần chạy `s08` in rõ nguồn tham số để không phải đoán.

Optuna **không nằm trong luồng chuẩn**. Chạy riêng khi cần:

```bash
# Chay thu 1 trial de kiem duong chay con thong
python -u srcs/05_machine_learning/forcasting_pipeline/actions/tune_optuna.py \
    --loss mae --horizon 1 --trials 1

# Tim that
python -u srcs/05_machine_learning/forcasting_pipeline/actions/tune_optuna.py \
    --loss mae --horizon 1 --trials 20
```

Kết quả ghi ra `best_params_optuna_thu.json` trong nhánh riêng, **không đụng**
`best_params.json` đã chốt. Muốn dùng thật thì xem kỹ rồi chép tay sang.

> Đổi siêu tham số là đổi mô hình, nên mọi số trong báo cáo phải sinh lại từ đầu. Muốn giữ
> đúng kết quả đang có thì **đừng chạy Optuna**.

---

## 5. Hành động ngoài luồng chuẩn

Không nằm trong `--stage all`, chạy riêng khi cần:

```bash
# Kiem chung viec chon mo hinh vo dich, khong train lai
python -u srcs/05_machine_learning/forcasting_pipeline/actions/validate_model_selection.py

# Dung mo hinh doi chung Prophet
python -u srcs/05_machine_learning/forcasting_pipeline/actions/baseline_prophet.py

# Xuat CSV cho Tableau
python -u srcs/05_machine_learning/forcasting_pipeline/actions/xuat_csv_tableau.py
```

---

## 6. Công cụ kiểm tra chất lượng

```bash
# Tap test co duoc giu kin den s09 khong
python -u srcs/05_machine_learning/forcasting_pipeline/checks/audit_test_sealed.py

# Chay lai nhieu lan co ra cung mot model khong
python -u srcs/05_machine_learning/forcasting_pipeline/checks/do_tinh_tai_lap_s08.py --so-lan 3
```

Toàn bộ `checks/` **chỉ đọc**, không ghi tệp kết quả nào.

---

## 7. Cấu hình

Mọi tham số nằm ở `config/05_machine_learning/pipeline/`, không có giá trị nào viết cứng
trong mã:

| Tệp | Nội dung |
|---|---|
| `runtime.yaml` | Số luồng, thiết bị tính, tính tất định, kiểu dữ liệu |
| `paths.yaml` | Đường dẫn vào/ra, hai gốc `root` và `root_goc` |
| `features.yaml` | Ngưỡng vật lý, phân vị, danh sách cấm, đặc trưng tất định |
| `train.yaml` | Ba hàm mất mát, trọng số mẫu, dừng sớm |
| `data.yaml` | Tần suất lưới, quy tắc tách tập, trạm loại trừ |
| `best_params.json` | Siêu tham số đã chốt theo từng (hàm mất mát, tầm) |


```yaml
gpu:
  use_gpu: false          # runtime.yaml
lightgbm:
  deterministic: true
```

LightGBM chỉ hỗ trợ `deterministic` trên CPU. Bật đồng thời `use_gpu` và `deterministic`
sẽ khiến chương trình dừng ngay kèm thông báo, thay vì âm thầm bỏ qua và cho kết quả
khác nhau giữa các lần chạy.

---

## 8. Cấu trúc thư mục

```
forcasting_pipeline/
  run.py                Diem chay duy nhat
  core/                 Cau hinh, duong dan, doc/ghi, chi so, LightGBM, do tre pha
  stages/               s00 -> s11, moi giai doan tach thanh cac buoc con
  actions/              Optuna, kiem chung chon mo hinh, Prophet, xuat CSV
  checks/               Bon cong cu kiem chung o Muc 6
  00_..._v3.py          16 script cua ban truoc refactor (08/2026), giu lam moc lich su
```

Mỗi tệp trong `core/`, `stages/`, `actions/`, `checks/` giữ dưới 200 dòng và có docstring
nêu rõ nguồn gốc từ ô mã nào của notebook, kèm lý do cho những chỗ dễ sửa nhầm.

---

## 9. Xử lý sự cố

**`Khong tim thay CSV raw ...`**: `s01` cần tệp gốc để biết dòng nào là số đo thật. Kiểm
khoá `raw_solar` trong `paths.yaml`.

**`Khong tim thay fold nao trong ...`**: chạy `s02` đến `s07` trước khi chạy `s08`.

**`Ma tran test thieu N dac trung`**: danh sách đặc trưng trong `model_config.json` không
khớp dữ liệu hiện có. Chạy lại từ `s07`.

**`... da ton tai. Stage nay KHONG duoc ghi de`**: `s00` từ chối ghi đè. Đổi
`paths.mlmart_base` sang đường dẫn mới, hoặc xoá tay tệp cũ nếu thật sự muốn dựng lại.
