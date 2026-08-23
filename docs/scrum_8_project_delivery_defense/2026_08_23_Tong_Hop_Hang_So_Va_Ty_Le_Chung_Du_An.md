# TỔNG HỢP TOÀN BỘ HẰNG SỐ TÍNH TOÁN VÀ TỶ LỆ CHUẨN CỦA DỰ ÁN
## TÀI LIỆU TRA CỨU ĐỘ SÂU & ĐỐI SOÁT BẢO VỆ ĐỒ ÁN TỐT NGHIỆP

> **Dự án:** Hệ thống Xử lý Dữ liệu, Nhận diện Dị thường Vận hành và Dự báo Sản lượng 42 Trạm Điện Mặt Trời tại Úc  
> **Nhóm thực hiện:** The Outliers — Chuyên ngành Xử lý Dữ liệu (Data Analytics)  
> **Vị trí lưu trữ:** `docs/scrum_8_project_delivery_defense/2026_08_23_Tong_Hop_Hang_So_Va_Ty_Le_Chung_Du_An.md`  
> **Mục đích:** Tra cứu toàn bộ các hằng số toán học, vật lý, tham số kỹ nghệ dữ liệu, ngưỡng mô hình học máy và tỷ lệ kinh tế/ESG được áp dụng trong mã nguồn và báo cáo đồ án.

---

## MỤC LỤC TỔNG QUAN

- [PHẦN 1: HẰNG SỐ VẬT LÝ QUANG ĐIỆN & THIÊN VĂN HỌC (SOLAR PHYSICS & ASTRONOMICAL)](#phần-1-hằng-số-vật-lý-quang-điện--thiên-văn-học-solar-physics--astronomical)
- [PHẦN 2: HẰNG SỐ QUẢN TRỊ HIỆU SUẤT, TÀI CHÍNH & ESG (BI MART & BUSINESS)](#phần-2-hằng-số-quản-trị-hiệu-suất-tài-chính--esg-bi-mart--business)
- [PHẦN 3: HẰNG SỐ ĐIỀN KHUYẾT NHÂN QUẢ & XỬ LÝ LƯỚI THỜI GIAN (ETL & IMPUTATION)](#phần-3-hằng-số-điền-khuyết-nhân-quả--xử-lý-lưới-thời-gian-etl--imputation)
- [PHẦN 4: HẰNG SỐ PHÂN LỚP DỊ THƯỜNG LAI GMM-IF & 5 RÀO CHẮN VẬT LÝ](#phần-4-hằng-số-phân-lớp-dị-thường-lai-gmm-if--5-rào-chắn-vật-lý)
- [PHẦN 5: HẰNG SỐ BIẾN ĐỔI ĐẶC TRƯNG & HUẤN LUYỆN MÔ HÌNH HỌC MÁY (ML PIPELINE)](#phần-5-hằng-số-biến-đổi-đặc-trưng--huấn-luyện-mô-hình-học-máy-ml-pipeline)
- [PHẦN 6: BẢNG TRA CỨU NHANH MATRIX TOÀN BỘ HẰNG SỐ (MASTER CONSTANTS CHEATSHEET)](#phần-6-bảng-tra-cứu-nhanh-matrix-toàn-bộ-hằng-số-master-constants-cheatsheet)

---

# PHẦN 1: HẰNG SỐ VẬT LÝ QUANG ĐIỆN & THIÊN VĂN HỌC (SOLAR PHYSICS & ASTRONOMICAL)

---

### 1. Bức xạ Tiêu chuẩn STC ($G_{\text{STC}}$)
- **Tên biến trong mã nguồn:** `G_STC`, `GHI_STC`, `standard_irradiance`
- **Giá trị & Đơn vị:** $1000\,\text{W/m}^2$ ($1{,}0\,\text{kW/m}^2$)
- **Từ đâu có:** Tiêu chuẩn quốc tế **IEC 60904-3** về Điều kiện Thử nghiệm Tiêu chuẩn (Standard Test Conditions — STC) của tấm pin quang điện.
- **Ý nghĩa:** Là mật độ thông lượng bức xạ mặt trời quy ước chiếu vuông góc lên bề mặt tấm pin ở mực nước biển vào ngày trời trong không mây.
- **Áp dụng cho:**
  - Tính sản lượng lý thuyết: $E_{\text{theo}} = P_{\text{stc}} \times (GHI / 1000) \times \Delta t$.
  - Tính Hệ số Hiệu suất thô: $PR_{\text{actual}} = E_{\text{actual}} / E_{\text{theo}}$.
  - Tính Năng suất tham chiếu: $Y_r = GHI / 1000 \times \Delta t$.

---

### 2. Nhiệt độ Cell Tiêu chuẩn STC ($T_{\text{STC}}$)
- **Tên biến trong mã nguồn:** `T_STC`, `temp_stc_c`
- **Giá trị & Đơn vị:** $25^\circ\text{C}$ ($298{,}15\,\text{K}$)
- **Từ đâu có:** Tiêu chuẩn quốc tế **IEC 60904-3** (STC Benchmark).
- **Ý nghĩa:** Mốc nhiệt độ môi trường phòng thí nghiệm chuẩn để kiểm định công suất danh định $P_{\text{stc}}$ của cell pin.
- **Áp dụng cho:**
  - Tính độ lệch nhiệt độ cell: $\Delta T = T_{\text{cell}} - 25^\circ\text{C}$.
  - Tính hệ số hiệu chỉnh $PR_{\text{correct}}$ theo **IEC 61724-1 Phụ lục B**.

---

### 3. Khối lượng Khí quyển Tiêu chuẩn (Air Mass — AM)
- **Tên biến trong mã nguồn:** `AIR_MASS_STC`, `air_mass_1_5`
- **Giá trị & Đơn vị:** $1{,}5$ (không thứ nguyên)
- **Từ đâu có:** Tiêu chuẩn **ASTM G173-03** / **IEC 60904-3**.
- **Ý nghĩa:** Độ dài đường đi của ánh sáng mặt trời qua bầu khí quyển Trái Đất so với đường đi thẳng đứng ở thiên đỉnh ($AM = 1 / \cos(\theta_z) \approx 1{,}5$ khi mặt trời ở góc nâng $41{,}81^\circ$).
- **Áp dụng cho:** Cơ sở chuẩn hóa phổ bức xạ khi tính toán hình học mặt trời và hiệu suất danh định.

---

### 4. Hệ số Suy giảm Công suất theo Nhiệt độ ($\gamma$)
- **Tên biến trong mã nguồn:** `temp_coefficient_per_deg`, `gamma_pmp`
- **Giá trị & Đơn vị:** $-0{,}0038 /^\circ\text{C}$ (tức $-0{,}38\% /^\circ\text{C}$; cấu hình dự phòng `0.004` trong `01_bi_mart_params.yaml`)
- **Từ đâu có:** Bảng thông số kỹ thuật (Datasheet) của tấm pin Silicon tinh thể (Monocrystalline SunPower SPR-E20 & Polycrystalline Trina Solar TSM-PD05) và chuẩn hóa theo Sandia National Laboratories / NREL.
- **Ý nghĩa:** Cứ mỗi $1^\circ\text{C}$ nhiệt độ cell pin tăng vượt quá mốc $25^\circ\text{C}$, công suất phát cực đại ($P_{\text{mp}}$) bị sụt giảm $0{,}38\%$ do hiệu ứng nhiệt làm thu hẹp dải vùng cấm bán dẫn (Bandgap).
- **Áp dụng cho:**
  - Tính tỷ lệ suy hao nhiệt: $Loss_{\text{temp}} = 0{,}0038 \times \max(0, T_{\text{cell}} - 25^\circ\text{C})$.
  - Tính $PR_{\text{adjusted}} = 0{,}85 \times (1 - Loss_{\text{temp}})$.
  - Bù trừ nhiệt cho $PR_{\text{correct}} = \frac{PR_{\text{actual}}}{1 + \gamma \cdot (T_{\text{cell}} - 25^\circ\text{C})}$.

---

### 5. Hệ số Truyền nhiệt Bức xạ lên Cell Pin ($k_{\text{cell}}$)
- **Tên biến trong mã nguồn:** `noct_radiation_factor`, `ross_factor`
- **Giá trị & Đơn vị:** $0{,}03\,^\circ\text{C} / (\text{W/m}^2)$
- **Từ đâu có:** Mô hình thực nghiệm nhiệt động học **Ross Model (1976)** và kiểm nghiệm thực địa của **King et al. (Sandia National Laboratories, 2004)** cho hệ thống áp mái (Rooftop PV).
- **Ý nghĩa:** Cứ mỗi $100\,\text{W/m}^2$ bức xạ chiếu vào, cell pin nóng thêm $3^\circ\text{C}$ so với nhiệt độ không khí xung quanh ($T_{\text{ambient}}$).
- **Áp dụng cho:**
  - Ước tính nhiệt độ cell pin: $T_{\text{cell}} = T_{\text{ambient}} + (GHI \times 0{,}03)$.
  - Tầng tính toán Materialized View `bi_mart.mv_bi_mart_hourly_measures`.

---

### 6. Ngưỡng Lọc Bức xạ Ngày theo Tiêu chuẩn IEC ($GHI_{\text{IEC\_filter}}$)
- **Tên biến trong mã nguồn:** `min_radiation_threshold_wm2`, `GHI_MIN_DAYLIGHT`
- **Giá trị & Đơn vị:** $100\,\text{W/m}^2$ (chuẩn IEC 61724-1) và $50\,\text{W/m}^2$ (ngưỡng nhạy cảm biến trong `01_bi_mart_params.yaml`)
- **Từ đâu có:** Tiêu chuẩn quốc tế **IEC 61724-1:2021** (Photovoltaic system performance — Part 1: Monitoring).
- **Ý nghĩa:** Khi $GHI < 100\,\text{W/m}^2$ (sáng sớm hoặc chiều muộn), tỷ lệ $E / GHI$ có mẫu số quá nhỏ gây ra các biến động ảo làm $PR$ vọt lên vô nghĩa ($> 100\%$). Chuẩn IEC yêu cầu chỉ tính PR tích lũy khi $GHI \ge 100\,\text{W/m}^2$.
- **Áp dụng cho:** Bộ lọc điều kiện trong công thức tính $PR$ tại Dashboard Tableau và Materialized View.

---

### 7. Góc Khúc xạ Khí quyển Chân trời ($\alpha_{\text{refraction}}$)
- **Tên biến trong mã nguồn:** `SUN_HORIZON_ANGLE`, `ALPHA_DAY_THRESHOLD`
- **Giá trị & Đơn vị:** $-0{,}833^\circ$ ($-50'$ góc)
- **Từ đâu có:** Thuật toán thiên văn học chuẩn của Cơ quan Khí quyển và Đại dương Quốc gia Hoa Kỳ (**NOAA Solar Position Algorithm**).
- **Ý nghĩa:** Gồm góc khúc xạ khí quyển tại đường chân trời ($34' \approx 0{,}566^\circ$) cộng với bán kính góc đĩa Mặt Trời ($16' \approx 0{,}267^\circ$). Khi góc nâng tâm mặt trời $\alpha > -0{,}833^\circ$, tia sáng đầu tiên bắt đầu chạm mặt đất.
- **Áp dụng cho:**
  - Tạo cờ thiên văn học nhị phân `is_day`: `is_day = 1` khi $\alpha > -0{,}833^\circ$, ngược lại bằng `0`.
  - Triệt tiêu 100% rò rỉ dữ liệu ban đêm.

---

### 8. Hằng số Mặt Trời Ngoài Khí quyển ($I_{\text{sc}}$)
- **Tên biến trong mã nguồn:** `SOLAR_CONSTANT`, `I_SC`
- **Giá trị & Đơn vị:** $1367\,\text{W/m}^2$ (hoặc $1361\,\text{W/m}^2$ theo WMO)
- **Từ đâu có:** Tổ chức Khí tượng Thế giới (**WMO Solar Constant Standard**).
- **Ý nghĩa:** Cường độ bức xạ mặt trời trên một đơn vị diện tích vuông góc với tia sáng tại khoảng cách trung bình Trái Đất - Mặt Trời ngoài khí quyển.
- **Áp dụng cho:** Thuật toán tính Bức xạ Trời Quang (Clear-Sky Ineichen Model) trong tầng Feature Engineering ML.

---

# PHẦN 2: HẰNG SỐ QUẢN TRỊ HIỆU SUẤT, TÀI CHÍNH & ESG (BI MART & BUSINESS)

---

### 9. Hệ số Hiệu suất Thiết kế Danh định ($PR_{\text{design\_benchmark}}$)
- **Tên biến trong mã nguồn:** `nominal_pr`, `pr_baseline_stc`
- **Giá trị & Đơn vị:** $0{,}85$ ($85\%$)
- **Từ đâu có:** Tiêu chuẩn thiết kế hệ thống điện mặt trời hòa lưới của **NREL** (National Renewable Energy Laboratory) và phần mềm **PVsyst**.
- **Ý nghĩa:** Đại diện cho hiệu suất tối đa kỳ vọng của một hệ thống PV mới, sạch sẽ ở điều kiện $25^\circ\text{C}$ sau khi đã trừ đi $15\%$ các tổn thất cố định không thể tránh khỏi (suy hao dây dẫn $2\%$, hiệu suất Inverter $97\%$, góc nghiêng phản xạ kính $3\%$, lệch chuỗi mismatch $2\%$).
- **Áp dụng cho:**
  - Tính chỉ số hiệu suất kỳ vọng: $PR_{\text{adjusted}} = 0{,}85 \times (1 - Loss_{\text{temp}})$.
  - Đóng vai trò là mốc chuẩn độc lập (Benchmark), chống lỗi logic vòng lặp Circular Logic.

---

### 10. Hệ số Quá tải Thiết kế DC/AC (Inverter Loading Ratio — $ILR$)
- **Tên biến trong mã nguồn:** `DC_AC_RATIO`, `inverter_loading_ratio`
- **Giá trị & Đơn vị:** $1{,}25$ ($125\%$)
- **Từ đâu có:** Tiêu chuẩn thiết kế kinh tế hệ thống PV thương mại (Commercial Rooftop PV Design Guidelines) tại Úc.
- **Ý nghĩa:** Công suất danh định tấm pin DC lắp đặt lớn hơn công suất chuyển đổi AC của Inverter $25\%$. Thiết kế này chấp nhận xén bỏ $2{,}3\%$ sản lượng đỉnh giữa trưa (Clipping) để giúp biến tần chạy đầy tải ở các khung giờ còn lại, nâng tổng sản lượng cả ngày cao hơn $8 - 12\%$.
- **Áp dụng cho:** Phân tích tổn thất $E_{\text{loss, clip}}$ và giải trình kỹ thuật với Hội đồng.

---

### 11. Biểu giá Mua Bán Điện Hòa Lưới (Feed-in Tariff — FiT)
- **Tên biến trong mã nguồn:** `fit_rate_vnd_per_kwh`, `fit_rate_aud`
- **Giá trị & Đơn vị:** $0{,}16\,\text{AUD/kWh}$ (tương đương $1.938\,\text{VNĐ/kWh}$ tại tỷ giá quy đổi tham chiếu $12.112\,\text{VNĐ/AUD}$)
- **Từ đâu có:** Biểu giá mua bán điện mặt trời quy chuẩn của Cơ quan Quản lý Thị trường Năng lượng Úc (**AEMO Victoria Wholesale & Retail Feed-in Tariff Framework**).
- **Ý nghĩa:** Mức đơn giá tài chính dùng để quy đổi mỗi kilowatt-giờ điện mặt trời tự dùng hoặc bán ra lưới thành giá trị kinh tế.
- **Áp dụng cho:**
  - Tính tổng giá trị tiết kiệm điện: $\text{Revenue} = \sum E_{\text{actual}} \times \text{FiT}$.
  - Tính tổn thất kinh tế do lỗi vận hành: $\text{Lost Revenue} = \sum E_{\text{loss}} \times \text{FiT}$.

---

### 12. Hệ số Phát thải Lưới điện Victoria ($EF_{\text{CO2}}$)
- **Tên biến trong mã nguồn:** `co2_emission_factor_kg_per_kwh`, `CO2_FACTOR_VIC`
- **Giá trị & Đơn vị:** $0{,}82\,\text{kg CO}_2 / \text{kWh}$ (chuẩn Victoria Úc) và $0{,}7222\,\text{kg CO}_2 / \text{kWh}$ (chuẩn lưới điện VN trong `01_bi_mart_params.yaml`)
- **Từ đâu có:** Báo cáo Hệ số Tài khoản Khí nhà kính Quốc gia Úc (**National Greenhouse Accounts Factors 2022**, Department of Climate Change, Energy, the Environment and Water - Scope 2 Emissions for Victoria State).
- **Ý nghĩa:** Khối lượng khí thải carbon dioxide tương đương được cắt giảm khi hệ thống điện mặt trời phát ra $1\,\text{kWh}$ điện sạch thay thế cho nhiệt điện than trên lưới điện bang Victoria.
- **Áp dụng cho:**
  - Tính chỉ số ESG trên Dashboard 1: $\text{CO}_2\text{ Avoided} = \sum E_{\text{actual}} \times 0{,}82\,\text{kg}$.

---

### 13. Khả năng Hấp thụ Carbon của Cây xanh ($C_{\text{tree}}$)
- **Tên biến trong mã nguồn:** `co2_per_tree_kg`
- **Giá trị & Đơn vị:** $21{,}77\,\text{kg CO}_2 / \text{cây/năm}$
- **Từ đâu có:** Cơ quan Bảo vệ Môi trường Hoa Kỳ (**US EPA Greenhouse Gas Equivalencies Calculator**).
- **Ý nghĩa:** Một cây xanh trưởng thành trong điều kiện bình thường hấp thụ trung bình khoảng $21{,}77\,\text{kg CO}_2$ mỗi năm.
- **Áp dụng cho:** Quy đổi khối lượng $\text{CO}_2$ cắt giảm sang số lượng cây xanh tương đương phục vụ báo cáo CSR/ESG.

---

# PHẦN 3: HẰNG SỐ ĐIỀN KHUYẾT NHÂN QUẢ & XỬ LÝ LƯỚI THỜI GIAN (ETL & IMPUTATION)

---

### 14. Bước Nhảy Lưới Thời gian Telemetry ($\Delta t_{\text{gen}}$)
- **Tên biến trong mã nguồn:** `TIME_STEP_HOURS`, `step_15m`
- **Giá trị & Đơn vị:** $15\,\text{phút} = 0{,}25\,\text{giờ}$
- **Từ đâu có:** Chu kỳ ghi dữ liệu định kỳ của hệ thống viễn thám IoT tại 42 trạm phát quang điện thuộc dự án UNISOLAR La Trobe University.
- **Ý nghĩa:** Bước thời gian rời rạc để tích phân công suất thành điện năng ($E = P \times 0{,}25$). Một ngày có chính xác $96$ mốc quan trắc ($24 \times 4$).
- **Áp dụng cho:**
  - Thiết lập bảng chiều `dim_time` với 96 bản ghi.
  - Chuyển đổi công suất sang điện năng và ngược lại.

---

### 15. Ngưỡng Bức xạ Cắt Đêm ($GHI_{\text{night\_cutoff}}$)
- **Tên biến trong mã nguồn:** `night_radiation_threshold`, `night_threshold_kwh`
- **Giá trị & Đơn vị:** $20{,}0\,\text{W/m}^2$ (bức xạ) và $0{,}05\,\text{kWh}$ (sản lượng phát)
- **Từ đâu có:** Ngưỡng điện áp đóng mở rơ-le khởi động biến tần (Inverter Wake-up Threshold).
- **Ý nghĩa:** Dưới mức bức xạ $20\,\text{W/m}^2$, toàn bộ năng lượng sinh ra là do nhiễu cảm biến biến dòng CT hoặc dòng rò rỉ.
- **Áp dụng cho:**
  - Thuật toán điền khuyết cấp 1: Nếu $GHI \le 20\,\text{W/m}^2$ hoặc `is_day == 0` thì cưỡng bức gán $E = 0{,}0\,\text{kWh}$.
  - Đã xử lý chính xác $1.383.493$ ô khuyết ban đêm ($90{,}05\%$).

---

### 16. Khung Giờ Ban Đêm Cố định ($T_{\text{night\_window}}$)
- **Tên biến trong mã nguồn:** `night_start_hour`, `night_end_hour`
- **Giá trị & Đơn vị:** Từ $18\text{h}30$ tối đến $05\text{h}30$ sáng hôm sau (`18.5` đến `5.5`)
- **Từ đâu có:** Phân tích góc phương vị mặt trời tại bang Victoria (vĩ độ $36^\circ\text{S} - 38^\circ\text{S}$) ở ngày ngắn nhất mùa đông.
- **Ý nghĩa:** Khoảng thời gian vật lý chắc chắn mặt trời đã lặn hoàn toàn dưới đường chân trời trên toàn bang.
- **Áp dụng cho:** Bộ lọc nhiễu ban đêm trong `03_hybrid_imputation.yaml` và kiểm toán dòng rò rỉ trên Heatmap Dashboard 3.

---

### 17. Ngưỡng Khoảng Trống Nội suy Tuyến tính ($Gap_{\text{linear}}$)
- **Tên biến trong mã nguồn:** `gap_linear_max_rows`
- **Giá trị & Đơn vị:** $2\,\text{bước}$ ($\le 30\,\text{phút}$)
- **Từ đâu có:** Nghiên cứu phân tích hàm tự tương quan (Autocorrelation Function — ACF) của chuỗi thời gian sản lượng mặt trời ở độ trễ bậc 1 ($r_1 > 0{,}98$).
- **Ý nghĩa:** Trong khoảng thời gian ngắn dưới 30 phút, biến thiên mây và bức xạ mang tính liên tục tuyến tính cao.
- **Áp dụng cho:** Thuật toán điền khuyết cấp 2 (Linear Interpolation), xử lý $53.684$ ô khuyết ($3{,}49\%$).

---

### 18. Ngưỡng Khoảng Trống Nội suy PCHIP Spline ($Gap_{\text{pchip}}$)
- **Tên biến trong mã nguồn:** `gap_cubic_max_rows`
- **Giá trị & Đơn vị:** Từ $3$ đến $8\,\text{bước}$ ($45\,\text{phút}$ đến $2\,\text{giờ}$)
- **Từ đâu có:** Thuật toán Hermite Cubic Spline bảo toàn tính đơn điệu (Piecewise Cubic Hermite Interpolating Polynomial — Fritsch & Carlson, 1980).
- **Ý nghĩa:** Khoảng thời gian từ 45p đến 2h vẫn giữ được hình thái parabol của quỹ đạo nhật động nhưng phi tuyến. PCHIP giúp khớp đường cong mượt mà mà không tạo ra dao động Runge hay điểm lượn sóng âm ($< 0\,\text{kWh}$).
- **Áp dụng cho:** Thuật toán điền khuyết cấp 3 (PCHIP Spline), xử lý $50.704$ ô khuyết ($3{,}30\%$).

---

### 19. Hệ số Dung sai Kẹp trần Công suất Vật lý ($Tol_{\text{over\_capacity}}$)
- **Tên biến trong mã nguồn:** `gmm_if_over_capacity_tolerance`, `tran_cong_suat_he_so`
- **Giá trị & Đơn vị:** $1{,}20$ ($120\%$) trong pipeline phát hiện dị thường và $1{,}02$ ($102\%$) trong huấn luyện ML
- **Từ đâu có:** Tiêu chuẩn đấu nối biến tần **AS/NZS 4777.2** kết hợp hiện tượng vật lý mép mây khuếch đại (*Cloud Edge Enhancement*) và quán tính nhiệt của cell pin lạnh.
- **Ý nghĩa:** Cho phép sản lượng 15 phút được phép vượt định mức tối đa $+20\%$ so với $P_{\text{stc}} \times 0{,}25\,\text{h}$ trong các trường hợp thời tiết đặc biệt trước khi bị coi là lỗi thiết bị.
- **Áp dụng cho:**
  - Hàm kẹp trần an toàn: $max\_physical\_kwh = P_{\text{stc}} \times 0{,}25 \times 1{,}20$.
  - Rào chắn vật lý `PHYSICAL_OVER_CAPACITY`.

---

# PHẦN 4: HẰNG SỐ PHÂN LỚP DỊ THƯỜNG LAI GMM-IF & 5 RÀO CHẮN VẬT LÝ

---

### 20. Độ sâu Cây Phân đoạn Không gian CART ($Tree_{\text{depth}}$)
- **Tên biến trong mã nguồn:** `gmm_if_tree_max_depth`, `gmm_if_tree_min_leaf`
- **Giá trị & Đơn vị:** `max_depth = 5`, `min_samples_leaf = 500`
- **Từ đâu có:** Tối ưu hóa phân đoạn cây quyết định (Decision Tree Regressor) trên không gian đặc trưng khí quyển ($GHI, DNI, DHI, T_{\text{ambient}}$).
- **Ý nghĩa:** Chia toàn bộ không gian thời tiết phức tạp thành các vùng lá cục bộ đồng nhất ($R^2 \approx 0{,}758$) để loại bỏ tính phi tuyến trước khi nạp vào GMM.
- **Áp dụng cho:** Tầng 1 của pipeline phát hiện dị thường lai GMM-IF.

---

### 21. Số Thành phần Gauss trong GMM ($K_{\text{gmm}}$)
- **Tên biến trong mã nguồn:** `gmm_if_components`, `n_components`
- **Giá trị & Đơn vị:** $2$ (thành phần phân bố Gauss)
- **Từ đâu có:** Mô hình Gaussian Mixture Model tối ưu theo chỉ số thông tin Bayesian (**BIC**).
- **Ý nghĩa:** Một thành phần đại diện cho cụm phát điện bình thường và một thành phần đại diện cho cụm có mây/suy giảm trong từng lá cây.
- **Áp dụng cho:** Tầng 2 GMM trong việc ước lượng hàm mật độ xác suất $p(x) = \sum_{k=1}^2 \pi_k \mathcal{N}(x | \mu_k, \Sigma_k)$.

---

### 22. Ngưỡng Xác suất Dị thường GMM ($p_{\text{threshold}}$)
- **Tên biến trong mã nguồn:** `gmm_if_prob_threshold`
- **Giá trị & Đơn vị:** $0{,}02$ ($2\%$)
- **Từ đâu có:** Ngưỡng phân vị xác suất đuôi phân bố chuẩn 2 phía ($Z \approx \pm 2{,}33\sigma$).
- **Ý nghĩa:** Bất kỳ quan sát nào có mật độ xác suất xuất hiện $p(x) < 0{,}02$ trong phân bố cục bộ sẽ bị đánh dấu cờ ứng viên dị thường.
- **Áp dụng cho:** Bộ sinh cờ dị thường GMM (`gmm_flag`).

---

### 23. Tỷ lệ Nhiễm bẩn Rừng Cô lập (Isolation Forest Contamination — $\nu$)
- **Tên biến trong mã nguồn:** `gmm_if_if_contamination`, `gmm_if_if_estimators`
- **Giá trị & Đơn vị:** `contamination = 0.03` ($3\%$), `n_estimators = 100` cây
- **Từ đâu có:** Nghiên cứu của Liu, Ting & Zhou (2008) về thuật toán Isolation Forest trên chuỗi cảm biến công nghiệp.
- **Ý nghĩa:** Thiết lập tỷ lệ dự kiến các điểm bất thường nằm ở phân vị sâu nhất của không gian đặc trưng toàn cục.
- **Áp dụng cho:** Bộ sinh cờ dị thường Isolation Forest (`if_flag`).

---

### 24. Ngưỡng Cảnh báo Nắng gắt Mất phát (`PHYSICAL_LOW_ENERGY_STRONG_SUN`)
- **Tên biến trong mã nguồn:** `GHI_STRONG_SUN`, `SUNSHINE_STRONG_SUN`, `LOW_ENERGY_RATIO_P95`
- **Giá trị & Đơn vị:** $GHI \ge 700\,\text{W/m}^2$, $Sunshine \ge 3000\,\text{giây}$, $E \le 0{,}05 \times P_{95}$
- **Từ đâu có:** Đặc tính vận hành công suất của hệ thống quang điện khi trời nắng gắt không mây.
- **Ý nghĩa:** Khi bức xạ mặt trời cực mạnh ($> 700\,\text{W/m}^2$) nhưng sản lượng phát lại tụt về mức dưới $5\%$ công suất đỉnh của trạm, đây là tín hiệu cảnh báo Inverter bị ngắt quá nhiệt, quá áp lưới hoặc đứt cầu chì chuỗi.
- **Áp dụng cho:** Rào chắn vật lý số 4 trong pipeline giải thích nguyên nhân ngoại lai (`gmm_if_outlier_reason`).

---

### 25. Ngưỡng Bước nhảy Phân bố Đột ngột (`PHYSICAL_DISTRIBUTION_JUMP`)
- **Tên biến trong mã nguồn:** `IQR_OUTLIER_FACTOR`, `NEIGHBOR_DELTA_RATIO`
- **Giá trị & Đơn vị:** $4 \times \text{IQR}$ và $|\Delta_{\text{neighbor}}| \ge \max(0{,}15 \times P_{95}, 1{,}0\,\text{kWh})$
- **Từ đâu có:** Thống kê mô tả kháng nhiễu (Robust Statistics — John Tukey) kết hợp kiểm tra độ biến thiên lân cận 2 giờ.
- **Ý nghĩa:** Phát hiện các điểm dữ liệu bị vọt đỉnh (Spike) hoặc rơi tự do (Dropout) đột ngột vượt ra ngoài 4 lần khoảng tứ phân vị và khác biệt lớn so với các khung giờ xung quanh.
- **Áp dụng cho:** Rào chắn vật lý số 5 để bắt lỗi đường truyền viễn thông SCADA Modbus.

---

# PHẦN 5: HẰNG SỐ BIẾN ĐỔI ĐẶC TRƯNG & HUẤN LUYỆN MÔ HÌNH HỌC MÁY (ML PIPELINE)

---

### 26. Tầm Dự báo Đa bước (Forecasting Horizons — $h$)
- **Tên biến trong mã nguồn:** `horizon_steps`
- **Giá trị & Đơn vị:** $h \in [1, 4]$ tương ứng với $h_1 = 15\,\text{phút}$ ($T+1$) và $h_4 = 60\,\text{phút} = 1\,\text{giờ}$ ($T+4$)
- **Từ đâu có:** Quy định về thị trường điều độ hòa lưới điện thời gian thực của Úc (**AEMO 5-minute & 30-minute Settlement Rules**).
- **Ý nghĩa:** Dự báo sản lượng điện ngắn hạn phục vụ điều độ phụ tải và vận hành hệ thống lưu trữ pin BESS.
- **Áp dụng cho:** Kiến trúc mô hình đa đầu ra của LightGBM Regressor.

---

### 27. Hệ số Mất mát Kháng Nhiễu Huber Loss ($\delta$)
- **Tên biến trong mã nguồn:** `alpha`, `huber_delta`
- **Giá trị & Đơn vị:** $\delta = 1{,}0$ (trong `train.yaml`)
- **Từ đâu có:** Hàm mất mát thống kê vững Peter Huber (1964).
- **Ý nghĩa:** Chuyển đổi mượt mà giữa hàm bình phương sai số MSE khi sai số nhỏ ($|y - \hat{y}| \le \delta$) sang hàm trị tuyệt đối sai số MAE khi sai số lớn ($|y - \hat{y}| > \delta$), giúp mô hình không bị lệch bởi các ngoại lai đột biến.
- **Áp dụng cho:** Hàm mục tiêu tối ưu (`objective: huber`) của mô hình vô địch LightGBM.

---

### 28. Bộ Siêu Tham số Huấn luyện Chuẩn của LightGBM
- **Tên biến trong mã nguồn:** `default_params`, `best_params.json`
- **Giá trị & Đơn vị:**
  - `n_estimators = 800` (Số cây quyết định)
  - `learning_rate = 0.05` (Tốc độ học)
  - `num_leaves = 160` (Số lá cực đại mỗi cây)
  - `min_child_samples = 30` (Số mẫu tối thiểu ở lá)
  - `subsample = 0.9` (Tỷ lệ chọn mẫu hàng dòng $90\%$)
  - `colsample_bytree = 0.9` (Tỷ lệ chọn mẫu cột đặc trưng $90\%$)
  - `n_folds = 5` (5-Fold Time-Series Cross Validation)
- **Từ đâu có:** Kết quả tối ưu hóa siêu tham số tự động bằng thuật toán Bayesian TPE qua thư viện **Optuna**.
- **Ý nghĩa:** Cân bằng hoàn hảo giữa khả năng học quan hệ phi tuyến và ngăn chặn hiện tượng quá khớp (Overfitting).
- **Áp dụng cho:** Huấn luyện mô hình dự báo LightGBM trên toàn bộ 42 trạm phát.

---

### 29. Giới hạn Kẹp Chuẩn hóa Mục tiêu ($k_{\text{target}}$)
- **Tên biến trong mã nguồn:** `k_target_min`, `k_target_max`, `clip_phan_vi`
- **Giá trị & Đơn vị:** $k_{\text{min}} = 0{,}0$, $k_{\text{max}} = 1{,}5$, `clip_phan_vi = 0.99` ($99\%$)
- **Từ đâu có:** Phương pháp chuẩn hóa vật lý tỷ lệ công suất không thứ nguyên: $k = \frac{E(t)}{P_{\text{stc}} \cdot \sin(\alpha(t))}$.
- **Ý nghĩa:** Chuyển đổi biến mục tiêu kWh về hệ số tỷ lệ bức xạ $k \in [0{,}0; 1{,}5]$ để triệt tiêu biến thiên nhật động hình sin tự nhiên, giúp mô hình học tập trung vào ảnh hưởng của mây và nhiệt độ.
- **Áp dụng cho:** Target Transformation & Inverse Transformation trong quy trình suy luận (Inference).

---

### 30. Ngưỡng Đa cộng tuyến Hệ số Phóng đại Phương sai ($\text{VIF}_{\text{threshold}}$)
- **Tên biến trong mã nguồn:** `VIF_MAX_THRESHOLD`
- **Giá trị & Đơn vị:** $\text{VIF} < 10{,}0$ (ngưỡng chấp nhận) và $\text{VIF} < 5{,}0$ (ngưỡng tối ưu)
- **Từ đâu có:** Lý thuyết thống kê đa biến về hiện tượng cộng tuyến (Variance Inflation Factor — Marquardt, 1970).
- **Ý nghĩa:** Đánh giá mức độ phụ thuộc tuyến tính giữa các biến đặc trưng đầu vào. Nếu $\text{VIF} \ge 10$, đặc trưng bị loại bỏ để tránh làm mất ổn định trọng số mô hình.
- **Áp dụng cho:** Sàng lọc 40 biến đặc trưng trong Feature Store trước khi đưa vào huấn luyện mô hình.

---

# PHẦN 6: BẢNG TRA CỨU NHANH MATRIX TOÀN BỘ HẰNG SỐ (MASTER CONSTANTS CHEATSHEET)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    BẢNG TRA CỨU NHANH TOÀN BỘ HẰNG SỐ VÀ TỶ LỆ DỰ ÁN                                   │
├────┬─────────────────────────────┬───────────────────┬──────────────────────────────┬──────────────────────────────────┤
│ STT│ Tên Hằng số / Tham số       │ Giá trị & Đơn vị  │ Nguồn gốc & Tiêu chuẩn       │ Áp dụng trong Thuật toán / Báo cáo│
├────┼─────────────────────────────┼───────────────────┼──────────────────────────────┼──────────────────────────────────┤
│ 1  │ Bức xạ tiêu chuẩn STC       │ 1000 W/m²         │ IEC 60904-3                  │ Tính E_theo, PR actual, Ref Yield│
│ 2  │ Nhiệt độ Cell tiêu chuẩn STC│ 25°C              │ IEC 60904-3                  │ Mốc tính delta T, PR correct     │
│ 3  │ Khối lượng khí quyển STC    │ AM 1.5            │ ASTM G173-03 / IEC 60904-3   │ Chuẩn hóa phổ quang học          │
│ 4  │ Hệ số suy giảm nhiệt công suất│ -0.38%/°C (0.0038)│ Datasheet SunPower/Trina Solar│ Tính Loss_temp, PR adjusted/corr │
│ 5  │ Hệ số truyền nhiệt bức xạ   │ 0.03 °C/(W/m²)    │ Ross Model (1976) / Sandia   │ Ước tính T_cell từ GHI & T_amb   │
│ 6  │ Ngưỡng lọc bức xạ ngày IEC  │ 100 W/m² (50 W/m²)│ IEC 61724-1:2021             │ Lọc điều kiện tính PR tích lũy   │
│ 7  │ Góc khúc xạ khí quyển chân trời│ -0.833° (-50')  │ NOAA Solar Position Algorithm│ Xác định cờ is_day nhị phân      │
│ 8  │ Hằng số mặt trời            │ 1367 W/m²         │ WMO Solar Constant           │ Mô hình bức xạ trời quang Ineichen│
│ 9  │ PR thiết kế danh định       │ 0.85 (85%)        │ NREL / PVsyst Standard       │ Tính đường chuẩn PR adjusted     │
│ 10 │ Tỷ lệ quá tải Inverter ILR  │ 1.25 (125%)       │ Commercial PV Design Guide   │ Giải trình Clipping Loss (2.3%)  │
│ 11 │ Biểu giá điện mua bán FiT   │ 0.16 AUD/kWh      │ AEMO Victoria Wholesale/Retail│ Quy đổi doanh thu & Lost Revenue │
│ 12 │ Hệ số phát thải CO2 lưới Vic │ 0.82 kg CO2/kWh   │ National Greenhouse Accounts │ Tính chỉ số CO2 Avoided (ESG)    │
│ 13 │ Hấp thụ CO2 cây xanh        │ 21.77 kg/cây/năm  │ US EPA GHG Equivalencies     │ Quy đổi số lượng cây xanh tương đương│
│ 14 │ Chu kỳ đo Telemetry         │ 15 phút (0.25h)   │ Hệ thống IoT UNISOLAR        │ Lưới thời gian dim_time (96 mốc) │
│ 15 │ Ngưỡng bức xạ ban đêm       │ 20.0 W/m² (0.05kWh│ Inverter Wake-up Threshold   │ Điền khuyết Cấp 1 (Gán 0.0 kWh)  │
│ 16 │ Khung giờ ban đêm cố định   │ 18h30 đến 05h30   │ Tọa độ bang Victoria Úc      │ Lọc nhiễu & Bắt lỗi rò rỉ đêm    │
│ 17 │ Khoảng khuyết Linear        │ <= 2 bước (<= 30p)│ ACF Autocorrelation Analysis │ Điền khuyết Cấp 2 (Tuyến tính)   │
│ 18 │ Khoảng khuyết PCHIP         │ 3 - 8 bước (45p-2h│ Fritsch & Carlson (1980)     │ Điền khuyết Cấp 3 (PCHIP Spline) │
│ 19 │ Dung sai kẹp trần công suất │ 1.20x (120% Pstc) │ AS/NZS 4777.2 / Cloud Edge   │ Hàm kẹp trần max_physical_kwh    │
│ 20 │ Cây phân đoạn CART          │ Depth=5, Leaf=500 │ Decision Tree Regressor      │ Tầng 1 Phân đoạn cục bộ GMM-IF   │
│ 21 │ Số thành phần GMM           │ 2 Gaussians       │ Bayesian Information Criterion│ Tầng 2 GMM ước lượng mật độ p(x) │
│ 22 │ Ngưỡng xác suất dị thường GMM│ p < 0.02 (2%)    │ Z-score phân vị đuôi 2 phía  │ Gán cờ gmm_flag                  │
│ 23 │ Tỷ lệ nhiễm bẩn IsoForest   │ Contamination=0.03│ Liu & Zhou (2008) IsoForest  │ Gán cờ if_flag (100 cây)         │
│ 24 │ Ngưỡng nắng gắt mất phát    │ GHI>=700, E<=5%P95│ PV Operation Domain Rules    │ Cờ PHYSICAL_LOW_ENERGY_STRONG_SUN│
│ 25 │ Ngưỡng bước nhảy phân bố    │ 4 * IQR, d>=15%P95│ Tukey Robust Statistics      │ Cờ PHYSICAL_DISTRIBUTION_JUMP    │
│ 26 │ Tầm dự báo Horizons         │ h1=15p, h4=60p    │ AEMO 5m/30m Settlement Rules │ Mô hình LightGBM đa bước         │
│ 27 │ Tham số mất mát Huber Loss  │ delta = 1.0       │ Peter Huber (1964) Robust Loss│ Objective function của LightGBM  │
│ 28 │ Siêu tham số chuẩn LightGBM │ 800 trees, lr=0.05│ Optuna Bayesian TPE Tuning   │ Cấu hình huấn luyện mô hình      │
│ 29 │ Kẹp chuẩn hóa mục tiêu k    │ k in [0.0; 1.5]   │ Physical Scaling (sin Alpha) │ Chuẩn hóa triệt tiêu nhật động   │
│ 30 │ Ngưỡng kiểm định đa cộng tuyến│ VIF < 10.0      │ Marquardt (1970) VIF Test    │ Sàng lọc 40 biến Feature Store   │
└────┴─────────────────────────────┴───────────────────┴──────────────────────────────┴──────────────────────────────────┘
```
