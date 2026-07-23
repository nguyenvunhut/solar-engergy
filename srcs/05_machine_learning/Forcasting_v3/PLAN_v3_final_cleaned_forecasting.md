# Kế hoạch Forecasting với `v3_final_cleaned`

> Trạng thái: **chờ duyệt kế hoạch**. File này chỉ mô tả luồng; chưa thay đổi code, không truy cập Supabase/cloud và không thao tác Git.

## 1. Mục tiêu chốt, phạm vi và các rule không được mâu thuẫn

Mục tiêu là tạo một pipeline forecasting **chỉ thuộc Machine Learning**, tái lập
được từ `v3_final_cleaned.parquet` và tạo được chuỗi 15 phút liên tục cho từng
site để dùng lag/rolling. Pipeline không sửa ETL, database, Supabase, Docker hay
file parquet nguồn.

### Input, output và hai nhánh model

- Input duy nhất, read-only: `data/mlmart_base/v3_final_cleaned.parquet`.
- Target: `energy_generated_kwh`; horizon, seed và mốc split nằm trong YAML.
- Khóa chuỗi: `site_id`, `timestamp`. Không dùng nhánh `sitekey` trong code
  forecasting vì schema thật của `v3_final_cleaned` dùng `site_id`.
- Granularity short-term: 15 phút, một chuỗi cho mỗi `site_id`.
- Horizon chốt cho short-term v1: **direct `horizon_steps=[1, 4]`**.
  `h=1` tương ứng 15 phút là use case chính; `h=4` tương ứng 1 giờ là horizon
  phụ để chứng minh model vượt persistence rõ hơn. Mỗi horizon tạo target/model
  hoặc run config riêng và áp dụng luật cứng `min_lag_steps >= horizon_steps`.
- **Short-term**: LightGBM dự báo 15 phút/horizon ngắn bằng lag, rolling và
  covariate biết được tại thời điểm forecast.
- **Long-term**: Prophet hoặc seasonal-naive ở granularity giờ/ngày; là nhánh
  khác, không dùng lag/rolling của short-term.

### Rule chốt cho continuous timeline

1. Timestamp local hiện tại là source of truth; DST đã xử lý upstream, không
   đổi UTC và không dùng BI hourly bucket để làm timestamp ML.
2. Reindex mỗi site thành grid 15 phút từ timestamp nhỏ nhất đến lớn nhất của
   chính site. Đây là **ML-derived data**; input gốc không bị ghi đè.
3. Tất cả gap phải có energy để lag/rolling liên tục:
   - ban đêm/daylight xác định ở độ phân giải 15 phút bằng solar-elevation từ
     `latitude`, `longitude`, `timestamp`; với row `energy_source=measured`,
     nếu energy dương vượt ngưỡng sensor-noise thì force `is_daylight=true` để
     không loại nhầm ramp hoàng hôn/bình minh thật; `weather_is_day` chỉ là
     hourly coarse cross-check/fallback, clock window `18:30-05:30` là fallback
     cuối cùng và phải log số dòng dùng fallback này;
   - gap `<24h`: daylight=false đặt 0; daylight=true dùng cascade causal `t-96` → `t-672`
     → median quá khứ theo site × quarter-hour × season/month;
   - gap `≥24h`, ví dụ 4 ngày: đặt energy bằng 0 theo business rule
     *máy/ngõ thu thập ngưng hoạt động*.
4. Cấm linear interpolation, cubic interpolation và regression fill. Không
   method nào được đọc energy ở phía sau timestamp đang lấp. Profile median chỉ
   update từ row observed trong quá khứ, không chain từ synthetic target.
5. Mọi row không phải `energy_source=measured` có `sample_weight=0` trong
   model headline: được dùng làm history cho lag/rolling/persistence nhưng
   không là target train headline và không xuất hiện trong metric headline.
6. Với row synthetic của gap `≥24h`, **không sửa nghĩa gốc của
   `gmm_if_outlier_flag`**. Gắn `exclude_from_training=true`,
   `exclude_reason=MACHINE_FAILURE_DATA_GAP` và lưu provenance trong
   `training_quality_reason`. Đây là rule quality của ML-derived output,
   không phải rerun GMM-IF và không sửa nhãn của input.
7. Row observed ngay sau source gap bị đánh dấu `AFTER_SOURCE_GAP` trong
   `max_lag_steps = max(lag_steps)` row tiếp theo. Metric bắt buộc báo song
   song có/không nhóm này vì lag/rolling có thể đọc history synthetic.
8. Split theo thời gian. Cột/transformer nào cần fit (encoder, scaler, PLS,
   selector, model) chỉ fit trên train-fold. Continuous fill được quét tuần tự
   từ quá khứ sang hiện tại nên không sử dụng future của validation/test.

### Thứ tự chạy chốt

```text
v3_final_cleaned.parquet (read-only)
  -> read-only audit
  -> canonical continuous 15-minute grid (causal left-to-right)
  -> chronological Train | Validation | sealed Test split
  -> expanding-window folds trên Train + Validation
  -> feature engineering / selection fit theo từng train-fold
  -> baseline + Optuna LightGBM
  -> refit Train + Validation -> evaluate Test một lần -> SHAP
```

### Data contract: input/output để không làm bẩn folder

| Loại | Đường dẫn cố định | Quyền của pipeline | Nội dung |
|---|---|---|---|
| Input nguồn | `data/mlmart_base/v3_final_cleaned.parquet` | **Read-only, không ghi đè** | Dataset đã fill-null, nguồn duy nhất của forecasting pipeline. |
| Config | `config/05_machine_learning/forecasting_v3_final_cleaned.yaml` | File sẽ được tạo trước khi chạy; read-only trong runtime | Split dates/ratios, horizon, seed, folds, features, Optuna, artifact paths. |
| Audit input | `data/model/v3_final_cleaned/00_audit/<run_id>/` | Chỉ ghi theo `run_id` | Read-only audit report từ parquet nguồn; không sinh continuous data. |
| Continuous grid | `data/model/v3_final_cleaned/01_continuous/<run_id>/` | Chỉ ghi theo `run_id` | Canonical 15 phút, imputation causal, gap audit, không đặt fold parquet ở đây. |
| Split trung gian | `data/model/v3_final_cleaned/02_splits/<run_id>/` | Chỉ tạo/xóa bằng `--overwrite-artifacts` | Một `split_manifest.json` + parquet development/test/folds; không đặt trong `data/mlmart_base/`. |
| Feature cache | `data/model/v3_final_cleaned/03_features/<run_id>/` | Chỉ tạo/xóa bằng `--overwrite-artifacts` | Feature parquet theo từng fold + một `feature_manifest.json`; gitignore/DVC. |
| Diagnostics | `data/model/v3_final_cleaned/04_diagnostics/<run_id>/` | Chỉ ghi theo `run_id` | VIF, PLS diagnostics, selector reports. |
| Baseline | `data/model/v3_final_cleaned/05_baselines/<run_id>/` | Chỉ ghi theo `run_id` | Persistence/seasonal-naive/Prophet baseline predictions + metrics. |
| Tuning | `data/model/v3_final_cleaned/06_tuning/<run_id>/` | Chỉ ghi theo `run_id` | `optuna_trials.csv`, `cv_metrics.csv`, `best_params.json`. |
| Model binary | `models/v3_final_cleaned/<run_id>/` | Chỉ ghi theo `run_id` | LightGBM/Prophet, selected feature list, model config. |
| Metrics kỹ thuật | `data/model/v3_final_cleaned/07_metrics/<run_id>/` | Chỉ ghi theo `run_id` | Chỉ 3 file tổng hợp: `metrics_overall.json`, `metrics_by_site.csv`, `prediction_audit.parquet`. |
| Báo cáo trình bày | `reports/ml_training_v3_final_cleaned/<run_id>/` | Chỉ append run mới | Markdown/diễn giải; được tạo sau khi metrics đã khóa, không là nơi pipeline phụ thuộc. |
| Hình | `pictures/ml_training_v3_final_cleaned/<run_id>/` | Chỉ ghi theo `run_id` | Chia theo đúng giai đoạn: audit, split, tuning, evaluation, explainability. |
| Log | `logs/ml_training_v3_final_cleaned_<run_id>.log` | Tạo mới mỗi lần chạy | stdout/stderr của đúng một run. |

Quy tắc ghi file:

1. `run_id = YYYYMMDD_HHMMSS_<input_checksum_8>`; mọi artifact của một lần chạy nằm dưới cùng `run_id`.
2. Mặc định **không ghi đè**. Nếu artifact path đã tồn tại, runner dừng và báo lỗi.
3. Chỉ `--overwrite-artifacts` mới được phép xóa/ghi lại artifact của chính
   `run_id`; không có lệnh nào được phép ghi vào `data/mlmart_base/`.
4. Split/feature/metric parquet–CSV–JSON là derived data, đưa vào `.gitignore`/DVC. `reports/` chỉ chứa diễn giải Markdown/bảng trích xuất sau khi metrics đã khóa; hình chọn lọc mới là artifact để review/Git.
5. Output luôn bắt đầu bằng `v3_final_cleaned`; không dùng chung `data/model/v3/` của pipeline cũ.

## 2. Hợp đồng dữ liệu trước khi train

Pipeline mở đầu bằng một bước read-only audit; nếu lỗi thì dừng thay vì tự sửa dữ liệu.

Kiểm tra bắt buộc:

1. Cột khóa: `site_id`, `timestamp`, `energy_generated_kwh`.
2. Timestamp parse được, timezone/DST nhất quán; không đảo thứ tự thời gian.
3. Không có duplicate theo `(site, timestamp)`.
4. Tần suất 15 phút và các time gap được thống kê theo site; phân loại gap ngắn/dài trước khi tạo bản ML-derived.
5. Null ở target/covariate, min/max energy, số dòng ban đêm theo `weather_is_day`,
   fallback daylight, outlier flag và phân bố theo site.
6. Kiểm tra peak energy–shortwave theo giờ để bắt time shift trước khi train.
7. Kiểm tra bucket-shift BI/ML chỉ là audit gate: ML không tự shift timestamp,
   nhưng phải báo nếu peak energy và peak shortwave lệch 1 giờ theo site/mùa.
8. Tạo provenance cột `energy_source` trong artifact ML-derived bằng cách join
   với raw CSV `data/raw/Solar_Energy_Generation.csv` theo
   `(site_id, timestamp) = (SiteKey, Timestamp)`. Đây là blocker để metric
   không chấm nhãn ETL-imputed như ground truth thật.

   Enum bắt buộc:

   ```text
   measured                         # raw SolarGeneration có giá trị thật
   etl_imputed                      # raw SolarGeneration null, ETL đã fill trong v3_final_cleaned
   night_zero                       # row ML reindex, daylight=false
   causal_day_persistence           # row ML reindex, fill từ t-96 measured/history hợp lệ
   causal_week_persistence          # row ML reindex, fill từ t-672 measured/history hợp lệ
   causal_profile_median            # row ML reindex, median past-only
   fallback_zero                    # row ML reindex, không đủ history, đặt 0
   machine_failure_zero             # gap >=24h, business outage, đặt 0
   ```

   Audit hiện tại từ data thật cần được tái tạo trong code:

   ```text
   raw rows = 2,731,946
   raw SolarGeneration null = 1,536,301 (~56.2%)
   v3_final_cleaned energy null = 0
   source gap events = 561
   gap events >=24h = 286
   missing 15-minute slots before ML reindex = 52,492 (~1.89% full grid)
   ```

   Những con số này là sanity check; nếu lệch đáng kể thì fail-fast thay vì
   train.

Kết quả lưu:

- `data/model/v3_final_cleaned/00_audit/<run_id>/data_contract.json`
- `data/model/v3_final_cleaned/00_audit/<run_id>/data_quality_by_site.csv`
- `data/model/v3_final_cleaned/00_audit/<run_id>/daylight_policy_audit.csv`
- `pictures/ml_training_v3_final_cleaned/<run_id>/00_audit/`

## 3. Luồng thời gian chống leakage

```text
v3_final_cleaned.parquet
        |
        v
  audit read-only theo (site_id, timestamp)
  + canonical continuous grid/fill causal quét từ quá khứ sang hiện tại
        |
        v
  final chronological split: Train | Validation | Test (test bị niêm phong)
        |
        v
  expanding-window CV trên Train + Validation
  Fold 1: [train_1] -> [val_1]
  Fold 2: [train_1 + val_1] -> [val_2]
  Fold 3: [train_1 + val_1 + val_2] -> [val_3]
        |
        v
  chọn tham số Optuna bằng pooled validation WAPE qua các fold
        |
        v
  train lại một lần trên Train + Validation với best params
        |
        v
  đánh giá đúng một lần trên Test chưa từng được dùng để tune
```

## 3A. Luồng triển khai chốt theo file Python

```text
00_audit_input_read_only
  -> 01_build_continuous_grid
  -> 02_split_time_series
  -> 03_feature_engineering_time
  -> 04_feature_engineering_space
  -> 05_feature_engineering_aggregate
  -> 06_vif_pls_diagnostics
  -> 07_feature_selection_sklearn
  -> 08_train_baselines
  -> 09_tune_lightgbm_expanding_optuna
  -> 10_train_final_train_validation
  -> 11_evaluate_final_test
  -> 12_explain_shap
  -> 13_train_prophet_long_term
```

Chi tiết fit/transform trong **một fold**:

```text
fold_train
  -> fit time/space/aggregate state (nếu state cần fit)
  -> fit VIF/PLS diagnostic và feature selector
  -> fit model
fold_val
  -> chỉ transform bằng state/selector/model của fold_train
  -> predict + metric
```

Vì vậy, câu đúng là **"train trên fold_train, validate trên fold_val"**;
không train `train + val` trong từng fold. Chỉ sau khi Optuna chọn được cấu
hình thắng mới refit tất cả transformer/selector/model trên `development =
Train + Validation`, rồi khóa performance bằng đúng một lần predict trên Test.

### Danh sách file sẽ có

```text
srcs/05_machine_learning/Forcasting_v3/
  00_audit_v3_final_cleaned.py              # read-only audit, fail-fast
  01_build_continuous_grid.py               # writer: ML-derived continuous timeline
  02_split_time_series_data.py
  03_feature_engineering_time_series.py
  04_feature_engineering_spatial.py
  05_feature_engineering_aggregate.py
  06_vif_pls_diagnostics.py
  07_select_features_sklearn.py
  08_train_baselines.py
  09_tune_lightgbm_expanding_optuna.py
  10_train_final_train_validation.py
  11_evaluate_final_test.py
  12_explain_shap.py
  13_train_prophet_long_term.py
  14_run_forecasting_pipeline.py
```

Notebook chỉ dùng để đọc artifact và trình bày, không chứa business logic:

```text
notebooks/29_forecasting_v3_final_cleaned/
  00_audit_continuous_split_review.ipynb
  01_feature_review.ipynb
  02_optuna_backtest_review.ipynb
  03_final_test_and_shap_review.ipynb
```

### Framework/thư viện dùng cho từng bước

Không có một framework duy nhất có thể làm đúng toàn bộ forecasting theo site.
Pipeline dùng mỗi thư viện đúng phạm vi của nó; business logic time-series vẫn
do Python/Pandas kiểm soát để tránh leakage.

| Giai đoạn | Framework/thư viện | Vai trò chốt |
|---|---|---|
| Đọc parquet, audit, reindex 15 phút, fill causal, lag/rolling | `pandas`, `numpy`, `pyarrow` | `pandas` group theo site và sort timestamp; đây là nơi thực thi rule gap/ban đêm, không dùng sklearn imputer. `pyarrow` ghi/đọc parquet chunk-safe. |
| Split và fold | `scikit-learn` (`TimeSeriesSplit`) + custom chronological wrapper | `TimeSeriesSplit` tạo expanding folds trên development; wrapper tự giữ test cuối và cùng timestamp cho mọi site. Không dùng `KFold`/random split. |
| Encode, scaling, selector | `scikit-learn` (`Pipeline`, `ColumnTransformer`, encoder, selector) | Fit state trên fold-train, rồi transform val/test bằng state đã khóa; chống leakage. |
| VIF | `statsmodels` | Chỉ diagnostic đa cộng tuyến numeric; không phải model train. |
| PLS | `scikit-learn` (`PLSRegression`) | Nhánh thử nghiệm supervised, chỉ giữ nếu CV tốt hơn raw feature; fit trong fold-train. |
| Baseline persistence | Python/Pandas | Rule deterministic t-1/t-96/t-672; không cần framework/model binary. |
| Short-term model | `lightgbm` (`LGBMRegressor`) | Gradient-boosted trees, nhận `sample_weight`, early stopping, xử lý nonlinear/tabular features. |
| Tuning | `optuna` | `TPESampler(seed=...)` + pruner; mỗi trial chạy toàn bộ expanding folds, objective là pooled validation WAPE. |
| Long-term | `prophet` | Series hourly/daily riêng theo site/aggregate; fit `ds`, `y`, seasonality; không dùng lag feature short-term. |
| Metrics | `numpy` + `scikit-learn.metrics` | MAE/RMSE/R² dùng sklearn; WAPE, sMAPE, Bias, Peak-MAE tự tính bằng numpy để kiểm soát zero-energy rule. |
| Giải thích | `shap` (`TreeExplainer`) | Chỉ giải thích LightGBM cuối sau khi test đã khóa; không dùng SHAP để tune. |
| Hình | `matplotlib`, `seaborn` + `viz_utils.py` | Chỉ đọc prediction/metric artifacts để vẽ, không chứa logic train. |

`scikit-learn.Pipeline` được dùng cho những transformer có `fit/transform`
(encode/scale/select). Không nhét reindex, target fill, lag hay rolling vào
Pipeline vì các bước đó cần group-by site và thứ tự thời gian; chúng được chạy
causal bằng Pandas trước, sau đó mới đưa feature matrix vào sklearn/LightGBM.

## 3B. Vai trò từng nhóm feature và thứ tự an toàn

1. **Time features**: calendar, lag, rolling. Target-derived lag/rolling chỉ
   lấy quá khứ; lịch sử trước partition được dùng làm context.
2. **Spatial/static features**: `site_id`, latitude, longitude, capacity,
   panel/inverter/campus. Đây là metadata; không phải nội suy không gian. Mọi
   encoding/scaling nếu có phải fit ở fold_train.
3. **Aggregate features**: aggregate weather/site chỉ hợp lệ khi giá trị đó
   biết tại prediction time. Aggregate có dính `energy_generated_kwh` phải
   shift về quá khứ; không dùng actual energy cùng timestamp của các site khác.
4. **VIF/PLS**: đặt sau FE nhưng chạy **trong từng fold_train**. VIF là audit
   đa cộng tuyến cho numeric features, không phải tiêu chí bắt buộc của
   LightGBM. PLS là supervised transformation nên chỉ được giữ nếu backtest
   chứng minh tốt hơn raw features; không được fit trên validation/test.
5. **sklearn feature selection**: fit trên fold_train sau PLS (nếu PLS được
   chọn); transform fold_val/test bằng feature set đã khóa.

## 3B.1. Outlier policy cho `v3_final_cleaned`

`v3_final_cleaned.parquet` là input đã qua ETL/outlier upstream. Pipeline
forecasting không rerun GMM-IF và không sửa/ghi đè input. Rule ban đêm trong
ML stage **không dùng clock-time cố định hoặc `weather_is_day` theo giờ làm
chuẩn chính**; định nghĩa `is_daylight` như sau:

1. Tính `is_daylight_physical` từ solar-elevation theo `latitude`, `longitude`,
   `timestamp` local ở đúng độ phân giải 15 phút.
2. Với row `energy_source=measured`, nếu `energy_generated_kwh >
   daylight_energy_epsilon` thì set `is_daylight=true` dù Open-Meteo
   `weather_is_day=0`. Đây là measured-energy override để giữ các slot ramp
   hoàng hôn/bình minh còn phát điện thật.
3. Với row không measured hoặc energy không vượt ngưỡng, dùng
   `is_daylight_physical` nếu tính được.
4. Nếu thiếu lat/lon nên không tính được solar-elevation, fallback sang
   `weather_is_day` nhưng gắn `daylight_source=weather_is_day_hourly_fallback`.
5. Nếu cả hai nguồn đều thiếu, fallback cuối bằng clock window và ghi vào
   `daylight_policy_audit.csv`.

`weather_is_day` và `weather_type_is_day` là cờ theo giờ nên chỉ dùng để audit
consistency/fallback, không là nguồn chính cho dữ liệu 15 phút. Audit bắt buộc
báo số dòng `weather_is_day=0` nhưng measured energy dương, đặc biệt theo
hour/month/site. Riêng row **mới do ML reindex** sẽ nhận rule ban đêm/gap theo
mục 3B.2; đó là ML-derived target, không phải chỉnh target nguồn.

Hai cột có sẵn từ ETL là `gmm_if_outlier_flag` và `gmm_if_outlier_reason`.
Chúng là nhãn hậu nghiệm được suy ra từ `energy_generated_kwh` thực tế tại cùng
timestamp, nên:

- không được dùng làm feature dự báo;
- không được tự động drop row vì sẽ tạo time gap, làm hỏng lag/rolling;
- được giữ nguyên cho mọi row source ở mọi split để audit và báo cáo chất lượng
  model.

Cột `outlier_group` được materialize **một lần** trong
`01_build_continuous_grid.py` (không phải chỉ trong `00_audit`), từ đó chảy
xuyên suốt `02_split` → `03_feature_engineering` → các stage train/eval mà
không script nào phải tự parse lại `gmm_if_outlier_reason`. Vẫn **không bao
giờ dùng làm feature dự báo** (nằm trong deny-list) — vai trò của nó là gắn
nhãn provenance để tính `sample_weight` và để báo cáo `metrics_by_site.csv`
theo scope, không phải input cho model.

| `outlier_group` | Điều kiện |
|---|---|
| `normal` | Không có rule nào trong `gmm_if_outlier_reason` (0 rule). |
| `gmm_if_consensus` | Đúng 1 rule, là `GMM_IF_CONSENSUS`. |
| `physical_over_capacity` | Đúng 1 rule, là `PHYSICAL_OVER_CAPACITY`. |
| `other_physical_rule` | Đúng 1 rule, là physical rule khác (no-sun, low-radiation, strong-sun, distribution-jump). |
| `multiple_rules` | Từ 2 rule trở lên cùng lúc (bất kể rule nào). |

**Audit capacity đã hoàn tất — kết luận, không còn là câu hỏi mở:**
`PHYSICAL_OVER_CAPACITY` chiếm 79.2% tổng flag (26,318/33,209 dòng), và gần
như 100% số đó đến từ đúng 2 site trong 42 site: site 19 (18,678 dòng, 29.7%
số dòng của chính site đó) và site 24 (7,823 dòng, 12.2%). Đã verify
`capacity_kw` hai site này khớp chính xác `number_of_panels × panel_wattage`
lấy từ `Solar_Site_Details.csv` (site 19: 104 panel × 330W = 34.32kW; site 24:
122 panel × 330W = 40.26kW) — **metadata đúng, không phải thiếu/impute**. Tuy
nhiên energy đo được vượt trần vật lý của khoảng 15 phút
(`capacity_kw × 0.25`) tới 2.52x (site 19, ratio median) và 1.36x (site 24),
với tỷ lệ vi phạm ổn định suốt ~2 năm dữ liệu (15-35%/tháng và 2-10%/tháng) —
không phải sự cố nhất thời hay giảm dần theo thời gian.

**Kết luận:** đây là lỗi cảm biến/đơn vị đo cục bộ ở đúng 2 site đó, không
phải nhiễu thống kê rải rác toàn hệ thống như `gmm_if_consensus`. Vì vậy
`physical_over_capacity` nhận xử lý **khác** — xem bảng experiment bên dưới.
`00_audit_v3_final_cleaned.py` xuất thêm `capacity_ceiling_audit.csv`
(per-site: `physical_over_capacity_pct`, `direct_ceiling_violation_pct`,
`ratio_median/p90/max`, `capacity_kw_is_imputed_pct`) làm diagnostic thường
trực — không phải hard gate (nguyên nhân site 19/24 đã rõ, cơ chế weight bên
dưới đã tự động xử lý) nhưng in cảnh báo mềm nếu tỷ trọng top-2-site tụt dưới
90% ở lần audit sau. Không hardcode `site_id`; rule chạy theo `outlier_group`
nên tự bắt đúng site nào đang vi phạm.

**Phát hiện thứ hai — blind spot của GMM-IF flag, KHÁC bản chất với site
19/24, không được xử lý giống nhau:** `capacity_ceiling_audit.csv` có 2 cột
độc lập — `physical_over_capacity_rows` (cờ GMM-IF cũ, đóng băng từ lúc ETL
chạy) và `direct_ceiling_violation_rows` (tính thẳng `energy > capacity_kw ×
0.25` trên `capacity_kw` hiện có trong `v3_final_cleaned`). Hai cột này lệch
nhau rất lớn: tổng `physical_over_capacity_rows` = 26,318 nhưng tổng
`direct_ceiling_violation_rows` = 104,892 — gấp 4 lần. 8 site có
`physical_over_capacity_rows=0` (GMM-IF coi là sạch) nhưng
`direct_ceiling_violation_pct` từ 6.5% đến 34.6% (site 11 cao nhất): site 1,
2, 6, 7, 8, 11, 12, 41.

Nguyên nhân: GMM-IF (`02_gmm_if.py`) chỉ flag khi `capacity_kw.notna()` —
lúc ETL chạy, 17 site (gồm cả 8 site trên) có `kWp` gốc null trong
`Solar_Site_Details.csv` nên rule tự động bỏ qua. `capacity_kw` sau đó mới
được impute ở bước khác trong `v3_final_cleaned`, và giá trị impute cho cả 17
site là **51.15kW giống hệt nhau** — đã verify đây chính là **median của 25
site có `kWp` thật** (median=51.1500), tức fallback chung toàn fleet, không
phải ước tính riêng cho từng site.

**Vì sao không được xử lý như `physical_over_capacity`:** ở site 19/24 đã
chứng minh `capacity_kw` ĐÚNG (khớp panel×watt) nên kết luận energy sai. Ở 8
site này thì ngược lại — `capacity_kw=51.15` chỉ là con số áng chừng đại trà,
rất có thể thấp hơn nhiều so với quy mô thật của site (fleet có site tới
384kW, 539kW). "Vượt trần 34.6%" ở site 11 nhiều khả năng là ảo giác do
capacity bị đánh giá thấp, không phải energy sai. Đây là lỗi **metadata
imputation**, không phải lỗi đo đạc — **tuyệt đối không dùng
`direct_ceiling_violation` để zero-weight khi train**, vì sẽ phạt oan energy
tốt.

**Việc cần làm (ngoài scope forecasting, không tự sửa trong pipeline này):**
tìm `capacity_kw` thật cho 17 site bị impute (tra lại nguồn gốc, suy từ
`number_of_panels` nếu có, hoặc ước lượng từ percentile-95 sản lượng thực tế
của chính site) — việc của tầng ETL/metadata, không phải của forecasting.
Trước mắt, `assert_audit_gates` cần in thêm cảnh báo riêng cho nhóm site có
`capacity_kw_is_imputed_pct` cao **và** `direct_ceiling_violation_pct` cao,
tách biệt khỏi cảnh báo top-2-site hiện tại (cảnh báo đó chỉ nhìn
`physical_over_capacity_rows` nên không thấy được blind spot này).

### Experiment train bắt buộc

**Mặc định pipeline chỉ train `measured_only_headline`** (config
`training.active_experiment`). 3 experiment còn lại là sensitivity run thủ
công (`--experiment=<tên>`), không tự động chạy cùng `--stage all` — tránh
nhân 4x chi phí LightGBM/Optuna mỗi lần chạy pipeline.

| Experiment | `outlier_group=physical_over_capacity` | `outlier_group=gmm_if_consensus` | `outlier_group∈{other_physical_rule, multiple_rules}` | ETL-imputed | Vai trò |
|---|:---:|:---:|:---:|:---:|---|
| `measured_only_headline` | **0** | 1 | 1 | 0 | Model chính, mặc định duy nhất chạy tự động. |
| `measured_plus_etl_imputed` | **0** | 1 | 1 | 1 | Sensitivity: ETL-imputed có giúp model học smooth profile không. |
| `zero_weight_gmm_consensus` | 0 | **0** | 1 | 0 | Sensitivity cho anomaly thống kê, vẫn giữ continuity/time context. |
| `zero_weight_all_flagged` | 0 | 0 | **0** | 0 | Sensitivity mạnh nhất, không mặc định là model deploy. |

Mọi hàng `normal` luôn weight=1 ở cả 4 experiment (không hiện trong bảng để
gọn). `after_source_gap`/`exclude_from_training`/synthetic rows luôn weight=0
ở mọi experiment — không đổi theo cột trên.

**Khác biệt so với thiết kế gốc:** `physical_over_capacity` nhận weight=0 ở
**mọi** experiment, kể cả `measured_only_headline` — không chỉ 2 experiment
sensitivity như bảng ban đầu dự kiến. Lý do: đây là giá trị không thể tồn tại
về vật lý (đã verify metadata `capacity_kw` đúng ở mục trên), không phải
"bất thường nhưng có thể là thật" như `gmm_if_consensus`. Cho model chính học
theo tín hiệu này tương đương dạy nó tái tạo lỗi đo đạc, và pha loãng WAPE
dùng để chọn model.

Sample weight chỉ áp dụng vào loss của fold-train. Dòng ETL-imputed, synthetic
và flagged vẫn tồn tại trong history để lag/rolling phản ánh đúng business
timeline đã chốt. Không dùng outlier group/flag để điều chỉnh test prediction.

`metrics_by_site.csv` bắt buộc báo metrics theo các scope chuẩn:

```text
all_rows
daylight_rows
measured_only
etl_imputed_rows
measured_excluding_after_gap_rows
non_outlier_rows
gmm_if_consensus_rows
physical_over_capacity_rows
other_physical_rule_rows
multiple_rules_rows
after_source_gap_rows
exclude_from_training_rows
```

Vì mỗi scope này vẫn tính per-`site_id`, site có tỷ lệ `physical_over_capacity`
cao (hiện là site 19/24) tự động hiện ra trong scope `physical_over_capacity_rows`
mà không cần code riêng theo site.

Các scope flagged/after-gap có thể ít row ở vài site; khi không đủ row, ghi
`n_rows` và `null` metric thay vì suy diễn kết quả. **Headline metric** và
model selection dùng:

```text
daylight_rows ∩ measured_only ∩ not after_source_gap_rows ∩ not exclude_from_training
```

`etl_imputed_rows` và `after_source_gap_rows` là sensitivity/audit, không phải
con số headline để bảo vệ performance.

## 3B.2. Time-gap policy cho `v3_final_cleaned`

Đồ án cần timeline 15 phút liên tục để tạo lag/rolling đúng cách.
`v3_final_cleaned` đã xử lý null của các row sẵn có, nhưng còn source gap vì
timestamp đó hoàn toàn không tồn tại. Đây là xử lý **chỉ trong ML**: tạo một
bản derived từ input read-only, không ghi trở lại ETL, warehouse hay Supabase.

Mọi gap được lấp thành một timeline năng lượng liên tục để lag/rolling vận hành
đúng. Với gap ≥24 giờ, business rule chốt là coi thiết bị/ngõ thu thập đã ngưng
hoạt động: energy synthetic bằng `0`. Mọi energy sinh từ imputation vẫn không
là ground truth đánh giá.

Timestamp local hiện tại là source of truth: DST đã được chuẩn hóa upstream,
row lùi đã loại. Không đổi sang UTC trong ML và không dùng hourly bucket BI
đã shift để xây dựng grid.

```text
v3_final_cleaned (observed rows)
  -> canonical 15-minute grid per site, từ min đến max timestamp của chính site
  -> phân loại gap ngắn/dài và gắn cờ provenance
  -> lấp toàn bộ gap bằng cascade causal, không dùng future target
  -> chronological split
  -> feature tables liên tục theo timestamp, với eligibility rõ ràng
```

### Quy tắc tạo grid và impute

1. Reindex mỗi site theo 15 phút **chỉ trong khoảng hoạt động quan sát được của
   site đó**; không tạo row trước ngày bắt đầu hoặc sau ngày kết thúc site.
2. Static metadata (`capacity`, location, panel...) forward/backward fill trong
   site; calendar tạo lại từ timestamp; weather join từ timestamp gốc và có cờ
   missing/imputed riêng.
3. Ngưỡng gap ngắn được cấu hình, mặc định đề xuất **≤ 2 giờ (8 mốc 15 phút)**.
   Ngưỡng chỉ quyết định method ưu tiên và nhãn audit; gap dài vẫn phải được
   lấp bằng fallback causal để timeline liên tục.
4. Energy ở ban đêm theo `is_daylight=false` được điền `0` với method
   `night_zero`. Đây là deterministic, không phải nội suy.
5. Với gap **<24 giờ**, energy thiếu ban ngày dùng cascade hoàn toàn causal, theo thứ tự:
   `seasonal_persistence_day_measured` (t-96, chỉ `energy_source=measured`) →
   `seasonal_persistence_week_measured` (t-672, chỉ `energy_source=measured`) →
   `expanding_site_time_profile_past_only` (median lịch sử **trước t** của
   cùng site × quarter-hour × season/month) →
   `site_daylight_zero_or_global_profile_fallback`. Fallback cuối bắt buộc phải
   có để không còn NaN: nếu cùng site chưa đủ history thì dùng median quá khứ
   toàn bộ site cùng quarter-hour/season; nếu vẫn rỗng thì đặt 0 và log số row
   vào `continuous_grid_audit.csv`. Profile chỉ update từ target measured, nên
   gap 4 ngày không tạo chain từ energy synthetic.
6. Với gap **≥24 giờ** (ví dụ 4 ngày), đặt `energy_generated_kwh=0.0` cho toàn
   bộ row reindex; method `machine_failure_zero`. Đây là business assumption
   đã cấu hình, không phải output của linear/regression hay GMM fitting.
7. Không dùng `linear interpolation`, `cubic`, hay regression: các cách đó
   cần nhìn target phía sau gap hoặc học target ngay trong đoạn thiếu, không
   phù hợp để dựng history forecasting.
8. Mọi row phải có đúng một giá trị `energy_source`. Những row mới do ML
   reindex phải có `timestamp_was_inserted=true`. Không tạo cột
   provenance target thứ hai; mọi tên cũ kiểu imputation-method bị xem là
   deprecated. `energy_source` là cột provenance duy nhất cho target energy.
9. Timeline sau reindex + fill liên tục cả timestamp lẫn energy, nên lag 1/4/96
   và rolling giữ được across-gap. Target synthetic không được dùng để tính
   loss hoặc metric chính; `energy_source=measured` là ground truth chính duy
   nhất.
10. Sau mỗi source gap, đánh dấu `AFTER_SOURCE_GAP` cho đúng
    `max_lag_steps` row observed tiếp theo. Với cấu hình hiện tại
    `max_lag_steps=672`, tương ứng 7 ngày ở tần suất 15 phút.

### Train và đánh giá trên chuỗi liên tục

- Gap ngắn và dài đều đã có synthetic history causal, nên persistence,
  lag/rolling và plot liên tục. `energy_source` đi cùng feature table để audit
  mức độ phụ thuộc vào history synthetic hoặc ETL-imputed.
- `sample_weight=0` cho target energy impute khi fit; `energy_source=measured`
  có weight theo outlier policy. Cách này không coi energy do ETL/ML fill sinh
  ra là nhãn thật.
- Validation/test prediction được tạo cho toàn timeline liên tục, nhưng MAE,
  RMSE, WAPE, sMAPE, R² headline chỉ chấm `energy_source=measured`,
  `is_daylight=true`, `exclude_from_training=false` và không nằm trong
  `AFTER_SOURCE_GAP`.
- Báo riêng coverage: measured rows, ETL-imputed rows, ML synthetic rows,
  night-zero rows, và source-gap intervals theo site/fold.
- Baseline persistence dùng giá trị lịch sử đã có/impute causal; report thêm
  metric `measured_only` và `measured_excluding_after_gap_rows` để không được
  lợi từ target giả.

### Output của stage continuous data

```text
data/model/v3_final_cleaned/01_continuous/<run_id>/
  continuous_grid_manifest.json
  continuous_grid_audit.csv
  observed_gap_events.parquet
  continuous_full.parquet
```

Các cột audit bắt buộc: `energy_source`, `timestamp_was_inserted`,
`weather_is_observed`, `source_gap_id`, `is_daylight`, `daylight_source`,
`exclude_from_training`, `exclude_reason`, `training_quality_reason`,
`after_source_gap_steps_remaining`.

### Gap reason trong training/audit

Không sửa input `v3_final_cleaned.parquet` và không rerun ETL/GMM-IF. Trong
**bản ML-derived continuous grid**, gap ≥24 giờ được gắn bằng cờ riêng
`exclude_from_training=true` và `exclude_reason=MACHINE_FAILURE_DATA_GAP`.
Không sửa `gmm_if_outlier_flag` để tránh trộn nghĩa "sensor/outlier thống kê"
với "mất kết nối nguồn dữ liệu".

| Điều kiện | `training_quality_reason` | Train loss / metric |
|---|---|---|
| Row raw, không vấn đề | rỗng | dùng bình thường theo outlier policy |
| Row được thêm, gap ≤ 2h | `SOURCE_GAP_SHORT_IMPUTED` | lấp causal, weight 0, không chấm metric chính |
| Row trong gap >2–24h | `SOURCE_GAP_LONG_OUTAGE` | lấp causal, weight 0, không chấm metric chính |
| Row trong gap ≥24h (ví dụ 4 ngày) | `SOURCE_GAP_MAJOR_OUTAGE+MACHINE_FAILURE_DATA_GAP` | energy=0, `exclude_from_training=true`, weight 0, không chấm metric chính |
| Row measured trong `max_lag_steps` sau gap | `AFTER_SOURCE_GAP` | giữ target measured; report riêng cả included/excluded để audit history synthetic |

`gmm_if_outlier_reason`, `exclude_reason` và `training_quality_reason` cùng
được giữ trong prediction audit. Khi một row có nhiều reason, report song song,
không gộp vào cùng một cột để tránh hiểu sai “outlier sensor” với “missing
source”.

## 3C. Baseline, Optuna, model pickle, test và SHAP

`08_train_baselines.py` chạy baseline trên đúng split/fold/horizon của model:

1. **Persistence theo horizon**: dự báo `energy(t + h) = energy(t)` của đúng
   site. Với `h=1` đây là persistence 15 phút; với `h=4` đây là persistence 1
   giờ. Đây là benchmark bắt buộc cho từng horizon.
2. **Seasonal persistence 1 ngày**: dự báo `energy(t + h) = energy(t + h - 96
   bước)`, tức cùng quarter-hour hôm qua theo đúng horizon.
3. **Seasonal persistence 1 tuần**: dùng lag 672 bước nếu coverage đủ; là
   benchmark phụ để kiểm tra weekly seasonality.
4. **Prophet** là baseline/model riêng của nhánh long-term, không thay thế
   persistence 15 phút.

Baseline ghi prediction và MAE/RMSE/WAPE/sMAPE theo từng fold/site vào
`data/model/v3_final_cleaned/05_baselines/<run_id>/baseline_metrics.csv` để
`09_tune...` và `11_evaluate...` so sánh cùng một thước đo. Không có baseline
thì không chứng minh được LightGBM tốt hơn quy tắc đơn giản.

### Baseline là model nào?

| Model | Nhánh | Công thức prediction | Mục đích |
|---|---|---|---|
| `persistence_horizon` | Short-term 15 phút/1 giờ | `ŷ(s, t+h) = y(s, t)` | Benchmark tối thiểu cho từng horizon: nếu LightGBM không vượt thì model không có giá trị thực tế. |
| `seasonal_persistence_day` | Short-term 15 phút | `ŷ(s, t) = y(s, t-96 steps)` | So với đúng cùng quarter-hour của hôm qua. |
| `seasonal_persistence_week` | Short-term 15 phút | `ŷ(s, t) = y(s, t-672 steps)` | Benchmark phụ cho chu kỳ tuần, chỉ chạy khi history đủ. |
| `prophet_hourly_or_daily` | Long-term | Prophet dự báo series aggregate theo giờ/ngày từng site | Benchmark/model long-term cho trend và seasonality; không cạnh tranh trực tiếp với 15 phút. |

`08_train_baselines.py` không cần `.pkl` cho ba persistence models vì chúng là
quy tắc deterministic. Với Prophet, lưu `prophet_model.pkl` riêng ở
`models/v3_final_cleaned/<run_id>/long_term/` cùng frequency và regressors đã
dùng.

Short-term 15 phút sinh `prediction_audit.parquet` với schema:
`site_id`, `timestamp`, `partition`, `fold`, `horizon`, `y_true`, `y_pred`,
`model_name`, `is_daylight`, `outlier_flag`, `energy_source`,
`exclude_from_training`, `exclude_reason`, `training_quality_reason`.

Prophet long-term sinh file riêng `prediction_audit_long_term.parquet` với
schema tương tự nhưng thêm `granularity` (`hourly`/`daily`) và không upsample
ngầm về 15 phút.

### Metrics bắt buộc và ý nghĩa

Ký hiệu: `yᵢ` là energy thực tế, `ŷᵢ` là dự báo, `eᵢ = yᵢ - ŷᵢ`, `n` là số
dòng đánh giá. Tất cả metrics tính độc lập theo **fold**, **site**, **horizon**
và scope chuẩn ở mục 3B.1; sau đó mới tổng hợp.

| Metric | Công thức | Dùng để kết luận |
|---|---|---|
| MAE | `mean(abs(eᵢ))` | Sai số kWh trung bình, trực quan và ít nhạy với cực trị hơn RMSE. |
| RMSE | `sqrt(mean(eᵢ²))` | Phạt mạnh các sai số đỉnh lớn; hữu ích cho rủi ro peak generation. |
| WAPE | `sum(abs(eᵢ)) / sum(abs(yᵢ)) × 100` | Metric chọn model/tune chính; ổn định khi energy bằng 0, khác MAPE. Thấp hơn là tốt hơn. |
| sMAPE | `mean(2×abs(eᵢ)/(abs(yᵢ)+abs(ŷᵢ)+ε)) × 100` | So sánh tỷ lệ sai số có đối xứng hơn MAPE; chỉ metric phụ do PV nhiều số 0. |
| R² | `1 - sum(eᵢ²)/sum((yᵢ-mean(y))²)` | Mức giải thích biến thiên; không dùng một mình để chọn model. Cao hơn là tốt hơn. |
| Bias | `mean(ŷᵢ-yᵢ)` | Model có dự báo cao/thấp hệ thống hay không. Gần 0 là tốt. |
| Peak MAE | MAE trên top 10% `y_true` daylight mỗi site | Chất lượng ở các điểm công suất cao. |
| Improvement vs persistence | `(WAPE_persistence - WAPE_model) / WAPE_persistence × 100` | Phần trăm LightGBM cải thiện so với persistence 15 phút. Dương là tốt. |

Khi tổng hợp nhiều fold, WAPE chọn model phải là pooled WAPE:
`sum_all_folds(abs(error)) / sum_all_folds(abs(y_true))`. Không tính trung bình
WAPE theo row count vì các fold có tổng năng lượng khác nhau.

Không dùng MAPE làm objective vì `energy_generated_kwh` có nhiều giá trị 0 ban
đêm. Những dòng ban đêm vẫn được báo riêng `all_rows`, nhưng model selection
short-term dùng `daylight_rows` để tránh zero rows làm đẹp metric giả tạo.

### Ba file metrics cuối có gì

1. `metrics_overall.json`
   - checksum input, run_id, split boundaries, seed, frequency, horizon;
   - MAE/RMSE/WAPE/sMAPE/R²/Bias/Peak-MAE của mỗi baseline, LightGBM L2,
     LightGBM Huber và Prophet (ở granularity riêng);
   - mean/std/worst-fold của Optuna best trial;
   - improvement vs `persistence_horizon`.
2. `metrics_by_site.csv`
   - một dòng cho `run_id × model_name × partition × site_id × horizon × scope`;
   - `scope` lấy đúng list chuẩn ở mục 3B.1;
   - các metrics phía trên + row count + target sum.
3. `prediction_audit.parquet`
   - row-level actual/prediction/residual và metadata để tái tạo toàn bộ metric
     hay biểu đồ mà không phải train lại.
4. `prediction_audit_long_term.parquet`
   - chỉ có khi chạy Prophet/long-term; chứa `granularity` và metric không trộn
     với short-term 15 phút.

- `09_tune...`: mỗi trial lặp tất cả expanding folds. Lưu params + CV metrics;
  không cần lưu hàng trăm `.pkl` theo trial.
- Chỉ giữ `best_params.json` trong `06_tuning/<run_id>/`.
- `10_train_final...`: refit một pipeline hoàn chỉnh trên development
  (Train+Validation) và lưu đúng một `model.pkl`, cùng `feature_list.json`,
  `transformers.pkl`/`pls.pkl` nếu nhánh PLS thắng.
- `11_evaluate...`: chỉ mở test một lần, sinh `prediction_audit.parquet`,
  `prediction_audit_long_term.parquet` nếu có Prophet, và metrics cuối.
- `12_explain_shap.py`: chạy sau model cuối, dùng sample có seed cố định từ
  test để giải thích model; SHAP không được dùng để tune model hay thay test
  metric.

### Quy tắc split

- Chia bằng **timestamp**, không random split và không KFold IID.
- Test là đoạn thời gian cuối cùng; không dùng cho feature selection, Optuna hay chọn model.
- Validation trong expanding CV là các block liên tiếp, cùng horizon với use case.
- Split dates được lưu vào manifest để chạy lại đúng kết quả.
- Nếu từng site có mốc dữ liệu khác nhau, giữ cùng nguyên tắc chronological per-site và ghi rõ coverage của từng site; không bỏ âm thầm một site.
- `horizon_steps` được lưu trong config và manifest. Feature manifest phải có
  `max_lookback_steps`, `min_target_derived_lag_steps`; `07_select...` assert
  `min_target_derived_lag_steps >= horizon_steps`.

### Quy tắc feature theo point-in-time

- Chỉ dùng `shift(+lag)` / rolling có `closed='left'` hoặc shift target trước khi rolling.
- Feature tại thời điểm `t` chỉ nhận dữ liệu nhỏ hơn hoặc bằng thời điểm biết được lúc dự báo; tuyệt đối không dùng `t+h`.
- Với validation/test, history cuối của partition trước được phép làm lookback. Không được lấy bất kỳ giá trị nào ở tương lai của partition hiện tại.
- Mọi scaler, encoder, imputer (nếu có) và feature selector đều `fit` trên train fold; validation/test chỉ `transform`.
- `gmm_if_outlier_flag` chỉ dùng để audit, loại mẫu train hoặc sample-weight theo config. Không dùng làm feature đầu vào vì nó được suy ra từ energy thực tế cùng timestamp.
- Các cột hậu nghiệm như `energy_pred`, residual, KPI/dashboard, hay expected energy được tính từ actual/future đều bị deny-list. `sunshine_duration` mặc định deny-list vì là đại lượng tích lũy trong giờ; chỉ được dùng nếu shift về quá khứ hoặc chứng minh availability tại prediction time. Weather chỉ được dùng khi chứng minh là có sẵn tại prediction time; nếu chỉ có weather historical thì ghi rõ đây là backtest with observed weather.

## 4. Feature engineering dự kiến

### Short-term LightGBM

- Calendar: hour, minute, day_of_week, month, season, sin/cos hour và day-of-year.
- Energy history candidate: lag 1, lag 4, lag 96, lag 672. Với mỗi horizon,
  tự loại mọi target-derived lag nhỏ hơn horizon; rolling mean/std/min/max luôn
  dùng history đã shift tối thiểu `horizon_steps`.
- Weather/covariate hợp lệ: shortwave radiation, DNI, diffuse radiation,
  temperature, cloud cover, wind, precipitation và metadata site nếu không null
  quá mức. `sunshine_duration` mặc định không dùng làm feature hiện tại.
- Metadata không đổi (capacity, panel count, latitude/longitude…) được kiểm tra null/cardinality trước; không dùng nếu chất lượng không đạt.
- Categorical encode và feature selection nằm **sau split**, riêng trong từng fold.

### Long-term Prophet

- Resample theo giờ hoặc ngày, xác định ở config.
- Dùng `ds`, `y`, seasonality ngày/tuần/năm; weather regressor chỉ khi availability được bảo đảm.
- So sánh với seasonal-naive cùng horizon. Prophet không dùng lag/rolling feature của short-term.

## 5. Model selection và Optuna

### Baseline bắt buộc

Baseline không phải model cuối, mà là ngưỡng để chứng minh model học được giá trị thực:

1. Persistence theo horizon: dùng giá trị quan sát gần nhất trước thời điểm dự báo.
2. Seasonal persistence: cùng time-of-day của ngày trước / tuần trước (tùy horizon).
3. Prophet seasonal baseline cho long-term.

### Optuna với expanding-window CV

- Objective chính: **pooled WAPE** trên validation folds (ổn định hơn MAPE khi PV gần 0).
- Metric phụ: MAE, RMSE, sMAPE, R²; báo riêng daytime/all rows và per-site.
- Tuning LightGBM: `learning_rate`, `num_leaves`, `max_depth`, `min_child_samples`, `feature_fraction`, `bagging_fraction`, `lambda_l1`, `lambda_l2`, số boosting rounds/early stopping và loss `l2`/`huber`.
- Mỗi trial chạy tất cả folds; objective là pooled WAPE trên toàn validation
  folds hoặc weighted theo `sum(abs(y_true))`, không weight theo số dòng. Lưu cả
  variance/worst-fold để không chọn model chỉ tốt ở một fold.
- Random seed cố định và ghi vào config/manifest. Không dùng test để chọn trial.
- Có pruning để dừng trial yếu; số trial và timeout là config, không hardcode trong code.

### Ngân sách tính toán

- LightGBM short-term là **global model** cho 42 site, có `site_id`/metadata làm
  feature; không train 42 model riêng ở v1.
- Optuna mặc định đề xuất: `n_trials=30`, `timeout_minutes=90`, `n_jobs=1`,
  `num_boost_round` tối đa 2,000 với early stopping. Các giá trị này nằm trong
  YAML, không hardcode trong Python.
- Nếu runtime vượt ngân sách, dùng một trong hai chế độ config:
  `tuning_sample_mode=recent_months` hoặc `tuning_sample_mode=site_stratified`,
  nhưng final train/test vẫn chạy trên toàn bộ data hợp lệ.
- Prophet long-term mặc định train **per-site** ở hourly/daily vì Prophet không
  phải global tabular model. Giới hạn `max_sites`, `timeout_minutes` và frequency
  nằm trong YAML; nếu không đủ thời gian thì chạy aggregate/site đại diện để làm
  baseline phụ, không dùng để thay kết luận short-term.

### Train cuối và so sánh

1. Chọn best params từ expanding folds.
2. Train model cuối trên **Train + Validation**.
3. Đánh giá một lần trên Test và khóa metrics.
4. Sau khi test đã được báo cáo, nếu cần model deploy, train thêm `production_model` trên toàn bộ Train + Validation + Test, nhưng không dùng metrics của model này để tuyên bố performance.
5. Benchmark so sánh baseline, LightGBM L2, LightGBM Huber và Prophet long-term ở cùng tập/horizon phù hợp.

## 6. Artifact và vị trí lưu bắt buộc

```text
data/mlmart_base/v3_final_cleaned.parquet             # input, không bị ghi đè
data/model/v3_final_cleaned/00_audit/<run_id>/          # read-only input audit
data/model/v3_final_cleaned/01_continuous/<run_id>/     # continuous grid + gap audit
data/model/v3_final_cleaned/02_splits/<run_id>/         # split manifest + split parquet
data/model/v3_final_cleaned/03_features/<run_id>/       # feature parquet + feature manifest
data/model/v3_final_cleaned/04_diagnostics/<run_id>/    # VIF/PLS/selector diagnostics
data/model/v3_final_cleaned/05_baselines/<run_id>/      # baseline predictions + metrics
data/model/v3_final_cleaned/06_tuning/<run_id>/         # Optuna + expanding-CV results
data/model/v3_final_cleaned/07_metrics/<run_id>/        # final machine-readable metrics
models/v3_final_cleaned/<run_id>/                       # fitted models, feature list, config
reports/ml_training_v3_final_cleaned/
  <run_id>/                                           # Markdown/summary được viết sau
pictures/ml_training_v3_final_cleaned/
  <run_id>/
    00_audit/                                          # quality, gap, timestamp/peak sanity
    01_splits/                                         # timeline Train/Val/Test + expanding folds
    02_tuning/                                         # Optuna history + parameter importance + CV fold metrics
    03_evaluation/                                     # benchmark, actual-vs-pred, residual, site/hour heatmap
    04_explainability/                                 # LightGBM importance + SHAP
logs/ml_training_v3_final_cleaned_<run_id>.log
```

`data/model/v3_final_cleaned/07_metrics/<run_id>/` chỉ có 3 output chính:

1. `metrics_overall.json`: data contract, split dates, benchmark tổng, best params, overall train/CV/test metrics, seed, input checksum.
2. `metrics_by_site.csv`: benchmark và test metrics của đủ 42 site; có thể pivot theo horizon/daytime trong cùng file.
3. `prediction_audit.parquet`: row-level actual/prediction/residual/partition/horizon để vẽ lại bất cứ hình nào.

Feature importance, SHAP, Optuna history và fold metrics nằm đúng giai đoạn
sinh ra chúng (`06_tuning/<run_id>/` hoặc `models/v3_final_cleaned/<run_id>/`),
không nhân bản sang metrics cuối.

## 7. Hình và bảng phải có để báo cáo

1. Timeline minh họa Train/Validation/Test và expanding folds.
2. Optuna history, parameter importance, best-trial table (`02_tuning/` trên
   pictures, đọc từ `06_tuning/<run_id>/`).
3. Benchmark table: baseline vs LightGBM L2 vs Huber vs Prophet, cả all/daytime/per-site.
4. Actual-vs-pred local zoom cho toàn bộ 42 site (hoặc ít nhất 42 trang/plots có manifest), residual theo thời gian (`03_evaluation/`).
5. Error heatmap site × hour, error by month/horizon và worst-site ranking (`03_evaluation/`).
6. Feature importance + SHAP summary/dependence cho model cuối (`04_explainability/`).
7. Time-gap, time-shift và outlier audit tách riêng (`00_audit/`); không đánh đồng outlier flag với forecast error.

## 8. Các file sẽ sửa/tạo sau khi anh duyệt

Sửa/tạo đúng các file trong `srcs/05_machine_learning/Forcasting_v3/`, không
tạo pipeline song song và không dùng lại numbering cũ:

1. `00_audit_v3_final_cleaned.py` — read-only audit, fail-fast.
2. `01_build_continuous_grid.py` — tạo ML-derived continuous grid.
3. `02_split_time_series_data.py` — final split + expanding-window manifest.
4. `03_feature_engineering_time_series.py` — feature point-in-time theo fold.
5. `04_feature_engineering_spatial.py` — metadata/site feature.
6. `05_feature_engineering_aggregate.py` — aggregate feature hợp lệ theo time.
7. `06_vif_pls_diagnostics.py` — VIF/PLS diagnostics.
8. `07_select_features_sklearn.py` — fit selector trên train fold, persist feature set.
9. `08_train_baselines.py` — persistence/seasonal-naive baseline.
10. `09_tune_lightgbm_expanding_optuna.py` — expanding CV + Optuna.
11. `10_train_final_train_validation.py` — refit Train+Validation.
12. `11_evaluate_final_test.py` — mở Test đúng một lần.
13. `12_explain_shap.py` — explainability sau khi metric khóa.
14. `13_train_prophet_long_term.py` — nhánh long-term riêng.
15. `14_run_forecasting_pipeline.py` — runner stage rõ ràng: `audit`,
    `continuous`, `split`, `features`, `diagnostics`, `baselines`, `tune`,
    `train_final`, `evaluate`, `shap`, `prophet`, `all`.
16. Cập nhật `README_forecasting_v3.md` thành hướng dẫn chạy/reproduce theo
    `v3_final_cleaned`.

## 9. Điều kiện pass trước khi train/xuất kết quả

- Input contract pass; không duplicate key, timezone/DST policy được ghi nhận.
- `energy_source` phủ 100% row trong continuous grid; không có null và tỷ lệ
  `measured`/`etl_imputed`/synthetic được ghi vào audit. Nếu join raw không
  match đủ key hoặc row count raw/mlmart bất thường thì fail.
- Không còn NaN ở `energy_generated_kwh` sau continuous cascade.
- Tỷ lệ dùng clock-window fallback cho `is_daylight` không vượt ngưỡng trong
  config; vượt ngưỡng thì fail vì không còn bảo vệ được rule thiên văn.
- Peak-hour argmax theo tháng/mùa (`peak_shift_audit.csv`) là **diagnostic-only,
  không gate** — argmax trên đường cong PV gần phẳng bị nhiễu (chênh peak vs
  á-quân thường <5%) và bị méo bởi tháng có DST-transition (tháng 10 lệch
  trung bình -1.36h so với các tháng khác dao động -0.45..+0.64h — đã verify
  đây là artifact gộp tháng, không phải lệch dữ liệu thật). Hard gate thật
  dùng cross-correlation energy↔shortwave theo lag -4..+4 bước 15 phút
  (`energy_shortwave_lag_audit.csv`): fail nếu tỷ lệ site có `best_lag < 0`
  (shortwave tương lai giải thích energy hiện tại — hướng non-causal thật)
  vượt `daylight.lag_check_fail_negative_site_pct` trong config.
- `after_source_gap_rows` và tỷ lệ row bị phủ bởi cửa sổ `max_lag_steps` được
  ghi trong `continuous_grid_audit.csv`. Headline metric phải dùng
  `measured_excluding_after_gap_rows`; after-gap metric chỉ là sensitivity.
- `outlier_group` phủ 100% row (không null); `capacity_ceiling_audit.csv`
  báo per-site tỷ lệ/mức độ `physical_over_capacity` — diagnostic, in cảnh
  báo mềm nếu tỷ trọng top-2-site tụt dưới 90%, không fail cứng.
- Không có future leakage trong feature manifest.
- `07_select_features_sklearn.py` phải assert
  `min_target_derived_lag_steps >= horizon_steps`.
- Test không xuất hiện trong Optuna trials, selected features hay early stopping decisions.
- Mọi fold có data đủ và coverage per-site được báo cáo.
- Best model phải vượt baseline theo pooled WAPE trên headline scope và ít nhất
  không thoái hóa ở worst sites/hours.
- Tất cả metrics/hình/model đều trỏ về cùng `run_id` và cùng checksum input.

## 10. Không nằm trong scope hiện tại

- Không refill null, không rebuild ETL/warehouse, không thay đổi Supabase, Docker, object storage hoặc Git.
- Không claim causal performance nếu weather dùng trong backtest chưa chứng minh availability tại prediction time.
- Không train model cuối trên toàn bộ dữ liệu rồi dùng chính dữ liệu đó để báo cáo test metric.
