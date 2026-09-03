# Notebook 00 — Điền khuyết (00_fill_null_imputation.ipynb)

> **Về các con số trong file này:** một số giá trị mô tả lượt chạy trước. Giá trị hiện
> hành và lý do từng con số thay đổi: [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md).


> Người đọc mục tiêu: chưa từng làm ML. Đọc `00_DOC_TRUOC_TIEN.md` trước.

---

## 1. Notebook này giải quyết vấn đề gì

Dữ liệu kéo từ kho (ML Mart) về có nhiều **ô trống (null)** — chỗ thì do cảm biến không ghi,
chỗ thì do trạm không khai báo thông tin. Ô trống là "mìn" cho các bước sau: một phép nhân
với ô trống cho ra ô trống, một biểu đồ gặp ô trống thì đứt đoạn, một thống kê gặp ô trống
thì âm thầm bỏ qua dòng đó — mỗi công cụ xử lý một kiểu, không kiểm soát được.

Notebook 00 xử lý toàn bộ ô trống **một lần, tại một chỗ, có ghi chép** — để mọi bước sau
được nhận một bảng dữ liệu mà trạng thái từng cột đã được quyết định rõ ràng.

- **File vào:** `data/mlmart_base/v5_preprocessing.parquet` — 2.731.946 dòng × 47 cột
- **File ra:** `data/mlmart_base/v5_final_cleaned.parquet` — y nguyên số dòng, số cột

Điểm cần hiểu ngay: "xử lý ô trống" **không có nghĩa là điền hết**. Có cột điền được, có cột
**cấm điền**. Quyết định điền/không điền cho từng cột chính là nội dung của notebook này.

---

## 2. Đầu vào có bao nhiêu ô trống, ở đâu

Cell đầu tiên chụp lại "ảnh hiện trạng" trước khi đụng vào bất cứ thứ gì (bản trích 20/08):

| Cột | Số ô trống | Vì sao trống |
|---|---|---|
| `gmm_if_outlier_reason` | 2.724.515 | Chỉ dòng bị gắn cờ bất thường mới có lý do → dòng bình thường trống là ĐÚNG |
| `optimizers` | 1.259.007 | Nhiều trạm không lắp bộ tối ưu |
| `capacity_kw` | 1.132.078 | **17/42 trạm không khai báo công suất** |
| `number_of_panels` | 1.132.078 | Trống cùng đúng những dòng của capacity |
| `panel`, `inverter`, `site_metric` | 1.132.078 | Cùng nhóm 17 trạm thiếu metadata |
| Nhóm thời tiết (bức xạ, nhiệt độ, mây, gió…) | 218 mỗi cột | 218 mốc không ghép được thời tiết |

Ảnh hiện trạng này được dùng lại ở notebook 00b để **đối chiếu trước/sau** — không tin lời
notebook 00 tự nói, mà kiểm bằng số.

*(Ghi chú bản 20/08: ở bản trích cũ 16/08, `cloud_cover_low` trống 846.973 ô và `wind_speed`
trống 217.946 ô. Bản mới chỉ còn 218 — tức tầng ETL phía trên đã điền trước khi dữ liệu
tới tay nhánh ML. Phần việc của notebook 00 với hai cột đó giờ chỉ còn 218 ô cuối.)*

---

## 3. Từng nhóm cột được xử lý thế nào, và VÌ SAO

### 3.1. Nhóm bức xạ ban đêm → điền 0 (sự thật vật lý, không phải ước lượng)

Ban đêm không có mặt trời → bức xạ bằng 0. Đây không phải "đoán giá trị bị thiếu" mà là
**điền một sự thật vật lý**. Không có rủi ro sai.

### 3.2. Nhóm thời tiết liên tục → nối tiếp CÓ GIỚI HẠN, rồi mới đến thống kê

Lấy `temperature_c` làm ví dụ. Chiến lược 3 tầng:

1. **Nối tiếp giá trị gần nhất (forward fill), tối đa 12 bước = 3 giờ.** Nhiệt độ là đại
   lượng biến thiên chậm — nếu 14h00 đo được 25°C và 14h15 mất tín hiệu, thì 25°C vẫn là
   ước lượng tốt. Nhưng chỉ trong giới hạn: kéo dài mãi thì 3h chiều "mượn" nhiệt độ của
   9h sáng — vô nghĩa. Con số 12 bước là ranh giới đó.
2. **Hết hạn nối tiếp → trung vị theo (trạm, giờ).** Ví dụ ô trống lúc 9h sáng ở trạm 27 →
   lấy trung vị mọi giá trị 9h sáng của trạm 27 trong lịch sử. Tôn trọng đặc điểm khí hậu
   riêng từng trạm và nhịp ngày.
3. **Vẫn không có → trung vị toàn cục.** Lưới an toàn cuối cùng, hầu như không bao giờ dùng tới.

Các cột khác cùng họ nhưng giới hạn ngắn hơn vì bản chất biến thiên nhanh hơn:
`wind_speed` tối đa 4 bước (1 giờ), `cloud_cover_*` tối đa 8 bước (2 giờ).

**Vì sao trung vị mà không phải trung bình?** Trung bình bị giá trị cực đoan kéo lệch (một
cơn giông làm gió giật 27 m/s sẽ kéo trung bình lên); trung vị thì không.

### 3.3. `precipitation_mm` → điền 0 kèm CỜ đánh dấu

Không mưa là trạng thái mặc định ở Úc. Nhưng "điền 0 vì không mưa" khác "điền 0 vì mất dữ
liệu" — nên mỗi ô được điền có thêm cờ `_filled` để về sau còn phân biệt được.

### 3.4. Nhóm cột chữ → coi "thiếu" là một hạng mục riêng

`panel`, `inverter`, `location_name` → `'Unknown'`; `optimizers` → `'None'`;
`site_metric` → `'kWh'`. Nguyên tắc: **không bịa thông tin** — "không biết hãng inverter"
tự nó là một thông tin, cứ để mô hình nhìn thấy điều đó qua hạng mục 'Unknown'.

### 3.5. `capacity_kw` và `number_of_panels` → CẤM ĐIỀN (quyết định quan trọng nhất)

Đây là thay đổi lớn của v5 so với bản cũ, quyết định bởi nhóm trưởng ngày 18/08.

**Chuyện cũ:** bản trước điền công suất thiếu bằng trung vị theo khuôn viên, lùi về trung vị
toàn cục nếu khuôn viên không có số. Nghe hợp lý — cho tới khi soi số: 17 trạm thiếu nằm ở
các khuôn viên mà **4/5 khuôn viên không có nổi MỘT giá trị công suất thật nào**. Kết quả:
cả 17 trạm bị gán cùng một con số trung vị toàn cục **51,15 kW** — một con số bịa, lặp lại
1.132.078 lần, và mô hình sẽ tưởng đó là dữ liệu thật.

**Quyết định v5: để trống.** Hai lý do:
1. LightGBM (mô hình của dự án) xử lý ô trống **tự nhiên**: tại mỗi nút cây, các dòng trống
   được gửi theo "hướng mặc định" học từ dữ liệu. Không cần điền gì cả.
2. Hai cột này **không nằm trong 39 đặc trưng** của mô hình — chúng chỉ phục vụ hiển thị.
   Điền bịa thì mất, để trống thì không mất gì.

Cell "bằng chứng" cuối notebook in ra để ai cũng kiểm được: đúng 17/42 trạm NaN, đúng
1.132.078 dòng mỗi cột, và danh sách công suất theo khuôn viên — 4 khuôn viên trả về danh
sách **rỗng** (bản cũ chỗ này hiện `[51.15]` — số bịa).

### 3.6. Đổi 8 cột chữ sang kiểu `category`

Không đổi giá trị nào — chỉ đổi cách lưu trong RAM: thay vì mỗi dòng lưu nguyên chuỗi
"Bundoora", lưu một số nguyên trỏ vào bảng tra. Đo được: **1.618 MB → 1.082 MB (giảm 33%)**.

Hai cột chữ CỐ Ý không đổi: `gmm_if_outlier_reason` (notebook 01 sẽ `fillna("")` — thao tác
này vỡ trên kiểu category) và `weather_join_method` (notebook 01 sẽ gán nhãn mới chưa có
trong bảng tra).

---

## 4. Cổng kiểm tra PASS/FAIL

Cuối notebook là cổng tự động — **PASS không có nghĩa "hết ô trống"**, mà nghĩa là "trạng
thái ô trống đúng như thiết kế":

```python
CHO_PHEP_NULL = {'capacity_kw', 'number_of_panels', 'gmm_if_outlier_reason',
                 'weather_id', 'weather_timestamp', 'weather_type_is_day'}
# PASS khi: không còn cột nào trống NGOÀI danh sách này
```

Sáu cột được phép trống: hai cột metadata cấm điền (mục 3.5), lý do outlier (trống là đúng
với dòng bình thường), và ba cột khóa thời tiết của 218 mốc không ghép được.

---

## 5. Số kiểm chứng của lần chạy 20/08

| Kiểm tra | Kỳ vọng | Ý nghĩa |
|---|---|---|
| Số dòng ra | 2.731.946 (= số dòng vào) | Điền khuyết không được thêm/bớt dòng |
| Null `gmm_if_outlier_reason` đầu vào | **2.724.515** | Nếu ra 2.698.666 → đang đọc nhầm bản trích CŨ |
| Tổng sản lượng đầu vào | **9.064.665 kWh** | Nếu ra 9.310.931 → bản cũ |
| Trạm NaN capacity | 17/42 | Bằng chứng quyết định không-điền |
| Cổng cuối | PASS | Không cột trống ngoài danh sách 6 |

Hai dòng "nếu ra... → bản cũ" là chốt chống nhầm phiên bản dữ liệu — bài học xương máu ngày
20/08: một lần chạy đã đọc nhầm bản cũ do đường dẫn trong một cell chưa được cập nhật, và
chính hai con số này tố cáo điều đó.

*Ghi chú: Luồng quy tắc điền khuyết đã được thống nhất và chốt hạ để phục vụ cho các notebook ML phía sau...*