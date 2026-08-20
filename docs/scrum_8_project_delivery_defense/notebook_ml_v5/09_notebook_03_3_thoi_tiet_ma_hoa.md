# Notebook 03_3 — Đặc trưng thời tiết và mã hoá (chi tiết đầy đủ)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy trước. Giá trị hiện
> hành và lý do từng con số thay đổi: [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md).


- **Vào:** `03_2_features_spatial/v5_*_spatial.parquet`
- **Ra:** `03_3_features_aggregate/v5_*_features.parquet` + `v5_category_maps.json`

---

## 1. Đặc trưng tương tác — vì sao phải tạo sẵn

Cây quyết định cắt **từng biến một**: `nếu bức xạ > 500 thì...`. Nó không tự nhân hai biến
với nhau. Nếu quan hệ thật sự là **tích** của hai biến, cây phải xấp xỉ bằng rất nhiều nhát
cắt bậc thang — tốn cây và kém chính xác.

Nên các tích quan trọng được tạo sẵn:

```python
temp_x_shortwave  = nhiệt độ × bức xạ
cloud_x_shortwave = mây × bức xạ
rad_x_sinelev     = bức xạ × sin(góc cao)
diffuse_ratio     = bức xạ khuếch tán / tổng bức xạ
```

### Ý nghĩa vật lý từng cái

| Đặc trưng | Vật lý đằng sau |
|---|---|
| `temp_x_shortwave` | Tấm pin nóng thì **hiệu suất giảm** (hệ số nhiệt độ âm, khoảng −0,3%/°C). Nắng mạnh + trời nóng cho ít điện hơn nắng mạnh + trời mát |
| `cloud_x_shortwave` | Mây làm giảm bức xạ hiệu dụng; tích này bắt mức độ tương tác |
| `rad_x_sinelev` | Bức xạ chiếu **nghiêng** lên mặt phẳng nằm ngang: cùng một mức bức xạ, góc chiếu thấp cho ít năng lượng hơn |
| `diffuse_ratio` | Tỷ lệ khuếch tán cao = trời đục/nhiều mây mỏng; thấp = trời trong. Đây là chỉ báo **chất lượng** ánh sáng, khác với cường độ |

Trong bộ 39 hiện tại, `temp_x_shortwave` đứng hạng **15** và `cloud_x_shortwave` hạng **26**
theo Mutual Information — tức các tích này thật sự hữu ích, không phải thêm cho có.

---

## 2. Mã hoá biến phân loại

Các cột chữ (`weather_condition`, `weather_description`, `inverter`, `panel`, `optimizers`,
`campus_name`) được đánh số và lưu bảng mã vào `v5_category_maps.json`.

### Ba quy tắc bắt buộc

1. **Bảng mã lập trên tập TRAIN**, rồi áp cho val/test. Nếu lập riêng cho từng tập, cùng một
   giá trị chữ sẽ nhận hai mã khác nhau ở hai tập → mô hình đọc sai hoàn toàn.
2. **Giá trị lạ (chưa từng thấy ở train) → mã −1.**
3. **Bảng mã phải được lưu ra file** để notebook 07 và dashboard dùng lại đúng bảng đó.

### Logic ẩn quan trọng nhất: phải KHAI BÁO là biến phân loại

Mã `0, 1, 2, ...` chỉ là nhãn, **không có thứ tự**. Nếu không khai báo với LightGBM, nó sẽ
coi là số và cắt kiểu `mã ≤ 17,5` — vô nghĩa, vì thứ tự mã chỉ là thứ tự bảng chữ cái của
tên gốc.

```python
model.fit(X, y, categorical_feature=[c for c in X.columns if c.endswith('_enc')])
```

Khai báo rồi, LightGBM cắt theo **tập hợp** (`mã ∈ {3, 7, 12}`) và **tự coi −1 là giá trị
thiếu** — khớp đúng thiết kế mã hoá ở trên.

Nhóm đã kiểm chứng bằng cách đọc cấu trúc cây đã huấn luyện: **2.131 nút cắt kiểu `==`,
0 nút cắt kiểu `<=`** cho các cột `_enc`.

---

## 3. Cổng kiểm tra chống rò rỉ

Kiểm lại toàn bộ: không đặc trưng nào chứa thông tin sau thời điểm T. Danh sách cột được phép
dịch sang T+h nằm ở `features.yaml → cot_tat_dinh` và **chỉ gồm thiên văn + lịch**.

---

## 4. Bộ câu hỏi phòng thủ

| Câu hỏi | Trả lời |
|---|---|
| Sao phải tạo cột tích, mô hình tự học không được à? | Cây cắt từng biến một, không tự nhân. Tích phải tạo sẵn thì cây mới dùng được trực tiếp |
| Mã hoá số cho biến chữ có gây hiểu nhầm thứ tự không? | Có, nếu không khai báo. Dự án khai báo `categorical_feature` và đã kiểm chứng bằng cấu trúc cây (2.131 nút cắt kiểu tập hợp) |
| Giá trị thời tiết lạ ở tập test thì sao? | Gán mã −1, LightGBM xử lý như giá trị thiếu |
| Vì sao lưu bảng mã ra file? | Để 07 và dashboard dùng đúng bảng của train; lập lại bảng là sai lệch mã |
