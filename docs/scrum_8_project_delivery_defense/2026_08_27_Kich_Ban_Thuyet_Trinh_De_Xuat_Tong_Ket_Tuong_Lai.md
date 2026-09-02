# KỊCH BẢN THUYẾT TRÌNH BẢO VỆ ĐỒ ÁN TỐT NGHIỆP: ĐỀ XUẤT CHIẾN LƯỢC, TỔNG KẾT & ĐỊNH HƯỚNG TƯƠNG LAI

> **Chuyên ngành:** Xử lý Dữ liệu (Data Analytics) — FPT Polytechnic  
> **Đề tài:** Hệ thống Xử lý Dữ liệu, Nhận diện Dị thường Vận hành và Phân tích Hiệu quả Cho 42 Trạm Điện Mặt Trời Áp Mái Đại Học La Trobe (Úc)  
> **Nhóm thực hiện:** The Outliers  
> **Người trình bày phần kết:** Sinh viên phụ trách Đề xuất Giải pháp, Tổng kết Dự án & Định hướng Tương lai  
> **Phong cách trình bày:** Gần gũi, tự nhiên, mạch lạc, dễ hiểu với Hội đồng chuyên ngành Công nghệ thông tin / Dữ liệu; giữ sự trang trọng, lễ phép của một buổi bảo vệ tốt nghiệp chính thức; tránh sa đà vào các thuật ngữ điện quá nặng.  
> **Thời lượng mục tiêu:** **8 - 10 phút**

---

## BẢNG PHÂN BỔ THỜI LƯỢNG THUYẾT TRÌNH (TIMELINE MANAGEMENT)

| Slide | Nội Dung Trọng Tâm | Hình Thức Trình Bày | Thời Lượng | Mốc Thời Gian |
| :--- | :--- | :--- | :---: | :---: |
| **Slide 1** | **Khái Quát Chặng Đường & 5 Vấn Đề Cốt Lõi (Pain Points)** | Slide tổng hợp vấn đề thực tế | `01:45` | `00:00 - 01:45` |
| **Slide 2** | **Ma Trận 5 Giải Pháp (Hạ Tầng vs Vận Hành)** | Slide cấu trúc giải pháp đối ứng | `01:15` | `01:45 - 03:00` |
| **Slide 3** | **Chi Tiết Giải Pháp, 6 Mã Cờ CBM & Demo Streamlit** | **Thao tác Demo trực tiếp Streamlit** | `03:30` | `03:00 - 06:30` |
| **Slide 4** | **Kết Luận: Giá Trị Dự Án, Thuận Lợi & Khó Khăn** | Slide tổng kết giá trị & bài học | `01:30` | `06:30 - 08:00` |
| **Slide 5** | **Định Hướng Phát Triển Tương Lai & Mời Hội Đồng Q&A** | Slide 3 giai đoạn mở rộng & Chào kết | `01:30` | `08:00 - 09:30` |
| **TỔNG** | **Toàn Bộ Phần Thuyết Trình** | **Đầy đủ, mạch lạc, kiểm soát giờ tốt** | **~09:30** | **< 10 phút** |

---

## SLIDE 1: KHÁI QUÁT CHẶNG ĐƯỜNG ĐÃ QUA & 5 VẤN ĐỀ VẬN HÀNH CỐT LÕI

### Thông tin Slide & Bố cục Trình chiếu (Slide Layout)
* **Thời lượng mục tiêu:** `01:45` (Mốc: `00:00 - 01:45`)
* **Tone giọng:** Điềm đạm, tự tin, mang tinh thần của một Data Analyst phân tích số liệu thực tế.
* **Nội dung hiển thị trên slide:**
  * *Tóm tắt hành trình nhóm đã qua:* 2,73 triệu dòng dữ liệu $\rightarrow$ Pipeline làm sạch 6 lớp $\rightarrow$ Phát hiện dị thường GMM-IF $\rightarrow$ Dashboard Tableau trực quan $\rightarrow$ Mô hình Machine Learning LightGBM dự báo sản lượng (tốt hơn baseline Prophet $50{,}09\%$ và $37{,}80\%$).
  * *5 Vấn đề vận hành cốt lõi (Pain Points) tìm ra từ dữ liệu:*
    1. **Nắng to nhưng bị nghẽn công suất giữa trưa (Cắt ngọn Inverter):** Thất thoát **$79.298\,\text{kWh/năm}$**.
    2. **Tấm pin bị nung quá nóng vào mùa hè (Mất $14{,}8\%$ sản lượng):** Thất thoát **$510.268\,\text{kWh/năm}$** ($>102.000\,\text{AUD/năm}$).
    3. **Cụm 970 kWp mái bằng bị hụt nắng mùa đông và đọng bùn viền đáy:** Thất thoát **$71.850\,\text{kWh/năm}$**.
    4. **Bảo trì bị động, phát hiện hư hỏng chậm (mất 2-4 tuần):** Thất thoát **$70.330\,\text{kWh/năm}$**.
    5. **Bụi bám mùa khô và tốn tiền rửa pin không cần thiết:** Mất **$62.060\,\text{kWh/năm}$** và lãng phí nhân công trước các đợt mưa.

---

### Kịch Bản Lời Thoại (Spoken Script)

> `[00:00]` *(Mỉm cười tự tin, hướng mắt về phía Hội đồng, cúi đầu chào lịch sự)*  
> "Kính thưa Quý Thầy/Cô trong Hội đồng Ban Giám khảo!  
> 
> Vừa rồi, các bạn trong nhóm The Outliers đã lần lượt trình bày chặng đường kỹ thuật của đề tài: Từ việc thu thập và làm sạch khối dữ liệu thực tế hơn **2,7 triệu dòng** qua **Pipeline 6 lớp**, ứng dụng mô hình học máy **GMM--Isolation Forest** để nhận diện dị thường, xây dựng hệ thống báo cáo trên **Tableau**, cho tới mô hình **LightGBM dự báo sản lượng điện** đạt độ chính xác cao hơn Prophet tới **50%** ở tầm cực ngắn và **37%** ở tầm một giờ.
> 
> `[00:40]` *(Giọng nói nhấn nhá, chuyển hướng nhìn sang slide Pain Points)*  
> Đứng ở góc độ người làm Phân tích Dữ liệu, nhóm chúng em luôn tâm niệm: **Mục tiêu cuối cùng của dữ liệu không phải là tạo ra những biểu đồ đẹp mắt hay khoe điểm mô hình cao, mà là dữ liệu giúp nhà trường nhìn ra vấn đề gì và giải quyết được bài toán thực tế nào?**
> 
> Khi đi sâu vào phân tích hành vi phát điện của 42 trạm quang điện tại Đại học La Trobe, dữ liệu đã chỉ cho nhóm thấy **5 vấn đề cốt lõi** khiến hệ thống bị thất thoát rất nhiều điện năng và tiền bạc:
> 
> `[01:05]` *(Chỉ vào từng vấn đề, diễn giải bằng hình tượng đời thường dễ hiểu)*  
> - **Vấn đề thứ nhất — Nắng to nhưng bị nghẽn công suất giữa trưa:** Vào các trưa hè nắng gắt nhất, mảng pin sinh ra lượng điện rất lớn nhưng bộ chuyển đổi điện không tải hết — giống như nước đổ vào một cái phễu quá nhỏ khiến nước tràn ra ngoài. Hiện tượng này khiến trường bị xén bỏ lãng phí gần **80.000 số điện mỗi năm**.
> - **Vấn đề thứ hai — Pin bị nung quá nóng vào mùa hè:** Do đa số các tấm pin được gắn sát rạt mặt mái tôn, không có khe hở cho gió lùa vào làm mát, bề mặt tấm pin bị hun nóng tới hơn 70°C. Càng nóng thì pin hoạt động càng kém, làm bốc hơi tới **14,8% sản lượng** — tương đương mất hơn **510.000 số điện** và hơn 100.000 đô la Úc mỗi năm!
> - **Vấn đề thứ ba — Cụm pin mái bằng bị hụt nắng đông và đọng bùn:** Các mái bằng lắp pin gần như nằm ngang. Mùa đông mặt trời chiếu nghiêng thì hụt ánh sáng; còn khi trời mưa thì nước không trôi hết mà đọng lại thành một dải bùn ở mép dưới tấm pin che khuất ánh sáng, làm mất gần **72.000 số điện mỗi năm**.
> - **Vấn đề thứ tư — Bảo trì bị động, phát hiện sự cố chậm:** Trước đây trường không có hệ thống cảnh báo tự động, kỹ sư phải đi tuần kiểm tra thủ công. Một trạm bị hỏng cầu chì hay nhảy cầu dao có khi 2 đến 4 tuần sau mới phát hiện ra, khiến lượng điện bị mất oan hơn **70.000 số điện**.
> - **Và vấn đề thứ năm — Bụi bẩn bám mùa khô và tốn tiền rửa pin thừa:** Bụi bám làm giảm hiệu suất, nhưng việc thuê người đi cọ rửa định kỳ cố định mà không theo dõi thời tiết lại gây lãng phí, có khi vừa rửa hôm trước thì hôm sau trời đổ mưa to."

---

## SLIDE 2: MA TRẬN 5 GIẢI PHÁP CHIẾN LƯỢC TOÀN DIỆN (HẠ TẦNG VS VẬN HÀNH)

### Thông tin Slide & Bố cục Trình chiếu (Slide Layout)
* **Thời lượng mục tiêu:** `01:15` (Mốc: `01:45 - 03:00`)
* **Tone giọng:** Chắc chắn, mạch lạc, làm nổi bật tư duy giải quyết vấn đề có hệ thống.
* **Nội dung hiển thị:** Ma trận 5 Giải pháp tương ứng chia thành 2 nhóm rõ ràng:
  * **Nhóm 1: Giải pháp về Hạ tầng & Vật lý kỹ thuật (3 Giải pháp):**
    1. *Hệ thống Pin lưu trữ BESS (1 MW / 2.5 MWh)* $\leftrightarrow$ Hấp thu lượng điện nghẽn giữa trưa hè.
    2. *Kê cao khe thông gió mái 10–15 cm* $\leftrightarrow$ Dùng gió tự nhiên làm mát pin.
    3. *Lắp khung nghiêng 15° cho cụm mái bằng* $\leftrightarrow$ Đón nắng đông và giúp nước mưa tự rửa trôi bùn bẩn.
  * **Nhóm 2: Giải pháp về Vận hành & Quy trình Dữ liệu (2 Giải pháp):**
    4. *Quy trình bảo trì dựa trên điều kiện (CBM)* $\leftrightarrow$ Dựa vào 6 mã cờ bất thường để sửa đúng chỗ, đúng lúc.
    5. *Lịch rửa pin thông minh theo dữ liệu mưa* $\leftrightarrow$ Chỉ rửa khi nắng hạn kéo dài, không rửa thừa.

---

### Kịch Bản Lời Thoại (Spoken Script)

> `[01:45]` *(Phong thái tự tin, chỉ tay vào slide tổng quan giải pháp)*  
> "Để giải quyết dứt điểm 5 vấn đề vừa nêu, nhóm The Outliers đề xuất **Ma trận 5 Giải pháp Chiến lược** tương ứng, được chia làm **2 nhóm chính**:
> 
> `[02:05]` *(Trình bày mạch lạc nhóm 1)*  
> - **Nhóm thứ nhất — Can thiệp về mặt Hạ tầng & Lắp đặt:** Gồm 3 giải pháp:  
>   (1) Lắp **Hệ thống pin lưu trữ BESS** để chứa lượng điện dư giữa trưa và tích trữ cho buổi tối;  
>   (2) Kê cao **Khe thông gió mái 10–15 cm** để gió tự nhiên luồn qua làm mát mặt sau tấm pin;  
>   (3) Dựng **Khung nghiêng 15° cho các mái bằng** để vừa đón nắng mùa đông, vừa tạo độ dốc cho nước mưa tự rửa trôi bụi bẩn.
> 
> `[02:30]` *(Trình bày mạch lạc nhóm 2)*  
> - **Nhóm thứ hai — Tối ưu hóa Vận hành nhờ Trí tuệ Dữ liệu:** Gồm 2 giải pháp khai thác trực tiếp kết quả phân tích của nhóm:  
>   (4) Chuyển sang **Quy trình bảo trì dựa trên điều kiện (CBM)** — sử dụng 6 mã cờ bất thường mà mô hình đã bóc tách để phát hiện và khoanh vùng sự cố ngay lập tức;  
>   (5) Xây dựng **Lịch rửa pin thông minh theo dữ liệu mưa** từ API thời tiết để tối ưu chi phí nhân công.
> 
> `[02:50]` *(Chuyển sang màn hình demo trực tiếp)*  
> Và để Thầy/Cô nhìn thấy rõ ràng cơ chế hoạt động cũng như các con số kinh tế thực tế của từng giải pháp, ngay sau đây em xin phép được **thao tác trực tiếp trên giao diện Mô phỏng What-If của ứng dụng Streamlit** do nhóm tự phát triển!"

---

## SLIDE 3: CHI TIẾT KỸ THUẬT, 6 MÃ CỜ CBM & DEMO TRỰC TIẾP STREAMLIT WHAT-IF

### Thông tin Slide & Bố cục Trình chiếu (Slide Layout)
* **Thời lượng mục tiêu:** `03:30` (Mốc: `03:00 - 06:30`)
* **Hình thức:** Chuyển sang tab trình duyệt Streamlit (`pages/2_What_If.py`), người thuyết trình vừa nói vừa click chuột bật các checkbox, chỉ vào các con số KPI và biểu đồ trên màn hình.
* **Nội dung trọng tâm:**
  1. *Giải thích cơ chế và số liệu từng hạng mục (BESS, Khe gió, Khung nghiêng, Lịch rửa mưa).*
  2. *ĐIỂM NHẤN ĐẶC BIỆT: Bóc tách thực tế 6 mã cờ dị thường trong quy trình CBM (Chứng minh dân Data giải quyết đúng bài toán nghiệp vụ, không phải làm toán vu vơ).*
  3. *Tổng kết kết quả khi áp dụng trọn vẹn 5 giải pháp cốt lõi.*

---

### Kịch Bản Lời Thoại (Spoken Script & Thao Tác Demo)

> `[03:00]` *(Mở tab Streamlit What-If Simulator, rê chuột vào các ô chọn)*  
> "Kính thưa Thầy/Cô, đây là giao diện **Mô phỏng Giả định What-If** trên Streamlit, kết nối trực tiếp với cơ sở dữ liệu để tính toán tức thời hiệu quả của từng phương án.
> 
> `[03:15]` *(Click chọn Checkbox 1: BESS — Card BESS sáng lên)*  
> - **Đầu tiên là Hệ thống pin lưu trữ BESS 1 MW / 2.5 MWh:** Thay vì để lượng điện dư thừa vào buổi trưa hè bị bỏ phí, pin BESS sẽ hứng trọn phần điện này, thu hồi được **gần 70.000 số điện sạch mỗi năm**. Lượng điện tích này sẽ được xả ra sử dụng vào khung giờ chiều tối khi sinh viên và giảng viên dùng nhiều điện và giá điện mua ngoài lưới đắt nhất. Riêng hạng mục này mang lại dòng tiền tiết kiệm **323.000 AUD mỗi năm** cho trường, hoàn vốn sau **3,87 năm**.
> 
> `[03:45]` *(Click chọn Checkbox 2: Khe gió mái tôn)*  
> - **Thứ hai là Khe thông gió mái 10–15 cm:** Chúng em đề xuất chêm thêm giá đỡ để nâng tấm pin cách mặt mái tôn ít nhất 15 cm. Gió trời sẽ luồn vào mặt sau làm mát tự nhiên, hạ nhiệt độ pin trung bình **8°C**. Nhờ pin mát hơn, hệ thống phát thêm được hơn **117.000 số điện mỗi năm**, tiết kiệm hơn **23.000 AUD** mà chi phí lắp đặt rất rẻ, hoàn vốn chỉ sau **12 tháng**!
> 
> `[04:10]` *(Click chọn Checkbox 3: Khung nghiêng 15° cho mái bằng)*  
> - **Thứ ba là Khung nghiêng 15° cho cụm 970 kWp mái bằng:** Đặt nghiêng 15° giúp tấm pin hứng vuông góc với ánh nắng mặt trời mùa đông, tăng ròng **53.000 số điện**. Đồng thời, khi trời mưa, nước mưa theo độ dốc 15° sẽ tự cuốn trôi sạch bùn đất đọng ở viền đáy tấm pin, thu hồi thêm **18.500 số điện** và đỡ tốn công người đi lau chùi. Tổng lợi ích đạt gần **15.000 AUD mỗi năm**, hoàn vốn sau **1,2 năm**.
> 
> `[04:35]` *(Click chọn Checkbox 4: Lịch rửa pin theo mưa)*  
> - **Thứ tư là Lịch rửa pin thông minh theo dữ liệu thời tiết:** Hệ thống dữ liệu tự động đếm số ngày khô hạn. Chỉ khi nào liên tục **từ 21 ngày trở lên không có mưa hoặc mưa quá nhỏ dưới 5 mm**, hệ thống mới đề xuất lệnh cho công nhân đi rửa pin. Nhờ đó lấy lại được **62.000 số điện**, đồng thời cắt bỏ hoàn toàn 3 đợt rửa thừa trước mùa mưa, tiết kiệm **6.000 AUD** tiền nhân công mà không tốn một đồng vốn đầu tư nào — mang lại hiệu quả tức thì!
> 
> `[05:00]` *(Click chọn Checkbox 5: Quy trình CBM — Dừng lại giải thích sâu sắc về 6 mã cờ)*  
> Và giải pháp thứ năm, cũng là giải pháp thể hiện rõ nhất giá trị của chuyên ngành Xử lý Dữ liệu chúng em: **Quy trình Bảo trì Dựa trên Điều kiện (CBM)**.
> 
> `[05:10]` *(Nhìn thẳng vào Hội đồng, giọng nói tự tin, gần gũi)*  
> Thưa Thầy/Cô, khi làm đề tài về phát hiện dị thường, có một câu hỏi rất tự nhiên là: **'Các em tìm ra Outliers xong thì để làm gì? Có giúp ích gì cho thực tế không hay chỉ là thuật toán phân cụm trên máy tính?'**  
> 
> Nhóm em xin khẳng định: **Chúng em không hề gán nhãn dị thường cho vui!**  
> Sáu mã cờ bất thường mà mô hình GMM--IF bóc tách chính là **6 'bệnh án kỹ thuật' cụ thể** phản ánh chính xác chuyện gì đang xảy ra ngoài hiện trường:
> 
> `[05:30]` *(Giải thích 6 mã cờ bằng ngôn ngữ đời thường, mạch lạc)*  
> 1. Mã cờ `LOW_ENERGY_STRONG_SUN`: Trời nắng chang chang giữa trưa mà sản lượng đột ngột rớt về 0 $\rightarrow$ Báo hiệu **nhảy cầu dao (Aptomat)** hoặc điện áp đường dây quá cao khiến thiết bị tự ngắt an toàn.
> 2. Mã cờ `ZERO_DAY_ANOMALY`: Ban ngày trời nắng đều mà cả ngày trạm không phát ra một số điện nào $\rightarrow$ Báo hiệu **cháy cầu chì chuỗi pin, đứt dây cáp hoặc hỏng bo mạch**.
> 3. Mã cờ `FLAT_TOP_CLIPPING`: Đồ thị phát điện bị xén bằng phẳng lì như bị chặt đầu $\rightarrow$ Báo hiệu **biến tần bị quá tải công suất**, chỉ đúng vị trí này cần lắp pin BESS để hứng điện thừa.
> 4. Mã cờ `NIGHT_GHOST_GENERATION`: Ban đêm trời tối om mà đồng hồ đo vẫn nhảy số phát điện $\rightarrow$ Báo hiệu **cảm biến đo dòng điện bị 'lú' (trôi điểm 0) hoặc bị nhiễu điện**, cần kỹ thuật viên đến cân chỉnh lại cảm biến.
> 5. Mã cờ `VOLTAGE_SPIKE_TRIP`: Điện áp nhảy vọt bất thường rồi sụt nguồn $\rightarrow$ Báo hiệu **mất cân bằng pha hoặc trạm biến áp của trường bị quá tải cục bộ**.
> 6. Và mã cờ `SENSOR_DRIFT_IRR`: Nắng vẫn to mà số điện phát cứ tụt dần đều theo ngày $\rightarrow$ Báo hiệu **mắt cảm biến đo bức xạ bị bụi bám mờ hoặc bị lệch chuẩn**.
> 
> `[06:05]` *(Nhấn mạnh giá trị của CBM)*  
> Nhờ có 6 mã cờ này, các kỹ sư của trường Đại học La Trobe không còn phải đi tuần tra mò mẫm từng trạm nữa. Nhìn vào màn hình là biết ngay trạm nào bị bệnh gì để mang đúng đồ nghề đến sửa. Thời gian phát hiện sự cố rút từ cả tháng xuống **dưới 1 giờ**, thời gian sửa chữa từ 2 tuần xuống **1 đến 3 ngày**, giúp thu hồi hơn **70.000 số điện**, mang lại **29.000 AUD mỗi năm** và hoàn vốn chỉ sau **chưa đầy 4 tháng**!
> 
> `[06:20]` *(Chỉ vào hàng thẻ KPI Tổng kết trên Streamlit khi cả 5 checkbox đều bật)*  
> Và đây là bức tranh tổng thể khi **áp dụng đồng bộ cả 5 giải pháp cốt lõi**:
> - **Sản lượng điện phát thêm ròng:** Đạt hơn **391.000 kWh/năm** (tăng thêm **+11,35%** sản lượng sạch).
> - **Hiệu suất vận hành PR toàn trường:** Tăng vọt từ $75,4\%$ lên **86,75%** (tăng $+11,35$ điểm phần trăm).
> - **Dòng tiền tiết kiệm hàng năm:** Đạt hơn **408.000 AUD mỗi năm** (tương đương hơn 6,5 tỷ đồng).
> - **Tổng vốn đầu tư CapEx:** Khoảng **1,3 triệu AUD** (trong đó pin BESS chiếm 1,25 triệu, còn 4 giải pháp kia chỉ tốn hơn 50.000 AUD).
> - **Thời gian hoàn vốn bình quân:** Toàn bộ dự án thu hồi vốn chỉ sau **3,18 năm**!"

---

## SLIDE 4: KẾT LUẬN — TỔNG KẾT GIÁ TRỊ DỰ ÁN, THUẬN LỢI VÀ KHÓ KHĂN

### Thông tin Slide & Bố cục Trình chiếu (Slide Layout)
* **Thời lượng mục tiêu:** `01:30` (Mốc: `06:30 - 08:00`)
* **Tone giọng:** Chân thành, đúc kết, khiêm tốn nhưng khẳng định được khối lượng công việc nhóm đã hoàn thành.
* **Nội dung hiển thị trên slide (Theo 2 cột chuẩn nội dung):**
  * **Cột trái — Tổng kết giá trị dự án:**
    - Pipeline **6 lớp** xử lý thành công **2,73 triệu dòng** dữ liệu thực tế.
    - Xác định và bóc tách các điểm dị thường giúp xóa bỏ các **điểm mù vận hành**.
    - Xây dựng các **Dashboard báo cáo** phù hợp với từng đối tượng người xem.
    - Xây dựng mô hình dự báo sản lượng điện với sai số thấp hơn **50,09% ($t+15$)** và **37,80% ($t+60$)** so với mô hình baseline.
    - Đưa ra các phương án giúp cải thiện hiệu suất của hệ thống điện mặt trời.
  * **Cột phải — Thuận lợi và khó khăn:**
    - *Thuận lợi:* Cơ sở dữ liệu 42 trạm quy mô lớn và đa dạng địa lý; Hệ thống tiêu chuẩn quốc tế hoàn thiện (IEC, AS/NZS, Sandia, CSIRO GenCost); Nền tảng công nghệ linh hoạt.
    - *Khó khăn:* Dữ liệu thực tế có nhiều khoảng trống và trôi cảm biến CT cần tiền xử lý phức tạp; Bài toán phối hợp liên ngành giữa Vật lý Quang điện và Khoa học Dữ liệu.

---

### Kịch Bản Lời Thoại (Spoken Script)

> `[06:30]` *(Chuyển sang Slide Kết Luận, ánh mắt ấm áp, giọng nói truyền cảm)*  
> "Kính thưa Hội đồng, nhìn lại toàn bộ quá trình thực hiện đồ án tốt nghiệp, nhóm The Outliers xin được tổng kết lại những giá trị dự án đạt được cũng như những bài học thực tế quý báu:
> 
> `[06:45]` *(Nhìn vào cột Tổng kết giá trị)*  
> **Về mặt giá trị đóng góp của dự án:**  
> - Nhóm đã xây dựng thành công **Pipeline 6 lớp hoàn chỉnh**, xử lý mượt mà hơn **2,7 triệu dòng dữ liệu** mà không để xảy ra lỗi rò rỉ dữ liệu tương lai.  
> - Các mô hình dữ liệu đã giúp **xóa bỏ hoàn toàn các điểm mù trong vận hành**, chuyển các con số khô khan thành nguyên nhân kỹ thuật có thể xử lý được.  
> - Xây dựng được hệ thống **Dashboard trực quan đa tầng**, phục vụ từ lãnh đạo theo dõi tài chính cho đến kỹ thuật viên điều hành hàng ngày.  
> - Phát triển **mô hình dự báo sản lượng LightGBM** giảm sai số từ 37% đến hơn 50% so với mô hình chuẩn Prophet.  
> - Và quan trọng nhất, đã đưa ra được **các phương án cải tiến có tính khả thi cao**, mang lại giá trị kinh tế hơn 400.000 AUD mỗi năm cho trường.
> 
> `[07:25]` *(Nhìn sang cột Thuận lợi và khó khăn)*  
> **Về thuận lợi và khó khăn trong quá trình làm đề tài:**  
> - *Về thuận lợi:* Nhóm may mắn được làm việc trên bộ dữ liệu thực tế rất lớn của 42 trạm tại Đại học La Trobe, cùng với hệ thống tài liệu và tiêu chuẩn quốc tế rất rõ ràng, giúp nhóm có cơ sở đối chiếu số liệu vững chắc.  
> - *Về khó khăn:* Dữ liệu thực tế không bao giờ sạch đẹp như bài tập mẫu trên lớp, dữ liệu bị đứt đoạn, mất kết nối và cảm biến bị đo sai ban đêm rất nhiều, đòi hỏi nhóm phải tìm hiểu kỹ thuật xử lý dữ liệu nhân quả khắt khe. Ngoài ra, việc kết hợp giữa kiến thức Xử lý Dữ liệu với kiến thức về năng lượng mặt trời là một thử thách liên ngành lớn, nhưng cũng là cơ hội để nhóm học hỏi được rất nhiều điều bổ ích."

---

## SLIDE 5: ĐỊNH HƯỚNG PHÁT TRIỂN TƯƠNG LAI & LỜI MỜI HỘI ĐỒNG ĐÁNH GIÁ

### Thông tin Slide & Bố cục Trình chiếu (Slide Layout)
* **Thời lượng mục tiêu:** `01:30` (Mốc: `08:00 - 09:30`)
* **Tone giọng:** Tươi sáng, nhiệt huyết, khiêm tốn và cầu thị.
* **Nội dung hiển thị trên slide (Lộ trình 3 giai đoạn & Việc gần nhất):**
  * **Lộ trình 3 Giai đoạn phát triển:**
    - *Giai đoạn 1 — Làm giàu dữ liệu ngoại cảnh:* Tích hợp API mã nguồn mở (miễn phí) về chất lượng không khí (AQI), chỉ số bụi mờ, sương mù $\rightarrow$ Giải quyết việc thiếu yếu tố ngoại cảnh làm bụi bẩn bám lên pin $\rightarrow$ Kết quả: Cải thiện độ chính xác dự báo mà không cần đầu tư thêm cảm biến vật lý.
    - *Giai đoạn 2 — Xây dựng nền tảng MLOps:* Thiết lập bộ điều phối và giám sát hiện tượng trôi dạt dữ liệu (Data Drift) $\rightarrow$ Giải quyết việc mô hình cũ dần theo mùa $\rightarrow$ Kết quả: Tự phát hiện dữ liệu bị lệch và tự động huấn luyện lại mô hình (Continuous Training).
    - *Giai đoạn 3 — Tích hợp cảnh báo & Báo cáo tự động:* Kết nối hệ thống dự báo với Zalo ZNS, Telegram Bot hoặc Email $\rightarrow$ Giải quyết việc người dùng phải chủ động mở Dashboard $\rightarrow$ Kết quả: Hệ thống tự động gửi báo cáo sản lượng hàng ngày hoặc cảnh báo thời tiết xấu thẳng đến điện thoại.
  * **Việc gần nhất, làm được ngay:** Hạ độ hạt thời tiết bằng ảnh vệ tinh — Đây là yếu tố ảnh hưởng trực tiếp nhất tới sai số, và cũng là thứ duy nhất có thể cải thiện ngay mà không cần đầu tư phần cứng.
  * **Giải thích khái niệm:** *Trôi dạt dữ liệu (Data Drift)* là hiện tượng dữ liệu thực tế dần khác lúc huấn luyện (ví dụ tấm pin cũ đi theo thời gian, thời tiết đổi mùa), khiến mô hình dự báo kém dần mà không báo lỗi.

---

### Kịch Bản Lời Thoại (Spoken Script)

> `[08:00]` *(Ánh mắt rạng rỡ, giọng nói đầy nhiệt huyết)*  
> "Kính thưa Hội đồng, để dự án có thể phát triển xa hơn nữa và ứng dụng vào thực tế thương mại, nhóm The Outliers đã vạch ra **Lộ trình phát triển 3 giai đoạn**:
> 
> `[08:15]` *(Trình bày ngắn gọn, súc tích 3 giai đoạn)*  
> - **Giai đoạn 1 — Làm giàu dữ liệu thời tiết:** Nhóm sẽ kết nối thêm các nguồn dữ liệu mở miễn phí về nồng độ bụi không khí và sương mù. Điều này giúp mô hình nhận biết được khi nào không khí ô nhiễm làm mờ tấm pin để điều chỉnh dự báo chính xác hơn mà không cần mua cảm biến đắt tiền.
> - **Giai đoạn 2 — Xây dựng nền tảng MLOps:** Khi thời gian trôi qua, tấm pin sẽ già đi và các mùa trong năm thay đổi, tạo ra hiện tượng **trôi dạt dữ liệu (Data Drift)** làm mô hình dự báo kém chính xác dần. Nhóm sẽ cài đặt hệ thống tự động phát hiện sự thay đổi này để tự động huấn luyện lại mô hình mà không cần con người can thiệp thủ công.
> - **Giai đoạn 3 — Gửi cảnh báo tự động về điện thoại:** Nhóm sẽ tích hợp hệ thống với Telegram Bot và Zalo ZNS. Người quản lý hay kỹ sư không cần ngồi canh máy tính mở dashboard mà hệ thống sẽ chủ động gửi báo cáo sản lượng mỗi ngày hoặc cảnh báo có sự cố khẩn cấp ngay trên màn hình điện thoại.
> 
> `[08:55]` *(Nêu việc làm được ngay)*  
> Trong các hướng đi trên, **việc gần nhất mà nhóm có thể triển khai được ngay** là hạ độ hạt thời tiết bằng ảnh mây vệ tinh tầm cao — đây là cách nhanh nhất để giảm sai số dự báo trong những ngày mây che cục bộ mà hoàn toàn không tốn chi phí phần cứng.
> 
> `[09:10]` *(Đứng thẳng trang nghiêm, hai tay khép nhẹ, ánh mắt bao quát toàn thể Thầy/Cô Hội đồng)*  
> 
> Kính thưa Quý Thầy/Cô trong Hội đồng Ban Giám khảo!  
> 
> Buổi bảo vệ tốt nghiệp hôm nay là dấu mốc khép lại chặng đường học tập đầy tự hào của chúng em tại Cao đẳng FPT Polytechnic. Đề tài của nhóm The Outliers chính là kết tinh từ những kiến thức chuyên môn về Xử lý Dữ liệu mà các Thầy/Cô đã tận tình chỉ dạy, kết hợp với tinh thần dám dấn thân tìm tòi giải quyết bài toán năng lượng thực tế.
> 
> Nhóm chúng em xin gửi lời tri ân sâu sắc nhất tới Quý Thầy/Cô!  
> 
> Sau đây, em xin trân trọng kính mời Quý Thầy/Cô trong Hội đồng cho những lời nhận xét, góp ý và đặt câu hỏi phản biện để nhóm chúng em được học hỏi và hoàn thiện đề tài hơn nữa.  
> 
> **Em xin trân trọng cảm ơn Thầy/Cô!**"
