# Notebook 03_2b — Kiểm chứng hình học mặt trời và ngưỡng ban ngày (`03_2b_doi_chieu_pvlib.ipynb`)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy ngày 19/08 hoặc
> trưa 20/08. Giá trị **hiện hành** và lý do từng con số thay đổi được liệt kê đầy đủ ở
> [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md). Đọc file đó trước khi
> trích bất kỳ con số nào vào báo cáo.


> Người đọc mục tiêu: chưa từng làm ML. Notebook "trọng tài" — chỉ đọc và phán, không sản
> xuất dữ liệu cho pipeline.

---

## 1. Ba câu hỏi nó trả lời

1. Hình học mặt trời của 03_2 có **tái lập đúng** thư viện chuẩn không?
2. Định nghĩa "ban ngày" của dự án có **đúng ban ngày thật** không?
3. Vì sao phải **cắt vùng rìa** (góc mặt trời quá thấp) khỏi huấn luyện?

Mỗi câu được trả lời bằng số đo + hình, không bằng lời hứa.

---

## 2. Câu 1 — Đối chiếu hai tầng với pvlib

Lấy ~84.000 điểm mẫu (2.000 mốc × 42 trạm), tính lại góc mặt trời bằng pvlib theo hai kịch bản:

| Tầng | Quy ước giờ | Trả lời | Kết quả |
|---|---|---|---|
| 1 | "cắt theo tháng" (quy ước v4 cũ) | Giữ quy ước cũ thì sai bao nhiêu? | p99 **8,54°**, max **12,35°** |
| 2 | Múi giờ Melbourne thật | 03_2 v5 có đúng không? | **0,0000°** — khớp tuyệt đối |

Đọc: v5 tái lập pvlib hoàn hảo (câu 1 xong), và con số 12,35° là **bằng chứng định lượng vì
sao phải nâng cấp** — không phải "đổi cho sang" mà vì quy ước cũ sai thật quanh ngày đổi giờ.

---

## 3. Câu 2 — "Ban ngày" có đúng ban ngày?

Pipeline có hai định nghĩa ban ngày tồn tại song song:
- `is_daylight` (từ dữ liệu thời tiết, độ phân giải GIỜ) — dùng khi chấm điểm;
- `sin_elevation > 0,05` (hình học, 15 phút) — cổng chọn dòng vào huấn luyện.

Notebook vẽ sản lượng THẬT của một ngày hè và một ngày đông, tô chồng hai vùng "ban ngày"
lên, kèm thước đo: **% điện năng nằm NGOÀI mỗi vùng**. Kết quả toàn tập train: chỉ
**0,0492%** điện nằm ngoài `is_daylight` và **0,0788%** ngoài cổng hình học — hai định nghĩa
đều ôm sát thực tế, phần lệch chỉ ở rìa bình minh/hoàng hôn.

Hình này còn có vạch đỏ đánh dấu quy ước cổ xưa nhất (5:30/18:30 cố định) — mùa hè trạm còn
phát điện tới ~20:30, tức quy ước đồng hồ cố định sẽ chém mất 2 tiếng buổi tối. Một hình
chứng minh được cả vì sao KHÔNG dùng giờ cố định.

---

## 4. Câu 3 — Vì sao cắt vùng rìa: nhãn "nổ" khi chia cho số bé

Nhãn huấn luyện là `k = y / (site_scale × sin)`. Khi mặt trời sát chân trời, `sin → 0`,
mẫu số → 0, và k nổ tung. Bảng đo theo từng khoảng sin:

| Khoảng sin | Số dòng | % điện năng | k lớn nhất | % dòng vượt trần nhãn |
|---|---|---|---|---|
| 0 – 0,02 | 2.416 | 0,016% | **19.573** (!) | **29,9%** |
| 0,02 – 0,05 | 6.358 | 0,054% | 16,0 | 1,5% |
| 0,4 – 0,7 (giữa ngày) | 253.627 | 44,1% | 2,0 | 2,0% |

Đọc bảng: vùng rìa chỉ mang **0,07% điện năng** nhưng chứa những nhãn lớn gấp chục nghìn
lần bình thường. Giữ chúng thì: (a) mô hình học nhiễu, (b) ngưỡng cắt nhãn (tính theo phân
vị trên toàn tập) bị kéo méo, hại lây sang 99,93% dữ liệu tử tế. Cắt ở `sin ≤ 0,05` là đổi
0,07% điện lấy thang chuẩn hóa sạch — một trao đổi có lợi áp đảo, và giờ có số để chứng minh.

Lưu ý cách trình bày: các hình "phân phối + ngưỡng" trong dự án vẽ bằng **đường tích lũy
(CDF)** — phần trăm bị cắt đọc thẳng trên trục dọc. Histogram trục log từng gây hiểu nhầm
nghiêm trọng ("tưởng cắt mất nửa dữ liệu" trong khi thực tế 1%) nên đã bị thay.

---

## 5. Khi nào chạy notebook này

Sau 03_2 (cần feature spatial) và sau 05 (hai cell cuối đọc `v5_train_selected`). Không nằm
trong chuỗi 00→08; chạy lúc nào cũng được để kiểm chứng lại.
