# BÁO CÁO KIỂM TOÁN CHI TIẾT: HẠNG MỤC 4 — NÂNG KHUNG NGHIÊNG 15° HƯỚNG BẮC CHO 970 kWp MÁI BẰNG

> **Dự án:** Nhóm 970 kWp Trạm Mái Bằng (Trong tổng số 2.428 kWp La Trobe)  
> **Sản lượng cơ sở nhóm mái bằng:** $1.377.400\,\text{kWh/năm}$  
> **Cơ sở khoa học:** Mô hình bức xạ mặt phẳng nghiêng Hay-Davies / NREL (Dobos, 2014) và Nghiên cứu bám bụi CSIRO Energy (2022).

---

## 1. Phép Tính Cân Bằng Năng Lượng 12 Tháng Khi Bẻ Góc Nghiêng 15°

Victoria nằm ở bán cầu Nam ($37^\circ\text{S}$), Mặt Trời vào mùa đông ở góc cao rất thấp ($h \approx 29^\circ - 38^\circ$). Khi nghiêng $15^\circ$ hướng Bắc ($0^\circ\text{ Azimuth}$):
* **Mùa đông (Tháng 5–8):** Đón vuông góc hơn, sản lượng tăng vọt **$+13{,}74\% \rightarrow +20{,}80\%$** (tổng tăng **$+44.436\,\text{kWh}$**).
* **Mùa hè (Tháng 11–2):** Mặt Trời gần đỉnh đầu ($h \approx 72^\circ - 76^\circ$), góc nghiêng $15^\circ$ bị lệch nhẹ, sản lượng giảm nhẹ **$-1{,}16\% \rightarrow -1{,}55\%$** (tổng giảm **$-8.924\,\text{kWh}$**).
* **Cân bằng năng lượng quang học cả năm:** Tăng ròng **$+53.350\,\text{kWh/năm}$** ($+3{,}90\%$ nhóm $970\,\text{kWp}$).

| Tháng | Mùa Vụ | Góc Cao Mặt Trời Trưa (h) | Sản Lượng Cơ Sở (kWh/tháng) | Tỷ Lệ Tăng/Giảm (%) | Sản Lượng Tăng/Giảm (kWh/tháng) | Giá Trị Tài Chính (AUD) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| T01 | Mùa Hè | 75,5 ° | 172.801 kWh | -1,45% | -2.508 kWh | -502 AUD |
| T02 | Mùa Hè | 68,0 ° | 147.757 kWh | -1,16% | -1.715 kWh | -343 AUD |
| T03 | Mùa Thu | 56,5 ° | 127.723 kWh | +1,74% | +2.224 kWh | +445 AUD |
| T04 | Mùa Thu | 44,5 ° | 93.914 kWh | +8,22% | +7.723 kWh | +1.545 AUD |
| T05 | Mùa Đông | 34,0 ° | 67.618 kWh | +15,96% | +10.795 kWh | +2.159 AUD |
| T06 | Mùa Đông | 29,0 ° | 55.096 kWh | +20,80% | +11.461 kWh | +2.292 AUD |
| T07 | Mùa Đông | 31,5 ° | 60.105 kWh | +19,16% | +11.514 kWh | +2.303 AUD |
| T08 | Mùa Đông | 39,5 ° | 77.635 kWh | +13,74% | +10.666 kWh | +2.133 AUD |
| T09 | Mùa Xuân | 51,0 ° | 101.427 kWh | +6,29% | +6.379 kWh | +1.276 AUD |
| T10 | Mùa Xuân | 63,5 ° | 130.227 kWh | +1,16% | +1.512 kWh | +302 AUD |
| T11 | Mùa Hè | 72,5 ° | 157.775 kWh | -1,16% | -1.832 kWh | -366 AUD |
| T12 | Mùa Hè | 76,5 ° | 185.323 kWh | -1,55% | -2.869 kWh | -574 AUD |
| **CẢ NĂM** | — | — | **1.377.400 kWh** | **+3,90%** | **+53.350 kWh** | **+10.670 AUD/NĂM** |

---

## 2. Ước Tính Lợi Ích Cơ Chế Tự Rửa Trôi Bùn Đọng Viền Đáy (Self-Cleaning)

* **Cơ chế:** Góc nghiêng $\ge 15^\circ$ giúp nước mưa $\ge 10\,\text{mm}$ tạo màng chảy cuốn trôi $95\% - 98\%$ bụi bẩn, triệt tiêu hiện tượng dải bùn đọng ở gờ nhôm đáy tấm pin (Mud Damming).
* **Định lượng lợi ích:**
  1. **Tiết kiệm chi phí nhân công rửa:** Cắt giảm từ 4 lần/năm xuống 1 lần/năm $\implies$ **Tiết kiệm trực tiếp $4.000\,\text{AUD/năm}$**.
  2. **Thu hồi tổn thất do Bypass Diode:** Triệt tiêu vệt che hàng cell đáy, thu hồi **$+18.500\,\text{kWh/năm} \implies +3.700\,\text{AUD/năm}$**.
  3. **Tổng sản lượng thu hồi (Quang học + Tự làm sạch):** **$71.850\,\text{kWh/năm}$**.
* **CapEx đầu tư chân đỡ chữ A:** **$18.000\,\text{AUD}$**.
* **Thời gian hoàn vốn hòa vốn:**
  $$\text{Payback} = \frac{18.000\,\text{AUD}}{14.670\,\text{AUD/năm}} = \mathbf{1{,}23\,\text{Năm}}$$