# Forecasting v3_final_cleaned

Pipeline nay chi thuoc Machine Learning. Input goc khong bi ghi de:

```text
data/mlmart_base/v3_final_cleaned.parquet
data/raw/Solar_Energy_Generation.csv
```

Config:

```text
config/05_machine_learning/forecasting_v3_final_cleaned.yaml
```

## Che do train an toan hien tai

Mac dinh config dang de:

```yaml
training:
  mode: production_lightgbm
  allow_full_train: false
  mock:
    enabled: false
    max_train_rows_per_horizon: 20000
    max_eval_rows_per_horizon: 20000
  lightgbm:
    device: gpu
    gpu_platform_id: 0
    gpu_device_id: 0
    force_cpu_if_gpu_unavailable: true
    n_jobs: 1
```

Nghia la:

- Khong dung sklearn fallback.
- Mac dinh khong cho full train de tranh lo tay an CPU/RAM/GPU.
- Muon smoke test thi dung config tam bat `mock.enabled=true`.
- Neu GPU LightGBM loi OpenCL/CUDA tren may local, code retry CPU LightGBM voi `n_jobs=1`, khong doi sang sklearn.
- Optuna bi skip khi `mock.enabled=true`; muon train that thi doi `allow_full_train=true` co chu dich, tang resource budget, roi moi chay tuning.

## Chay tung stage

Dung cung mot `run_id` cho toan bo lan chay:

```bash
RUN_ID=manual_$(date +%Y%m%d_%H%M%S)
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage audit --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage continuous --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage split --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage features_time --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage features_spatial --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage features_aggregate --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage diagnostics --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage select --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage baselines --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage tune --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage train_final --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage evaluate --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage shap --run-id "$RUN_ID"
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage prophet --run-id "$RUN_ID"
```

Chay mot lenh:

```bash
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage all --run-id "$RUN_ID"
```

## Output chinh

```text
data/model/v3_final_cleaned/00_audit/<run_id>/
data/model/v3_final_cleaned/01_continuous/<run_id>/continuous_full.parquet
data/model/v3_final_cleaned/02_splits/<run_id>/
data/model/v3_final_cleaned/03_features/<run_id>/
data/model/v3_final_cleaned/04_diagnostics/<run_id>/
data/model/v3_final_cleaned/05_baselines/<run_id>/baseline_metrics.csv
data/model/v3_final_cleaned/06_tuning/<run_id>/best_params.json
models/v3_final_cleaned/<run_id>/h1/model.pkl
models/v3_final_cleaned/<run_id>/h4/model.pkl
data/model/v3_final_cleaned/07_metrics/<run_id>/metrics_overall.json
data/model/v3_final_cleaned/07_metrics/<run_id>/metrics_by_site.csv
data/model/v3_final_cleaned/07_metrics/<run_id>/prediction_audit.parquet
data/model/v3_final_cleaned/07_metrics/<run_id>/prediction_audit_long_term.parquet
```

## Rule bao ve metric

`energy_source` la cot provenance target duy nhat:

```text
measured
etl_imputed
night_zero
causal_day_persistence
causal_week_persistence
causal_profile_median
fallback_zero
machine_failure_zero
```

Headline metric chi cham:

```text
energy_source == measured
is_daylight == true
after_source_gap_steps_remaining == 0
exclude_from_training == false
```

`weather_is_day` chi la hourly fallback/audit. Daylight chinh dung solar
elevation 15 phut; measured energy duong duoc override daylight de khong loai
nham ramp binh minh/hoang hon.

## Notebook

Notebook import smoke nam tai:

```text
notebooks/29_forecasting_v3_final_cleaned/00_pipeline_import_smoke_test.ipynb
```

Notebook audit truoc khi bat full train:

```text
notebooks/29_forecasting_v3_final_cleaned/05_training_audit_before_full_run.ipynb
```
