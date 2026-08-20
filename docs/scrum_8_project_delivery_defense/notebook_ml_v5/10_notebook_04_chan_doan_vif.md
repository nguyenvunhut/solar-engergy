# Notebook 04 — Chẩn đoán đa cộng tuyến (chi tiết đầy đủ)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy trước. Giá trị hiện
> hành và lý do từng con số thay đổi: [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md).


- **Vào:** `03_3_features_aggregate/v5_train_features.parquet`
- **Ra:** `04_diagnostics/feature_diagnostics.csv`

> Notebook này **không loại đặc trưng nào**. Nó chỉ lập bảng chẩn đoán để notebook 05 dùng.
> Tách bạch "đo" và "quyết định" là có chủ đích: người đọc thấy được cơ sở của quyết định.

---

## 1. Vấn đề: nhiều cột nói cùng một điều

Sau ba notebook tạo đặc trưng, có gần 90 cột ứng viên. Nhiều cột **trùng lặp thông tin**:
- `weather_condition_enc` và `weather_description_enc` — ánh xạ **1-1 hoàn toàn** (7 giá trị ↔ 7 giá trị)
- `ghi_cs` và `clearsky_proxy` — cái sau là hàm của cái trước
- `ky_vong` và `site_scale × sin_elevation` — bằng nhau theo định nghĩa

Đa cộng tuyến không làm cây quyết định **sai**, nhưng làm ba thứ tệ đi: tầm quan trọng đặc
trưng bị chia nhỏ và khó đọc, mô hình phình to vô ích, và giải thích SHAP bị loãng.

---

## 2. Bốn phép đo

```python
VIF_SAMPLE_SIZE     = 50_000     # đủ để VIF ổn định, nhẹ RAM
CORR_SAMPLE_SIZE    = 200_000
CORR_HIGH_THRESHOLD = 0.95       # |r| > 0,95 là tương quan cao
VIF_HIGH_THRESHOLD  = 10.0       # quy ước phổ biến cho đa cộng tuyến nặng
DUP_THRESHOLD       = 0.9999     # |r| > 0,9999 coi như trùng hoàn toàn
```

### 2.1. Cột hằng số và cột thiếu nhiều
Cột chỉ có một giá trị → không mang thông tin. Cột thiếu quá nhiều → không tin được.

### 2.2. Ma trận tương quan
Tìm cặp |r| > 0,9999 — đó là **bản sao toán học** của nhau.

### 2.3. VIF — hệ số phóng đại phương sai
Với mỗi đặc trưng: hồi quy nó theo **tất cả** đặc trưng còn lại, lấy R², rồi:

```
VIF = 1 / (1 − R²)
```

Đọc: VIF = 10 nghĩa là **90% biến thiên của cột này đã được các cột khác giải thích**.

Số thật trong dự án: `weather_condition_enc` VIF ≈ 138, `weather_description_enc` ≈ 132 — hai
cột này gây VIF cho **nhau** vì là ánh xạ 1-1.

**Xử lý của dự án:** không loại, mà **khai báo cả hai là biến phân loại** cho LightGBM. Với
biến phân loại, mô hình cắt theo tập hợp nên trùng lặp không gây hại như với biến số.

### 2.4. PLS — góc nhìn thứ hai
Bình phương tối thiểu riêng phần: chiếu dữ liệu lên vài thành phần tương quan cao nhất với
mục tiêu, xem đặc trưng nào đóng góp mạnh. Độc lập với VIF nên dùng để đối chiếu chéo.

---

## 3. Cạm bẫy đã gặp và cách sửa

Khi notebook 00 chuyển các cột chữ sang kiểu `category` để tiết kiệm RAM, bộ lọc "chọn cột
số" bị nhầm: kiểu `dictionary<values=string, indices=int32>` của Arrow **chứa chuỗi 'int'**
nên lọt qua bộ lọc theo tên kiểu. Kết quả: lỗi
`ArrowInvalid: Failed to parse string 'Bundoora' as float`.

Sửa: kiểm tra kiểu bằng hàm chuẩn của pyarrow (`pa.types.is_floating`, `pa.types.is_integer`)
thay vì so chuỗi tên kiểu. Số cột từ 93 (sai) về 89 (đúng).

**Bài học:** lọc kiểu dữ liệu bằng cách so chuỗi tên kiểu là mong manh.

---

## 4. Bộ câu hỏi phòng thủ

| Câu hỏi | Trả lời |
|---|---|
| VIF > 10 sao vẫn giữ đặc trưng? | Vì chúng là biến **phân loại**, được khai báo đúng kiểu cho LightGBM; đa cộng tuyến giữa biến phân loại không gây hại như với biến số |
| Ngưỡng VIF = 10 ở đâu ra? | Quy ước phổ biến trong thống kê ứng dụng; ở đây chỉ dùng để **đánh dấu**, không để loại tự động |
| Sao notebook không tự loại luôn? | Cố ý tách "đo" khỏi "quyết định": 04 đo, 05 quyết định. Người đọc thấy được cơ sở |
| Vì sao lấy mẫu 50.000 để tính VIF? | VIF cần nghịch đảo ma trận; 50.000 dòng đủ để ước lượng ổn định mà không tốn RAM |
