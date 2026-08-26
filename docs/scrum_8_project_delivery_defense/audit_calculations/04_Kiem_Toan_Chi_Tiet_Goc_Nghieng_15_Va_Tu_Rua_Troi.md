# BÁO CÁO KIỂM TOÁN CHI TIẾT: HẠNG MỤC 4 — NÂNG KHUNG NGHIÊNG 15° HƯỚNG BẮC CHO 970 kWp MÁI BẰNG

> **Dự án:** Nhóm 970 kWp Trạm Mái Bằng (Trong tổng số 2.428 kWp La Trobe)  
> **Sản lượng cơ sở nhóm mái bằng:** $1.377.400\,\text{kWh/năm}$  
> **Cơ sở khoa học:** Mô hình bức xạ mặt phẳng nghiêng Hay-Davies / NREL (Dobos, 2014) và Nghiên cứu bám bụi CSIRO Energy (2022).

---

## 1. Cơ Sở Hình Học Quang Điện & Diễn Giải Chi Tiết Các Công Thức

### 1.1. Phương trình Bức xạ Mặt phẳng Nghiêng Hay-Davies Transposition Model
$$\cos(\theta_{15^\circ}(t)) = \sin(\alpha(t))\cos(15^\circ) + \cos(\alpha(t))\sin(15^\circ)\cos(\psi(t))$$
$$POA_{15^\circ}(t) = DNI(t) \cdot \cos(\theta_{15^\circ}(t)) + DHI(t) \cdot \left(\frac{1 + \cos(15^\circ)}{2}\right) + GHI(t) \cdot \rho_{\text{ground}} \cdot \left(\frac{1 - \cos(15^\circ)}{2}\right)$$  

**Diễn giải chi tiết:**
* Bang Victoria nằm ở vĩ độ $37^\circ\text{S}$ (Bán cầu Nam), hướng đón nắng tối ưu là hướng Bắc chính xác ($0^\circ\text{ Azimuth}$).
* $\alpha(t)$: Góc cao Mặt Trời (Solar Elevation Angle). Vào mùa đông, Mặt Trời đi rất thấp ($h \approx 29^\circ - 38^\circ$). Trên mái bằng ($0^\circ$), góc tới $\theta$ lên tới $60^\circ$, gây phản xạ quang học mặt kính rất lớn (Incidence Angle Modifier loss). Việc dựng khung nghiêng $15^\circ$ giúp mặt pin đón vuông góc với tia trực xạ $DNI$, tăng bức xạ hiệu dụng mùa đông lên **$+13{,}74\% \rightarrow +20{,}80\%$**.
* Vào mùa hè, Mặt Trời lên gần thiên đỉnh ($h \approx 72^\circ - 76^\circ$), góc nghiêng $15^\circ$ bị lệch nhẹ so với góc phẳng, làm sản lượng giảm nhẹ **$-1{,}16\% \rightarrow -1{,}55\%$**.
* **Cân bằng năng lượng cả năm:** Phần tăng đột biến mùa đông ($+44.436\,\text{kWh}$) vượt xa phần giảm nhẹ mùa hè ($-8.924\,\text{kWh}$), đem lại mức tăng ròng **$+53.350\,\text{kWh/năm}$** ($+3{,}90\%$ sản lượng cụm mái bằng).

---

### 1.2. Công thức Thu hồi Tổn thất Đọng Bùn Viền Nhôm Đáy (Mud-Damming Self-Cleaning)
$$\Delta e_{\text{self\_cleaning}}(t) = 0{,}0134 \times e\_hourly(t) \implies \mathbf{18.500\,\text{kWh/năm}}$$  

**Diễn giải cơ chế vật lý:**
* Trên mái bằng độ dốc $<8^\circ$, lực căng bề mặt giữ nước mưa đọng lại ở gờ nhôm đáy tấm pin, tạo thành dải bùn đất tích tụ (Mud Damming).
* Vệt bùn này che phủ hàng tế bào quang điện dưới cùng, kích hoạt Bypass Diode của tấm pin hoạt động liên tục, làm mất $33\%$ công suất của cả chuỗi pin.
* Khi nâng giàn khung nghiêng $15^\circ$, độ dốc trọng lực thắng hoàn toàn lực căng bề mặt. Mọi trận mưa rào $\ge 10\,\text{mm}$ tạo thành màng nước chảy xiết cuốn trôi $98\%$ bùn đất, giải phóng Bypass Diode và thu hồi trọn vẹn $18.500\,\text{kWh/năm}$.

---

## 2. Bảng Phân Tích Cân Bằng Năng Lượng 12 Tháng Chi Tiết

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

## 3. Tổng Hợp Hiệu Quả Kinh Tế & Hoàn Vốn

* **Tổng năng lượng thu hồi:** **$71.850\,\text{kWh/năm}$** (gồm $53.350\,\text{kWh}$ quang học $+ 18.500\,\text{kWh}$ tự làm sạch).
* **Tiết kiệm nhân công rửa pin:** **$4.000\,\text{AUD/năm}$** (giảm từ 4 lần xuống 1 lần rửa/năm).
* **Tổng giá trị tài chính:** **$14.670\,\text{AUD/năm}$**.
* **CapEx chân đế chữ A nhôm định hình:** **$18.000\,\text{AUD}$**.
* **Thời gian hoàn vốn hòa vốn:**
  $$\text{Payback} = \frac{18.000\,\text{AUD}}{14.670\,\text{AUD/năm}} = \mathbf{1{,}23\,\text{Năm}}$$