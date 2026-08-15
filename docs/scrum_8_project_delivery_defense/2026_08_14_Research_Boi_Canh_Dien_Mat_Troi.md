# Research bối cảnh điện mặt trời — bám phần cứng thật của dự án

**Ngày:** 14/08/2026
**Phạm vi:** loại tấm pin, inverter, optimizer, tổn thất do nhiệt, cách đặt tấm pin,
tỷ lệ lỗi phần cứng, và cách tối ưu hệ áp mái theo từng chỉ số.

**Nguyên tắc của tài liệu này:**

- Mỗi mục ghi rõ **nguồn nói gì** (trích ý chính) và **áp vào dự án ra sao**.
- Chỗ nào **không tìm được số liệu** thì ghi thẳng là không có, không suy đoán.
- Số liệu về phần cứng dự án đọc trực tiếp từ `data/mlmart_base/v4_final_cleaned.parquet`.

---

## 0. Bộ dữ liệu có paper riêng — UNISOLAR

Đây là phát hiện quan trọng nhất của đợt research: **bộ dữ liệu dự án đang dùng có
một bài báo mô tả dữ liệu (data descriptor) do chính nhóm tạo ra nó công bố.**

### Thông tin trích dẫn

> S. Wimalaratne, D. Haputhanthri, S. Kahawala, G. Gamage, D. Alahakoon và
> A. Jennings, **"UNISOLAR: An Open Dataset of Photovoltaic Solar Energy Generation
> in a Large Multi-Campus University Setting"**, *2022 15th International Conference
> on Human System Interaction (HSI)*, 2022, tr. 1--5.
> DOI: [10.1109/HSI55341.2022.9869474](https://doi.org/10.1109/HSI55341.2022.9869474)

- **Số lượt trích dẫn:** 25 (theo Semantic Scholar, tra ngày 14/08/2026)
- **Kho dữ liệu:** <https://github.com/CDAC-lab/UNISOLAR>
- **Bối cảnh:** công bố trong khuôn khổ cam kết Net Zero Carbon Emissions 2029 của
  Đại học La Trobe, thuộc nền tảng LEAP (La Trobe Energy AI/Analytics Platform)
- **Toàn văn:** IEEE Xplore trả phí, **không có bản open access**

### Abstract nói gì (dịch ý)

Nhóm tác giả giới thiệu bộ dữ liệu mở về sản lượng quang điện, bức xạ mặt trời và
thời tiết ở độ phân giải cao, thu từ **42 trạm PV trên 5 khuôn viên** của Đại học
La Trobe, bang Victoria, Úc. Bộ dữ liệu gồm **khoảng hai năm** sản lượng quang điện
thu ở **khoảng 15 phút**. Vị trí địa lý và **thông số kỹ thuật của từng trạm** cũng
được cung cấp để hỗ trợ nghiên cứu mô hình hoá sản lượng.

Dữ liệu thời tiết có ở **khoảng 1 phút**, do **Cục Khí tượng Úc (BOM)** cung cấp, gồm
sáu biến: nhiệt độ biểu kiến, nhiệt độ không khí, nhiệt độ điểm sương, độ ẩm tương
đối, tốc độ gió và hướng gió. Bài báo mô tả phương pháp thu thập, làm sạch và ghép
dữ liệu thời tiết. Bộ dữ liệu có thể dùng để dự báo, làm chuẩn đối sánh, và cải thiện
kết quả vận hành tại các trạm điện mặt trời.

Theo trang GitHub: dữ liệu trải **tháng 01/2020 đến tháng 04/2022**, sản lượng ở
15 phút, **bức xạ ở mức giờ**, thời tiết lấy từ **trạm khí tượng gần nhất mỗi khuôn
viên**, trung bình về khoảng 15 phút.

### Đối chiếu với dữ liệu dự án đang dùng

| Tiêu chí | UNISOLAR công bố | Dự án đang dùng | Khớp? |
|---|---|---|---|
| Số trạm | 42 | 42 | Khớp |
| Số khuôn viên | 5 | 5 | Khớp |
| Độ phân giải sản lượng | 15 phút | 15 phút | Khớp |
| Khoảng thời gian | 01/2020 – 04/2022 | 01/01/2020 – 23/04/2022 (843 ngày) | Khớp |
| Thông số kỹ thuật từng trạm | Có | Có (`panel`, `inverter`, `optimizers`) | Khớp |
| **Nguồn thời tiết** | **BOM, 6 biến, 1 phút** | **Open-Meteo, theo giờ** | **KHÁC** |
| **Bức xạ** | Theo giờ | Theo giờ (`shortwave_radiation`) | Khớp |

### Ba điểm cần đưa vào báo cáo

**① Phải trích dẫn bài này ở phần mô tả dữ liệu.** Đây là nguồn gốc chính thức của
bộ dữ liệu. Báo cáo tốt nghiệp mà không dẫn data descriptor của chính bộ dữ liệu
mình dùng là một thiếu sót rõ ràng.

**② Phải giải thích vì sao dùng Open-Meteo thay vì bộ thời tiết đi kèm.** Lập luận
bảo vệ đã rõ sau khi đọc toàn văn (xem PH1): bộ gốc có **bức xạ theo giờ từ Solcast
với đúng hai tham số** là GHI và cloud opacity. Open-Meteo cũng theo giờ nhưng cung
cấp thêm **bức xạ thành phần** (`direct_normal_irradiance`,
`diffuse_solar_radiation`), **mây theo ba tầng**, `sunshine_duration` và lượng mưa.
Vậy dự án **không đánh đổi độ phân giải** mà **đổi lấy nhiều biến vật lý hơn**. Đây
là lý do đứng vững được trước hội đồng.

**③ Bài báo mô tả sẵn phương pháp làm sạch và ghép dữ liệu.** Nên đối chiếu quy trình
ETL của dự án với quy trình gốc để nêu rõ chỗ nào kế thừa, chỗ nào làm khác.

### ĐÃ CÓ TOÀN VĂN — `~/Downloads/wimalaratne2022.pdf` (5 trang, tải 25/06/2026)

Nhóm đã tải bài này từ trước; đường dẫn ghi trong
`docs/2026_08_06_Danh_Sach_Paper_Can_Tai_Ve.md`. Ảnh chụp bài báo cũng có sẵn tại
`report_section_6/images_khong_dung/paper_unisolar_dataset_khung.png` nhưng **chưa
được dùng trong báo cáo**.

Sáu phát hiện dưới đây **chỉ có trong toàn văn**, không có trong abstract.

#### PH1. Bức xạ đến từ Solcast, không phải BOM

Bài báo tách rõ hai nguồn:

- **Solcast** cung cấp **bức xạ**, độ phân giải **giờ**, đúng hai tham số:
  **GHI** và **Cloud opacity percentage**.
- **BOM** cung cấp **thời tiết**: nhiệt độ không khí, nhiệt độ điểm sương, độ ẩm
  tương đối, tốc độ gió, hướng gió. Ghi ở 1 phút, **đóng gói trong bộ dữ liệu ở mức
  trung bình 15 phút**.

Năm trạm khí tượng BOM tương ứng năm khuôn viên:

| Khuôn viên | Trạm khí tượng | Mã trạm | Vĩ độ | Kinh độ |
|---|---|---|---|---|
| Bundoora | Viewbank | 086068 | −37,74 | 145,10 |
| Wodonga | Albury Airport AWS | 072160 | −36,07 | 146,95 |
| Shepparton | Shepparton Airport | 081125 | −36,43 | 145,39 |
| Mildura | Mildura Airport | 076031 | −34,24 | 142,09 |
| Bendigo | Bendigo Airport | 081123 | −36,74 | 144,33 |

> **Sửa lại nhận định trước đó:** bộ gốc **không** có bức xạ 1 phút. Bức xạ vốn đã
> là **theo giờ** (Solcast). Vậy việc dự án dùng Open-Meteo theo giờ **không hề làm
> mất độ phân giải bức xạ** so với bộ gốc. Đây là lập luận bảo vệ tốt hơn nhiều so
> với giả định ban đầu.

#### PH2. Ngữ nghĩa mốc thời gian — cực kỳ quan trọng

Data dictionary của bài báo ghi rõ:

- `Timestamp`: **mốc kết thúc** của khoảng 15 phút
- `SolarGeneration`: **tổng sản lượng trong 15 phút vừa qua tính từ mốc đó**

Nghĩa là giá trị tại mốc $T$ đại diện cho khoảng $(T-15\text{ phút},\ T]$, **không
phải** giá trị tức thời tại $T$. Điều này ảnh hưởng trực tiếp tới quy tắc ghép thời
tiết nhân quả: dữ liệu khí tượng dùng cho mốc $T$ phải thuộc khoảng đã kết thúc
trước hoặc đúng bằng $T$ — đúng như pipeline đang làm.

#### PH3. Bộ gốc MÔ TẢ tiền xử lý, nhưng dữ liệu công bố vẫn là dữ liệu thô

> **Đã kiểm chứng bằng dữ liệu ngày 14/08/2026 — kết luận ngược với cách đọc ban đầu.**

Đọc mô tả trong bài báo dễ tưởng bộ dữ liệu công bố đã được làm sạch. Kiểm trực tiếp
trên `data/raw/Solar_Energy_Generation.csv` (2.731.946 dòng, đúng 4 cột
`CampusKey, SiteKey, Timestamp, SolarGeneration`) cho kết quả khác:

| Kiểm tra | Kết quả trên tệp raw | Diễn giải |
|---|---|---|
| Giá trị bằng $0$ | **0 dòng** | Bộ gốc **không** chứa số 0 nào |
| Ô trống (NaN) | **1.536.301 dòng — 56,2%** | Thiếu dữ liệu để trống, không ép về 0 |
| $0 <$ giá trị $< 0{,}1$ | 0 dòng | — |
| **Vượt phân vị 99 của từng trạm** | **11.537 dòng — 0,42%** | **Ngoại lai CÒN NGUYÊN** |

**Kết luận 1 — ngoại lai chưa bị cắt khỏi bộ công bố.** Câu *"The outliers are moved
downstream for further investigation"* có nghĩa là ngoại lai được **gắn cờ và chuyển
sang bước sau để điều tra**, không phải bị loại khỏi dữ liệu phát hành. Việc lọc chỉ
diễn ra trong quy trình huấn luyện của chính nhóm tác giả. Dữ liệu tải về vẫn là
**dữ liệu thô**.

**Kết luận 2 — tỷ lệ 50,6% số 0 là do pipeline của dự án, không phải của bộ gốc.**
Tệp raw không có số 0 nào, chỉ có **56,2% ô trống**. Con số 50,6% dòng bằng 0 trong
ML Mart v4 xuất hiện **sau khi tầng ETL của dự án điền `night_zero` và các nhãn
provenance khác**. Đây là kết quả xử lý của nhóm, phải ghi nhận đúng như vậy trong
báo cáo.

**Hệ quả cho phần GMM--IF:** pipeline phát hiện ngoại lai của dự án **không chạy chồng
lên một lớp đã lọc sẵn**. Bộ dữ liệu đầu vào vẫn còn nguyên ngoại lai, nên lớp GMM--IF
là lớp phát hiện thực chất đầu tiên áp lên dữ liệu này.

#### PH3b. Chi tiết kỹ thuật đáng ghi nhận từ mô tả của bài báo

Trích nguyên văn phần mô tả tiền xử lý:

> Số đọc công tơ là **số cộng dồn**, nên sản lượng trong mỗi khoảng 15 phút được tính
> bằng **hiệu của hai số đọc liền kề**. Các giá trị này sau đó được tiền xử lý để
> phát hiện ngoại lai bằng **một tập hợp kỹ thuật, trong đó kỹ thuật nền tảng xét
> các giá trị cô lập nằm trên phân vị 99 của từng trạm**. Ngoại lai được chuyển
> xuống các bước sau để điều tra thêm. Ngoài ra, **giá trị nhỏ hơn 0,1 được ép về 0**
> để nâng chất lượng dữ liệu.

Ba hệ quả cho dự án:

1. **Tỷ lệ 50,6% số dòng bằng 0** và **5,2% bước ban ngày bằng 0** trong dữ liệu
   không hoàn toàn là hiện tượng tự nhiên — một phần do quy tắc **ép giá trị < 0,1
   về 0** của bộ gốc.
2. Pipeline GMM--IF của dự án chạy **chồng lên** một lớp phát hiện ngoại lai đã có
   sẵn (phân vị 99 theo trạm). Cần nói rõ điều này, nếu không hội đồng sẽ tưởng dự
   án là lớp phát hiện duy nhất.
3. Sản lượng là **hiệu của hai số đọc cộng dồn** — giải thích vì sao có thể xuất hiện
   giá trị âm hoặc nhảy bậc khi công tơ bị reset hoặc mất số đọc.

#### PH4. Kiểu lắp đặt khác nhau giữa các khuôn viên

Bài báo nêu rõ:

- **Bundoora** và **Mildura**: PV lắp **trên mái** (rooftop)
- **Bendigo** và **Albury-Wodonga**: **mái che xe chạy bằng năng lượng mặt trời**
  (solar carport)

Đây là chi tiết có giá trị lớn khi đọc cùng phần tổn thất nhiệt ở Mục 3: **carport
thoáng gió cả hai mặt**, nên nhiệt độ vận hành thấp hơn hẳn tấm áp mái. Chênh lệch
có thể tới **10--15°C**, tương đương **4--6%** sản lượng ở ngày nóng.

Bundoora là khuôn viên chính: **7.500 tấm pin trên 25 toà nhà**, giảm **4.000 tấn
CO₂/năm**, đáp ứng **50% nhu cầu điện ban ngày**. Toàn chương trình Net Zero 2029 của
La Trobe đầu tư **75 triệu đô la Úc**.

#### PH5. Bài báo có sẵn một mô hình đối chứng XGBoost

Mục *Technical Validation* của bài báo dựng năm mô hình XGBoost (một cho cả năm, bốn
cho từng mùa Nam bán cầu), dùng ba đặc trưng chọn theo phân tích tương quan: **nhiệt
độ không khí, độ ẩm tương đối và GHI**. Kết quả công bố:

| Mô hình | MAE | RMSE | nRMSE |
|---|---|---|---|
| Cả năm | 17,7615 | 34,7363 | 0,4613 |
| Xuân | 20,0709 | 38,3097 | 0,4835 |
| Hạ | 21,5280 | 40,3528 | 0,4171 |
| Thu | 9,0811 | 20,8432 | 0,5833 |
| Đông | 11,1063 | --- | --- |

> **Cảnh báo khi so sánh:** các mô hình này chạy trên **những trạm PV lớn nhất** của
> trường, không phải toàn bộ 42 trạm, nên MAE tuyệt đối (17,76 kWh) **không so trực
> tiếp** được với MAE của dự án (1,37 kWh trên tập test). Muốn so phải dùng chỉ số
> chuẩn hoá và cùng phạm vi trạm.

#### PH6. Tương quan GHI của bài báo là 0,9 — dự án đo được 0,403

Bài báo viết: *"GHI đạt tương quan gần 0,9. Điều này cho thấy ảnh hưởng dương rất
mạnh của bức xạ lên sản lượng PV"*, và *"góc thiên đỉnh có tương quan âm mạnh nhất
vì đạt giá trị nhỏ nhất vào giữa trưa khi cường độ nắng cao nhất"*.

Dự án đo trên **toàn bộ 42 trạm gộp chung** chỉ được **0,403**.

**Chênh lệch này không phải mâu thuẫn mà là bằng chứng mạnh cho thiết kế của dự án.**
Bài báo tính tương quan trên **các trạm lớn nhất**, tức quy mô đồng nhất. Dự án gộp
42 trạm chênh nhau **48,7 lần** về sản lượng trung bình, nên cùng một mức bức xạ cho
ra sản lượng rất khác nhau tuỳ trạm — làm loãng tương quan từ 0,9 xuống 0,403.

Đây chính là lý do pipeline **bắt buộc** phải chuẩn hoá theo `site_scale`. Có thể
dùng đúng cặp số **0,9 so với 0,403** này để chứng minh trong báo cáo.

---

## 0b. Phần cứng thật của dự án

Đọc từ cột `panel`, `inverter`, `optimizers`, `capacity_kw`, `number_of_panels` của
tệp ML Mart v4, lấy một dòng đại diện cho mỗi `site_id` (42 trạm).

### Tấm pin

| Model | Số trạm |
|---|---|
| Trina 330W | 16 |
| Trina 310W | 7 |
| SunPower SPR-E20-435-COM | 1 |
| Unknown | 17 |
| TBD | 1 |

### Inverter

| Hãng | Số trạm |
|---|---|
| SolarEdge (SE15K, SE17K, SE25K, SE27.6K, SE50K, SE82.8K) | 23 |
| SMA | 1 |
| ABB | 1 |
| Unknown | 17 |

Các trạm lớn ghép nhiều inverter, ví dụ `4 x SolarEdge SE82.8K`, `3 x SolarEdge SE50K`.

### Optimizer

| Loại | Số trạm |
|---|---|
| SolarEdge P730 | 14 |
| SolarEdge P700 | 9 |
| **None (không có optimizer)** | **19** |

Số lượng optimizer mỗi trạm từ 35 tới 584 chiếc.

### Quy mô và vị trí

- Công suất: **21 – 540 kW**
- Số tấm pin: **69 – 1.241** tấm/trạm
- 5 khuôn viên Đại học La Trobe, bang Victoria, Úc:
  **Albury-Wodonga, Bendigo, Bundoora, Mildura, Shepparton**
- Vĩ độ **−34,205 đến −37,718**; kinh độ 142,167 đến 146,849

> **Điểm quan trọng nhất:** dự án dùng kiến trúc **SolarEdge DC-optimized**
> (module-level power electronics), nhưng **chỉ 23/42 trạm có optimizer**.
> 19 trạm còn lại chạy chuỗi thuần. Đây là một *thí nghiệm tự nhiên* nằm sẵn
> trong dữ liệu.

---

## 1. Kiến trúc DC optimizer so với inverter chuỗi

### Nguồn nói gì

**Lenergy (Úc) — String Inverters vs Microinverters vs DC Optimisers**

- Inverter chuỗi bị ảnh hưởng nặng bởi che bóng: **một tấm bị che kéo tụt sản lượng
  của cả chuỗi**.
- Với DC optimizer, mỗi tấm được theo dõi độc lập, nên tấm bị che hoặc suy giảm
  **không kéo phần còn lại xuống**.
- DC optimizer **đưa tổn thất mismatch về gần 0** và giảm ảnh hưởng của che bóng
  khoảng **một phần ba**.
- Optimizer chỉ xử lý phía DC, **vẫn cần inverter chuỗi** để đổi sang AC — đây là
  khác biệt kiến trúc quyết định phần lớn đánh đổi về chi phí và độ tin cậy.
- Giám sát: optimizer và microinverter cho **giám sát mức từng tấm**; inverter chuỗi
  không có optimizer chỉ cho dữ liệu toàn hệ.

### Pros and cons

| | DC Optimizer (23 trạm) | Chuỗi thuần (19 trạm) |
|---|---|---|
| Che bóng | Cô lập được tấm bị che | Kéo tụt cả chuỗi |
| Mismatch | Gần 0 | Tích luỹ theo tuổi tấm |
| Giám sát | Từng tấm | Chỉ toàn hệ |
| Số điểm có thể hỏng | Nhiều hơn — mỗi tấm thêm một thiết bị điện tử | Ít hơn |
| Vị trí thiết bị | **Trên mái, dưới tấm pin** — nóng và khó tiếp cận | Inverter đặt dưới, dễ bảo trì |
| Chi phí ban đầu | Cao hơn | Thấp hơn |

**Điểm ít được nhắc:** optimizer nằm đúng chỗ nóng nhất của hệ thống và khó tiếp cận
nhất. Thay một optimizer hỏng tốn công hơn thay inverter đặt dưới đất.

---

## 2. Tấm pin và hệ số nhiệt độ

### Nguồn nói gì

**A1 SolarStore — Temperature coefficient of solar panels**

- Hệ số nhiệt độ theo công suất của tấm phổ thông nằm trong dải
  **−0,2%/°C đến −0,5%/°C**.
- Hệ số này cho biết công suất thay đổi bao nhiêu phần trăm khi nhiệt độ lệch 1°C
  khỏi mốc chuẩn 25°C.

**NOCT** (Nominal Operating Cell Temperature) của tấm phổ thông là **45–48°C**, đo ở
điều kiện 800 W/m², không khí 20°C, gió 1 m/s.

### Số chính thức từ datasheet Trina — ĐÃ XÁC MINH

Tra được datasheet chính hãng dòng **Trina PD14** (Allmax / Tallmax), đúng họ sản
phẩm của hai model dự án đang dùng:

| Thông số | Trina TSM-330 PD14 | Dòng 310--325W PD14 |
|---|---|---|
| **Hệ số nhiệt độ $P_{max}$** | **$-0{,}41\%/^\circ\text{C}$** | cùng họ, tương đương |
| Hiệu suất module | $17{,}0\%$ | tối đa $16{,}8\%$ |
| Dung sai công suất | $0 / +5$ W | $0 / +5$ W |
| Bảo hành vật liệu | $10$ năm | $10$ năm |
| Bảo hành công suất tuyến tính | $25$ năm | $25$ năm |

**Ý nghĩa của $-0{,}41\%/^\circ\text{C}$:** đây là **đầu xấu** của dải phổ thông
($-0{,}2$ đến $-0{,}5\%/^\circ\text{C}$). Tấm càng nóng càng mất nhiều công suất, và
$-0{,}41$ nghĩa là mỗi độ C vượt mốc $25^\circ$C làm mất $0{,}41\%$ công suất.

Tính lại ví dụ Mildura ngày $40^\circ$C với số chính thức:

| Kiểu lắp | Nhiệt độ tế bào | Chênh so STC | **Tổn thất** |
|---|---|---|---|
| Áp mái, không khe hở | $\approx 80^\circ$C | $55^\circ$C | $55 \times 0{,}41 = \mathbf{22{,}6\%}$ |
| Mái có khe $12$ cm | $\approx 70^\circ$C | $45^\circ$C | $45 \times 0{,}41 = \mathbf{18{,}5\%}$ |
| **Carport (Bendigo, Albury-Wodonga)** | $\approx 62^\circ$C | $37^\circ$C | $37 \times 0{,}41 = \mathbf{15{,}2\%}$ |

Chênh giữa áp mái không khe hở và carport là **7,4 điểm phần trăm** trong cùng một
ngày nóng — đây là con số định lượng cho phát hiện PH4 ở Mục 0.

**SunPower SPR-E20-435-COM** (1 trạm) dùng công nghệ back-contact, hệ số nhiệt tốt
hơn đáng kể (dòng E20 quanh $-0{,}30\%/^\circ\text{C}$) và hiệu suất trên $20\%$.
Một trạm nên không ảnh hưởng thống kê tổng, nhưng **là trạm đáng tách riêng khi phân
tích** vì đặc tính nhiệt khác hẳn 23 trạm Trina.

> **Lưu ý minh bạch:** con số $-0{,}30\%/^\circ\text{C}$ của SunPower là **dải điển
> hình của dòng E20**, chưa tra được datasheet đúng mã SPR-E20-435-COM.

---

## 3. Tổn thất do quá nhiệt

### Nguồn nói gì

**Solarstone — Natural Ventilation and Effect of Temperature on Solar Roofs**

- Tấm có thông gió tích hợp chạy mát hơn **3–4°C** so với tấm không thông gió.
- Chênh lệch đó tương đương **chênh 1,5–2% hiệu năng**, tính theo hệ số nhiệt chuẩn
  −0,5%/°C.

**Nghiên cứu về khe hở và cách lắp**

- Khe hở **12–15 cm** giữa tấm và mái: tấm nóng hơn không khí khoảng **30°C**.
- **Không có khe hở**: tấm nóng hơn không khí tới **40°C**.
- Lắp trên đất hoặc cột: chỉ nóng hơn không khí **20–25°C** — thấp nhất.
- Khe hở **10–12,5 cm là tối ưu** để đạt nhiệt độ tế bào thấp nhất.

**Dominguez, Kleissl et al. (UCSD) — Effects of Solar Photovoltaic Panels on Roof
Heat Transfer:** nghiên cứu học thuật về truyền nhiệt giữa tấm pin và mái.

**Tổng hợp:** nhiệt độ cao có thể kéo hiệu năng hệ thống xuống **5–15%**.

### Áp vào dự án

Ví dụ tính cho Mildura ngày 40°C, tấm áp mái không khe hở:

```
Nhiệt độ tế bào ≈ 40°C + 40°C = 80°C
Chênh so với STC  = 80 − 25 = 55°C
Tổn thất          = 55 × 0,39%/°C ≈ 21,5% công suất
```

Cùng ngày đó nếu có khe thông gió 12 cm thì tế bào chỉ khoảng 70°C, tổn thất giảm
xuống ~17,6% — **chênh gần 4 điểm phần trăm chỉ nhờ khe hở**.

---

## 4. Cách đặt tấm pin tối ưu

### Nguồn nói gì

**Solar Choice (Úc) và các nguồn địa phương Victoria**

- **Hướng:** Nam bán cầu thì **hướng Bắc là tối ưu**. Đặt hướng khác có thể mất
  **10–20%** sản lượng.
- **Góc nghiêng:** tối ưu bằng vĩ độ. Với Melbourne (vĩ độ 37,81°) là khoảng
  **38°**; nhiều nguồn khuyến nghị dải thực dụng **25–30°** hoặc **30–40°**.
- **Dung sai rộng:** nếu độ dốc mái nằm trong khoảng **±10–15°** so với góc vĩ độ,
  chỉ mất **1–1,5%** sản lượng tối đa.
- **Đông/Tây:** đặt tấm trên mái dốc thoải (khoảng 10°) theo hướng Đông–Tây
  (90° và 270°) làm mất trung bình **14%** hiệu suất.

### Áp vào dự án

5 khuôn viên trải từ vĩ độ −34,2 (Mildura) tới −37,7 (Bundoora), nên góc tối ưu
khác nhau khoảng 3,5° giữa hai đầu — nằm gọn trong dung sai ±10–15°, tức **một
thiết kế góc chung cho cả 5 khuôn viên là chấp nhận được**.

**Đánh đổi cần biết:**

- Góc nghiêng thấp: tổng sản lượng năm nhỉnh hơn ở vĩ độ thấp, nhưng **bám bụi
  nhiều hơn** và **thoát nhiệt kém hơn**.
- Hướng Tây: tổng sản lượng thấp hơn hướng Bắc, nhưng **đẩy đỉnh phát về buổi
  chiều** — phù hợp với cơ sở dùng điện nhiều vào chiều như trường đại học.

---

## 5. Tỷ lệ lỗi phần cứng

### KHÔNG TÌM ĐƯỢC — nói thẳng

**Không có số liệu tỷ lệ lỗi thực địa công bố cho SolarEdge P700 và P730.**

Đã tìm và chỉ thấy:

- Datasheet kỹ thuật của dòng P-Series — **không có** dữ liệu tỷ lệ hỏng.
- Trang *Multi-Level Reliability Approach* của SolarEdge — mô tả **phương pháp**
  thử nghiệm tuổi thọ gia tốc và bảo hành 25 năm, **không công bố con số**.
- Diễn đàn DIY Solar có báo cáo hỏng lẻ tẻ — **là giai thoại, không dùng làm bằng
  chứng học thuật được**.

**Cách lấy số thật nếu cần:** liên hệ trực tiếp bộ phận kỹ thuật SolarEdge, hoặc
lấy từ đơn vị lắp đặt có theo dõi hiệu năng trên đội hệ thống lớn.

### Tỷ lệ lỗi theo LINH KIỆN — số liệu thực địa

Không có số cho đúng model P700/P730, nhưng có số cho **loại linh kiện**. Kết luận
nhất quán qua nhiều nghiên cứu độc lập: **inverter là thành phần hỏng nhiều nhất
trong hệ quang điện**, bỏ xa tấm pin.

| Chỉ số | Giá trị | Nguồn |
|---|---|---|
| Inverter chiếm bao nhiêu phần tổng số lỗi thiết bị | **52--60%** | Nghiên cứu nhà máy PV |
| Inverter chiếm bao nhiêu phần sự cố được báo cáo | **~66%** | Dữ liệu thực địa |
| Inverter chiếm bao nhiêu phần tổng số lỗi hệ thống | **43%** | Tổng hợp ngành |
| Phần sản lượng mất do lỗi inverter | **36%** | Tổng hợp ngành |
| Tỷ lệ hỏng inverter chuỗi trong $2$ năm đầu | **$\approx 0{,}89\%$** | So sánh string vs micro |
| Tỷ lệ hỏng microinverter trong $2$ năm đầu | **$\approx 0{,}0551\%$** | So sánh string vs micro |
| Inverter dân dụng hỏng lần đầu trong $15$ năm | **34%** | Thống kê dân dụng |
| Thay thế/sửa chữa hàng năm (microinverter, Ấn Độ) | **$1{,}5$--$2{,}0\%$/năm** | Ý kiến chuyên gia, dữ liệu áp mái |

**Đọc bảng này cho dự án:**

**① Inverter mới là mối lo, không phải tấm pin.** Dự án có **23 trạm dùng SolarEdge**,
nhiều trạm ghép $2$--$5$ inverter (ví dụ `4 x SolarEdge SE82.8K`). Càng nhiều inverter
trên một trạm thì xác suất ít nhất một cái hỏng càng cao. Một trạm có $4$ inverter,
mỗi cái hỏng độc lập với tỷ lệ $p$ trong $2$ năm, thì xác suất trạm gặp sự cố là
$1-(1-p)^4$ --- gấp gần bốn lần một trạm đơn inverter.

**② Con số $0{,}89\%$ so với $0{,}0551\%$ nói gì về kiến trúc của dự án.** Chênh
lệch $16$ lần giữa inverter chuỗi và microinverter cho thấy **phân tán công suất
xuống mức tấm làm giảm mạnh tỷ lệ hỏng của từng khối**. Nhưng cần cẩn thận: dự án
dùng **optimizer**, không phải microinverter. Optimizer chỉ xử lý phía DC và **vẫn
cần inverter chuỗi**, nên hệ vẫn giữ nguyên rủi ro của inverter chuỗi, **cộng thêm**
rủi ro của $35$--$584$ optimizer đặt trên mái mỗi trạm.

**③ Đánh đổi thật của kiến trúc optimizer:**

| | Lợi | Hại |
|---|---|---|
| Số điểm hỏng | --- | Tăng thêm $35$--$584$ thiết bị/trạm |
| Phát hiện hỏng | Biết chính xác tấm nào | --- |
| Ảnh hưởng khi hỏng | Mất $1$ tấm thay vì cả chuỗi | --- |
| Chi phí sửa | --- | Phải leo mái, tháo tấm |
| Rủi ro inverter | Không giảm | Vẫn giữ nguyên |

Nói cách khác: optimizer **không làm hệ ít hỏng hơn**, mà làm **mỗi lần hỏng ít thiệt
hại hơn và dễ tìm hơn**. Đây là điểm cần nói đúng, tránh khẳng định quá tay.

### Số liệu độc lập DÙNG ĐƯỢC

**NREL — Fleet Performance Data Initiative**

- Tổng hợp trên **hơn 54.000 hệ thống** toàn cầu.
- Tấm pin hiện đại suy giảm ở mức trung vị **0,5–0,7%/năm**.
- Dữ liệu từ **8,5 GW** và **24.000 kênh dữ liệu inverter** riêng biệt.
- Bốn chủ đề phân tích chính: xu hướng Performance Index, độ khả dụng hệ thống,
  tổn thất do bụi bẩn, và suy giảm hệ thống.

**NREL — Photovoltaic Degradation Rates: An Analytical Review:** tổng quan phân tích
về tốc độ suy giảm của tấm pin.

**IEA PVPS Task 13** — chuyên trách độ tin cậy và hiệu năng hệ quang điện:

- *Assessment of Photovoltaic Module Failures in the Field* (T13-09-2017) — đánh
  giá các dạng lỗi tấm pin trong vận hành thực tế.
- *Degradation and Failure Modes in New PV Cell and Module Technologies*
  (T13-30-2025) — cơ chế suy giảm và lỗi của công nghệ tấm pin mới.

**Ghi chú của NREL:** việc dùng inverter chuỗi hay module-level power electronics
**ảnh hưởng tới tổn thất mismatch**, và do đó thay đổi cách mà suy giảm của từng tấm
cuối cùng đóng góp vào tổn thất hiệu năng toàn hệ.

### Áp vào dự án

Dữ liệu dự án trải **843 ngày** (01/01/2020 → 23/04/2022), tức khoảng 2,3 năm.
Với mức suy giảm 0,5–0,7%/năm, tổng suy giảm dự kiến chỉ **1,2–1,6%** — **quá nhỏ
để tách khỏi nhiễu thời tiết**, nên không nên đưa suy giảm tấm pin vào mô hình dự báo
ngắn hạn của dự án.

---

## 6. Cách tối ưu thực tế theo từng chỉ số

### Giảm tổn thất nhiệt (temperature loss)

- Khe thông gió **10–12,5 cm** dưới tấm — biện pháp rẻ nhất, hiệu quả **1,5–2%**
- Tránh lắp áp sát mái tôn sẫm màu
- Ưu tiên tấm có hệ số nhiệt thấp cho khuôn viên nóng (Mildura)

### Nâng Performance Ratio (PR)

- Rửa tấm định kỳ — bụi bẩn là nguyên nhân hàng đầu kéo PR xuống ở vùng khô
- Dùng giám sát mức tấm (đã có sẵn ở 23 trạm nhờ optimizer) để phát hiện tấm suy
  giảm sớm
- Kiểm tra kết nối DC, chống ăn mòn đầu nối

### Nâng Capacity Factor (CF)

- Chỉnh hướng và góc về gần tối ưu khi có dịp thay mái
- Giảm che bóng: cắt cây, tránh bóng ống khói, tính khoảng cách hàng để tránh tự che

### Tăng tổng sản lượng

- Tỷ số DC/AC (oversizing) **1,1–1,3** để tận dụng inverter tốt hơn
- Bố trí hỗn hợp Bắc–Tây nếu muốn khớp đường phụ tải buổi chiều

### Giảm hư hỏng

- Kiểm tra nhiệt hồng ngoại định kỳ để bắt điểm nóng và mối nối kém
- Với hệ có optimizer: theo dõi cảnh báo mức tấm, thay trước khi hỏng lan
- Đặt inverter nơi thoáng mát, tránh nắng chiếu trực tiếp

---

## 7. Ba hướng khai thác ngay từ dữ liệu đang có

### 7.1 So sánh 23 trạm có optimizer với 19 trạm không có

Đây là **thí nghiệm tự nhiên** nằm sẵn trong dữ liệu, không phải chạy thêm gì.
Nếu nhóm có optimizer cho PR cao hơn hoặc ít ngày sụt bất thường hơn, đó là phát
hiện có giá trị thật — và giải thích được vì sao mô hình dự báo trên hai nhóm này
hành xử khác nhau.

### 7.2 Khai thác chênh lệch khí hậu giữa 5 khuôn viên

Mildura (vĩ độ −34,2) thuộc vùng bán khô hạn, bức xạ cao và nóng; Bundoora (−37,7)
là khí hậu ôn đới ven biển. Cùng loại tấm pin nhưng tổn thất nhiệt khác hẳn nhau.

### 7.3 Giải thích tương quan bức xạ–sản lượng chỉ 0,403

Con số thấp bất ngờ này có ba nguyên nhân cộng dồn:

1. Chênh lệch quy mô **48,7 lần** giữa trạm mạnh nhất và yếu nhất
2. Kiến trúc khác nhau — 23 trạm có optimizer, 19 trạm không
3. Tổn thất nhiệt khác nhau theo khuôn viên

Đây chính là lý do pipeline **bắt buộc** phải chuẩn hoá theo `site_scale` thay vì
đưa bức xạ thô vào mô hình.

---

## 8. Danh sách nguồn

| Nguồn | Loại | Dùng cho mục |
|---|---|---|
| **[UNISOLAR — Wimalaratne và cộng sự (2022), IEEE HSI](https://doi.org/10.1109/HSI55341.2022.9869474)** | **Data descriptor — nguồn gốc bộ dữ liệu** | **Mô tả dữ liệu (bắt buộc trích)** |
| [UNISOLAR — kho dữ liệu GitHub](https://github.com/CDAC-lab/UNISOLAR) | Kho dữ liệu | Định dạng, khoảng thời gian |
| [IEA PVPS T13-09-2017 — Assessment of PV Module Failures in the Field](https://iea-pvps.org/wp-content/uploads/2017/09/170515_IEA-PVPS-report_T13-09-2017_Internetversion_2.pdf) | Báo cáo quốc tế | Lỗi tấm pin thực địa |
| [IEA PVPS rep7_08 — Reliability Study of Grid Connected PV Systems: Field Experience](https://iea-pvps.org/wp-content/uploads/2020/01/rep7_08.pdf) | Báo cáo quốc tế | Độ tin cậy hệ nối lưới |
| [Failure Rates in Photovoltaic Systems: A Careful Selection of Quantitative Data (ResearchGate)](https://www.researchgate.net/publication/344194402_Failure_Rates_in_Photovoltaic_Systems_A_Careful_Selection_of_Quantitative_Data_Available_in_the_Literature) | Tổng quan học thuật | Tỷ lệ lỗi định lượng |
| [Sandia/OSTI — TRACE-PV: Tool for Reliability Assessment of Critical Electronics in PV](https://www.osti.gov/servlets/purl/1898525) | Phòng thí nghiệm quốc gia | Độ tin cậy điện tử công suất |
| [STET 2025 — Reliability analysis and life cycle costing of rooftop solar PV](https://www.stet-review.org/articles/stet/full_html/2025/01/stet20250006/stet20250006.html) | Tạp chí bình duyệt | Tỷ lệ thay thế hàng năm áp mái |
| [Trina Solar — Datasheet dòng PD14 (Allmax/Tallmax)](https://static.trinasolar.com/sites/default/files/AU_Datasheet_TALLMAX_PD14.pdf) | Nhà sản xuất | **Hệ số nhiệt $-0{,}41\%/^\circ$C** |
| [Trina TSM-PD14-330 — EnergySage](https://www.energysage.com/equipment/solar-panels/trina-solar-us/tsm-pd14-330-277bc4e2/) | Cơ sở dữ liệu thiết bị | Thông số TSM-330 |
| [IEA PVPS T13-30-2025 — Degradation and Failure Modes](https://iea-pvps.org/wp-content/uploads/2025/02/IEA-PVPS-T13-30-2025-REPORT-Degradation-and-Failure.pdf) | Báo cáo quốc tế | Cơ chế suy giảm |
| [NREL — Photovoltaic Degradation Rates: An Analytical Review](https://docs.nrel.gov/docs/fy12osti/51664.pdf) | Phòng thí nghiệm quốc gia | Tốc độ suy giảm |
| [NREL — Perspective: Performance Loss Rate in PV Systems](https://docs.nrel.gov/docs/fy23osti/85463.pdf) | Phòng thí nghiệm quốc gia | Tổn thất hiệu năng, ảnh hưởng của MLPE |
| [SolarEdge — Multi-Level Reliability Approach](https://solaredge.com/us/solutions/reliability-approach) | Nhà sản xuất | Phương pháp thử độ tin cậy (không có số) |
| [SolarEdge — P-Series Commercial Power Optimizer Datasheet](https://knowledge-center.solaredge.com/sites/kc/files/se-p-series-commercial-add-on-power-optimizer-datasheet.pdf) | Nhà sản xuất | Thông số P700/P730 |
| [Solarstone — Natural Ventilation and Effect of Temperature on Solar Roofs](https://solarstone.com/blog/natural-ventilation-and-effect-of-temperature-on-solar-roofs) | Nhà cung cấp | Thông gió, 3–4°C, 1,5–2% |
| [Dominguez & Kleissl (UCSD) — Effects of PV Panels on Roof Heat Transfer](http://maeresearch.ucsd.edu/kleissl/pubs/DominguezetalSE2011.pdf) | Học thuật | Truyền nhiệt mái |
| [A1 SolarStore — Temperature coefficient of solar panels](https://a1solarstore.com/blog/too-much-sun-what-is-temperature-coefficient-of-solar-panels.html) | Thương mại | Dải hệ số nhiệt |
| [Solar Choice — Solar panel tilt and orientation in Australia](https://www.solarchoice.net.au/blog/solar-panel-tilt-and-orientation-in-australia/) | Chuyên trang Úc | Góc và hướng |
| [Lenergy — String Inverters vs Microinverters vs DC Optimisers](https://lenergy.com.au/string-inverters-vs-microinverters-vs-dc-optimisers/) | Đơn vị lắp đặt Úc | So sánh kiến trúc |

### Xếp hạng độ tin cậy

1. **Cao nhất:** IEA PVPS, NREL — báo cáo có bình duyệt, mẫu hàng chục nghìn hệ thống
2. **Trung bình:** bài học thuật UCSD; datasheet nhà sản xuất (đúng thông số nhưng
   thiên về marketing khi nói độ tin cậy)
3. **Tham khảo:** trang thương mại và đơn vị lắp đặt — số liệu hợp lý và nhất quán
   với nguồn cấp trên, nhưng **không nên trích làm nguồn chính** trong báo cáo học thuật

**Khuyến nghị:** nếu đưa vào báo cáo tốt nghiệp, chỉ trích nhóm 1 và 2. Nhóm 3 chỉ
dùng để định hướng tìm hiểu.
