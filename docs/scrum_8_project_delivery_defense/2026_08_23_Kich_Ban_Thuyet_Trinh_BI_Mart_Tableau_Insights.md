# KỊCH BẢN THUYẾT TRÌNH BẢO VỆ ĐỒ ÁN TỐT NGHIỆP
## PHÂN HỆ: BI DATA MART, BỘ CHỈ SỐ METRICS, HỆ THỐNG DASHBOARD TABLEAU VÀ KEY INSIGHTS CHIẾN LƯỢC

> **Đề tài:** Hệ thống Xử lý Dữ liệu, Nhận diện Dị thường Vận hành và Dự báo Sản lượng 42 Trạm Điện Mặt Trời tại Úc  
> **Nhóm thực hiện:** The Outliers — Chuyên ngành Xử lý Dữ liệu (Data Analytics)  
> **Thời lượng trình bày phân hệ:** 7 – 8 phút (trong tổng thời lượng 20 phút của nhóm)  
> **Cấu trúc trình bày mỗi Slide:** **VẤN ĐỀ DOMAIN & NHU CẦU NGƯỜI XEM -> THỰC THI & GIẢI PHÁP TRỰC QUAN HÓA -> KẾT QUẢ ĐÁP ỨNG YÊU CẦU NGHIỆP VỤ**  
> **Phong cách trình bày:** Tự tin, mạch lạc, ngôn ngữ nói tự nhiên, làm chủ số liệu, tập trung vào *"Bản chất vật lý"*, *"Kỹ thuật lắp đặt tản nhiệt"*, *"Nhu cầu thực tế của người dùng"* và *"Khả năng giải quyết bài toán domain"*.

---

## MỤC LỤC KỊCH BẢN

- [PHẦN 1: SCRIPT THUYẾT TRÌNH THEO CẤU TRÚC (VẤN ĐỀ -> THỰC THI -> KẾT QUẢ ĐÁP ỨNG)](#phần-1-script-thuyết-trình-theo-cấu-trúc-vấn-đề---thực-thi---kết-quả-đáp-ứng)
  - [Slide 1: Kiến trúc Tầng Phục vụ Dữ liệu BI Mart (Serving Layer) (1.0 phút)](#slide-1-kiến-trúc-tầng-phục-vụ-dữ-liệu-bi-mart-serving-layer-thời-lượng-10-phút)
  - [Slide 2: Khung Bộ Chỉ số Đo lường & Quản trị Cốt lõi (Core BI Metrics) (1.5 phút)](#slide-2-khung-bộ-chỉ-số-đo-lường--quản-trị-cốt-lõi-core-bi-metrics-thời-lượng-15-phút)
  - [Slide 3: Dashboard 1 — Tổng quan Vận hành & Đóng góp Môi trường (Executive Overview) (1.5 phút)](#slide-3-dashboard-1--tổng-quan-vận-hành--đóng-góp-môi-trường-executive-overview-thời-lượng-15-phút)
  - [Slide 4: Dashboard 2 — Hiệu suất Vận hành & Phân rã Tổn thất Nhiệt (Efficiency & Loss Analysis) (1.5 phút)](#slide-4-dashboard-2--hiệu-suất-vận-hành--phân-rã-tổn-thất-nhiệt-efficiency--loss-analysis-thời-lượng-15-phút)
  - [Slide 5: Dashboard 3 — Giám sát Bất thường & Cảnh báo Bảo trì (Anomaly Detection & Predictive Maintenance) (1.5 phút)](#slide-5-dashboard-3--giám-sát-bất-thường--cảnh-báo-bảo-trì-anomaly-detection--predictive-maintenance-thời-lượng-15-phút)
  - [Slide 6: Tổng hợp Key Insights Chiến lược & Khuyến nghị Hành động (1.5 phút)](#slide-6-tổng-hợp-key-insights-chiến-lược--khuyến-nghị-hành-động-thời-lượng-15-phút)
- [PHẦN 2: BATTLECARDS — BỘ CÂU HỎI PHẢN BIỆN HÓC BÚA TỪ HỘI ĐỒNG](#phần-2-battlecards--bộ-câu-hỏi-phản-biện-hóc-búa-từ-hội-đồng)
- [PHẦN 3: TỔNG HỢP 5 KEY INSIGHTS & KHUYẾN NGHỊ QUẢN TRỊ (CHEATSHEET)](#phần-3-tổng-hợp-5-key-insights--khuyến-nghị-quản-trị-cheatsheet)
- [PHẦN 4: TỔNG HỢP TOÀN BỘ INSIGHT CHIẾN LƯỢC TOÀN DỰ ÁN (DWH, BI, VẬT LÝ LẮP ĐẶT, O&M & QUẢN TRỊ - TRỪ ML)](#phần-4-tổng-hợp-toàn-bộ-insight-chiến-lược-toàn-dự-án-dwh-bi-vật-lý-lắp-đặt-om--quản-trị---trừ-ml)

---

# PHẦN 1: SCRIPT THUYẾT TRÌNH THEO CẤU TRÚC (VẤN ĐỀ -> THỰC THI -> KẾT QUẢ ĐÁP ỨNG)

---

### Slide 1: Kiến trúc Tầng Phục vụ Dữ liệu BI Mart (Serving Layer)
*(Thời lượng: ~1.0 phút)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [HÀNH ĐỘNG THUYẾT TRÌNH]:                                                              │
│ - Chiếu Slide sơ đồ kiến trúc Data Warehouse kết nối sang BI Mart và Tableau.         │
│ - Phong thái tự tin, mắt nhìn thẳng Hội đồng, giọng nói dứt khoát, mạch lạc.          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**[Lời thoại thuyết trình]:**

"Kính thưa Thầy/Cô trong Hội đồng, bước sang phân hệ Trực quan hóa và Báo cáo Quản trị (BI), nhóm em triển khai giải pháp theo cấu trúc: **Vấn đề hiệu năng -> Giải pháp kiến trúc -> Kết quả đạt được**.

* **1. VẤN ĐỀ CẦN GIẢI QUYẾT (The Problem):**  
  Bảng sự kiện sản lượng `fact_solar_energy_gen` lưu trữ hơn **$2{,}73\text{ triệu dòng}$** ở chu kỳ vi mô $15\text{ phút}$, trong khi dữ liệu thời tiết lại ở cấp $1\text{ giờ}$. Nếu thực hiện phép JOIN trực tiếp trên Tableau và bắt công cụ tự tính toán các chỉ số phức tạp như hệ số hiệu suất PR hay suy hao nhiệt độ, mỗi lần người dùng tương tác lọc dữ liệu màn hình sẽ bị trễ, làm quá tải tài nguyên máy chủ cơ sở dữ liệu.

* **2. THỰC THI & GIẢI PHÁP KỸ THUẬT (Implementation):**  
  Để xử lý triệt để, nhóm em không đẩy gánh nặng tính toán cho Tableau, mà đã xây dựng **Tầng BI Data Mart** tập trung thông qua một Materialized View lõi duy nhất: `bi_mart.mv_bi_mart_hourly_measures` trên PostgreSQL Supabase:
  - **Nén dữ liệu:** Gộp 4 block $15\text{ phút}$ thành cấp $1\text{ giờ}$, triệt tiêu hoàn toàn lỗi nhân bản dòng (Fan-out effect).
  - **Tiền tính toán logic (Pre-calculated):** Tính sẵn $PR_{\text{actual}}$, $PR_{\text{adjusted}}$, suy hao nhiệt $Loss_{\text{temp}}$, sản lượng kỳ vọng $E_{\text{expected}}$ và cờ dị thường GMM-IF.
  - **Đơn nhất nguồn chân lý:** Dữ liệu cấp giờ được giữ làm mức chi tiết chuẩn (Granularity) để Tableau linh hoạt tổng hợp lên Ngày, Tháng, Năm mà không cần duy trì nhiều bảng phụ.

* **3. KẾT QUẢ ĐẠT ĐƯỢC (Result & Impact):**  
  - **Kết nối trực tiếp và bảo mật:** Tableau kết nối trực tiếp vào cơ sở dữ liệu thông qua tài khoản được phân quyền riêng cho BI (`tableau_user` với quyền Read-Only), đảm bảo tính an toàn và bảo mật dữ liệu.
  - **Giảm tải tính toán cho Tableau:** Toàn bộ công thức phức tạp đã được tiền xử lý ở tầng cơ sở dữ liệu, giúp Tableau chỉ tập trung vào nhiệm vụ trực quan hóa.
  - **Cải thiện tốc độ truy vấn:** Tập dữ liệu được tổng hợp nhỏ gọn hơn rất nhiều, giúp các thao tác lọc, chuyển trang và tương tác trên Dashboard diễn ra nhanh chóng, mượt mà và ổn định."

---

### Slide 2: Khung Bộ Chỉ số Đo lường & Quản trị Cốt lõi (Core BI Metrics)
*(Thời lượng: ~1.5 phút)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [HÀNH ĐỘNG THUYẾT TRÌNH]:                                                              │
│ - Chiếu Slide bảng ma trận các Metrics: PR, CF, Yield, Loss Breakdown, Sunshine, CO2.  │
│ - Nhấn mạnh vào bản chất của 3 biến thể PR (PR actual, PR adjusted, PR correct).       │
│ - Giọng nói giải thích tự tin, làm nổi bật tư duy toán học và nghiệp vụ ngành quang điện.│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**[Lời thoại thuyết trình]:**

"Trước khi đưa số liệu lên giao diện, nhóm em đã chuẩn hóa toàn bộ hệ thống đo lường theo tiêu chuẩn quốc tế **IEC 61724-1**:

* **1. VẤN ĐỀ CẦN GIẢI QUYẾT (The Problem):**  
  Nếu chỉ nhìn vào sản lượng điện ($kWh$), chúng ta không thể so sánh được hiệu quả giữa trạm nhỏ ($10\,\text{kWp}$) và trạm lớn ($500\,\text{kWp}$). Nghiêm trọng hơn, vào mùa hè trời nắng gắt, nhiệt độ môi trường cao làm nóng cell pin khiến hiệu suất bị tụt tự nhiên. Nếu không bóc tách được yếu tố nhiệt độ, hệ thống sẽ phát cảnh báo giả rằng thiết bị bị hỏng.

* **2. THỰC THI & GIẢI PHÁP KỸ THUẬT (Implementation):**  
  Nhóm em đã phân rã toán học thành **3 biến thể Performance Ratio (PR)** độc lập:
  - **$PR_{\text{actual}}$ (Hiệu suất đo thô):** Tỷ lệ giữa điện thực tế và lý thuyết ($E_{\text{actual}} / E_{\text{theo}}$). Phản ánh thực trạng tức thời nhưng chịu toàn bộ suy hao nhiệt mùa hè.
  - **$PR_{\text{adjusted}}$ (Hiệu suất kỳ vọng BI Mart):** Tính bằng $0{,}85 \times (1 - Loss_{\text{temp}})$. Nhóm dùng con số $0{,}85$ làm mốc chuẩn thiết kế định mức độc lập ở $25^\circ\text{C}$ để trả lời câu hỏi: *'Với trời nóng này, một trạm chuẩn thì kỳ vọng PR phải đạt bao nhiêu?'*. Nhóm tuyệt đối không tính từ $PR_{\text{actual}}$ để tránh lỗi vòng lặp logic (Circular Logic) làm mất khả năng báo hỏng.
  - **$PR_{\text{correct}}$ (Hiệu suất chuẩn hóa nhiệt IEC 61724-1):** Bù trừ suy hao nhiệt về mốc $25^\circ\text{C}$ ($\frac{PR_{\text{actual}}}{1 + \gamma \cdot \Delta T}$). Chỉ số này phản ánh chính xác **độ khỏe nội tại của phần cứng**, dùng để bảo vệ hợp đồng bảo trì (SLA).

* **3. KẾT QUẢ ĐẠT ĐƯỢC (Result & Impact):**  
  - Thiết lập thành công bộ chỉ số kỹ thuật toàn diện: Hệ số công suất $CF = 17{,}2\%$, Năng suất riêng $Y_f = 4{,}35\text{ kWh/kWp/ngày}$, Phân rã tổn thất nhiệt $14{,}8\%$, Clipping $2{,}3\%$, Thời lượng nắng và Giảm phát thải $\text{CO}_2$ ($0{,}82\text{ kg/kWh}$).
  - Cung cấp cơ sở định lượng để phân biệt chính xác giữa *Suy hao nhiệt tự nhiên* và *Sự cố hỏng hóc thiết bị*."

---

### Slide 3: Dashboard 1 — Tổng quan Vận hành & Đóng góp Môi trường (Executive Overview)
*(Thời lượng: ~1.5 phút)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [HÀNH ĐỘNG THUYẾT TRÌNH]:                                                              │
│ - Chuyển sang giao diện Dashboard 1 trên Tableau.                                      │
│ - Tay chỉ lần lượt: Dải thẻ BANs trên cùng -> 2 Biểu đồ xu hướng -> Bản đồ 5 Campuses.│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**[Lời thoại thuyết trình]:**

"Giao diện đầu tiên là **Dashboard 1: Overview**, đóng vai trò là trung tâm giám sát tổng thể dành cho Ban Giám hiệu và Cấp Quản trị:

* **1. VẤN ĐỀ DOMAIN & NHU CẦU NGƯỜI XEM (Domain Problem & User Needs):**  
  Cấp quản trị cần trả lời 4 câu hỏi nghiệp vụ cốt lõi:
  - *Thứ nhất:* Toàn bộ 42 trạm trên 5 cơ sở đang phát ra bao nhiêu điện ($kWh$) và hiệu quả khai thác công suất ($CF$), hiệu suất vận hành ($PR$) đạt mức nào?
  - *Thứ hai:* Tính mùa vụ và thời lượng nắng ($Sunshine\text{ Hours}$) tác động cụ thể ra sao đến nguồn năng lượng qua các tháng?
  - *Thứ ba:* Tỷ trọng đóng góp sản lượng giữa các cơ sở đại học (Campuses) phân bổ như thế nào?
  - *Thứ tư:* Hệ thống đã đóng góp bao nhiêu vào chỉ tiêu phát triển bền vững và giảm phát thải $\text{CO}_2$ của nhà trường?

* **2. THỰC THI & GIẢI PHÁP TRỰC QUAN HÓA TRÊN TABLEAU (Implementation):**  
  Nhóm em bố trí giao diện khoa học theo cấu trúc:
  - **Dải thẻ BANs đầu trang:** Cập nhật tức thời 5 chỉ số then chốt: `Total Generation` ($127.633\text{ kWh}$ trong tháng chọn), `Capacity Factor` ($10{,}22\%$), `Performance Ratio Actual` ($82{,}12\%$), `Sunshine Duration` ($96{,}36\text{ giờ}$) và `CO2 Avoided` ($92.176\text{ kg}$) kèm tỷ lệ tăng giảm so với kỳ trước.
  - **Biểu đồ kết hợp Sản lượng & PR (Solar Energy Generation):** Phân tích chuỗi thời gian 28 tháng giữa thanh sản lượng $kWh$ và đường hiệu suất $PR_{\text{actual}}$ màu xanh lá.
  - **Biểu đồ xu hướng CF & Nắng (Capacity Factor & Sunshine Trend):** So khớp trực tiếp diện tích thời lượng nắng thực tế với đường hệ số công suất $CF$.
  - **Bản đồ địa lý 5 Cơ sở (Solar Generation by Campus):** Trực quan hóa vị trí địa lý của 42 trạm tại bang Victoria và thể hiện tỷ trọng sản lượng: Bundoora chiếm $61{,}63\%$, Bendigo $23{,}35\%$, Albury-Wodonga $10{,}11\%$, Mildura $3{,}82\%$ và Shepparton $1{,}09\%$.

* **3. KẾT QUẢ ĐÁP ỨNG YÊU CẦU NGHIỆP VỤ (Outcome & Value Delivered):**  
  Dashboard 1 giải quyết trọn vẹn nhu cầu giám sát vĩ mô: Giúp ban lãnh đạo nắm bắt ngay tình trạng hoạt động toàn mạng lưới chỉ trong 5 giây quan sát, phát hiện ngay các tháng hụt sản lượng do thiếu nắng và theo dõi sát sao tiến độ hoàn thành mục tiêu Net Zero."

---

### Slide 4: Dashboard 2 — Hiệu suất Vận hành & Phân rã Tổn thất Nhiệt (Efficiency & Loss Analysis)
*(Thời lượng: ~1.5 phút)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [HÀNH ĐỘNG THUYẾT TRÌNH]:                                                              │
│ - Chuyển Slide sang Dashboard 2.                                                       │
│ - Chỉ vào: Thẻ BANs PR -> Scatter Plot 4 góc phần tư -> Heatmap 12 tháng -> Bar so sánh.│
│ - Nhấn mạnh vào vật lý lắp đặt: Hướng tấm pin, khoảng cách hở cách mái và Carport.    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**[Lời thoại thuyết trình]:**

"Tiếp theo là **Dashboard 2: Efficiency & Loss**, công cụ chẩn đoán chuyên sâu dành cho Kỹ sư Năng lượng và Kỹ thuật:

* **1. VẤN ĐỀ DOMAIN & NHU CẦU NGƯỜI XEM (Domain Problem & User Needs):**  
  Kỹ sư vận hành đối mặt với các khúc mắc kỹ thuật:
  - *Thứ nhất:* Trạm đang bị suy hao do nhiệt (`Loss Temp`) bao nhiêu % và hiệu suất thực tế ($PR_{\text{actual}}$) so với hiệu suất kỳ vọng ($PR_{\text{adjusted}}$) chênh lệch ra sao?
  - *Thứ hai:* Trong 42 trạm, những trạm nào đang có hiệu suất kém hoặc suy hao nhiệt bất thường so với mức trung bình toàn mạng lưới?
  - *Thứ ba:* Cường độ suy hao nhiệt biến thiên theo 12 tháng trong năm như thế nào và nguyên nhân vật lý từ cách lắp đặt là gì?
  - *Thứ tư:* Giữa các công nghệ phần cứng khác nhau (Tấm pin Trina 330W, SunPower, Trina 310W và các dòng Inverter/Bộ tối ưu công suất P700/P730), loại nào đang mang lại sản lượng trên mỗi tấm pin (`Avg kWh/panel`) cao nhất?

* **2. THỰC THI & GIẢI PHÁP TRỰC QUAN HÓA TRÊN TABLEAU (Implementation):**  
  Nhóm em thiết kế 4 phân vùng phân tích tương hỗ:
  - **Bộ ba BANs hiệu suất:** Đặt cạnh nhau $PR_{\text{actual}}$ ($82{,}12\%$), $PR_{\text{adjusted}}$ ($83{,}19\%$) và `Loss Temp` ($2{,}15\%$) để đối soát tức thời mức độ đạt chuẩn kỹ thuật.
  - **Biểu đồ phân tán 4 góc phần tư (Solar site generation performance):** Trục hoành là $PR_{\text{actual}}$, trục tung là `Avg. Loss Temp`, tô màu theo loại tấm pin. Đường tham chiếu (Reference Line) trung bình giúp lọc ngay các trạm cá biệt (như Site 16, Site 39).
  - **Bản đồ nhiệt Tổn thất (Avg Temp loss heat map by Site and Month):** Ma trận 12 tháng $\times$ 42 trạm, làm nổi bật các dải màu cam đậm vào các tháng mùa hè (Tháng 11 đến Tháng 2) khi nhiệt độ tăng cao.
  - **Biểu đồ cột so sánh phần cứng:** 
    - Đo lường sản lượng trung bình trên mỗi tấm pin (`Avg kWh/panel`) và tỷ lệ suy hao nhiệt theo từng dòng tấm pin.
    - Phân tích sản lượng trung bình theo từng cấu hình Inverter (SMA, ABB, SolarEdge SE27.6k, SE82.8k...) và bộ tối ưu Optimizer (P700, P730).

* **3. KẾT QUẢ ĐÁP ỨNG YÊU CẦU & BÀI HỌC VẬT LÝ LẮP ĐẶT (Outcome & Installation Engineering):**  
  - **Minh oan cho thiết bị:** Dashboard 2 chứng minh rõ ràng việc sụt giảm hiệu suất là do nhiệt độ cell pin nung nóng lên tới $68^\circ\text{C} - 72^\circ\text{C}$ lúc trưa hè (gây tổn thất $14{,}8\%$).
  - **Giải pháp lắp đặt thực tế:** Để giảm thiểu tổn thất nhiệt này, kỹ thuật lắp đặt bắt buộc phải tuân thủ 3 nguyên tắc:
    1. *Khoảng cách hở cách mái (Standoff Height):* Tuyệt đối không áp sát tấm pin sát mái tôn ($< 5\,\text{cm}$); phải nâng khoảng cách hở từ **$10 - 15\,\text{cm}$** để tạo **Hiệu ứng Ống khói Tự nhiên (Natural Stack Effect)** giúp không khí đối lưu làm mát mặt dưới, hạ $8 - 12^\circ\text{C}$ nhiệt độ cell.
    2. *Vị trí lắp đặt tối ưu:* Mô hình **Solar Carport (Nhà để xe năng lượng mặt trời)** đạt hiệu quả tản nhiệt vượt trội nhất nhờ thông gió 360 độ (nhiệt độ cell thấp hơn $12 - 15^\circ\text{C}$ so với mái tôn kín).
    3. *Hướng lắp đặt:* Ở Bán cầu Nam, hướng **Bắc chuẩn ($0^\circ$)** đạt sản lượng đỉnh quanh năm; tuy nhiên bố trí hướng **Đông - Tây (East-West)** sẽ giúp san phẳng phụ tải và hạ nhiệt độ đỉnh giờ trưa."

---

### Slide 5: Dashboard 3 — Giám sát Bất thường & Cảnh báo Bảo trì (Anomaly Detection & Predictive Maintenance)
*(Thời lượng: ~1.5 phút)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [HÀNH ĐỘNG THUYẾT TRÌNH]:                                                              │
│ - Chuyển Slide sang Dashboard 3.                                                       │
│ - Chỉ vào: BANs Outlier -> Biểu đồ chuỗi thời gian chấm đỏ -> Bảng phân rã đa biến.    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**[Lời thoại thuyết trình]:**

"Cuối cùng là **Dashboard 3: Anomaly Detection**, công cụ giám sát thời gian thực phục vụ công tác Vận hành & Bảo trì (O&M):

* **1. VẤN ĐỀ DOMAIN & NHU CẦU NGƯỜI XEM (Domain Problem & User Needs):**  
  Kỹ sư bảo trì O&M cần biết chính xác:
  - *Thứ nhất:* Tổng số giờ phát sinh bất thường (`Outlier Hours`) và tỷ lệ dị thường (`Outlier Rate`) của hệ thống là bao nhiêu?
  - *Thứ hai:* Bất thường xuất hiện vào những ngày nào, khung giờ nào và tại trạm nào?
  - *Thứ ba:* Nguyên nhân vật lý cốt lõi của từng điểm bất thường là gì: Do sự cố thiết bị (quá áp/quá nhiệt Inverter, đứt cầu chì chuỗi) hay do yếu tố thời tiết biến động (mây che đột ngột, mưa giông)?

* **2. THỰC THI & GIẢI PHÁP TRỰC QUAN HÓA TRÊN TABLEAU (Implementation):**  
  Nhóm em tích hợp kết quả từ pipeline GMM-IF và 5 rào chắn vật lý vào giao diện:
  - **Dải BANs cảnh báo O&M:** Thể hiện `Outlier Hours` ($104\text{ giờ}$), `Outlier Rate` ($0{,}45\%$) và $PR_{\text{corrected}}$ ($85{,}35\%$) đã bù trừ suy hao nhiệt để đo độ khỏe thực của thiết bị.
  - **Biểu đồ chuỗi thời gian điểm nút đỏ (Outlier detection daily):** Đường cong màu xanh là sản lượng $kWh$ theo từng giờ; các điểm dị thường được gắn **chấm tròn màu đỏ** nổi bật giúp kỹ sư nhận diện ngay vị trí đồ thị bị méo hoặc đứt gãy.
  - **Biểu đồ tương quan & Xu hướng tháng (Outlier Rate and Number by Month):** Cột màu cam là số lượng ngoại lai, đường màu đỏ là tỷ lệ Outlier qua 12 tháng kèm đường kiểm soát trung bình ($0{,}80\%$).
  - **Ma trận bóc tách chi tiết (Outliers details):** Khi chọn một ngày và một trạm cụ thể (ví dụ Site 35 ngày 09/08/2021), hệ thống hiển thị chi tiết 4 thước đo trong từng giờ từ $07\text{h}$ đến $20\text{h}$: Sản lượng phát ($E_{\text{Hourly}}$), Bức xạ sóng ngắn ($Shortwave\text{ Radiation}$), Độ che phủ mây ($Cloud\text{ Cover}$) và Nhiệt độ ($Temperature$).

* **3. KẾT QUẢ ĐÁP ỨNG YÊU CẦU NGHIỆP VỤ (Outcome & Value Delivered):**  
  Dashboard 3 chuyển đổi hoàn toàn quy trình bảo trì từ 'chờ hỏng mới sửa' sang **Bảo trì Dựa trên Điều kiện (CBM)**: Kỹ sư O&M chỉ cần mở bảng chi tiết là có thể đối soát ngay: Nếu bức xạ cao, trời không mây mà sản lượng bằng 0 $\implies$ Lỗi phần cứng Inverter; nếu bức xạ tụt đồng thời với mây tăng $\implies$ Do thời tiết tự nhiên, không cần điều động nhân sự đi kiểm tra thực địa."

---

### Slide 6: Tổng hợp Key Insights Chiến lược & Khuyến nghị Hành động
*(Thời lượng: ~1.5 phút)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [HÀNH ĐỘNG THUYẾT TRÌNH]:                                                              │
│ - Chiếu Slide bảng 5 Key Insights & Khuyến nghị Hành động.                            │
│ - Giọng nói dứt khoát, kết luận bài thuyết trình với tầm nhìn chiến lược.             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**[Lời thoại thuyết trình]:**

"Từ toàn bộ quá trình xử lý dữ liệu và trực quan hóa chuyên sâu trên 3 Dashboard, nhóm em đúc kết **5 Key Insights chiến lược** và đưa ra các khuyến nghị hành động thực tế cho hệ thống điện mặt trời:

* **Insight 1 — Bất đối xứng Mùa vụ Cực đoan (3.5 lần):**  
  - *Dữ liệu:* Hệ số công suất mùa hè đạt đỉnh $CF \approx 20{,}0\%$, nhưng mùa đông tụt dốc xuống chỉ còn $7{,}03\%$ (giảm $3{,}5$ lần).  
  - *Khuyến nghị:* Nhà trường bắt buộc phải trang bị **Hệ thống Pin Lưu trữ Năng lượng BESS** để tích trữ sản lượng dư thừa mùa hè và điều hòa phụ tải vào mùa đông nhằm đạt mục tiêu tự chủ năng lượng.

* **Insight 2 — Lệch pha Tiềm năng Địa lý:**  
  - *Dữ liệu:* Hai cơ sở Bundoora và Bendigo đang gánh tới $84{,}98\%$ tổng sản lượng, trong khi cơ sở **Mildura** — nơi có bức xạ mặt trời cao nhất bang Victoria ($5{,}7\text{ PSH}$) — mới chỉ chiếm $3{,}82\%$ công suất.  
  - *Khuyến nghị:* Ưu tiên giải ngân vốn đầu tư mở rộng diện tích mảng pin tại khuôn viên Mildura trong giai đoạn 2 để tối đa hóa hiệu suất sinh điện.

* **Insight 3 — Kỹ thuật Lắp đặt & Tản nhiệt Giảm Suy hao ($14{,}8\%$):**  
  - *Dữ liệu:* Suy hao nhiệt độ mùa hè làm mất tới $14{,}8\%$ sản lượng tiềm năng do hiện tượng áp sát mặt mái tôn khiến cell pin nung nóng trên $65^\circ\text{C}$.  
  - *Khuyến nghị Kỹ thuật:*
    1. *Khoảng cách cách mái:* Thiết kế khung đỡ nâng tấm pin cách mặt mái từ **$10 - 15\,\text{cm}$** để tạo luồng khí đối lưu tự nhiên (Stack Effect).
    2. *Vị trí lắp đặt:* Chuyển đổi sang mô hình **Solar Carport (Nhà để xe quang điện)** giúp thông gió đa chiều $360^\circ$ và hạ $12 - 15^\circ\text{C}$ nhiệt độ cell.
    3. *Hướng & Góc nghiêng:* Lắp đặt hướng Bắc ($0^\circ$) với góc dốc **$30^\circ - 35^\circ$** (bằng vĩ độ Victoria) giúp tự rửa sạch bụi bẩn mùa mưa; kết hợp hướng Đông - Tây đối với các tòa nhà có nhu cầu dùng điện cao điểm sáng và chiều.

* **Insight 4 — Ưu thế Vượt trội của Công nghệ Pin Monocrystalline:**  
  - *Dữ liệu:* Dòng pin SunPower Mono-Si kết hợp Inverter SolarEdge/SMA duy trì sản lượng trung bình trên mỗi tấm pin ($0{,}057 - 0{,}059\text{ kWh/panel}$) vượt trội $38\%$ so với các tấm pin Polycrystalline.  
  - *Khuyến nghị:* Chuẩn hóa toàn bộ danh mục mua sắm thiết bị thay thế sang tấm pin công nghệ Mono-Si hoặc công nghệ **Kính kép 2 mặt (Bifacial Glass-Glass)** tản nhiệt nhanh.

* **Insight 5 — Kiểm soát An toàn Dị thường Vận hành:**  
  - *Dữ liệu:* Tỷ lệ ngoại lai thực tế của toàn mạng lưới được kiểm soát ở mức rất an toàn ($0{,}45\% - 0{,}80\%$). Các bất thường chủ yếu tập trung vào hiện tượng quá áp lưới giờ trưa và sai lệch mốc 0 của cảm biến ban đêm.  
  - *Khuyến nghị:* Ứng dụng Dashboard 3 làm công cụ giám sát O&M thường nhật để tự động phát hiện sớm sự cố, giảm thời gian gián đoạn phát điện xuống dưới 24 giờ.

Em xin chân thành cảm ơn Quý Thầy/Cô trong Hội đồng đã chú ý lắng nghe, và nhóm chúng em rất mong nhận được những câu hỏi chất vấn từ Thầy/Cô!"

---

# PHẦN 2: BATTLECARDS — BỘ CÂU HỎI PHẢN BIỆN HÓC BÚA TỪ HỘI ĐỒNG

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            BỘ CÂU HỎI PHẢN BIỆN HỘI ĐỒNG (DEFENSE BATTLECARDS)              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Câu hỏi 1: "Tại sao trong công thức PR adjust các em lại dùng con số 0.85 mà không tính trực tiếp từ PR actual?"
* **Cách trả lời ăn điểm:**
  "Dạ thưa Thầy/Cô, số $0{,}85$ ($85\%$) là **Hệ số Hiệu suất Thiết kế Danh định (Design Benchmark)** chuẩn mực quốc tế của một hệ thống điện mặt trời mới ở điều kiện STC $25^\circ\text{C}$ (theo NREL và PVsyst), sau khi đã trừ đi khoảng $15\%$ các tổn thất vật lý cố định như suy hao dây dẫn, hiệu suất Inverter và phản xạ mặt kính.  
  $PR_{\text{adjusted}}$ đóng vai trò là **Đường chuẩn kỳ vọng độc lập** để trả lời câu hỏi: *'Với thời tiết nóng này, một hệ thống đạt chuẩn thì kỳ vọng PR phải đạt bao nhiêu?'*.  
  Nếu chúng em lấy $PR_{\text{actual}}$ để tính $PR_{\text{adjusted}}$, hệ thống sẽ dính **lỗi logic vòng lặp (Circular Logic)**: Khi trạm bị cháy cầu chì làm $PR_{\text{actual}}$ tụt xuống $30\%$, đường kỳ vọng cũng tụt theo xuống $27\%$, hệ thống sẽ lầm tưởng trạm đang hoạt động vượt kỳ vọng và còi báo động O&M sẽ bị vô hiệu hóa hoàn toàn ạ."

---

#### Câu hỏi 2: "Tại sao vào mùa hè trời nắng đẹp mà hệ số PR actual lại bị giảm xuống dưới 75%? Có phải hệ thống bị hỏng không?"
* **Cách trả lời ăn điểm:**
  "Dạ thưa Thầy/Cô, hệ thống hoàn toàn bình thường ạ. Đó là do đặc tính vật lý của chất bán dẫn Silicon: khi nhiệt độ bề mặt tấm pin tăng lên $65^\circ\text{C} - 70^\circ\text{C}$, điện áp hở mạch bị sụt giảm theo hệ số nhiệt $\gamma = -0{,}38\%/^\circ\text{C}$, gây ra suy hao nhiệt tự nhiên khoảng $14{,}8\%$.  
  Để chứng minh trạm không hỏng, nhóm em sử dụng chỉ số **$PR_{\text{correct}}$ theo tiêu chuẩn IEC 61724-1 Phụ lục B** (đã bù trừ suy hao nhiệt về mốc $25^\circ\text{C}$). Kết quả $PR_{\text{correct}}$ vẫn đạt trên **$82\%$ (Class A)**, giúp bảo vệ nhà thầu vận hành không bị phạt oan hợp đồng cam kết SLA ạ."

---

#### Câu hỏi 3: "Biến tần bị Inverter Clipping mất 2.3% sản lượng, tại sao nhóm không đề xuất thay biến tần công suất lớn hơn?"
* **Cách trả lời ăn điểm:**
  "Dạ thưa Thầy/Cô, việc thiết kế tỷ lệ tấm pin lớn hơn biến tần (DC/AC Ratio $\approx 1{,}25$) là tiêu chuẩn tối ưu chi phí LCOE trong ngành điện mặt trời.  
  Hiện tượng clipping chỉ xảy ra khoảng $1 - 2$ tiếng giữa trưa của vài ngày nắng đỉnh mùa hè (chiếm $2{,}3\%$ năm). Nếu nâng công suất Inverter để lấy $2{,}3\%$ này, chi phí mua Inverter lớn hơn và nâng cấp hạ tầng điện sẽ tốn kém rất nhiều, trong khi phần lớn thời gian còn lại trong năm Inverter sẽ chạy non tải với hiệu suất thấp. Do đó, mức tổn thất $2{,}3\%$ là mức đánh đổi kinh tế hoàn toàn tối ưu ạ."

---

#### Câu hỏi 4: "Tại sao nhóm chỉ dùng một Materialized View mv_bi_mart_hourly_measures mà không tạo thêm View cấp ngày?"
* **Cách trả lời ăn điểm:**
  "Dạ thưa Thầy/Cô, đây là quyết định tối ưu hóa kiến trúc DWH của nhóm:
  1. **Đơn nhất nguồn dữ liệu (Single Source of Truth):** Dữ liệu cấp giờ ($683.385$ dòng sau khi nén từ $2{,}73$ triệu dòng) có dung lượng rất nhẹ ($< 80\,\text{MB}$), hoàn toàn nằm gọn trong bộ nhớ RAM của máy chủ và Tableau Data Engine.
  2. **Tính linh hoạt tối đa:** Giữ mức độ chi tiết (Granularity) ở cấp giờ cho phép Tableau thực hiện linh hoạt mọi phép khoan sâu (Drill-down) theo khung giờ, theo ca trực, hoặc gom nhóm động theo Ngày, Tuần, Tháng, Năm bằng các hàm LOD và Date Trunc mà không cần duy trì nhiều View trùng lặp, giúp giảm $50\%$ chi phí bảo trì và thời gian làm mới (Refresh) cơ sở dữ liệu ạ."

---

# PHẦN 3: TỔNG HỢP 5 KEY INSIGHTS & KHUYẾN NGHỊ QUẢN TRỊ (CHEATSHEET)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            TỔNG HỢP 5 KEY INSIGHTS & KHUYẾN NGHỊ QUẢN TRỊ                   │
├────────────────────────────────┬────────────────────────────────────────────────────────────┤
│ 1. Độ lệch Mùa vụ Cực đoan     │ Sản lượng Hè gấp 3.5 lần Đông (CF: 20.00% vs 7.03%).       │
│                                │ Khuyến nghị: Bắt buộc đầu tư hệ thống BESS để trữ điện.    │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ 2. Rủi ro Tập trung Tài sản    │ Bundoora & Bendigo chiếm 84.98% sản lượng.                 │
│                                │ Khuyến nghị: Ưu tiên mở rộng sang Mildura (nơi nắng tốt nhất).│
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ 3. Vật lý Lắp đặt & Tản nhiệt  │ Nâng hở mái 10-15cm tạo Stack Effect; ưu tiên Solar Carport.│
│                                │ Khuyến nghị: Hướng Bắc 30-35°, bảo dưỡng quạt Inverter T9. │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ 4. Tối ưu Công nghệ Tấm pin    │ SunPower Mono-Si đạt 0.059 kWh/panel (vượt trội 38% Poly).  │
│                                │ Khuyến nghị: Chuẩn hóa mua sắm vật tư thay thế sang Mono-Si.│
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ 5. Chuyển đổi Vận hành O&M     │ Outlier Rate ở mức 0.45% - 0.80%; đối soát đa biến tức thì.│
│                                │ Giá trị: Xử lý sự cố trong ngày, giảm downtime xuống <24h. │
└────────────────────────────────┴────────────────────────────────────────────────────────────┘
```

---

# PHẦN 4: TỔNG HỢP TOÀN BỘ INSIGHT CHIẾN LƯỢC TOÀN DỰ ÁN (DWH, BI, VẬT LÝ LẮP ĐẶT, O&M & QUẢN TRỊ - TRỪ ML)

Phần này đúc kết toàn diện mọi phát hiện sâu sắc nhất từ toàn bộ dự án (ngoại trừ các thuật toán Machine Learning), được phân chia theo 6 Trụ cột Chuyên môn:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                       6 TRỤ CỘT INSIGHTS CHIẾN LƯỢC TOÀN DIỆN CỦA DỰ ÁN                     │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ Trụ cột 1: Kiến trúc Dữ liệu & Serving Layer (Data Lakehouse & BI Mart)                     │
│ Trụ cột 2: Đo lường Hiệu năng & Bản chất 3 Biến thể PR (IEC 61724-1 Standard)               │
│ Trụ cột 3: Kỹ thuật Lắp đặt & Vật lý Tản nhiệt Giảm Suy hao Nhiệt (Solar Installation)      │
│ Trụ cột 4: Quy hoạch Không gian & Độ lệch Mùa vụ (Asset Allocation & Seasonality)           │
│ Trụ cột 5: Vận hành Bảo trì & Chẩn đoán Bệnh Vật lý (Condition-Based Maintenance)           │
│ Trụ cột 6: Khung Khuyến nghị Quản trị & Lộ trình Hành động 4 Giai đoạn (Governance Roadmap) │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### TRỤ CỘT 1: INSIGHTS KIẾN TRÚC DỮ LIỆU & SERVING LAYER (DATA LAKEHOUSE & BI MART)

- **Bài toán Fan-out Effect khi lệch pha chu kỳ:** Dữ liệu sản lượng telemetry phát sinh ở chu kỳ $15\text{ phút}$ ($2{,}73\text{ triệu dòng}$), trong khi dữ liệu thời tiết Open-Meteo phát sinh ở chu kỳ $1\text{ giờ}$ ($850.752\text{ dòng}$). Nếu thực hiện JOIN trực tiếp trên Tableau sẽ gây ra hiện tượng nhân bản dữ liệu thời tiết 4 lần (Fan-out), làm sai lệch tổng lượng bức xạ và quá tải RAM máy chủ.
- **Giải pháp Single Source of Truth cấp Giờ:** Nén toàn bộ 4 block 15p về cấp 1 giờ thông qua một Materialized View lõi duy nhất: `bi_mart.mv_bi_mart_hourly_measures` ($683.385\text{ dòng}$, dung lượng $< 80\,\text{MB}$). Dữ liệu cấp giờ vừa đủ chi tiết để Tableau phân tích hình thái nhật động trong ngày, vừa đủ gọn nhẹ để tải toàn bộ vào bộ nhớ tạm trong thời gian dưới $100\,\text{ms}$.
- **Tối ưu hóa Chi phí Hạ tầng qua Connection Pooling:** Kết nối Tableau trực tiếp vào Supabase PostgreSQL thông qua cổng **Supabase Connection Pooler (Port 6543)** ở chế độ Transaction Mode, sử dụng tài khoản chuyên dụng `tableau_user` chỉ cấp quyền `SELECT` trên schema `bi_mart`. Kiến trúc này vừa đảm bảo an toàn dữ liệu, vừa ngăn chặn hiện tượng rò rỉ kết nối (Connection Exhaustion) khi nhiều người dùng cùng truy cập Dashboard đồng thời.

---

### TRỤ CỘT 2: INSIGHTS ĐO LƯỜNG HIỆU NĂNG & BẢN CHẤT 3 BIẾN THỂ PR (IEC 61724-1)

- **Hiện tượng méo mó mùa hè của $PR_{\text{actual}}$:** Vào mùa hè, tổng sản lượng $kWh$ phát ra cao nhất năm nhưng chỉ số $PR_{\text{actual}}$ lại bị kéo tụt xuống mức thấp nhất ($< 75\%$). Đây là hiện tượng vật lý hoàn toàn bình thường do cell pin bị nung nóng trên $65^\circ\text{C}$ làm giảm điện áp hở mạch, không phải do thiết bị suy thoái.
- **Ý nghĩa sống còn của Mốc chuẩn Độc lập $PR_{\text{adjusted}} = 0{,}85 \times (1 - Loss_{\text{temp}})$:** Tuyệt đối không được tính $PR_{\text{adjusted}}$ dựa trên $PR_{\text{actual}}$. Con số $0{,}85$ ($85\%$) đại diện cho hiệu suất định mức của một hệ thống đạt chuẩn quốc tế ở điều kiện $25^\circ\text{C}$. Việc dùng mốc chuẩn độc lập giúp loại bỏ hoàn toàn **lỗi logic vòng lặp (Circular Logic)**: Nếu hệ thống bị hỏng làm $PR_{\text{actual}}$ tụt, đường chuẩn $PR_{\text{adjusted}}$ vẫn giữ nguyên ở mức kỳ vọng, giúp còi báo động O&M bật sáng ngay lập tức.
- **Bảo vệ Hợp đồng Vận hành (SLA) bằng $PR_{\text{correct}}$ (IEC 61724-1 Annex B):** Bằng cách bù trừ toàn bộ suy hao nhiệt về mốc chuẩn $25^\circ\text{C}$ ($\frac{PR_{\text{actual}}}{1 + \gamma \cdot \Delta T}$), $PR_{\text{correct}}$ của toàn mạng lưới đạt trên **$82\% - 85\%$ (chuẩn Class A)** xuyên suốt 12 tháng. Chỉ số này phản ánh độ khỏe thực chất của phần cứng, giúp chủ đầu tư và nhà thầu vận hành đối soát minh bạch, tránh các khoản phạt vi phạm hợp đồng vô lý.

---

### TRỤ CỘT 3: INSIGHTS KỸ THUẬT LẮP ĐẶT & VẬT LÝ TẢN NHIỆT GIẢM SUY HAO

Suy hao do nhiệt độ là nguyên nhân gây thất thoát năng lượng lớn nhất trong toàn bộ hệ thống (chiếm tới **$14{,}8\%$** sản lượng tiềm năng). Để giảm thiểu tổn thất này trong các dự án mở rộng, kỹ thuật lắp đặt thực tế cần tuân thủ 5 nguyên tắc:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                           5 NGUYÊN TẮC KỸ THUẬT LẮP ĐẶT GIẢM TỔN THẤT NHIỆT                 │
├──────────────────────────┬──────────────────────────────────────────────────────────────────┤
│ 1. Khoảng cách Hở Mái    │ Nâng chân tấm pin cách mái tôn từ 10 - 15 cm.                    │
│    (Standoff Height)     │ Tạo Hiệu ứng Ống khói Tự nhiên (Stack Effect) hạ 8 - 12°C.       │
├──────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ 2. Vị trí Lắp đặt Tối ưu │ Ưu tiên mô hình Solar Carport (Nhà để xe quang điện).            │
│                          │ Thông gió đa chiều 360°, nhiệt độ cell thấp hơn 12 - 15°C.       │
├──────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ 3. Hướng Lắp đặt         │ Hướng Bắc chuẩn (Azimuth 0°) để đạt sản lượng cực đại năm.       │
│    (Azimuth Orientation) │ Hướng Đông - Tây để san phẳng phụ tải và giảm đỉnh nhiệt trưa.   │
├──────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ 4. Góc Nghiêng Lắp đặt   │ Cố định 30° - 35° (bằng vĩ độ Victoria) giúp tự rửa sạch bụi bẩn.│
│    (Tilt Angle)          │ Giảm góc xuống 10° - 15° trên mái tôn phải tăng khoảng hở đáy.   │
├──────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ 5. Công nghệ Tấm pin     │ Tấm pin Kính kép 2 mặt (Bifacial Glass-Glass) tản nhiệt nhanh,   │
│                          │ hấp thụ thêm 10 - 15% bức xạ phản xạ mặt sau (Albedo gain).      │
└──────────────────────────┴──────────────────────────────────────────────────────────────────┘
```

1. **Khoảng cách nâng chân tấm pin cách mái (Standoff Height / Air Gap):**
   - *Thực trạng sai lầm:* Lắp đặt áp sát mặt mái tôn (Flush Mount, khoảng hở $< 5\,\text{cm}$) biến khoảng không bên dưới thành "túi khí nóng giam hãm", nhiệt độ cell pin dễ dàng vượt ngưỡng $70^\circ\text{C}$.
   - *Chuẩn kỹ thuật:* Bắt buộc lắp đặt khung nâng với khoảng cách từ mặt dưới tấm pin đến mái tôn tối thiểu từ **$10\,\text{cm} - 15\,\text{cm}$**. Khoảng hở này kích hoạt **Hiệu ứng Ống khói Tự nhiên (Natural Stack/Chimney Effect)**: Khí nóng bốc lên trên kéo theo luồng không khí mát từ chân giàn pin chạy luồn qua mặt dưới, giúp hạ nhiệt độ cell pin từ **$8^\circ\text{C} - 12^\circ\text{C}$**, phục hồi ngay $3\% - 4{,}5\%$ sản lượng điện.

2. **Vị trí Lắp đặt: Nhà để xe Quang điện (Solar Carport) vs Áp mái (Rooftop):**
   - **Solar Carport (Nhà để xe):** Là vị trí lắp đặt đạt **hiệu quả tản nhiệt tối ưu nhất** trong khuôn viên trường đại học/công sở:
     - Bốn mặt hoàn toàn lộ thiên, gió tự nhiên lưu thông đa chiều 360 độ $\implies$ Nhiệt độ vận hành cell pin thấp hơn từ **$12^\circ\text{C} - 15^\circ\text{C}$** so với giàn pin áp trên mái tôn kín.
     - Lợi ích kép: Che nắng làm mát xe cho cán bộ sinh viên, tích hợp trực tiếp trạm sạc xe điện thông minh (EV Charging Station).
   - **Áp mái công trình (Rooftop):** Tận dụng diện tích mái sẵn có nhưng bắt buộc phải sơn lớp phủ mái phản xạ nhiệt (Cool Roof Coating) màu trắng để giảm bức xạ nhiệt hấp thụ vào mặt lưng tấm pin.

3. **Hướng Lắp đặt (Azimuth) tại Bán cầu Nam (Úc):**
   - **Hướng Bắc chuẩn (True North, Azimuth $= 0^\circ$):** Là hướng tối ưu tuyệt đối để đón trọn vẹn quỹ đạo mặt trời quanh năm ở Bán cầu Nam, mang lại tổng sản lượng $kWh$ cả năm cao nhất.
   - **Hướng Đông - Tây (East-West Orientation):** Bố trí $50\%$ giàn pin hướng Đông và $50\%$ hướng Tây là giải pháp chiến lược cho các trường học:
     - Giúp sản xuất nhiều điện vào sáng sớm ($8\text{h} - 10\text{h}$) và chiều muộn ($14\text{h} - 16\text{h}$), trùng khớp với giờ học và làm việc cao điểm.
     - Triệt tiêu hiện tượng vọt đỉnh sản lượng lúc $12\text{h}$ trưa $\implies$ Hạ nhiệt độ cell pin từ **$5^\circ\text{C} - 8^\circ\text{C}$** và giảm thiểu tối đa hiện tượng xén công suất Inverter Clipping.
   - *Cảnh báo:* Tuyệt đối tránh hướng Nam ở Bán cầu Nam (dữ liệu EDA chứng minh các trạm hướng Tây Nam bị sụt giảm tới $38\%$ năng suất).

4. **Góc Nghiêng Lắp đặt (Tilt Angle):**
   - Góc nghiêng tối ưu quanh năm tại bang Victoria (vĩ độ $36^\circ\text{S} - 38^\circ\text{S}$) là **$30^\circ - 35^\circ$**.
   - Góc dốc $30^\circ - 35^\circ$ giúp tối đa hóa sản lượng vào các tháng mùa đông (khi mặt trời xuống thấp) và tạo độ dốc tự nhiên để nước mưa tự cuốn trôi bụi bẩn và phân chim (Self-cleaning), giảm chi phí bảo dưỡng vệ sinh.

5. **Công nghệ Tấm pin Kính kép 2 mặt (Bifacial Glass-Glass):**
   - Cấu trúc kính kép ở cả mặt trước và mặt sau giúp dẫn nhiệt và bức xạ nhiệt ra môi trường nhanh hơn cấu trúc tấm nền nhựa truyền thống (Polymer Backsheet).
   - Khi lắp trên Solar Carport hoặc mái nhà có sơn phản quang, mặt sau tấm pin hấp thụ thêm bức xạ phản xạ mặt đất (Albedo Gain) giúp tăng thêm $10\% - 15\%$ tổng sản lượng điện.

---

### TRỤ CỘT 4: INSIGHTS QUY HOẠCH KHÔNG GIAN & ĐỘ LỆCH MÙA VỤ (ASSET ALLOCATION & SEASONALITY)

- **Độ lệch Mùa vụ Cực đoan 3.5 lần:** Do vị trí địa lý ở vĩ độ cận cực của bang Victoria, hệ số công suất mùa hè đạt đỉnh $CF \approx 20{,}0\%$, nhưng mùa đông tụt dốc xuống chỉ còn $7{,}03\%$. *Khuyến nghị:* Nhà trường không thể dựa hoàn toàn vào điện mặt trời trực tiếp vào mùa đông nếu không có **Hệ thống Pin Lưu trữ Năng lượng BESS** để tích trữ và điều hòa phụ tải.
- **Rủi ro Tập trung Tài sản & Lệch pha Địa lý:**
  - $84{,}98\%$ tổng sản lượng hiện tại đang dồn về 2 cơ sở: Bundoora ($61{,}63\%$) và Bendigo ($23{,}35\%$).
  - Trong khi đó, cơ sở **Mildura** — nơi có bức xạ mặt trời dồi dào nhất toàn bang Victoria ($5{,}7\text{ Peak Sun Hours/ngày}$, cao hơn Melbourne $35\%$) — mới chỉ chiếm vỏn vẹn $3{,}82\%$ công suất lắp đặt.
  - *Khuyến nghị Chiến lược:* Dự án mở rộng giai đoạn 2 bắt buộc phải ưu tiên giải ngân vốn đầu tư lắp đặt giàn pin tại khuôn viên Mildura để tận dụng tối đa nguồn tài nguyên nắng tự nhiên.

---

### TRỤ CỘT 5: INSIGHTS VẬN HÀNH O&M & CHẨN ĐOÁN BỆNH VẬT LÝ (CBM)

- **Tỷ lệ Ngoại lai An toàn ($0{,}45\% - 0{,}80\%$):** Toàn bộ 42 trạm chỉ phát sinh $7.431$ dòng dị thường thực sự ($0{,}27\%$ toàn tập dữ liệu), nằm hoàn toàn trong ngưỡng kiểm soát an toàn của ngành quang điện ($< 5\%$).
- **Chẩn đoán Phân biệt 3 Nhóm Bệnh Vật lý Đặc trưng:**
  1. *Lỗi Inverter Quá áp Lưới / Quá nhiệt (`PHYSICAL_LOW_ENERGY_STRONG_SUN`):* Chiếm tới $60\%$ thiệt hại sản lượng do sự cố. Thường xảy ra vào giờ trưa nắng gắt khi điện áp lưới vượt ngưỡng bảo vệ ($> 253\text{V}$) hoặc quạt tản nhiệt Inverter bị kẹt $\implies$ Giải pháp: Cân chỉnh nấc phân áp máy biến áp và bảo dưỡng quạt làm mát định kỳ vào Tháng 9.
  2. *Lỗi Đứt Cầu chì Chuỗi Pin (String-level Fuse Blown):* Sản lượng cả ngày chạy bình thường nhưng bị tụt cố định một tỷ lệ $33\%$ hoặc $50\%$ so với đường chuẩn $E_{\text{expected}}$ $\implies$ Giải pháp: Kỹ sư dùng đồng hồ Ampe kìm đo dòng DC từng chuỗi và thay cầu chì ngay trong ngày.
  3. *Lỗi Sai lệch Mốc 0 Cảm biến Ban đêm (`PHYSICAL_HIGH_ENERGY_NO_SUN`):* Xuất hiện các giá trị $E > 0$ từ $18\text{h}30$ đến $05\text{h}30$ khi bức xạ $= 0$ $\implies$ Giải pháp: Hiệu chuẩn lại biến dòng CT và kiểm tra mạch bảo vệ chống dòng điện ngược.
- **Rửa Pin Thông minh theo Điều kiện (Condition-Based Cleaning):** Chỉ phát lệnh rửa pin khi tỷ lệ suy hao do bụi bẩn vượt ngưỡng $5\%$ sau chuỗi 40 ngày không có mưa lớn, giúp trường tiết kiệm chi phí dịch vụ và hàng chục nghìn lít nước mỗi năm.

---

### TRỤ CỘT 6: KHUNG KHUYẾN NGHỊ QUẢN TRỊ & LỘ TRÌNH HÀNH ĐỘNG 4 GIAI ĐOẠN

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                          LỘ TRÌNH HÀNH ĐỘNG THỰC TẾ DÀNH CHO BAN QUẢN TRỊ                   │
├─────────────┬───────────────────────────┬───────────────────────────────────────────────────┤
│ Giai đoạn   │ Tên Giai đoạn             │ Các Hành động Trọng tâm Cần triển khai            │
├─────────────┼───────────────────────────┼───────────────────────────────────────────────────┤
│ **Pha 1**   │ Bảo dưỡng Phòng ngừa O&M  │ - Vệ sinh và kiểm tra toàn bộ quạt tản nhiệt      │
│ (Ngay lập   │ (Pre-Summer Maintenance)  │   Inverter vào Tháng 9 trước mùa nóng.            │
│  tức)       │                           │ - Hiệu chuẩn lại cảm biến biến dòng CT ban đêm.   │
├─────────────┼───────────────────────────┼───────────────────────────────────────────────────┤
│ **Pha 2**   │ Cải tạo Tản nhiệt Hạ tầng │ - Nâng khung giàn pin áp mái đạt khoảng hở 10-15cm│
│ (3-6 tháng) │ (Thermal Retrofit)        │ - Thí điểm mô hình Solar Carport tại bãi xe.      │
│             │                           │ - Sơn phủ lớp phản xạ nhiệt trắng trên mái tôn.   │
├─────────────┼───────────────────────────┼───────────────────────────────────────────────────┤
│ **Pha 3**   │ Mở rộng Công suất Mildura │ - Giải ngân vốn mở rộng mảng pin tại Mildura      │
│ (6-12 tháng)│ (Geographic Expansion)    │   (nơi có bức xạ 5.7 PSH cao nhất bang).          │
│             │                           │ - Chuẩn hóa sử dụng tấm pin Monocrystalline.      │
├─────────────┼───────────────────────────┼───────────────────────────────────────────────────┤
│ **Pha 4**   │ Tích hợp Hệ thống Pin BESS│ - Lắp đặt hệ thống pin lưu trữ năng lượng BESS    │
│ (12-24 tháng│ (Energy Storage System)   │   để điều hòa phụ tải giữa mùa hè và mùa đông.    │
│  tới)       │                           │ - Hoàn thành mục tiêu Tự chủ Năng lượng Net Zero. │
└─────────────┴───────────────────────────┴───────────────────────────────────────────────────┘
```
