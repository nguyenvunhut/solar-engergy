# TÀI LIỆU LÊN BỐ CỤC (OUTLINE) TRỰC QUAN HÓA TRÊN TABLEAU
**Dự án:** Hệ thống Phân tích và Dự báo Sản lượng Điện Mặt Trời (The Outliers)
**Tham chiếu:** Syllabus CLO6 (Trực quan hóa kết quả phân tích)

---

## I. TỔNG QUAN YÊU CẦU TRỰC QUAN HÓA (VISUALIZATION STRATEGY)
Dựa trên "Khẩu quyết" của Syllabus: **"Không có câu hỏi -> Không có phân tích"** và **"Đừng chỉ mô tả -> phải giải thích"**, hệ thống Dashboard trên Tableau được thiết kế theo tư duy *Top-Down* (Từ tổng quan kinh doanh đến chi tiết kỹ thuật/vận hành). 

Hệ thống bao gồm 4 Layout (Dashboard) chính phục vụ cho 2 nhóm người dùng:
1. **Ban Giám Đốc (C-Level / Managers):** Tập trung vào KPIs doanh thu, sản lượng tổng thể, mức độ đáp ứng chỉ tiêu.
2. **Kỹ Sư Vận Hành & Bảo Trì (O&M Engineers):** Tập trung vào hiệu suất (PR), suy hao do nhiệt, tín hiệu dị thường và dự báo hỏng hóc.

---

## II. CHI TIẾT CÁC LAYOUT (DASHBOARDS)

### 1. Dashboard 1: Executive Overview (Tổng quan Hệ thống & Hiệu suất Kinh doanh)
**Đối tượng:** Ban Giám Đốc, Quản lý Vận hành.
**Mục tiêu:** Cung cấp cái nhìn toàn cảnh về sức khỏe của 42 trạm PV tại Úc.

- **Câu hỏi nghiệp vụ giải quyết:**
  - Tổng sản lượng điện sinh ra (MWh/GWh) cho đến nay (YTD, MTD, WTD) là bao nhiêu?
  - Chúng ta có đạt được mục tiêu sản lượng kỳ vọng không?
  - Trạm nào đang hoạt động tốt nhất / tệ nhất về Hệ số công suất (Capacity Factor)?
  - Phân bổ địa lý của các trạm có ảnh hưởng như thế nào đến tổng sản lượng?
  - Performance của từng loại tấm Pin.

- **Metrics & KPIs:**
  - Lũy kế sản lượng: $E_{actual}$ (YTD, MTD).
  - Tỷ lệ đáp ứng mục tiêu (Yield Fulfillment Ratio): $\sum E_{actual} / \sum E_{target}$ (%).
  - Hệ số công suất khai thác trung bình (Capacity Factor - CF).

- **Các Viz (Biểu đồ) trên Layout:**
  - **BANs (Big Ass Numbers):** Hiển thị Tổng sản lượng, CF trung bình, và % Hoàn thành mục tiêu kèm theo mũi tên +/- so với kỳ trước (MoM, YoY).
  - **Symbol Map (Bản đồ địa lý):** Phân bổ 42 trạm tại Úc, kích thước (size) biểu diễn cho công suất (Capacity_kw) và màu sắc (color) biểu diễn cho CF (Xanh: Tốt, Đỏ: Kém).
  - **Bullet Chart:** So sánh $E_{actual}$ (thanh thực tế) với $E_{target}$ (vạch mục tiêu) theo từng cụm trạm hoặc top các trạm.
  - **Area/Line Chart (Trend):** Xu hướng sản lượng tổng lũy kế (Cumulative) theo thời gian.

---

### 2. Dashboard 2: Operational Efficiency & Loss Analysis (Hiệu suất Vận hành & Phân rã Tổn thất)
**Đối tượng:** Quản lý Kỹ thuật, Kỹ sư Năng lượng.
**Mục tiêu:** Đánh giá hiệu suất nội tại của tấm pin độc lập với thời tiết, đồng thời "giải thích" nguyên nhân cốt lõi gây sụt giảm công suất.

- **Câu hỏi nghiệp vụ giải quyết:**
  - Vì sao giữa trưa nắng gắt (bức xạ cao) nhưng sản lượng lại có dấu hiệu chững lại hoặc đi xuống?
  - Hệ thống mất bao nhiêu kWh do ảnh hưởng của nhiệt độ môi trường và Inverter?
  - Hiệu suất thực sự của trạm (PR) sau khi đã hiệu chỉnh nhiệt độ là bao nhiêu?

- **Metrics & KPIs:**
  - Performance Ratio (PR) & $PR_{adjusted}$ (đã hiệu chỉnh nhiệt độ).
  - Tổn thất nhiệt (Temperature Loss Ratio).
  - Loss Breakdown: Tổn thất do nhiệt, do Inverter, do đường dây.

- **Các Viz (Biểu đồ) trên Layout:**
  - **Scatter Plot (Tương quan Đa biến):** Trục X (Thời gian trong ngày), Trục Y trái (Sản lượng), Trục Y phải (Nhiệt độ $T_{ambient}$). Biểu đồ này sẽ làm rõ hiện tượng "Suy hao do nhiệt độ" (Thermal Degradation).
  - **Waterfall Chart (Biểu đồ thác nước):** Phân rã từ Sản lượng kỳ vọng lý tưởng ($E_{expected\_ideal}$) trừ đi các khoảng tổn thất (Nhiệt, Inverter...) để ra được $E_{actual}$. Trả lời thẳng vào câu hỏi "Sản lượng bị thất thoát ở khâu nào?".
  - **Dual Axis Line Chart:** So sánh PR và $PR_{adjusted}$ theo ngày/tháng để thấy rõ độ võng của hiệu suất do yếu tố thời tiết.

---

### 3. Dashboard 3: Anomaly Detection & Predictive Maintenance (Phát hiện Bất thường & Cảnh báo)
**Đối tượng:** Kỹ sư O&M (Operation & Maintenance).
**Mục tiêu:** Theo dõi các cờ báo động (Outlier Flags) sinh ra từ quá trình ETL (Rolling IQR) và ML. Chẩn đoán nguyên nhân hỏng hóc vật lý.

- **Câu hỏi nghiệp vụ giải quyết:**
  - Trạm nào đang xảy ra hiện tượng rò rỉ dòng điện ban đêm (nhiễu rò rỉ từ 18h-5h)?
  - Khi nào tấm pin cần được vệ sinh do bám bẩn hoặc có dấu hiệu hỏng Inverter?
  - Đang có các outliers nào, ở khung giờ, site nào?

- **Metrics & KPIs:**
  - Độ lệch cơ sở dự báo ($\Delta$ Baseline Deviation): $E_{actual} - E_{forecast\_baseline}$.
  - Tỷ lệ tương quan Bức xạ - Công suất (Irradiance to Power Ratio).
  - Số lượng Outliers (Nhiễu ngày / Nhiễu đêm).

- **Các Viz (Biểu đồ) trên Layout:**
  - **Time-Series Highlight Chart:** Biểu đồ đường của Sản lượng thực tế (15 phút/lần). Dùng chức năng màu sắc hoặc dấu chấm (shapes) màu Đỏ chót tại các mốc thời gian được "cờ" là Outlier.
  - **Heatmap (Lưới nhiệt độ theo Giờ-Ngày):** Trục Y là Giờ (0-23h), Trục X là Ngày. Highlight các ô có sản lượng > 0 trong khung giờ ban đêm (chứng minh dòng điện rò rỉ).
  - **Control Chart (Biểu đồ kiểm soát):** Vẽ đường Baseline của tỷ lệ Irradiance/Power, với giới hạn kiểm soát trên/dưới (UCL/LCL). Các điểm nằm ngoài kiểm soát (đặc biệt khi bức xạ cao nhưng công suất sụt) sẽ gợi ý kỹ sư đi vệ sinh kính bám bẩn.

---

### 4. Dashboard 4: Forecasting & Future Outlook (Dự báo Sản lượng tương lai)
**Đối tượng:** Ban Giám Đốc, Đội ngũ Lên kế hoạch Phân phối điện.
**Mục tiêu:** Cung cấp thông tin dự báo từ mô hình Machine Learning (Prophet/ARIMA) để doanh nghiệp lập kế hoạch hòa lưới điện hoặc cam kết hợp đồng bán điện.

- **Câu hỏi nghiệp vụ giải quyết:**
  - Sản lượng điện dự báo trong 7-30 ngày tới là bao nhiêu dựa trên dự báo thời tiết và dữ liệu quá khứ?
  - Mức độ tin cậy của mô hình dự báo nằm ở khoảng nào?
  - So sánh $E_{actual}$ hiện tại và $E_{expected}$ có đi sát với Baseline không?

- **Metrics & KPIs:**
  - Forecasted Energy ($E_{forecast\_baseline\_hourly}$).
  - Cận trên / Cận dưới của mức dự báo (Upper/Lower Confidence Intervals).

- **Các Viz (Biểu đồ) trên Layout:**
  - **Line Chart with Confidence Bands:** Đường line thể hiện $E_{actual}$ nối tiếp với đường gạch đứt thể hiện $E_{forecast}$, có dải màu xám nhạt làm biên độ sai số (Confidence Bands).
  - **Bar Chart (Variance Analysis):** Phân tích phương sai giữa Dự báo và Thực tế theo ngày. Cột dương (vượt kỳ vọng), cột âm (thấp hơn kỳ vọng).

---

## III. MAPPING THEO CHUẨN ĐẦU RA (CLO6 & LỜI DẶN SYLLABUS)

1. **Khẩu quyết "DATA: Data bẩn = insight sai":** Dashboard 3 chứng minh sự cần thiết của quy trình dọn rác ban đêm. Nếu không loại bỏ nhiễu ban đêm, Dashboard 1 (YTD/MTD) sẽ tính sai doanh thu lũy kế.
2. **Khẩu quyết "ANALYSIS: Đừng chỉ mô tả -> Phải giải thích":** Thay vì chỉ vẽ biểu đồ Line Chart sản lượng giảm, Dashboard 2 bổ sung Waterfall Chart và tương quan với Nhiệt độ để **giải thích** tại sao sản lượng giảm (do ảnh hưởng của Thermal Degradation thay vì thiếu nắng).
3. **Khẩu quyết "REAL WORLD: Logic mới là giá trị":** Việc tính toán các Measure như $PR_{adjusted}$ (Hiệu chỉnh nhiệt độ) hay Baseline Deviation được đưa vào Database (Tầng BI Mart) từ trước để tối ưu hóa. Tableau chỉ làm nhiệm vụ lôi ra và trực quan, đảm bảo tốc độ và sự đúng đắn của logic nghiệp vụ thế giới thực.
