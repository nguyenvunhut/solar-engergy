# BRIEF THIẾT KẾ & ĐẶC TẢ KỸ THUẬT: STREAMLIT WHAT-IF OPTIMIZATION DASHBOARD
## HỆ THỐNG MÔ PHỎNG KỊCH BẢN TỐI ƯU HÓA HIỆU SUẤT & TÀI CHÍNH 42 TRẠM ĐIỆN MẶT TRỜI

> **Dự án:** Hệ thống Xử lý Dữ liệu, Nhận diện Dị thường Vận hành và Phân tích Kinh doanh 42 Trạm Điện Mặt Trời Áp mái (Đại học La Trobe, Bang Victoria, Úc)  
> **Nhóm thực hiện:** The Outliers — Chuyên ngành Xử lý Dữ liệu (Data Analytics / FPT Polytechnic)  
> **Tài liệu tham chiếu:** 
> - [`Hiệu Suất Điện Mặt Trời.md`](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/docs/scrum_8_project_delivery_defense/Hi%E1%BB%87u%20Su%E1%BA%A5t%20%C4%90i%E1%BB%87n%20M%E1%BA%B7t%20Tr%E1%BB%9Di.md)
> - [`2026_08_25_Bao_Cao_Dinh_Luong_Chi_Tiet_Insights_Va_De_Xuat_Cai_Tien_Audited.md`](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/docs/scrum_8_project_delivery_defense/2026_08_25_Bao_Cao_Dinh_Luong_Chi_Tiet_Insights_Va_De_Xuat_Cai_Tien_Audited.md)
> - [`2026_08_23_Tong_Hop_Hang_So_Va_Ty_Le_Chung_Du_An.md`](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/docs/scrum_8_project_delivery_defense/2026_08_23_Tong_Hop_Hang_So_Va_Ty_Le_Chung_Du_An.md)

---

## 1. MỤC TIÊU & TỔNG QUAN TRANG DASHBOARD STREAMLIT

### 1.1. Mục tiêu Nghiệp vụ
Xây dựng một trang ứng dụng tương tác **What-If Scenario Simulation & Optimization Dashboard** trên nền tảng **Streamlit**, cho phép Hội đồng Phản biện, Ban Quản lý Năng lượng (C-Level, O&M Managers) và Kỹ sư Vận hành:
1. **Quan sát Hiện trạng Lịch sử (Historical Baseline)**: Nắm bắt toàn bộ các chỉ số vận hành thực tế ($2.731.946$ bản ghi, $2.428\,\text{kWp}$, $42$ trạm áp mái) trước khi thực hiện cải tiến.
2. **Mô phỏng Động Đa Kịch bản (Dynamic Reactive Simulation)**: Tích chọn từng ô Checkbox tương ứng với **7 hạng mục đề xuất kỹ thuật & O&M** của nhóm nghiên cứu.
3. **Cập nhật Tức thì (Real-time Metric Re-calculation)**: Khi tích/hủy bất kỳ hạng mục nào, toàn bộ hệ số hiệu suất ($PR$), sản lượng ($E$), hệ số tải ($CF$), các thành phần tổn thất ($Loss_{\text{temp}}$, $Loss_{\text{clip}}$, $Loss_{\text{soiling}}$, $Loss_{\text{anomaly}}$), doanh thu/tiết kiệm ($\text{AUD}$) và chỉ số phát thải môi trường ($\text{CO}_2$) sẽ thay đổi ngay lập tức theo các hàm công thức vật lý & kinh tế định lượng chuẩn xác.
4. **Bảng Kết quả Tổng hợp & Bóc tách Từng Hạng mục**: Đánh giá chi phí đầu tư ($\text{CapEx}$), lợi ích tài chính gia tăng hàng năm ($\Delta \text{Revenue}$), thời gian hoàn vốn ($\text{Payback Period}$) và tỷ suất sinh lời ($\text{ROI}$) chi tiết cho từng giải pháp.

---

## 2. BỘ THÔNG SỐ CƠ SỞ LỊCH SỬ (HISTORICAL BASELINE METRICS)

Toàn bộ các phép tính mô phỏng được neo (anchor) vào dữ liệu vận hành thực tế đã kiểm toán $3$ năm ($2020 - 2022$) của $42$ trạm điện mặt trời Đại học La Trobe:

```
┌───────────────────────────────────────────────┬───────────────────────────────┬──────────────────────────────┐
│ Thông Số Vận Hành Cơ Sở (Baseline Parameters) │ Giá Trị Kiểm Toán Thực Tế     │ Đơn Vị Tính / Ghi Chú        │
├───────────────────────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ Quy mô danh mục trạm                         │ 42                            │ Trạm áp mái độc lập          │
│ Tổng công suất định danh DC (P_STC)           │ 2.428                         │ kWp (Chuẩn STC IEC 60904-3)  │
│ Phân bổ theo 5 Campus                         │ Bundoora: 1.540 kWp (26 trạm) │ Bendigo: 510 kWp (8 trạm)    │
│                                               │ Albury-Wodonga: 240 kWp (4 tr)│ Shepparton: 78 kWp (2 trạm)  │
│                                               │ Mildura: 60 kWp (2 trạm)      │                              │
│ Cụm trạm lắp phẳng mái bằng (0° Tilt)         │ 970                           │ kWp (Sản lượng: 1.377.400 kWh│
│ Sản lượng phát cơ sở hàng năm (E_baseline)    │ 3.447.760                     │ kWh/năm (3,45 GWh/năm)       │
│ Năng suất phát điện riêng cơ sở (Yield_base)  │ 1.420                         │ kWh/kWp/năm                  │
│ Hệ số hiệu suất thực tế (PR_baseline)         │ 75,40%                        │ % (IEC 61724-1)              │
│ Hệ số công suất tải cơ sở (CF_baseline)       │ 16,21%                        │ % (Capacity Factor)          │
│ Tổn thất nhiệt độ cell (Loss_temp)            │ 14,80%                        │ ~510.268 kWh/năm (Sandia)    │
│ Tổn thất cắt ngọn Inverter (Loss_clip)        │ 2,30%                         │ 79.298 kWh/năm (ILR = 1.25)  │
│ Tổn thất do dị thường vận hành (Loss_anomaly) │ 2,04%                         │ 70.330 kWh/năm (6.891 cờ IF) │
│ Tổn thất góc nghiêng + bụi bùn đáy (970 kWp)  │ 3,90% (nhóm) + 18.500 kWh bùn │ 71.850 kWh/năm (Mái bằng)    │
│ Tổn thất che bóng + quá nhiệt biến tần        │ 1,65%                         │ 57.074 kWh/năm (6 trạm bóng) │
│ Tổn thất bụi bẩn mùa khô (Loss_soiling)       │ 1,80%                         │ 62.060 kWh/năm (Chuỗi khô)   │
│ Doanh thu / Tiết kiệm cơ sở hàng năm          │ 700.000                       │ AUD/năm (Theo biểu giá NEM)  │
│ Lượng phát thải CO2 tránh được cơ sở          │ 2.827.163                     │ kg CO2/năm (0,82 kg/kWh)     │
└───────────────────────────────────────────────┴───────────────────────────────┴──────────────────────────────┘
```

---

## 3. DANH SÁCH 7 HẠNG MỤC CHECKBOX ĐỀ XUẤT CẢI TIẾN HIỆU SUẤT

Dashboard hiển thị **7 Checkbox tương tác độc lập** (hoặc tích chọn đồng thời). Dưới đây là chi tiết công thức, sản lượng thu hồi, chi phí và lợi ích của từng hạng mục:

```
┌────┬────────────────────────────────────────────┬──────────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ STT│ Tên Hạng Mục Checkbox                      │ Tỷ Lệ Cải Thiện  │ Điện Thu Hồi │ Giá Trị Kinh │ CapEx Đầu Tư │ Hoàn Vốn     │
│    │ (Streamlit Interactive Component)          │ (% Hiệu Suất)    │ (kWh / Năm)  │ Tế (AUD/Năm) │ (AUD)        │ (Payback TB) │
├────┼────────────────────────────────────────────┼──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ 1  │ [ ] 1. Hệ thống BESS 5 Campus (1MW/2.5MWh) │ +20,6% hiệu ích  │ 712.182 kWh  │ 323.164 AUD  │ 1.250.000 AUD│ 3,87 Năm     │
│ 2  │ [ ] 2. Khe hở thông gió mái 10–15 cm       │ +3,40% toàn trạm │ 117.224 kWh  │ 23.445 AUD   │ 24.280 AUD   │ 1,04 Năm     │
│ 3  │ [ ] 3. Bảo trì CBM & AI Anomaly (GMM-IF)   │ +2,04% toàn trạm │ 70.330 kWh   │ 29.066 AUD   │ 8.000 AUD/năm│ < 4 Tháng    │
│ 4  │ [ ] 4. Nâng khung nghiêng chữ A 15° mái bằn│ +3,90% nhóm 970k │ 71.850 kWh   │ 14.670 AUD   │ 18.000 AUD   │ 1,23 Năm     │
│ 5  │ [ ] 5. Mái che Inverter & DC Optimizers    │ +1,65% toàn trạm │ 57.074 kWh   │ 11.415 AUD   │ 12.500 AUD   │ 1,10 Năm     │
│ 6  │ [ ] 6. Lịch rửa pin thông minh theo mưa    │ +1,80% mùa khô   │ 62.060 kWh   │ 18.412 AUD   │ 0 AUD (Quy t)│ 0 Ngày (Tức) │
│ 7  │ [ ] 7. Nâng cấp TOPCon (Kỳ Repowering)     │ +6,20% toàn trạm │ 213.761 kWh  │ 42.752 AUD   │ Kỳ đại tu    │ Tích hợp     │
└────┴────────────────────────────────────────────┴──────────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

---

### Chi Tiết Kỹ Thuật & Công Thức Từng Hạng Mục:

#### 🔹 Hạng mục 1: Hệ thống Pin Lưu trữ BESS Phân tán 5 Campus ($1\,\text{MW} / 2{,}5\,\text{MWh}$)
* **Cơ chế**: Thu hồi $88\%$ năng lượng cắt ngọn biến tần (Inverter Clipping $\text{ILR} = 1{,}25$) qua cấu trúc BESS DC-Coupled kết hợp chênh lệch giá giờ cao điểm (TOU Peak Arbitrage $17:00 - 21:00$) và gọt đỉnh phụ tải ($800\,\text{kW}$ Demand Charge).
* **Công thức**:
  $$\Delta E_{\text{clip, recovered}} = 79.298\,\text{kWh} \times 88\% = 69.782\,\text{kWh/năm}$$
  $$\text{Tổng năng lượng xả BESS} = 712.182\,\text{kWh/năm}$$
  $$\Delta \text{Revenue}_{\text{BESS}} = \text{Tiết kiệm TOU} + \text{Gọt đỉnh Demand} + \text{Bán điện} = 323.164\,\text{AUD/năm}$$
* **Tác động chỉ số**: $\Delta E = +69.782\,\text{kWh}$ (thu hồi cắt ngọn), $Loss_{\text{clip}}$ giảm từ $2{,}30\% \rightarrow 0{,}28\%$, $\text{CapEx} = 1.250.000\,\text{AUD}$, hoàn vốn $3{,}87\,\text{năm}$.

---

#### 🔹 Hạng mục 2: Khoảng hở Thông gió Mái $10 - 15\,\text{cm}$ (Chuẩn AS/NZS 5033)
* **Cơ chế**: Lắp giàn khung nhôm nâng cao $150\,\text{mm}$ tạo dòng đối lưu không khí tự nhiên mặt sau tấm pin, hạ nhiệt độ cell $T_{\text{cell}}$ trung bình $-8{,}0^\circ\text{C}$ (mùa hè hạ $-11^\circ\text{C}$, mùa đông hạ $-4^\circ\text{C}$).
* **Công thức**:
  $$\Delta T_{\text{cell}} = -8{,}0^\circ\text{C} \implies \Delta P_{\text{thermal}} = -\Delta T_{\text{cell}} \times 0{,}38\%/^\circ\text{C} \approx +3{,}04\% - +4{,}30\%$$
  $$\Delta E_{\text{ventilation}} = +117.224\,\text{kWh/năm} \implies \Delta \text{Revenue} = +23.445\,\text{AUD/năm}$$
* **Tác động chỉ số**: $\Delta E = +117.224\,\text{kWh}$, $Loss_{\text{temp}}$ giảm từ $14{,}80\% \rightarrow 11{,}40\%$, $\text{PR}$ tăng $+2{,}56\%$, $\text{CapEx} = 24.280\,\text{AUD}$, hoàn vốn $1{,}04\,\text{năm}$ ($12{,}4\,\text{tháng}$).

---

#### 🔹 Hạng mục 3: Chuyển đổi Bảo trì CBM & AI Anomaly (GMM-IF)
* **Cơ chế**: Rút ngắn thời gian phát hiện lỗi MTTD từ $14-30$ ngày xuống $<1$ giờ và thời gian khắc phục sự cố MTTR từ $7-14$ ngày xuống $1-3$ ngày làm việc đối với 6 mã lỗi vật lý (ngắt quá áp trưa, đứt cầu chì chuỗi, dồn gói Modbus, trôi điểm 0 CT, che bóng cục bộ).
* **Công thức**:
  $$\Delta E_{\text{cbm}} = +70.330\,\text{kWh/năm} \implies \Delta \text{Revenue} = +29.066\,\text{AUD/năm}$$
* **Tác động chỉ số**: $\Delta E = +70.330\,\text{kWh}$, $Loss_{\text{anomaly}}$ giảm từ $2{,}04\% \rightarrow 0{,}0\%$, $\text{PR}$ tăng $+1{,}54\%$, $\text{CapEx} = 8.000\,\text{AUD/năm}$ (phí AI cloud & drone scan), hoàn vốn $<4\,\text{tháng}$.

---

#### 🔹 Hạng mục 4: Nâng Khung Nghiêng chữ A $15^\circ$ Hướng Bắc Cho $970\,\text{kWp}$ Mái Bằng
* **Cơ chế**: Tối ưu hóa quang học theo quỹ đạo mặt trời mùa đông Victoria ($37^\circ\text{S}$), tăng sản lượng mùa đông $+44.436\,\text{kWh}$, giảm nhẹ mùa hè $-8.924\,\text{kWh}$ (tăng ròng $+53.350\,\text{kWh/năm}$). Kích hoạt góc dốc tự thoát nước mưa cuốn trôi dải bùn đọng viền nhôm đáy, thu hồi $+18.500\,\text{kWh}$ tổn thất che bóng chuỗi và tiết kiệm $+4.000\,\text{AUD}$ chi phí thuê nhân công rửa pin.
* **Công thức**:
  $$\Delta E_{\text{tilt\_net}} = 53.350\,\text{kWh} + 18.500\,\text{kWh} = \mathbf{71.850\,\text{kWh/năm}}$$
  $$\Delta \text{Revenue}_{\text{tilt}} = 10.670\,\text{AUD} (\text{điện quang học}) + 4.000\,\text{AUD} (\text{nhân công}) = \mathbf{14.670\,\text{AUD/năm}}$$
* **Tác động chỉ số**: $\Delta E = +71.850\,\text{kWh}$, $\text{PR}$ trạm mái bằng tăng $+3{,}90\%$, $\text{PR}$ toàn hệ thống tăng $+1{,}57\%$, $\text{CapEx} = 18.000\,\text{AUD}$, hoàn vốn $1{,}23\,\text{năm}$.

---

#### 🔹 Hạng mục 5: Mái Che Nắng Biến Tần & Bộ Tối Ưu Hóa Công Suất DC Optimizers
* **Cơ chế**: Lắp tấm che nắng giảm nhiệt bộ tản nhiệt Heatsink biến tần $<72^\circ\text{C}$, triệt tiêu lỗi giảm tải derating thu hồi $+18.450\,\text{kWh/năm}$ và bảo vệ $2$ Inverter không hỏng sớm ($16.000\,\text{AUD}$). Lắp DC Optimizers cho 6 trạm che bóng ($320\,\text{kWp}$) thu hồi $+38.624\,\text{kWh/năm}$.
* **Công thức**:
  $$\Delta E_{\text{inv\_opt}} = 18.450 + 38.624 = \mathbf{57.074\,\text{kWh/năm}} \implies \Delta \text{Revenue} = \mathbf{11.415\,\text{AUD/năm}}$$
* **Tác động chỉ số**: $\Delta E = +57.074\,\text{kWh}$, $Loss_{\text{shade\_inv}}$ giảm từ $1{,}65\% \rightarrow 0{,}0\%$, $\text{CapEx} = 12.500\,\text{AUD}$, hoàn vốn $1{,}10\,\text{năm}$.

---

#### 🔹 Hạng mục 6: Lịch Rửa Pin Thông Minh Dựa Trên Lượng Mưa (Precipitation Tracking)
* **Cơ chế**: Theo dõi cảm biến thời tiết, chỉ kích hoạt rửa thủ công khi chuỗi ngày khô hạn liên tục $\ge 21\,\text{ngày}$ và lượng mưa tích lũy $<2\,\text{mm}$. Thu hồi $+62.060\,\text{kWh}$ tổn thất bám bụi mùa khô ($+1{,}80\%$) và cắt giảm $3$ lần rửa thừa/năm tiết kiệm $+6.000\,\text{AUD}$ nhân công.
* **Công thức**:
  $$\Delta E_{\text{cleaning}} = \mathbf{62.060\,\text{kWh/năm}}$$
  $$\Delta \text{Revenue}_{\text{cleaning}} = 12.412\,\text{AUD} (\text{điện thu hồi}) + 6.000\,\text{AUD} (\text{tiết kiệm rửa thừa}) = \mathbf{18.412\,\text{AUD/năm}}$$
* **Tác động chỉ số**: $\Delta E = +62.060\,\text{kWh}$, $Loss_{\text{soiling}}$ giảm từ $1{,}80\% \rightarrow 0{,}0\%$, $\text{CapEx} = 0\,\text{AUD}$ (tối ưu quy trình), hoàn vốn tức thì ($0\,\text{ngày}$).

---

#### 🔹 Hạng mục 7: Nâng Cấp Công Nghệ Tấm Pin TOPCon / HJT (Kỳ Đại Tu Repowering)
* **Cơ chế**: Thay thế P-type PERC bằng N-type TOPCon có hiệu suất $\eta = 22{,}5\%$ (tăng từ $18{,}5\%$), hệ số nhiệt $\gamma = -0{,}30\%/^\circ\text{C}$ (cải thiện từ $-0{,}38\%/^\circ\text{C}$), triệt tiêu suy thoái quang học Zero LID và tỷ lệ lão hóa giảm từ $0{,}55\% \rightarrow 0{,}40\%/\text{năm}$.
* **Công thức**:
  $$\Delta E_{\text{repowering}} = 3.447.760 \times 6{,}20\% = \mathbf{213.761\,\text{kWh/năm}} \implies \Delta \text{Revenue} = \mathbf{42.752\,\text{AUD/năm}}$$
* **Tác động chỉ số**: $\Delta E = +213.761\,\text{kWh}$, $\text{PR}$ tăng $+4{,}67\%$, $\text{CapEx}$ tích hợp vào ngân sách đại tu định kỳ vòng đời $15 - 20\,\text{năm}$.

---

## 4. MA TRẬN TỔNG HỢP VÀ BẢNG KẾT QUẢ CUỐI CÙNG (FINAL RESULTS TABLE)

Khi **tất cả 6 hạng mục kỹ thuật cốt lõi (1 $\rightarrow$ 6)** được kích hoạt (chưa gồm kỳ đại tu Repowering):

```
┌───────────────────────────────────────────────┬───────────────────┬───────────────────┬──────────────────────────────┐
│ Chỉ Số Toàn Hệ Thống (42 Trạm / 2.428 kWp)    │ Baseline (Gốc)    │ Sau Tối Ưu (Sim)  │ Mức Cải Thiện (Delta Δ)      │
├───────────────────────────────────────────────┼───────────────────┼───────────────────┼──────────────────────────────┤
│ Sản lượng phát điện hàng năm (Energy Gen)     │ 3.447.760 kWh/năm │ 4.519.980 kWh/năm │ +1.072.220 kWh (+31,10% ròng)│
│ Năng suất phát điện riêng (Specific Yield)    │ 1.420 kWh/kWp/năm │ 1.861 kWh/kWp/năm │ +441 kWh/kWp/năm (+31,10%)   │
│ Hệ số hiệu suất thực tế (Performance Ratio)   │ 75,40%            │ 83,95%            │ +8,55% điểm phần trăm        │
│ Hệ số công suất tải (Capacity Factor - CF)    │ 16,21%            │ 21,25%            │ +5,04% điểm phần trăm        │
│ Tổn thất nhiệt độ cell (Thermal Loss)         │ 14,80%            │ 11,40%            │ Giảm -3,40% tổn thất         │
│ Tổn thất cắt ngọn Inverter (Clipping Loss)    │ 2,30%             │ 0,28%             │ Giảm -2,02% tổn thất (BESS)  │
│ Tổn thất do dị thường vận hành (Anomaly Loss) │ 2,04%             │ 0,00%             │ Triệt tiêu 100% (GMM-IF CBM) │
│ Tổn thất bám bụi & đọng bùn viền nhôm đáy     │ 2,34%             │ 0,00%             │ Triệt tiêu 100% (Mưa + 15°)  │
│ Tổng Doanh thu & Tiết kiệm hàng năm           │ 700.000 AUD/năm   │ 1.116.169 AUD/năm │ +416.169 AUD/năm (+59,45%)   │
│ Tổng chi phí đầu tư CapEx                     │ 0 AUD             │ 1.312.780 AUD     │ Đã bao gồm 1MW/2.5MWh BESS   │
│ Thời gian hoàn vốn hòa vốn bình quân (Payback)│ —                 │ 3,15 Năm          │ Tương đương 38 Tháng         │
│ Lượng phát thải CO2 cắt giảm bổ sung          │ 2.827 tấn CO2/năm │ 3.706 tấn CO2/năm │ +879 tấn CO2/năm (+31,10%)   │
│ Số lượng cây xanh tương đương (EPA Benchmark) │ 129.865 cây       │ 170.252 cây       │ +40.387 cây xanh tương đương │
└───────────────────────────────────────────────┴───────────────────┴───────────────────┴──────────────────────────────┘
```

---

## 5. ĐẶC TẢ GIAO DIỆN & CẤU TRÚC CODE STREAMLIT (UI/UX SPECIFICATION)

### 5.1. Bố cục Phân trang & Thành phần Giao diện

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ STREAMLIT WHAT-IF OPTIMIZATION DASHBOARD (THE OUTLIERS - LA TROBE UNIVERSITY 42 SITES)                 │
├───────────────────────────────┬────────────────────────────────────────────────────────────────────────┤
│ 🛠️ SIDEBAR CONTROLS           │ 📊 MAIN DISPLAY AREA                                                   │
│                               │                                                                        │
│ 📌 Kịch bản Định sẵn (Presets)│ 1. TOP METRIC CARDS (BASELINE vs SIMULATED)                            │
│ [x] Toàn bộ 6 Hạng mục O&M    │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│ [ ] Quick Wins (CapEx < 50k)  │ │ SẢN LƯỢNG    │ │ HỆ SỐ PR     │ │ GIÁ TRỊ TĂNG │ │ HOÀN VỐN     │    │
│ [ ] BESS & Grid Arbitrage     │ │ 4.52 GWh/năm │ │ 83.95%       │ │ +416k AUD/năm│ │ 3.15 Năm     │    │
│                               │ │ (+31.10%)    │ │ (+8.55% PR)  │ │ (CapEx 1.31M)│ │ (38 Tháng)   │    │
│ 🔘 DANH SÁCH CHECKBOX ĐỀ XUẤT │ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘    │
│ [x] 1. BESS 5 Campus (1MW)    │                                                                        │
│ [x] 2. Khe hở thông gió 15cm  │ 2. BIỂU ĐỒ TRỰC QUAN HÓA SO SÁNH (PLOTLY INTERACTIVE CHARTS)           │
│ [x] 3. CBM AI Anomaly GMM-IF  │ • Waterfall Chart: Phân rã dòng năng lượng gia tăng từng giải pháp.    │
│ [x] 4. Nâng khung 15° mái bằng│ • Monthly Generation Bar Chart: Baseline 12 tháng vs Sau tối ưu.       │
│ [x] 5. Mái che Inverter & Opt │ • Loss Breakdown Donut Chart: Cơ cấu giảm tổn thất (Nhiệt, Clip, Bụi). │
│ [x] 6. Rửa pin theo lượng mưa │                                                                        │
│ [ ] 7. Nâng cấp TOPCon (Repow)│ 3. BẢNG CHI TIẾT TỪNG HẠNG MỤC CẢI THIỆN (EXPANDABLE & DATAFRAME)      │
│                               │ • Bảng so sánh Before vs After với thanh tiến độ % (st.dataframe).     │
│ ⚙️ BIỂU GIÁ THỊ TRƯỜNG NEM    │ • Bảng bóc tách tài chính: CapEx, Tiết kiệm/Năm, Payback từng mục.     │
│ • Giá mua điện: 0.220 AUD/kWh │                                                                        │
│ • Giá bán FIT:  0.076 AUD/kWh │ 4. EXECUTIVE ACTION PLAN & INSIGHT CALLOUTS                            │
│ • Giá TOU Peak: 0.320 AUD/kWh │ • [Callout Green] Quick Wins mang lại 82.338 AUD/năm với CapEx < 55k!   │
│ • Demand Fee:   15.00 $/kW/th │ • [Callout Blue] BESS giúp gọt 800 kW đỉnh phụ tải 5 khuôn viên trường. │
└───────────────────────────────┴────────────────────────────────────────────────────────────────────────┘
```

---

### 5.2. Đoạn Mã Nguồn Mẫu (Streamlit Python Code Template)

```python
# app_whatif_simulation.py
# ỨNG DỤNG MÔ PHỎNG WHAT-IF KỊCH BẢN TỐI ƯU HIỆU SUẤT ĐIỆN MẶT TRỜI
# NHÓM THE OUTLIERS - FPT POLYTECHNIC

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. CẤU HÌNH TRANG
st.set_page_config(
    page_title="What-If Optimization Dashboard | The Outliers",
    page_icon="☀️",
    layout="wide"
)

# 2. HẰNG SỐ BASELINE LỊCH SỬ (HISTORICAL BASELINE)
BASELINE = {
    "capacity_kwp": 2428.0,
    "annual_energy_kwh": 3447760.0,
    "specific_yield": 1420.0,
    "pr_percent": 75.40,
    "cf_percent": 16.21,
    "loss_temp_percent": 14.80,
    "loss_clip_percent": 2.30,
    "loss_anomaly_percent": 2.04,
    "loss_soiling_percent": 2.34,
    "annual_revenue_aud": 700000.0,
    "co2_factor": 0.82
}

# 3. TỪ ĐIỂN DỮ LIỆU ĐỀ XUẤT CẢI TIẾN
IMPROVEMENTS = {
    "bess": {
        "name": "1. Hệ thống BESS 5 Campus (1MW/2.5MWh)",
        "delta_kwh": 69782.0 + (712182.0 - 69782.0), # Xả TOU + Thu hồi clipping
        "energy_recovered_kwh": 69782.0,
        "delta_revenue_aud": 323164.0,
        "capex_aud": 1250000.0,
        "delta_pr": 1.52,
        "delta_loss_clip": -2.02,
        "category": "Lưu trữ & Hòa lưới"
    },
    "ventilation": {
        "name": "2. Khe hở thông gió mái 10–15 cm",
        "delta_kwh": 117224.0,
        "energy_recovered_kwh": 117224.0,
        "delta_revenue_aud": 23445.0,
        "capex_aud": 24280.0,
        "delta_pr": 2.56,
        "delta_loss_temp": -3.40,
        "category": "Cơ khí & Tản nhiệt"
    },
    "cbm_ai": {
        "name": "3. Bảo trì CBM & AI Anomaly (GMM-IF)",
        "delta_kwh": 70330.0,
        "energy_recovered_kwh": 70330.0,
        "delta_revenue_aud": 29066.0,
        "capex_aud": 8000.0,
        "delta_pr": 1.54,
        "delta_loss_anomaly": -2.04,
        "category": "AI & O&M Thông minh"
    },
    "tilt_15deg": {
        "name": "4. Nâng khung 15° cho 970 kWp mái bằng",
        "delta_kwh": 71850.0, # 53.350 quang học + 18.500 tự rửa trôi
        "energy_recovered_kwh": 71850.0,
        "delta_revenue_aud": 14670.0,
        "capex_aud": 18000.0,
        "delta_pr": 1.57,
        "delta_loss_soiling": -0.54,
        "category": "Hình học Quang điện"
    },
    "inverter_shield": {
        "name": "5. Mái che Inverter & DC Optimizers",
        "delta_kwh": 57074.0,
        "energy_recovered_kwh": 57074.0,
        "delta_revenue_aud": 11415.0,
        "capex_aud": 12500.0,
        "delta_pr": 1.25,
        "delta_loss_shade": -1.65,
        "category": "Thiết bị Biến tần"
    },
    "smart_cleaning": {
        "name": "6. Lịch rửa pin theo lượng mưa",
        "delta_kwh": 62060.0,
        "energy_recovered_kwh": 62060.0,
        "delta_revenue_aud": 18412.0,
        "capex_aud": 0.0,
        "delta_pr": 1.35,
        "delta_loss_soiling": -1.80,
        "category": "Quy trình Vận hành"
    },
    "repowering": {
        "name": "7. Nâng cấp TOPCon (Kỳ Repowering)",
        "delta_kwh": 213761.0,
        "energy_recovered_kwh": 213761.0,
        "delta_revenue_aud": 42752.0,
        "capex_aud": 0.0, # Tích hợp chi phí đại tu
        "delta_pr": 4.67,
        "delta_loss_temp": -1.50,
        "category": "Đại tu Dài hạn"
    }
}

# 4. SIDEBAR - CHỌN CHECKBOX
st.sidebar.title("☀️ Tùy Chọn Kịch Bản")
preset = st.sidebar.selectbox(
    "Chọn kịch bản nhanh:",
    ["Tùy chỉnh cá nhân", "Tất cả giải pháp O&M (1 -> 6)", "Quick Wins (CapEx < 50k AUD)", "Chỉ giải pháp AI & Quy trình"]
)

# Xử lý logic Preset
default_checks = {k: False for k in IMPROVEMENTS}
if preset == "Tất cả giải pháp O&M (1 -> 6)":
    for k in ["bess", "ventilation", "cbm_ai", "tilt_15deg", "inverter_shield", "smart_cleaning"]:
        default_checks[k] = True
elif preset == "Quick Wins (CapEx < 50k AUD)":
    for k in ["ventilation", "cbm_ai", "tilt_15deg", "inverter_shield", "smart_cleaning"]:
        default_checks[k] = True
elif preset == "Chỉ giải pháp AI & Quy trình":
    for k in ["cbm_ai", "smart_cleaning"]:
        default_checks[k] = True

selected = {}
st.sidebar.subheader("Danh sách Hạng mục Tối ưu:")
for k, v in IMPROVEMENTS.items():
    selected[k] = st.sidebar.checkbox(v["name"], value=default_checks[k])

# 5. TÍNH TOÁN KẾT QUẢ REACTIVE
sim_delta_kwh = sum(IMPROVEMENTS[k]["delta_kwh"] for k in selected if selected[k])
sim_recovered_kwh = sum(IMPROVEMENTS[k]["energy_recovered_kwh"] for k in selected if selected[k])
sim_delta_revenue = sum(IMPROVEMENTS[k]["delta_revenue_aud"] for k in selected if selected[k])
sim_capex = sum(IMPROVEMENTS[k]["capex_aud"] for k in selected if selected[k])
sim_delta_pr = sum(IMPROVEMENTS[k]["delta_pr"] for k in selected if selected[k])

sim_energy = BASELINE["annual_energy_kwh"] + sim_delta_kwh
sim_pr = min(90.0, BASELINE["pr_percent"] + sim_delta_pr)
sim_yield = sim_energy / BASELINE["capacity_kwp"]
sim_cf = (sim_energy / (BASELINE["capacity_kwp"] * 8760)) * 100
sim_revenue = BASELINE["annual_revenue_aud"] + sim_delta_revenue
sim_payback = (sim_capex / sim_delta_revenue) if sim_delta_revenue > 0 else 0.0
sim_co2 = sim_energy * BASELINE["co2_factor"]

# 6. HIỂN THỊ GIAO DIỆN CHÍNH
st.title("⚡ Mô Phỏng Tối Ưu Hóa Hiệu Suất & Kinh Tế 42 Trạm Điện Mặt Trời")
st.caption("Dự án Tốt nghiệp The Outliers | Đối soát dữ liệu La Trobe University 2020–2022")

# Top Metric Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Sản Lượng Hàng Năm", f"{sim_energy/1e6:.2f} GWh", f"{sim_delta_kwh/1e3:+.1f} MWh ({sim_delta_kwh/BASELINE['annual_energy_kwh']*100:+.1f}%)")
col2.metric("Hệ Số Hiệu Suất PR", f"{sim_pr:.2f}%", f"{sim_delta_pr:+.2f}% PR")
col3.metric("Doanh Thu / Tiết Kiệm", f"${sim_revenue:,.0f} AUD", f"+${sim_delta_revenue:,.0f} AUD/năm")
col4.metric("Thời Gian Hoàn Vốn", f"{sim_payback:.2f} Năm" if sim_payback > 0 else "0 Ngày", f"CapEx: ${sim_capex:,.0f} AUD")

# Divider
st.markdown("---")

# 7. BẢNG KẾT QUẢ TỔNG HỢP & BÓC TÁCH CHI TIẾT
st.subheader("📋 Bảng So Sánh Trước & Sau Tối Ưu Hóa (Baseline vs Simulated)")
summary_df = pd.DataFrame({
    "Chỉ Số Vận Hành": [
        "Sản lượng điện hàng năm (Energy Generation)",
        "Năng suất phát điện riêng (Specific Yield)",
        "Hệ số hiệu suất thực tế (Performance Ratio)",
        "Hệ số công suất tải (Capacity Factor)",
        "Tổn thất nhiệt độ cell (Loss Temp)",
        "Doanh thu & Tiết kiệm hàng năm",
        "Tổng chi phí đầu tư (CapEx)",
        "Thời gian hoàn vốn hòa vốn (Payback Period)",
        "Lượng CO2 cắt giảm hàng năm"
    ],
    "Baseline (Gốc)": [
        f"{BASELINE['annual_energy_kwh']:,.0f} kWh",
        f"{BASELINE['specific_yield']:.0f} kWh/kWp",
        f"{BASELINE['pr_percent']:.2f}%",
        f"{BASELINE['cf_percent']:.2f}%",
        f"{BASELINE['loss_temp_percent']:.2f}%",
        f"${BASELINE['annual_revenue_aud']:,.0f} AUD",
        "$0 AUD",
        "—",
        f"{BASELINE['annual_energy_kwh']*BASELINE['co2_factor']/1e3:,.1f} tấn CO2"
    ],
    "Sau Tối Ưu (Mô phỏng)": [
        f"{sim_energy:,.0f} kWh",
        f"{sim_yield:.0f} kWh/kWp",
        f"{sim_pr:.2f}%",
        f"{sim_cf:.2f}%",
        f"{max(11.4, BASELINE['loss_temp_percent'] - (3.4 if selected.get('ventilation') else 0)):.2f}%",
        f"${sim_revenue:,.0f} AUD",
        f"${sim_capex:,.0f} AUD",
        f"{sim_payback:.2f} Năm" if sim_payback > 0 else "Tức thì",
        f"{sim_co2/1e3:,.1f} tấn CO2"
    ],
    "Mức Cải Thiện (Delta Δ)": [
        f"+{sim_delta_kwh:,.0f} kWh (+{sim_delta_kwh/BASELINE['annual_energy_kwh']*100:.1f}%)",
        f"+{sim_yield - BASELINE['specific_yield']:.0f} kWh/kWp",
        f"+{sim_delta_pr:.2f}%",
        f"+{sim_cf - BASELINE['cf_percent']:.2f}%",
        f"-{3.4 if selected.get('ventilation') else 0:.2f}%",
        f"+${sim_delta_revenue:,.0f} AUD/năm",
        f"+${sim_capex:,.0f} AUD",
        f"{sim_payback:.2f} Năm" if sim_payback > 0 else "0 Ngày",
        f"+{(sim_co2 - BASELINE['annual_energy_kwh']*BASELINE['co2_factor'])/1e3:,.1f} tấn CO2"
    ]
})
st.dataframe(summary_df, use_container_width=True, hide_index=True)

# Bảng Bóc Tách Từng Hạng Mục Cải Thiện
st.subheader("🔍 Chi Tiết Đóng Góp Từng Hạng Mục Đã Chọn")
items_data = []
for k, v in IMPROVEMENTS.items():
    if selected[k]:
        payback_item = (v["capex_aud"] / v["delta_revenue_aud"]) if v["delta_revenue_aud"] > 0 else 0.0
        items_data.append({
            "Hạng Mục Giải Pháp": v["name"],
            "Nhóm Kỹ Thuật": v["category"],
            "Điện Thu Hồi (kWh/năm)": f"{v['delta_kwh']:,.0f}",
            "Lợi Ích Kinh Tế (AUD/năm)": f"${v['delta_revenue_aud']:,.0f}",
            "CapEx (AUD)": f"${v['capex_aud']:,.0f}",
            "Hoàn Vốn (Năm)": f"{payback_item:.2f}" if payback_item > 0 else "Tức thì",
            "Tăng PR (%)": f"+{v['delta_pr']:.2f}%"
        })

if items_data:
    detail_df = pd.DataFrame(items_data)
    st.dataframe(detail_df, use_container_width=True, hide_index=True)
else:
    st.info("💡 Vui lòng tích chọn ít nhất một hạng mục ở Sidebar để xem phân tích chi tiết.")
```

---

## 6. KẾ HOẠCH TRIỂN KHAI & TÍCH HỢP HỆ THỐNG

1. **Vị trí tệp mã nguồn:** `srcs/06_dashboard/streamlit_whatif_app.py`.
2. **Thư viện phụ thuộc:** `streamlit`, `pandas`, `numpy`, `plotly`.
3. **Kết nối DWH/Supabase:** Nạp trực tiếp tham số từ Materialized View `bi_mart.mv_bi_mart_daily_kpis` hoặc cấu hình YAML `config/01_bi_mart_params.yaml`.
4. **Phục vụ Buổi Bảo vệ Đồ án (Defense Ready):**
   * Demo trực tiếp cho Hội đồng thấy tác động tức thì của việc giải quyết các bài toán vật lý (khoảng hở thông gió mái $15\,\text{cm}$, nâng góc nghiêng $15^\circ$, AI CBM phát hiện 6 mã lỗi) đến doanh thu và sản lượng thu hồi.
