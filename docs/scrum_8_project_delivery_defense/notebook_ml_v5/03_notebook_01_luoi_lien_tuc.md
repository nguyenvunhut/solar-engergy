# Notebook 01 — Dựng lưới 15 phút và gắn nhãn nguồn gốc (chi tiết đầy đủ)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy trước. Giá trị hiện
> hành và lý do từng con số thay đổi: [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md).


> Notebook này quyết định **dòng nào là sự thật, dòng nào là suy đoán**. Toàn bộ tính trung
> thực của các con số trong báo cáo đứng trên cột `energy_source` sinh ra ở đây.

- **Vào:** `data/mlmart_base/v5_final_cleaned.parquet` + `data/raw/Solar_Energy_Generation.csv`
- **Ra:** `data/model/v5/01_reindex/v5_continuous_grid.parquet`

---

## 1. Vì sao phải dựng lưới

Dữ liệu gốc **không đều**: mất điện, rớt mạng, đồng hồ hỏng → có lúc thiếu hẳn vài mốc, có
lúc thiếu cả ngày. Nhưng đặc trưng trễ và trượt (`lag_96` = 24 giờ trước, `rolling_96`) giả
định lưới **đều tuyệt đối**: mỗi trạm đúng một dòng mỗi 15 phút.

Nếu không dựng lưới, `lag_96` sẽ không phải "24 giờ trước" mà là "96 dòng trước" — hai thứ
khác nhau khi có lỗ hổng. Đây là loại lỗi âm thầm, không báo lỗi, chỉ làm mô hình sai.

```python
FREQ_MINUTES    = 15
MAJOR_GAP_HOURS = 24
MAX_LAG_STEPS   = 672      # 7 ngày × 96 mốc
```

---

## 2. Cách dựng lưới

Với **từng trạm**: lấy mốc đầu và mốc cuối → sinh dãy đều 15 phút → ghép dữ liệu thật vào.
Mốc nào không có dữ liệu thì thành dòng mới, đánh dấu `timestamp_was_inserted = True`.

Kiểm tra đúng: `(mốc cuối − mốc đầu) / 15 phút + 1` phải bằng đúng số dòng của trạm đó.

---

## 3. Cột `energy_source` — phần quan trọng nhất

Sau khi chèn dòng, phải điền giá trị. Nhưng **phải ghi lại đã điền bằng cách nào**, vì không
được phép chấm điểm mô hình trên số do chính mình bịa ra.

### 3.1. Bậc thang điền (cascade), theo thứ tự ưu tiên

| Bậc | Nhãn | Điều kiện | Giá trị điền |
|---|---|---|---|
| 0 | `measured` | Có trong file CSV gốc | Giữ nguyên số đo |
| 1 | `night_zero` | Ban đêm | 0 |
| 2 | `causal_day_persistence` | Ban ngày, có dữ liệu **hôm qua** cùng giờ | Giá trị hôm qua |
| 3 | `causal_week_persistence` | Ban ngày, có dữ liệu **tuần trước** cùng giờ | Giá trị tuần trước |
| 4 | `causal_profile_median` | Ban ngày, có hồ sơ ngày điển hình | Trung vị hồ sơ |
| 5 | `fallback_zero` | Không suy được gì | 0 |
| — | `machine_failure_zero` | Máy hỏng (ETL đánh dấu) | 0 |
| — | `etl_imputed` | Tầng ETL đã điền từ trước | Giữ giá trị ETL |

### 3.2. Chữ "causal" nghĩa là gì

Chỉ dùng dữ liệu **quá khứ**. Không được lấy giá trị ngày mai để điền vào hôm nay — dù về
mặt kỹ thuật rất dễ làm (nội suy hai phía cho kết quả "đẹp" hơn).

Vì sao cấm: nếu điền bằng dữ liệu tương lai, dòng đó mang thông tin tương lai. Nó bị loại
khỏi chấm điểm (w=0), **nhưng vẫn tham gia làm lịch sử** cho `lag_96` và `rolling_96` của các
dòng khác → thông tin tương lai rò rỉ gián tiếp vào đặc trưng.

### 3.3. Vì sao phải đối chiếu với file CSV gốc

Chỉ có file gốc Kaggle mới biết dòng nào là số đo thật. Sau khi qua tầng ETL, mọi dòng đều
"có giá trị" và nhìn giống hệt nhau. Notebook đọc CSV gốc và ghép theo `(site_id, timestamp)`
để xác định `measured`.

Số thực tế: **1.195.645 dòng đo thật** trên tổng 2.731.946 dòng (43,8%).

---

## 4. Kiểm tra ghép thời tiết đúng nhân quả

Thời tiết mua theo **giờ**, sản lượng đo theo **15 phút**. Ghép sao cho không lấy thời tiết
của tương lai.

```python
LOOKUP_KEY = ("site_id", "_weather_hour")
```

Mỗi mốc sản lượng lấy thời tiết của **giờ chứa nó** (giờ đã bắt đầu, tức quá khứ). Notebook
có cell kiểm chứng: so `weather_timestamp` với `timestamp`.

**Kết quả đo trên bản trích 20/08:** lệch 0–45 phút, trung vị 30 phút, **0 dòng (0,000%)**
dùng thời tiết tương lai. Nhãn ghép: `raw_hour_causal_join` cho 2.731.728/2.731.946 dòng.

*(Lịch sử: bản v3 từng có lỗi này — 71,9% dòng dùng thời tiết tương lai, phải làm hotfix
riêng. Đó là lý do bước kiểm chứng này tồn tại.)*

---

## 5. Mặt nạ lịch sử `has_complete_history_features`

```python
MAX_LAG_STEPS = 672        # 7 ngày
MAJOR_GAP_HOURS = 24
```

Dòng nào chưa đủ 672 bước lịch sử liền trước thì `lag_96`, `rolling_96` không tính đủ →
đánh dấu để notebook 06 loại khỏi huấn luyện.

`MAJOR_GAP_HOURS = 24`: nếu có đứt quãng trên 24 giờ, dữ liệu hai bên **không được nối liền
mạch** — coi như hai đoạn riêng. Nếu nối, `lag_96` của dòng đầu đoạn sau sẽ lấy nhầm giá trị
từ trước lỗ hổng.

---

## 6. Mask outlier

Cờ outlier từ tầng ETL (`gmm_if_outlier_flag`, `gmm_if_outlier_reason`) được chuyển thành cột
`outlier_group` gọn hơn để notebook 06 dùng khi tính trọng số:

```
normal · gmm_if_consensus · physical_over_capacity · other_physical_rule · multiple_rules
```

**Lưu ý bản trích 20/08:** tầng ETL đổi cách xử lý — thay vì *gắn cờ* dòng vượt trần, giờ nó
*kẹp giá trị* về 1,20× trần metadata. Hệ quả: `PHYSICAL_OVER_CAPACITY` từ 26.318 dòng xuống
**0 dòng**, và 20.468 dòng **đo thật** bị ghi đè giá trị. Đây là lý do notebook 06 vẫn loại
cứng trạm 19 và 24.

---

## 7. Bộ câu hỏi phòng thủ

| Câu hỏi | Trả lời |
|---|---|
| Chèn thêm dòng có phải là bịa dữ liệu? | Có chèn, nhưng **ghi rõ nguồn gốc** từng dòng và **loại chúng khỏi chấm điểm**. Chỉ dòng `measured` được tính điểm |
| Vì sao phải chèn thay vì bỏ qua? | Vì đặc trưng trễ/trượt cần lưới đều; bỏ trống thì `lag_96` không còn là "24 giờ trước" |
| Làm sao biết dòng nào là số đo thật? | Đối chiếu từng dòng với file CSV gốc Kaggle theo `(trạm, mốc thời gian)` |
| Ghép thời tiết có bị nhìn tương lai? | Đã kiểm: 0,000% dòng vi phạm; nhãn ghép `raw_hour_causal_join` |
| Dòng điền có ảnh hưởng mô hình không? | Không vào hàm mục tiêu (w=0) và không vào tập chấm; nhưng **có** góp vào lịch sử của lag/rolling — đây là hạn chế được ghi nhận |
