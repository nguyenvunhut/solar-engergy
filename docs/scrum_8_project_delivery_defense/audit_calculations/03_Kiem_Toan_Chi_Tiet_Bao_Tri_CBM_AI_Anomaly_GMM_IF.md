# BÁO CÁO KIỂM TOÁN CHI TIẾT: HẠNG MỤC 3 — CHUYỂN ĐỔI BẢO TRÌ CBM & AI ANOMALY GMM-IF

> **Dự án:** 42 Trạm Điện Mặt Trời Áp Mái Đại Học La Trobe  
> **Dữ liệu nguồn:** Cờ dị thường `gmm_if_outlier_flag` (5,638 dòng bị gắn cờ) và trường phân loại `gmm_if_outlier_reason` trong `mv_bi_mart_hourly_measures`  
> **Tiêu chuẩn tham chiếu:** Báo cáo quốc tế IEA-PVPS Task 13 (Report T13-15:2023) và Clean Energy Council (CEC) Australia.

---

## 1. Nguyên Lý Khắc Phục & Rút Ngắn Thời Gian Sửa Chữa (MTTR)

* **Quy trình truyền thống (Reactive / Time-Based O&M):**
  * MTTD (Mean Time to Detect): $14 - 30\,\text{ngày}$ mới phát hiện qua hóa đơn tiền điện hoặc báo cáo sản lượng quý.
  * MTTR (Mean Time to Repair): $7 - 14\,\text{ngày}$ do kỹ sư phải đến kiểm tra thủ công 42 trạm.
  * Tổng thời gian gián đoạn phát điện: **$21 - 44\,\text{ngày}$**.
* **Quy trình AI CBM tự động hóa:**
  * MTTD: $< 1\,\text{giờ}$ (phát hiện ngay trong chu kỳ $15\,\text{phút}$ của pipeline).
  * MTTR: **$1 - 3\,\text{ngày}$** nhờ Work Order tự động chỉ đích danh: Mã trạm, vị trí tủ Combiner Box, loại sự cố.
  * **Hệ số cứu vãn năng lượng:**
    $$f_{\text{cbm}} = 1 - \frac{\text{MTTR}_{\text{mới}}}{\text{MTTR}_{\text{cũ}}} = 1 - \frac{2\,\text{ngày}}{14\,\text{ngày}} = \mathbf{85{,}7\%}$$

---

## 2. Bóc Tách 6 Mã Cờ Dị Thường Vật Lý Trong Dữ Liệu Thực Tế

| STT | Mã Cờ Dị Thường Trong Code & DWH | Số Bản Ghi Gắn Cờ | Sản Lượng Hụt Đo Được (kWh) | Năng Lượng Cứu Vãn Qua CBM (kWh) | Hướng Dẫn Hành Động Kỹ Sư O&M |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | `GMM_IF_CONSENSUS` | 4.581 dòng | 11.639 kWh | 9.974 kWh | Đối soát đường cong I-V curve, quét camera nhiệt tìm tấm pin suy thoái hoặc bóng che cục bộ. |
| 2 | `PHYSICAL_DISTRIBUTION_JUMP` | 1.376 dòng | 4.238 kWh | 3.632 kWh | Dùng ampe kìm DC đo dòng chuỗi tại Combiner Box, thay cầu chì DC đứt (-33% công suất). |
| 3 | `PHYSICAL_LOW_ENERGY_STRONG_SUN` | 39 dòng | 80 kWh | 69 kWh | Kiểm tra rơ-le ngắt quá áp lưới AC (AS/NZS 4777.2 > 253V), chỉnh nấc MBA và vệ sinh quạt tản nhiệt Inverter. |
| 4 | `PHYSICAL_HIGH_ENERGY_LOW_RADIATION` | 110 dòng | 0 kWh | 0 kWh | Hiệu chỉnh lại điểm 0 (Zero Calibration) cảm biến biến dòng CT. |
| 5 | `PHYSICAL_HIGH_ENERGY_NO_SUN` | 30 dòng | 0 kWh | 0 kWh | Hiệu chỉnh điểm 0 cảm biến CT, kiểm tra cách điện tải tự dùng AC ban đêm. |
| **Σ** | **TỔNG CỘNG TOÀN BỘ SỰ CỐ** | **6,136 dòng** | **15.957 kWh** | **13.675 kWh** | **Thu hồi toàn diện các lỗi vận hành** |

---

## 3. Tổng Hợp Năng Lượng & Hiệu Quả Tài Chính CBM

* **Tổng điện năng thu hồi cả năm:** **$70.330\,\text{kWh/năm}$** ($+2{,}04\%$ tổng sản lượng toàn hệ thống).
* **Giá trị tài chính thu hồi hàng năm:**
  * Năm 2020: **$26.659\,\text{AUD}$**
  * Năm 2021: **$28.714\,\text{AUD}$**
  * Năm 2022: **$32.528\,\text{AUD}$**
  * **Trung bình 3 năm:** **$29.066\,\text{AUD/năm}$**
* **Chi phí duy trì AI CBM Platform & Drone IR Scan định kỳ:** **$8.000\,\text{AUD/năm}$**.
* **Thời gian hoàn vốn:** **$< 4\,\text{Tháng}$** (Dòng tiền dương ngay trong năm đầu tiên).