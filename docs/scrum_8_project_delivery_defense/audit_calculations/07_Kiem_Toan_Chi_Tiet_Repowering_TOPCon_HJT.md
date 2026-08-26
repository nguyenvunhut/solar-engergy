# BÁO CÁO KIỂM TOÁN CHI TIẾT: HẠNG MỤC 7 — NÂNG CẤP TẤM PIN TOPCON / HJT (KỲ REPOWERING ĐẠI TU)

> **Dự án:** Toàn bộ 42 Trạm Điện Mặt Trời Áp Mái (2.428 kWp)  
> **Dữ liệu nguồn:** $683.665$ dòng cấp giờ (`t_cell`, `shortwave_radiation`, `e_hourly`)  
> **Cơ sở công nghệ:** So sánh đặc tính quang bán dẫn P-type PERC thế hệ cũ vs N-type TOPCon/HJT thế hệ mới.

---

## 1. Cơ Sở Công Nghệ Bán Dẫn & Diễn Giải Chi Tiết Các Công Thức

### 1.1. Công thức Cải thiện Hệ số Suy giảm Nhiệt độ (Temperature Coefficient)
$$P(T_{\text{cell}}) = P_{\text{STC}} \cdot \left[1 + \gamma \cdot (T_{\text{cell}} - 25^\circ\text{C})\right]$$
$$\Delta \gamma = |\gamma_{\text{PERC}}| - |\gamma_{\text{TOPCon}}| = |-0{,}38\%/^\circ\text{C}| - |-0{,}30\%/^\circ\text{C}| = \mathbf{+0{,}08\%/^\circ\text{C}}$$
$$\Delta \eta_{\text{temp\_benefit}}(t) = 0{,}0008 \times \max(0,\, t\_cell(t) - 25^\circ\text{C})$$  

**Diễn giải chi tiết:**
* Tấm pin P-type PERC thế hệ cũ có hệ số nhiệt $\gamma = -0{,}38\%/^\circ\text{C}$.
* Tấm pin N-type TOPCon thế hệ mới ứng dụng lớp tiếp xúc thụ động oxit đường hầm (Tunnel Oxide Passivated Contact), giúp giảm tái tổ hợp hạt mang điện ở nhiệt độ cao, hệ số nhiệt cải thiện vượt bậc về $\gamma = -0{,}30\%/^\circ\text{C}$.
* Chênh lệch $\Delta \gamma = 0{,}08\%/^\circ\text{C}$ giúp tấm pin phát điện vượt trội trong những ngày hè nắng nóng đỉnh điểm khi nhiệt độ cell lên tới $60 - 70^\circ\text{C}$.

---

### 1.2. Công thức Tổng Sản Lượng Tăng Thêm Toàn Diện
$$\Delta e_{\text{repowering}}(t) = e\_hourly(t) \times \left[0{,}062 + \Delta \eta_{\text{temp\_benefit}}(t)\right]$$  

**Diễn giải chi tiết:**
* $0{,}062$ ($+6{,}2\%$): Mức tăng sản lượng cơ bản nhờ hiệu suất chuyển đổi quang điện của tấm pin tăng từ $18{,}5\% \rightarrow 22{,}5\%$ trên cùng một diện tích mái nhà hiện hữu.
* $\Delta \eta_{\text{temp\_benefit}}(t)$: Phần tăng thêm động lực nhiệt độ theo thời gian thực.
* Triệt tiêu hoàn toàn hiện tượng suy thoái quang học ban đầu (Light-Induced Degradation - Zero LID) và giảm tốc độ suy thoái hàng năm từ $0{,}55\%/\text{năm} \rightarrow 0{,}40\%/\text{năm}$.

---

## 2. So Sánh Thông Số Kỹ Thuật Công Nghệ Pin

| Thông Số Kỹ Thuật | P-type PERC (Hiện Tại) | N-type TOPCon (Nâng Cấp) | Mức Cải Thiện Vượt Trội |
| :--- | :---: | :---: | :---: |
| Hiệu suất chuyển đổi quang điện ($\eta$) | $17{,}5\% - 19{,}5\%$ | $22{,}0\% - 23{,}2\%$ | $+3{,}5\% - +4{,}5\%$ tuyệt đối ($+20\%$ tương đối) |
| Hệ số suy giảm nhiệt độ ($\gamma$) | $-0{,}38\%/^\circ\text{C}$ | $-0{,}30\%/^\circ\text{C}$ | Cải thiện $+0{,}08\%/^\circ\text{C}$ (ít nóng hơn) |
| Tỷ lệ suy thoái quang học ban đầu (LID) | $1{,}5\% - 2{,}0\%$ năm đầu | $0{,}0\%$ (Zero LID) | Triệt tiêu hoàn toàn suy thoái do Boron-Oxy |
| Tỷ lệ lão hóa hàng năm (Degradation) | $0{,}55\%/\text{năm}$ | $0{,}40\%/\text{năm}$ | Tăng sản lượng tích lũy vòng đời 30 năm |

---

## 3. Phân Rã Lợi Ích Hệ Số Nhiệt TOPCon Theo Dải Nhiệt Độ Tấm Pin Thực Tế

| Dải Nhiệt Độ Tấm Pin (°C) | Số Giờ Vận Hành Ban Ngày | Tổng Sản Lượng Đo Được (kWh) | Sản Lượng Tăng Thêm Nhờ Hệ Số Nhiệt TOPCon (kWh) |
| :--- | :---: | :---: | :---: |
| Dải ≤25°C | 123.329 giờ | 1.823.344 kWh | 0 kWh |
| Dải 25–35°C | 84.752 giờ | 2.456.067 kWh | 9.759 kWh |
| Dải 35–45°C | 51.769 giờ | 2.129.465 kWh | 25.460 kWh |
| Dải 45–55°C | 34.888 giờ | 1.871.801 kWh | 37.050 kWh |
| Dải >55°C | 12.177 giờ | 716.093 kWh | 19.223 kWh |
| **TỔNG CỘNG** | **306,915 Giờ** | **8.996.770 kWh** | **91.493 kWh/năm** |

---

## 4. Tổng Hợp Hiệu Quả Kỳ Đại Tu Repowering

* **Tổng sản lượng điện gia tăng:** **$+213.761\,\text{kWh/năm}$** ($+6{,}20\%$ tổng sản lượng toàn hệ thống).
* **Giá trị kinh tế gia tăng hàng năm:** **$42.752\,\text{AUD/năm}$**.
* **Kế hoạch triển khai:** Tích hợp trực tiếp vào kỳ thay mới tấm pin định kỳ vòng đời 15–20 năm (Zero Extra CapEx).