# Tổng hợp Chuyên sâu: Kỹ thuật Quang điện (PV), Hệ thống Áp mái, Biến tần và Đặc thù Khí hậu Bang Victoria (Úc)

> **Tài liệu Phục vụ:** Báo cáo Tốt nghiệp, Bảo vệ Đề tài (Defense), và Diễn giải Insight Nghiệp vụ cho Dự án 42 Trạm Điện Mặt trời Đại học La Trobe.  
> **Tác giả:** Nhóm *The Outliers* (Chuyên ngành Xử lý Dữ liệu — Cao đẳng FPT Polytechnic).  
> **Ngày phát hành:** 16/08/2026.  
> **Liên kết Dữ liệu Dự án:** `data/mlmart_base/v4_final_cleaned.parquet`, `reports/DATN_REPORT_FINAL_01.tex`.

---

## 1. Khung Tiêu chuẩn và Nguồn Tài liệu Kỹ thuật Uy tín

Để đảm bảo toàn bộ các nhận định, tính toán và đề xuất trong dự án đều đạt chuẩn kỹ thuật quốc tế và phù hợp với quy định sở tại của Úc, nhóm tổng hợp từ 6 nguồn tài liệu quy chuẩn hàng đầu:

| Tổ chức / Cơ quan | Văn bản / Tiêu chuẩn Quy chiếu | Trọng tâm Áp dụng trong Dự án |
|---|---|---|
| **Clean Energy Council (CEC) Australia** | *CEC Installation & Grid Connect Guidelines* | Quy định góc nghiêng tối thiểu $\ge 10^\circ$, tỷ lệ quá tải Inverter tối đa $133\%$, tiêu chuẩn an toàn đấu nối. |
| **Standards Australia** | **AS/NZS 5033:2021** (Installation of PV arrays) <br> **AS/NZS 4777.2:2020** (Inverter grid connection) | Khoảng cách lưu thông gió mái tôn $\ge 100-150\,\text{mm}$, bảo vệ chống dòng rò DC, ngắt mạch khẩn cấp. |
| **Bureau of Meteorology (BOM) Australia** | *Solar Exposure Climate Data (MJ/m²)* | Dữ liệu chuẩn bức xạ mặt trời theo giờ, nhiệt độ cực đoan và chỉ số mây tại bang Victoria (Melbourne, Bendigo, Wodonga). |
| **IEA-PVPS Task 13** | *IEA-PVPS T13-15:2023 Technical Report* | Mô hình phân rã tổn thất quang điện, tỷ lệ hư hỏng biến tần (MTBF), và hệ số suy thoái cell pin theo năm. |
| **NREL & Sandia Labs** | *System Advisor Model (SAM) & PVWatts* | Mô hình nhiệt độ tế bào quang điện (King / Sandia Model), công thức tính chỉ số hiệu suất PR, CF. |
| **CSIRO & ARENA** | *Australian Solar Energy Performance Study* | Nghiên cứu tác động của bụi mịn sol khí cháy rừng (Bushfire smoke) và bão bụi sa mạc đến hiệu suất PV tại Úc. |

---

## 2. Kỹ thuật Lắp đặt Tấm pin Mặt trời Áp mái (Rooftop PV Systems)

### 2.1. Góc Nghiêng (Tilt Angle) và Cơ chế Tự làm sạch (Self-Cleaning)
* **Góc tối ưu theo vĩ độ:**
  * Bang Victoria nằm trong khoảng vĩ độ $34^\circ\text{S} - 38^\circ\text{S}$ (Bán cầu Nam). Theo lý thuyết thiên văn học, góc nghiêng lý tưởng để thu được năng lượng cực đại quanh năm là bằng vĩ độ địa phương ($\approx 35^\circ$).
* **Thực tế lắp đặt áp mái thương mại (Commercial Rooftops):**
  * Trên các tòa nhà giảng đường, thư viện của Đại học La Trobe, đa phần mái là dạng mái bằng hoặc mái tôn dốc nhẹ ($5^\circ - 15^\circ$).
  * **Quy chuẩn CEC $\ge 10^\circ$:** Theo khuyến nghị của *Clean Energy Council*, góc nghiêng tối thiểu phải đạt $10^\circ$. Ở góc này, nước mưa mới tạo ra dòng chảy đủ mạnh để cuốn trôi bụi bẩn, phân chim và lá cây bám dính. Nếu lắp phẳng dưới $10^\circ$, cặn bẩn sẽ đọng lại ở viền khung dưới của tấm pin, tạo ra hiện tượng che bóng cục bộ (Soiling Shading), lâu dài sinh ra điểm nóng (Hot-spots) phá hủy tế bào bán dẫn.
* **Tối ưu Tải trọng Gió & Mật độ Công suất:**
  * Lắp ở góc dốc thấp ($10^\circ - 15^\circ$) giúp giảm lực cản gió giật (Wind Lift Force) trong các cơn bão mùa đông tại Melbourne, đồng thời giảm khoảng cách giữa các hàng tấm pin (Inter-row Spacing) mà không bị đổ bóng che nhau, giúp tăng tổng công suất lắp đặt trên một mét vuông mái.

```
                  Ánh sáng mặt trời (Bán cầu Nam: chiếu từ phía BẮC)
                         \    \    \
                          \    \    \
               ┌───────────\────\────\───┐ 
               │    Tấm Pin Quang Điện   │
               │   (Nghiêng 10° - 15°)   │
               └───────────┬─────────────┘
                           │ 
      ═════════════════════╪════════════════════════════ Mái tôn Colorbond
             │ ◄── Khoảng hở gió ≥ 100-150mm ──► │
```

### 2.2. Hướng La bàn (Azimuth Orientation)
* **Hướng Bắc Thực (True North - $0^\circ$ Azimuth):**
  * Ở bán cầu Nam, mặt trời di chuyển trên bầu trời phía Bắc. Hướng Bắc đón trọn vẹn bức xạ trực xạ ($DNI$) vào giữa trưa, tạo ra sản lượng tổng năm cao nhất.
* **Hướng Đông ($90^\circ$) và Hướng Tây ($270^\circ$) — Thiết kế Đông - Tây (Dual-pitch):**
  * Tại các khuôn viên trường đại học, phụ tải điện sinh hoạt và nghiên cứu (máy lạnh, máy chủ, đèn chiếu sáng giảng đường) tăng cao từ $08:30$ sáng đến $17:00$ chiều.
  * Việc bố trí tấm pin hướng Đông giúp đón nắng sớm từ 07:00–10:00; hướng Tây đón nắng chiều 14:00–17:00.
  * Mặc dù tổng sản lượng năm giảm khoảng $10-12\%$ so với hướng Bắc, nhưng đồ thị phát điện có dạng hình vòm rộng (Broad Peak), trùng khớp hoàn hảo với biểu đồ tiêu thụ điện thực tế của khuôn viên, giảm tỷ lệ phát điện thừa phải bán rẻ lên lưới.

### 2.3. Cấu trúc Mái Tôn Công nghiệp (Colorbond) và Tản nhiệt Tự nhiên
* **Hấp thụ nhiệt của mái tôn:**
  * Mái tôn kim loại của các tòa nhà thương mại tại Úc có thể nóng lên tới $65-75^\circ\text{C}$ vào các ngày hè nắng gắt. Nhiệt lượng này bức xạ ngược lên mặt sau của tấm pin.
* **Khoảng cách lưu thông không khí (Ventilation Gap):**
  * Theo tiêu chuẩn **AS/NZS 5033**, hệ thống áp mái phải có giá đỡ tạo khoảng cách hở tối thiểu từ $100\,\text{mm}$ đến $150\,\text{mm}$ so với mặt mái tôn.
  * Luồng không khí đối lưu tự nhiên đi qua khe hở này giúp hạ nhiệt độ tế bào quang điện từ $5^\circ\text{C}$ đến $10^\circ\text{C}$, cứu vãn từ $2\%$ đến $4\%$ sản lượng điện không bị suy hao do nhiệt.

---

## 3. Kỹ thuật Biến tần (Inverter) & Hiện tượng Cắt ngọn (Clipping)

### 3.1. Phân loại Cấu trúc Biến tần trong Dự án
Dữ liệu từ 42 trạm tại 5 khuôn viên La Trobe thể hiện sự đa dạng về chủng loại biến tần:

1. **Biến tần Chuỗi (String Inverters - 10 kW đến 50 kW):**
   * Phổ biến nhất trong các hệ thống thương mại (như SMA Sunny Tripower, Fronius Symo, Sungrow).
   * Ưu điểm: Hiệu suất chuyển đổi cao ($98-98{,}6\%$), chi phí đầu tư trên mỗi kWp thấp, dễ bảo trì thay thế.
   * Nhược điểm: Nếu một tấm pin trong chuỗi bị che bóng hoặc hỏng diode, toàn bộ chuỗi nối tiếp bị giảm dòng theo tấm yếu nhất (Hiệu ứng cổ chai - Bottleneck Effect).
2. **Hệ thống có Bộ tối ưu hóa DC (DC Optimizers - SolarEdge):**
   * Trang bị trên một số trạm có cấu trúc mái phức tạp. Mỗi tấm pin được gắn 1 mạch MPPT riêng trước khi gom về biến tần trung tâm, giúp triệt tiêu hoàn toàn tổn thất do che bóng lệch hướng.

```
[String 1: Pin 1]──[Pin 2]──...──[Pin N] ──┐
                                           ├──► [ Inverter Chuỗi (MPPT) ] ──► [ Lưới AC ]
[String 2: Pin 1]──[Pin 2]──...──[Pin N] ──┘
```

### 3.2. Tỷ lệ Quá tải DC/AC (DC-to-AC Ratio / Inverter Loading Ratio - ILR)
* **Quy chuẩn Úc (CEC Rule):** Cho phép tỷ lệ lắp đặt công suất danh định giàn pin ($P_{\text{DC}}$) vượt công suất định mức biến tần ($P_{\text{AC}}$) lên tới **$133\%$** (ILR = $1{,}33$).
* **Lý do kinh tế kỹ thuật:**
  * Giàn pin rất hiếm khi phát đạt $100\%$ công suất STC do tổn thất nhiệt, bụi bẩn, góc chiếu nghiêng.
  * Lắp quá tải $120-130\%$ giúp biến tần hoạt động ở dải công suất tối ưu ($70-100\%$) trong phần lớn thời gian ban ngày (sáng sớm và chiều muộn), tối đa hóa tổng sản lượng kWh sinh ra trong ngày.
* **Hiện tượng Cắt ngọn Biến tần (Inverter Clipping):**
  * Vào những ngày hè hoặc ngày xuân trời trong, khi bức xạ trực xạ đạt đỉnh ($GHI > 900\,\text{W/m}^2$) và nhiệt độ mát mẻ, công suất DC tạo ra vượt quá công suất biến tần cho phép ($P_{\text{DC}} > P_{\text{AC, max}}$).
  * Biến tần tự động điều chỉnh điểm làm việc MPPT dịch khỏi điểm cực đại để giới hạn công suất đầu ra đúng bằng công suất danh định $P_{\text{AC}}$.
  * **Biểu hiện trên dữ liệu:** Đồ thị sản lượng bị san phẳng ở đỉnh (Flat-top curve). Đây là **hành vi vận hành có chủ đích**, không phải lỗi thiết bị.

```
 Công suất (kW)
     ^
     │                 / \  ◄── Sản lượng DC tiềm năng (nếu Inverter vô hạn)
 P_ac│┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┌───┐┈┈┈┈ ◄── CẮT NGỌN BIẾN TẦN (INVERTER CLIPPING)
     │               /     \
     │              /       \
     │             /         \
     └────────────┴───────────┴────► Thời gian trong ngày (06:00 - 18:00)
```

### 3.3. Suy giảm Công suất do Quá nhiệt Biến tần (Inverter Thermal Derating)
* **Cơ chế tự bảo vệ:** Các linh kiện bán dẫn công suất (IGBT, tụ điện điện phân) bên trong biến tần có giới hạn nhiệt độ chịu đựng (thường là $85^\circ\text{C}$).
* **Hành vi suy thoái:**
  * Khi nhiệt độ môi trường ngoài trời vượt quá $40-45^\circ\text{C}$ (rất phổ biến tại Bendigo, Mildura mùa hè) hoặc biến tần lắp đặt ở vị trí bị ánh nắng chiếu trực tiếp, quạt tản nhiệt không đủ làm mát heatsink.
  * Vi xử lý của biến tần sẽ chủ động cắt giảm công suất đầu ra từ $10\%$ đến $40\%$ (Thermal Derating) để giữ nhiệt độ bo mạch an toàn.
  * **Insight bảo trì:** Cần lắp đặt mái che nắng chuyên dụng (Inverter Sunshade) và bảo dưỡng quạt làm mát định kỳ trước mùa hè.

### 3.4. Dòng Rò và Trôi Điểm Không Ban đêm (Nighttime Tare Loss & Sensor Drift)
* **Tiêu thụ điện tự dùng ban đêm (Tare Loss):** Khi trời tối ($GHI = 0$), mạch điều khiển vi xử lý, module truyền thông RS-485/WiFi và màn hình của biến tần tiêu thụ lượng điện nhỏ từ $2\,\text{W}$ đến $10\,\text{W}$.
* **Hiện tượng Trôi điểm 0 (Sensor Zero-Drift):**
  * Các cảm biến đo dòng hiệu ứng Hall (CT Sensors) tại tủ điện có thể bị trôi điểm cân bằng do biến thiên nhiệt độ đêm - ngày.
  * Điều này tạo ra các bản ghi vi phát điện giả mạo ($0{,}001 - 0{,}03\,\text{kWh}$) vào lúc $01:00-03:00$ sáng trong dữ liệu thô.
  * **Ứng dụng trong dự án:** Tầng ETL và rào chắn vật lý đã tự động nhận diện và gán mã `night_leakage` hoặc reset về $0\,\text{kWh}$, làm sạch triệt để trước khi nạp vào Kho Dữ liệu.

---

## 4. Đặc thù Thời tiết & Khí hậu Bang Victoria (Úc)

### 4.1. Tổng quan Khí hậu và Phân bố Địa lý 5 Khuôn viên Đại học La Trobe

Bang Victoria có diện tích $227.444\,\text{km}^2$, trải dài qua nhiều vùng khí hậu khác nhau theo phân loại Köppen:

```
                      MILDURA (Bắc - Bán khô hạn, BSh/BWh)
                         │  • Bức xạ: 5.8 kWh/m²/ngày
                         │  • Mùa hè cực nóng (>42°C)
                         ▼
                   SHEPPARTON (Trung Bắc - Cfa)
                         │
                   BENDIGO (Trung tâm - Cfb)
                         │  • Bức xạ: 5.2 kWh/m²/ngày
                         ▼
        ALBURY-WODONGA (Đông Bắc - Cfa)
        • Thung lũng sông Murray, sương mù mùa đông
                         ▼
      BUNDOORA / MELBOURNE (Phía Nam - Cfb - Ôn đới Hải dương)
      • Thời tiết "4 mùa trong 1 ngày", mây đối lưu ven biển
```

| Khuôn viên (Campus) | Tọa độ Địa lý | Đặc trưng Khí hậu | Bức xạ Trung bình Ngày (BOM) | Nhiệt độ Cực đại Mùa hè |
|---|---|---|---|---|
| **Bundoora (Melbourne)** | $37{,}72^\circ\text{S},\, 145{,}05^\circ\text{E}$ | Ôn đới hải dương ($Cfb$), gió biển vịnh Port Phillip, mây đối lưu thay đổi nhanh. | $4{,}2 - 4{,}6\,\text{kWh/m}^2$ | $40 - 43^\circ\text{C}$ |
| **Bendigo** | $36{,}76^\circ\text{S},\, 144{,}28^\circ\text{E}$ | Ôn đới lục địa chuyển tiếp ($Cfb$), ít mây, số giờ nắng cao. | $4{,}9 - 5{,}3\,\text{kWh/m}^2$ | $42 - 44^\circ\text{C}$ |
| **Albury-Wodonga** | $36{,}12^\circ\text{S},\, 146{,}93^\circ\text{E}$ | Cận nhiệt đới ẩm ($Cfa$), thung lũng sông Murray, mùa đông sương mù dày. | $4{,}8 - 5{,}1\,\text{kWh/m}^2$ | $41 - 43^\circ\text{C}$ |
| **Shepparton** | $36{,}38^\circ\text{S},\, 145{,}40^\circ\text{E}$ | Khí hậu đồng bằng Goulburn Valley, nắng gắt, khô ráo. | $5{,}1 - 5{,}4\,\text{kWh/m}^2$ | $43 - 45^\circ\text{C}$ |
| **Mildura** | $34{,}21^\circ\text{S},\, 142{,}15^\circ\text{E}$ | Bán khô hạn vùng Sunraysia ($BSh$), bức xạ quang điện dồi dào nhất bang. | $5{,}5 - 5{,}8\,\text{kWh/m}^2$ | $44 - 47^\circ\text{C}$ |

### 4.2. Hiện tượng Đợt Nắng Nóng Mùa Hè (Summer Heatwaves) và Tổn thất Nhiệt
* **Đặc điểm khí tượng:** Vào tháng 12 đến tháng 2 hàng năm, gió bắc thổi từ vùng sa mạc trung tâm nước Úc tràn xuống bang Victoria, tạo ra các đợt nắng nóng kéo dài $3-5$ ngày với nhiệt độ không khí $T_{\text{amb}} \ge 38-44^\circ\text{C}$.
* **Cơ chế suy giảm công suất tế bào pin (Thermal Loss):**
  * Nhiệt độ cell pin được ước lượng theo mô hình NOCT (King et al.):
    \begin{equation}
        T_{\text{cell}} = T_{\text{amb}} + \left(\frac{\text{NOCT} - 20^\circ\text{C}}{800}\right) \times GHI
    \end{equation}
  * Với $T_{\text{amb}} = 40^\circ\text{C}$ và $GHI = 1000\,\text{W/m}^2$, nhiệt độ cell pin vọt lên **$68^\circ\text{C} - 72^\circ\text{C}$**!
  * Độ chênh nhiệt so với điều kiện chuẩn ($25^\circ\text{C}$) là $\Delta T = 45^\circ\text{C}$.
  * Với hệ số nhiệt độ công suất điển hình $\gamma = -0{,}38\%/^\circ\text{C}$, mức suy hao công suất thuần do nhiệt là:
    \begin{equation}
        P_{\text{loss, temp}} = |\gamma| \times \Delta T = 0{,}38\% \times 45 = \mathbf{17{,}1\%}!
    \end{equation}
  * **Insight quan trọng:** Giữa trưa nắng chang chang mùa hè, sản lượng điện thực tế bị sụt giảm gần $1/5$ công suất thiết kế. Đây là quy luật vật lý bán dẫn tự nhiên, giúp ban quản lý hiểu rằng PR giảm không phải do tấm pin bị hỏng.

### 4.3. Đám mây Đối lưu và Tốc độ Biến thiên Nhanh (Convective Cloud Ramping)
* Tại khu vực Melbourne / Bundoora, gió biển mang hơi ẩm gặp nhiệt độ đất liền tạo ra các đám mây tích đối lưu (Cumulus clouds) di chuyển với tốc độ $40-60\,\text{km/h}$.
* Bức xạ mặt trời có thể giảm từ $950\,\text{W/m}^2$ xuống $150\,\text{W/m}^2$ chỉ trong vòng $30-60$ giây.
* Mức độ biến thiên cực nhanh này đặt ra yêu cầu khắt khe cho thuật toán bám điểm công suất cực đại (MPPT) của biến tần và chứng minh sự cần thiết của mô hình dự báo ngắn hạn $15$ phút ($H=1$) của dự án để đơn vị vận hành lưới điện chủ động ứng phó.

### 4.4. Bụi Mịn Cháy Rừng (Bushfire Smoke Aerosols) và Bão Bụi Sa Mạc
* **Sự kiện Mùa hè Đen (Black Summer Bushfires 2019–2020):**
  * Đầu năm 2020 (trùng với giai đoạn bắt đầu của bộ dữ liệu UNISOLAR), các vụ cháy rừng lịch sử tại miền đông nước Úc phát tán hàng triệu tấn bụi mịn PM2.5 vào bầu khí quyển.
  * **Tác động quang học:** Độ dày quang học sol khí (Aerosol Optical Depth - AOD) tăng vọt từ $0{,}08$ lên $>1{,}5$. Bức xạ trực xạ ($DNI$) bị tán xạ mạnh, làm tỷ lệ bức xạ khuếch tán ($DHI / GHI$) tăng từ mức thông thường $15\%$ lên hơn **$70\%$**.
  * Dù trời trông vẫn sáng nhưng sản lượng quang điện bị sụt giảm $20-35\%$ do tế bào pin silicon chỉ hấp thụ hiệu quả các tia sáng trực xạ thẳng góc.
* **Lắng đọng tro bụi (Ash Soiling):** Lớp tro bụi mỏng phủ trên mặt kính làm giảm độ truyền quang ($2-5\%$), đòi hỏi chu kỳ xịt rửa tấm pin tăng cường sau mùa cháy rừng.

---

## 5. Bảng Tổng hợp Mối Liên hệ: Lý thuyết Kỹ thuật $\rightarrow$ Insight Dự án

| Hiện tượng Kỹ thuật / Khí tượng | Biểu hiện trong Dữ liệu Dự án | Mã Dị thường / Phân tích Liên quan | Khuyến nghị Vận hành & Quyết định (Actionable Insights) |
|---|---|---|---|
| **Nhiệt độ cell pin $>65^\circ\text{C}$ ngày hè** | Sản lượng thực tế thấp hơn lý thuyết $15-20\%$ dù trời không mây. | Nhóm tổn thất `Thermal Loss` trên Dashboard Loss & Efficiency. | Thiết kế bổ sung khoảng hở thông gió mái tôn $\ge 150\,\text{mm}$; xem xét phủ sơn phản nhiệt trên mái nhà. |
| **Tỷ lệ DC/AC $>1{,}25$ trưa nắng** | Sản lượng phát điện bị cắt phẳng đỉnh tại công suất danh định $P_{\text{stc}}$. | `inverter_clipping` | Giữ nguyên cấu hình vì đây là tối ưu kinh tế; không cần thay thế biến tần lớn hơn. |
| **Biến tần quá nhiệt $>50^\circ\text{C}$ ngoài trời** | Công suất trạm sụt giảm đột ngột $30-50\%$ giữa trưa tại Mildura/Bendigo. | `inverter_thermal_derating` | Lắp đặt tấm chắn nắng trực tiếp (Sunshield) cho cụm biến tần ngoài trời; vệ sinh lưới tản nhiệt định kỳ. |
| **Bụi bẩn bám dính lâu ngày (Soiling)** | Hệ số PR suy giảm từ từ theo thời gian ($82\% \rightarrow 71\%$) sau $3$ tháng không mưa. | Phân tích xu hướng suy giảm PR trạm (Degradation Trend). | Lập lịch rửa pin tự động sau mỗi 45 ngày khô hạn; đảm bảo góc nghiêng $\ge 10^\circ$ để tự rửa trôi khi mưa. |
| **Hỏng diode chuỗi pin (String Fault)** | Sản lượng trạm giảm đúng $33\%$ hoặc $50\%$ so với trạm đối chứng cùng khuôn viên. | `gmm_if_outlier_flag = 1` (Mã `underperformance_anomaly`) | Điều động kỹ sư hiện trường dùng camera nhiệt hồng ngoại quét vị trí chuỗi pin lỗi để thay thế diode. |
| **Nhiễu cảm biến dòng điện đêm** | Xuất hiện giá trị sản lượng $0{,}005 - 0{,}02\,\text{kWh}$ lúc $02:00$ sáng ($GHI = 0$). | `night_leakage` / `zero_drift` | Tầng ETL tự động ép về $0$; lên kế hoạch hiệu chuẩn (Calibration) bộ biến dòng CT tại tủ phân phối. |
| **Khói bụi cháy rừng / Mây đối lưu** | Tỷ lệ bức xạ tán xạ $DHI/GHI > 0{,}75$, sai số dự báo Baseline truyền thống tăng cao. | Đặc trưng `diffuse_ratio` & `temp_x_shortwave` trong mô hình LightGBM. | Sử dụng mô hình Machine Learning LightGBM tích hợp biến khí tượng thời gian thực thay vì mô hình chuỗi thời gian đơn biến. |

---

## 6. Tài liệu Tham khảo Kỹ thuật Chính (References)

1. **Clean Energy Council (2021)**, *Grid-Connected Solar PV Systems (No Battery Storage) Design and Installation Guidelines*, Melbourne, Australia.
2. **Standards Australia (2021)**, *AS/NZS 5033:2021 — Installation and safety requirements for photovoltaic (PV) arrays*, SAI Global.
3. **Standards Australia (2020)**, *AS/NZS 4777.2:2020 — Grid connection of energy systems via inverters*, SAI Global.
4. **Bureau of Meteorology — BOM (2024)**, *Climate and Solar Radiation Data Services for Victoria*, Commonwealth of Australia. \url{http://www.bom.gov.au/climate/averages/solar/}
5. **Wimalaratne, S., et al. (2022)**, *UNISOLAR: An Open Dataset of Photovoltaic Solar Energy Generation in a Large Multi-Campus University Setting*, IEEE HSI 2022.
6. **IEA-PVPS Task 13 (2023)**, *Designing for Reliability: Technical Report IEA-PVPS T13-15:2023*, International Energy Agency.
7. **King, D. L., Boyson, W. E., & Kratochvil, J. A. (2004)**, *Photovoltaic Array Performance Model*, Sandia National Laboratories, SAND2004-3535.
8. **CSIRO (2020)**, *Impacts of the 2019-20 Bushfires on Australian Solar Energy Generation and Air Quality*, CSIRO Energy Centre, Newcastle, Australia.
