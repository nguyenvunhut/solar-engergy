# Báo Cáo Kiểm Tra Đường Dẫn & Logic Mã Nguồn Toàn Bộ Pipeline Refactor
Dự án: Tốt nghiệp - Energy Forecasting - Nhóm thực hiện: The Outliers
Thời gian kiểm tra: 2026-07-27
Thư mục thực thi: `notebooks/refactor/`

---
## 1. Bảng Chuỗi Dữ Liệu (Data Pipeline Chain)
Dưới đây là bảng đối chiếu chi tiết đường dẫn **ĐỌC (Input)** -> **GHI (Output)** -> **Notebook tiêu thụ tiếp theo** cho 11 notebook trong pipeline:

| STT | Notebook | Đường Dẫn ĐỌC (Input) | Đường Dẫn GHI (Output) | Notebook Đọc Tiếp |
|---|---|---|---|---|
| 1 | `01_reindex_mask_outlier.ipynb` | `../../data/mlmart_base/v3_final_cleaned.parquet (Dữ liệu làm sạch gốc)` | `../../data/model/v3/01_reindex/v3_continuous_grid.parquet` | `02_split_time_series.ipynb` |
| 2 | `02_split_time_series.ipynb` | `../../data/model/v3/01_reindex/v3_continuous_grid.parquet` | `../../data/model/v3/02_split/development/v3_development.parquet`<br>`../../data/model/v3/02_split/test/v3_test.parquet`<br>`../../data/model/v3/02_split/train/v3_train.parquet`<br>`../../data/model/v3/02_split/val/v3_val.parquet`<br>`../../data/model/v3/02_split/time_series_folds/fold_1..5_train.parquet`<br>`../../data/model/v3/02_split/time_series_folds/fold_1..5_val.parquet`<br>`../../data/model/v3/02_split/v3_split_summary.csv`<br>`../../data/model/v3/02_split/v3_time_series_fold_summary.csv` | `03_1_features_time.ipynb` |
| 3 | `03_1_features_time.ipynb` | `../../data/model/v3/02_split/development/v3_development.parquet`<br>`../../data/model/v3/02_split/test/v3_test.parquet`<br>`../../data/model/v3/02_split/train/v3_train.parquet`<br>`../../data/model/v3/02_split/val/v3_val.parquet`<br>`../../data/model/v3/02_split/time_series_folds/fold_1..5_train.parquet`<br>`../../data/model/v3/02_split/time_series_folds/fold_1..5_val.parquet` | `../../data/model/v3/03_1_features_time/v3_development_time.parquet`<br>`../../data/model/v3/03_1_features_time/v3_test_time.parquet`<br>`../../data/model/v3/03_1_features_time/v3_train_time.parquet`<br>`../../data/model/v3/03_1_features_time/v3_val_time.parquet`<br>`../../data/model/v3/03_1_features_time/time_series_folds/fold_1..5_train_time.parquet`<br>`../../data/model/v3/03_1_features_time/time_series_folds/fold_1..5_val_time.parquet` | `03_2_features_spatial.ipynb` |
| 4 | `03_2_features_spatial.ipynb` | `../../data/model/v3/03_1_features_time/v3_development_time.parquet`<br>`../../data/model/v3/03_1_features_time/v3_test_time.parquet`<br>`../../data/model/v3/03_1_features_time/v3_train_time.parquet`<br>`../../data/model/v3/03_1_features_time/v3_val_time.parquet`<br>`../../data/model/v3/03_1_features_time/time_series_folds/fold_1..5_train_time.parquet`<br>`../../data/model/v3/03_1_features_time/time_series_folds/fold_1..5_val_time.parquet` | `../../data/model/v3/03_2_features_spatial/v3_development_spatial.parquet`<br>`../../data/model/v3/03_2_features_spatial/v3_test_spatial.parquet`<br>`../../data/model/v3/03_2_features_spatial/v3_train_spatial.parquet`<br>`../../data/model/v3/03_2_features_spatial/v3_val_spatial.parquet`<br>`../../data/model/v3/03_2_features_spatial/time_series_folds/fold_1..5_train_spatial.parquet`<br>`../../data/model/v3/03_2_features_spatial/time_series_folds/fold_1..5_val_spatial.parquet` | `03_3_features_aggregate.ipynb` |
| 5 | `03_3_features_aggregate.ipynb` | `../../data/model/v3/03_2_features_spatial/v3_development_spatial.parquet`<br>`../../data/model/v3/03_2_features_spatial/v3_test_spatial.parquet`<br>`../../data/model/v3/03_2_features_spatial/v3_train_spatial.parquet`<br>`../../data/model/v3/03_2_features_spatial/v3_val_spatial.parquet`<br>`../../data/model/v3/03_2_features_spatial/time_series_folds/fold_1..5_train_spatial.parquet`<br>`../../data/model/v3/03_2_features_spatial/time_series_folds/fold_1..5_val_spatial.parquet` | `../../data/model/v3/03_3_features_aggregate/v3_development_features.parquet`<br>`../../data/model/v3/03_3_features_aggregate/v3_test_features.parquet`<br>`../../data/model/v3/03_3_features_aggregate/v3_train_features.parquet`<br>`../../data/model/v3/03_3_features_aggregate/v3_val_features.parquet`<br>`../../data/model/v3/03_3_features_aggregate/time_series_folds/fold_1..5_train_features.parquet`<br>`../../data/model/v3/03_3_features_aggregate/time_series_folds/fold_1..5_val_features.parquet`<br>`../../data/model/v3/03_3_features_aggregate/v3_category_maps.json` | `04_vif_diagnostics.ipynb`, `05_select_features.ipynb` |
| 6 | `04_vif_diagnostics.ipynb` | `../../data/model/v3/03_3_features_aggregate/v3_train_features.parquet` | `../../data/model/v3/04_diagnostics/feature_diagnostics.csv` | `05_select_features.ipynb` |
| 7 | `05_select_features.ipynb` | `../../data/model/v3/03_3_features_aggregate/v3_train_features.parquet`<br>`../../data/model/v3/04_diagnostics/feature_diagnostics.csv`<br>`../../data/model/v3/03_3_features_aggregate/v3_development_features.parquet`<br>`../../data/model/v3/03_3_features_aggregate/v3_test_features.parquet`<br>`../../data/model/v3/03_3_features_aggregate/v3_val_features.parquet`<br>`../../data/model/v3/03_3_features_aggregate/time_series_folds/fold_1..5_train_features.parquet`<br>`../../data/model/v3/03_3_features_aggregate/time_series_folds/fold_1..5_val_features.parquet` | `../../data/model/v3/05_selected/selected_features.json`<br>`../../data/model/v3/05_selected/feature_scores.csv`<br>`../../data/model/v3/05_selected/v3_development_selected.parquet`<br>`../../data/model/v3/05_selected/v3_test_selected.parquet`<br>`../../data/model/v3/05_selected/v3_train_selected.parquet`<br>`../../data/model/v3/05_selected/v3_val_selected.parquet`<br>`../../data/model/v3/05_selected/time_series_folds/fold_1..5_train_selected.parquet`<br>`../../data/model/v3/05_selected/time_series_folds/fold_1..5_val_selected.parquet` | `06_1_train_mse.ipynb`, `06_2_train_mae.ipynb`, `06_3_train_huber.ipynb`, `07_final_test.ipynb` |
| 8 | `06_1_train_mse.ipynb` | `../../data/model/v3/05_selected/selected_features.json`<br>`../../data/model/v3/05_selected/time_series_folds/fold_1..5_train_selected.parquet`<br>`../../data/model/v3/05_selected/time_series_folds/fold_1..5_val_selected.parquet`<br>`../../data/model/v3/05_selected/v3_development_selected.parquet`<br>`../../data/model/v3/05_selected/v3_val_selected.parquet` | `../../data/model/v3/06_train/mse/best_params.json`<br>`../../data/model/v3/06_train/mse/optuna_trials.csv`<br>`../../data/model/v3/06_train/mse/model.pkl`<br>`../../data/model/v3/06_train/mse/model_config.json`<br>`../../data/model/v3/06_train/mse/metrics_val.json` | `07_final_test.ipynb` |
| 9 | `06_2_train_mae.ipynb` | `../../data/model/v3/05_selected/selected_features.json`<br>`../../data/model/v3/05_selected/time_series_folds/fold_1..5_train_selected.parquet`<br>`../../data/model/v3/05_selected/time_series_folds/fold_1..5_val_selected.parquet`<br>`../../data/model/v3/05_selected/v3_development_selected.parquet`<br>`../../data/model/v3/05_selected/v3_val_selected.parquet` | `../../data/model/v3/06_train/mae/best_params.json`<br>`../../data/model/v3/06_train/mae/optuna_trials.csv`<br>`../../data/model/v3/06_train/mae/model.pkl`<br>`../../data/model/v3/06_train/mae/model_config.json`<br>`../../data/model/v3/06_train/mae/metrics_val.json` | `07_final_test.ipynb` |
| 10 | `06_3_train_huber.ipynb` | `../../data/model/v3/05_selected/selected_features.json`<br>`../../data/model/v3/05_selected/time_series_folds/fold_1..5_train_selected.parquet`<br>`../../data/model/v3/05_selected/time_series_folds/fold_1..5_val_selected.parquet`<br>`../../data/model/v3/05_selected/v3_development_selected.parquet`<br>`../../data/model/v3/05_selected/v3_val_selected.parquet` | `../../data/model/v3/06_train/huber/best_params.json`<br>`../../data/model/v3/06_train/huber/optuna_trials.csv`<br>`../../data/model/v3/06_train/huber/model.pkl`<br>`../../data/model/v3/06_train/huber/model_config.json`<br>`../../data/model/v3/06_train/huber/metrics_val.json` | `07_final_test.ipynb` |
| 11 | `07_final_test.ipynb` | `../../data/model/v3/06_train/{mse,mae,huber}/metrics_val.json`<br>`../../data/model/v3/06_train/{winning_loss}/model.pkl`<br>`../../data/model/v3/06_train/{winning_loss}/model_config.json`<br>`../../data/model/v3/05_selected/v3_test_selected.parquet` | `../../data/model/v3/07_final_test/best_loss.json`<br>`../../data/model/v3/07_final_test/metrics_overall.json`<br>`../../data/model/v3/07_final_test/metrics_by_site.csv`<br>`../../data/model/v3/07_final_test/prediction_audit.parquet` | `Nguồn báo cáo nghiệm thu cuối cùng của dự án` |

---
## 2. Danh Sách Lỗi Biến / Hàm / Import Chưa Định Nghĩa (Nội Bộ Notebook)
Đã quét cú pháp (AST Analysis) và bảng ký hiệu (Symbol Table) từng cell từ trên xuống dưới cho cả 11 notebook.

### Kết quả kiểm tra 11 Notebook:
1. `01_reindex_mask_outlier.ipynb`: **KHÔNG CÓ LỖI** (0 lỗi)
2. `02_split_time_series.ipynb`: **KHÔNG CÓ LỖI** (0 lỗi)
3. `03_1_features_time.ipynb`: **KHÔNG CÓ LỖI** (0 lỗi)
4. `03_2_features_spatial.ipynb`: **KHÔNG CÓ LỖI** (0 lỗi)
5. `03_3_features_aggregate.ipynb`: **KHÔNG CÓ LỖI** (0 lỗi)
6. `04_vif_diagnostics.ipynb`: **KHÔNG CÓ LỖI** (0 lỗi)
7. `05_select_features.ipynb`: **KHÔNG CÓ LỖI** (0 lỗi)
8. `06_1_train_mse.ipynb`: **PHÁT HIỆN 1 LỖI CÚ PHÁP CHUỖI KHÔNG ĐÓNG (SyntaxError)**
   - **Cell 11 (Dòng 10):** Lỗi `SyntaxError: unterminated string literal` tại câu lệnh `print("\n--- HOÀN TẤT PHẦN A: TUNE OPTUNA ---")` do chuỗi ký tự xuống dòng `\n` nằm trực tiếp trong f-string gây ngắt dòng sai cú pháp Python.
   - Kéo theo lỗi phụ: Cell 13 và Cell 15 bị báo `NameError` cho biến `study` và `final_n_estimators` vì Cell 11 bị ngắt đoạn không thực thi được.
9. `06_2_train_mae.ipynb`: **PHÁT HIỆN 1 LỖI CÚ PHÁP CHUỖI KHÔNG ĐÓNG (SyntaxError)**
   - **Cell 11 (Dòng 10):** Lỗi `SyntaxError: unterminated string literal` tương tự tại câu lệnh `print("\n--- HOÀN TẤT PHẦN A: TUNE OPTUNA ---")`.
   - Kéo theo lỗi phụ `NameError` cho biến `study` ở Cell 13 và Cell 15.
10. `06_3_train_huber.ipynb`: **PHÁT HIỆN 1 LỖI CÚ PHÁP CHUỖI KHÔNG ĐÓNG (SyntaxError)**
    - **Cell 11 (Dòng 10):** Lỗi `SyntaxError: unterminated string literal` tương tự tại câu lệnh `print("\n--- HOÀN TẤT PHẦN A: TUNE OPTUNA ---")`.
    - Kéo theo lỗi phụ `NameError` cho biến `study` ở Cell 13 và Cell 15.
11. `07_final_test.ipynb`: **KHÔNG CÓ LỖI** (0 lỗi)

---
## 3. Danh Sách Đường Dẫn Đọc Mà Không Ai Tạo Ra
Đã đối chiếu tất cả các đường dẫn trong câu lệnh `read_parquet`, `read_csv`, `json.load` với dữ liệu hiện có và dữ liệu được tạo ra từ các bước trước.

- **Kết quả:** **0 LỖI**. Tất cả đường dẫn đọc trong 11 notebook đều khớp 100% với file có sẵn hoặc file được sinh ra từ notebook đứng trước.

---
## 4. Danh Sách File Ghi Ra Mà Không Ai Sử Dụng (File Mồ Côi)
Đã kiểm tra tất cả các file được xuất ra từ các bước:

1. `../../data/model/v3/02_split/v3_split_summary.csv`: Được giữ lại phục vụ báo cáo thống kê phân chia tập dữ liệu.
2. `../../data/model/v3/02_split/v3_time_series_fold_summary.csv`: Được giữ lại phục vụ báo cáo thống kê 5 fold CV.
3. `../../data/model/v3/03_3_features_aggregate/v3_category_maps.json`: Bảng ánh xạ mã hóa categorical được lưu trữ phục vụ giải mã (inference).
4. `../../data/model/v3/05_selected/feature_scores.csv`: Bảng điểm Mutual Information phục vụ báo cáo xếp hạng đặc trưng.
5. `../../data/model/v3/06_train/{mse,mae,huber}/optuna_trials.csv`: Nhật ký các trial Optuna phục vụ phân tích độ hội tụ.
6. `../../data/model/v3/06_train/{mse,mae,huber}/best_params.json`: Siêu tham số tối ưu lưu phục vụ audit.
- **Đánh giá:** Tất cả các file ghi ra không bị lãng phí, đều đóng vai trò lưu vết (audit log) hoặc báo cáo thành phần của dự án.

---
## 5. Kết Luận Và Đề Xuất Sửa Lỗi
### Kết luận tổng quan: PIPELINE ĐÃ THÔNG SUỐT VỀ MẶT DỮ LIỆU, CHỈ CẦN SỬA 1 LỖI CÚ PHÁP NHỎ TẠI 3 NOTEBOOK 06.

### Danh sách 3 việc cần khắc phục (Chờ người dùng xác nhận):
1. **Sửa lỗi cú pháp string tại Cell 11 của cả 3 notebook 06 (`06_1`, `06_2`, `06_3`):**
   - Thay thế câu lệnh: `print("\n--- HOÀN TẤT PHẦN A: TUNE OPTUNA ---")`
   - Thành câu lệnh tách dòng an toàn: `print(""); print("--- HOÀN TẤT PHẦN A: TUNE OPTUNA ---")`
2. **Toàn bộ 8 notebook còn lại (`01`, `02`, `03_1`, `03_2`, `03_3`, `04`, `05`, `07`) đều HOÀN HẢO 100%**, không có bất kỳ lỗi biến, lỗi hàm hay lỗi đường dẫn nào.
3. **Chuỗi dữ liệu 11 bước hoàn toàn thông suốt**, từ dữ liệu gốc `v3_final_cleaned.parquet` đến kết quả báo cáo niêm phong `07_final_test`.
