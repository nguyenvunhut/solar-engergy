# Ghi chú trục thời gian - prediction_audit_h1.csv / prediction_audit_h4.csv

Model dự báo tại thời điểm `timestamp` (input) cho sản lượng ở một thời điểm **sau đó**
(h1 = sau 15 phút, h4 = sau 60 phút). File có nhiều cột "thời gian" vì mỗi cột phục vụ
1 mục đích khác nhau - **dùng nhầm cột sẽ làm biểu đồ actual/predicted lệch pha giả**.

## Cột nào dùng làm trục X khi vẽ Tableau

**BẮT BUỘC dùng `plot_timestamp_h1` (hoặc `plot_timestamp_h4`) làm trục thời gian khi vẽ.**
Đây là cột duy nhất mà `y_true` và `y_pred` cùng mô tả đúng 1 mốc thời gian thực tế
(thời điểm sản lượng thật sự xảy ra). Vẽ 2 đường `y_true` vs `y_pred` theo trục nào khác
`plot_timestamp` đều SAI - kết quả so sánh sẽ lệch pha giả, không phản ánh đúng độ chính xác model.

**Không dùng `timestamp`** làm trục X để so `y_true` với `y_pred` - `timestamp` là thời
điểm input (feature), không phải thời điểm của sản lượng đang được dự báo. Dùng cột này
làm trục X sẽ khiến `y_pred` (dự báo cho tương lai) bị vẽ lùi về đúng lúc input, tạo cảm
giác model "trễ pha" giả dù model không hề trễ.

## Giải thích từng cột thời gian

| Cột | Ý nghĩa |
|---|---|
| `timestamp` | Thời điểm **input** - lúc model nhận feature để dự báo |
| `target_timestamp` | Thời điểm **mục tiêu thật** cần dự báo (`timestamp` + 15p cho h1, + 60p cho h4) |
| `source_timestamp` | Alias của `timestamp`, giữ lại để đối chiếu |
| `label_timestamp` | Thời điểm dùng để gán nhãn actual khi so khớp actual vs predict |
| `plot_timestamp` | **BẮT BUỘC dùng cột này để vẽ** - bằng `target_timestamp`, là mốc mà `y_true`/`y_pred` cùng mô tả |

## Các cột giá trị

- `y_true_h1` / `y_true_h4`: sản lượng thực tế (kWh) tại `plot_timestamp`
- `y_pred_h1` / `y_pred_h4`: sản lượng model dự báo (kWh) cho đúng mốc `plot_timestamp` đó
- `residual_h1` / `residual_h4` = `y_true - y_pred`
- `site_id`: mã trạm (1-42)
- `energy_source`: nguồn gốc dữ liệu target thật (`measured` = đo thực tế, các nhãn khác là suy diễn/impute - nên lọc `energy_source == "measured"` khi cần số liệu "sạch")
- `is_daylight`: true/false, có phải giờ ban ngày (dựa góc cao mặt trời) - lọc `is_daylight == True` khi phân tích hiệu năng ban ngày (ban đêm sản lượng luôn = 0, không có ý nghĩa đánh giá)

## Tóm tắt nhanh cho người vẽ Tableau

- Trục X: `plot_timestamp_h1` (file h1) hoặc `plot_timestamp_h4` (file h4)
- 2 đường Y: `y_true_h1` vs `y_pred_h1` (tương tự cho h4)
- Lọc theo `site_id` nếu xem từng trạm
- Muốn số liệu "chính thức" (khớp báo cáo): lọc thêm `energy_source == "measured"` và `is_daylight == True`
