# TÀI LIỆU HƯỚNG DẪN QUY CHUẨN TRỰC QUAN HÓA (VISUALIZATION GUIDELINES)
**Dự án:** Hệ thống Phân tích và Dự báo Sản lượng Điện Mặt Trời (The Outliers)

---

## I. MỤC ĐÍCH
Tài liệu này quy định hệ thống màu sắc (Color Palette) và các nguyên tắc thiết kế (Best Practices) khi dựng Dashboard trên Tableau. Mục tiêu là để đảm bảo tính đồng nhất, sự chuyên nghiệp và giúp người dùng cuối (End-users) dễ dàng nắm bắt Insights mà không bị rối mắt.

---

## II. BẢNG MÀU QUY CHUẨN (COLOR PALETTE)

Trong lĩnh vực năng lượng tái tạo (điện mặt trời), màu sắc cần mang lại cảm giác thân thiện với môi trường, minh bạch và cảnh báo rõ ràng.

### 1. Bảng màu chính (Primary Colors)
Dùng cho các thành phần chính như BANs (Big Numbers), Header, đường Line chính, Bar chart mặc định:
- **Xanh dương đậm (Navy Blue):** `#1F4E79` - Dùng cho thanh tiêu đề (Header), viền khung, hoặc để biểu thị các Metrics chung như Tổng số trạm.
- **Vàng cam (Solar Orange):** `#F39C12` - Đại diện cho Bức xạ mặt trời (Irradiance) hoặc Nhiệt độ ($T_{ambient}$).
- **Xanh lá mạ (Eco Green):** `#2ECC71` - Đại diện cho Sản lượng điện ($E_{actual}$) hoặc Hệ số công suất (Capacity Factor).

### 2. Bảng màu ngữ nghĩa (Semantic / Alert Colors)
Dùng để biểu thị trạng thái (Tốt/Xấu, Đạt/Không đạt):
- **Tích cực (Positive):** `#27AE60` (Xanh lục) - Khi đạt KPI, tỷ lệ hoàn thành vượt mục tiêu, hiệu suất PR cao.
- **Cảnh báo (Warning):** `#F1C40F` (Vàng) - Khi hệ suất hơi sụt giảm hoặc nhiệt độ bắt đầu vượt ngưỡng 25°C.
- **Báo động / Dị thường (Danger / Outlier):** `#E74C3C` (Đỏ) - Dùng ĐỘC QUYỀN để đánh dấu **Outliers** (nhiễu dòng điện ban đêm, điểm dị thường), hiệu suất thấp kỷ lục, hoặc cảnh báo $\Delta$ Baseline bị âm quá sâu.

### 3. Quy tắc sử dụng dải màu (Sequential & Diverging)
- **Sequential (Màu tuần tự):** Dùng cho Heatmap (ví dụ: Bản đồ rò rỉ điện ban đêm). Dải màu từ Trắng (0 kWh) đến Đỏ đậm (rò rỉ nặng).
- **Diverging (Màu phân cực):** Dùng để so sánh độ lệch (Variance) giữa Thực tế và Dự báo.
  - *Xanh dương (Dương - Vượt kỳ vọng)* <---> *Trắng (Đúng kỳ vọng)* <---> *Cam đỏ (Âm - Thất thoát)*.

### 4. Background & Formatting
- **Background Dashboard:** Trắng (`#FFFFFF`) hoặc Xám nhạt (`#F8F9FA`). Khuyến nghị dùng **Light Mode** để báo cáo trông giống văn bản doanh nghiệp chuyên nghiệp.
- **Font chữ (Typography):** 
  - Ưu tiên sử dụng `Tableau Light` hoặc `Tableau Regular`.
  - Font màu Đen nhạt (`#333333`) thay vì Đen tuyệt đối (`#000000`) để giảm mỏi mắt.

---

## III. QUY ĐỊNH KHI DỰNG VISUALIZATION TRÊN TABLEAU

### 1. Nguyên tắc thiết kế Tối giản (Data-Ink Ratio)
- **Lưới tọa độ (Gridlines):** Tắt toàn bộ Gridlines mặc định hoặc để nét đứt nhạt (`#E0E0E0`). Chỉ giữ lại Zero-line (đường số 0) dầy hơn một chút để định vị.
- **Đường viền (Borders):** Loại bỏ viền thừa của các biểu đồ (Remove chart borders) để tạo không gian liền mạch (White space).
- **Trục tọa độ (Axis):** 
  - Ẩn bớt (Hide) Header của trục nếu tiêu đề biểu đồ đã nói lên ý nghĩa (VD: Biểu đồ đã có tên "Sản lượng (kWh)" thì không cần Trục Y lặp lại chữ "Sản lượng").
  - Xoay ngang nhãn (Labels) thay vì dọc để người xem không phải nghiêng đầu đọc chữ. Nếu chữ quá dài, hãy dùng Bar chart nằm ngang thay vì Column chart dọc.

### 2. Nguyên tắc với Biểu đồ (Charts & Viz)
- **Không dùng Pie Chart/Donut Chart** nếu có nhiều hơn 4 danh mục. Thay vào đó hãy dùng Bar chart.
- **BANs (Big Ass Numbers):** Luôn đặt ở phía trên cùng của Dashboard (Top-left hoặc Top-center) để đập vào mắt người xem đầu tiên. Phải có % so sánh với kỳ trước (MoM/YoY).
- **Đồng nhất Trục (Synchronize Axis):** Khi dùng Dual Axis (Ví dụ: So sánh PR và PR_adjusted), **BẮT BUỘC** phải Synchronize Axis nếu chúng có chung đơn vị đo, để tránh trực quan lừa gạt (Misleading).

### 3. Quy định về Tương tác & Tooltips (Interactive Elements)
- **Tooltips:** 
  - Không để Tooltip mặc định của Tableau (liệt kê một mớ các trường dữ liệu).
  - Phải format thành một câu có nghĩa hoặc danh sách gạch đầu dòng rõ ràng.
  - *Ví dụ:* 
    ```text
    Ngày: <DAY(Date)>
    Trạm: <Site_Name>
    -------------------------
    Sản lượng thực tế: <SUM(E_actual)> kWh
    Độ lệch so với dự báo: <AGG(Baseline_Deviation)> kWh
    ```
- **Bộ lọc (Filters):** Gom tất cả bộ lọc về một bên phải (Right-panel) hoặc một thanh ngang dưới Header. Đổi định dạng filter sang dạng Dropdown (Single Value hoặc Multiple Values) để tiết kiệm diện tích. Áp dụng filter cho "All using this data source" hoặc các worksheet liên quan.

### 4. Đặt tên (Naming Conventions)
- **Dashboard:** Tên viết in hoa chữ cái đầu, nêu bật chức năng. VD: `Executive Overview`, `O&M Anomaly Detection`.
- **Worksheet:** Viết theo cấu trúc: `[Loại biểu đồ] - [Nội dung]`. VD: `Line - Sản lượng lũy kế YTD`, `Map - Phân bố trạm`.
- Ẩn toàn bộ tên Worksheet trên Dashboard nếu đã có thẻ text giải thích đi kèm.
