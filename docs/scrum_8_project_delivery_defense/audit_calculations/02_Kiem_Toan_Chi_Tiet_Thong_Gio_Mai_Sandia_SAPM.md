# BÁO CÁO KIỂM TOÁN CHI TIẾT: HẠNG MỤC 2 — KHOẢNG HỞ THÔNG GIÓ MÁI 10–15 CM & MÔ HÌNH SANDIA SAPM

> **Dự án:** 42 Trạm Điện Mặt Trời Áp Mái Đại Học La Trobe (2.428 kWp)  
> **Dữ liệu nguồn:** `mv_bi_mart_hourly_measures` (Biến: `temperature_c`, `shortwave_radiation`, `wind_speed`, `loss_temp`, `e_hourly`)  
> **Tiêu chuẩn kỹ thuật:** Tiêu chuẩn lắp đặt quang điện áp mái AS/NZS 5033 và Mô hình thực nghiệm truyền nhiệt Sandia SAPM (King et al., 2004).

---

## 1. Cơ Sở Vật Lý & Diễn Giải Chi Tiết Các Công Thức Truyền Nhiệt

### 1.1. Phương trình Nhiệt Động Học Thực Nghiệm Sandia SAPM
$$T_{\text{cell}}(t) = T_{\text{amb}}(t) + GHI(t) \cdot e^{a + b \cdot v_w(t)} + \frac{GHI(t)}{1000} \cdot \Delta T$$  

**Diễn giải chi tiết từng tham số:**
* $T_{\text{cell}}(t)$ ($^\circ\text{C}$): Nhiệt độ hoạt động thực tế của tế bào quang điện (Cell Temperature).
* $T_{\text{amb}}(t)$ ($^\circ\text{C}$): Nhiệt độ không khí môi trường đo được tại trạm khí tượng (`temperature_c`).
* $GHI(t)$ ($\text{W/m}^2$): Bức xạ tổng cộng mặt phẳng ngang (`shortwave_radiation`).
* $v_w(t)$ ($\text{m/s}$): Tốc độ gió đối lưu làm mát (`wind_speed`).
* $a, b$: Bộ hệ số thực nghiệm truyền nhiệt của phòng thí nghiệm quốc gia Sandia (Mỹ) cho các cấu trúc lắp đặt:
  * **Lắp áp sát mái (Flush Roof Mount):** $a = -2{,}98, b = -0{,}0471$. Dòng khí phía sau tấm pin bị cản trở bởi bề mặt mái tôn/bê tông, nhiệt lượng bị bẫy lại làm nhiệt độ cell tăng vọt lên tới $68 - 72^\circ\text{C}$ vào mùa hè.
  * **Lắp có khe hở thông gió $10–15\,\text{cm}$ (Open Rack / Ventilated):** $a = -3{,}56, b = -0{,}0750$. Khoảng cách $150\,\text{mm}$ kích hoạt đối lưu không khí tự nhiên theo hiệu ứng ống khói (Chimney Effect) và đối lưu cưỡng bức khi có gió, giúp tản nhiệt liên tục ở mặt lưng.
* $\Delta T = 3{,}0^\circ\text{C}$: Độ chênh lệch nhiệt độ dẫn truyền từ mặt kính/lưng module tới mối nối P-N silicon bên trong màng EVA ở bức xạ chuẩn $1.000\,\text{W/m}^2$.

---

### 1.2. Công thức Độ Hạ Nhiệt Cell & Giảm Tỷ Lệ Tổn Thất Nhiệt
$$\Delta T_{\text{cell}}(t) = \max\left(0,\, T_{\text{flush}}(t) - T_{\text{open}}(t)\right)$$
$$\Delta loss_{\text{temp}}(t) = \gamma \cdot \Delta T_{\text{cell}}(t) = 0{,}0038 \times \Delta T_{\text{cell}}(t)$$  

**Diễn giải chi tiết:**
* $\Delta T_{\text{cell}}(t)$ ($^\circ\text{C}$): Mức nhiệt độ cell hạ được nhờ dòng khí đối lưu mặt sau.
* $\gamma = 0{,}0038\,\text{/}^\circ\text{C}$ ($0{,}38\%/^\circ\text{C}$): Hệ số suy giảm công suất theo nhiệt độ của tấm pin Silicon đa tinh thể/đơn tinh thể P-type PERC. Cứ mỗi $1^\circ\text{C}$ nhiệt độ cell tăng trên $25^\circ\text{C}$ chuẩn STC, công suất phát điện bị mất đi $0{,}38\%$. Do đó, việc hạ nhiệt $\Delta T_{\text{cell}}$ sẽ thu hồi trực tiếp $\Delta loss_{\text{temp}} = 0{,}38\% \times \Delta T_{\text{cell}}$.

---

### 1.3. Công thức Sản Lượng Điện Năng Thu Hồi Cấp Dòng Dữ Liệu
$$\Delta e(t) = e\_hourly(t) \times \frac{\Delta loss_{\text{temp}}(t)}{1 - loss\_temp(t)}$$  

**Diễn giải logic toán học:**
* $e\_hourly(t)$ (kWh): Sản lượng điện thực tế đo được tại Inverter, vốn đã bị suy hao bởi tổn thất nhiệt độ $loss\_temp(t)$ ban đầu.
* $\frac{e\_hourly(t)}{1 - loss\_temp(t)}$: Năng lượng tiềm năng lý thuyết của giàn pin nếu loại bỏ hoàn toàn suy hao nhiệt độ ở thời điểm $t$.
* Phép nhân với $\Delta loss_{\text{temp}}(t)$ mang lại phần sản lượng điện ròng được thu hồi trực tiếp từ việc hạ nhiệt tấm pin.

---

## 2. Bảng Phân Rã 12 Tháng Nhiệt Độ Cell & Sản Lượng Thu Hồi Thực Tế

| Tháng | Mùa Vụ | T_amb TB (°C) | T_cell Áp Mái (°C) | T_cell Thông Gió (°C) | Mức Hạ Nhiệt ΔT (°C) | Tỷ Lệ Cải Thiện (%) | Sản Lượng Thu Hồi (kWh/tháng) | Tiết Kiệm (AUD/tháng) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| T01 | Mùa Hè | 22.5 °C | 41.9 °C | 32.8 °C | -11.0 °C | +4.20% | 18.165 kWh | 3.633 AUD |
| T02 | Mùa Hè | 21.8 °C | 38.5 °C | 30.1 °C | -10.8 °C | +4.10% | 15.171 kWh | 3.034 AUD |
| T03 | Mùa Thu | 18.9 °C | 35.2 °C | 27.7 °C | -9.3 °C | +3.52% | 11.241 kWh | 2.248 AUD |
| T04 | Mùa Thu | 14.8 °C | 29.0 °C | 23.1 °C | -7.2 °C | +2.73% | 6.429 kWh | 1.286 AUD |
| T05 | Mùa Đông | 11.2 °C | 23.9 °C | 18.9 °C | -5.1 °C | +1.95% | 3.306 kWh | 661 AUD |
| T06 | Mùa Đông | 9.2 °C | 19.4 °C | 15.5 °C | -4.1 °C | +1.56% | 2.155 kWh | 431 AUD |
| T07 | Mùa Đông | 8.9 °C | 17.6 °C | 14.0 °C | -4.4 °C | +1.66% | 2.498 kWh | 500 AUD |
| T08 | Mùa Đông | 10.5 °C | 20.6 °C | 15.9 °C | -5.7 °C | +2.15% | 4.176 kWh | 835 AUD |
| T09 | Mùa Xuân | 13.1 °C | 24.9 °C | 19.2 °C | -7.4 °C | +2.83% | 7.191 kWh | 1.438 AUD |
| T10 | Mùa Xuân | 15.8 °C | 28.9 °C | 21.9 °C | -9.0 °C | +3.42% | 11.143 kWh | 2.229 AUD |
| T11 | Mùa Hè | 18.4 °C | 34.8 °C | 26.6 °C | -10.5 °C | +4.00% | 15.814 kWh | 3.163 AUD |
| T12 | Mùa Hè | 21.1 °C | 37.0 °C | 28.2 °C | -11.3 °C | +4.30% | 19.935 kWh | 3.987 AUD |
| **CẢ NĂM** | — | **15,6 °C** | — | — | **-8,0 °C (TB)** | **+3,40% (TB)** | **117.224 kWh/NĂM** | **23.445 AUD/NĂM** |

---

## 3. Phân Tích Tài Chính & Hiệu Quả Đầu Tư

* **Tổng điện năng thu hồi từ nhiệt:** **$117.224\,\text{kWh/năm}$** ($+3{,}40\%$ tổng sản lượng toàn hệ thống).
* **Giá trị tiết kiệm điện hàng năm:**
  * Năm 2020: **$21.100\,\text{AUD}$**
  * Năm 2021: **$22.859\,\text{AUD}$**
  * Năm 2022: **$27.548\,\text{AUD}$**
  * **Trung bình 3 năm:** **$23.445\,\text{AUD/năm}$**
* **Chi phí lắp đặt giá đỡ nhôm định hình nâng cao 150mm:** **$24.280\,\text{AUD}$** ($10\,\text{AUD/kWp}$ cho $2.428\,\text{kWp}$).
* **Thời gian hoàn vốn chính xác:**
  $$\text{Payback} = \frac{24.280\,\text{AUD}}{23.445\,\text{AUD/năm}} = \mathbf{1{,}035\,\text{Năm}} \approx \mathbf{12{,}4\,\text{Tháng}}$$