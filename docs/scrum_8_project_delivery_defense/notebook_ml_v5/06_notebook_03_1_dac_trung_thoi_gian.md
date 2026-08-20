# Notebook 03_1 — Đặc trưng thời gian, trễ và trượt (`03_1_features_time.ipynb`)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy trước. Giá trị hiện
> hành và lý do từng con số thay đổi: [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md).


> Người đọc mục tiêu: chưa từng làm ML. Đây là notebook đầu tiên của cụm "tạo đặc trưng"
> (03_1 → 03_2 → 03_3).

---

## 1. Tư duy chung: mô hình chỉ thấy những gì mình đưa cho nó

LightGBM không tự biết "bây giờ là trưa" hay "một tiếng trước phát được bao nhiêu". Mọi
hiểu biết đó phải được **đóng gói thành cột số**. Notebook 03_1 đóng gói hai loại hiểu
biết: **thời gian** (bây giờ là lúc nào) và **quán tính** (chuỗi vừa diễn biến ra sao).

- **Vào:** các tập từ `02_split` (development, test, train, val, 3 fold — xử lý riêng từng tập)
- **Ra:** `03_1_features_time/v5_*_time.parquet`

---

## 2. Nhóm 1: đặc trưng lịch — và mẹo "vòng tròn"

### Vấn đề 23h và 0h

Nếu đưa giờ vào mô hình dạng số thô (0–23), thì 23h và 0h cách nhau 23 đơn vị — trong khi
thực tế chúng cách nhau 1 tiếng. Mô hình cây có thể sống được với điều này, nhưng sẽ tốn
nhiều nhát cắt vô ích ở chỗ nối.

### Giải pháp: chiếu lên vòng tròn

```
hour_sin = sin(2π × giờ/24)        hour_cos = cos(2π × giờ/24)
doy_sin  = sin(2π × ngày/365)      doy_cos  = cos(2π × ngày/365)
```

Tưởng tượng mặt đồng hồ: mỗi giờ là một điểm trên vòng tròn, tọa độ (sin, cos) của điểm đó
làm hai cột mới. Trên vòng tròn, 23h và 0h nằm sát nhau — đúng bản chất. Cùng kỹ thuật cho
ngày-trong-năm (nhịp mùa).

### Mùa theo bán cầu NAM

Dữ liệu ở Úc: tháng 12–1–2 là **mùa hè**, 6–7–8 là **mùa đông** — ngược với trực giác người
Việt. Bảng `SOUTHERN_SEASON_MAP` viết tường minh trong notebook để không ai vô tình "sửa
lại cho đúng" thành sai.

---

## 3. Nhóm 2: đặc trưng trễ (lag) — và một quyết định nhờ kiểm định mà có

```
LAGS = (4, 96)     # lag_4 = giá trị 1 GIỜ trước, lag_96 = 24 GIỜ trước
```

`lag_96` mang nhịp ngày ("hôm qua giờ này phát 40 kWh"); `lag_4` mang quán tính gần ("một
tiếng trước trời đang âm u").

### Vì sao KHÔNG có lag_1 (giá trị 15 phút trước)?

Đây là một trong những quyết định có bằng chứng dày nhất dự án. Bản đầu có `lag_1`, và mô
hình đạt điểm rất tốt — nhưng một cuộc kiểm định độc lập (31/07) phát hiện dự báo **trễ
pha**: đường dự báo là đường thực tế **dịch sang phải 15 phút**. Mô hình đã học mẹo rẻ
tiền: "cứ chép giá trị vừa rồi" — vì 15 phút trước gần đúng bằng hiện tại. Kết quả kiểm
định: 39/40 trạm vượt ngưỡng trễ 5 phút, 126/127 ngày dự báo đi sau thực tế.

`lag_1` bị loại. `lag_4` được kiểm định lại: 0/40 trạm vượt ngưỡng — giữ. Từ đó pipeline có
hẳn một "cổng đo trễ" chạy trước mỗi lần huấn luyện (xem tài liệu notebook 06).

Bài học cho người mới: **điểm số tốt chưa chắc mô hình tốt** — phải kiểm cả CÁCH nó đạt điểm.

---

## 4. Nhóm 3: đặc trưng trượt (rolling)

```
ROLLING_WINDOWS = (4, 96)   →  mean / std / min / max trên cửa sổ 1 giờ và 24 giờ
```

- `rolling_mean_4`: mức phát trung bình giờ qua — nền hiện tại.
- `rolling_std_4`: độ giật giờ qua — trời đang ổn định hay mây rối loạn. Đây là đặc trưng
  "đo độ loạn" mà giá trị điểm đơn lẻ không có.
- `rolling_max_96` / `rolling_min_96`: biên độ 24 giờ qua.

Mọi cửa sổ đều tính **lùi về quá khứ** (backward). Kết hợp với lưới đều của notebook 01 và
mặt nạ `has_complete_history_features`, các cột này không bao giờ lén chứa điểm tương lai.

---

## 5. Mẫu số Lonij — đối thủ được nuôi để so tài

```
PHAN_VI_LONIJ = 0.80, SO_NGAY_LONIJ = 15
```

Cột `pv_clr_lonij` = phân vị 80 sản lượng đo được **tại cùng khung giờ trong 15 ngày liền
trước** — công thức chuẩn hóa của Lonij et al. (2012), giữ đúng tham số bài báo. Nó KHÔNG
được dùng làm đặc trưng (nằm trong danh sách cấm của notebook 05) — nó tồn tại để notebook
05c cho công thức của dự án và công thức của bài báo **đấu tay đôi bằng số** trên cùng dữ
liệu. (Kết quả: dự án thắng ~3 điểm WAPE — xem tài liệu 05c.)

---

## 6. Cổng QA cuối notebook

1. **Point-in-time đúng đắn**: với một mẫu dòng ngẫu nhiên, tính lại tay từng lag/rolling
   từ dữ liệu gốc và so khớp — chứng minh không cột nào nhìn tương lai.
2. **Báo cáo đứt gãy**: liệt kê các đoạn gián đoạn theo mức nghiêm trọng, đối chiếu với
   mặt nạ lịch sử của notebook 01.
3. **Đếm NaN từng cột mới**: NaN chỉ được phép ở đầu chuỗi mỗi trạm (chưa đủ lịch sử) —
   đúng chỗ, đúng số lượng.


---

## PHỤ LỤC CỦA NOTEBOOK NÀY — các đặc trưng được tạo ở đây, kèm bài tính tay

> Dòng ví dụ dùng xuyên suốt: **trạm 27, 13:00 ngày 15/01/2021**. Sáu giá trị sản lượng
> gần nhất (kWh/15 phút): 11:45 = 41,1875 · 12:00 = 59,5625 · 12:15 = 62,6250 ·
> 12:30 = 47,9375 · 12:45 = 51,5625 · **13:00 = 96,8125**. Hôm qua 13:00 = 66,7500.

### Nhóm quán tính (9 cột)

| Cột | Công thức | Tính tay trên dòng ví dụ | Khớp file? |
|---|---|---|---|
| `lag_4` | y(T − 1 giờ) | y(12:00) = **59,5625** | ✔ |
| `lag_96` | y(T − 24 giờ) | y(14/01 13:00) = **66,7500** | ✔ |
| `rolling_mean_4` | trung bình 4 bước trước T | (59,5625+62,6250+47,9375+51,5625)/4 = 221,6875/4 = **55,421875** | ✔ |
| `rolling_max_4` | max 4 bước trước | max = **62,6250** | ✔ |
| `rolling_min_4` | min 4 bước trước | min = **47,9375** | ✔ |
| `rolling_std_4` | độ lệch chuẩn MẪU (chia n−1) | lệch: +4,1406; +7,2031; −7,4844; −3,8594 → bình phương cộng = 139,941 → /3 = 46,647 → √ = **6,8298** | ✔ (6,829847) |
| `rolling_mean_96` | trung bình 96 bước (24h) | cùng cách, 96 số hạng | ✔ |
| `rolling_std_96` | std mẫu 96 bước | — | ✔ |
| `rolling_max_96` | max 24 giờ | — | ✔ |

Hai điểm hay bấm sai: (1) cửa sổ tính trên 4 bước **NGAY TRƯỚC** T, không gồm chính T;
(2) std chia **n−1**, không phải n.

### Nhóm lịch (6 cột)

Giờ = 13, ngày thứ 15 của năm:

| Cột | Công thức | Tính tay | Khớp file? |
|---|---|---|---|
| `hour` | giờ nguyên | **13** | ✔ |
| `minute_of_day` | giờ×60 + phút | 13×60 = **780** | ✔ |
| `hour_sin` | sin(2π·13/24) | sin(195°) = **−0,258819** | ✔ |
| `hour_cos` | cos(2π·13/24) | cos(195°) = **−0,965926** | ✔ |
| `doy_sin` | sin(2π·15/365) | sin(14,79°) = **0,255182** | ✔ |
| `doy_cos` | cos(2π·15/365) | **0,966893** | ✔ |

Kiểm chéo: sin² + cos² = 0,06698 + 0,93302 = 1 ✔.

*(Cột `pv_clr_lonij` cũng sinh ở đây nhưng KHÔNG phải đặc trưng — nó bị cấm ở notebook 05,
chỉ dùng làm đối thủ so tài trong 05c.)*
