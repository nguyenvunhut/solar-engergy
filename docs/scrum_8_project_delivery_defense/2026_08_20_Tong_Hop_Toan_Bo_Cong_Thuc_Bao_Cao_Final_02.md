# CẨM NANG TOÀN DIỆN CÔNG THỨC TOÁN HỌC, VẬT LÝ & KỸ THUẬT DỮ LIỆU (BÁO CÁO FINAL 02)
> **Dự án:** Hệ thống Xử lý Dữ liệu, Phát hiện Dị thường Vận hành và Dự báo Sản lượng 42 Trạm Điện Mặt Trời tại Úc  
> **Nhóm thực hiện:** The Outliers — Đồ án Tốt nghiệp Chuyên ngành Xử lý Dữ liệu (FPT Polytechnic)  
> **Tài liệu tham chiếu:** [`reports/DATN_REPORT_FINAL_02.tex`](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/reports/DATN_REPORT_FINAL_02.tex) & Codebase [`srcs/`](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/srcs)  
> **Mục đích:** Tài liệu tra cứu độ sâu cao (High-Depth Cheatsheet & Defense Masterclass) phục vụ ôn tập, đối soát số liệu và bảo vệ đồ án trước Hội đồng chấm thi tốt nghiệp.

---

## MỤC LỤC TỔNG QUAN

1. [PHẦN 1: BỘ CHỈ SỐ QUẢN TRỊ HIỆU SUẤT & KINH DOANH QUANG ĐIỆN (SOLAR DOMAIN & KPIS)](#phần-1-bộ-chỉ-số-quản-trị-hiệu-suất--kinh-doanh-quang-điện-solar-domain--kpis)
2. [PHẦN 2: THUẬT TOÁN THIÊN VĂN HỌC & TIỀN XỬ LÝ DỮ LIỆU VẬT LÝ (ASTRONOMICAL & PHYSICS)](#phần-2-thuật-toán-thiên-văn-học--tiền-xử-lý-dữ-liệu-vật-lý-astronomical--physics)
3. [PHẦN 3: THUẬT TOÁN ĐIỀN KHUYẾT NHÂN QUẢ ĐA TẦNG & KẸP TRẦN CÔNG SUẤT (HYBRID IMPUTATION & CLAMPING)](#phần-3-thuật-toán-điền-khuyết-nhân-quả-đa-tầng--kẹp-trần-công-suất-hybrid-imputation--clamping)
4. [PHẦN 4: PHÂN LỚP LAI GMM--IF & 5 RÀO CHẮN DỊ THƯỜNG VẬT LÝ (ANOMALY DETECTION & GMM-IF)](#phần-4-phân-lớp-lai-gmm--if--5-rào-chắn-dị-thường-vật-lý-anomaly-detection--gmm-if)
5. [PHẦN 5: BIẾN ĐỔI ĐẶC TRƯNG, HÌNH HỌC MẶT TRỜI & TRỜI QUANG (FEATURE ENGINEERING & SOLAR GEOMETRY)](#phần-5-biến-đổi-đặc-trưng-hình-học-mặt-trời--trời-quang-feature-engineering--solar-geometry)
6. [PHẦN 6: CHUẨN HÓA MỤC TIÊU VẬT LÝ & KHỬ LỆCH PHA THỜI GIAN (TARGET NORMALIZATION & PHASE DELAY)](#phần-6-chuẩn-hóa-mục-tiêu-vật-lý--khử-lệch-pha-thời-gian-target-normalization--phase-delay)
7. [PHẦN 7: BỘ THƯỚC ĐO ĐÁNH GIÁ MÔ HÌNH HỌC MÁY & ĐÓNG GÓP ĐẶC TRƯNG SHAP (EVALUATION METRICS & SHAP)](#phần-7-bộ-thước-đo-đánh-giá-mô-hình-học-máy--đóng-góp-đặc-trưng-shap-evaluation-metrics--shap)
8. [PHẦN 8: HỆ THỐNG TRƯỜNG TÍNH TOÁN TABLEAU DASHBOARDS 1, 2, 3 (TABLEAU CALCULATED FIELDS)](#phần-8-hệ-thống-trường-tính-toán-tableau-dashboards-1-2-3-tableau-calculated-fields)
9. [PHẦN 9: BẢNG TRA CỨU NHANH KÝ HIỆU & ĐƠN VỊ TOÀN DỰ ÁN (MASTER SYMBOLS & UNITS)](#phần-9-bảng-tra-cứu-nhanh-ký-hiệu--đơn-vị-toàn-dự-án-master-symbols--units)

---

# PHẦN 1: BỘ CHỈ SỐ QUẢN TRỊ HIỆU SUẤT & KINH DOANH QUANG ĐIỆN (SOLAR DOMAIN & KPIS)

### 1.1. Hệ số Hiệu suất (Performance Ratio — PR)
* **Công thức toán học:**
  $$\text{PR} = \frac{E_{\text{actual}}}{\sum P_{\text{stc}} \times \left(\frac{GHI}{1000\,\text{W/m}^2}\right) \times \Delta t} \times 100\% = \frac{Y_f}{Y_r} \times 100\%$$
* **Bảng giải nghĩa thành phần:**

| Ký hiệu | Tên gọi thành phần | Đơn vị | Miền giá trị chuẩn | Ý nghĩa kỹ thuật & nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- |
| $\text{PR}$ | Hệ số hiệu suất hệ thống | $\%$ | $75\% - 85\%$ | Thước đo chuẩn hóa đo lường mức độ hoàn thiện của hệ thống PV so với điều kiện bức xạ lý tưởng. $\text{PR} < 70\%$ cảnh báo suy thoái nghiêm trọng. |
| $E_{\text{actual}}$ | Sản lượng điện thực tế thu được | $\text{kWh}$ | $\ge 0$ | Tổng lượng điện xoay chiều (AC) đo đạc thực tế phát ra tại đồng hồ/biến tần. |
| $P_{\text{stc}}$ | Công suất danh định STC của trạm | $\text{kWp}$ | $10 - 500\,\text{kWp}$ | Công suất đỉnh cực đại được chứng nhận ở Điều kiện Thử nghiệm Tiêu chuẩn (STC: Bức xạ $1000\,\text{W/m}^2$, nhiệt độ cell $25^\circ\text{C}$, Air Mass AM 1.5). |
| $GHI$ | Bức xạ tổng cộng mặt phẳng ngang | $\text{W/m}^2$ | $0 - 1400\,\text{W/m}^2$ | Cường độ năng lượng ánh sáng mặt trời chiếu tới bề mặt nằm ngang. |
| $1000\,\text{W/m}^2$ | Bức xạ tham chiếu tiêu chuẩn | $\text{W/m}^2$ | Hằng số | Bức xạ quy ước chuẩn quốc tế STC ($1\,\text{kW/m}^2$). |
| $\Delta t$ | Khoảng thời gian tích phân | $\text{giờ (h)}$ | $0{,}25\,\text{h}$ (15p) / $1\,\text{h}$ | Bước thời gian quan trắc đo đạc. |
| $Y_f$ | Final Yield (Năng suất phát thực) | $\text{kWh/kWp}$ | $\ge 0$ | $Y_f = E_{\text{actual}} / P_{\text{stc}}$ — Tương đương số giờ nắng hiệu dụng thực tế. |
| $Y_r$ | Reference Yield (Năng suất tham chiếu) | $\text{giờ (h)}$ | $\ge 0$ | $Y_r = (GHI / 1000) \times \Delta t$ — Số giờ nắng đỉnh tương đương lý thuyết (*Peak Sun Hours*). |

* **Góc nhìn Phản biện Hội đồng (Defense Insight):**  
  PR độc lập với quy mô công suất trạm. Khi bức xạ mép mây khuếch đại (*Cloud Enhancement*), PR tức thời 15p có thể vọt lên $> 100\%$, nhưng PR tích lũy trung bình tháng luôn nằm trong dải $75\% - 85\%$.

---

### 1.2. Hệ số Huy động Công suất (Capacity Factor — CF)
* **Công thức toán học:**
  $$\text{CF} = \frac{\sum E_{\text{actual}}}{P_{\text{stc}} \times T_{\text{total}}} \times 100\% = \frac{\sum E_{\text{actual}}}{P_{\text{stc}} \times 8760\,\text{h}} \times 100\% \quad (\text{tính theo năm})$$
* **Bảng giải nghĩa thành phần:**

| Ký hiệu | Tên gọi thành phần | Đơn vị | Miền giá trị chuẩn | Ý nghĩa kỹ thuật & nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- |
| $\text{CF}$ | Hệ số công suất trạm | $\%$ | $15\% - 22\%$ (Solar) | Tỷ lệ giữa sản lượng điện thực phát so với kịch bản trạm phát liên tục $100\%$ công suất danh định suốt $24/24\text{h}$. |
| $T_{\text{total}}$ | Tổng số giờ trong chu kỳ tính | $\text{giờ (h)}$ | $8760\,\text{h}$ (năm) / $720\,\text{h}$ (tháng) | Tổng thời gian vật lý (bao gồm cả ngày và đêm). |

* **Góc nhìn Phản biện Hội đồng (Defense Insight):**  
  Do ban đêm mặt trời không chiếu sáng (chiếm $\approx 50\%$ thời gian), CF của điện mặt trời tự nhiên bị chặn trên ở mức $< 30\%$. Tại bang Victoria (Úc), $\text{CF} \approx 16\% - 19\%$ là mức hiệu quả xuất sắc.

---

### 1.3. Năng suất Riêng (Specific Yield / Final Yield — $Y_f$)
* **Công thức toán học:**
  $$\text{Specific Yield} = \frac{E_{\text{actual}}}{P_{\text{stc}}} \quad (\text{kWh/kWp})$$
* **Bảng giải nghĩa thành phần:**

| Ký hiệu | Tên gọi thành phần | Đơn vị | Miền giá trị chuẩn | Ý nghĩa kỹ thuật & nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- |
| $\text{Specific Yield}$ | Năng suất riêng | $\text{kWh/kWp}$ | $3{,}5 - 5{,}5\,\text{kWh/kWp/ngày}$ | Lượng điện năng tạo ra trên mỗi đơn vị công suất lắp đặt. |

* **Ý nghĩa thực tế:** Giúp so sánh công bằng hiệu quả của trạm nhỏ $10\,\text{kWp}$ (nhà kho) với trạm lớn $500\,\text{kWp}$ (sân vận động/tòa nhà trung tâm).

---

### 1.4. Tổn thất Suy hao do Nhiệt độ (Thermal Loss)
* **Công thức toán học:**
  $$E_{\text{loss, temp}} = E_{\text{theo}} \times |\gamma| \times \max(0, T_{\text{cell}} - 25^\circ\text{C})$$
  $$T_{\text{cell}} \approx T_{\text{ambient}} + \left( \frac{\text{NOCT} - 20^\circ\text{C}}{800} \right) \times GHI$$
* **Bảng giải nghĩa thành phần:**

| Ký hiệu | Tên gọi thành phần | Đơn vị | Miền giá trị chuẩn | Ý nghĩa kỹ thuật & nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- |
| $E_{\text{loss, temp}}$ | Sản lượng suy giảm do nhiệt độ | $\text{kWh}$ | $\ge 0$ (chiếm $\approx 14{,}8\%$) | Năng lượng bị thất thoát do hiệu ứng kích thích nhiệt làm giảm dải vùng cấm bán dẫn của tấm pin. |
| $E_{\text{theo}}$ | Sản lượng lý thuyết theo bức xạ | $\text{kWh}$ | $\ge 0$ | Sản lượng kỳ vọng nếu pin duy trì ở mức chuẩn $25^\circ\text{C}$. |
| $\gamma$ | Hệ số suy giảm nhiệt độ công suất | $\%/^\circ\text{C}$ | $-0{,}35\% \to -0{,}42\%/^\circ\text{C}$ | Đặc tính vật lý của tấm pin quang điện Silicon (dự án lấy chuẩn $\gamma = -0{,}38\%/^\circ\text{C}$). |
| $T_{\text{cell}}$ | Nhiệt độ thực tế của tế bào quang điện | $^\circ\text{C}$ | $45^\circ\text{C} - 65^\circ\text{C}$ (giữa trưa) | Nhiệt độ bên trong tấm pin (nóng hơn nhiệt độ môi trường từ $20 - 30^\circ\text{C}$). |
| $\text{NOCT}$ | Nhiệt độ vận hành danh định của cell | $^\circ\text{C}$ | $45^\circ\text{C} \pm 2^\circ\text{C}$ | Nominal Operating Cell Temperature (ở bức xạ $800\,\text{W/m}^2$, gió $1\,\text{m/s}$, môi trường $20^\circ\text{C}$). |

---

### 1.5. Tổn thất Xén Công suất Biến tần (Inverter Clipping Loss)
* **Công thức toán học:**
  $$E_{\text{loss, clip}} = \max\Big(0,\ \big(P_{\text{dc\_in}} \cdot \eta_{\text{inv}} - P_{\text{ac\_max}}\big) \times \Delta t\Big)$$
* **Ý nghĩa:** Khi dàn pin DC phát công suất vượt quá định mức AC cực đại của bộ biến tần (tỷ lệ DC/AC Overclocking $1{,}15 - 1{,}30$), thuật toán MPPT chủ động dịch điểm làm việc để xén bớt công suất (gây mất mát $\approx 2{,}3\%$ sản lượng, nhưng bảo vệ an toàn cho Inverter).

---

### 1.6. Doanh thu Thất thoát & Tối ưu Tài chính O&M (Financial Metrics)
* **Doanh thu Thất thoát (Lost Revenue):**
  $$\text{Lost Revenue (AUD)} = \sum E_{\text{loss}} \times \text{FiT}$$
  *(Trong đó $\text{FiT} \approx 0{,}05 - 0{,}07\,\text{AUD/kWh}$ là biểu giá bán điện mặt trời FiT Feed-in Tariff tại bang Victoria).*
* **Tỷ suất Hoàn vốn Đầu tư O&M (Return on Investment — ROI):**
  $$\text{ROI} = \frac{\text{Doanh thu Cứu vãn (AUD)} - \text{Chi phí O\&M (AUD)}}{\text{Chi phí O\&M (AUD)}} \times 100\% \quad (\text{Dự án đạt } > 270\%)$$
* **Thời gian Hoàn vốn (Payback Period):**
  $$\text{Payback Period} = \frac{\text{Chi phí Đầu tư O\&M Ban đầu}}{\text{Lợi ích Tiết kiệm Ròng Hàng tháng}} \quad (\text{Dự án đạt } < 4{,}5\text{ tháng})$$

---

# PHẦN 2: THUẬT TOÁN THIÊN VĂN HỌC & TIỀN XỬ LÝ DỮ LIỆU VẬT LÝ (ASTRONOMICAL & PHYSICS)

### 2.1. Chuỗi Phương trình Lượng giác Cầu Định vị Mặt Trời (NOAA / ERA5-Land)

Thuật toán tính toán vị trí nhật tâm/địa tâm trải qua 4 bước:

#### Bước 1: Góc năm phân số ($\gamma$, Fractional Year)
$$\gamma = \frac{2\pi}{365} \left( DOY - 1 + \frac{Hour_{\text{UTC}} - 12}{24} \right) \quad (\text{radian})$$
* $DOY \in [1, 366]$: Ngày thứ mấy trong năm (*Day of Year*).
* $Hour_{\text{UTC}} \in [0, 24)$: Giờ quốc tế phối hợp.

#### Bước 2: Phương trình Thời gian ($EoT$) & Độ Xích vĩ Mặt Trời ($\delta$)
$$\begin{aligned}
EoT &= 229{,}18 \times \big( 0{,}000075 + 0{,}001868\cos\gamma - 0{,}032077\sin\gamma \\
    &\quad - 0{,}014615\cos 2\gamma - 0{,}040849\sin 2\gamma \big) \quad (\text{phút})
\end{aligned}$$
$$\begin{aligned}
\delta &= 0{,}006918 - 0{,}399912\cos\gamma + 0{,}070257\sin\gamma - 0{,}006758\cos 2\gamma \\
       &\quad + 0{,}000907\sin 2\gamma - 0{,}002697\cos 3\gamma + 0{,}00148\sin 3\gamma \quad (\text{radian})
\end{aligned}$$
* $EoT$: Bù trừ độ lệch thời gian do quỹ đạo Trái Đất hình elip và độ nghiêng trục tự quay ($[-14{,}2; +16{,}4]\,\text{phút}$).
* $\delta$: Góc nghiêng giữa tia sáng mặt trời và mặt phẳng xích đạo Trái Đất ($[-23{,}44^\circ; +23{,}44^\circ]$).

#### Bước 3: Giờ Mặt Trời Thực ($TST$) & Góc Giờ ($\omega$)
$$\Delta t = EoT + 4\lambda - 60 \cdot TZ \implies TST = (Hour_{\text{local}} \times 60 + Minute) + \Delta t \quad (\text{phút})$$
$$\omega = \left( \frac{TST}{4} \right) - 180^\circ \quad (\text{độ})$$
* $\lambda$: Kinh độ địa lý trạm phát ($^\circ\text{E}$). $4\lambda$: Mỗi độ kinh tuyến lệch 4 phút giờ mặt trời.
* $TZ$: Múi giờ địa phương ($TZ = +10$ hoặc $+11$ theo giờ mùa hè AEDT).
* $\omega$: Góc quay của Trái Đất quanh trục tính từ chính trưa ($TST = 720\,\text{phút} \implies \omega = 0^\circ$).

#### Bước 4: Góc Nâng Mặt Trời ($\alpha$) & Cờ Nhị phân $\texttt{is\_day}$
$$\sin\alpha = \sin\phi \cdot \sin\delta + \cos\phi \cdot \cos\delta \cdot \cos\omega \implies \alpha = \arcsin(\sin\alpha)$$
$$\texttt{is\_day} = \begin{cases}
1 & \text{khi } \alpha > -0{,}833^\circ \quad (\text{Ban ngày: Mặt Trời trên đường chân trời}) \\
0 & \text{khi } \alpha \le -0{,}833^\circ \quad (\text{Ban đêm: Mặt Trời lặn dưới chân trời})
\end{cases}$$
* $\phi$: Vĩ độ địa lý trạm phát ($^\circ\text{S}$).
* $-0{,}833^\circ$: Ngưỡng góc nâng hiệu chỉnh hiện tượng khúc xạ khí quyển sát chân trời ($34' \approx 0{,}566^\circ$) cộng với bán kính góc đĩa Mặt Trời ($16' \approx 0{,}267^\circ$).

---

### 2.2. Ngưỡng Khởi động Inverter & Điều kiện Gán Không Vật lý ($\text{Condition}_{\text{Zero}}$)
$$\text{Condition}_{\text{Zero}} = (GHI \le 20{,}0\,\text{W/m}^2) \lor (\texttt{is\_day} == 0) \implies E_{\text{imputed}} = 0{,}0\,\text{kWh}$$
* **Nguyên lý:** Biến tần công nghiệp cần điện áp hở mạch tối thiểu $V_{\text{pv\_start}} \approx 120 - 200\,\text{V}$ để đóng rơ-le hòa lưới. Dưới $20\,\text{W/m}^2$, biến tần ở chế độ Standby/Sleep. Quy tắc này điền chính xác $1.383.493$ dòng khuyết ban đêm ($90{,}05\%$).

---

# PHẦN 3: THUẬT TOÁN ĐIỀN KHUYẾT NHÂN QUẢ ĐA TẦNG & KẸP TRẦN CÔNG SUẤT (HYBRID IMPUTATION & CLAMPING)

```
                       ┌───────────────────────────────────────────────┐
                       │   TẬP DỮ LIỆU SẢN LƯỢNG 15 PHÚT (2.73M DÒNG)  │
                       │   Khuyết thiếu: 1.536.301 ô NULL (56,23%)     │
                       └───────────────────────┬───────────────────────┘
                                               │
                                               ▼
         ┌───────────────────────────────────────────────────────────────────────────┐
         │ CẤP 1: RULE-BASED NIGHT ZERO (Bức xạ <= 20 W/m2 HOẶC is_day == 0)        │
         │ Điền: 1.383.493 dòng (90,05% NULL) --> Gán: 0.0 kWh                      │
         └─────────────────────────────────────┬─────────────────────────────────────┘
                                               │ (Còn lại: 152.808 ô NULL ban ngày)
                                               ▼
         ┌───────────────────────────────────────────────────────────────────────────┐
         │ CẤP 2: NỘI SUY TUYẾN TÍNH THỜI GIAN (Khoảng khuyết <= 2 bước = <= 30p)    │
         │ Điền: 53.684 dòng (3,49% NULL) --> clip(Linear, 0, max_physical_kwh)      │
         └─────────────────────────────────────┬─────────────────────────────────────┘
                                               │ (Còn lại: 99.124 ô NULL)
                                               ▼
         ┌───────────────────────────────────────────────────────────────────────────┐
         │ CẤP 3: PCHIP SPLINE BẢO TOÀN ĐƠN ĐIỆU (Khoảng khuyết 3 - 8 bước = 45p-2h) │
         │ Điền: 50.704 dòng (3,30% NULL) --> clip(PCHIP, 0, max_physical_kwh)       │
         └─────────────────────────────────────┬─────────────────────────────────────┘
                                               │ (Còn lại: 48.420 ô NULL)
                                               ▼
         ┌───────────────────────────────────────────────────────────────────────────┐
         │ CẤP 4: HỒI QUY ĐA BIẾN THEO TRẠM (Khoảng khuyết diện rộng > 8 bước = > 2h)│
         │ Điền: 48.420 dòng (3,15% NULL) --> clip(Regression, 0, max_physical_kwh) │
         └─────────────────────────────────────┬─────────────────────────────────────┘
                                               │
                                               ▼
         ┌───────────────────────────────────────────────────────────────────────────┐
         │ LỚP CHỐT CHẶN AN TOÀN: subset["energy"].clip(0.0, max_physical_kwh)       │
         │ NULL CÒN LẠI: 0 DÒNG (100% HOÀN TẤT) | VI PHẠM TRẦN VẬT LÝ: 0 BẢN GHI    │
         └───────────────────────────────────────────────────────────────────────────┘
```

### 3.1. Chi tiết 4 Cấp độ Điền khuyết

#### Cấp 1: Quy tắc Ban đêm & Bức xạ Dưới ngưỡng Inverter
$$E(t) = 0{,}0\,\text{kWh} \quad \text{khi } (GHI \le 20\,\text{W/m}^2) \lor (\texttt{is\_day} == 0)$$

#### Cấp 2: Nội suy Tuyến tính Thời gian Ngắn ($\le 2$ bước, $\le 30$ phút)
$$E_{\text{linear}}(t) = \text{clip}\left( E(t_a) + \frac{E(t_b) - E(t_a)}{t_b - t_a} (t - t_a),\ 0{,}0,\ max\_physical\_kwh \right)$$

#### Cấp 3: Nội suy Đa thức Hermite Bảo toàn Đơn điệu (PCHIP Spline, $3 - 8$ bước)
$$P(x) = y_k h_{00}(t) + y_{k+1} h_{01}(t) + d_k \Delta x_k h_{10}(t) + d_{k+1} \Delta x_k h_{11}(t)$$
$$E_{\text{pchip}}(t) = \text{clip}\Big( P(t),\ 0{,}0,\ max\_physical\_kwh \Big)$$
* $h_{ij}(t)$: Các hàm đa thức cơ sở Hermite bậc 3.
* $d_k$: Đạo hàm tiếp tuyến bảo toàn tính đơn điệu (triệt tiêu $100\%$ dao động Runge và hiện tượng võng âm dưới $0\,\text{kWh}$).

#### Cấp 4: Hồi quy Tuyến tính Đa biến Theo Trạm ($> 8$ bước, $> 2$ giờ)
$$\hat{E}(t) = \beta_0 + \beta_1 \cdot GHI(t) + \beta_2 \cdot DNI(t) + \beta_3 \cdot DHI(t) + \beta_4 \cdot T_{\text{ambient}}(t)$$
$$E_{\text{reg}}(t) = \text{clip}\Big( \hat{E}(t),\ 0{,}0,\ max\_physical\_kwh \Big)$$

---

### 3.2. Cơ chế Kẹp trần Công suất Vật lý Động ($max\_physical\_kwh$)
* **Công thức toán học:**
  $$max\_physical\_kwh(s) = P_{\text{stc}}(s) \times 0{,}25\,\text{h} \times 1{,}20 \quad (\text{kWh})$$
* **Bảng giải nghĩa tham số:**

| Tham số | Giá trị | Ý nghĩa kỹ thuật |
| :--- | :--- | :--- |
| $P_{\text{stc}}(s)$ | Đọc động từ `dim_solar_site` | Công suất danh định STC riêng của từng trạm $s$ (từ $10 - 500\,\text{kWp}$). |
| $0{,}25\,\text{h}$ | $15 / 60\text{ giờ}$ | Tích phân thời gian chu kỳ 15 phút ($E = P \times \Delta t$). |
| $1{,}20\times$ | Hệ số dung sai $20\%$ | Cho phép biên độ an toàn trước hiện tượng mép mây (*Cloud Enhancement*), quán tính nhiệt pin lạnh, và khả năng quá tải AC của biến tần theo tiêu chuẩn AS/NZS 4777.2. |

---

# PHẦN 4: PHÂN LỚP LAI GMM--IF & 5 RÀO CHẮN DỊ THƯỜNG VẬT LÝ (ANOMALY DETECTION & GMM-IF)

### 4.1. Cơ chế Hợp nhất Đồng thuận (Fusion Consensus $GMM \wedge IF$)
$$\text{Flag}_{\text{ML}} = \text{Flag}_{\text{GMM}} \wedge \text{Flag}_{\text{IF}}$$
* **GMM (Gaussian Mixture Model):** Phân đoạn lá cây quyết định ($R^2 \approx 0{,}758$), mô hình hóa mật độ xác suất $p(x) = \sum_{k=1}^2 \pi_k \mathcal{N}(x | \mu_k, \Sigma_k)$. Gắn cờ khi $p(x) < 0{,}02$.
* **IF (Isolation Forest):** 100 cây ngẫu nhiên, đo độ sâu trung bình $E(h(x))$ để cô lập điểm. Gắn cờ khi điểm dị thường $s(x, n) = 2^{-\frac{\mathbb{E}(h(x))}{c(n)}}$ thuộc top $3\%$.
* **Tỷ lệ sống sót qua phép giao:** Chỉ $17{,}72\%$ ứng viên GMM và $17{,}35\%$ ứng viên IF được giữ lại ($6.102$ dòng), loại bỏ $> 82\%$ cảnh báo giả.

---

### 4.2. Bảng Công thức 5 Rào chắn Dị thường Vật lý

| Mã Lý do Dị thường | Biểu thức Điều kiện Kỹ thuật | Ngưỡng Tham số | Ý nghĩa Nghiệp vụ & Chẩn đoán |
| :--- | :--- | :--- | :--- |
| `PHYSICAL_OVER_CAPACITY` | $E > P_{\text{stc}} \times 0{,}25\,\text{h} \times 1{,}20$ | $1{,}20 \times P_{\text{stc}}$ | Xung điện lưới, lỗi telemetry hoặc sai lệch siêu dữ liệu trạm. |
| `PHYSICAL_HIGH_ENERGY_NO_SUN` | $GHI \le 25\,\text{W/m}^2 \land \text{sunshine} \le 60\text{s} \land E \ge \max(1{,}0,\ 0{,}20 \cdot P_{\text{stc}})$ | $E \ge 20\% P_{\text{stc}}$ | Dòng rò ban đêm (Night Leakage) hoặc trôi điểm 0 cảm biến dòng CT. |
| `PHYSICAL_HIGH_ENERGY_LOW_RAD` | $GHI \le 50\,\text{W/m}^2 \land E \ge \max(1{,}0,\ 0{,}20 \cdot P_{\text{stc}}) \land E > Q_3 + 4 \cdot \text{IQR}$ | Phân vị nhóm bức xạ $+ 4\,\text{IQR}$ | Dị thường đuôi sâu khi bức xạ yếu; sai lệch đồng bộ thời gian. |
| `PHYSICAL_LOW_ENERGY_STRONG_SUN` | $GHI \ge 700\,\text{W/m}^2 \land \text{sunshine} \ge 3000\text{s} \land E \le 0{,}05 \cdot P_{95} \land E \le Q_1 - 2 \cdot \text{IQR}$ | $E \le 5\% P_{95}$ | Biến tần ngắt quá nhiệt (Inverter Trip), hỏng diode bypass hoặc che bóng diện rộng. |
| `PHYSICAL_DISTRIBUTION_JUMP` | Bỏ qua giờ chuyển tiếp (05h, 06h, 18h): $\|E - E_{\text{neighbor}}\| \ge \max(0{,}15 \cdot P_{95}, 1{,}0) \land E \notin [Q_1 - 4\text{IQR}, Q_3 + 4\text{IQR}]$ | Bước nhảy cục bộ $2\text{h}$ lân cận | Spike tín hiệu cảm biến hoặc dropout viễn thông Modbus. |

* **Định nghĩa Khoảng Tứ phân vị (IQR):**
  $$\text{IQR} = Q_3 (75th) - Q_1 (25th)$$

---

# PHẦN 5: BIẾN ĐỔI ĐẶC TRƯNG, HÌNH HỌC MẶT TRỜI & TRỜI QUANG (FEATURE ENGINEERING & SOLAR GEOMETRY)

### 5.1. Đồng bộ Độ chi tiết Dữ liệu (Temporal Granularity Aggregation: 15p $\rightarrow$ 1h)
$$E_{\text{hour}} = \sum_{i=1}^{4} E_{15\text{min}, i} \quad (\text{kWh})$$
* Dữ liệu thời tiết Open-Meteo có chu kỳ $1\,\text{h}$ được kết nối chính xác vào mốc chẵn giờ, loại bỏ hoàn toàn rò rỉ dữ liệu tương lai (*Lookahead Bias*).

---

### 5.2. Mã hóa Đặc trưng Chu kỳ Tuần hoàn (Cyclic Sine/Cosine Encoding)
$$\text{hour\_sin} = \sin\left(\frac{2\pi \cdot \text{hour}}{24}\right), \quad \text{hour\_cos} = \cos\left(\frac{2\pi \cdot \text{hour}}{24}\right)$$
$$\text{month\_sin} = \sin\left(\frac{2\pi \cdot \text{month}}{12}\right), \quad \text{month\_cos} = \cos\left(\frac{2\pi \cdot \text{month}}{12}\right)$$
$$\text{azimuth\_sin} = \sin(\theta_{\text{azimuth}}), \quad \text{azimuth\_cos} = \cos(\theta_{\text{azimuth}})$$
* **Ý nghĩa:** Biến đổi thang đo gián đoạn ($23\text{h}$ sang $0\text{h}$, tháng 12 sang tháng 1, góc $359^\circ$ sang $0^\circ$) thành không gian tọa độ tròn liên tục, bảo toàn khoảng cách Euclid cho cây quyết định LightGBM.

---

### 5.3. Bức xạ Trời quang theo Mô hình Haurwitz (Clear Sky Irradiance — $GHI_{cs}$)
$$GHI_{cs} = 1098 \times \sin(h) \times \exp\left(-\frac{0{,}059}{\sin(h)}\right) \times \text{cs\_factor} \quad (\text{W/m}^2)$$
* $h$: Góc cao Mặt Trời ($\sin h = \sin\alpha$).
* $\text{cs\_factor}$: Hệ số hiệu chỉnh độ trong khí quyển riêng của từng fold trạm ($1{,}460 \to 1{,}557$).
* **Chỉ số Trời quang (Clear Sky Index — $CSI$):**
  $$CSI = \frac{GHI_{\text{measured}}}{GHI_{cs}}$$
  *$CSI \ge 1{,}20$ phản ánh hiện tượng khuếch đại mép mây (Cloud Enhancement).*

---

# PHẦN 6: CHUẨN HÓA MỤC TIÊU VẬT LÝ & KHỬ LỆCH PHA THỜI GIAN (TARGET NORMALIZATION & PHASE DELAY)

### 6.1. Chuẩn hóa Mục tiêu Phi thứ nguyên ($k_{\text{target}}$)
$$k_{\text{target}} = \operatorname{clip}\left( \frac{y}{\texttt{site\_scale} \times \max(\sin h,\ \varepsilon)},\ 0,\ k_{\max} \right)$$
* **Khôi phục Sản lượng Dự báo ($\hat{y}$):**
  $$\hat{y} = \min\left( \hat{k} \times \texttt{site\_scale} \times \max(\sin h,\ \varepsilon),\ \ \texttt{tran\_cong\_suat} \times 1{,}02 \right)$$

* **Bảng giải nghĩa các tham số tối ưu:**

| Tham số | Giá trị | Ý nghĩa kỹ thuật |
| :--- | :--- | :--- |
| $\texttt{site\_scale}$ | Phân vị 95 trạm ($P_{95}$) | Khử khác biệt về quy mô công suất giữa 42 trạm ($10 - 500\,\text{kWp}$). |
| $\sin h$ | $\sin(\text{Góc cao mặt trời})$ | Khử đường cong nhật quỹ ngày đêm tự nhiên. |
| $\varepsilon$ | $0{,}05$ ($\alpha \approx 2{,}87^\circ$) | Đặt sàn cho mẫu số, loại bỏ $0{,}054\%$ sản lượng sát chân trời tránh nổ số học ($k \to \infty$). |
| $k_{\max}$ | $1{,}3764$ (Phân vị 99 train) | Cận cắt chặn đuôi phân phối dị thường, cải thiện $2{,}76\%$ WAPE. |
| $1{,}02\times$ | Nới trần $2\%$ | Chừa dư địa cho dao động bức xạ ngắn hạn ở mép mây. |

---

### 6.2. Đo lường Độ trễ Pha Tiếp tuyến Sai số (Phase Delay Metric)
$$\text{Độ trễ (phút)} = -\,\frac{\sum_t d_t \cdot e_t}{\sum_t d_t^2} \times 15$$
$$d_t = \frac{y_{t+1} - y_{t-1}}{2} \quad (\text{Độ dốc tiếp tuyến thực tế})$$
$$e_t = \hat{y}_t - y_t \quad (\text{Sai số dự báo})$$
* **Ý nghĩa:** Tách bạch hoàn toàn **sai số biên độ** khỏi **sai số thời điểm**.
* **Kết quả:** Mô hình LightGBM loại bỏ `lag_1` và sử dụng `lag_4, lag_96` đạt độ trễ $+2{,}46\,\text{phút}$ (thỏa mãn ngưỡng $\pm 5{,}0\,\text{phút}$ của cổng kiểm định).

---

# PHẦN 7: BỘ THƯỚC ĐO ĐÁNH GIÁ MÔ HÌNH HỌC MÁY & ĐÓNG GÓP ĐẶC TRƯNG SHAP (EVALUATION METRICS & SHAP)

### 7.1. Bảng Tổng hợp Thước đo Đánh giá Mô hình

| Tên Thước đo | Biểu thức Toán học | Đơn vị | Ý nghĩa Kỹ thuật & Ưu điểm vượt trội |
| :--- | :--- | :--- | :--- |
| **WAPE** (Weighted Absolute Percentage Error) | $\text{WAPE} = \frac{\sum_i \|y_i - \hat{y}_i\|}{\sum_i \|y_i\|} \times 100\%$ | $\%$ | **Thước đo cốt lõi của đồ án.** Không bị nổ số học khi $y \to 0$ (khắc phục nhược điểm của MAPE); tự động gán trọng số theo quy mô công suất trạm. |
| **MAE** (Mean Absolute Error) | $\text{MAE} = \frac{1}{N}\sum_{i=1}^N \|y_i - \hat{y}_i\|$ | $\text{kWh}$ | Sai số trung bình tuyệt đối tính bằng đơn vị sản lượng thực tế. |
| **RMSE** (Root Mean Squared Error) | $\text{RMSE} = \sqrt{\frac{1}{N}\sum_{i=1}^N (y_i - \hat{y}_i)^2}$ | $\text{kWh}$ | Nhạy cảm với các sai số lớn; đo lường độ phân tán phương sai sai số. |
| **$R^2$** (Coefficient of Determination) | $R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$ | Không đ/v ($[- \infty, 1]$) | Tỷ lệ phương sai của sản lượng được mô hình giải thích. Dự án đạt $R^2 \approx 0{,}891$. |
| **Skill Score** ($SS$) | $SS = \left( 1 - \frac{\text{WAPE}_{\text{LightGBM}}}{\text{WAPE}_{\text{Prophet}}} \right) \times 100\%$ | $\%$ | Đo lường tỷ lệ phần trăm cải thiện sai số so với mô hình cơ sở Facebook Prophet ($SS > 0$). |

* **Kết quả Kiểm định Test Niêm phong:**
  - $\text{WAPE}_{\text{H1}} (15\text{p}) = \mathbf{17{,}74\%}$
  - $\text{WAPE}_{\text{H4}} (60\text{p}) = \mathbf{22{,}62\%}$
  - $\text{Skill Score} = \mathbf{+58{,}2\%}$ (vượt trội hoàn toàn so với mô hình chuỗi thời gian truyền thống).

---

### 7.2. Giá trị Đóng góp Đặc trưng SHAP (Shapley Additive exPlanations)
$$\phi_i(x) = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!\ (|F| - |S| - 1)!}{|F|!} \Big[ f_x(S \cup \{i\}) - f_x(S) \Big]$$
* $\phi_i(x)$: Đóng góp biên trung bình của đặc trưng thứ $i$ vào kết quả dự báo.
* $F$: Tập hợp toàn bộ 53 đặc trưng đầu vào.
* $S$: Tập hợp con các đặc trưng loại trừ đặc trưng $i$.
* **Khám phá SHAP trong dự án:**
  - **Top 1:** Bức xạ sóng ngắn ($GHI$) và Bức xạ trời quang ($GHI_{cs}$) đóng góp $> 60\%$ sức mạnh dự báo.
  - **Top 2:** Nhiệt độ môi trường $T_{\text{ambient}}$ mang giá trị SHAP âm khi $GHI$ cao (minh chứng định lượng cho tổn thất nhiệt $14{,}8\%$).
  - **Top 3:** Đặc trưng trễ không gian (`spatial_lag`) hỗ trợ nhận diện hướng di chuyển của các đám mây giữa các trạm lân cận.

---

# PHẦN 8: HỆ THỐNG TRƯỜNG TÍNH TOÁN TABLEAU DASHBOARDS 1, 2, 3 (TABLEAU CALCULATED FIELDS)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                          TABLEAU DESKTOP BI CALCULATION MATRIX                              │
├────────────────────────────────┬────────────────────────────────────────────────────────────┤
│ Tên Measure trong Tableau      │ Cú pháp Công thức Tableau Calculation (DAX / SQL)          │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ [PR Actual %]                  │ SUM([Energy Generated Kwh]) /                              │
│                                │ SUM([Theoretical Energy Kwh]) * 100                        │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ [Specific Yield kWh/kWp]       │ SUM([Energy Generated Kwh]) / ATTR([Capacity Kw])          │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ [Capacity Factor %]            │ SUM([Energy Generated Kwh]) /                              │
│                                │ (ATTR([Capacity Kw]) * 24 * COUNTD([Date])) * 100          │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ [Theoretical Energy Kwh]       │ (ATTR([Capacity Kw]) * [Ghi] / 1000) * 0.25                │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ [Thermal Loss Kwh]             │ SUM([Theoretical Energy Kwh]) * 0.0038 *                   │
│                                │ MAX(0, AVG([Temperature 2m]) + 25 - 25)                   │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ [Inverter Clipping Loss Kwh]   │ SUM(IF [Gmm If Outlier Reason] =                           │
│                                │ 'PHYSICAL_LOW_ENERGY_STRONG_SUN'                           │
│                                │ THEN [Theoretical Energy Kwh] - [Energy Generated Kwh]    │
│                                │ ELSE 0 END)                                                │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ [Outlier Rate %]               │ COUNTD(IF [Gmm If Outlier Flag] = TRUE THEN [Gen Id] END)  │
│                                │ / COUNTD([Gen Id]) * 100                                   │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ [Lost Revenue AUD]             │ SUM([Energy Lost Kwh]) * [FiT Tariff AUD]                  │
├────────────────────────────────┼────────────────────────────────────────────────────────────┤
│ [Outlier Hours MoM %]          │ (ZN(SUM([Outlier Hours])) -                                │
│                                │ LOOKUP(ZN(SUM([Outlier Hours])), -1)) /                    │
│                                │ ABS(LOOKUP(ZN(SUM([Outlier Hours])), -1)) * 100            │
└────────────────────────────────┴────────────────────────────────────────────────────────────┘
```

---

# PHẦN 9: BẢNG TRA CỨU NHANH KÝ HIỆU & ĐƠN VỊ TOÀN DỰ ÁN (MASTER SYMBOLS & UNITS)

| Ký hiệu | Tên gọi chuẩn học thuật | Đơn vị tiêu chuẩn | Phạm vi giá trị | Xuất hiện tại Chương/Module |
| :--- | :--- | :--- | :--- | :--- |
| $E_{\text{actual}}$ | Sản lượng điện phát thực tế | $\text{kWh}$ | $\ge 0$ | Toàn bộ dự án |
| $P_{\text{stc}}$ | Công suất danh định STC | $\text{kWp}$ / $\text{kW}$ | $10 - 500\,\text{kWp}$ | `dim_solar_site` / ETL |
| $GHI$ | Bức xạ tổng cộng mặt phẳng ngang | $\text{W/m}^2$ | $0 - 1400\,\text{W/m}^2$ | `fact_weather` / ETL |
| $DNI$ | Bức xạ trực xạ pháp tuyến | $\text{W/m}^2$ | $0 - 1100\,\text{W/m}^2$ | `fact_weather` / ML |
| $DHI$ | Bức xạ tán xạ bầu trời | $\text{W/m}^2$ | $0 - 600\,\text{W/m}^2$ | `fact_weather` / ML |
| $GHI_{cs}$ | Bức xạ ngang trời quang lý thuyết | $\text{W/m}^2$ | $\ge 0$ | Feature Engineering |
| $T_{\text{ambient}}$ | Nhiệt độ không khí ở độ cao 2m | $^\circ\text{C}$ | $-5^\circ\text{C} \to 45^\circ\text{C}$ | `fact_weather` |
| $T_{\text{cell}}$ | Nhiệt độ bề mặt tấm pin quang điện | $^\circ\text{C}$ | $10^\circ\text{C} \to 70^\circ\text{C}$ | Chẩn đoán suy hao nhiệt |
| $\alpha$ / $h$ | Góc nâng / độ cao Mặt Trời | độ ($^\circ$) / radian | $-90^\circ \to +90^\circ$ | Astronomical Algorithm |
| $\theta_{\text{azimuth}}$ | Góc phương vị Mặt Trời | độ ($^\circ$) | $0^\circ \to 360^\circ$ | Solar Geometry |
| $\gamma$ | Hệ số suy giảm công suất theo nhiệt độ | $\%/^\circ\text{C}$ | $-0{,}38\%/^\circ\text{C}$ | Báo cáo Chẩn đoán KPI |
| $k_{\text{target}}$ | Hệ số sản lượng chuẩn hóa phi thứ nguyên | Không đ/v | $[0{,}0;\ 1{,}3764]$ | ML Target Pipeline |
| $SS$ | Forecast Skill Score | $\%$ | $[- \infty, 100\%]$ | ML Evaluation |
| $\text{FiT}$ | Feed-in Tariff (Giá bán điện) | $\text{AUD/kWh}$ | $0{,}05 - 0{,}07\,\text{AUD}$ | BI Mart / ROI |
| $WAPE$ | Weighted Absolute Percentage Error | $\%$ | $17{,}74\% \to 22{,}62\%$ | ML Metric |

---

> [!TIP]
> **Lời khuyên khi Bảo vệ trước Hội đồng:**
> - Khi được hỏi về **"Tại sao PR có lúc $> 100\%$?"**: Hãy dẫn ngay công thức Mục 1.1 và giải thích hiện tượng mép mây *Cloud Enhancement* kết hợp quán tính nhiệt pin lạnh làm bức xạ tức thời vọt lên $1.200\,\text{W/m}^2$.
> - Khi được hỏi về **"Tại sao không dùng MAPE mà dùng WAPE?"**: Dẫn Mục 7.1 giải thích mẫu số MAPE tiến về $0$ lúc bình minh/hoàng hôn làm sai số nổ tung, trong khi WAPE cộng dồn mẫu số triệt tiêu hoàn toàn lỗi này.
> - Khi được hỏi về **"Tại sao dùng PCHIP thay vì Cubic Spline?"**: Dẫn Mục 3.1 giải thích PCHIP bảo toàn tính đơn điệu, không sinh số âm và triệt tiêu dao động Runge.
> - Khi được hỏi về **"Tại sao đặt ngưỡng Clamping $1{,}20\times$?"**: Dẫn Mục 3.2 giải thích 4 căn cứ vật lý: Cloud Enhancement, Cold PV Dynamics, Albedo và tiêu chuẩn quá tải Inverter AS/NZS 4777.2.
