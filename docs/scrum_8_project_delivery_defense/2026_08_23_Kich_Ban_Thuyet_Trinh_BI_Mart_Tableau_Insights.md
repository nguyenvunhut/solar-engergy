# KỊCH BẢN THUYẾT TRÌNH BẢO VỆ ĐỒ ÁN TỐT NGHIỆP
## PHÂN HỆ: BI DATA MART, BỘ CHỈ SỐ METRICS, HỆ THỐNG DASHBOARD TABLEAU VÀ INSIGHTS CHIẾN LƯỢC

> **Đề tài:** Hệ thống Xử lý Dữ liệu, Nhận diện Dị thường Vận hành và Dự báo Sản lượng 42 Trạm Điện Mặt Trời tại Úc  
> **Nhóm thực hiện:** The Outliers — Chuyên ngành Xử lý Dữ liệu (Data Analytics)  
> **Thời lượng trình bày phân hệ:** 7 – 8 phút (trong tổng thời lượng 20 phút của nhóm)  
> **Cấu trúc trình bày mỗi Slide:** **VẤN ĐỀ CẦN GIẢI QUYẾT -> THỰC THI & GIẢI PHÁP KỸ THUẬT -> KẾT QUẢ & GIÁ TRỊ MANG LẠI**  
> **Phong cách trình bày:** Tự tin, mạch lạc, ngôn ngữ nói tự nhiên, làm chủ số liệu, tập trung vào *"Bản chất vật lý"*, *"Dữ liệu biết nói"* và *"Giải thích nguyên nhân cốt lõi"*.

---

## MỤC LỤC KỊCH BẢN

- [PHẦN 1: SCRIPT THUYẾT TRÌNH THEO CẤU TRÚC (VẤN ĐỀ -> THỰC THI -> KẾT QUẢ)](#phần-1-script-thuyết-trình-theo-cấu-trúc-vấn-đề---thực-thi---kết-quả)
  - [Slide 1: Kiến trúc Tầng Phục vụ Dữ liệu BI Mart (Serving Layer) (1.0 phút)](#slide-1-kiến-trúc-tầng-phục-vụ-dữ-liệu-bi-mart-serving-layer-thời-lượng-10-phút)
  - [Slide 2: Khung Bộ Chỉ số Đo lường & Quản trị Cốt lõi (Core BI Metrics) (2.0 phút)](#slide-2-khung-bộ-chỉ-số-đo-lường--quản-trị-cốt-lõi-core-bi-metrics-thời-lượng-20-phút)
  - [Slide 3: Dashboard 1 — Executive Overview (Tổng quan Vận hành & ESG) (1.5 phút)](#slide-3-dashboard-1--executive-overview-tổng-quan-vận-hành--esg-thời-lượng-15-phút)
  - [Slide 4: Dashboard 2 — Operational Efficiency & Loss Analysis (1.5 phút)](#slide-4-dashboard-2--operational-efficiency--loss-analysis-thời-lượng-15-phút)
  - [Slide 5: Dashboard 3 — Anomaly Detection & Predictive Maintenance (1.5 phút)](#slide-5-dashboard-3--anomaly-detection--predictive-maintenance-thời-lượng-15-phút)
- [PHẦN 2: BATTLECARDS — BỘ CÂU HỎI PHẢN BIỆN HÓC BÚA TỪ HỘI ĐỒNG](#phần-2-battlecards--bộ-câu-hỏi-phản-biện-hóc-búa-từ-hội-đồng)
- [PHẦN 3: TỔNG HỢP 5 KEY INSIGHTS & KHUYẾN NGHỊ HÀNH ĐỘNG (CHEATSHEET)](#phần-3-tổng-hợp-5-key-insights--khuyến-nghị-hành-động-cheatsheet)

---

# PHẦN 1: SCRIPT THUYẾT TRÌNH THEO CẤU TRÚC (VẤN ĐỀ -> THỰC THI -> KẾT QUẢ)

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
  Bảng sự kiện sản lượng `fact_solar_energy_gen` có quy mô hơn **$2{,}73\text{ triệu dòng}$** đo mỗi $15\text{ phút}$, trong khi dữ liệu thời tiết lại là cấp $1\text{ giờ}$. Nếu thực hiện phép JOIN trực tiếp trên Tableau và bắt công cụ tự tính toán các chỉ số phức tạp như hệ số hiệu suất PR hay suy hao nhiệt độ, mỗi lần người dùng bấm lọc trạm màn hình sẽ bị trễ, làm quá tải tài nguyên máy chủ cơ sở dữ liệu.

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
*(Thời lượng: ~2.0 phút)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [HÀNH ĐỘNG THUYẾT TRÌNH]:                                                              │
│ - Chiếu Slide bảng ma trận các Metrics: PR, CF, Yield, Loss Breakdown, Financial/ESG. │
│ - Nhấn mạnh vào bản chất của 3 biến thể PR (PR actual, PR adjusted, PR correct).       │
│ - Giọng nói giải thích tự tin, làm nổi bật tư duy toán học và nghiệp vụ ngành quang điện.│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**[Lời thoại thuyết trình]:**

"Trước khi đưa số liệu lên giao diện, nhóm em đã chuẩn hóa toàn bộ hệ thống đo lường theo tiêu chuẩn quốc tế **IEC 61724-1**:

* **1. VẤN ĐỀ CẦN GIẢI QUYẾT (The Problem):**  
  Nếu chỉ nhìn vào sản lượng điện ($kWh$), chúng ta không thể so sánh được hiệu quả giữa trạm nhỏ ($10\,\text{kWp}$) và trạm lớn ($500\,\text{kWp}$). Nghiêm trọng hơn, vào mùa hè trời nắng gắt, nhiệt độ cao làm tấm pin bị nóng khiến hiệu suất bị tụt tự nhiên. Nếu không bóc tách được yếu tố nhiệt độ, hệ thống sẽ phát cảnh báo giả rằng thiết bị bị hỏng.

* **2. THỰC THI & GIẢI PHÁP KỸ THUẬT (Implementation):**  
  Nhóm em đã phân rã toán học thành **3 biến thể Performance Ratio (PR)** độc lập:
  - **$PR_{\text{actual}}$ (Hiệu suất đo thô):** Tỷ lệ giữa điện thực tế và lý thuyết ($E_{\text{actual}} / E_{\text{theo}}$). Phản ánh thực trạng tức thời nhưng chịu đủ suy hao nhiệt mùa hè.
  - **$PR_{\text{adjusted}}$ (Hiệu suất kỳ vọng BI Mart):** Tính bằng $0{,}85 \times (1 - Loss_{\text{temp}})$. Nhóm dùng con số $0{,}85$ làm mốc chuẩn thiết kế định mức độc lập ở $25^\circ\text{C}$ để trả lời câu hỏi: *'Với trời nóng này, một trạm chuẩn thì kỳ vọng PR phải đạt bao nhiêu?'*. Nhóm tuyệt đối không tính từ $PR_{\text{actual}}$ để tránh lỗi vòng lặp logic (Circular Logic) làm mất khả năng báo hỏng.
  - **$PR_{\text{correct}}$ (Hiệu suất chuẩn hóa nhiệt IEC 61724-1):** Bù trừ suy hao nhiệt về mốc $25^\circ\text{C}$ ($\frac{PR_{\text{actual}}}{1 + \gamma \cdot \Delta T}$). Chỉ số này phản ánh chính xác **độ khỏe nội tại của phần cứng**, dùng để bảo vệ hợp đồng bảo trì (SLA).

* **3. KẾT QUẢ ĐẠT ĐƯỢC (Result & Impact):**  
  - Thiết lập thành công bộ chỉ số toàn diện: Hệ số công suất $CF = 17{,}2\%$, Năng suất riêng $Y_f = 4{,}35\text{ kWh/kWp/ngày}$, Phân rã tổn thất nhiệt $14{,}8\%$, Clipping $2{,}3\%$, Doanh thu FiT và Giảm phát thải $\text{CO}_2$ ($0{,}82\text{ kg/kWh}$).
  - Cung cấp cơ sở định lượng để phân biệt chính xác giữa *Suy hao nhiệt tự nhiên* và *Sự cố hỏng hóc thiết bị*."

---

### Slide 3: Dashboard 1 — Executive Overview (Tổng quan Vận hành & ESG)
*(Thời lượng: ~1.5 phút)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [HÀNH ĐỘNG THUYẾT TRÌNH]:                                                              │
│ - Chuyển sang giao diện Dashboard 1 trên Tableau.                                      │
│ - Tay chỉ lần lượt: Dải thẻ BANs trên cùng -> Bản đồ khuôn viên -> Biểu đồ mùa vụ.    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**[Lời thoại thuyết trình]:**

"Giao diện đầu tiên là **Dashboard 1 — Executive Overview**, đóng vai trò là trung tâm chỉ huy dành cho Ban Giám hiệu:

* **1. VẤN ĐỀ CẦN GIẢI QUYẾT (The Problem):**  
  Ban Giám hiệu thiếu một góc nhìn tổng thể đa chiều về sức khỏe vận hành của 42 trạm phân tán, không nắm được tiến độ hoàn thành mục tiêu tài chính tiết kiệm điện và chỉ tiêu phát triển bền vững Net Zero của trường.

* **2. THỰC THI & GIẢI PHÁP KỸ THUẬT (Implementation):**  
  Nhóm em thiết kế Dashboard 1 theo bố cục Gestalt F-Pattern chuẩn mực:
  - **Dải chỉ số BANs trên cùng:** Tích hợp tổng sản lượng lũy kế, $PR$, $CF$ và khối lượng $\text{CO}_2$ cắt giảm.
  - **Bản đồ địa lý 42 trạm:** Trực quan hóa quy mô công suất và tô màu theo hệ số công suất CF.
  - **Biểu đồ xu hướng mùa vụ:** Phân tích sản lượng theo từng tháng và theo từng dòng tấm pin.

* **3. KẾT QUẢ & INSIGHTS CHIẾN LƯỢC (Result & Key Insights):**  
  - **Số liệu tổng kết:** Đạt tổng sản lượng **$74{,}98\text{ GWh}$**, tiết kiệm hơn **$11{,}2\text{ triệu AUD}$**, $PR = 78{,}4\%$ (chuẩn **Class A**), cắt giảm **$61.485\text{ tấn }\text{CO}_2$** (tương đương trồng $2{,}8\text{ triệu}$ cây xanh).
  - **Insight 1 — Bất đối xứng Mùa vụ 3.5 lần:** Mùa hè $CF \approx 20\%$, nhưng mùa đông tụt xuống $7{,}03\%$. *Khuyến nghị:* Trường bắt buộc phải đầu tư hệ thống pin lưu trữ BESS để đạt tự chủ năng lượng 100%.
  - **Insight 2 — Rủi ro Tập trung Tài sản:** Cơ sở Bundoora và Bendigo gánh tới $84{,}4\%$ sản lượng, trong khi cơ sở **Mildura** — nơi nắng tốt nhất bang ($5{,}7\text{ kWh/m}^2/\text{ngày}$) — mới chỉ đóng góp $3{,}96\%$. *Khuyến nghị:* Ưu tiên giải ngân mở rộng mảng pin tại Mildura trong giai đoạn 2."

---

### Slide 4: Dashboard 2 — Operational Efficiency & Loss Analysis
*(Thời lượng: ~1.5 phút)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [HÀNH ĐỘNG THUYẾT TRÌNH]:                                                              │
│ - Chuyển Slide sang Dashboard 2.                                                       │
│ - Nhấn mạnh vào biểu đồ 2 trục tọa độ (Dual-Axis) và Bản đồ nhiệt (Heatmap) suy hao.  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**[Lời thoại thuyết trình]:**

"Tiếp theo là **Dashboard 2: Operational Efficiency & Loss Analysis**, công cụ chẩn đoán chuyên sâu dành cho Kỹ sư Năng lượng:

* **1. VẤN ĐỀ CẦN GIẢI QUYẾT (The Problem):**  
  Kỹ sư vận hành nhìn thấy hiện tượng nghịch lý: Giữa trưa nắng gắt nhất nhưng sản lượng lại bị chững lại hoặc suy giảm; đồng thời có hiện tượng đồ thị bị cắt bằng ở đỉnh (Clipping), làm dấy lên nghi ngờ Inverter bị lỗi kỹ thuật.

* **2. THỰC THI & GIẢI PHÁP KỸ THUẬT (Implementation):**  
  Nhóm em xây dựng các công cụ trực quan giải thích nguyên nhân gốc rễ:
  - **Đồ thị 2 trục tọa độ (Dual-Axis):** Lồng ghép Sản lượng thực tế, Bức xạ $GHI$ và Nhiệt độ bề mặt pin $T_{\text{cell}}$.
  - **Bản đồ nhiệt Tổn thất (Loss Heatmap):** Phân rã tỷ lệ suy hao nhiệt theo 12 tháng trong năm và theo 42 trạm.
  - **Biểu đồ Benchmark thiết bị:** So sánh năng suất riêng ($Y_f$) giữa các dòng pin và biến tần.

* **3. KẾT QUẢ & PHÁT HIỆN KỸ THUẬT (Result & Key Insights):**  
  - **Minh oan cho thiết bị:** Chứng minh thủ phạm lớn nhất làm giảm sản lượng là **Suy hao do Quá nhiệt**, chiếm tới **$14{,}8\%$** tổng năng lượng tiềm năng ($> 120.000\text{ AUD/năm}$) khi bề mặt pin bị nung nóng lên tới $68^\circ\text{C} - 72^\circ\text{C}$ lúc trưa hè.
  - **Làm rõ bản chất Inverter Clipping ($2{,}3\%$):** Đây là thiết kế có chủ đích theo tỷ lệ quá tải DC/AC ($ILR = 1{,}25$), giúp Inverter chạy tối ưu trong $97{,}7\%$ thời gian còn lại, mang lại tổng sản lượng ngày cao hơn $8 - 12\%$.
  - **Xác nhận chất lượng phần cứng:** Dòng pin SunPower Mono-Si kết hợp Inverter SMA/Fronius đạt năng suất $4{,}35\text{ kWh/kWp/ngày}$, vượt trội $38\%$ so với pin Poly-Si hướng Tây Nam."

---

### Slide 5: Dashboard 3 — Anomaly Detection & Predictive Maintenance
*(Thời lượng: ~1.5 phút)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [HÀNH ĐỘNG THUYẾT TRÌNH]:                                                              │
│ - Chuyển Slide sang Dashboard 3.                                                       │
│ - Chỉ vào các điểm đỏ dị thường và dải đỏ ban đêm trên Heatmap.                        │
│ - Kết bài dứt khoát, tự tin, nêu bật giá trị thu hồi tài chính.                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**[Lời thoại thuyết trình]:**

"Cuối cùng là **Dashboard 3: Anomaly Detection** — hệ thống cảnh báo sớm giúp chuyển đổi mô hình bảo trì O&M:

* **1. VẤN ĐỀ CẦN GIẢI QUYẾT (The Problem):**  
  Mô hình bảo trì truyền thống mắc 2 nhược điểm lớn:
  1. *Bảo trì thụ động ("Hỏng mới sửa"):* Trạm bị đứt cầu chì chuỗi làm hụt $33\%$ sản lượng nhưng phải chờ cả tháng đối soát hóa đơn mới biết, gây mất trắng doanh thu mùa cao điểm.
  2. *Bảo trì định kỳ ("3 tháng rửa pin 1 lần"):* Lãng phí tiền bạc đi rửa các trạm đang sạch, trong khi trạm bị bẩn sau bão cát lại phải chờ 3 tháng mới được xử lý.

* **2. THỰC THI & GIẢI PHÁP KỸ THUẬT (Implementation):**  
  Nhóm em tích hợp trực quan toàn bộ kết quả từ mô hình lai GMM-IF và 5 rào chắn vật lý:
  - **Time-series Highlighter:** Đánh dấu điểm đỏ tức thời tại các mốc thời gian dị thường, hover chuột là thấy ngay mã nguyên nhân kỹ thuật (`gmm_if_outlier_reason`).
  - **Bản đồ nhiệt 24h:** Nhận diện ngay các dòng rò rỉ điện ban đêm ($18\text{h}30 - 5\text{h}30$).

* **3. KẾT QUẢ & GIÁ TRỊ O&M THỰC TIỄN (Result & Impact):**  
  - **Kiểm soát ngoại lai xuất sắc:** Bóc tách chính xác **$0{,}27\%$** dị thường thực sự ($7.431$ dòng), nằm hoàn toàn trong ngưỡng an toàn ngành ($< 5\%$).
  - **Bắt đúng 3 nhóm bệnh:** Phát hiện lỗi quá áp lưới/quá nhiệt Inverter ($60\%$ thiệt hại), lỗi đứt cầu chì chuỗi pin (hụt cố định $33\%/50\%$) và lỗi lệch mốc 0 cảm biến CT ban đêm.
  - **Hiệu quả kinh tế vượt trội:** Đề xuất lịch bảo dưỡng quạt Inverter tháng 9 và lịch rửa pin thông minh theo điều kiện, giúp trường Đại học La Trobe **thu hồi thêm $72.750\text{ AUD/năm}$**, thời gian hoàn vốn đầu tư **dưới 4,5 tháng**.

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
  Hiện tượng clipping chỉ xảy ra khoảng $1 - 2$ tiếng giữa trưa của vài ngày nắng đỉnh mùa hè (chiếm $2{,}3\%$ năm). Nếu nâng công suất Inverter để lấy $2{,}3\%$ này, chi phí mua Inverter lớn hơn và nâng cấp hạ tầng điện sẽ tốn thêm hàng trăm nghìn AUD, trong khi phần lớn thời gian còn lại trong năm Inverter sẽ chạy non tải với hiệu suất thấp. Do đó, mức tổn thất $2{,}3\%$ là mức đánh đổi kinh tế hoàn toàn tối ưu ạ."

---

#### Câu hỏi 4: "Tại sao nhóm chỉ dùng một Materialized View mv_bi_mart_hourly_measures mà không tạo thêm View cấp ngày?"
* **Cách trả lời ăn điểm:**
  "Dạ thưa Thầy/Cô, đây là quyết định tối ưu hóa kiến trúc DWH của nhóm:
  1. **Đơn nhất nguồn dữ liệu (Single Source of Truth):** Dữ liệu cấp giờ ($683.385$ dòng sau khi nén từ $2{,}73$ triệu dòng) có dung lượng rất nhẹ ($< 80\,\text{MB}$), hoàn toàn nằm gọn trong bộ nhớ RAM của máy chủ và Tableau Data Engine.
  2. **Tính linh hoạt tối đa:** Giữ mức độ chi tiết (Granularity) ở cấp giờ cho phép Tableau thực hiện linh hoạt mọi phép khoan sâu (Drill-down) theo khung giờ, theo ca trực, hoặc gom nhóm động theo Ngày, Tuần, Tháng, Năm bằng các hàm LOD và Date Trunc mà không cần duy trì nhiều View trùng lặp, giúp giảm $50\%$ chi phí bảo trì và thời gian làm mới (Refresh) cơ sở dữ liệu ạ."

---

# PHẦN 3: TỔNG HỢP 5 KEY INSIGHTS & KHUYẾN NGHỊ HÀNH ĐỘNG (CHEATSHEET)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            TỔNG HỢP 5 KEY INSIGHTS & KHUYẾN NGHỊ QUẢN TRỊ                   │
├────────────────────────────────┬────────────────────────────────────────────────────────────┤
│ 1. Độ lệch Mùa vụ Cực đoan     │ Sản lượng Hè gấp 3.5 lần Đông (CF: 20.00% vs 7.03%).       │
│                                │ Khuyến nghị: Bắt buộc đầu tư hệ thống BESS để trữ điện.    │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ 2. Rủi ro Tập trung Tài sản    │ Bundoora & Bendigo chiếm 84.4% sản lượng.                  │
│                                │ Khuyến nghị: Ưu tiên mở rộng sang Mildura (nơi nắng tốt nhất).│
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ 3. Suy hao do Quá nhiệt Áp đảo │ Nhiệt độ cell pin mùa hè lên 72°C làm mất 14.8% sản lượng. │
│                                │ Khuyến nghị: Lắp tấm che nắng, bảo dưỡng quạt Inverter T9. │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ 4. Tối ưu Inverter Clipping    │ Clipping chỉ chiếm 2.3% năm (thiết kế có chủ đích ILR=1.25).│
│                                │ Khuyến nghị: Giữ nguyên cấu hình, không lãng phí thay thế. │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ 5. Chuyển đổi Vận hành O&M     │ Outlier Rate ở mức 0.27% (rất an toàn); bắt đúng lỗi rò đêm.│
│                                │ Giá trị: Thu hồi 72.750 AUD/năm, hoàn vốn trong 4.5 tháng.  │
└────────────────────────────────┴────────────────────────────────────────────────────────────┘
```
