# Danh sách các Measure (Chỉ số) cần tính toán trong BI Mart

Dựa vào tài liệu thiết kế và ngữ cảnh nghiệp vụ của dự án điện năng lượng mặt trời (Solar Energy), dưới đây là danh sách các Measure cần được tính toán sẵn ở tầng BI Mart (Back-end) trước khi đưa vào công cụ BI (Tableau/Power BI) để trực quan hóa. Việc tính toán sẵn ở BI Mart giúp giảm tải tính toán cho BI tool, đảm bảo tính nhất quán của logic nghiệp vụ, và tăng tốc độ tải trang (dashboard load time).

## 1. Nhóm chỉ số vận hành cốt lõi (Operational Measures)

### 1.1. Sản lượng điện nén cấp Giờ (Hourly Energy Generated)
- **Công thức:** $E_{hourly} = \sum_{t=1}^{4} E_{15min, t}$
- **Ý nghĩa:** Cộng gộp sản lượng điện phát ra của 4 block 15 phút thành 1 dòng dữ liệu đại diện cho một khung giờ.
- **Mục đích ở BI Mart:** Giải quyết bài toán lệch pha tần suất dữ liệu (Granularity Mismatch) giữa dữ liệu sản lượng (15 phút) và dữ liệu thời tiết (1 giờ), giúp việc kết nối `LEFT JOIN` không bị lỗi nhân bản dòng (Fan-out Effect).

### 1.2. Hệ số công suất khai thác (Capacity Factor - CF)
- **Công thức:** $CF = \frac{E_{daily}}{P_{stc} \times 24}$
- **Ý nghĩa:** Đo lường hiệu suất sử dụng tài sản vốn đầu tư. Chỉ số này so sánh sản lượng thực tế trong ngày với kịch bản lý tưởng là trạm vận hành 24/24 ở công suất cực đại ($P_{stc}$).
- **Mục đích:** CF giúp Ban giám đốc đánh giá độ suy giảm chất lượng vật lý hoặc khấu hao của hệ thống tấm pin qua các tháng (nếu thời tiết không đổi nhưng CF sụt giảm).

## 2. Nhóm chỉ số hiệu suất và tổn thất vật lý (Efficiency KPIs)

### 2.1. Tỷ số hiệu suất trạm phát (Performance Ratio - PR)
- **Công thức:** $PR = \frac{E_{hourly}}{P_{stc} \times \left(\frac{G}{1000}\right)}$ *(với G là cường độ bức xạ `shortwave_radiation`)*.
- **Xử lý ngoại lệ (Back-end):** Bắt buộc bọc hàm điều kiện `CASE WHEN G <= 0 THEN 0 ELSE [Công_thức] END` để tránh lỗi `ZeroDivisionError` vào ban đêm.
- **Ý nghĩa:** Thước đo tiêu chuẩn quốc tế đánh giá độ khỏe nội tại của hệ thống pin, độc lập với điều kiện thời tiết. Dùng để chẩn đoán chính xác trạm có bị bám bẩn hoặc lỗi Inverter hay không.

### 2.2. Tỷ lệ hao hụt công suất do quá nhiệt (Temperature Loss Ratio)
- **Công thức:** 
  - Nếu $T_{ambient} > 25^\circ C$: $Loss_{temp} = (T_{ambient} - 25) \times 0.004$
  - Nếu $T_{ambient} \le 25^\circ C$: $Loss_{temp} = 0$
- **Ý nghĩa:** Giải thích hiện tượng "điểm gãy hiệu suất" trên biểu đồ (ví dụ: buổi trưa bức xạ cao nhất nhưng công suất lại tụt dốc do tổn thất nhiệt lượng).

### 2.3. Tỷ số hiệu suất có hiệu chỉnh nhiệt độ động ($PR_{adjusted}$)
- **Nhiệt độ tấm pin ước tính:** $T_{cell} = temperature\_2m + (shortwave\_radiation \times 0.03)$
- **Hệ số sụt giảm:** $Loss_{temp} = 0.004 \times (T_{cell} - 25)$ *(chỉ tính khi $T_{cell} > 25^\circ C$)*
- **Công thức:** $PR_{adjusted} = 0.85 \times (1 - Loss_{temp})$
- **Ý nghĩa:** Tính toán chỉ số PR sát thực tế nhất dựa trên tác động của nhiệt độ môi trường và bức xạ hiện tại, thay vì dùng một hằng số cố định.

## 3. Nhóm chỉ số dự báo và cảnh báo (Alerts & Forecasts)

### 3.1. Sản lượng dự kiến tiêu chuẩn / Sản lượng kỳ vọng ($E_{expected}$)
- **Công thức:** $E_{expected} = kWp \times \frac{shortwave\_radiation}{1000} \times PR_{adjusted}$
- **Ý nghĩa:** Dự báo sản lượng điện lý thuyết có thể đạt được trong giờ dựa vào công suất thiết kế, số giờ nắng đỉnh quy đổi (PSH) và PR đã hiệu chỉnh nhiệt độ.

### 3.2. Độ lệch cơ sở dự báo ($\Delta$ Baseline Deviation)
- **Công thức:** $\Delta = E_{actual\_hourly} - E_{forecast\_baseline\_hourly}$ *(Mô hình AI)*
- **Ý nghĩa:** Đóng vai trò là "Cờ báo động" cho kỹ thuật bảo trì. Nếu $\Delta$ âm sâu vượt ngưỡng sai số cho phép, hệ thống BI sẽ kích hoạt cảnh báo đỏ (Red Alert) để xử lý hỏng hóc hoặc che bóng vật lý.

---

## 4. Các Measure đề xuất bổ sung (Theo Context Hệ thống Điện Mặt Trời)

Ngoài các measure trong tài liệu cốt lõi, để một Dashboard trên BI tool (Tableau/Power BI) có thể hiện thị đa chiều và toàn diện cho nhiều cấp độ người dùng (Ban Giám đốc, Kỹ sư O&M), cần bổ sung các measure sau vào BI Mart:

### 4.1. Nhóm Chỉ số Thời gian (Time-Intelligence Measures)
- **Sản lượng tích lũy lũy kế (Cumulative Energy - YTD, MTD, WTD):** Cần pre-calculate tổng sản lượng theo ngày/tuần/tháng/năm để người dùng có thể so sánh sản lượng hiện tại so với cùng kỳ năm trước (YoY) hoặc tháng trước (MoM).
- **Tỷ lệ đáp ứng mục tiêu (Yield Fulfillment Ratio):** $\frac{\sum E_{actual}}{\sum E_{target}} \times 100\%$. Giúp Ban giám đốc theo dõi tiến độ hoàn thành KPI năng lượng.

### 4.2. Nhóm Phân rã Tổn thất (Loss Breakdown - Dành cho biểu đồ Waterfall)
- **Tổn thất do nhiệt độ (kWh):** $E_{expected\_ideal} - E_{expected\_temp\_adjusted}$
- **Tổn thất do Inverter (kWh):** Ước lượng dựa trên hao hụt chuyển đổi DC sang AC (khoảng 1.5% - 3%).
- **Tổn thất đường dây và suy hao tự nhiên (kWh).**
- **Ý nghĩa:** Đưa ra con số tuyệt đối (kWh) thay vì chỉ dùng tỷ lệ (%), giúp dễ dàng vẽ biểu đồ Waterfall cho thấy năng lượng bị mất đi qua từng giai đoạn vật lý.

### 4.3. Tỷ lệ tương quan (Irradiance to Power Ratio)
- Phép chia trực tiếp giữa `E_actual` và tổng lượng bức xạ $H$. Bất kỳ sự chệch hướng bất thường nào của tỷ lệ này (mà không thể giải thích bằng nhiệt độ) sẽ là dấu hiệu rõ ràng nhất của lỗi thiết bị (như bẩn mặt kính nghiêm trọng, phân chim, lá cây che phủ).
