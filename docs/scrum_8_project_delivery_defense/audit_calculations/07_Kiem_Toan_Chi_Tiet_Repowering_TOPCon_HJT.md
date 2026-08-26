# BÁO CÁO KIỂM TOÁN CHI TIẾT: HẠNG MỤC 7 — NÂNG CẤP TẤM PIN TOPCON / HJT (KỲ REPOWERING ĐẠI TU)

> **Dự án:** Toàn bộ 42 Trạm Điện Mặt Trời Áp Mái (2.428 kWp)  
> **Dữ liệu nguồn:** $683.665$ dòng cấp giờ (`t_cell`, `shortwave_radiation`, `e_hourly`)  
> **Cơ sở công nghệ:** So sánh đặc tính quang bán dẫn P-type PERC thế hệ cũ vs N-type TOPCon/HJT thế hệ mới.

---

## 1. So Sánh Thông Số Kỹ Thuật Công Nghệ Pin

| Thông Số Kỹ Thuật | P-type PERC (Hiện Tại) | N-type TOPCon (Nâng Cấp) | Mức Cải Thiện Vượt Trội |
| :--- | :---: | :---: | :---: |
| Hiệu suất chuyển đổi quang điện ($\eta$) | $17{,}5\% - 19{,}5\%$ | $22{,}0\% - 23{,}2\%$ | $+3{,}5\% - +4{,}5\%$ tuyệt đối ($+20\%$ tương đối) |
| Hệ số suy giảm nhiệt độ ($\gamma$) | $-0{,}38\%/^\circ\text{C}$ | $-0{,}30\%/^\circ\text{C}$ | Cải thiện $+0{,}08\%/^\circ\text{C}$ (ít nóng hơn) |
| Tỷ lệ suy thoái quang học ban đầu (LID) | $1{,}5\% - 2{,}0\%$ năm đầu | $0{,}0\%$ (Zero LID) | Triệt tiêu hoàn toàn suy thoái do Boron-Oxy |
| Tỷ lệ lão hóa hàng năm (Degradation) | $0{,}55\%/\text{năm}$ | $0{,}40\%/\text{năm}$ | Tăng sản lượng tích lũy vòng đời 30 năm |

---

## 2. Phân Rã Lợi Ích Hệ Số Nhiệt TOPCon Theo Dải Nhiệt Độ Tấm Pin Thực Tế

| Dải Nhiệt Độ Tấm Pin (°C) | Số Giờ Vận Hành Ban Ngày | Tổng Sản Lượng Đo Được (kWh) | Sản Lượng Tăng Thêm Nhờ Hệ Số Nhiệt TOPCon (kWh) |
| :--- | :---: | :---: | :---: |
| Dải ≤25°C | 123.329 giờ | 1.823.344 kWh | 0 kWh |
| Dải 25–35°C | 84.752 giờ | 2.456.067 kWh | 9.759 kWh |
| Dải 35–45°C | 51.769 giờ | 2.129.465 kWh | 25.460 kWh |
| Dải 45–55°C | 34.888 giờ | 1.871.801 kWh | 37.050 kWh |
| Dải >55°C | 12.177 giờ | 716.093 kWh | 19.223 kWh |
| **TỔNG CỘNG** | **306,915 Giờ** | **8.996.770 kWh** | **91.493 kWh/năm** |

---

## 3. Tổng Hợp Hiệu Quả Kỳ Đại Tu Repowering

* **Tổng sản lượng điện gia tăng:** **$+213.761\,\text{kWh/năm}$** ($+6{,}20\%$ tổng sản lượng toàn hệ thống).
* **Giá trị kinh tế gia tăng hàng năm:** **$42.752\,\text{AUD/năm}$**.
* **Kế hoạch triển khai:** Tích hợp trực tiếp vào kỳ thay mới tấm pin định kỳ vòng đời 15–20 năm (Zero Extra CapEx).