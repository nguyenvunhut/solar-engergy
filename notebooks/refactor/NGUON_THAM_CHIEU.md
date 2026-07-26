# Nguồn tham chiếu — Code lấy từ đâu?

**Dự án:** Tốt nghiệp - Energy Forecasting - Nhóm thực hiện: The Outliers
**Mục đích:** Truy vết chính xác từng dòng code trong `notebooks/refactor/` đến từ file nào của team.

---

## 1. Các file gốc của team nằm ở đâu

Tất cả nằm trong **`notebooks/split_and_feature/`** (không bị xoá, không bị sửa):

| File | Dung lượng | Nội dung |
|---|---|---|
| `2026_07_24_Feature_Engineering_Time.ipynb` | 227 KB, 26 cell | Split + FE thời gian + QA/QC + Trực quan hoá Plotly |
| `2026_07_25_Feature_Engineering_Aggregate.ipynb` | 9,5 KB, 17 cell | FE domain + QA/QC + Phân phối + Tương quan |
| `fe_temporal.py` | 80 dòng | 2 hàm FE thời gian |
| `fe_domain.py` | 48 dòng | 1 hàm FE domain |
| `01_slip_time_series.ipynb` | 26 KB, 2 cell | Script split đầy đủ *(1 cell code 19.037 ký tự)* |
| `02_feature_engineering.ipynb` | 34 KB, 2 cell | *(1 cell code 24.001 ký tự — chưa dùng)* |

### Lịch sử: 2 notebook `202x` trước đây nằm ở đâu?

Ban đầu chúng nằm trong **`srcs/05_machine_learning/01_preprocessing/`**, sau đó được chuyển sang
`notebooks/split_and_feature/` (nhánh `feature/ml-forecasting-v3`, ngày 2026-07-26).

Lịch sử commit trong git:

| Commit | Nội dung |
|---|---|
| `8c75df2` | `feat(ml): [SCRUM-74] add time-based feature engineering and lag rolling features` |
| `905db1d` | `feat(ml): [SCRUM-74] add QA/QC checks and insights to FE notebook` |
| `0812f9c` | `style(ml): [SCRUM-74] upgrade visualizations to Plotly for modern interactive charts` |
| `f70a017` | `style(ml): [SCRUM-74] change Plotly theme to light mode and soft colors` |
| `dff9ade` | `feat(ml): [SCRUM-74] add gap ratio and detailed handling proposals in notebook` |
| `de7c3ce` | `refactor(ml): [SCRUM-74] inherit TimeSeriesSplit boundaries for FE step` |
| `bf8cf84` | `feat(ml): [SCRUM-89] add domain aggregate features module and notebook` |
| `c6b0fda` | `refactor(ml): [SCRUM-89] remove target leakage feature inverter_loading_ratio_proxy` |

→ Notebook Time thuộc **SCRUM-74**, notebook Aggregate thuộc **SCRUM-89**.

---

## 2. Bảng truy vết: mỗi notebook refactor lấy từ đâu

### `01_reindex_mask_outlier.ipynb`

| Phần | Nguồn |
|---|---|
| Toàn bộ | **Team CHƯA CÓ** — map từ `srcs/05_machine_learning/Forcasting_v3/01_build_continuous_grid.py` |
| Hàm `classify_outlier_group` | `srcs/05_machine_learning/Forcasting_v3/forecasting_common.py` |

**Vì sao phải lấy từ `srcs`:** team đã **phát hiện** lỗi này nhưng chưa sửa. Xem
`2026_07_24_..._Time.ipynb` **cell 15 + 16** (mục *"5.3. Kiểm tra tính liên tục của thời gian —
CRITICAL INSIGHT"*), output team chạy ra:

```
[CRITICAL ERROR] Phát hiện 561 điểm đứt gãy (gap) thời gian
trên tổng số 2268266 dòng (chiếm 0.0247%).
```

Team dừng ở chẩn đoán. Notebook 01 là bước vá lỗ hổng đó.

### `02_split_time_series.ipynb`

| Phần | Nguồn chính xác |
|---|---|
| Toàn bộ logic split | `01_slip_time_series.ipynb` — **cell 1** (cell code 19.037 ký tự) |
| Hàm `filter_window()` | giữ nguyên từ file trên |
| Hàm `summarize_part()` | giữ nguyên từ file trên |
| Công thức `test_size`, `max_train_size` | giữ nguyên từ hàm `build_sklearn_time_series_folds()` |
| 8 chốt kiểm tra `raise` | giữ nguyên từ `validate_config()` + `require_columns()` |

> ⚠️ **Một điểm KHÔNG lấy theo team:** `STRATEGY = "expanding"` (team để `sliding`).
> Lý do: **ticket SCRUM-74 yêu cầu expanding**, và `config/05_machine_learning/forecasting_v3_final_cleaned.yaml`
> cũng để `strategy: expanding`. Hai notebook của team đang lệch so với ticket — cần báo lại team.
> Chi tiết kỹ thuật và số liệu chứng minh ở `README.md` mục 6.1.

### `03_feature_time.ipynb`

| Phần | Nguồn chính xác |
|---|---|
| `build_time_features()` | `fe_temporal.py` **dòng 4–38** |
| `build_lag_rolling_features()` | `fe_temporal.py` **dòng 40–80** |
| `apply_feature_engineering()` + cắt context + `dropna` | `2026_07_24_..._Time.ipynb` **cell 7** |
| QA kiểm tra NaN + `assert` | `2026_07_24_..._Time.ipynb` **cell 12** |
| QA point-in-time correctness | `2026_07_24_..._Time.ipynb` **cell 14** |
| Kiểm tra Time Gaps | `2026_07_24_..._Time.ipynb` **cell 15 + 16** |
| Tổng kết Insight QA/QC | `2026_07_24_..._Time.ipynb` **cell 17** |
| Trực quan hoá 12.1 Lag & Rolling | `2026_07_24_..._Time.ipynb` **cell 20 + 21** (Plotly `graph_objects`) |
| Trực quan hoá 12.2 Cyclical | `2026_07_24_..._Time.ipynb` **cell 22 + 23** (Plotly `make_subplots`) |
| Trực quan hoá 12.3 Gaps Severity | `2026_07_24_..._Time.ipynb` **cell 24 + 25** |
| Nối Historical Context 96 bước | `2026_07_24_..._Time.ipynb` **cell 5** (phần `context_steps = 96`) |

### `04_feature_spatial.ipynb`

| Phần | Nguồn chính xác |
|---|---|
| `capacity_per_panel` | `fe_domain.py` — khối comment **`# 1. Capacity per Panel`** |
| Cột `{col}_missing` indicator | **Team CHƯA CÓ** — ý tưởng từ `srcs/05/04_feature_engineering_spatial.py` |

### `05_feature_aggregate.ipynb`

| Phần | Nguồn chính xác |
|---|---|
| `temp_x_radiation` | `fe_domain.py` — khối **`# 2. Temperature x Radiation Interaction`** |
| `thermal_loss_factor` | `fe_domain.py` — khối **`# 3. Thermal Loss Factor`** |
| `diffuse_fraction` | `fe_domain.py` — khối **`# 5. Diffuse Fraction`** |
| Cấu trúc mục 1→9 | `2026_07_25_..._Aggregate.ipynb` — **toàn bộ 17 cell** |
| QA/QC missing + Infinity | `2026_07_25_..._Aggregate.ipynb` **cell 6 + 7** |
| Nhận xét về QA | `2026_07_25_..._Aggregate.ipynb` **cell 8** |
| Histogram + Boxplot (KDE) | `2026_07_25_..._Aggregate.ipynb` **cell 9 + 10** |
| Tương quan & Đa cộng tuyến | `2026_07_25_..._Aggregate.ipynb` **cell 11 + 12** |
| Nhận xét & Đề xuất | `2026_07_25_..._Aggregate.ipynb` **cell 13** |
| Scatter phi tuyến (sample 10.000) | `2026_07_25_..._Aggregate.ipynb` **cell 14** |

### `06_vif_diagnostics.ipynb`

| Phần | Nguồn |
|---|---|
| Toàn bộ | **Team CHƯA CÓ** — ý tưởng từ `srcs/05/06_vif_pls_diagnostics.py`, viết lại bằng pandas/sklearn thuần |

### `07_select_features.ipynb`

| Phần | Nguồn |
|---|---|
| Toàn bộ | **Team CHƯA CÓ** — ý tưởng từ `srcs/05/07_select_features_sklearn.py`, viết lại bằng pandas/sklearn thuần |
| Danh sách cấm (deny list) | `config/05_machine_learning/forecasting_v3_final_cleaned.yaml` → `features.deny_list` |

---

## 3. Tóm tắt cho buổi trình bày

**Trong 7 notebook:**

| Loại | Notebook | Ghi chú |
|---|---|---|
| **Code team, bê nguyên** | 02, 03, 04, 05 | Đã diff xác nhận giống hệt |
| **Team chưa có, viết mới** | 01, 06, 07 | Lấy ý tưởng từ `srcs`, viết lại theo style team |

**Kết quả diff (kiểm bằng script, không phải nói suông):**

| Hàm của team | Đích | Kết quả |
|---|---|---|
| `build_time_features()` | NB03 | **Thân hàm giống hệt** |
| `build_lag_rolling_features()` | NB03 | **Thân hàm giống hệt** |
| `build_domain_aggregate_features()` | NB04 + NB05 | **Mọi dòng code đều có mặt** |

Khác biệt duy nhất: đổi tên tham số `df` → `df_in`. Không đụng logic.

**Ba bước team chưa có mà pipeline bắt buộc phải có:**

1. **Reindex lưới 15 phút** (NB01) — vá 561 điểm đứt gãy mà chính team đã gắn nhãn `CRITICAL`
2. **Chẩn đoán VIF** (NB06) — nhưng **không tự động xoá feature**, vì lag/rolling tương quan cao là *thiết kế*
3. **Danh sách cấm chống rò rỉ** (NB07) — chặn các cột tính từ chính target

---

## 4. Câu hỏi hội đồng có thể hỏi & câu trả lời

**H: Kết quả có khớp với lần team chạy không?**
Đ: Không, và đó là điều đúng. Dữ liệu đầu vào **giống hệt** (2.731.946 dòng cả hai bên), nhưng thêm
bước reindex nên **+52.492 dòng**. Con số `Train: 2272298` cũ của team tính trên dữ liệu còn 561 lỗ hổng.

**H: Sao dùng `expanding` mà không phải `sliding` như trong notebook của team?**
Đ: Theo **ticket SCRUM-74** và `config/05_machine_learning/forecasting_v3_final_cleaned.yaml`
(`strategy: expanding`). Hai notebook của team để `sliding` là lệch so với ticket. Ngoài ra `expanding`
phù hợp hơn với dữ liệu này: số site tăng dần theo thời gian (2020Q1 chỉ có **13** site, tới 2021Q1 mới
đủ **42**). Với `sliding`, fold 1 chỉ có 524.962 dòng còn fold 5 có 1.073.007 dòng — chênh gấp đôi dù
cùng số timestamp, khiến các fold không so sánh được. `expanding` cho train phình dần nên fold sau luôn
bao trọn lịch sử fold trước.

**H: Sao phải chia theo trục timestamp mà không chia theo dòng?**
Đ: Có 42 site, mỗi mốc thời gian ứng với 42 dòng. Chia theo dòng thì **cùng một thời điểm sẽ nằm ở cả
train lẫn validation** → rò rỉ. Team đã viết wrapper `build_sklearn_time_series_folds()` chính vì lý do này.

**H: Sao loại các cột outlier khỏi feature? Bỏ đi model có yếu không?**
Đ: Không yếu, mà tránh điểm số ảo. Bằng chứng từ dữ liệu: khi `exclude_from_training == True` thì
`energy_generated_kwh = 0.0` ở **100,00%** trường hợp (36.847 dòng, std = 0). Đưa vào thì model chỉ tra
bảng *"thấy cờ thì đoán 0"*. Thực tế khi dự báo tương lai thì các cột này **chưa tồn tại** — chúng chỉ
tính được sau khi đã đo sản lượng. Chúng chỉ dùng để lọc dòng, gán trọng số, và khoanh vùng tính metric.

**H: VIF cao ở lag/rolling thì sao?**
Đ: Bình thường và đúng thiết kế — `lag_1` và `rolling_mean_1h` cùng sinh từ một chuỗi target. Máy móc
áp luật "VIF > 10 thì loại" sẽ xoá sạch lag/rolling, tức vứt đi feature mạnh nhất của bài toán dự báo
chuỗi thời gian. Notebook 06 chỉ chẩn đoán và báo cáo, quyết định để ở notebook 07 bằng mutual information.
