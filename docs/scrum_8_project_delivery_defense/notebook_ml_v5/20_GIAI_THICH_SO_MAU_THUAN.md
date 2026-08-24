# ĐỌC KHI THẤY SỐ MÂU THUẪN — vì sao cùng một thứ lại có nhiều con số

> Trong các file tài liệu và trong notebook, **cùng một đại lượng có thể xuất hiện với vài
> giá trị khác nhau**. Đó không phải lỗi. File này giải thích từng trường hợp, để khi bị hỏi
> "sao chỗ này ghi 53 mà chỗ kia ghi 52" thì trả lời được ngay.

---

## 1. Nguyên nhân gốc: có BA lượt chạy khác nhau trong hai ngày

| Lượt | Thời điểm | Dữ liệu | Cơ chế trọng số | Optuna |
|---|---|---|---|---|
| **A** | 19/08 | Bản trích ETL cũ | `w = 1 + k` | Có (20 trial) |
| **B** | 20/08 trưa | Bản trích ETL **mới** | `w = mẫu_số` | **Tắt** (N_TRIALS = 0) |
| **C** | 20/08 chiều | Bản trích ETL mới | `w = mẫu_số` | Có (20 trial) |

Ba lượt này khác nhau ở **dữ liệu** và **cấu hình**, nên mọi con số đều lệch chút ít. Nguyên
tắc khi trích số vào báo cáo: **chỉ lấy số của lượt cuối cùng (C)**, và ghi rõ lượt nào.

### Vì sao dữ liệu đổi giữa 19/08 và 20/08

Tầng ETL chạy lại với hai thay đổi (SCRUM-81):
- Ngưỡng dung sai vượt công suất: 1,0 → **1,20**, và chuyển từ *gắn cờ* sang **kẹp giá trị**.
  Hệ quả: `PHYSICAL_OVER_CAPACITY` từ 26.318 dòng xuống **0 dòng**; 20.468 dòng **đo thật**
  bị ghi đè về đúng 1,20× trần metadata (site 19: 15.971 dòng, site 24: 4.485, site 27: 12).
- Hybrid imputation đổi quy tắc đêm và kẹp trần. Tổng sản lượng toàn bộ dữ liệu **−2,64%**.
- Ngoài ra ETL điền thêm: `cloud_cover_low` từ 846.973 ô trống xuống 218; `wind_speed` từ
  217.946 xuống 218; `temperature_c` đổi giá trị ở 1,3 triệu dòng.
- **Không đổi:** `shortwave_radiation` (0 dòng thay đổi) — biến quan trọng nhất.

---

## 2. "53 đặc trưng" hay "52 đặc trưng"?

**Cả hai đều đúng, ở hai thời điểm khác nhau.**

```
Lượt A và B:  39 đặc trưng chọn  +  14 cột _mt  =  53
Lượt C:       39 đặc trưng chọn  +  13 cột _mt  =  52
```

Cột `_mt` chỉ được sinh cho những đại lượng **có mặt trong bộ đã chọn**. Chuỗi sự kiện:

1. Notebook 05 được sửa để chấm Mutual Information trên `y(T+1)` thay vì `y(T)`.
2. Thứ hạng MI xê dịch → **`hour_sin` rơi khỏi Top-35** (nó vốn đứng hạng 35, sát vạch cắt).
3. Không có `hour_sin` trong bộ 39 → không sinh `hour_sin_mt`.
4. 14 cột `_mt` giảm còn 13 → tổng 52.

**Con số hiện hành là 52.** Các file tài liệu viết "53" là mô tả lượt A/B.

### Bộ 39 đã đổi hai lần — và đó là đúng thiết kế

| Lần | Vào | Ra | Nguyên nhân |
|---|---|---|---|
| 20/08 sáng | `inverter_enc` | `cloud_cover_low` | ETL điền 846.973 ô trống → phân phối đổi → MI tụt (nó ở hạng 34/35) |
| 20/08 chiều | — | `hour_sin` | Sửa MI chấm trên `y(T+1)` → thứ hạng xê dịch |

Bộ đặc trưng **được suy từ dữ liệu**, không viết cứng. Dữ liệu đổi thì bộ đổi. Nguyên tắc:
**ghi nhận, tuyệt đối không sửa tay để ép về bộ cũ.**

---

## 3. Sàn nhiễu σ: 0,0609 hay 0,0741?

| Lượt | σ (6 hạt giống) | 3σ |
|---|---|---|
| A (19/08) | 0,0609 | 0,183 |
| **C (20/08)** | **0,0741** | **0,222** |

Cùng một phép đo, hai kết quả — vì dữ liệu và cơ chế trọng số đã đổi. Nhiễu huấn luyện là
**đặc tính của cặp (dữ liệu, cấu hình)**, không phải hằng số của thư viện.

**Ý nghĩa thực tiễn:** ngưỡng "khác biệt có thật" nới từ 0,183 lên **0,222 điểm**. Nghĩa là
với dữ liệu hiện tại, hai phương án chênh nhau dưới 0,222 điểm thì **không được kết luận cái
nào tốt hơn**.

Khi trích vào báo cáo: dùng **0,0741**, và nói rõ "đo bằng 6 hạt giống trên chính cấu hình
cuối cùng".

---

## 4. `clip_k`: 1,3583 · 1,3587 · 1,3764 — ba con số cho một tham số

| Giá trị | Thuộc lượt | Ghi chú |
|---|---|---|
| 1,3764 | v4 (trước đó) | Bản trích ETL đời cũ |
| 1,3583 | A (19/08) | |
| **1,3587** | **C (20/08)** | Con số hiện hành |

**Đây chính là bằng chứng cho luận điểm quan trọng nhất của dự án:** pipeline **không
hardcode con số, mà hardcode quy tắc** — "trần cắt nhãn = phân vị 0,99 của `k` trên tập
train". Dữ liệu đổi thì con số tự đổi theo. Nếu ba lượt chạy cho ra ba con số **giống hệt
nhau** mới là đáng nghi.

Cách nói khi bảo vệ: *"Chúng em không chọn 1,3587. Chúng em chọn quy tắc phân vị 0,99; trên
bộ dữ liệu này quy tắc đó cho 1,3587."*

---

## 5. TN4 cho bốn giá trị GIỐNG HỆT NHAU — nghĩa là gì

Kết quả lượt C:

```
he_so_trong_so_dinh = 0.0  →  WAPE 22.0428
he_so_trong_so_dinh = 0.5  →  WAPE 22.0428
he_so_trong_so_dinh = 1.0  →  WAPE 22.0428
he_so_trong_so_dinh = 2.0  →  WAPE 22.0428
```

**Không phải "tham số không nhạy". Mà là "tham số đã chết".**

Từ 20/08, cơ chế trọng số chuyển sang `che_do_trong_so = 'mau_so'`. Trong code, nhánh cũ
`w = 1 + α·k` nằm sau điều kiện `if che_do == 'theo_nhan'` — nhánh này **không bao giờ chạy
nữa**. Nên đổi α từ 0 đến 2 không ảnh hưởng gì.

 **Cách đọc đúng:** TN4 ở lượt C là **bằng chứng cơ chế cũ đã được gỡ bỏ hoàn toàn khỏi
đường tính**, không phải bằng chứng "α không quan trọng".

Bằng chứng thật cho việc **chọn cơ chế trọng số** nằm ở **TN11**, nơi ba cơ chế được cài đặt
trực tiếp và so sánh:

| Cơ chế | WAPE tổng | WAPE vùng đỉnh | WAPE vùng thấp | Thiên lệch ME |
|---|---|---|---|---|
| A: `w = 1 + k` | 22,7428 | **12,36** | 100,45 | **+0,4532** ⚠ |
| B: `w = 1` | 22,2789 | 13,95 | 88,18 | +0,1696 |
| **C: `w = mẫu_số`**  | **22,1273** | 14,23 | **85,87** | **+0,1070** |

Đang dùng là **C** — tốt nhất ở WAPE tổng, vùng thấp, và thiên lệch. Đổi lại kém nhất ở vùng
đỉnh (14,23 so với 12,36) — đây là đánh đổi được công bố, không giấu.

*(So sánh với lượt A ngày 19/08: A = 22,56 / 12,78 / 97,24 / +0,371 và C = 22,23 / 14,50 /
84,24 / +0,074. Thứ tự xếp hạng giữ nguyên qua hai bộ dữ liệu — đây là bằng chứng kết luận
bền, không phụ thuộc một lần chạy.)*

---

## 6. TN2b: "1.00 thắng 2/3 seed" hay "0.99 thắng 1/3 seed"?

| Lượt | Kết quả | Chênh trung bình (1.00 − 0.99) |
|---|---|---|
| A (19/08) | 1.00 thắng 2/3 seed | −0,0017 |
| **C (20/08)** | **0.99 thắng 1/3 seed** | **−0,0172** |

Chi tiết lượt C:

| Hạt giống | 0.99 | 1.00 | Ai thắng |
|---|---|---|---|
| 7 | 22,0333 | 21,9962 | 1.00 |
| 42 | 22,0428 | 22,0196 | 1.00 |
| 2026 | 22,0033 | 22,0119 | **0.99** |

**Cách đọc đúng — và đây là điểm mấu chốt:** kết luận của TN2b **không phải** "cái nào thắng
nhiều seed hơn". Kết luận là: **thứ hạng đảo chiều tuỳ hạt giống** ⇒ khác biệt nằm trong
nhiễu ⇒ không được dùng WAPE để chọn giữa 0,99 và 1,00.

Cả hai lượt A và C đều cho cùng kết luận đó, chỉ khác chi tiết seed nào thắng. Chênh trung
bình 0,0172 so với 3σ = 0,222 → **nhỏ hơn 13 lần**.

Việc chọn 0,99 dựa trên **tiêu chí phụ nêu trước**: ngưỡng của mức 0,99 suy từ phân bố
(1,3587, ổn định), còn ngưỡng của mức 1,00 do **đúng một điểm dữ liệu lớn nhất** quyết định —
ở lượt A nó nhảy lên 7,1865, gấp 5 lần mức 0,995.

---

## 7. Các số WAPE: 22,0424 · 22,0428 · 22,2897 · 17,7273

Bốn con số này **đo bốn thứ khác nhau**, rất dễ nhầm:

| Con số | Là gì | Tập nào |
|---|---|---|
| 22,2897 | MAE h1, lượt A (có tune, trọng số cũ) | Validation |
| 22,0424 | MAE h1, lượt B (không tune, `mẫu_số`) | Validation |
| 22,0428 | Cùng cấu hình B nhưng chạy qua harness của 05b | Validation |
| **17,7273** | MAE h1, lượt B | **TEST** |

**Vì sao số TEST (17,73) lại TỐT HƠN số VALIDATION (22,04)?** Câu này chắc chắn bị hỏi.

Trả lời: hai tập nằm ở **hai giai đoạn thời gian khác nhau**. Tập test là 15% cuối cùng, rơi
vào giai đoạn thời tiết ổn định hơn (ít ngày mây biến động). Đây là hiện tượng bình thường
với chuỗi thời gian và là lý do phải **báo cáo cả hai con số** chứ không chỉ chọn cái đẹp.

Chênh lệch 22,0424 (notebook) và 22,0428 (harness 05b) là 0,0004 — do hai đường code khác
nhau đôi chút ở khâu lọc; nhỏ hơn σ hàng trăm lần, không có ý nghĩa.

---

## 8. TN1 `eps_elev`: argmin không phải giá trị đang dùng

Kết quả lượt C:

```
eps = 0.00  →  22.0018   ← thấp nhất
eps = 0.02  →  22.0185
eps = 0.05  →  22.0428   ← đang dùng
eps = 0.10  →  22.0378
eps = 0.15  →  22.0434
```

Chênh giữa đang dùng và argmin: **0,0410**, so với 3σ = 0,222 → **hoà trong nhiễu**.

**Vì sao vẫn giữ 0,05 dù 0,00 có điểm thấp hơn:** tiêu chí phụ là **ràng buộc vật lý**, nêu
trước khi chạy. Ở `eps = 0`, mẫu số `site_scale × sin` tiến về 0 ở vùng bình minh/hoàng hôn,
làm nhãn `k` nổ tung — đo được `k` lớn nhất tới **19.573** ở vùng `sin ≤ 0,02`. Nhãn nổ không
làm hỏng WAPE tổng ngay (vì vùng đó chỉ chiếm 0,07% điện năng) nhưng nó **kéo lệch ngưỡng cắt
nhãn** cho toàn bộ phần còn lại: tính cả vùng rìa thì phân vị 0,99 lệch **+0,71%**.

Đây là ví dụ điển hình cho luật "hoà trong nhiễu thì chọn theo tiêu chí phụ", không phải
"luôn chọn điểm thấp nhất".

---

## 9. `clip_csi`: 1,2 hay 1,5 — và mâu thuẫn 0,057 / 0,059 trong 05f

**`clip_csi`:** giá trị cũ là 1,2, nâng lên **1,5** vì có ngày trời quang bức xạ đo vượt mức
lý thuyết (hiện tượng khuếch đại rìa mây — có thật về vật lý). Mọi tài liệu ghi 1,2 là mô tả
bản cũ.

**Mâu thuẫn 0,057 / 0,059 trong notebook 05f:** phần output in ra chứng minh hằng số
**0,059** khớp với artifact, nhưng phần markdown viết tay lại nói **0,057** khớp. Nguyên
nhân: markdown viết từ đợt trước khi notebook 03_2 còn dùng biến thể tự cài đặt với hằng số
0,057; sau khi chuyển sang gọi thẳng `pvlib.clearsky.haurwitz` thì hằng số đúng là **0,059**
(giá trị gốc của bài báo Haurwitz 1945).

**Số đúng là 0,059.** Phần markdown trong 05f cần sửa lời cho khớp — đã ghi nhận, chưa sửa.

---

## 10. Bảng tra nhanh: khi bị hỏi "số nào mới đúng"

| Đại lượng | Giá trị hiện hành | Số cũ hay gặp |
|---|---|---|
| Đặc trưng vào mô hình | **52** | 53 |
| Đặc trưng được chọn | **39** | 39 (không đổi) |
| `clip_k` | **1,3587** | 1,3583 · 1,3764 |
| σ nhiễu huấn luyện | **0,0741** | 0,0609 |
| 3σ (ngưỡng khác biệt thật) | **0,2224** | 0,183 |
| Hằng số Haurwitz | **1098 / 0,059** | 0,057 |
| `clip_csi` | **1,5** | 1,2 |
| Cơ chế trọng số | **`mau_so`** | `1 + k` |
| `he_so_trong_so_dinh` | **0,0 (nút đã chết)** | 1,0 |
| Số dòng huấn luyện h1 | **599.545** | 599.552 · 599.174 |
| `PHYSICAL_OVER_CAPACITY` | **0 dòng** | 26.318 dòng |

---

## 11. Nguyên tắc chung để không bao giờ bị bắt lỗi số

1. **Mỗi con số phải kèm ngữ cảnh**: lượt chạy nào, tập nào, cấu hình nào.
2. **Số trong báo cáo chỉ lấy từ output cell** của lượt cuối cùng, chép nguyên văn.
3. **Số đổi giữa các lượt là bình thường** — vì tham số được suy từ dữ liệu. Số **không** đổi
   khi dữ liệu đổi mới là dấu hiệu đáng ngờ.
4. Khi bị hỏi về một con số cũ trong tài liệu: trả lời *"đó là giá trị của lượt chạy ngày
   19/08 trên bản trích ETL cũ; giá trị hiện hành là X, lý do thay đổi là Y"* — đây là câu
   trả lời của người kiểm soát được dữ liệu của mình.
