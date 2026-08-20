# Notebook 05f — Hợp lệ hoá các hằng số vật lý (`05f_hop_le_hoa_tham_so_hardcode.ipynb`)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy ngày 19/08 hoặc
> trưa 20/08. Giá trị **hiện hành** và lý do từng con số thay đổi được liệt kê đầy đủ ở
> [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md). Đọc file đó trước khi
> trích bất kỳ con số nào vào báo cáo.


## Khác gì 05b
- **05b**: quét tham số bằng cách **huấn luyện lại** và so điểm số.
- **05f**: **đo trực tiếp trên dữ liệu**, không huấn luyện gì. Dùng cho các hằng số vật lý mà
  điểm số mô hình không phải thước đo phù hợp.

- **Vào:** `03_2_features_spatial/v5_train_spatial.parquet`
- **Ra:** `05f_hop_le_hoa/hinh/*.png`

## Nguyên tắc tái lập
Cell đầu tiên in **mã băm MD5** của file dữ liệu đầu vào, cùng phiên bản pandas/numpy. Ai
chạy lại với cùng mã băm phải ra cùng số.

## Bốn thực nghiệm

### TN1 — hệ số nới trần công suất `1,02`
Tính tỷ lệ `sản lượng đo / trần công suất` trên toàn bộ dòng đo thật ban ngày, rồi đếm số
dòng vượt từng mức ngưỡng.

Kết quả (bản 19/08): phân vị 99,99% = 1,0023; **cao nhất 1,007**; số dòng vượt 1,01 = **0**.
Kết luận: 1,02 là **rào an toàn không bao giờ kích hoạt** trên dữ liệu này — chọn 1,01 hay
1,05 đều cho kết quả y hệt. Đây là cách trả lời mạnh nhất cho câu "sao lại 1,02": *mọi giá
trị ≥ 1,01 đều tương đương, chúng em lấy 1,02 để có 2% biên trên mức cực đại quan sát được*.

### TN2 — hằng số Haurwitz `1098` và `0,059`
Ước lượng lại hai hằng số từ chính dữ liệu 42 trạm và so với giá trị công bố năm 1945. Đồng
thời đối chiếu với bản cài đặt trong thư viện pvlib.

### TN3 — hệ số hiệu chỉnh `cs_factor` và cận cắt `[0,8 – 2,0]`
Hai câu hỏi: (a) cận cắt có bao giờ chạm không? (b) hệ số có bị thổi phồng không?
Phát hiện quan trọng: nếu lọc theo `ghi_cs > 50 W/m²` (cách cũ) thì **42/42 trạm** đều bị đẩy
chạm cận trên 2,0 → cột trở thành hằng số vô dụng. Đổi sang lọc theo **góc cao > 10°** thì
hiện tượng biến mất. Đây là một lỗi thật đã được phát hiện và sửa nhờ thực nghiệm này.

### TN4 — ngưỡng cắt chỉ số trời quang `CLIP_CSI = 1,5`
Vẽ phân bố chỉ số trời quang và đếm phần trăm bị cắt ở các mức 1,2 và 1,5.

### Hai thực nghiệm đối chứng
Kiểm tra hai điểm đính chính trong công thức có làm sai kết quả mô hình không — trả lời câu
"phát hiện ra lỗi rồi thì có phải chạy lại toàn bộ pipeline không?".

## Chuẩn trình bày hình
Mọi hình dạng "phân phối + ngưỡng" đều vẽ bằng **đường tích luỹ (CDF)** chứ không phải
histogram thang log. Lý do: với histogram thang log, một cột 10 điểm trông cao gần bằng cột
10.000 điểm, khiến người xem tưởng ngưỡng đang cắt mất **một nửa** dữ liệu trong khi thực tế
chỉ cắt 1%. Với CDF, phần trăm bị cắt đọc thẳng trên trục dọc, không thể hiểu nhầm.
