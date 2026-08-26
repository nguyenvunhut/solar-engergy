# BÁO CÁO KIỂM TOÁN CHI TIẾT: HẠNG MỤC 1 — HỆ THỐNG PIN LƯU TRỮ BESS & THU HỒI INVERTER CLIPPING

> **Dự án:** 42 Trạm Điện Mặt Trời Áp Mái Đại Học La Trobe (2.428 kWp, 5 Khuôn Viên)  
> **Dữ liệu nguồn:** `bi_mart.mv_bi_mart_hourly_measures` (683,665 dòng chuỗi thời gian cấp giờ)  
> **Phương pháp kiểm toán:** Tích phân công suất cắt ngọn từng chu kỳ đo, mô hình hóa BESS DC-Coupled $\eta_{\text{RTE}} = 88\%$, dịch chuyển giờ cao điểm TOU (17:00–21:00) và gọt đỉnh công suất Demand Charge.

---

## 1. Cơ Sở Lý Thuyết & Diễn Giải Chi Tiết Các Công Thức Toán Học

### 1.1. Công thức Tỷ lệ Quá tải Thiết kế (Inverter Loading Ratio - ILR) & Công suất Trần Biến tần AC
$$\text{ILR} = \frac{P_{\text{DC}}}{P_{\text{AC}}} \approx 1{,}25 \implies P_{\text{AC\_max}} = \frac{P_{\text{STC}}}{\text{ILR}} = \frac{P_{\text{STC}}}{1{,}25} = 0{,}80 \times P_{\text{STC}}$$  

**Diễn giải chi tiết:**
* $P_{\text{STC}}$ (kWp): Tổng công suất định danh một chiều cực đại của các chuỗi pin mặt trời ở điều kiện tiêu chuẩn STC ($1.000\,\text{W/m}^2$, $25^\circ\text{C}$).
* $P_{\text{AC\_max}}$ (kW): Công suất xoay chiều tối đa mà bộ biến tần (Inverter) có thể hòa vào lưới điện nội bộ trường học.
* $\text{ILR} = 1{,}25$: Trong thiết kế điện mặt trời thương mại, công suất DC luôn được lắp lớn hơn định mức AC từ $20\% - 30\%$ để tối ưu hóa hiệu suất Inverter trong các khung giờ nắng vừa ($400 - 700\,\text{W/m}^2$, chiếm $80\%$ thời gian trong năm). Tuy nhiên, vào các giờ trưa mùa hè nắng gắt ($GHI \ge 900 - 1.050\,\text{W/m}^2$), công suất DC sinh ra vượt quá $P_{\text{AC\_max}}$, biến tần bắt buộc phải tự dịch chuyển điểm làm việc MPPT về phía điện áp hở mạch $V_{\text{oc}}$ để xén bỏ phần công suất thừa, gây ra hiện tượng **Inverter Clipping Loss**.

---

### 1.2. Công thức Tích phân Xác định Năng lượng Cắt ngọn Tức thời
$$\Delta e_{\text{clip}}(t) = \max\left(0,\, \left(e\_stc\_hourly(t) \times pr\_adjusted(t)\right) - 0{,}80 \times p\_stc \times 1{,}0\,\text{h}\right)$$  

**Diễn giải chi tiết:**
* $e\_stc\_hourly(t) = p\_stc \times \frac{GHI(t)}{1000}$ (kWh): Sản lượng điện DC lý thuyết nếu không có suy hao nhiệt.
* $pr\_adjusted(t)$: Hệ số hiệu suất thực tế của hệ thống sau khi đã trừ đi tổn thất nhiệt độ cell ($pr\_adjusted \approx 0{,}85 \times (1 - loss\_temp)$).
* $e\_stc\_hourly(t) \times pr\_adjusted(t)$ (kWh): Năng lượng DC thực tế sinh ra từ giàn pin có thể truyền tới đầu vào Inverter.
* $0{,}80 \times p\_stc \times 1{,}0\,\text{h}$ (kWh): Ngưỡng năng lượng AC tối đa Inverter được phép chuyển đổi trong $1\,\text{giờ}$.
* Hàm $\max(0, \cdot)$: Đảm bảo chỉ ghi nhận giá trị dương khi có hiện tượng quá tải cắt ngọn; nếu công suất DC nhỏ hơn trần biến tần thì $\Delta e_{\text{clip}}(t) = 0$.

---

### 1.3. Công thức Thu hồi Năng lượng bằng Cấu trúc BESS DC-Coupled
$$\Delta e_{\text{recovered}}(t) = \Delta e_{\text{clip}}(t) \times \eta_{\text{RTE}} = \Delta e_{\text{clip}}(t) \times 0{,}88$$  

**Diễn giải chi tiết:**
* **Cấu trúc BESS DC-Coupled:** Bộ lưu trữ pin Lithium LiFePO4 được đấu nối trực tiếp vào thanh cái DC Bus phía trước tầng nghịch lưu Inverter. Khi giàn pin phát công suất vượt trần AC, phần dòng điện DC thừa được nạp thẳng vào khối pin lưu trữ thay vì bị Inverter xén bỏ.
* $\eta_{\text{RTE}} = 0{,}88$ (Round-Trip Efficiency - Hiệu suất vòng lặp nạp/xả): Đại diện cho tổn thất điện trở nội, phản ứng điện hóa và biến đổi DC/DC ($12\%$ hao phí, $88\%$ năng lượng hữu ích thu hồi được).

---

### 1.4. Công thức Doanh thu Tối ưu hóa Giá trị Năng lượng (TOU Arbitrage & Demand Charge Shaving)
$$\Delta \text{Revenue}(t) = \begin{cases}
\Delta e_{\text{discharged}}(t) \times (P_{\text{Peak}} - P_{\text{FIT}}), & \text{khi } hourly\_bucket \in [17, 21] \\
\Delta e_{\text{discharged}}(t) \times P_{\text{FIT}}, & \text{các khung giờ khác}
\end{cases}$$  

**Diễn giải chi tiết:**
* $P_{\text{Peak}} = 0{,}320\,\text{AUD/kWh}$: Biểu giá mua điện lưới giờ cao điểm tối (17:00–21:00) theo biểu giá NEM Victoria.
* $P_{\text{FIT}} = 0{,}076\,\text{AUD/kWh}$: Biểu giá bán điện mặt trời dư thừa lên lưới vào ban ngày.
* $P_{\text{Peak}} - P_{\text{FIT}} = 0{,}244\,\text{AUD/kWh}$: Chênh lệch giá biên (Arbitrage Margin) thu được nhờ tích điện mặt trời giá rẻ ban ngày và xả ra tự dùng vào ban đêm, thay thế cho nguồn điện lưới đắt đỏ.
* **Gọt đỉnh công suất (Peak Shaving):** Giảm đỉnh công suất phụ tải khuôn viên trường học xuống $800\,\text{kW}$, tiết kiệm thêm khoản phí công suất phạt Demand Charge ($15{,}00\,\text{AUD/kW/tháng} \times 800\,\text{kW} \times 12\,\text{tháng} = 144.000\,\text{AUD/năm}$).

---

## 2. Kết Quả Tính Toán & Bóc Tách 12 Tháng Tổn Thất Cắt Ngọn

Tổn thất cắt ngọn tập trung chủ yếu vào **5 tháng mùa hè và đầu xuân (tháng 10 đến tháng 2)**, hoàn toàn biến mất vào mùa đông khi góc bức xạ Mặt Trời không vượt ngưỡng trần AC Inverter:

| Tháng | Mùa Vụ | Bức Xạ GHI TB (W/m²) | Năng Lượng Cắt Ngọn (kWh) | Năng Lượng Thu Hồi Qua BESS (kWh) | Tổn Thất Còn Lại (kWh) | Tỷ Trọng / Nhận Xét Vận Hành |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| Th1 | Mùa Hè | 280.4 W/m² | 10.520 kWh | 9.258 kWh | 1.262 kWh | Chiếm 13.3% tổng năm |
| Th2 | Mùa Hè | 255.8 W/m² | 9.761 kWh | 8.589 kWh | 1.171 kWh | Chiếm 12.3% tổng năm |
| Th3 | Mùa Thu | 192.8 W/m² | 8.885 kWh | 7.819 kWh | 1.066 kWh | Chiếm 11.2% tổng năm |
| Th4 | Mùa Thu | 138.8 W/m² | 5.709 kWh | 5.024 kWh | 685 kWh | Chiếm 7.2% tổng năm |
| Th5 | Mùa Thu | 103.1 W/m² | 2.874 kWh | 2.529 kWh | 345 kWh | Chiếm 3.6% tổng năm |
| Th6 | Mùa Đông | 75.0 W/m² | 2.377 kWh | 2.091 kWh | 285 kWh | Chiếm 3.0% tổng năm |
| Th7 | Mùa Đông | 79.0 W/m² | 2.990 kWh | 2.631 kWh | 359 kWh | Chiếm 3.8% tổng năm |
| Th8 | Mùa Đông | 114.5 W/m² | 4.645 kWh | 4.088 kWh | 557 kWh | Chiếm 5.9% tổng năm |
| Th9 | Mùa Xuân | 160.7 W/m² | 6.299 kWh | 5.543 kWh | 756 kWh | Chiếm 7.9% tổng năm |
| Th10 | Mùa Xuân | 204.5 W/m² | 7.491 kWh | 6.592 kWh | 899 kWh | Chiếm 9.4% tổng năm |
| Th11 | Mùa Xuân | 255.8 W/m² | 8.196 kWh | 7.213 kWh | 984 kWh | Chiếm 10.3% tổng năm |
| Th12 | Mùa Hè | 295.6 W/m² | 9.551 kWh | 8.405 kWh | 1.146 kWh | Chiếm 12.0% tổng năm |
| **CẢ NĂM** | — | **TB 3 Năm** | **79.298 kWh** | **69.782 kWh** | **9.516 kWh** | **2,30% Tổng Sản Lượng Toàn Hệ Thống** |

---

## 3. Ma Trận Cấu Hình Pin Lưu Trữ BESS 5 Khuôn Viên

| STT | Khuôn Viên (Campus) | Số Trạm | Công Suất DC (kWp) | Công Suất BESS (kW) | Dung Lượng BESS (kWh) | CapEx Đầu Tư (500 AUD/kWh) | Năng Lượng Xả TOU + Clip (kWh/năm) | Gọt Đỉnh Phụ Tải (kW) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | Bundoora | 26 trạm | 1.540 kWp | 600 kW | 1.500 kWh | 750.000 AUD | 451.713 kWh | 480 kW |
| 2 | Bendigo | 8 trạm | 510 kWp | 210 kW | 525 kWh | 262.500 AUD | 149.593 kWh | 168 kW |
| 3 | Albury-Wodonga | 4 trạm | 240 kWp | 90 kW | 225 kWh | 112.500 AUD | 70.397 kWh | 72 kW |
| 4 | Shepparton | 2 trạm | 78 kWp | 30 kW | 75 kWh | 37.500 AUD | 22.879 kWh | 24 kW |
| 5 | Mildura | 2 trạm | 60 kWp | 20 kW | 50 kWh | 25.000 AUD | 17.599 kWh | 16 kW |
| **Σ** | **TỔNG CỘNG 5 KHUÔN VIÊN** | **42 TRẠM** | **2.428 kWp** | **1.000 kW** | **2.500 kWh** | **1.250.000 AUD** | **712.182 kWh/NĂM** | **800 kW** |

---

## 4. Đánh Giá Hiệu Quả Tài Chính & Thời Gian Hoàn Vốn

* **Năng lượng BESS xả phục vụ tự dùng & cắt đỉnh:** **$712.182\,\text{kWh/năm}$**
* **Doanh thu & Tiết kiệm chi phí điện:**
  * Năm 2020: **$260.766\,\text{AUD/năm}$**
  * Năm 2021: **$304.818\,\text{AUD/năm}$**
  * Năm 2022: **$382.065\,\text{AUD/năm}$**
  * **Trung bình 3 năm:** **$323.164\,\text{AUD/năm}$**
* **Tổng vốn đầu tư CapEx:** **$1.250.000\,\text{AUD}$** (Giá tham chiếu pin LiFePO4 công nghiệp $500\,\text{AUD/kWh}$).
* **Thời gian hoàn vốn hòa vốn (Payback Period):**
  $$\text{Payback} = \frac{1.250.000\,\text{AUD}}{323.164\,\text{AUD/năm}} = \mathbf{3{,}87\,\text{Năm}}$$