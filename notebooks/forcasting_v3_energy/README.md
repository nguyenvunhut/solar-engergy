# Refactor Pipeline Notebooks (01 → 07)

**Dự án:** Tốt nghiệp - Energy Forecasting - Nhóm thực hiện: The Outliers
**Ngày:** 2026-07-26

---

## 0. Hướng dẫn chạy toàn bộ pipeline (thứ tự notebook)

Chạy tuần tự theo đúng thứ tự dưới đây, không bỏ bước, không đảo thứ tự:

```
notebooks/preprocess/00_realign_mlmart_weather_hotfix.ipynb
    ↳ đọc + ghi đè data/mlmart_base/v3_preprocessing.parquet
    ↳ sửa causal weather join (weather_timestamp = floor(timestamp, 1h))
    ↳ idempotent - chạy lại nhiều lần không đổi kết quả nếu data đã đúng

notebooks/refactor/00_hotfix_join_causal_audit.ipynb     [TÙY CHỌN - chỉ kiểm chứng]
    ↳ đọc v3_preprocessing.parquet, ghi audit ra data/model/v3/00_hotfix_audit/
    ↳ không sửa file gốc

notebooks/preprocess/00_fill_null_imputation.ipynb
    ↳ đọc v3_preprocessing.parquet (đã hotfix) → ghi data/mlmart_base/v3_final_cleaned.parquet

notebooks/preprocess/01_recheck_fill_null.ipynb           [TÙY CHỌN - chỉ kiểm chứng]
    ↳ đọc lại cả v3_preprocessing.parquet và v3_final_cleaned.parquet để đối chiếu

notebooks/refactor/01_reindex_mask_outlier.ipynb  →  02  →  03_1  →  03_2  →  03_3
    →  04_vif_diagnostics  →  05_select_features
    →  06_1_train_mae / 06_2_train_huber / 06_3_train_mse / 06_0b_baseline_prophet
    →  07_final_test  →  08_explainable_ai  →  09_kiem_chung_tre_pha
```

**Lưu ý quan trọng:**
- `00_realign_mlmart_weather_hotfix.ipynb` nằm ở `notebooks/preprocess/` — vì nó **xử lý thật** (ghi
  đè `v3_preprocessing.parquet`, kết quả được `00_fill_null_imputation.ipynb` dùng tiếp).
- `00_hotfix_join_causal_audit.ipynb` vẫn ở `notebooks/refactor/` — vì nó **chỉ kiểm chứng** (đọc
  `v3_preprocessing.parquet`, ghi ra file audit riêng ở `data/model/v3/00_hotfix_audit/`, không sửa
  gì, không có notebook nào khác đọc lại file audit đó). Quy tắc: chỉ di chuyển notebook nào thật sự
  xử lý/ghi đè dữ liệu được dùng tiếp; notebook thuần kiểm chứng thì để nguyên chỗ cũ.
- `06_1/06_2/06_3` là 3 hàm mất mát (MAE/Huber/MSE) train độc lập, so nhau trên tập Validation trong
  `07_final_test.ipynb` để chọn model vô địch cho từng horizon (h1/h4).
- Toàn bộ chuỗi notebook trên đã được convert 1-1 (copy chính xác, không viết lại) sang
  `srcs/05_machine_learning/refactor_pipeline/*.py`, chạy được qua
  `python srcs/05_machine_learning/refactor_pipeline/run_pipeline.py --stage all` — xem file đó nếu
  cần chạy bằng script thay vì mở từng notebook.

---

## 1. Mục tiêu

Thư mục `notebooks/` cũ đang rối: có notebook chỉ **2 cell** trong đó 1 cell code dài **19.037 ký tự**
(cả script nhét vào một ô), 4 cụm `EDA/` `preprocess/` `forecasting/` `split_and_feature/` không có
thứ tự chạy, tên file 3 kiểu lẫn lộn.

Bộ notebook này sắp xếp lại thành pipeline `01 → 07`, với nguyên tắc:

> **Logic là của team. Thứ tự chạy bám theo `srcs/05_machine_learning/Forcasting_v3/`.**

Bản gốc trong `notebooks/split_and_feature/` **giữ nguyên, không xoá, không sửa**.

---

## 2. Chuỗi dữ liệu

```
01: v3_final_cleaned.parquet + Solar_Energy_Generation.csv  →  v3_continuous_grid.parquet
02: v3_continuous_grid.parquet                              →  data/model/v3/{train,val,test}/v3_*.parquet
03: data/model/v3/{train,val,test}                          →  train_fe / val_fe / test_fe.parquet
04: train_fe / val_fe / test_fe                             →  train_spatial / val_spatial / test_spatial
05: train_spatial / val_spatial / test_spatial              →  train_agg / val_agg / test_agg
06: train_agg                                               →  feature_diagnostics.csv
07: train_agg + feature_diagnostics.csv                     →  selected_features.json + feature_scores.csv
```

Chạy tuần tự từ 01 đến 07. Mỗi notebook đọc output của notebook liền trước.

---

## 3. Nguồn gốc code từng notebook

| NB | Nguồn logic | Mức độ bê nguyên |
|---|---|---|
| 01 | **Không có code team** — map từ `srcs/05/01_build_continuous_grid.py` | Viết mới theo style team |
| 02 | `split_and_feature/01_slip_time_series.ipynb` | Bê nguyên, chỉ tách cell + bỏ khung CLI |
| 03 | `split_and_feature/fe_temporal.py` | **Giống hệt** thân hàm |
| 04 | `split_and_feature/fe_domain.py` (khối `# 1`) | **Giống hệt** |
| 05 | `split_and_feature/fe_domain.py` (khối `# 2 # 3 # 5`) | **Giống hệt** |
| 06 | code team `srcs/05/06_vif_pls_diagnostics.py` | Viết 
theo style team |
| 07 | **Không có code team** — ý tưởng từ `srcs/05/07_select_features_sklearn.py` | Viết mới theo style team |

### 3.1. Kết quả diff code FE (đã kiểm bằng script)

| Hàm của team | Notebook đích | Kết quả diff |
|---|---|---|
| `build_time_features()` | 03 | Thân hàm **giống hệt** |
| `build_lag_rolling_features()` | 03 | Thân hàm **giống hệt** |
| `build_domain_aggregate_features()` | 04 + 05 | **Mọi dòng code đều có mặt** |

Khác biệt duy nhất: đổi tên tham số `df` → `df_in` (và `df_out = df_in.copy()`).
Không đụng tới logic.

---

## 4. Phần LOGIC THÊM VÀO so với team

Đây là các bước team **chưa có**, được bổ sung để pipeline chạy đúng.

### 4.1. Notebook 01 — Reindex lưới 15 phút (MỚI HOÀN TOÀN)

**Lý do:** chính team đã phát hiện lỗi này nhưng chưa sửa. Trong
`2026_07_24_Feature_Engineering_Time.ipynb` mục *"5.3. Kiểm tra tính liên tục của thời gian (Time Gaps)
- CRITICAL INSIGHT"*, output team chạy ra:

```
[CRITICAL ERROR] Phát hiện 561 điểm đứt gãy (gap) thời gian
trên tổng số 2268266 dòng (chiếm 0.0247%).
  0 days 01:15:00    68
  1 days 03:30:00    42
  1 days 07:15:00    42
```

Team viết rõ trong markdown: *"nếu dữ liệu time-series bị mất tín hiệu (gap), các hàm trượt theo dòng
(`.shift(1)` hoặc `.rolling(window=4)`) sẽ bị vô hiệu hóa logic"* — nhưng dừng ở chẩn đoán.

**Đã thêm:** dựng lưới 15 phút liên tục cho từng site, điền target cho slot mới chèn bằng cascade nhân quả.

**Kết quả thực tế:**

| | Số dòng |
|---|---|
| `v3_final_cleaned.parquet` (đầu vào) | 2.731.946 |
| `v3_continuous_grid.parquet` (sau reindex) | 2.784.438 |
| **Chèn thêm** | **52.492** (+1,92%) |

561 *điểm* đứt gãy ⟶ 52.492 *slot* 15 phút bị thiếu (trung bình 93,6 slot ≈ 23,4 giờ mỗi gap,
khớp với bảng team in ra).

Phân loại nguồn gốc target sau khi điền:

| `energy_source` | Dòng |
|---|---|
| `machine_failure_zero` (gap ≥ 24h) | 42.055 |
| `night_zero` | 6.287 |
| `causal_day_persistence` | 2.668 |
| `fallback_zero` | 984 |
| `causal_profile_median` | 283 |
| `causal_week_persistence` | 215 |
| **Tổng** | **52.492** ✓ khớp đúng số dòng chèn |

**Quy tắc nhân quả bắt buộc:** thời tiết chỉ `ffill()`, **không bao giờ `bfill()`** — không kéo dữ liệu
tương lai về quá khứ. Metadata tĩnh thiếu thì **giữ NaN**, không bịa.

### 4.2. Notebook 01 — Mask outlier (MỚI)

Sinh cột `outlier_group` từ `gmm_if_outlier_flag` + `gmm_if_outlier_reason`.

| `outlier_group` | Dòng (toàn bộ) |
|---|---|
| `normal` | 2.751.229 |
| `physical_over_capacity` | 26.318 |
| `gmm_if_consensus` | 5.389 |
| `multiple_rules` | 791 |
| `other_physical_rule` | 711 |

### 4.3. Notebook 03 — Nối Historical Context (MỚI)

**Lý do:** notebook 02 cắt train/val/test theo mốc thời gian mà không kèm context. Tính `lag_24` /
`rolling_mean_3h` thẳng trên val/test sẽ ra NaN → hai câu `assert` chống rò rỉ của team sẽ nổ.

**Đã thêm:** nối 96 dòng cuối của tập trước vào đầu tập sau theo từng site
(`groupby("site_id").tail(96)`), tính feature, rồi cắt bỏ context. Đây đúng là cách team đã làm trong
`2026_07_24_Time.ipynb` cell 7.

> **Lưu ý:** `CONTEXT_STEPS = 96` mà `lag_24 = shift(96)` — vừa khít, không có biên dự phòng.
> Chạy thực tế đã pass, nhờ notebook 01 đã reindex liên tục.

### 4.4. Notebook 06 — Chẩn đoán VIF (MỚI HOÀN TOÀN)

VIF, ma trận tương quan, phát hiện cột hằng số.

> **Quan trọng:** trong time-series, `lag_1` và `rolling_mean_1h` **tương quan cao là đương nhiên** vì
> cùng sinh từ một chuỗi target. Đó là **thiết kế**, không phải lỗi. Notebook 06 **chỉ chẩn đoán và
> báo cáo, không tự động xoá feature nào**. Nếu máy móc áp luật "VIF > 10 thì loại" sẽ xoá sạch lag/rolling
> — tức vứt đi những feature mạnh nhất của bài toán.

### 4.5. Notebook 07 — Chọn feature + Danh sách cấm (MỚI HOÀN TOÀN)

Chấm điểm bằng `mutual_info_regression`, và **chặn cứng** các cột gây rò rỉ nhãn.

**Bằng chứng rò rỉ, lấy từ chính dữ liệu train (1.787.862 dòng):**

| Bằng chứng | Số liệu |
|---|---|
| `exclude_from_training == True` → `energy_generated_kwh` | `0.0` ở **100,00%** (36.847 dòng), std = 0 |
| `outlier_group == physical_over_capacity` mean target | **19,43 kWh** |
| `outlier_group == normal` mean target | **2,75 kWh** |

**Vì sao phải cấm:** các cột này được tính **SAU KHI** đã đo được sản lượng. Khi dự báo tương lai thì
chúng chưa tồn tại. Đưa vào model thì model không học gì — nó chỉ tra bảng *"thấy cờ thì đoán 0"*,
cho điểm R²/RMSE đẹp giả trên train/val nhưng vô dụng khi dự báo thật.

**Vai trò đúng của 5 cột outlier/provenance:** (1) lọc dòng khỏi tập train, (2) gán trọng số mẫu,
(3) khoanh vùng tính metric.

Danh sách cấm: `energy_generated_kwh`, `gmm_if_outlier_flag`, `gmm_if_outlier_reason`, `outlier_group`,
`exclude_from_training`, `exclude_reason`, `training_quality_reason`, `energy_source`,
`timestamp_was_inserted`, `source_gap_id`, `after_source_gap_steps_remaining`, `is_daylight`,
`weather_is_day`, `sunshine_duration`, `weather_is_observed`, các cột `*_id`, các cột `v3_*`,
`timestamp`, `time_diff`, `full_date`.

---

## 5. So sánh kết quả với lần chạy của team

**Dữ liệu đầu vào giống hệt nhau:**

```
Team đọc v2_preprocessing.parquet  → output in ra "Tổng số dòng: 2731946"
Ta   đọc v3_final_cleaned.parquet  →                       2.731.946 dòng
```

**Kết quả sẽ KHÁC**, và đó là điều đúng, do 2 khác biệt có chủ đích:

1. **+52.492 dòng** từ bước reindex (team chưa có). Trong đó 42.055 dòng (80%) rơi vào gap ≥ 24h nên
   bị gắn `exclude_from_training = True`, không vào tập train.
2. Bước split có thay đổi (xem mục 6).

Con số `Train: 2272298` của team **không tái lập được**, vì nó tính trên dữ liệu còn 561 lỗ hổng mà
chính team đánh dấu `CRITICAL`.

---

## 6. Các điểm ĐÃ LỆCH so với code team và cách xử lý

Kết quả diff notebook 02 với `01_slip_time_series.ipynb`:

| # | Lệch | Xử lý |
|---|---|---|
| 1 | Chiến lược split — xem mục 6.1 bên dưới | **Chốt dùng `"expanding"`** |
| 2 | Mất `validate_config()` và `require_columns()` | **Đã bổ sung lại** |
| 3 | `summarize_part()` thiếu 5 cột đếm cờ | **Đã bổ sung lại** |

### 6.1. Quyết định về chiến lược split: dùng `expanding`

Trong repo đang có **mâu thuẫn** về chiến lược split:

| Nguồn | Chiến lược |
|---|---|
| Ticket giao cho team (SCRUM-74) | **`expanding`** |
| `2026_07_24_Feature_Engineering_Time.ipynb` | `sliding` — **hardcode**, không có nhánh expanding |
| `01_slip_time_series.ipynb` | `sliding` (mặc định), có hỗ trợ cả hai |
| `config/05_machine_learning/forecasting_v3_final_cleaned.yaml` | **`expanding`** |
| **Notebook 02 (chốt)** | **`expanding`** |

**Chốt theo ticket: `STRATEGY = "expanding"`.** Hai notebook của team đang để `sliding`, tức **lệch
so với ticket** — đây là điểm cần báo lại cho team.

Khác biệt kỹ thuật:

| | `sliding` | `expanding` |
|---|---|---|
| `test_size` | `len // (n_splits + sliding_train_blocks)` = `len // 8` | `len // (n_splits + 1)` = `len // 6` |
| `max_train_size` | `test_size × 3` (cửa sổ train cố định) | `None` (train phình dần) |

**Lý do kỹ thuật ủng hộ `expanding`** — số site không đồng đều theo thời gian:

| Quý | Số site hoạt động |
|---|---|
| 2020Q1 | **13** |
| 2020Q2 | 30 |
| 2020Q3 | 36 |
| 2020Q4 | 39 |
| 2021Q1 → 2022Q2 | **42** (đủ) |

Với `sliding`, fold 1 train rơi vào 2020-01 → 2020-09 khi chỉ có 13–36 site: cùng 25.824 timestamp
nhưng chỉ **524.962 dòng**, trong khi fold 5 có **1.073.007 dòng** — gấp đôi. Các fold không so sánh
được với nhau.

Với `expanding`, train phình dần từ đầu nên fold sau luôn bao trọn lịch sử của fold trước, giảm hẳn
độ lệch này.

Các chốt kiểm tra đã khôi phục ở lệch #2:
```python
require_columns(df, [timestamp_col, site_col, target_col])
if STRATEGY not in ("sliding", "expanding"):     raise ValueError(...)
if not 0 < TEST_RATIO < 1:                       raise ValueError(...)
if N_SPLITS < 2:                                 raise ValueError(...)
if SLIDING_TRAIN_BLOCKS < 1:                     raise ValueError(...)
if len(development_ts) < N_SPLITS + 2:           raise ValueError(...)
if len(timestamp_axis) <= N_SPLITS * test_size:  raise ValueError(...)
```

### Phần cố ý bỏ khi chuyển từ script sang notebook

Không phải mất logic, chỉ là đổi cách truy cập biến:

- `class TimeSeriesSplitConfig` (dataclass) → biến thường ở cell đầu
- `parse_args()`, `main()`, `argparse` → notebook không cần CLI
- `PROJECT_ROOT = Path.cwd().resolve().parents[3]` → path tương đối `../../data/...`
- `write_readme()` → thay bằng file README này
- `config.input_path` → `INPUT_PATH` (và tương tự cho mọi thuộc tính config)

---

## 7. Quy ước viết notebook

Rút từ `2026_07_25_Feature_Engineering_Aggregate.ipynb` — style chuẩn của team:

- Mỗi bước = 1 markdown `## N. Tiêu đề` + 1 code cell. Cell chia nhỏ, mỗi cell một việc.
- **Không tạo file `.py`** — toàn bộ logic viết inline trong cell.
- **Mỗi code cell phải có output** (`print` / `display` ở cuối).
- Comment và `print` bằng **tiếng Việt có dấu**.
- **Không** emoji, **không** ký tự vẽ khung `├─ └─`, **không** định dạng `{x:,}`.
- Banner báo cáo: `print("\n--- TIÊU ĐỀ IN HOA ---")`. Cảnh báo: `print("[CRITICAL ERROR] ...")`.
- Đường dẫn tương đối `../../data/...`.
- Sau QA/biểu đồ có markdown `### Nhận xét:` viết bằng lời.
- Section cuối luôn là `## N. Export Processed Dataset`.

---

## 8. Việc cần làm khi chạy lại

0. **Thư mục `data/model/v3/time_series_folds/` đã được xoá sạch** — trước đó nó chứa lẫn lộn output của
   2 lần chạy khác chiến lược, và `fold_3_train.parquet` bị hỏng (*"Parquet magic bytes not found in
   footer"*) do lần chạy bị ngắt giữa chừng. Chạy lại notebook 02 sẽ sinh lại đủ 10 file.
1. Chạy tuần tự **01 → 07**. Notebook 02 vừa đổi sang `expanding` + thêm các chốt kiểm tra nên
   **phải chạy lại từ 02**, không dùng lại `train_fe.parquet` cũ.
2. Kiểm notebook 03 mục *"Kiểm tra tính liên tục của thời gian"* — phải in **0 điểm đứt gãy**
   (team đo được 561). Đây là bằng chứng định lượng bước 01 có tác dụng.
3. Kiểm hai câu `assert` chống rò rỉ NaN ở notebook 03 phải pass.
4. Kiểm `selected_features.json` **không được chứa** 5 cột outlier/provenance.
