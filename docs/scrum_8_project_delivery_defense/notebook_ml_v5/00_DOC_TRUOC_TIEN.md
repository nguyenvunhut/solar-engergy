# Đọc trước tiên — nhánh Học máy v5 từ số 0

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy ngày 19/08 hoặc
> trưa 20/08. Giá trị **hiện hành** và lý do từng con số thay đổi được liệt kê đầy đủ ở
> [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md). Đọc file đó trước khi
> trích bất kỳ con số nào vào báo cáo.


> Viết cho người **mới học Machine Learning**, chưa biết gì về dự án này. Không cần biết
> điện mặt trời, không cần biết LightGBM. Đọc hết file này rồi mới sang các file khác.

---

## PHẦN 1 — Bài toán là gì

### 1.1. Bối cảnh vật lý

Trường Đại học La Trobe (Úc) lắp **42 dàn pin mặt trời** trên mái các toà nhà, phân bố ở
**5 khuôn viên** (Bundoora, Bendigo, Albury-Wodonga, Mildura, Shepparton).

Mỗi dàn có một đồng hồ đo, ghi lại lượng điện sản xuất **15 phút một lần**. Một ngày có
`24 × 4 = 96` mốc đo. Nhân với 42 trạm và hơn 2 năm dữ liệu → khoảng **2,7 triệu dòng**.

Song song đó, dự án mua dữ liệu thời tiết từ Open-Meteo: bức xạ mặt trời, nhiệt độ, mây, gió,
mưa — nhưng theo **từng giờ**, không phải 15 phút. Đây là điểm lệch quan trọng sẽ xuất hiện
lại nhiều lần.

### 1.2. Nhiệm vụ

> Đứng ở thời điểm **T**, chỉ dùng thông tin **đã biết tại T**, hãy dự báo sản lượng điện
> tại **T + 15 phút** (gọi tắt là **h1**) và **T + 60 phút** (**h4**).

Chữ "chỉ dùng thông tin đã biết tại T" là ràng buộc sống còn. Nếu vô tình để mô hình nhìn
thấy dữ liệu tương lai, nó sẽ cho kết quả rất đẹp trên máy nhưng vô dụng khi triển khai
thật. Trong ML người ta gọi lỗi này là **rò rỉ dữ liệu (data leakage)**, và nó là nguyên
nhân số một khiến các dự án ML thất bại khi đưa vào vận hành.

### 1.3. Vì sao bài toán khó

Trực giác đầu tiên: "mặt trời lên cao thì phát nhiều điện, cứ tính vị trí mặt trời là xong".
Sai. Số liệu thật của dự án cho thấy: **tại cùng một góc cao mặt trời**, sản lượng dao động
**4–5 lần** giữa các thời điểm khác nhau.

| Góc mặt trời (sin) | Sản lượng thấp (phân vị 10) | Trung vị | Cao (phân vị 90) | Tỷ lệ cao/thấp |
|---|---|---|---|---|
| 0,70 – 1,00 (giữa trưa) | 0,278 | 0,850 | 1,151 | **4,1 lần** |
| 0,40 – 0,70 | 0,267 | 0,783 | 1,219 | 4,6 lần |
| 0,20 – 0,40 | 0,185 | 0,493 | 0,966 | 5,2 lần |

*(Các số trong bảng là giá trị `k` — sẽ giải thích ở Phần 2.)*

Nguyên nhân của 4–5 lần chênh lệch đó là **mây**. Và mây thì không tính bằng công thức thiên
văn được — phải học từ dữ liệu. Đó là lý do dự án cần Machine Learning chứ không phải chỉ
một công thức vật lý.

---

## PHẦN 2 — Ý tưởng cốt lõi: chuẩn hoá mục tiêu

Đây là phần quan trọng nhất của toàn bộ dự án. Hiểu phần này thì hiểu tất cả.

### 2.1. Vấn đề nếu dự báo thẳng kWh

Giả sử ta bắt mô hình đoán thẳng số kWh. Mô hình sẽ phải học **ba** thứ cùng lúc:

1. Trạm này to hay nhỏ (trạm lớn phát 90 kWh/15 phút, trạm nhỏ chỉ 8 kWh).
2. Bây giờ là mấy giờ, mùa nào (trưa hè nhiều hơn chiều đông).
3. Trời hôm nay thế nào (mây hay quang).

Nhưng **hai điều đầu tiên ta đã biết trước rồi!** Quy mô trạm thì tra trong lịch sử là ra;
vị trí mặt trời lúc 14h30 ngày mai thì thiên văn học đã tính chính xác từ hàng chục năm
trước. Bắt mô hình học lại những thứ đã biết là lãng phí năng lực của nó.

### 2.2. Giải pháp: chia cho phần đã biết

Dự án định nghĩa một đại lượng mới, gọi là **k**:

```
                sản lượng đo được (kWh)
   k  =  ─────────────────────────────────────────────
          site_scale   ×   sin(góc cao mặt trời)
          └─ quy mô ─┘     └── hình học thiên văn ──┘
                    "mẫu số chuẩn hoá"
```

Trong đó:

- **`site_scale`** = phân vị 0,99 của sản lượng ban ngày của **chính trạm đó**, tính **chỉ
  trên tập huấn luyện**. Nói nôm na: "mức sản lượng cao nhất mà trạm này thường đạt được".
  Đây là **số liệu thật lấy từ dữ liệu đo**, không phải công thức lý thuyết.

- **`sin(góc cao mặt trời)`** = mặt trời đang cao bao nhiêu trên đường chân trời. Bằng 1 khi
  mặt trời ngay đỉnh đầu, bằng 0 khi ở đường chân trời. Tính bằng thư viện `pvlib` theo
  thuật toán chuẩn của Phòng thí nghiệm Năng lượng Tái tạo Quốc gia Mỹ (NREL).

### 2.3. Ví dụ số thật — trạm 27, ngày 15/01/2021

| Giờ | Sản lượng đo (kWh) | site_scale | sin(góc cao) | Mẫu số | **k** | Nhân ngược lại |
|---|---|---|---|---|---|---|
| 10:00 | 30,8125 | 97,1875 | 0,6720 | 65,3073 | **0,4718** | 30,8125 ✔ |
| 13:30 | 44,0625 | 97,1875 | 0,9582 | 93,1280 | **0,4731** | 44,0625 ✔ |
| 18:30 | 22,1250 | 97,1875 | 0,4085 | 39,6982 | **0,5573** | 22,1250 ✔ |

Hãy nhìn kỹ hai dòng đầu:
- Sản lượng 10:00 và 13:30 **chênh nhau 43%** (30,8 so với 44,1 kWh).
- Nhưng `k` của hai thời điểm **gần như bằng nhau** (0,4718 và 0,4731).

Điều này nói lên: **hiệu suất trời ở hai thời điểm đó là như nhau**; toàn bộ khác biệt 43%
kia chỉ là do mặt trời cao thấp khác nhau. Phép chia đã "bóc" đúng cái phần biết trước ra
khỏi bài toán.

### 2.4. Phép chia này KHÔNG làm mất thông tin

Cột cuối bảng trên là kết quả nhân ngược `k × mẫu số`. Nó khôi phục **chính xác** giá trị
gốc. Kiểm chứng trên cả ngày: sai số lớn nhất là **1,4 × 10⁻¹⁴ kWh** — tức bằng 0 theo giới
hạn số học của máy tính.

Nói cách khác: chuẩn hoá chỉ là **đổi đơn vị đo**, giống như đổi từ độ C sang độ F, hoặc nói
"đầy 70% bình xăng" thay vì "35 lít". Không có giả định nào được thêm vào, không có thông tin
nào bị mất.

### 2.5. Vì sao điều này quan trọng khi bảo vệ

Câu hỏi hay gặp: *"Mô hình học ra kWh trời quang hay dữ liệu thật?"*

Trả lời: **dữ liệu thật, 100%**. Tử số là số đo từ đồng hồ điện. Mẫu số là quy mô đo được
cộng với thiên văn học. Không có mô hình vật lý nào sinh ra nhãn huấn luyện cả.

*(Có một cột tên `ghi_cs` là bức xạ trời quang theo mô hình Haurwitz, nhưng nó chỉ là **một
đặc trưng đầu vào**, không phải nhãn.)*

---

## PHẦN 3 — Bộ đặc trưng đưa vào mô hình (hiện là 52)

### 3.1. "Đặc trưng" là gì

Trong ML, **đặc trưng (feature)** là các cột dữ liệu đưa vào mô hình để nó dựa vào đó mà
đoán. Nếu ví mô hình như một học sinh làm bài, thì đặc trưng là các dữ kiện đề bài cho.

### 3.2. Ba con số hay bị nhầm lẫn

| Con số | Nghĩa | Xuất hiện ở đâu |
|---|---|---|
| **~90** | Số cột ứng viên sau khi tạo xong đặc trưng (notebook 03_1, 03_2, 03_3) | Bảng chẩn đoán notebook 04 |
| **39** | Số đặc trưng được **chọn** ở notebook 05 | `selected_features.json` |
| **52** | Số đặc trưng **thực sự đưa vào mô hình** | Log `Tong so dac trung: 52` |

### 3.3. Vì sao 39 lại thành 52

Ở notebook 06, trước khi huấn luyện, pipeline thêm **13 cột mới** — là bản sao của các đại
lượng **tất định** nhưng tính tại **thời điểm đích T+h** thay vì thời điểm hiện tại T. Chúng
có hậu tố `_mt` (viết tắt của "mục tiêu").

**13 cột đó là:**

| Nhóm | Các cột |
|---|---|
| Hình học mặt trời | `solar_elevation`, `solar_azimuth`, `azimuth_sin`, `azimuth_cos`, `sin_elevation` |
| Suy ra từ hình học | `ghi_cs` (bức xạ trời quang), `ky_vong`, `ty_le_bao_hoa` |
| Nhãn thời gian | `minute_of_day`, `hour`, `hour_cos`, `doy_sin`, `doy_cos` |

`39 + 13 = 52`.

> **Con số này KHÔNG cố định — và tài liệu cũ ghi 53 là đúng ở thời điểm đó.**
> Số cột `_mt` bằng số đại lượng tất định **có mặt trong bộ 39**. Ở lượt chạy trước,
> `hour_sin` nằm trong bộ 39 nên sinh thêm `hour_sin_mt` → 14 cột `_mt` → tổng **53**. Sau khi
> sửa cách chấm Mutual Information (chấm trên `y(T+1)` thay vì `y(T)`), thứ hạng xê dịch và
> `hour_sin` rơi khỏi Top-35 → không còn `hour_sin_mt` → 13 cột → tổng **52**.
> Danh sách đầy đủ mọi con số đã thay đổi: [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md).

### 3.4. Vì sao thêm các cột `_mt` này KHÔNG phải rò rỉ dữ liệu

Đây là câu hỏi mà người phản biện chắc chắn sẽ hỏi, nên phải trả lời được rành mạch.

**Nguyên tắc phân định:** một đại lượng ở tương lai được phép dùng **nếu và chỉ nếu** nó
tính được chính xác từ bây giờ mà không cần đo đạc gì thêm.

- Vị trí mặt trời lúc 14h30 ngày mai: **tính được** bằng cơ học thiên thể. Lịch thiên văn đã
  có sẵn cho hàng trăm năm tới. → **Được dùng.**
- Bức xạ mặt trời lúc 14h30 ngày mai: **không tính được**, phải chờ đến lúc đó mới biết mây
  thế nào. → **Cấm dùng.**

Trong `features.yaml` có danh sách cấm dịch, ghi rõ: `shortwave_radiation`,
`diffuse_solar_radiation`, `direct_normal_irradiance`, `temperature_c`, `cloud_*`, và toàn bộ
đặc trưng trễ/trượt — tất cả **giữ nguyên tại thời điểm T**.

**Bằng chứng nhóm đã kiểm chứng, không chỉ nói suông:** notebook 01 đối chiếu từng dòng, mốc
thời tiết luôn ≤ mốc sản lượng; lệch trung vị 30 phút, và **0 dòng (0,000%)** dùng thời tiết
tương lai.

### 3.5. Vì sao cần các cột `_mt`

Vì mô hình phải biết **thời điểm nó đang dự báo tới** trông như thế nào. Ví dụ: bây giờ là
17h45, mặt trời còn cao 15°. Dự báo cho 18h45 — lúc đó mặt trời đã lặn. Nếu mô hình chỉ biết
hình học tại 17h45, nó sẽ dự báo còn nhiều điện; biết thêm hình học tại 18h45 thì nó biết
phải dự báo gần 0.

Nhóm đã thử phương án **thay thế** (bỏ cột tại T, chỉ giữ cột tại T+h) và **bác bỏ bằng số**:
buổi sáng 6–9h kết quả tệ hơn 37%, buổi chiều 16–18h tốt hơn 16%. Nên phương án cuối là
**giữ cả hai**.

---

## PHẦN 4 — Toàn cảnh chuỗi notebook

```
     ┌─────────────────── CHUẨN BỊ DỮ LIỆU ───────────────────┐
     00  điền khuyết ──→ 00b kiểm lại
     01  dựng lưới 15 phút liên tục + gắn nhãn nguồn gốc
     02  chia tập theo thời gian (+ 02_EDA khám phá)
     │
     ├─────────────────── TẠO ĐẶC TRƯNG ─────────────────────┐
     03_1  thời gian, trễ, trượt
     03_2  hình học mặt trời, quy mô trạm     (03_2b kiểm chứng)
     03_3  thời tiết, mã hoá phân loại
     04    chẩn đoán đa cộng tuyến
     05    CHỌN 39 ĐẶC TRƯNG
     │
     ├─────────────────── HUẤN LUYỆN ────────────────────────┐
     06_1 MAE   06_2 Huber   06_3 MSE   (mỗi cái h1 + h4)
     06_4  chọn quán quân TRÊN TẬP KIỂM ĐỊNH
     │
     └─────────────────── ĐÁNH GIÁ ──────────────────────────┘
     07    MỞ TẬP TEST (một lần duy nhất)
     07b   so với Prophet
     08    giải thích bằng SHAP

     Nhánh phụ (không sinh dữ liệu): 05b, 05c, 05f — thực nghiệm
     chứng minh từng tham số cố định không phải bịa.
```

---

## PHẦN 5 — Ba luật bất di bất dịch

### Luật 1 — Tập test chỉ mở một lần, ở notebook 07

Dữ liệu chia làm ba phần theo **thời gian**:

```
|──────────── HUẤN LUYỆN ────────────|── KIỂM ĐỊNH ──|──── TEST ────|
        (mô hình học ở đây)          (chọn mô hình)   (chấm điểm cuối)
                                                       15% cuối cùng
```

- **Huấn luyện (train)**: mô hình nhìn và học.
- **Kiểm định (validation)**: dùng để **chọn** giữa các phương án. Mô hình không học từ đây,
  nhưng ta có nhìn vào để quyết định.
- **Test**: giả lập "tương lai chưa từng thấy". Chỉ mở **sau khi** mọi quyết định đã khoá.

Nếu xem kết quả test rồi quay lại chỉnh tham số, tập test biến thành tập kiểm định thứ hai
và con số cuối cùng không còn trung thực. Trong dự án này, quy tắc đó được ghi thành luật.

### Luật 2 — Mọi thống kê chỉ tính trên tập huấn luyện

`site_scale`, trần công suất, ngưỡng cắt nhãn, bảng mã biến phân loại, trung vị điền khuyết —
tất cả tính **chỉ trên tập train**, lưu ra file, rồi **áp nguyên** cho kiểm định và test.

Vì sao? Nếu tính `site_scale` trên toàn bộ dữ liệu, thì con số đó đã chứa thông tin của tương
lai. Mô hình gián tiếp "biết" tương lai qua mẫu số. Đây là dạng rò rỉ tinh vi, rất khó phát
hiện nếu không đặt luật từ đầu.

### Luật 3 — Chỉ chấm điểm trên dòng đo thật, ban ngày

Trong 2,7 triệu dòng, không phải dòng nào cũng là số đo thật:

| Nhãn `energy_source` | Nghĩa | Có được chấm điểm không |
|---|---|---|
| `measured` | Đo thật từ đồng hồ | ✅ **Có** |
| `etl_imputed` | Tầng ETL điền vào chỗ trống | ❌ Không |
| `night_zero` | Ban đêm, gán 0 | ❌ Không |
| `causal_day_persistence` | Lấy giá trị cùng giờ hôm qua | ❌ Không |
| `machine_failure_zero` | Máy hỏng | ❌ Không |

Nếu chấm điểm cả dòng ban đêm (giá trị 0), mô hình chỉ cần đoán 0 vào ban đêm là đã "đúng"
hơn nửa số dòng — điểm số đẹp nhưng vô nghĩa. Nên **con số chính thức của báo cáo** chỉ tính
trên phạm vi `measured & is_daylight`.

---

## PHẦN 6 — Thuật ngữ tra nhanh

| Thuật ngữ | Giải thích ngắn |
|---|---|
| **Đặc trưng (feature)** | Cột dữ liệu đưa vào mô hình làm dữ kiện |
| **Nhãn (label/target)** | Đáp án mà mô hình phải học đoán — ở đây là `k` |
| **Rò rỉ dữ liệu (leakage)** | Mô hình vô tình nhìn thấy thông tin tương lai |
| **Nhân quả (causal)** | Chỉ dùng dữ liệu quá khứ và hiện tại |
| **Độ trễ (lag)** | Giá trị của chính chuỗi ở quá khứ, ví dụ `lag_96` = 24 giờ trước |
| **Cửa sổ trượt (rolling)** | Thống kê trên một đoạn quá khứ, ví dụ trung bình 24 giờ qua |
| **Fold** | Một cặp (huấn luyện, kiểm định) trong kiểm định chéo |
| **WAPE** | `Σ\|dự báo − thật\| / Σ\|thật\| × 100` — thước đo sai số chính của dự án |
| **Hạt giống (seed)** | Số khởi tạo bộ sinh ngẫu nhiên; đổi seed → mô hình hơi khác |
| **Siêu tham số** | Tham số cấu hình mô hình (số cây, tốc độ học…), không học từ dữ liệu |
| **Optuna** | Thư viện tự động dò siêu tham số tốt |
| **LightGBM** | Thư viện cây quyết định tăng cường — mô hình chính của dự án |
| **SHAP** | Phương pháp chia phần đóng góp của từng đặc trưng vào một dự báo |
| **Persistence** | Đối chứng đơn giản nhất: dự báo = giá trị gần nhất đã biết |

---

## PHẦN 7 — Vì sao chọn LightGBM chứ không phải mạng nơ-ron

| Tiêu chí | LightGBM (cây quyết định tăng cường) | Mạng nơ-ron sâu |
|---|---|---|
| Dữ liệu dạng bảng | Rất mạnh — thường thắng trong các cuộc thi | Cần nhiều dữ liệu hơn |
| Xử lý giá trị thiếu | Tự xử lý bằng cơ chế hướng mặc định | Phải điền trước |
| Biến phân loại | Hỗ trợ trực tiếp (cắt theo tập hợp) | Phải mã hoá one-hot hoặc embedding |
| Giải thích | Có TreeSHAP chính xác, nhanh | Khó hơn, thường phải xấp xỉ |
| Thời gian huấn luyện | Vài phút trên CPU | Thường cần GPU |
| Số mẫu của dự án | ~600.000 dòng huấn luyện — vừa tầm | Hơi ít cho mạng sâu |

Với dữ liệu dạng bảng và quy mô như dự án này, LightGBM là lựa chọn tiêu chuẩn.
