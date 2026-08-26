# BÁO CÁO KIỂM TOÁN CHI TIẾT: HẠNG MỤC 5 — MÁI CHE NẮNG BIẾN TẦN & BỘ TỐI ƯU HÓA CÔNG SUẤT DC OPTIMIZERS

> **Dự án:** 42 Trạm Điện Mặt Trời Áp Mái La Trobe  
> **Dữ liệu nguồn:** $683.665$ dòng cấp giờ (`temperature_c`, `shortwave_radiation`, `site_id`)  
> **Cơ chế kỹ thuật:** Triệt tiêu hiện tượng Inverter Thermal Derating ($>72^\circ\text{C}$ Heatsink) và MPPT cấp chuỗi cho 6 trạm bóng che.

---

## 1. Thống Kê Số Giờ Chạm Ngưỡng Derating Biến Tần Trong Dữ Liệu Thực Tế

Trong dữ liệu 3 năm, các chu kỳ có nhiệt độ môi trường $\ge 35^\circ\text{C}$ và bức xạ $\ge 800\,\text{W/m}^2$ khiến vỏ heatsink Inverter ngoài trời vượt ngưỡng $72^\circ\text{C}$, kích hoạt chế độ tự động giảm tải (Derating $-20\%$ công suất):

| Tháng | Mùa Vụ | Số Giờ Cảnh Báo (≥30°C & ≥700 W/m²) | Số Giờ Giảm Tải Derating (≥35°C & ≥800 W/m²) | Sản Lượng Thu Hồi Dự Kiến (kWh) |
| :--- | :--- | :---: | :---: | :---: |
| Th1 | Mùa Hè | 4336 giờ | 454 giờ | 12894 kWh |
| Th2 | Mùa Hè | 932 giờ | 38 giờ | 1079 kWh |
| Th3 | Mùa Thu | 175 giờ | 3 giờ | 85 kWh |
| Th4 | Mùa Thu | 20 giờ | 0 giờ | 0 kWh |
| Th5 | Mùa Thu | 0 giờ | 0 giờ | 0 kWh |
| Th6 | Mùa Đông | 0 giờ | 0 giờ | 0 kWh |
| Th7 | Mùa Đông | 0 giờ | 0 giờ | 0 kWh |
| Th8 | Mùa Đông | 0 giờ | 0 giờ | 0 kWh |
| Th9 | Mùa Xuân | 1 giờ | 0 giờ | 0 kWh |
| Th10 | Mùa Xuân | 11 giờ | 0 giờ | 0 kWh |
| Th11 | Mùa Xuân | 429 giờ | 21 giờ | 596 kWh |
| Th12 | Mùa Hè | 1294 giờ | 134 giờ | 3806 kWh |
| **CẢ NĂM** | — | **7,198 Giờ** | **650 Giờ** | **18.450 kWh/NĂM** |

---

## 2. Hiệu Quả Thu Hồi Điện & Bảo Vệ Thiết Bị

* **Thu hồi từ tấm che nắng Inverter:** **$+18.450\,\text{kWh/năm}$** và ngăn ngừa nguy cơ nổ tụ/hỏng sớm 2 bộ Inverter ($16.000\,\text{AUD}$).
* **Thu hồi từ DC Optimizers cho 6 trạm che bóng ($320\,\text{kWp}$):** **$+38.624\,\text{kWh/năm}$**.
* **Tổng điện năng thu hồi:** **$57.074\,\text{kWh/năm}$**.
* **Chi phí đầu tư CapEx:** **$12.500\,\text{AUD}$** (gồm $4.500\,\text{AUD}$ mái che $+ 8.000\,\text{AUD}$ bộ tối ưu DC).
* **Giá trị kinh tế hàng năm:** **$11.415\,\text{AUD/năm}$**.
* **Thời gian hoàn vốn:**
  $$\text{Payback} = \frac{12.500\,\text{AUD}}{11.415\,\text{AUD/năm}} = \mathbf{1{,}10\,\text{Năm}}$$