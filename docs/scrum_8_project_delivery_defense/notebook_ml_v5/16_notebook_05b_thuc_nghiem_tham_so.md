# Notebook 05b — Thực nghiệm hợp lệ hoá tham số (chi tiết đầy đủ)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy ngày 19/08 hoặc
> trưa 20/08. Giá trị **hiện hành** và lý do từng con số thay đổi được liệt kê đầy đủ ở
> [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md). Đọc file đó trước khi
> trích bất kỳ con số nào vào báo cáo.


> Notebook trả lời câu hỏi nguy hiểm nhất khi bảo vệ: **"con số này ở đâu ra?"** — cho từng
> tham số cố định trong pipeline, bằng thực nghiệm chứ không bằng lời.

- **Vào:** `05_selected/*` và cấu hình `train.yaml` / `features.yaml`
- **Ra:** `05b_thuc_nghiem_tham_so/*.csv` + toàn bộ hình

---

## 1. Vị trí trong quy trình

```
05 chọn đặc trưng  →  05b CHỐT THAM SỐ  →  06 huấn luyện bằng tham số đã chốt
```

Đây là **bước trước khi train**, không phải bước kiểm tra sau. Từ 20/08, mọi thí nghiệm trong
05b chạy độc lập với artifact của 06 (trước đây TN6/TN8 đọc `model_config.json` nên bắt buộc
phải có 06 trước — ngược thứ tự logic; nay chúng tự train mô hình tại chỗ).

Ngoại lệ duy nhất: **TN7** (đường hội tụ Optuna) nằm ở cuối notebook 06_4, vì nó hỏi "cuộc
dò đã hội tụ chưa" — không thể trả lời trước khi dò.

---

## 2. Hai điều kiện làm phép so sánh có giá trị

### 2.1. Tắt Optuna trong thí nghiệm
Mọi giá trị được thử dùng **chung một bộ siêu tham số mặc định**. Nếu để Optuna chạy, giá trị
nào tình cờ được tune kỹ hơn sẽ thắng — và ta không biết thắng vì tham số hay vì được tune.

### 2.2. Cố định phạm vi chấm điểm
Đổi `eps_elev` làm tập huấn luyện co giãn (từ 604.734 xuống 557.014 dòng), nhưng **phạm vi
chấm luôn dựng lại ở mức chuẩn 0,05**. Nhờ vậy mọi giá trị được chấm trên **đúng cùng một tập
dòng** — log in ra `do 289.348 dong` giống nhau ở mọi mức.

Không có điều kiện này, so sánh vô nghĩa: chấm trên hai tập khác nhau thì con số không so
được.

### 2.3. Trọng số phải khớp production *(sửa 20/08)*
Harness của 05b chạy qua pipeline `srcs`, mà `srcs` trước đây vẫn dùng cơ chế trọng số cũ
(`1 + α·k`) trong khi notebook 06 đã chuyển sang `mẫu_số`. Tức thực nghiệm đang đo trên **một
hàm mục tiêu khác** với mô hình thật → kết luận không áp được.

Đã sửa: thêm khoá `che_do_trong_so: mau_so` vào `train.yaml` và cài đặt tương ứng trong
`core/weights.py`. Giờ hai bên cùng một hàm mục tiêu.

---

## 3. Danh mục thí nghiệm

| # | Tham số | Cách làm | Trả lời câu hỏi |
|---|---|---|---|
| TN1 | `eps_elev` | Quét 0 → 0,15, **train lại** mỗi mức | Ngưỡng ngày/đêm đặt ở đâu? |
| TN2 | `clip_phan_vi` | Quét 0,90 → 1,00 (**1,00 = không cắt gì**, làm nhóm đối chứng) | Cắt nhãn có oan không? |
| TN2b | 0,99 vs 1,00 × 3 hạt giống | Kiểm chứng khác biệt thật hay nhiễu | |
| TN3 | `tran_cong_suat_he_so` | Quét 1,00 → 1,10 | Rào an toàn 1,02 hợp lý? |
| TN4 | Trọng số vùng đỉnh | Quét hệ số (cơ chế đã loại) | **Nút chết** — xem mục 8 |
| TN5 | `clip_csi` | Đo trực tiếp trên dữ liệu, không train | Trần trời quang cắt bao nhiêu %? |
| TN6 | Mức phân vị ngưỡng cắt | Một mô hình, cắt nhiều mức khi chấm | Đối chiếu chéo với TN2 |
| TN8 | `TOP_K_FEATURES` | Train ở K = 25/30/35/40/45 | Vì sao cắt ở 35? |
| — | Ngưỡng ε mẫu số | Quét 0,005 → 0,20 | Sàn chống chia cho 0 |
| TN9 | Chồng lấn nhãn ở ranh giới fold | Đếm dòng | Có rò rỉ qua fold không? |
| **TN10** | **Nhiễu huấn luyện** | **6 hạt giống, cùng cấu hình** | **Khác biệt bao nhiêu mới là thật?** |
| TN11 | Ablation trọng số | 3 cơ chế: `1+k` / tắt / `mẫu_số` | Chọn cơ chế nào? |

---

## 4. TN10 — thí nghiệm quan trọng nhất

Huấn luyện **6 lần với 6 hạt giống ngẫu nhiên khác nhau**, mọi thứ khác giữ nguyên.

Kết quả **lượt hiện hành (20/08)**: trung bình 22,6963% · **σ = 0,0741** · **3σ = 0,2224**.

*(Lượt 19/08 cho σ = 0,0609. Hai con số khác nhau vì dữ liệu và cơ chế trọng số đã đổi —
nhiễu huấn luyện là đặc tính của cặp (dữ liệu, cấu hình), không phải hằng số cố định.)*

**Ý nghĩa:** chỉ riêng việc đổi cách xáo dữ liệu (LightGBM lấy 90% dòng và 90% cột cho mỗi
cây) đã làm điểm số dao động ±0,06. Vậy **hai phương án chênh nhau ít hơn 3σ ≈ 0,18 điểm thì
không được kết luận cái nào tốt hơn**.

Đây là **thước để đọc mọi thí nghiệm còn lại**. Không có nó, mọi so sánh đều là đoán mò —
và đó là lỗi rất phổ biến trong các báo cáo ML.

---

## 5. Ba khuôn phán quyết

Cell "PHÁN QUYẾT" áp máy móc ba khuôn lên số đo, in kết luận sinh từ dữ liệu:

1. **THẮNG ĐO ĐƯỢC** — giá trị đang dùng là tốt nhất trong dải quét.
2. **HOÀ TRONG NHIỄU** (chênh < 3σ) — chọn theo **tiêu chí phụ nêu trước**: độ ổn định của
   ước lượng, ràng buộc vật lý, hoặc tính đơn giản.
3. **THUA NGOÀI NHIỄU** — chỉ giữ nếu là đánh đổi có chủ đích, có biên bản.

### Ví dụ đọc TN2

Mức 1,00 (không cắt) có WAPE **thấp hơn** mức 0,99 khoảng 0,04 điểm. Nhìn qua tưởng "không
cắt tốt hơn". Nhưng:

- TN2b lượt hiện hành: seed 7 → 1,00 thắng · seed 42 → 1,00 thắng · **seed 2026 → 0,99 thắng**
  ⇒ **thứ hạng đảo chiều tuỳ hạt giống**.
- Chênh lệch trung bình qua 3 hạt giống: **0,0172 điểm**, nhỏ hơn 3σ (0,2224) **13 lần**.
- *(Lượt 19/08 cho chênh −0,0017 và cũng đảo chiều — hai lượt độc lập, cùng một kết luận.)*

⇒ Khác biệt là **nhiễu**. Chọn 0,99 vì ngưỡng của nó suy từ phân bố (ổn định), còn ngưỡng của
mức 1,00 do **đúng một điểm dữ liệu** quyết định (7,19 — nhảy gấp 5 lần so với mức 0,995).

---

## 6. Bốn hạn chế đã biết (nêu trước, đừng để bị hỏi)

1. **TN8 chỉ hiệu lực tới K = 35.** Nó đọc tập đã cắt còn 39 cột, nên các mức K = 40/45 không
   thêm được đặc trưng mới. Notebook có in cảnh báo. Muốn quét thật phải đọc file 90 cột.
2. **TN7 phải chạy sau 06** (đã chuyển sang cuối 06_4).
3. **Việc chọn đặc trưng ở notebook 05** dùng dữ liệu toàn tập train rồi áp cho các fold sớm.
4. **Chồng lấn nhãn ở ranh giới fold** (TN9) được ghi nhận và công bố, không cắt.

---

## 7. Bộ câu hỏi phòng thủ

| Câu hỏi | Trả lời |
|---|---|
| Sao biết khác biệt 0,04 điểm là nhiễu? | TN10 đo σ = 0,0741 bằng 6 hạt giống (3σ = 0,2224); TN2b cho thấy thứ hạng đảo theo hạt giống |
| Thực nghiệm có chạy đúng đường của mô hình thật không? | Có, sau bản sửa 20/08: cùng trọng số `mẫu_số`, cùng bộ lọc, cùng phạm vi chấm |
| Vì sao tắt Optuna trong thí nghiệm? | Để mọi giá trị được đối xử như nhau; nếu để tune thì không biết thắng vì tham số hay vì được tune kỹ hơn |
| Các tham số này có được chọn trước khi train không? | Có. 05b nằm giữa 05 và 06 trong quy trình |


---

## 8. TN4 — nút chết, và vì sao đó là kết quả TỐT

Lượt hiện hành, TN4 cho **bốn giá trị y hệt nhau**:

```
α = 0,0 → 22,0428        α = 0,5 → 22,0428
α = 1,0 → 22,0428        α = 2,0 → 22,0428
```

Nguyên nhân: cơ chế trọng số đã chuyển sang `che_do_trong_so = 'mau_so'`, nên nhánh
`w = 1 + α·k` nằm sau `if che_do == 'theo_nhan'` **không bao giờ được gọi**.

**Đọc đúng:** đây là bằng chứng cơ chế cũ đã **gỡ sạch khỏi đường tính**, không phải bằng
chứng "α không nhạy". Notebook có sẵn bẫy cảnh báo cho tình huống này:

```
[CANH BAO - KNOB CHET?] WAPE trung nhau o MOI gia tri quet ->
tham so nay co the KHONG con nam trong duong tinh.
```

Bằng chứng cho việc **chọn** cơ chế trọng số nằm ở **TN11** — ba cơ chế cài đặt trực tiếp,
so trên cùng dữ liệu:

| Cơ chế | WAPE tổng | Vùng đỉnh | Vùng thấp | Thiên lệch ME |
|---|---|---|---|---|
| A: `w = 1 + k` | 22,7428 | **12,36** | 100,45 | **+0,4532** ⚠ |
| B: `w = 1` | 22,2789 | 13,95 | 88,18 | +0,1696 |
| **C: `w = mẫu_số`** ✅ | **22,1273** | 14,23 | **85,87** | **+0,1070** |

C thắng B 0,15 điểm ở WAPE tổng và có thiên lệch thấp nhất; trả giá ở vùng đỉnh (14,23 so
với 12,36 của A) — đánh đổi được công bố, không giấu.

**Điểm mạnh khi bảo vệ:** thứ tự xếp hạng A < B < C giữ nguyên qua **hai bộ dữ liệu khác
nhau** (19/08 và 20/08) ⇒ kết luận bền, không phụ thuộc một lần chạy may rủi.
