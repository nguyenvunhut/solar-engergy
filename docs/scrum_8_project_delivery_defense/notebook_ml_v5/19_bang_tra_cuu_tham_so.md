# Bảng tra cứu — mọi tham số cố định của nhánh ML và nguồn gốc

> Số trong bảng này là **giá trị hiện hành (lượt chạy 20/08 chiều)**. Nếu gặp con số khác
> trong tài liệu hoặc notebook cũ, xem [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md).

## 1. Tham số và bằng chứng

| Tham số | Giá trị | Ở đâu | Suy ra thế nào | Bằng chứng thực nghiệm |
|---|---|---|---|---|
| `eps_elev` | 0,05 | features.yaml | Sàn chống chia cho số gần 0 trong mẫu số | TN1: hoà trong nhiễu (chênh 0,041 < 3σ = 0,222) → chọn theo ràng buộc vật lý: ở `eps=0` nhãn `k` nổ tới 19.573 và kéo lệch ngưỡng cắt +0,71% |
| `clip_phan_vi` | 0,99 | train.yaml | Trần cắt nhãn = phân vị 0,99 của `k` **trên train**; con số tự đổi theo dữ liệu (nay 1,3587) | TN2 (quét 0,90→1,00, có mức "không cắt" làm đối chứng) + TN2b (3 hạt giống, thứ hạng đảo → nhiễu) + TN6 (đối chiếu chéo, chênh 0,0005) |
| `tran_cong_suat_he_so` | 1,02 | train.yaml | Rào an toàn khi nhân ngược về kWh | TN3: chênh 0,0011 điểm giữa 1,00 và 1,10 — hoà tuyệt đối; 05f: tỷ lệ đo/trần cao nhất **1,007** → rào chưa từng kích hoạt |
| **`che_do_trong_so`** | **`mau_so`** | train.yaml | `ŷ−y = mẫu_số×(k̂−k)` ⇒ MAE có trọng số mẫu_số = tử số WAPE | TN11: C thắng B 0,15 điểm và có thiên lệch thấp nhất (+0,107 so với +0,170 và +0,453) |
| `he_so_trong_so_dinh` | 0,0 | train.yaml | **Nút đã chết** sau khi chuyển sang `mau_so` | TN4 cho 4 giá trị y hệt nhau — bằng chứng cơ chế cũ đã gỡ khỏi đường tính |
| `clip_csi` | 1,5 | features.yaml | Trần chỉ số trời quang khi hạ bức xạ về 15 phút | TN5 (đo % điểm bị cắt từng mức) + 05f TN4 |
| `quantile_scale` | 0,99 | features.yaml | `site_scale` = phân vị 99 sản lượng trạm | 05c: thắng 8 phương án khác, hơn công thức Lonij (2012) **3,07 điểm** |
| `quantile_tran` | 0,999 | features.yaml | `tran_cong_suat` | *Chưa có thực nghiệm riêng — hạn chế đã ghi nhận* |
| `quantile_cs_factor` | 0,98 | features.yaml | Hệ số hiệu chỉnh trời quang từng trạm | 05f TN3 xét hệ quả; mức phân vị chưa quét riêng |
| Ngưỡng góc cao cho `cs_factor` | 10° | notebook 03_2 | Dưới góc này chỉ số trời quang mất tin cậy | Đo thật: phân vị 98 của tỷ lệ lúc 19h = 3,2 so với 1,0–1,1 giữa trưa; 2 công bố quốc tế |
| Hằng số Haurwitz | 1098 / **0,059** | notebook 03_2 (qua pvlib) | Mô hình bức xạ trời quang | Haurwitz (1945); 05f TN2 ước lượng lại; khớp `pvlib.clearsky.haurwitz` 0,0000 W/m² |
| `lags` / `rolling` | (4, 96) | features.yaml | 1 giờ và 24 giờ | Audit trễ pha 31/07: `lag_1` khiến 39/40 trạm trễ → loại; `lag_4` sạch 0/40 |
| `TOP_K_FEATURES` | 35 (+ bảo vệ = **39**) | notebook 05 | Cắt bảng xếp hạng Mutual Information | TN8: K=35 là **argmin**, chênh 0,0000 so với mức đang dùng |
| `N_TRIALS` | 20 | notebook 06 | Ngân sách Optuna | TN7 (cuối 06_4): đường hội tụ phẳng sau ~10 trial |
| `δ` của Huber | tự suy | notebook 06_2 | `δ = 1,345 × MAD(phần dư train ngoài mẫu)` | Quy tắc Huber (1964) cho 95% hiệu quả tiệm cận |
| Loại trạm 19, 24 | — | notebook 06 | Metadata `capacity_kw` sai 3–4 lần | Đo trên file gốc: tỷ lệ đo/trần trạm 19 có trung vị 1,43 và cực đại 4,92; sau ETL mới, 55,6% dòng đo của trạm 19 bị kẹp phẳng |
| σ nhiễu huấn luyện | **0,0741** | TN10 | 6 hạt giống, cùng cấu hình | Thước để phán quyết mọi so sánh khác (3σ = 0,2224) |

## 2. Ba con số hay bị nhầm

- **39** = số đặc trưng được chọn ở notebook 05 (`selected_features.json`).
- **52** = số đặc trưng thực sự vào LightGBM = 39 + **13** cột `_mt` *(trước là 14 → 53; xem file 20 để biết vì sao giảm)*.
- **48** = số **cột** trong file `*_selected.parquet` = 39 đặc trưng + 9 cột phụ (không vào mô hình).

## 3. Hai con số về quy mô dữ liệu

- **42 trạm** — nhưng chỉ nằm ở **5 khuôn viên**, nên số mẫu độc lập về thời tiết thực chất
  là 5. Cần nêu trong mục hạn chế.
- **599.545 dòng × 52 đặc trưng** là ma trận huấn luyện thật của h1, từ 1.550.856 dòng ban
  đầu (sau các bộ lọc: loại đêm, thiếu lịch sử, dòng ETL điền, loại 2 trạm).

## 4. Tham số chưa có thực nghiệm riêng (hạn chế tự khai)

1. `quantile_tran = 0,999` — chưa quét mức phân vị.
2. `quantile_cs_factor = 0,98` — chưa quét mức phân vị.
3. Cận cắt `cs_factor [0,8 – 2,0]` — 05f mới xét hệ quả, chưa quét cận.
4. `losses.huber.alpha` — chỉ liên quan nếu chọn Huber làm quán quân (hiện MAE thắng).

Khai trước bốn điều này mạnh hơn nhiều so với để hội đồng tự tìm ra.
