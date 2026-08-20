# Notebook 03_2 — Hình học mặt trời và quy mô trạm (chi tiết đầy đủ)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy ngày 19/08 hoặc
> trưa 20/08. Giá trị **hiện hành** và lý do từng con số thay đổi được liệt kê đầy đủ ở
> [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md). Đọc file đó trước khi
> trích bất kỳ con số nào vào báo cáo.


> Notebook có **nhiều phép tính vật lý nhất**. Mọi con số ở đây đều bị hỏi khi bảo vệ vì
> chúng là hằng số. File này giải thích từng cái từ gốc.

- **Vào:** `03_1_features_time/v5_*_time.parquet`
- **Ra:** `03_2_features_spatial/v5_*_spatial.parquet` + `quy_mo_tram.json`

---

## 1. Vì sao cần notebook này

Ba vấn đề vật lý mà dữ liệu thô không tự giải quyết:

1. **Không biết mặt trời đang ở đâu.** Dữ liệu chỉ có mốc thời gian; muốn biết góc mặt trời
   phải tính từ vĩ độ, kinh độ, ngày, giờ.
2. **Thời tiết theo GIỜ, sản lượng theo 15 PHÚT.** Ghép thẳng thì bức xạ thành đường bậc
   thang — mỗi giá trị lặp 4 lần.
3. **42 trạm to nhỏ khác nhau.** Cần một thước đo quy mô để đưa về cùng thang so sánh.

---

## 2. Vị trí mặt trời — vì sao phải dùng thư viện chuẩn

### 2.1. Bản v5 dùng pvlib

```python
from pvlib import solarposition, clearsky
sp = solarposition.get_solarposition(utc_index, latitude=lat, longitude=lon)
```

`pvlib` cài đặt thuật toán **SPA** (Solar Position Algorithm) của NREL — Phòng thí nghiệm
Năng lượng Tái tạo Quốc gia Hoa Kỳ. Sai số công bố: dưới 0,0003°.

### 2.2. Múi giờ — cạm bẫy lớn nhất

Úc có **giờ mùa hè (DST)**: đồng hồ nhảy 1 tiếng vào một ngày cụ thể trong năm, và ngày đó
**đổi theo từng năm**.

Bản v4 dùng phép gần đúng: "tháng 10 đến tháng 3 thì +11 giờ, còn lại +10 giờ". Notebook
03_2b đo cái giá của phép gần đúng này:

| Cách tính | Sai số góc cao mặt trời (phân vị 99) | Cực đại |
|---|---|---|
| Cắt DST theo tháng (v4) | **8,54°** | **12,35°** |
| Múi giờ `Australia/Melbourne` thật (v5) | **0,0000°** | **0,0000°** |

Sai 12° góc mặt trời là sai rất nặng — đủ để lệch hẳn giờ mọc/lặn. Bản v5 dùng
`ZoneInfo('Australia/Melbourne')`, tra offset **tại 12h trưa từng ngày** (tránh các giờ mơ hồ
quanh thời điểm đổi giờ).

**Câu hỏi:** *"Sao không tự viết công thức cho gọn?"*
Trả lời: đã từng tự viết (công thức NOAA rút gọn). Kết quả lệch tới 12° ở những ngày đổi giờ.
Dùng thư viện chuẩn ngành vừa đúng hơn vừa dễ bảo vệ — đó là thuật toán mà cả ngành điện mặt
trời dùng.

---

## 3. Bức xạ trời quang — mô hình Haurwitz (1945)

```
ghi_cs = 1098 × sin(h) × exp( −0,059 / sin(h) )        h = góc cao mặt trời
```

**Ý nghĩa:** ước lượng bức xạ chiếu xuống mặt đất **nếu trời hoàn toàn quang**. Nó là đường
"trần lý thuyết" để so sánh: bức xạ đo được chia cho `ghi_cs` ra **chỉ số trời quang** —
gần 1 là trời quang, gần 0 là mây dày.

**Hai hằng số 1098 và 0,059 ở đâu ra:** từ chính bài báo Haurwitz (1945), fit trên dữ liệu
quan trắc. Notebook 05f ước lượng lại từ dữ liệu 42 trạm để kiểm chứng, và đối chiếu với bản
cài đặt trong `pvlib.clearsky.haurwitz` — **khớp 0,0000 W/m²**.

**Vì sao chọn Haurwitz mà không phải mô hình phức tạp hơn:** nó chỉ cần **một** đầu vào là
góc mặt trời. Các mô hình tốt hơn (Ineichen, REST2) cần độ đục khí quyển, hơi nước, sol khí —
dữ liệu mà dự án không có.

---

## 4. Hệ số hiệu chỉnh theo trạm `cs_factor`

### 4.1. Vấn đề

Haurwitz là mô hình toàn cầu, không biết gì về địa phương. Trên dữ liệu này nó ước lượng
**thiếu**: bức xạ đo được vượt `ghi_cs` ở khoảng **27%** số mốc. Hậu quả: chỉ số trời quang
thường xuyên vượt 1 và bị trần cắt mất.

### 4.2. Cách xử lý

```
cs_factor = phân vị 0,98 của (bức xạ đo / ghi_cs),  chỉ lấy mốc có góc cao > 10°
ghi_cs   ← ghi_cs × cs_factor
```

Mỗi trạm một hệ số riêng, tính **chỉ trên tập train**.

### 4.3. Ngưỡng 10° — một lỗi thật đã được phát hiện nhờ thực nghiệm

Ban đầu bộ lọc là `ghi_cs > 50 W/m²`. Hậu quả: **42/42 trạm** đều bị đẩy chạm cận trên 2,0,
cột `cs_factor` trở thành hằng số vô dụng.

Nguyên nhân: ở góc thấp (bình minh/hoàng hôn), `ghi_cs` tính liên tục theo 15 phút nên rơi về
0 **rất nhanh**, trong khi bức xạ đo lấy theo giờ (lặp 4 lần trong khối) chưa kịp giảm theo.
Tỷ lệ giữa hai cái nổ tung. Số đo thật: phân vị 98 của tỷ lệ lúc **19h là 3,2**, trong khi
giữa trưa (12–14h) chỉ **1,0–1,1**.

Sửa: lọc theo **góc cao mặt trời > 10°** (`sin > 0,1736`) thay vì theo `ghi_cs`. Ngưỡng 10°
lấy theo hai công bố về đánh giá mô hình trời quang (Kwarikunda & Chiguvare 2021; Mabasa và
cộng sự 2021), với lý do: dưới 10° đường đi tia sáng qua khí quyển dài hơn nhiều, sai số mô
hình tăng vọt.

---

## 5. Hạ bức xạ từ 1 giờ về 15 phút (downscale)

### 5.1. Ý tưởng

Trong một giờ, ta biết **tổng** bức xạ (từ dữ liệu thời tiết) nhưng không biết nó phân bố thế
nào trong 4 khoảng 15 phút. Dùng **hình dạng** của `ghi_cs` — vốn tính được chính xác từng 15
phút — để phân bổ.

```
tỷ trọng(t) = ghi_cs(t) / Σ ghi_cs(4 mốc trong giờ)
bức xạ(t)   = bức xạ giờ × 4 × tỷ trọng(t)
```

### 5.2. Hai chốt chặn

```python
CLIP_CSI = 1.5                 # trần chỉ số trời quang
TY_LE_GHI_CS_TOI_DA = 1.5      # biến thiên ghi_cs trong một khối ≤ 1,5 lần
```

- **`CLIP_CSI = 1,5`**: có ngày trời quang bức xạ đo **vượt** mức lý thuyết. Đây là hiện tượng
  vật lý có thật — **khuếch đại bởi rìa mây** (cloud enhancement): mây phản xạ thêm ánh sáng
  xuống tấm pin. Trần 1,5 cho phép hiện tượng này tồn tại nhưng chặn các giá trị phi lý.
  Trước đây trần là 1,2 và cắt mất dữ liệu thật.
- **`TY_LE_GHI_CS_TOI_DA`**: nếu trong một khối giờ mà `ghi_cs` biến thiên quá 1,5 lần (đầu
  giờ và cuối giờ chênh nhau lớn — hay xảy ra lúc bình minh/hoàng hôn), phép phân bổ trở nên
  không tin cậy → dùng phân bổ đều.

---

## 6. Quy mô và trần công suất từng trạm

```python
QUANTILE_SCALE = 0.99      # site_scale     — mẫu số chuẩn hoá
QUANTILE_TRAN  = 0.999     # tran_cong_suat — trần khi nhân ngược
```

Tính trên **dòng ban ngày của tập TRAIN**, lưu ra `quy_mo_tram.json`, rồi **áp nguyên** cho
val/test.

**Vì sao dùng phân vị chứ không dùng giá trị lớn nhất:** giá trị lớn nhất do **một** điểm dữ
liệu quyết định — một cảm biến lỗi là hỏng cả thang đo. Phân vị 0,99 bỏ qua 1% đuôi trên,
bền hơn nhiều.

**Vì sao dùng dữ liệu đo mà không dùng `capacity_kw` trong metadata:** vì metadata **sai**.
Đo trên file gốc: trạm 19 có sản lượng đo thật vượt trần metadata tới **4,92 lần**, trung vị
đã là **1,43 lần**. Suy quy mô từ chính dữ liệu đo là cách duy nhất đáng tin.

**Vì sao chỉ tính trên train:** nếu tính trên toàn bộ dữ liệu thì `site_scale` chứa thông tin
của giai đoạn test → mô hình gián tiếp biết tương lai qua mẫu số. Đây là rò rỉ rất khó phát
hiện nếu không đặt luật từ đầu.

### Hai đặc trưng suy ra

```
ky_vong       = site_scale × sin(góc cao)     # kỳ vọng độ lớn tại thời điểm đó
ty_le_bao_hoa = ky_vong / tran_cong_suat      # đang tiến gần mức bão hoà chưa
```

`ty_le_bao_hoa` cho mô hình biết khi nào inverter sắp cắt đỉnh — một hiện tượng phi tuyến
quan trọng của điện mặt trời.

---

## 7. Cách kiểm tra notebook chạy đúng

| Kiểm tra | Kỳ vọng |
|---|---|
| File `quy_mo_tram.json` | Đủ 42 trạm, có cả `site_scale` và `tran_cong_suat` |
| Biểu đồ downscale | Đường bức xạ sau xử lý trơn hình chuông, không còn bậc thang |
| Quét 42 trạm × mọi ngày | Không còn đỉnh nhọn bất thường |
| `cs_factor` | KHÔNG được là hằng số; phải phân tán giữa các trạm |
| Đối chiếu 03_2b | Sai số so pvlib ≈ 0,0000° |

---

## 8. Bộ câu hỏi phòng thủ

| Câu hỏi | Trả lời |
|---|---|
| Vì sao tin được góc mặt trời tính đúng? | Dùng pvlib (thuật toán SPA của NREL); notebook 03_2b đối chiếu độc lập ra 0,0000° |
| Hằng số 1098 và 0,059 ở đâu? | Bài báo Haurwitz 1945; 05f ước lượng lại trên dữ liệu dự án và khớp bản cài đặt pvlib |
| Sao trần chỉ số trời quang là 1,5 mà không phải 1,0? | Vì bức xạ đo **thật sự** vượt mức lý thuyết do khuếch đại rìa mây; 05f đo phân bố và % bị cắt ở từng mức |
| `site_scale` là phân vị 99 — sao không lấy max? | Max do một điểm quyết định, không bền; phân vị 99 bỏ 1% đuôi |
| Sao không dùng công suất lắp đặt ghi trong metadata? | Metadata sai: trạm 19 có sản lượng đo vượt trần metadata 4,92 lần |
| Downscale có làm sai lệch tổng bức xạ không? | Không: phép phân bổ giữ nguyên tổng trong mỗi giờ, chỉ đổi cách chia trong giờ |
| Ngưỡng 10° cho `cs_factor` ở đâu ra? | Hai công bố quốc tế + số đo của chính dự án (tỷ lệ lúc 19h là 3,2 so với 1,0–1,1 giữa trưa) |
