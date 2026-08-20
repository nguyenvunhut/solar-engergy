# Notebook 00b — Kiểm tra độc lập việc điền khuyết (`00b_recheck_fill_null.ipynb`)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy trước. Giá trị hiện
> hành và lý do từng con số thay đổi: [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md).


> Người đọc mục tiêu: chưa từng làm ML. Đọc `00_DOC_TRUOC_TIEN.md` và file notebook 00 trước.

---

## 1. Vì sao cần một notebook chỉ để "kiểm tra lại"

Nguyên tắc kiểm toán: **người làm không tự chấm điểm mình**. Notebook 00 điền khuyết và tự
báo PASS — nhưng nếu chính code của 00 có lỗi thì lời tự báo đó cũng sai theo. Notebook 00b
là người kiểm tra độc lập: nó **không dùng lại một dòng code nào của 00**, chỉ mở hai file
(trước và sau) rồi tự đếm, tự so.

Đây là mô hình hai lớp giống kế toán – kiểm toán, và là lý do 00b **chỉ đọc, không ghi** —
nó không được phép sửa gì, chỉ được phép kết luận.

- **File vào:** `v5_preprocessing.parquet` (trước khi điền) và `v5_final_cleaned.parquet` (sau)
- **File ra:** KHÔNG có — chỉ in bảng kết luận

---

## 2. Nó kiểm tra những gì

### Kiểm tra 1 — Bảng đối chiếu ô trống trước/sau

Với từng cột trong cả 47 cột:

```
Null_Before = số ô trống ở file TRƯỚC
Null_After  = số ô trống ở file SAU
Đã_điền     = Null_Before − Null_After
```

Đọc bảng này bắt được ba loại lỗi ngay lập tức:
- Cột đáng lẽ phải điền hết mà `Null_After > 0` → 00 bỏ sót.
- Cột CẤM điền (capacity_kw…) mà `Null_After < Null_Before` → 00 điền bậy, vi phạm quyết
  định nhóm trưởng.
- `Null_After > Null_Before` → có bước nào đó tạo THÊM ô trống, hỏng nặng.

### Kiểm tra 2 — Phân phối các cột đo lường có bị bóp méo không

Với 11 cột đo lường (bức xạ, nhiệt độ, mây, gió, mưa, giờ nắng), tính **trung bình và độ
lệch chuẩn trước/sau** rồi đặt cạnh nhau.

Logic đằng sau: điền khuyết đúng cách chỉ lấp chỗ trống bằng giá trị "hợp lý theo ngữ
cảnh", nên **hình dạng phân phối phải gần như nguyên vẹn**. Nếu trung bình nhiệt độ nhảy
từ 15,2°C lên 18,7°C sau khi điền — tức là đã bơm vào hàng loạt giá trị lệch, phải quay
lại xem tại sao. Đây là cách phát hiện lỗi mà KHÔNG cần biết đáp án đúng: mình không biết
giá trị thật của ô trống, nhưng biết việc điền không được phép làm cả tập dữ liệu đổi tính
cách.

---

## 3. Chi tiết kỹ thuật đáng biết: đọc theo lô

Cả hai file, mỗi file 2,7 triệu dòng × 47 cột. 00b đọc theo **lô 100.000 dòng** rồi cộng dồn
số đếm, thay vì nạp cả file vào RAM. Với người mới: đây là thói quen quan trọng khi làm dữ
liệu lớn — thống kê dạng "đếm/cộng" luôn tính được theo lô, không cần giữ toàn bộ dữ liệu
trong bộ nhớ cùng lúc.

---

## 4. Vị trí trong quy trình

```
00 (điền khuyết) ──> 00b (kiểm tra độc lập) ──> 01 (chỉ chạy khi 00b sạch)
```

Nếu 00b phát hiện bất thường: dừng, sửa 00, chạy lại cả 00 lẫn 00b. Không bao giờ "kệ nó,
chạy tiếp" — vì mọi notebook sau đều đứng trên giả định file cleaned đã đúng thiết kế.
