# Hướng dẫn chạy LightGBM GPU / mock test

File này ghi cách chạy riêng cho pipeline forecasting v3, tránh nhầm giữa mock test và train thật.

## 1. Kiểm tra GPU/OpenCL trên NixOS

Trên máy NixOS của anh, trước hết kiểm tra:

```bash
nvidia-smi
clinfo | head -80
```

Nếu `clinfo` thấy:

```text
Platform Name  NVIDIA CUDA
Device Name    NVIDIA GeForce RTX 3050 6GB Laptop GPU
```

thì OpenCL của NVIDIA đã hoạt động.

## 2. Biến môi trường cần cho LightGBM trên NixOS

LightGBM GPU OpenCL cần thấy thư mục ICD của NVIDIA: phan nay cho NixOS

```bash
export OCL_ICD_VENDORS=/nix/store/rfacrwa133a0xibh0qig0lrva3n51bhz-nvidia-x11-595.71.05/etc/OpenCL/vendors
```

Biến này chỉ ảnh hưởng process shell hiện tại. Không sửa kernel, không sửa driver, không ảnh hưởng boot.

## 3. Chạy mock GPU test an toàn

Mock chỉ để kiểm tra code train chạy được bằng LightGBM thật trên sample nhỏ. Không dùng metric mock để báo cáo.

```bash
cd ~/Desktop/refactor_code
source .venv/bin/activate

cp config/05_machine_learning/forecasting_v3_final_cleaned.yaml /tmp/forecasting_v3_mock_gpu.yaml
sed -i 's/mode: production_lightgbm/mode: mock_lightgbm/' /tmp/forecasting_v3_mock_gpu.yaml
sed -i 's/enabled: false/enabled: true/' /tmp/forecasting_v3_mock_gpu.yaml
sed -i 's/max_train_rows_per_horizon: 20000/max_train_rows_per_horizon: 1000/' /tmp/forecasting_v3_mock_gpu.yaml
sed -i 's/max_eval_rows_per_horizon: 20000/max_eval_rows_per_horizon: 1000/' /tmp/forecasting_v3_mock_gpu.yaml
sed -i 's/n_estimators: 25/n_estimators: 2/' /tmp/forecasting_v3_mock_gpu.yaml

export OCL_ICD_VENDORS=/nix/store/rfacrwa133a0xibh0qig0lrva3n51bhz-nvidia-x11-595.71.05/etc/OpenCL/vendors

python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py \
  --config /tmp/forecasting_v3_mock_gpu.yaml \
  --stage train_final \
  --run-id smoke_audit
```

GPU pass khi log có:

```text
Using GPU Device: NVIDIA GeForce RTX 3050 6GB Laptop GPU
GPU programs have been built
```

Nếu log có:

```text
lightgbm_cpu_after_gpu_retry
```

thì GPU chưa chạy được trong pipeline stage đó, nhưng code đã fallback CPU LightGBM an toàn.

## 4. Chạy production train thật

Chỉ bật khi muốn train thật, vì có thể nặng CPU/RAM/GPU:

```yaml
training:
  mode: production_lightgbm
  allow_full_train: true
  mock:
    enabled: false
```

Sau đó chạy:

```bash
cd ~/Desktop/refactor_code
source .venv/bin/activate

export OCL_ICD_VENDORS=/nix/store/rfacrwa133a0xibh0qig0lrva3n51bhz-nvidia-x11-595.71.05/etc/OpenCL/vendors

RUN_ID=train_$(date +%Y%m%d_%H%M%S)

python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py \
  --stage all \
  --run-id "$RUN_ID"
```

## 5. Windows team chạy thế nào

Windows không dùng `OCL_ICD_VENDORS`.

Chạy bình thường:

```powershell
python -u srcs/05_machine_learning/Forcasting_v3/14_run_forecasting_pipeline.py --stage train_final --run-id smoke_audit
```

Nếu Windows có LightGBM GPU/OpenCL đúng thì nó dùng GPU. Nếu không, code fallback CPU LightGBM theo config.

## 6. Trạng thái đã kiểm chứng

Đã kiểm chứng trên máy anh:

```text
GPU/OpenCL system             OK
LightGBM GPU synthetic sample OK
LightGBM GPU pipeline matrix  OK với sample nhỏ 200 dòng, 35 feature
Pipeline CPU fallback         OK
```

Chưa được xem là pass production GPU full pipeline cho tới khi `train_final` log rõ `Using GPU Device` trong chính stage pipeline.
