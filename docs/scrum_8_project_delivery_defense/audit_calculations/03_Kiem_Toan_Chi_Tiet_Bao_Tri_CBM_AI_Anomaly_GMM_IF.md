# BÁO CÁO KIỂM TOÁN CHI TIẾT: HẠNG MỤC 3 — CHUYỂN ĐỔI BẢO TRÌ CBM & AI ANOMALY GMM-IF

> **Dự án:** 42 Trạm Điện Mặt Trời Áp Mái Đại Học La Trobe  
> **Dữ liệu nguồn:** Cờ dị thường `gmm_if_outlier_flag` (5,638 dòng bị gắn cờ) và trường phân loại `gmm_if_outlier_reason` trong `mv_bi_mart_hourly_measures`  
> **Tiêu chuẩn tham chiếu:** Báo cáo quốc tế IEA-PVPS Task 13 (Report T13-15:2023) và Clean Energy Council (CEC) Australia.

---

## 1. Cơ Sở Khoa Học & Diễn Giải Chi Tiết Các Công Thức AI CBM

### 1.1. Công thức Xác định Thiếu hụt Sản lượng Tức thời do Dị thường Vận hành
$$\Delta e_{\text{anomaly\_loss}}(t) = \begin{cases}
\max\left(0,\, e\_expected(t) - e\_hourly(t)\right), & \text{khi } gmm\_if\_outlier\_flag = \text{TRUE} \\
0, & \text{khi } gmm\_if\_outlier\_flag = \text{FALSE}
\end{cases}$$  

**Diễn giải chi tiết:**
* `gmm_if_outlier_flag`: Nhãn boolean do mô hình học máy lai Gaussian Mixture Model kết hợp Isolation Forest (GMM-IF) dự đoán. Nhãn TRUE chỉ định thời điểm trạm pin gặp sự cố kỹ thuật vật lý chứ không phải do thời tiết xấu.
* $e\_expected(t)$ (kWh): Sản lượng kỳ vọng bình thường của trạm ở điều kiện thời tiết thực tế tương ứng.
* $e\_hourly(t)$ (kWh): Sản lượng thực tế bị suy giảm do sự cố.
* $\Delta e_{\text{anomaly\_loss}}(t)$: Lượng điện năng bị bốc hơi tại chu kỳ $t$ do hư hỏng thiết bị.

---

### 1.2. Công thức Hệ số Cứu vãn Năng lượng (CBM Energy Salvage Factor) theo MTTR
$$f_{\text{cbm}} = 1 - \frac{\text{MTTR}_{\text{mới}}}{\text{MTTR}_{\text{cũ}}} = 1 - \frac{2\,\text{ngày}}{14\,\text{ngày}} = \mathbf{0{,}857 \; (85{,}7\%)}$$
$$\Delta e_{\text{recovered, cbm}}(t) = \Delta e_{\text{anomaly\_loss}}(t) \times f_{\text{cbm}}$$  

**Diễn giải cơ chế vận hành:**
* **Quy trình O&M truyền thống (Time-Based / Reactive):** Khi đứt cầu chì DC hoặc Inverter trip, không có cảnh báo vi mô. MTTD (phát hiện) mất $14 - 30\,\text{ngày}$, MTTR (sửa chữa) mất thêm $7 - 14\,\text{ngày}$. Tổng thời gian chết gián đoạn năng lượng kéo dài từ **$21 - 44\,\text{ngày}$**.
* **Quy trình AI CBM tự động hóa:** Pipeline phát hiện dị thường trong chu kỳ $15\,\text{phút}$ (MTTD $< 1\,\text{giờ}$). Hệ thống tự động đẩy Work Order tới thiết bị di động của kỹ sư chỉ rõ: Tên trạm, số tủ Combiner Box, nguyên nhân lỗi $\implies$ Kỹ sư mang đúng vật tư xử lý dứt điểm trong vòng **$1 - 3\,\text{ngày}$**.
* Nhờ rút ngắn thời gian sửa chữa từ $14\,\text{ngày}$ xuống $2\,\text{ngày}$, hệ thống bảo toàn và thu hồi được **$85{,}7\%$** lượng điện năng lẽ ra bị mất.

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