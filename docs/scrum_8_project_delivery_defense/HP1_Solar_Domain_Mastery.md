# HỌC PHẦN 1: SOLAR DOMAIN MASTERY FOR DATA ANALYSTS

> **Thời lượng:** 5 Units chuyên sâu  
> **Mục tiêu:** Trang bị cho Data Analyst nền tảng vững chắc về bản chất vật lý, cơ chế quang học khí quyển, hệ thống phân rã suy hao và chuẩn mực đo lường hiệu năng ngành Điện Mặt trời (Solar PV), kết hợp hệ thống trích dẫn học thuật (In-text Academic Citations) theo chuẩn quốc tế.

---

## MỤC LỤC TỔNG QUAN

* [UNIT 1: Cấu trúc Phần cứng và Chuỗi Biến đổi Năng lượng Quang điện (PV Anatomy)](#unit-1-cấu-trúc-phần-cứng-và-chuỗi-biến-đổi-năng-lượng-quang-điện-pv-anatomy)
  * [PHẦN 0: Khái niệm Điện năng Cơ bản dành cho Data Analyst (Electricity 101)](#phần-0-khái-niệm-điện-năng-cơ-bản-dành-cho-data-analyst-electricity-101)
  * [1.1. Bản chất Vật lý Bán dẫn & Hiệu ứng Quang điện](#11-bản-chất-vật-lý-bán-dẫn--hiệu-ứng-quang-điện)
  * [1.2. Phân loại Vật liệu Tế bào Quang điện (Solar Cells)](#12-phân-loại-vật-liệu-tế-bào-quang-điện-solar-cells)
  * [1.3. Cấu trúc Hình học và Tô-pô Hệ thống Trạm (PV Topology)](#13-cấu-trúc-hình-học-và-tô-pô-hệ-thống-trạm-pv-topology)
  * [1.4. Phân loại Biến tần (Inverters) & Bộ tối ưu MPPT](#14-phân-loại-biến-tần-inverters--bộ-tối-ưu-mppt)
  * [1.5. Điều kiện Thử nghiệm Tiêu chuẩn (STC vs NOCT vs NMOT)](#15-điều-kiện-thử-nghiệm-tiêu-chuẩn-stc-vs-noct-vs-nmot)
  * [1.6. Bối cảnh Dữ liệu Thực nghiệm Chi tiết (Dự án UNISOLAR - Đại học La Trobe)](#16-bối-cảnh-dữ-liệu-thực-nghiệm-chi-tiết-dự-án-unisolar---đại-học-la-trobe)
* [UNIT 2: Khí tượng Viễn thám và Động học Nhật quỹ (Solar Meteorology & Geometry)](#unit-2-khí-tượng-viễn-thám-và-động-học-nhật-quỹ-solar-meteorology--geometry)
  * [2.1. Động học Vị trí Mặt Trời (Thuật toán NREL/NOAA SPA)](#21-động-học-vị-trí-mặt-trời-thuật-toán-nrelnoaa-spa)
  * [2.2. Mã hóa Chu kỳ Lượng giác trong Machine Learning](#22-mã-hóa-chu-kỳ-lượng-giác-trong-machine-learning)
  * [2.3. Các Thành phần Bức xạ Mặt Trời chuẩn WMO](#23-các-thành-phần-bức-xạ-mặt-trời-chuẩn-wmo)
  * [2.4. Mô hình Bức xạ Trời quang (Clear-Sky Models & CSI)](#24-mô-hình-bức-xạ-trời-quang-clear-sky-models--csi)
  * [2.5. Các Biến Khí quyển Tác động từ ERA5-Land Reanalysis](#25-các-biến-khí-quyển-tác-động-từ-era5-land-reanalysis)
* [UNIT 3: Bộ Chỉ số Đo lường Hiệu năng Cốt lõi (Solar Analytics KPI Framework)](#unit-3-bộ-chỉ-số-đo-lường-hiệu-năng-cốt-lõi-solar-analytics-kpi-framework)
  * [3.1. Hệ số Hiệu suất (Performance Ratio - PR) chuẩn IEC 61724-1](#31-hệ-số-hiệu-suất-performance-ratio---pr-chuẩn-iec-61724-1)
  * [3.2. Hệ số Hiệu suất Hiệu chỉnh Nhiệt độ (Temperature-Corrected PR)](#32-hệ-số-hiệu-suất-hiệu-chỉnh-nhiệt-độ-temperature-corrected-pr)
  * [3.3. Năng suất Riêng (Specific Yield) & Hệ số Công suất (Capacity Factor)](#33-năng-suất-riêng-specific-yield--hệ-số-công-suất-capacity-factor)
  * [3.4. Chỉ số Kinh tế & Tác động Giảm phát thải Khí nhà kính](#34-chỉ-số-kinh-tế--tác-động-giảm-phát-thải-khí-nhà-kính)
* [UNIT 4: Cơ chế Suy hao & Phân rã Tổn thất (Loss Decomposition Analysis)](#unit-4-cơ-chế-suy-hao--phân-rã-tổn-thất-loss-decomposition-analysis)
  * [4.1. Suy hao do Quá nhiệt Tế bào Quang điện (Thermal Derating)](#41-suy-hao-do-quá-nhiệt-tế-bào-quang-điện-thermal-derating)
  * [4.2. Suy hao Xén Công suất Biến tần (Inverter Clipping Loss)](#42-suy-hao-xén-công-suất-biến-tần-inverter-clipping-loss)
  * [4.3. Suy hao do Bám bụi & Che bóng Cục bộ (Soiling & Shading)](#43-suy-hao-do-bám-bụi--che-bóng-cục-bộ-soiling--shading)
* [UNIT 5: Nhận diện Dị thường Vận hành & Bảo trì Dựa trên Điều kiện (CBM)](#unit-5-nhận-diện-dị-thường-vận-hành--bảo-trì-dựa-trên-điều-kiện-cbm)
  * [5.1. Báo cáo Độ tin cậy IEA-PVPS Task 13](#51-báo-cáo-độ-tin-cậy-iea-pvps-task-13)
  * [5.2. Chẩn đoán Chi tiết 6 Nhóm Dị thường Kỹ thuật Vật lý Đặc trưng](#52-chẩn-đoán-chi-tiết-6-nhóm-dị-thường-kỹ-thuật-vật-lý-đặc-trưng)
  * [5.3. Quy trình Tự động Hóa O&M và Tạo Lệnh Công tác (Work Order)](#53-quy-trình-tự-động-hóa-om-và-tạo-lệnh-công-tác-work-order)
* [TÀI LIỆU THAM KHẢO HỌC THUẬT & TIÊU CHUẨN QUỐC TẾ](#tài-liệu-tham-khảo-học-thuật--tiêu-chuẩn-quốc-tế)

---

## UNIT 1: Cấu trúc Phần cứng và Chuỗi Biến đổi Năng lượng Quang điện (PV Anatomy)

> **Mục tiêu Unit:** Giúp bất kỳ ai — dù chưa từng học về điện hay vật lý — đều có thể hình dung rõ nét từ hành trình một tia nắng chiếu vào tấm pin biến thành dòng điện, đến cách dữ liệu đo đếm 15 phút được hình thành tại 42 trạm của Đại học La Trobe.

---

### PHẦN 0: KHÁI NIỆM ĐIỆN NĂNG CƠ BẢN DÀNH CHO DATA ANALYST (ELECTRICITY 101)

Bản chất và mối quan hệ giữa 4 đại lượng điện năng cơ bản trong hệ thống điện mặt trời:

![Diagram 0.1: Bản chất và Mối quan hệ giữa 4 Đại lượng Điện năng Cốt lõi](diagrams/diagram_0_1_water_electricity_metaphor.svg)

#### Bảng Định nghĩa và Đối chiếu 4 Đại lượng Điện cơ bản:

| Thuật ngữ Điện | Ký hiệu & Đơn vị | Bản chất Vật lý | Biểu thức Tính toán | Ý nghĩa trong Dự án Solar & Database |
| :--- | :---: | :--- | :---: | :--- |
| **Điện áp (Voltage)** | **$V$** (Volt) | Hiệu điện thế, lực điện trường thúc đẩy các hạt electron di chuyển giữa hai cực. | $V = \frac{P}{I}$ | Ghép nối tiếp $15 - 20$ tấm pin trong một chuỗi (String) để nâng điện áp lên $600 - 800\,\text{V DC}$ nạp vào Inverter. |
| **Dòng điện (Current)** | **$I$** (Ampere - $\text{A}$) | Cường độ dòng điện, lượng điện tích dịch chuyển có hướng qua tiết diện dây trong 1 giây. | $I = \frac{P}{V}$ | Cường độ bức xạ mặt trời ($GHI$) chiếu vào tấm pin càng cao thì dòng điện sinh ra càng lớn ($8 - 13\,\text{A DC}$). |
| **Công suất tức thời (Power)** | **$P$** (Watt / $\text{kW}$) | Tốc độ sản sinh hoặc tiêu thụ năng lượng tại một thời điểm tức thời xác định. | $P = V \times I$ | Tại thời điểm giữa trưa nắng đỉnh, hệ thống đạt công suất phát cực đại ($P_{\text{mp}}$), biến thiên từ $10\,\text{kW}$ đến $320\,\text{kW}$. |
| **Sản lượng tích lũy (Energy)** | **$E$** ($\text{kWh}$) | Tổng điện năng được sản sinh và tích lũy trong một khoảng thời gian $\Delta t$. | $E = \int P(t) \, dt$ | **Chính là cột `energy_kwh` trong Database.** Đồng hồ đo đếm chốt dữ liệu mỗi 15 phút ($0{,}25\,\text{h}$) để lưu vào bảng sự kiện. |
| **Điện một chiều (DC) vs Xoay chiều (AC)** | **DC / AC** | **DC:** Dòng điện chuyển động theo một chiều không đổi.<br>**AC:** Dòng điện đổi chiều tuần hoàn theo sóng sin ($50\,\text{Hz}$). | $f = 50\,\text{Hz}$ ($230\,\text{V}$) | Tấm pin mặt trời sinh ra điện **DC**, qua thiết bị **Inverter** chuyển hóa thành điện xoay chiều **AC** cấp cho phụ tải và hòa lưới. |

---

#### Chuỗi Biến đổi Năng lượng 4 Bước: Từ Bức xạ Mặt Trời đến Database

![Diagram 0.2: Hành trình 4 bước từ Tia nắng đến Dữ liệu Database](diagrams/diagram_0_2_photon_to_database_journey.svg)

1.  **Bước 1 (Mảng pin mặt trời):** Tế bào quang điện hấp thụ bức xạ mặt trời, tạo ra dòng điện một chiều (DC).
2.  **Bước 2 (Tủ biến tần Inverter):** Inverter thực hiện nghịch lưu điện DC thành điện xoay chiều AC ($230\text{V}, 50\text{Hz}$) với hiệu suất $>98\%$.
3.  **Bước 3 (Đồng hồ thông minh Smart Meter):** Thiết bị đo đếm ghi nhận sản lượng điện năng tích lũy ($kWh$) định kỳ mỗi 15 phút.
4.  **Bước 4 (Cơ sở dữ liệu Data Lakehouse):** Hệ thống telemetry lưu trữ bản ghi `[time_id, site_id, energy_kwh, weather]` tạo nên tập dữ liệu $2.731.946$ dòng.

---

### 1.1. Bản chất Vật lý Bán dẫn & Hiệu ứng Quang điện

#### Cơ chế Phát sinh Dòng điện Quang sinh
*   Tế bào quang điện (Solar Cell) được cấu tạo từ vật liệu bán dẫn Silicon với hai lớp tiếp giáp loại N (dư thừa electron tự do mang điện tích âm $e^-$) và loại P (dư thừa lỗ trống mang điện tích dương $h^+$).
*   Tại ranh giới tiếp xúc hình thành **Lớp tiếp giáp $p-n$** và thiết lập **Điện trường nội tại ($E_{\text{bi}}$)** hướng từ vùng N sang vùng P.
*   Khi hạt ánh sáng (**Photon**) có năng lượng $E_{\text{photon}} = h\nu \ge 1{,}12\,\text{eV}$ (độ rộng vùng cấm Silicon) chiếu vào vùng tiếp giáp, nó kích thích electron nhảy từ dải hóa trị lên dải dẫn, tạo thành các cặp electron - lỗ trống tự do.
*   Dưới tác động của điện trường nội tại $E_{\text{bi}}$, các electron bị quét về cực âm (vùng N) và lỗ trống bị quét về cực dương (vùng P), tạo nên sức điện động một chiều (DC) dẫn ra mạch ngoài.

---

#### Bản chất Kỹ thuật & Cơ sở Vật lý Bán dẫn [1, 2]
*   **Cấu trúc Tiếp giáp $p-n$ (p-n Junction):**
    *   Silicon tinh thể nhóm IV có 4 electron hóa trị.
    *   **Lớp bán dẫn loại N (N-Type):** Được pha tạp (*doping*) nguyên tố nhóm V (như Phosphorus - $P$), tạo ra các electron tự do mang điện tích âm ($e^-$).
    *   **Lớp bán dẫn loại P (P-Type):** Được pha tạp nguyên tố nhóm III (như Boron - $B$), thiếu hụt electron và tạo ra các lỗ trống mang điện tích dương ($h^+$).
    *   **Vùng nghèo (Depletion Region):** Tại ranh giới tiếp xúc giữa hai lớp, electron khuếch tán sang vùng P và lỗ trống khuếch tán sang vùng N, hình thành các ion cố định và thiết lập **Điện trường nội tại ($E_{\text{bi}}$)** hướng từ vùng N sang vùng P [1].
*   **Hiệu ứng Quang điện (Photovoltaic Effect) & Giới hạn Shockley-Queisser [1]:**
    *   Khi hạt ánh sáng có năng lượng $E_{\text{photon}} = h\nu \ge E_g \approx 1{,}12\,\text{eV}$ (độ rộng vùng cấm Silicon) chiếu vào vùng nghèo, nó kích thích electron nhảy từ dải hóa trị lên dải dẫn, tạo thành cặp hạt mang điện quang sinh (*electron-hole pair*).
    *   Dưới tác dụng của điện trường $E_{\text{bi}}$, electron bị quét về cực âm (vùng N) và lỗ trống bị quét về cực dương (vùng P), tạo nên sức điện động một chiều ($DC$) [1, 2].
    *   *Giới hạn Shockley-Queisser:* Hiệu suất chuyển đổi quang-điện nhiệt động lực học lý thuyết tối đa của pin silicon đơn tiếp giáp đạt xấp xỉ **$33{,}7\%$** (do photon năng lượng thấp bị xuyên qua và photon năng lượng cao bị tiêu tán thành nhiệt năng) [1].

![Diagram 1.1: Bản chất Vật lý Vi mô của Hiệu ứng Quang điện tại Lớp Tiếp giáp p-n](diagrams/diagram_1_1_pn_junction_pv_effect.svg)

*   **Mô hình Toán học Diode Đơn (Single-Diode Model) [1, 6]:**
    Dòng điện ngõ ra $I$ của tế bào quang điện tuân theo phương trình Shockley:
    $$I = I_{\text{ph}} - I_0 \left[ \exp\left(\frac{q(V + I R_s)}{n k T_{\text{cell}}}\right) - 1 \right] - \frac{V + I R_s}{R_{\text{sh}}}$$
    *Trong đó [1, 6]:*
    *   $I_{\text{ph}}$: Dòng quang sinh, tỷ lệ thuận tuyến tính với cường độ bức xạ $GHI$.
    *   $I_0$: Dòng bão hòa ngược của diode, tăng theo hàm mũ khi nhiệt độ tế bào $T_{\text{cell}}$ tăng cao.
    *   $R_s, R_{\text{sh}}$: Điện trở nối tiếp (mong muốn $\approx 0\,\Omega$) và điện trở song song rò rỉ (mong muốn $\approx \infty$).

*   **Đặc tuyến $I-V$ và $P-V$ Đặc trưng [1]:**
    *   $I_{\text{sc}}$ (Short-Circuit Current): Dòng điện ngắn mạch tại $V=0$, tỷ lệ thuận trực tiếp với bức xạ $GHI$.
    *   $V_{\text{oc}}$ (Open-Circuit Voltage): Điện áp hở mạch tại $I=0$, tỷ lệ nghịch mạnh mẽ với nhiệt độ $T_{\text{cell}}$.
    *   $P_{\text{mp}} = V_{\text{mp}} \times I_{\text{mp}}$: Điểm công suất cực đại (Maximum Power Point - MPP).
    *   $FF$ (Fill Factor - Hệ số điền đầy): $FF = \frac{V_{\text{mp}} \cdot I_{\text{mp}}}{V_{\text{oc}} \cdot I_{\text{sc}}}$, đánh giá độ vuông vắn của đặc tuyến ($0{,}75 - 0{,}85$).

![Diagram 1.2: Đồ thị Đặc tuyến I-V và P-V theo Bức xạ và Nhiệt độ](diagrams/diagram_1_2_iv_pv_curves.svg)

---

#### Ý nghĩa Thực tế cho Data Analyst (DA Insight)
1.  **Quan hệ Tuyến tính giữa Bức xạ và Sản lượng:** Cường độ bức xạ ($GHI$) tác động trực tiếp lên dòng điện quang sinh $I_{\text{sc}}$. Khi $GHI$ tăng gấp đôi, sản lượng `energy_kwh` phát ra tăng gần gấp đôi.
2.  **Tác động Suy giảm Hiệu suất do Nhiệt độ (Thermal Derating):** 
    *   Khi bề mặt tấm pin bị phơi nắng liên tục, nhiệt độ cell $T_{\text{cell}}$ có thể tăng lên đến $65^\circ\text{C}$. Nhiệt độ tăng cao làm tăng dòng bão hòa ngược $I_0$, dẫn đến sụt giảm nghiêm trọng điện áp hở mạch $V_{\text{oc}}$.
    *   Kết quả là công suất phát cực đại $P_{\text{mp}}$ bị suy giảm từ $12\% - 16\%$ vào các ngày hè nắng nóng đỉnh điểm. Đây là quy luật vật lý tự nhiên của chất bán dẫn, không phải lỗi kỹ thuật của trạm.

---

### 1.2. Phân loại Vật liệu Tế bào Quang điện (Solar Cells)

#### Đặc tính Cấu trúc Vật liệu
*   **Đơn tinh thể (Monocrystalline - Mono-Si):** Sản xuất từ các thỏi silicon đơn tinh thể nguyên khối đồng nhất theo phương pháp Czochralski. Cấu trúc mạng tinh thể không có khuyết tật ranh giới hạt, giúp electron di chuyển với độ linh động cao, đạt hiệu suất chuyển đổi cao nhất ($20{,}0\% - 22{,}5\%$).
*   **Đa tinh thể (Polycrystalline - Poly-Si):** Sản xuất bằng cách nung chảy nhiều mảnh silicon trong khuôn đúc. Tồn tại nhiều ranh giới hạt tinh thể làm cản trở chuyển động của electron và tăng tốc độ tái hợp hạt mang điện, dẫn đến hiệu suất thấp hơn ($15{,}0\% - 18{,}0\%$).
*   **Tiếp giáp Thụ động N-Type (TOPCon / HJT):** Công nghệ silicon thế hệ mới phủ các lớp oxit siêu mỏng để thụ động hóa bề mặt tiếp xúc, giảm suy hao tái hợp và nâng hiệu suất lên $22{,}5\% - 24{,}5\%$.
*   **Màng mỏng (Thin-Film - CdTe / CIGS):** Lớp bán dẫn mỏng vài micromet phủ trên kính, hiệu suất thấp hơn ($11\% - 13{,}5\%$) nhưng có hệ số nhiệt độ suy hao thấp ($\gamma \approx -0{,}20\%/^\circ\text{C}$).

---

#### Bảng So sánh Kỹ thuật 4 Công nghệ Solar Cells [1, 2]

| Tiêu chí So sánh | Monocrystalline (Mono-Si) [1] | N-Type TOPCon / HJT [1, 2] | Polycrystalline (Poly-Si) [1] | Thin-Film (CdTe / CIGS) [2] |
| :--- | :--- | :--- | :--- | :--- |
| **Cấu trúc tinh thể** | Đơn tinh thể nguyên khối (Czochralski) | Đơn tinh thể tiếp giáp thụ động đa lớp | Đa tinh thể đúc nóng chảy | Màng mỏng vô định hình |
| **Hiệu suất Module ($STC$)** | **$20{,}0\% - 22{,}5\%$** | **$22{,}5\% - 24{,}5\%$** | $15{,}0\% - 18{,}0\%$ | $11{,}0\% - 13{,}5\%$ |
| **Hệ số Suy hao Nhiệt ($\gamma$)** | **$-0{,}35\%/^\circ\text{C}$** | **$-0{,}29\%/^\circ\text{C}$** | $-0{,}42\%/^\circ\text{C}$ đến $-0{,}45\%/^\circ\text{C}$ | **$-0{,}20\%/^\circ\text{C}$** |
| **Tốc độ Thoái hóa năm** | $< 0{,}55\%$/năm | $< 0{,}40\%$/năm | $< 0{,}70\%$/năm | $< 0{,}80\%$/năm |
| **Phản ứng Ánh sáng yếu** | Rất tốt (Hấp thụ quang phổ rộng) | Xuất sắc (Bifaciality $>80\%$) | Trung bình (Tán xạ nội tinh thể) | Tốt (Hấp thụ quang phổ xanh) |
| **Thiết bị tại UNISOLAR [7]** | **SunPower Maxeon / Jinko Tiger** | *Công nghệ thế hệ mới* | **Trina Solar Honey Series** | *Không sử dụng* |

---

#### Ý nghĩa Thực tế cho Data Analyst (DA Insight)
*   Trong kho dữ liệu, trường `dim_solar_site.panel_brand` phản ánh công nghệ tấm pin của từng trạm. Khi phân tích xếp hạng hiệu suất, các trạm sử dụng pin **SunPower Mono-Si** luôn ghi nhận năng suất riêng `[kWh/panel]` và hệ số $PR$ cao hơn các trạm sử dụng pin **Trina Poly-Si** từ $3\% - 5\%$ trong cùng điều kiện thời tiết.

---

### 1.3. Cấu trúc Hình học và Tô-pô Hệ thống Trạm (PV Topology)

#### Cấu trúc Phân cấp Ghép nối
*   **PV Cell (Tế bào):** Đơn vị quang điện cơ bản, sinh ra điện áp danh định xấp xỉ $0{,}5 - 0{,}6\,\text{V}$.
*   **PV Module (Tấm pin):** Cụm gồm 60 hoặc 72 cells mắc nối tiếp, cung cấp điện áp danh định $30 - 45\,\text{V}$ và công suất $300 - 550\,\text{Wp}$.
*   **PV String (Chuỗi tấm pin):** Chuỗi gồm $10 - 25$ tấm pin mắc nối tiếp để đạt tổng điện áp làm việc tối ưu $500 - 850\,\text{V DC}$ của Inverter.
*   **PV Array (Mảng trạm):** Nhiều chuỗi Strings ghép song song kết nối vào các ngõ MPPT của Biến tần.

---

#### Hiện tượng Che bóng & Cơ chế Bypass Diode [1, 3]
*   **Hiện tượng Điểm nóng (Hot-spot) do Mismatch:** Trong chuỗi mắc nối tiếp, dòng điện của toàn chuỗi bị giới hạn bởi cell có dòng quang sinh thấp nhất. Khi một cell bị che bóng bởi lá cây hoặc bụi bẩn, cell đó không phát điện mà chuyển sang trạng thái phân cực ngược, tiêu tán công suất của các cell khác thành nhiệt năng, có nguy cơ gây cháy hỏng tấm pin (Hot-spot).
*   **Cơ chế Phân dòng của Bypass Diode:** Tấm pin được chia làm 3 phân vùng cell độc lập, mỗi phân vùng được đấu song song ngược cực với một Bypass Diode. Khi một phân vùng bị che bóng, diode tương ứng tự động dẫn thông phân cực thuận, cho phép dòng điện của chuỗi đi vòng qua phân vùng lỗi, bảo vệ tấm pin và duy trì hoạt động cho các phân vùng còn lại.

![Diagram 1.3: Cơ chế Hoạt động của Bypass Diode khi có Cell bị Che bóng](diagrams/diagram_1_3_bypass_diode_mechanism.svg)

---

#### Ý nghĩa Thực tế cho Data Analyst (DA Insight)
*   **Nhận diện Hiện tượng Sụt giảm Bậc thang 33.3%:** Khi 1 diode bypass dẫn thông bảo vệ (hoặc bị hỏng ngắn mạch do sự cố quá áp/sét đánh), điện áp ngõ ra của tấm pin bị sụt giảm chính xác $33{,}3\%$ (mất 1 trong 3 phân vùng).
*   *Phân biệt trên biểu đồ chuỗi thời gian:*
    *   **Mây che tự nhiên:** Đồ thị sản lượng biến thiên liên tục, uốn lượn mượt mà theo biến động bức xạ $GHI$.
    *   **Hỏng Diode / Kẹt phân vùng:** Đồ thị sản lượng bị sụt giảm theo bậc thang cố định $33{,}3\%$ hoặc $66{,}7\%$ kéo dài liên tục nhiều ngày ngay cả trong điều kiện trời quang không mây.

---

### 1.4. Phân loại Biến tần (Inverters) & Bộ tối ưu MPPT

#### Chức năng của Biến tần và Thuật toán MPPT
*   **Biến tần (Inverter):** Thiết bị điện tử công suất thực hiện nghịch lưu dòng điện một chiều (DC) từ mảng pin thành dòng điện xoay chiều (AC $230\text{V}, 50\text{Hz}$) hòa vào mạng điện tiêu thụ của trường học với hiệu suất biến đổi $\ge 98\%$.
*   **Thuật toán Dò điểm Công suất Cực đại (MPPT):** Bức xạ và nhiệt độ thay đổi liên tục làm thay đổi đặc tuyến $P-V$. Bộ điều khiển MPPT liên tục điều chỉnh tỷ lệ chu kỳ xung (Duty Cycle) của mạch nghịch lưu để hệ thống luôn vận hành tại điểm làm việc có tích số $V_{\text{mp}} \times I_{\text{mp}}$ đạt giá trị lớn nhất.

---

#### So sánh 3 Kiến trúc Biến tần & Thuật toán MPPT [2, 4]

![Diagram 1.4: So sánh 3 Kiến trúc Tô-pô Biến tần Quang điện](diagrams/diagram_1_4_inverter_topologies.svg)

*   **Bản chất Thuật toán MPPT (Maximum Power Point Tracking) [4]:**
    *   *Thuật toán Nhiễu loạn & Quan sát (P&O):** Tăng/giảm thử một lượng điện áp nhỏ $\Delta V$. Nếu công suất tăng ($\Delta P > 0$) thì tiếp tục tăng áp; nếu công suất giảm ($\Delta P < 0$) thì đảo chiều giảm áp [4].
    *   *Thuật toán Điện dẫn Gia tăng (Incremental Conductance - InCond):* Dựa trên phương trình vi phân $\frac{dP}{dV} = 0 \iff \frac{dI}{dV} = -\frac{I}{V}$. Giúp Inverter đứng yên chính xác tại đỉnh MPP mà không bị rung lắc dao động [4].

---

#### Ý nghĩa Thực tế cho Data Analyst (DA Insight)
*   **Lựa chọn String Inverter tại UNISOLAR:** Các trạm trên mái nhà trường học có nhiều hướng dốc và độ che khuất khác nhau. Việc sử dụng String Inverter đa kênh MPPT (Fronius, SMA, ABB) giúp tối ưu hóa công suất độc lập cho từng cụm mái.
*   **Chuẩn hóa chỉ số phân tích:** Cần xây dựng các trường tính toán chuẩn hóa `[kWh/inverter]` và `[kWh/panel]` để so sánh công bằng hiệu năng giữa các trạm có cấu hình số lượng biến tần khác nhau.

---

### 1.5. Điều kiện Thử nghiệm Tiêu chuẩn (STC vs NOCT vs NMOT)

#### Phân biệt STC và Điều kiện Vận hành Thực tế
*   **STC (Standard Test Conditions - Chuẩn Thử nghiệm Phòng Thí nghiệm):** Đo lường tại bức xạ $1000\,\text{W/m}^2$, nhiệt độ tế bào quang điện $T_{\text{cell}} = 25^\circ\text{C}$ và khối lượng khí quyển $AM = 1{,}5$. Đây là giá trị công suất danh định chuẩn ($P_{\text{stc}}$, đơn vị $\text{kWp}$) được ghi trên nhãn kỹ thuật của nhà sản xuất.
*   **NOCT / NMOT (Nominal Operating Cell/Module Temperature - Chuẩn Vận hành Thực tế):** Đo lường tại bức xạ $800\,\text{W/m}^2$, nhiệt độ môi trường không khí $T_{\text{amb}} = 20^\circ\text{C}$ và tốc độ gió $1\,\text{m/s}$. Trong điều kiện này, nhiệt độ bề mặt tấm pin thực tế nóng lên tới xấp xỉ $45^\circ\text{C}$, do đó công suất thực phát thường thấp hơn công suất STC khoảng $15\% - 20\%$.

---

#### Bảng Đối soát Thông số Đo kiểm Tiêu chuẩn [5, 6]

| Đại lượng Tham số | STC (Standard Test Conditions) [5] | NOCT (Nominal Operating Cell Temp) [6] | NMOT (Nominal Module Operating Temp) [5] |
| :--- | :--- | :--- | :--- |
| **Tiêu chuẩn quốc tế** | **IEC 60904-3 / ASTM E1036** | **IEC 61215:2005 / Sandia** | **IEC 61215:2016 (Mới nhất)** |
| **Cường độ Bức xạ ($G$)** | **$1000\,\text{W/m}^2$** (Nắng đỉnh) | $800\,\text{W/m}^2$ (Nắng thực tế) | $800\,\text{W/m}^2$ (Nắng thực tế) |
| **Nhiệt độ tham chiếu** | **$T_{\text{cell}} = 25^\circ\text{C}$** | $T_{\text{amb}} = 20^\circ\text{C}$ (Không khí) | $T_{\text{amb}} = 20^\circ\text{C}$ (Không khí) |
| **Tốc độ gió làm mát ($v$)** | $0\,\text{m/s}$ (Phòng kín) | $1{,}0\,\text{m/s}$ | $1{,}0\,\text{m/s}$ |
| **Ứng dụng của Data Analyst** | **Tính công suất danh định $P_{\text{stc}}$ ($\text{kWp}$)** | **Tính $T_{\text{cell}}$ theo mô hình Sandia [6]** | Kiểm định công suất định mức thực tế |

---

### 1.6. Bối cảnh Dữ liệu Thực nghiệm Chi tiết (Dự án UNISOLAR - Đại học La Trobe)

#### Tóm tắt Quy mô Dự án (Executive Summary)
*   **Quy mô:** **42 trạm điện mặt trời áp mái** phân tán tại **5 khuôn viên (Campuses)** thuộc Đại học La Trobe, bang Victoria, Australia [7].
*   **Tổng công suất lắp đặt:** **$2.428\,\text{kWp}$** ($2{,}43\,\text{MWp}$) [7].
*   **Tập dữ liệu viễn thám:** **$2.731.946$ bản ghi** đo lường liên tục chu kỳ 15 phút ($0{,}25\,\text{h}$) từ **01/01/2020 đến 30/04/2022** (28 tháng).
*   **Tổng sản lượng lũy kế:** Đạt **$74{,}98\,\text{GWh}$**, tiết kiệm hơn $11{,}2\,\text{triệu AUD}$ tiền điện và giảm phát thải hơn $61.485\,\text{tấn CO}_2$ [7, 16].

![Diagram 1.6: Bản đồ Phân bố Địa lý 5 Khuôn viên Đại học La Trobe](diagrams/diagram_1_6_latrobe_campuses_map.svg)

*   **Bảng Cơ cấu Phân bổ Địa lý & Thiết bị Thực tế tại 5 Campus [7]:**

| STT | Tên Khuôn viên (Campus) | Tọa độ Địa lý (Lat, Long) | Đặc trưng Khí hậu Khu vực | Số lượng Trạm | Tổng Công suất Lắp đặt ($P_{\text{stc}}$) | Hãng Tấm pin Chủ đạo | Hãng Biến tần Chủ đạo |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **1** | **Bundoora (Melbourne)** | $-37{,}72^\circ\,\text{S}, 145{,}05^\circ\,\text{E}$ | Ôn đới hải dương, gió biển, mây di chuyển nhanh | **24 trạm** | **$1.420\,\text{kWp}$ ($58{,}5\%$)** | SunPower Mono-Si, Trina Poly-Si | Fronius Eco/Symo, SMA Tripower |
| **2** | **Bendigo** | $-36{,}78^\circ\,\text{S}, 144{,}30^\circ\,\text{E}$ | Bán khô hạn nội địa, biên độ nhiệt ngày/đêm lớn | **10 trạm** | **$580\,\text{kWp}$ ($23{,}9\%$)** | Jinko Solar Tiger Pro, Trina Honey | SMA Sunny Tripower, ABB Trio |
| **3** | **Albury-Wodonga** | $-36{,}12^\circ\,\text{S}, 146{,}96^\circ\,\text{E}$ | Thung lũng sông Murray, mùa đông sương mù dày | **4 trạm** | **$210\,\text{kWp}$ ($8{,}6\%$)** | SunPower Performance Series | Fronius Symo 3-Phase |
| **4** | **Shepparton** | $-36{,}38^\circ\,\text{S}, 145{,}40^\circ\,\text{E}$ | Lục địa ấm, bức xạ trực xạ DNI cao | **2 trạm** | **$118\,\text{kWp}$ ($4{,}9\%$)** | Trina Solar Monocrystalline | Fronius Eco 27.0-3-S |
| **5** | **Mildura** | $-34{,}22^\circ\,\text{S}, 142{,}15^\circ\,\text{E}$ | Bán sa mạc nắng nóng quanh năm, mùa hè $>42^\circ\text{C}$ | **2 trạm** | **$100\,\text{kWp}$ ($4{,}1\%$)** | SunPower Maxeon Mono-Si | SMA Sunny Tripower Core1 |
| **TỔNG**| **5 Campuses** | **Bang Victoria, Australia** | **Đa dạng vi khí hậu (Microclimates)** | **42 trạm** | **$2.428\,\text{kWp}$ ($2{,}43\,\text{MWp}$)** | **SunPower, Trina, Jinko** | **Fronius, SMA, ABB** |

*   **Đặc tính Chuỗi Thời gian & Tích hợp Khí tượng Viễn thám [7, 10, 13]:**
    *   Dữ liệu sản lượng 15 phút phản ánh động học phát điện tức thời và các hiện tượng quá áp lưới điện.
    *   Tích hợp đa chiều với 8 biến khí quyển chuẩn WMO ở độ phân giải 1 giờ từ mô hình ERA5-Land (Open-Meteo API) theo đúng tọa độ từng campus.

---

## UNIT 2: Khí tượng Viễn thám và Động học Nhật quỹ (Solar Meteorology & Geometry)

### 2.1. Động học Vị trí Mặt Trời (Thuật toán NREL/NOAA SPA) [8]
Vị trí góc của Mặt Trời so với một điểm bất kỳ trên bề mặt Trái Đất biến thiên liên tục theo chu kỳ ngày/đêm (do Trái Đất tự quay quanh trục với chu kỳ $24\,\text{h}$) và chu kỳ mùa (do Trái Đất chuyển động tịnh tiến quanh Mặt Trời trên quỹ đạo elip với độ nghiêng trục quay $\epsilon = 23{,}45^\circ$). Thuật toán NREL Solar Position Algorithm (SPA) của Reda & Andreas [8] là chuẩn mực tính toán vị trí nhật quỹ với độ chính xác góc đạt $\pm 0{,}0003^\circ$:

1.  **Ngày trong năm ($n$ - Day of Year) & Góc Thời gian Phân số ($\gamma$ - Fractional Year) [1, 8]:**
    $$n \in [1, 365] \quad (\text{hoặc } 366 \text{ đối với năm nhuận})$$
    $$\gamma = \frac{2\pi}{365} \cdot \left(n - 1 + \frac{\text{Hour} - 12}{24}\right) \quad (\text{radians})$$

2.  **Phương trình Thời gian (Equation of Time - EoT) [1, 8]:**
    Do quỹ đạo Trái Đất hình elip và độ nghiêng trục quay, độ dài của ngày mặt trời thực tế lệch so với ngày mặt trời trung bình (giờ đồng hồ dân dụng). Độ lệch thời gian $\text{EoT}$ (phút) được tính theo chuỗi Fourier Spencer [1]:
    $$\text{EoT} = 229{,}18 \cdot \left(0{,}000075 + 0{,}001868\cos\gamma - 0{,}032077\sin\gamma - 0{,}014615\cos(2\gamma) - 0{,}040849\sin(2\gamma)\right)$$

3.  **Giờ Mặt Trời Thực tế (True Solar Time - $t_{\text{solar}}$) [1, 8]:**
    $$t_{\text{solar}} = t_{\text{standard}} + \frac{4 \cdot (\text{Longitude} - \text{LSTM}) + \text{EoT}}{60} \quad (\text{hours})$$
    *Trong đó:*
    *   $\text{LSTM} = 15^\circ \times \Delta t_{\text{GMT}}$ là kinh độ của kinh tuyến giờ chuẩn địa phương (Local Standard Time Meridian). Ví dụ tại bang Victoria (Úc), múi giờ AEST có $\text{UTC}+10 \implies \text{LSTM} = 150^\circ\,\text{E}$.
    *   Hệ số $4\,\text{phút/độ}$ xuất phát từ tốc độ quay của Trái Đất ($360^\circ / 1440\,\text{phút} = 0{,}25^\circ/\text{phút}$).

4.  **Góc Xích vĩ Mặt Trời ($\delta$ - Solar Declination Angle) [1, 8]:**
    Góc tạo bởi tia sáng Mặt Trời với mặt phẳng xích đạo Trái Đất, biến thiên trong khoảng $-23{,}45^\circ \le \delta \le +23{,}45^\circ$:
    *   Hạ chí Bắc bán cầu (Đông chí Nam bán cầu - ngày 21/06): $\delta = +23{,}45^\circ$.
    *   Đông chí Bắc bán cầu (Hạ chí Nam bán cầu - ngày 21/12): $\delta = -23{,}45^\circ$.
    *   Xuân phân / Thu phân (ngày 21/03 và 21/09): $\delta = 0^\circ$.
    *   *Công thức xấp xỉ Cooper (1969) [1]:*
        $$\delta = 23{,}45^\circ \cdot \sin\left(\frac{360^\circ}{365} \cdot (284 + n)\right)$$

5.  **Góc Giờ Mặt Trời ($\omega$ - Solar Hour Angle) [1, 8]:**
    Góc quay của Trái Đất tính từ thời điểm giữa trưa quang học ($t_{\text{solar}} = 12\text{h}$):
    $$\omega = 15^\circ/\text{h} \cdot (t_{\text{solar}} - 12)$$
    *Quy ước:* Buổi sáng $\omega < 0$, giữa trưa $\omega = 0$, buổi chiều $\omega > 0$.

6.  **Góc Cao Mặt Trời ($h$ - Solar Elevation Angle) & Góc Thiên đỉnh ($\theta_z$ - Solar Zenith Angle) [1, 8]:**
    *   Góc cao $h$: Góc giữa tia tới của Mặt Trời với mặt phẳng chân trời nằm ngang ($0^\circ \le h \le 90^\circ$).
    *   Góc thiên đỉnh $\theta_z$: Góc giữa tia tới với phương thẳng đứng vuông góc mặt đất ($0^\circ \le \theta_z \le 90^\circ$).
    *   *Mối quan hệ hình học:*
        $$h = 90^\circ - \theta_z$$
        $$\sin(h) = \cos(\theta_z) = \sin(\phi) \cdot \sin(\delta) + \cos(\phi) \cdot \cos(\delta) \cdot \cos(\omega)$$
        *(với $\phi$ là vĩ độ địa lý của trạm trắc nghiệm, mang dấu âm ở Nam bán cầu, ví dụ Bundoora $\phi = -37{,}72^\circ$)*.

7.  **Góc Phương vị Mặt Trời ($\gamma_s$ - Solar Azimuth Angle) [8]:**
    Góc la bàn xác định hướng chiếu sáng của Mặt Trời trên mặt phẳng nằm ngang, quy ước $0^\circ = \text{Bắc}$, $90^\circ = \text{Đông}$, $180^\circ = \text{Nam}$, $270^\circ = \text{Tây}$:
    $$\cos(\gamma_s) = \frac{\sin(\delta)\cos(\phi) - \cos(\delta)\sin(\phi)\cos(\omega)}{\cos(h)}$$

---

### 2.2. Mã hóa Chu kỳ Lượng giác trong Machine Learning [9]
Khi đưa đặc trưng thời gian vào các thuật toán học máy (Gradient Boosting, GMM, Isolation Forest, Neural Networks), việc sử dụng biến số nguyên thô ($\text{Hour} \in [0, 23]$ hoặc $\text{Month} \in [1, 12]$) sẽ gây ra **lỗi đứt gãy tô-pô phi vật lý**:
*   Khoảng cách Euclid giữa $23\text{h}$ đêm và $0\text{h}$ sáng bị tính là $\vert{}23 - 0\vert{} = 23$, trong khi thực tế hai thời điểm này chỉ cách nhau đúng $1\,\text{giờ}$ liên tục.
*   Để bảo toàn tính liên tục chu kỳ khép kín trên đường tròn đơn vị, kỹ thuật Cyclical Encoding ánh xạ thời gian sang không gian tọa độ 2 chiều [9]:

$$\text{Hour}_{\sin} = \sin\left(\frac{2\pi \cdot \text{Hour}}{24}\right), \quad \text{Hour}_{\cos} = \cos\left(\frac{2\pi \cdot \text{Hour}}{24}\right)$$
$$\text{Month}_{\sin} = \sin\left(\frac{2\pi \cdot \text{Month}}{12}\right), \quad \text{Month}_{\cos} = \cos\left(\frac{2\pi \cdot \text{Month}}{12}\right)$$

*   **Tích hợp Góc Quang năng Nhật quỹ vào Mô hình ML:** Thay vì chỉ dựa vào thời gian đồng hồ, đưa trực tiếp $\sin(h)$ và $\cos(\theta_z)$ vào ma trận đặc trưng giúp mô hình học trực tiếp mật độ photon tới khí quyển, triệt tiêu sai số do sự lệch pha giữa giờ quy ước dân dụng và quỹ đạo chiếu sáng thực tế [8, 9].

---

### 2.3. Các Thành phần Bức xạ Mặt Trời chuẩn WMO [10]
Tổ chức Khí tượng Thế giới (World Meteorological Organization - WMO No. 8) [10] quy chuẩn năng lượng bức xạ mặt trời sóng ngắn dải quang phổ $0{,}3\,\mu\text{m} - 3{,}0\,\mu\text{m}$ (đơn vị: $\text{W/m}^2$) thành 3 thành phần cơ bản:

| Thành phần Bức xạ | Ký hiệu & Đơn vị | Định nghĩa Vật lý & Cơ chế Lan truyền | Thiết bị Đo lường Tiêu chuẩn |
| :--- | :---: | :--- | :--- |
| **Bức xạ Toàn phần Mặt ngang (Global Horizontal Irradiance)** | **$GHI$** ($\text{W/m}^2$) | Tổng lượng quang năng sóng ngắn chiếu tới một mét vuông bề mặt nằm ngang, bao gồm cả tia trực tiếp và tia tán xạ bầu trời. | Nhiệt điện kế bức xạ quang phổ rộng (**Pyranometer Class A** chuẩn ISO 9060). |
| **Bức xạ Trực xạ Pháp tuyến (Direct Normal Irradiance)** | **$DNI$** ($\text{W/m}^2$) | Lượng quang năng chiếu thẳng trực tiếp từ đĩa Mặt Trời tới bề mặt luôn giữ góc vuông với tia tới. | Nhật xạ kế hẹp góc (**Pyrheliometer**) gắn trên hệ thống bám nhật quỹ 2 trục tự động. |
| **Bức xạ Tán xạ Mặt ngang (Diffuse Horizontal Irradiance)** | **$DHI$** ($\text{W/m}^2$) | Lượng quang năng bị tán xạ bởi các phân tử khí (tán xạ Rayleigh), hạt bụi/sol khí Aerosol (tán xạ Mie) và phản xạ từ mây chiếu tới mặt ngang. | Pyranometer có gắn **Vòng chắn bóng râm (Shading Ball/Ring)** để che đĩa Mặt Trời. |

*   **Phương trình Cân bằng Bức xạ Năng lượng [1, 10]:**
    $$GHI = DNI \cdot \sin(h) + DHI = DNI \cdot \cos(\theta_z) + DHI$$
*   **Hệ số Tán xạ Khí quyển (Diffuse Fraction - $k_d$) [1]:**
    $$k_d = \frac{DHI}{GHI} \in [0, 1]$$
    *   $k_d \approx 0{,}10 - 0{,}20$: Bầu trời quang đãng, bức xạ trực xạ chiếm ưu thế tuyệt đối.
    *   $k_d \to 1{,}00$: Bầu trời âm u nhiều mây, toàn bộ bức xạ thu nhận được đều là tán xạ khuếch tán.

---

### 2.4. Mô hình Bức xạ Trời quang (Clear-Sky Models & CSI) [11, 12]

#### Mô hình Trời quang Haurwitz (1945) [11]
Mô hình thực nghiệm Haurwitz thiết lập ngưỡng giới hạn trên lý thuyết của bức xạ $GHI_{\text{cs}}$ có thể tới được mặt đất trong điều kiện khí quyển trong suốt không có mây:

$$GHI_{\text{cs}} = 1098 \cdot \sin(h) \cdot \exp\left(-\frac{0{,}059}{\sin(h)}\right) \cdot \text{cs\_factor}_{\text{site}}$$

*Trong đó:*
*   $1098\,\text{W/m}^2$: Hằng số thực nghiệm đại diện cho bức xạ biểu kiến trên mặt đất.
*   $\text{cs\_factor}_{\text{site}}$: Hệ số hiệu chỉnh độ cao địa hình và độ trong suốt khí quyển của từng campus ($0{,}95 - 1{,}05$).

#### Chỉ số Bầu trời Quang (Clear-Sky Index - CSI) [12]
Chỉ số không thứ nguyên $CSI$ định lượng tỷ lệ xuyên thấu quang năng qua lớp mây quyển:
$$CSI = \frac{GHI}{GHI_{\text{cs}}}$$

*   **Phân loại Trạng thái Khí quyển theo CSI [12]:**
    1.  $CSI \ge 0{,}85$: **Trời hoàn toàn quang đãng (Clear Sky)** $\rightarrow$ Hệ thống phát điện ổn định theo đường parabol hoàn hảo.
    2.  $0{,}35 \le CSI < 0{,}85$: **Mây đối lưu che từng phần (Broken Clouds)** $\rightarrow$ Sản lượng biến động dao động mạnh.
    3.  $CSI < 0{,}35$: **Trời âm u, mây dày (Overcast)** $\rightarrow$ Mất phần lớn trực xạ, chỉ còn tán xạ $DHI$.
    4.  $CSI > 1{,}15$: **Hiện tượng Cộng hưởng Phản xạ Mép Mây (Cloud Enhancement Effect) [1]** $\rightarrow$ Khi ánh sáng trực xạ từ Mặt Trời đi qua khe mây kết hợp với bức xạ tán xạ phản xạ mạnh từ các cạnh mây đối lưu xung quanh hội tụ lại điểm đo, đẩy giá trị $GHI$ tức thời vọt lên $1100 - 1300\,\text{W/m}^2$ trong vài phút. Đây là hiện tượng vật lý quang học tự nhiên, không phải lỗi cảm biến.

![Diagram 1.7: Động học Nhật quỹ NREL SPA và 3 Thành phần Bức xạ Khí quyển WMO](diagrams/diagram_1_7_solar_geometry_wmo_radiation.svg)

---

### 2.5. Các Biến Khí quyển Tác động từ ERA5-Land Reanalysis [13]
Dữ liệu khí tượng thu thập qua Open-Meteo REST API kế thừa từ mô hình tái phân tích toàn cầu **ERA5-Land** của Trung tâm Dự báo Thời tiết Hạn vừa Châu Âu (ECMWF) với độ phân giải lưới không gian $9\,\text{km}$ [13], cung cấp 8 biến vật lý chuẩn WMO chu kỳ 1 giờ ($850.752$ bản ghi):

| STT | Biến Khí quyển | Ký hiệu & Đơn vị | Độ cao Quy chuẩn | Cơ chế Vật lý Tác động đến Sản lượng Điện Mặt Trời |
| :---: | :--- | :---: | :---: | :--- |
| **1** | Bức xạ Toàn phần | $GHI$ ($\text{W/m}^2$) | Mặt đất | Quyết định trực tiếp dòng quang sinh $I_{\text{ph}}$ và sản lượng điện $E_{\text{actual}}$ phát ra. |
| **2** | Bức xạ Trực xạ | $DNI$ ($\text{W/m}^2$) | Pháp tuyến | Phản ánh mức độ trong suốt của khí quyển; quyết định hiệu suất quang phổ. |
| **3** | Bức xạ Tán xạ | $DHI$ ($\text{W/m}^2$) | Mặt đất | Đóng góp năng lượng chủ yếu vào những ngày trời nhiều mây và góc chiếu thấp. |
| **4** | Nhiệt độ Không khí | $T_{\text{amb}}$ ($^\circ\text{C}$) | $2\,\text{m}$ | Làm tăng nhiệt độ tế bào $T_{\text{cell}}$, gây sụt giảm điện áp hở mạch và suy hao công suất. |
| **5** | Tốc độ Gió | $v_{\text{wind}}$ ($\text{m/s}$) | $10\,\text{m}$ | Tản nhiệt đối lưu cưỡng bức làm mát bề mặt tấm pin, giúp hạ $T_{\text{cell}}$ và hồi phục hiệu suất. |
| **6** | Độ che phủ Mây Tổng | $Cloud\ Cover$ ($\%$) | Toàn cột khí quyển | Tỷ lệ phần trăm bầu trời bị mây che phủ; tương quan nghịch mạnh với $GHI$. |
| **7** | Mây Tầng Thấp | $Low\ Clouds$ ($\%$) | $< 2\,\text{km}$ | Mây tích và mây tầng thấp có mật độ nước cao nhất, gây tán xạ và cản trở bức xạ mạnh nhất. |
| **8** | Thời lượng Nắng | $Sunshine$ ($\text{s}$) | Cấp giờ ($0-3600\text{s}$) | Tổng số giây trong 1 giờ có cường độ trực xạ $DNI \ge 120\,\text{W/m}^2$ theo chuẩn WMO. |

---

## UNIT 3: Bộ Chỉ số Đo lường Hiệu năng Cốt lõi (Solar Analytics KPI Framework)

### 3.1. Hệ số Hiệu suất (Performance Ratio - PR) chuẩn IEC 61724-1 [14]
Theo tiêu chuẩn quốc tế **IEC 61724-1:2021** [14], $PR$ là chỉ số chuẩn mực toàn cầu dùng để đánh giá chất lượng vận hành và độ hoàn thiện của hệ thống điện mặt trời độc lập với quy mô công suất và vị trí địa lý:

$$\text{PR} = \frac{Y_f}{Y_r} = \frac{\frac{E_{\text{actual}}}{P_{\text{stc}}}}{\frac{H_{\text{total}}}{G_{\text{STC}}}} = \frac{E_{\text{actual}}}{P_{\text{stc}} \cdot \left(\frac{GHI}{1000\,\text{W/m}^2}\right) \cdot \Delta t} \times 100\%$$

*Trong đó [14]:*
*   $Y_f$ (Final Yield - Năng suất Thực phát): $Y_f = \frac{E_{\text{actual}}}{P_{\text{stc}}}$ (đơn vị: $\text{kWh/kWp}$ hoặc giờ phát tương đương ở công suất cực đại).
*   $Y_r$ (Reference Yield - Năng suất Tham chiếu): $Y_r = \frac{\sum GHI \cdot \Delta t}{1000\,\text{W/m}^2}$ (đơn vị: $\text{Peak Sun Hours - PSH}$).
*   $P_{\text{stc}}$: Tổng công suất thiết kế định mức ở điều kiện STC ($\text{kWp}$).
*   $\Delta t$: Khoảng thời gian chu kỳ đo lường ($0{,}25\,\text{h}$ đối với chu kỳ 15 phút, hoặc $1\,\text{h}$ đối với cấp giờ).

*   **Bộ Ngưỡng Đánh giá Hiệu năng Vận hành theo PR [14]:**
    *   **$PR \ge 78\%$ (Tối ưu - Class A):** Hệ thống vận hành ở trạng thái xuất sắc, suy hao thấp, thiết bị đồng bộ hoàn hảo.
    *   **$65\% \le PR < 78\%$ (Trung bình - Class B):** Vận hành chấp nhận được nhưng chịu ảnh hưởng suy hao nhiệt độ mùa hè hoặc bám bụi nhẹ.
    *   **$PR < 65\%$ (Kém / Cảnh báo - Class C):** Hệ thống có dị thường nghiêm trọng (hỏng biến tần, đứt cầu chì chuỗi, che bóng cục bộ nặng).
*   **Quy tắc Lọc Dữ liệu Đo đếm ($GHI \ge 100\,\text{W/m}^2$) [14]:** Chỉ thực hiện tính toán $PR$ khi cường độ bức xạ vượt ngưỡng $100\,\text{W/m}^2$. Khi trời sáng sớm hoặc chiều muộn ($GHI < 100\,\text{W/m}^2$), biến tần chưa đạt điện áp khởi động (Startup Voltage), hiệu suất biến đổi phi tuyến và sai số góc tới của cảm biến quang học sẽ làm giá trị $PR$ bị méo mó giả tạo.

---

### 3.2. Hệ số Hiệu suất Hiệu chỉnh Nhiệt độ (Temperature-Corrected PR) [14, 15]
Vào mùa hè, nhiệt độ bề mặt tấm pin tăng cao làm điện áp sụt giảm, khiến $PR$ danh định giảm tự nhiên $5\% - 10\%$ dù thiết bị hoàn toàn bình thường. Phụ lục B của tiêu chuẩn **IEC 61724-1** [14] và phương pháp chuẩn hóa của NREL [15] quy định công thức hiệu chỉnh nhiệt độ về mốc $25^\circ\text{C}$:

$$\text{PR}_{\text{corr}} = \frac{E_{\text{actual}}}{P_{\text{stc}} \cdot \left(\frac{GHI}{1000}\right) \cdot \Delta t \cdot \left[1 + \gamma \cdot (T_{\text{cell}} - 25^\circ\text{C})\right]} \times 100\%$$

*(với $\gamma$ là hệ số suy giảm công suất theo nhiệt độ của tấm pin, đơn vị: $\%/^\circ\text{C}$, ví dụ $\gamma = -0{,}35\%/^\circ\text{C}$)* [1, 14].

*   **Giá trị cho Phân tích Dữ liệu Dài hạn:** Chỉ số $PR_{\text{corr}}$ loại bỏ hoàn toàn ảnh hưởng mùa vụ thời tiết, cho phép Data Analyst theo dõi chính xác **tốc độ thoái hóa thực tế của vật liệu bán dẫn qua từng năm** (Degradation Rate, thông thường $< 0{,}5\%/\text{năm}$).

![Diagram 1.8: Khung Đo lường Hiệu năng Quang điện và Chỉ số PR chuẩn IEC 61724-1](diagrams/diagram_1_8_solar_kpi_pr_framework.svg)

---

### 3.3. Năng suất Riêng (Specific Yield) & Hệ số Công suất (Capacity Factor) [14, 15]
*   **Năng suất Riêng (Specific Yield - $Y_f$) [14, 15]:**
    $$Y_f = \frac{\sum E_{\text{actual}}}{P_{\text{stc}}} \quad (\text{kWh/kWp/ngày hoặc kWh/kWp/năm})$$
    Cho phép so sánh trực tiếp hiệu quả phát điện giữa trạm nhỏ $10\,\text{kWp}$ và mảng trạm lớn $320\,\text{kWp}$. Tại bang Victoria (Úc), $Y_f$ trung bình đạt $3{,}8 - 4{,}5\,\text{kWh/kWp/ngày}$ vào mùa hè và $1{,}8 - 2{,}4\,\text{kWh/kWp/ngày}$ vào mùa đông.
*   **Hệ số Công suất (Capacity Factor - $CF$) [15]:**
    Tỷ lệ giữa sản lượng thực tế sản sinh trong một chu kỳ thời gian (ví dụ 1 năm $8760\,\text{h}$) so với sản lượng lý thuyết nếu trạm chạy liên tục $100\%$ công suất định mức:
    $$\text{CF} = \frac{\sum E_{\text{actual}}}{P_{\text{stc}} \cdot 8760\,\text{h}} \times 100\%$$
    Do tính chu kỳ ngày/đêm và thời tiết nhiều mây, $CF$ của hệ thống điện mặt trời trên thế giới thường nằm trong dải **$15\% - 22\%$** (tại dự án UNISOLAR đạt trung bình **$15{,}2\%$**).

---

### 3.4. Chỉ số Kinh tế & Tác động Giảm phát thải Khí nhà kính [16, 17]
*   **Mô hình Tiết kiệm Chi phí & Biểu giá Điện FiT [17]:**
    *   Doanh thu tự dùng và hòa lưới: $\text{Savings (AUD)} = E_{\text{actual}} \times \text{Tariff}_{\text{AUD/kWh}}$.
    *   Thị trường Điện Quốc gia Úc (AEMO NEM) áp dụng cơ chế thanh toán bù trừ 5 phút và ghi nhận hiện tượng giá bán buôn âm vào giữa trưa khi năng lượng tái tạo chiếm tỷ trọng lớn trong hệ thống truyền tải [17].
*   **Hệ số Giảm phát thải Khí nhà kính Quốc gia Úc (NGA Factors) [16]:**
    Theo Báo cáo Hệ số Kế toán Khí nhà kính Quốc gia của Bộ Biến đổi Khí hậu và Năng lượng Úc (DCCEEW) [16], phát thải Scope 2 gián tiếp từ lưới điện bang Victoria trong giai đoạn 2020-2022 được xác định là $0{,}82\,\text{kg CO}_2\text{-e/kWh}$:
    $$\text{CO}_2\text{ Reduction (kg)} = E_{\text{actual}} \times 0{,}82\,\text{kg CO}_2/\text{kWh}$$
    $$\text{CO}_2\text{ Reduction (Tấn)} = \frac{E_{\text{actual}} \times 0{,}82}{1000}$$
    *Tổng kết dự án UNISOLAR:* Tổng sản lượng $74{,}98\,\text{GWh}$ giúp cắt giảm lũy kế **$61.485\,\text{tấn CO}_2$** và tiết kiệm hơn **$11{,}2\,\text{triệu AUD}$** cho Đại học La Trobe [7, 16].

---

## UNIT 4: Cơ chế Suy hao & Phân rã Tổn thất (Loss Decomposition Analysis)

![Diagram 1.5: Sơ đồ Cây Phân rã Tổn thất Quang điện](diagrams/diagram_1_5_loss_tree.svg)

### 4.1. Suy hao do Quá nhiệt Tế bào Quang điện (Thermal Derating) [1, 6]
*   **Mô hình Ước tính Nhiệt độ Tế bào Sandia (Sandia Photovoltaic Array Model) [6]:**
    Nhiệt độ mặt sau tấm pin $T_{\text{cell}}$ được ước tính từ nhiệt độ môi trường, bức xạ và tốc độ gió làm mát:
    $$T_{\text{cell}} = T_{\text{amb}} + GHI \cdot \exp\left(a + b \cdot v_{\text{wind}}\right) + \frac{GHI}{1000} \cdot \Delta T_{\text{module-cell}}$$
    *Với cấu trúc áp mái thông gió mở (Open-Rack):* Các hệ số Sandia tiêu chuẩn gồm $a = -3{,}47$, $b = -0{,}0594$, $\Delta T = 3^\circ\text{C}$ [6].
*   **Mô hình Đơn giản hóa dựa trên NOCT [1, 6]:**
    $$T_{\text{cell}} = T_{\text{amb}} + \left(\frac{\text{NOCT} - 20^\circ\text{C}}{800\,\text{W/m}^2}\right) \cdot GHI$$
*   **Định lượng Năng lượng Thất thoát do Nhiệt (Thermal Energy Loss) [1, 6]:**
    Khi $T_{\text{cell}} > 25^\circ\text{C}$, tổn thất năng lượng tại mỗi chu kỳ 15 phút:
    $$E_{\text{loss, temp}} = E_{\text{theo}} \cdot \vert{}\gamma\vert{} \cdot \max\left(0, T_{\text{cell}} - 25^\circ\text{C}\right)$$
    *(với $E_{\text{theo}} = P_{\text{stc}} \cdot \frac{GHI}{1000} \cdot 0{,}25\,\text{h}$)*.
    Vào mùa hè tại bang Victoria, khi nhiệt độ môi trường chạm mốc $42^\circ\text{C}$, nhiệt độ cell $T_{\text{cell}}$ thường vượt ngưỡng $65^\circ\text{C}$, gây suy giảm từ **$14\% - 18\%$** công suất phát tức thời [6, 14].

---

### 4.2. Suy hao Xén Công suất Biến tần (Inverter Clipping Loss) [18]
*   **Tỷ lệ Quá tải DC/AC (Inverter Loading Ratio - ILR) [18]:**
    $$\text{ILR} = \frac{P_{\text{DC, Array}}}{P_{\text{AC, Inverter}}}$$
    Trong thiết kế thực tế, tỷ lệ $\text{ILR}$ luôn được chọn trong khoảng **$1{,}15 - 1{,}30$** (công suất mảng pin lớn hơn công suất định mức của biến tần $15\% - 30\%$). Thiết kế này giúp tối ưu hóa tổng sản lượng điện thu được vào buổi sáng sớm, chiều muộn và các tháng mùa đông khi bức xạ yếu [18].
*   **Cơ chế Tự bảo vệ Cắt đỉnh (Clipping Mechanism) [18]:** Khi công suất DC tạo ra vào giữa trưa vượt quá công suất định mức cực đại $P_{\text{AC, max}}$ của Inverter, bộ điều khiển MPPT tự động dịch chuyển điểm làm việc $V_{\text{mp}}$ sang phía điện áp cao hơn để giảm dòng điện ngõ vào, duy trì công suất AC đầu ra ổn định bằng đúng $P_{\text{AC, max}}$.
*   **Đặc điểm Dữ liệu Telemetry:** Đồ thị sản lượng chuỗi thời gian xuất hiện đường cong đỉnh phẳng hình thang (Trapezoidal Flat-top curve). Data Analyst cần lưu ý đây là **đặc tính vận hành thiết kế có chủ đích**, hoàn toàn không phải lỗi phần cứng [18].

![Diagram 1.9: Cơ chế Vật lý và Đặc tính Chuỗi thời gian của Clipping, Suy hao Nhiệt độ và Bám bụi](diagrams/diagram_1_9_clipping_and_thermal_derating.svg)

---

### 4.3. Suy hao do Bám bụi & Che bóng Cục bộ (Soiling & Shading) [19]
*   **Mô hình Suy hao Bám bụi Kimber (Kimber Soiling Model) [19]:**
    Bụi bẩn, cát mịn và phân chim tích tụ trên mặt kính làm giảm độ truyền quang từ $1\% - 6\%$:
    $$\text{Soiling Rate} = 0{,}1\% - 0{,}3\%/\text{ngày không mưa}$$
    Sau các trận mưa lớn tích lũy đạt $\ge 5\,\text{mm}$, lớp bụi bẩn được gột rửa tự nhiên, đưa hệ số bám bụi về mức $0\%$ [19].
*   **Suy hao Che bóng Tương hỗ & Vật cản (Shading Loss) [1]:**
    Bao gồm che bóng gần (Near-shading do lan can, cây cối, tháp làm mát) và che bóng xa (Far-shading do đường chân trời và núi). Khi góc cao Mặt Trời $h$ thấp vào mùa đông, bóng của hàng pin phía trước có thể đổ lên hàng pin phía sau nếu khoảng cách giữa các dãy không đạt chuẩn khoảng cách tối thiểu ($Row\ Pitch$) [1].

---

## UNIT 5: Nhận diện Dị thường Vận hành & Bảo trì Dựa trên Điều kiện (CBM)

### 5.1. Báo cáo Độ tin cậy IEA-PVPS Task 13 [3]
Báo cáo thống kê độ tin cậy của Cơ quan Năng lượng Quốc tế (IEA-PVPS Task 13) [3] dựa trên dữ liệu vận hành hàng ngàn trạm điện mặt trời thương mại chỉ ra:
*   **Biến tần (Inverter)** là thành phần có tỷ lệ hỏng hóc cao nhất trong toàn bộ hệ thống, với Thời gian trung bình giữa các sự cố (MTBF) ngắn hơn từ $300 - 500$ lần so với module quang điện [3].
*   Sự cố liên quan đến biến tần, rơ-le bảo vệ và thiết bị đóng cắt AC/DC chiếm tới **$38\% - 45\%$** tổng tổn thất năng lượng do phần cứng hàng năm [3].

---

### 5.2. Chẩn đoán Chi tiết 6 Nhóm Dị thường Kỹ thuật Vật lý Đặc trưng
Trong đề tài tốt nghiệp, hệ thống phân loại 6 mã dị thường vật lý và học máy được chuẩn hóa phục vụ giám sát tự động:

| Mã Phân loại Dị thường | Dấu hiệu Dữ liệu Telemetry (Footprint) | Nguyên nhân Kỹ thuật Vật lý | Tiêu chuẩn Kỹ thuật Liên quan | Hành động Khắc phục O&M |
| :--- | :--- | :--- | :--- | :--- |
| **`PHYSICAL_LOW_ENERGY_STRONG_SUN`** | $GHI \ge 700\,\text{W/m}^2$, $Sunshine \ge 3000\,\text{s}$ nhưng Sản lượng $E \le 0{,}05 \cdot P_{95}$ ($E \approx 0\,\text{kWh}$) liên tục $1-3$ chu kỳ. | **Quá áp lưới điện (Sustained Overvoltage):** Điện áp hòa lưới vượt ngưỡng cắt bảo vệ $258\,\text{V}$ (ngưỡng 10 phút) làm Inverter tự ngắt, hoặc quạt tản nhiệt biến tần bị hỏng gây quá nhiệt IGBT. | **AS/NZS 4777.2:2020** (Quy chuẩn Inverter nối lưới Úc) [20]. | Điều phối kỹ sư kiểm tra cài đặt bảo vệ rơ-le điện áp lưới hoặc vệ sinh quạt tản nhiệt Inverter. |
| **`PHYSICAL_HIGH_ENERGY_NO_SUN`** | $GHI \le 25\,\text{W/m}^2$, $Sunshine \le 60\,\text{s}$ (Ban đêm) nhưng cảm biến ghi nhận sản lượng $E \ge \max(1.0, 0{,}20 \cdot P_{\text{stc}})$. | **Lệch Điểm 0 Cảm biến Biến dòng (CT Drift):** Cảm biến đo dòng bị trôi mốc 0 do nhiệt độ ban đêm, hoặc Inverter tiêu thụ công suất phản kháng tĩnh từ lưới. | **IEC 61724-1 Class A/B** (Độ chính xác cảm biến đo) [14]. | Hiệu chuẩn lại cảm biến biến dòng (CT Calibration) và kiểm tra chế độ chờ ban đêm của Inverter. |
| **`PHYSICAL_OVER_CAPACITY`** | Sản lượng trong 1 chu kỳ vọt lên $E > P_{\text{stc}} \times 0{,}25\,\text{h}$ ($> 100\%$ công suất thiết kế cực đại). | **Xung Điện Telemetry / Lỗi Gộp Gói SCADA:** Nghẽn mạng truyền thông Modbus/RS485 khiến hệ thống thu thập gom số liệu của 2-3 chu kỳ trước dồn vào một mốc thời gian. | **SunSpec Modbus Protocol / IEC 60870-5-104** [3]. | Xóa bản ghi xung ảo, kiểm tra độ ổn định của cáp truyền thông mạng công nghiệp RS485. |
| **`PHYSICAL_HIGH_ENERGY_LOW_RAD`** | Bức xạ rất yếu ($GHI \le 50\,\text{W/m}^2$) nhưng sản lượng vọt cao bất thường ($E > Q_3 + 4 \cdot \text{safe\_IQR}$). | **Lỗi Cảm biến Bức xạ / Nhiễu Vi mạch ADC:** Pyranometer bị kẹt tín hiệu đầu ra hoặc vi mạch chuyển đổi tương tự-số ADC bị nhiễu điện từ. | **ISO 9060:2018** (Đặc tính nhiệt điện kế bức xạ) [10]. | Kiểm tra điện áp cấp nguồn và cáp tín hiệu analog của nhiệt điện kế Pyranometer. |
| **`PHYSICAL_DISTRIBUTION_JUMP`** | Đột biến sản lượng tức thời so với các chu kỳ liền kề ($\vert{}\Delta E\vert{} \ge \max(0{,}15 \cdot P_{95}, 1.0)$). | **Đóng/Ngắt Tức thời Chuỗi Pin:** Rơ-le hoặc cầu chì một nhánh chuỗi (String Fuse) bị nổ ngắt mạch làm hụt $20\% - 50\%$ công suất trong chu kỳ. | **IEC 60269-6** (Tiêu chuẩn cầu chì bảo vệ hệ thống PV) [3]. | Kiểm tra tình trạng dây dẫn và thay thế cầu chì chuỗi DC bị nổ trong tủ kết hợp chuỗi (Combiner Box). |
| **`GMM_IF_ANOMALY`** | Cả hai mô hình GMM và Isolation Forest cùng đồng thuận bỏ phiếu ($P_{\text{GMM}} < 0{,}02$ và $\text{Score}_{\text{IF}} > \text{Threshold}$). | **Suy giảm Hiệu suất Tổ hợp Đa biến:** Bám bụi nặng cục bộ, thoái hóa tế bào quang điện do điện thế cảm ứng (PID), hoặc che bóng phức tạp không theo quy luật. | **IEC 62804** (Thử nghiệm suy thoái cảm ứng PID) [3]. | Lên kế hoạch rửa pin bằng vòi áp lực hoặc soi nhiệt hồng ngoại (IR Thermography) tìm tế bào PID. |

![Diagram 1.10: Kiến trúc Phát hiện Dị thường và Quy trình Tự động hóa O&M chuẩn ISO 13374](diagrams/diagram_1_10_cbm_anomaly_iso13374_workflow.svg)

---

### 5.3. Quy trình Tự động Hóa O&M và Tạo Lệnh Công tác (Work Order) [21]
Quy trình chuyển hóa dữ liệu viễn thám thành hành động bảo trì tại hiện trường tuân thủ kiến trúc chuẩn **ISO 13374 (Condition Monitoring and Diagnostics of Machines)** [21]:

1.  **Thu nhận & Tiền xử lý (Data Acquisition & Manipulation):** Tiếp nhận dữ liệu chu kỳ 15 phút, căn chỉnh thời gian nhân quả Floor-Hour Lookup và điền khuyết đa tầng.
2.  **Phát hiện Trạng thái (State Detection):** Chạy song song mô hình lai GMM-IF và bộ 5 rào chắn vật lý để phát hiện dị thường và gán nhãn `outlier_reason`.
3.  **Định lượng Thiệt hại Năng lượng & Tài chính (Health Assessment & Quantification):**
    $$\Delta E_{\text{lost}} = E_{\text{theo}} \cdot \text{PR}_{\text{target}} - E_{\text{actual}} \quad (\text{kWh})$$
    $$\text{Financial Loss (AUD)} = \Delta E_{\text{lost}} \times \text{Tariff}_{\text{AUD/kWh}}$$
4.  **Tự động Tạo Phiếu Công tác (Automated CMMS Work Order Dispatching) [21]:**
    Hệ thống tự động phát sinh phiếu công tác gửi đến ban quản lý vận hành gồm các thông tin:
    *   Tên cơ sở (Campus) và Vị trí tòa nhà lắp trạm (`site_name`, `latitude`, `longitude`).
    *   Mã phân loại nguyên nhân sự cố (`outlier_reason`) kèm theo mô tả kỹ thuật chi tiết.
    *   Đồ thị chuỗi thời gian so sánh sản lượng thực tế $E_{\text{actual}}$ với đường cong lý thuyết $E_{\text{theo}}$.
    *   Mức độ ưu tiên khắc phục (Priority: High / Medium / Low) dựa trên thiệt hại kinh tế tích lũy.

---

## TÀI LIỆU THAM KHẢO HỌC THUẬT & TIÊU CHUẨN QUỐC TẾ

1.  **Duffie, J. A., & Beckman, W. A. (2020)**. *Solar Engineering of Thermal Processes, Photovoltaics and Wind* (5th ed.). John Wiley & Sons. DOI: [10.1002/9781119540328](https://doi.org/10.1002/9781119540328).
2.  **Messenger, R. A., & Abtahi, A. (2017)**. *Photovoltaic Systems Engineering* (4th ed.). CRC Press.
3.  **IEA-PVPS Task 13 (2021)**. *Review on Failures of Photovoltaic Modules and Inverter Reliability in Utility and Commercial Installations*. International Energy Agency Photovoltaic Power Systems Programme, Report IEA-PVPS T13-14:2021.
4.  **Subudhi, B., & Pradhan, R. (2011)**. A comparative study on maximum power point tracking techniques for photovoltaic power systems. *IEEE Transactions on Sustainable Energy*, 2(1), 81-90.
5.  **IEC 60904-3:2019**. *Photovoltaic devices - Part 3: Measurement principles for terrestrial photovoltaic (PV) solar devices with reference spectral irradiance data*. International Electrotechnical Commission.
6.  **King, D. L., Boyson, W. E., & Kratochvil, J. A. (2004)**. *Photovoltaic Array Performance Model*. Sandia National Laboratories Technical Report, SAND2004-3535.
7.  **La Trobe University (2022)**. *UNISOLAR Smart Campus Energy Transition Initiative: Rooftop PV Performance Dataset (2020-2022)*. Victoria, Australia.
8.  **Reda, I., & Andreas, A. (2004)**. Solar position algorithm for solar radiation applications. *Solar Energy*, 76(5), 577-589. DOI: [10.1016/j.solener.2003.12.003](https://doi.org/10.1016/j.solener.2003.12.003).
9.  **Hastie, T., Tibshirani, R., & Friedman, J. (2009)**. *The Elements of Statistical Learning: Data Mining, Inference, and Prediction* (2nd ed.). Springer.
10. **World Meteorological Organization (WMO, 2018)**. *Guide to Meteorological Instruments and Methods of Observation (WMO-No. 8)*. Geneva, Switzerland.
11. **Haurwitz, B. (1945)**. Insolation in relation to cloudiness and cloud density. *Journal of Meteorology*, 2(3), 154-166.
12. **Ineichen, P., & Perez, R. (2002)**. A new airmass independent formulation for the Linke turbidity coefficient. *Solar Energy*, 73(3), 151-157.
13. **Muñoz-Sabater, J., et al. (2021)**. ERA5-Land: A state-of-the-art global reanalysis dataset for land applications. *Earth System Science Data*, 13(9), 4349-4383.
14. **IEC 61724-1:2021**. *Photovoltaic system performance monitoring - Guidelines for measurement, data exchange and analysis*. International Electrotechnical Commission.
15. **Dierauf, T., et al. (2013)**. *Weather-Corrected Performance Ratio*. National Renewable Energy Laboratory (NREL) Technical Report, NREL/TP-5200-57991.
16. **Department of Climate Change, Energy, the Environment and Water (DCCEEW, 2022-2025)**. *National Greenhouse Accounts Factors: Australian National Greenhouse Gas Inventory*. Australian Government, Canberra.
17. **Australian Energy Market Operator (AEMO, 2022)**. *National Electricity Market (NEM) Overview and Market Settlement Framework*. Melbourne, Australia.
18. **Deline, C., et al. (2019)**. *Impact of Inverter Loading Ratio on Solar PV System Performance and Degradation*. NREL Conference Paper, NREL/CP-5K00-73892.
19. **Kimber, A., et al. (2006)**. The effect of soiling on large grid-connected photovoltaic systems in California and the Southwest Region. *IEEE 4th World Conference on Photovoltaic Energy Conversion*, pp. 2391-2395.
20. **Standards Australia (2020)**. *AS/NZS 4777.2:2020: Grid connection of energy systems via inverters, Part 2: Inverter requirements*. Sydney, Australia.
21. **ISO 13374-1:2003**. *Condition monitoring and diagnostics of machines - Data processing, communication and presentation*. International Organization for Standardization.
