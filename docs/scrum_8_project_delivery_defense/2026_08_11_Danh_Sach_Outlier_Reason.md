# Danh sách `outlier_reason` của pipeline GMM-IF

Tài liệu này ghi đúng các mã lý do được sinh bởi hàm
`explain_outlier_row()` trong:

`srcs/02_transform/02_generate_outliers/02_gmm_if.py`

Các mã được lưu vào cột `gmm_if_outlier_reason` khi export cờ outlier. Một
dòng có thể đồng thời vi phạm nhiều điều kiện; khi đó các mã được nối bằng
dấu `+`.

## Các reason hiện tại

| Mã reason | Định nghĩa trong pipeline | Ý nghĩa nghiệp vụ |
|---|---|---|
| `GMM_IF_CONSENSUS` | GMM đánh dấu dòng là bất thường trong segment tương ứng **và** Isolation Forest cũng đánh dấu chính dòng đó. Đây là phép giao `GMM AND IF`. | Quan sát có hình thái bất thường đồng thời ở phân bố cục bộ và không gian đặc trưng toàn cục; cần kiểm tra lại cảm biến hoặc trạng thái vận hành. |
| `PHYSICAL_OVER_CAPACITY` | Năng lượng phát trong một bước 15 phút vượt `capacity_kw * 0.25`. Cấu hình hiện tại dùng `gmm_if_over_capacity_tolerance = 1.0`. | Giá trị vượt trần công suất định mức của site; có thể là lỗi cảm biến, lỗi metadata hoặc hiện tượng phát bất thường, không được mặc định coi là lỗi thiết bị. |
| `PHYSICAL_HIGH_ENERGY_NO_SUN` | `shortwave_radiation <= 25`, `sunshine_duration <= 60`, đồng thời năng lượng phát `>= max(1.0, 0.20 * capacity_reference_kw)`. | Sản lượng cao trong điều kiện gần như không có bức xạ và thời lượng nắng; mâu thuẫn vật lý cần được kiểm tra. |
| `PHYSICAL_HIGH_ENERGY_LOW_RADIATION` | `shortwave_radiation <= 50`, năng lượng phát đạt ít nhất `max(1.0, 0.20 * capacity_reference_kw)`, và đồng thời vượt `Q3 + 4 * safe_IQR` trong nhóm bức xạ tương ứng. | Sản lượng cao bất thường khi bức xạ thấp; mạnh hơn một dao động thông thường vì vừa vi phạm điều kiện vật lý vừa nằm ở đuôi phân bố. |
| `PHYSICAL_LOW_ENERGY_STRONG_SUN` | `shortwave_radiation >= 700`, `sunshine_duration >= 3000`, mức năng lượng kỳ vọng cao, nhưng năng lượng thực tế `<= 0.05 * site_p95` và `<= Q1 - 2 * safe_IQR`. | Sản lượng gần như mất trong điều kiện nắng mạnh; có thể gợi ý mất phát, lỗi đo, suy giảm vận hành hoặc vấn đề inverter/panel cần kiểm tra. Đây là cờ cảnh báo, không phải kết luận nguyên nhân. |
| `PHYSICAL_DISTRIBUTION_JUMP` | Không áp dụng tại các giờ chuyển tiếp `05`, `06`, `18`. Giá trị năng lượng nằm ngoài `Q3 + 4 * safe_IQR` hoặc `Q1 - 4 * safe_IQR`, đồng thời độ lệch so với các điểm lân cận thỏa `abs(neighbor_delta) >= max(0.15 * site_p95, 1.0)`. | Một bước nhảy hoặc tụt cục bộ lớn so với phân bố của nhóm tương ứng và diễn biến khoảng hai giờ xung quanh; có thể là spike, dropout hoặc lỗi truyền dữ liệu. |

## Cách đọc reason kết hợp

Ví dụ:

```text
GMM_IF_CONSENSUS+PHYSICAL_DISTRIBUTION_JUMP
```

Nghĩa là cùng một dòng vừa được GMM và Isolation Forest đồng thuận đánh dấu,
vừa vi phạm quy tắc bước nhảy phân bố vật lý. Không được tách chuỗi này thành
một loại outlier mới; đây là hai reason cùng xuất hiện trên một quan sát.

## Quy tắc tạo reason cuối

```text
gmm_if_consensus_flag = gmm_flag AND if_flag
is_outlier = gmm_if_consensus_flag OR physical_rule_flag
```

Trong đó `physical_rule_flag` là phép OR của năm reason vật lý:

```text
PHYSICAL_OVER_CAPACITY
PHYSICAL_HIGH_ENERGY_NO_SUN
PHYSICAL_HIGH_ENERGY_LOW_RADIATION
PHYSICAL_LOW_ENERGY_STRONG_SUN
PHYSICAL_DISTRIBUTION_JUMP
```

## Nhãn không dùng làm reason của pipeline mới

- `FINAL_FLAG` chỉ là giá trị dự phòng của hàm giải thích khi một dòng được
  in trong log nhưng không có cờ reason chi tiết. Không xem đây là một loại
  outlier nghiệp vụ.
- `UNKNOWN` chỉ là giá trị dự phòng của bước export nếu file ứng viên không
  có cột reason. Nó không phải reason do detector sinh ra.
- `zero_generation_daylight`, `stuck_sensor` và `iqr_rolling` không được hàm
  hiện tại sinh ra trong pipeline GMM-IF mới, nên không đưa vào danh sách
  reason này.

## Nguồn đối chiếu

- Sinh reason: `srcs/02_transform/02_generate_outliers/02_gmm_if.py`, hàm
  `explain_outlier_row()`.
- Ngưỡng thuật toán: `config/02_transform/01_generate_outliers.yaml`.
- Đổi tên `outlier_reason` thành cột lưu trữ
  `gmm_if_outlier_reason`: `srcs/02_transform/02_generate_outliers/03_export_csv.py`.
