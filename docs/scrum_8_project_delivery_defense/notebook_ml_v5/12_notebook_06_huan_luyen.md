# Notebook 06_1 / 06_2 / 06_3 — Huấn luyện mô hình (chi tiết đầy đủ)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy ngày 19/08 hoặc
> trưa 20/08. Giá trị **hiện hành** và lý do từng con số thay đổi được liệt kê đầy đủ ở
> [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md). Đọc file đó trước khi
> trích bất kỳ con số nào vào báo cáo.


> Đây là notebook nhiều **logic ẩn** nhất của cả dự án. Đọc kỹ file này thì trả lời được
> hầu hết câu hỏi về phần học máy.

---

## 1. Ba notebook, một bộ code

`06_1_train_mae` · `06_2_train_huber` · `06_3_train_mse` **giống hệt nhau từng dòng**, chỉ
khác hai biến ở cell tham số:

```python
LOSS_NAME     = 'mae'    # hoặc 'huber' / 'mse'
LGB_OBJECTIVE = 'l1'     # hoặc 'huber'  / 'mse'
```

Vì sao phải tách ba notebook thay vì một vòng lặp: để mỗi biến thể có **output riêng, hình
riêng, artifact riêng**, và khi bảo vệ mở ra được từng cái. Nhược điểm là phải sửa ba chỗ mỗi
lần đổi logic — đây là đánh đổi đã biết và chấp nhận.

**Mỗi notebook chạy HAI tầm dự báo:** nửa đầu làm h1 (T+15 phút), nửa sau làm h4 (T+60 phút).
Cell `HORIZON_STEPS` nằm riêng để đổi mà không phải sửa cell cấu hình.

---

## 2. Luồng dữ liệu bên trong — 12 bước

```
 1. doc_du_lieu('v5_train_selected')      lọc dòng hợp lệ
 2. them_muc_tieu(dev, h)                 dịch nhãn sang T+h, sinh 13 cột _mt
 3. lọc site_scale > 0 và sin > 0.05      cổng ban ngày
 4. tinh_clip_tu_train(dev_h)             suy ngưỡng cắt nhãn từ phân vị 0.99
 5. cat_k(...)                            chuẩn hoá + cắt nhãn
 6. build_sample_weight(...)              trọng số mẫu
 7. lọc w > 0                             chỉ dòng thật sự học
 8. cổng kiểm tra trước train             6 phép kiểm, sai là dừng
 9. train thử nhanh + ĐO TRỄ PHA          sai quá 5 phút thì dừng, không tune
10. Optuna 20 trial trên 3 fold           chọn siêu tham số
11. fit mô hình cuối trên toàn tập train
12. chấm điểm validation + xuất artifact
```

---

## 3. Bước 1 — Lọc dòng hợp lệ (`doc_du_lieu`)

Bốn bộ lọc, **thứ tự quan trọng**:

```python
d = d[d['exclude_from_training'] == False]          # (1)
d = d[d['has_complete_history_features'] == True]    # (2)
d = d.dropna(subset=['energy_generated_kwh'])        # (3)
d = d[~d['site_id'].isin([19, 24])]                  # (4)
```

| Bộ lọc | Loại cái gì | Vì sao |
|---|---|---|
| (1) `exclude_from_training` | Dòng bị tầng ETL đánh dấu loại | Ví dụ dòng nằm trong khoảng máy hỏng dài |
| (2) `has_complete_history_features` | Dòng chưa đủ 672 bước (7 ngày) lịch sử phía trước | Không đủ lịch sử thì `lag_96`, `rolling_96` là rỗng hoặc sai |
| (3) `dropna(target)` | Dòng không có sản lượng | Không có nhãn thì không học được |
| (4) **loại trạm 19 và 24** | Toàn bộ hai trạm | `capacity_kw` trong metadata sai 3–4 lần: sản lượng đo thật của trạm 19 vượt "trần" của chính nó tới **4,92 lần**, trung vị đã 1,43 lần |

**Câu hỏi hay bị hỏi:** *"Loại hẳn 2 trạm có làm mất tính tổng quát không?"*
Trả lời: mất **4,84%** dòng đo thật. Nhưng giữ lại thì tệ hơn: từ bản trích ETL ngày 20/08,
tầng ETL đã **kẹp cứng** giá trị đo của hai trạm này về đúng 1,20× trần metadata — 55,6% dòng
đo của trạm 19 giờ là một đường phẳng nhân tạo. Học từ đường phẳng đó là học một mức bão hoà
không có thật.

---

## 4. Bước 2 — `them_muc_tieu`: chỗ sinh ra các cột `_mt`

```python
out['y_true'] = out.groupby('site_id')['energy_generated_kwh'].shift(-h)
```

`shift(-h)` **trong từng trạm** — không được shift xuyên trạm, nếu không dòng cuối của trạm A
sẽ lấy nhãn của dòng đầu trạm B.

Cùng lúc đó, 14 đại lượng tất định được dịch sang T+h và lưu thành cột mới hậu tố `_mt`:

```
solar_elevation_mt, solar_azimuth_mt, azimuth_sin_mt, azimuth_cos_mt, sin_elevation_mt,
ghi_cs_mt, ky_vong_mt, ty_le_bao_hoa_mt,
minute_of_day_mt, hour_mt, hour_sin_mt, hour_cos_mt, doy_sin_mt, doy_cos_mt
```

**39 đặc trưng gốc + 13 cột `_mt` = 52** — con số in ra trong log.

> Số cột `_mt` **thay đổi theo bộ 39**: chỉ đại lượng nào nằm trong bộ đã chọn mới được sinh
> bản `_mt`. Lượt trước có `hour_sin` trong bộ 39 nên là 14 cột → tổng 53; nay `hour_sin` rơi
> khỏi Top-35 nên còn 13 → tổng 52. Xem [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md).

**Logic ẩn cần biết:** thời tiết **không** có bản `_mt`. Danh sách được phép dịch nằm ở
`features.yaml → cot_tat_dinh`; danh sách cấm dịch ghi ngay dưới đó: `shortwave_radiation`,
`diffuse_solar_radiation`, `direct_normal_irradiance`, `temperature_c`, `cloud_*`, `lag_96`,
`rolling_*_96`.

**Câu hỏi:** *"Dùng dữ liệu tại T+h là nhìn trộm tương lai?"*
Trả lời: chỉ với đại lượng **tính được trước bằng thiên văn và lịch** — vị trí mặt trời lúc
14h30 ngày mai đã biết chính xác từ hàng chục năm trước. Thời tiết thì tuyệt đối không dịch.
Nhóm đã kiểm chứng: 0/2.731.946 dòng dùng thời tiết tương lai.

---

## 5. Bước 3 — Cổng ban ngày `sin_elevation > 0.05`

`0.05` tương ứng góc mặt trời khoảng **2,87°**.

Vì sao cần: nhãn là `k = y / (site_scale × sin)`. Khi `sin → 0`, mẫu số → 0 và nhãn nổ tung.
Số đo thật trên tập huấn luyện:

| Vùng sin | Số dòng | % điện năng | k lớn nhất |
|---|---|---|---|
| 0 – 0,02 | 2.416 | 0,016% | **19.573** |
| 0,02 – 0,05 | 6.358 | 0,054% | 16,0 |
| 0,4 – 0,7 | 253.627 | 44,1% | 1,99 |

Cắt vùng rìa mất **0,07% điện năng**, đổi lại tránh được nhãn nổ. Nếu không cắt, ngưỡng cắt
nhãn (phân vị 99) bị kéo lệch **+0,71%** cho toàn bộ phần còn lại.

---

## 6. Bước 4 — Ngưỡng cắt nhãn: suy từ dữ liệu, KHÔNG viết cứng

```python
def tinh_clip_tu_train(df, phan_vi=CLIP_PHAN_VI):   # CLIP_PHAN_VI = 0.99
    k = df['y_true'] / mau_chuan_hoa(df)
    return k.quantile(phan_vi)
```

Bản chạy 20/08 cho **clip_k ≈ 1,3587**. Bản 19/08 cho 1,3583 — hai lần chạy trên hai bản dữ
liệu khác nhau, ra hai con số hơi khác, **đúng như thiết kế**: pipeline hardcode **quy tắc**
(phân vị 0,99), không hardcode **con số**.

### Logic ẩn quan trọng: mỗi fold suy ngưỡng RIÊNG

```python
CLIP_K_FOLD = {}
if vai_tro == 'train':
    clip_k = tinh_clip_tu_train(d)   # tính từ fold-train của chính fold đó
    CLIP_K_FOLD[n] = clip_k
else:
    clip_k = CLIP_K_FOLD.get(n)      # fold-val dùng ngưỡng của fold-train tương ứng
```

Trước bản sửa 19/08, cả 3 fold dùng chung một ngưỡng tính từ tập train cuối cùng → **fold 1
và 2 nhìn thấy tương lai** qua ngưỡng. Sai lệch đo được ở fold 1 là **37%**. Đây là dạng rò rỉ
rất tinh vi: không rò qua đặc trưng mà rò qua **một con số thống kê**.

**Cắt nhãn KHÔNG phải xoá dòng.** Dòng vẫn ở trong tập huấn luyện, chỉ giá trị nhãn bị chặn
trần. Và khi **chấm điểm**, `y_true` giữ nguyên số đo gốc, không cắt.

---

## 7. Bước 6 — Trọng số mẫu (phần đổi ngày 20/08)

```python
w = 0.0                                   # mặc định: không tham gia hàm mục tiêu
w[hợp lệ & measured & normal]        = 1.0
w[hợp lệ & measured & other/multi]   = 1.0
w[hợp lệ & measured & gmm_consensus] = 1.0   # tuỳ experiment
w[physical_over_capacity]            = 0.0   # luôn loại
# rồi nhân trọng số theo cơ chế:
w = w * (mẫu_số / trung_bình_mẫu_số)         # CHE_DO_TRONG_SO = 'mau_so'
```

### Vì sao chọn `w = mẫu_số`

Xuất phát từ một đẳng thức: `ŷ − y = mẫu_số × (k̂ − k)`.

WAPE có tử số là `Σ|ŷ − y|`. Thay vào: `Σ mẫu_số × |k̂ − k|`. Đó **chính là** MAE có trọng số
`mẫu_số` trên thang `k`. Nghĩa là huấn luyện với trọng số này = tối ưu đúng thước đo báo cáo.
Nguyên lý nền: Gneiting (2011) — hàm mất mát dùng để ước lượng phải nhất quán với thước dùng
để chấm điểm; Kolassa (2007) — WAPE = MAE / trung bình y.

Trọng số này **tất định**: tính từ `site_scale × sin_elevation`, cả hai đều biết trước, không
nhìn vào nhãn. Nên nó **không kéo dự báo lên**.

### Cơ chế cũ `w = 1 + α·k` đã bị loại (20/08)

> **Hệ quả cần biết khi đọc thí nghiệm TN4 trong 05b:** sau khi chuyển sang `mau_so`, tham số
> `he_so_trong_so_dinh` trở thành **nút chết** — nhánh `w = 1 + α·k` nằm sau điều kiện
> `if che_do == 'theo_nhan'` nên không bao giờ được gọi. Vì vậy TN4 cho **bốn giá trị WAPE y
> hệt nhau** (22,0428 ở mọi mức α). Đó là bằng chứng cơ chế cũ đã gỡ sạch khỏi đường tính,
> **không phải** bằng chứng "α không quan trọng". Bằng chứng cho việc *chọn* cơ chế nằm ở
> **TN11** (so trực tiếp ba cơ chế A/B/C).

| | WAPE val | Thiên lệch ME (test) |
|---|---|---|
| `1 + k` (cũ) | 22,2349 | **+0,3193 kWh = +4,06%** |
| `mẫu_số` (mới) | 22,0424 | **+0,0632 kWh = +0,81%** |

Vấn đề của `1+k`: trọng số **phụ thuộc chính giá trị nhãn**. Dòng nào sản lượng cao thì tự
thưởng cho mình trọng số lớn → mô hình bị kéo lên → dự báo cao hơn thực tế 4%.

**Câu hỏi:** *"Sao lại đánh trọng số, không phải mọi quan sát đều bình đẳng sao?"*
Trả lời: bình đẳng trên thang `k` không có nghĩa bình đẳng trên thang kWh. Sai 0,1 đơn vị `k`
lúc giữa trưa tốn 9,31 kWh nhưng lúc chiều tà chỉ tốn 3,97 kWh. Vì mình chấm điểm bằng kWh,
trọng số phải phản ánh điều đó.

---

## 8. Bước 8 — Sáu cổng kiểm tra trước khi train

Nếu bất kỳ cổng nào fail, notebook **dừng**, không train:

1. **Nhãn đúng là y(T+h)** — đối chiếu vài dòng đầu với phép shift thủ công.
2. **Không có cột `_mt` của thời tiết** — chống rò rỉ.
3. **Ma trận không rỗng, không toàn NaN.**
4. **Không đặc trưng nào trùng khớp hoàn hảo với nhãn** (dấu hiệu rò rỉ trực tiếp).
5. **Ngưỡng cắt nằm trong khoảng hợp lý.**
6. **Số đặc trưng đúng 52** (39 + 13 cột `_mt`).

---

## 9. Bước 9 — Cổng đo TRỄ PHA (logic ẩn quan trọng nhất)

Đây là phần ít người ngoài biết nhưng cực kỳ quan trọng.

**Vấn đề:** mô hình chuỗi thời gian rất dễ rơi vào mẹo "chép lại giá trị gần nhất". Kết quả
là đường dự báo trông rất khớp nhưng **dịch sang phải** — tức luôn đi sau thực tế. Nhìn biểu
đồ thì đẹp, nhưng vô dụng khi vận hành.

**Cách đo — theo độ dốc, không dùng RMSE:**

```
dốc(t)   = (thực_tế(t+1) − thực_tế(t−1)) / 2
sai(t)   = dự_báo(t) − thực_tế(t)
trễ_phút = −Σ(dốc × sai) / Σ(dốc²) × 15
```

Nguyên lý: nếu dự báo bị dịch phải `c` bước thì `sai ≈ −c × dốc`. Hệ số hồi quy của `sai`
theo `dốc` chính là `c`. Cách này **tách sai số thời điểm khỏi sai số biên độ** — dự báo cao
hay thấp không ảnh hưởng chỉ số này.

**Ngưỡng:** `|trễ| > 5 phút` → dừng, không tune. Lần chạy 20/08 đo được **+2,53 phút**, 0/40
trạm vượt ngưỡng → cổng ĐẠT.

Cổng này chạy trên một mô hình nhỏ (300.000 dòng, ~4 giây) **trước** khi tốn 50 phút cho
Optuna. Phát hiện sớm, chi phí thấp.

---

## 10. Bước 10 — Optuna trên 3 fold

```python
N_TRIALS = 20
```

Mỗi trial: thử một bộ siêu tham số, huấn luyện trên **cả 3 fold**, tính **pooled WAPE** (gộp
dự báo của 3 fold rồi tính một lần, không phải trung bình 3 con số).

**Logic ẩn — số cây lấy từ early stopping, không lấy từ Optuna:**

```python
BEST_PARAMS['n_estimators'] = int(np.median(so_cay_tung_fold))
```

Lý do: Optuna đề xuất số cây, nhưng early stopping mới biết thực tế cần bao nhiêu. Lấy
**trung vị** qua 3 fold thay vì trung bình để một fold dị thường (fold 1 rất ít dữ liệu)
không kéo lệch.

**Câu hỏi:** *"Vì sao 20 trial mà không phải 100?"*
Trả lời: đường hội tụ (TN7, cuối notebook 06_4) cho thấy điểm số thôi cải thiện sau khoảng
**10 trial**. Ngân sách 20 là gấp đôi mức bão hoà.

---

## 11. Bước 11–12 — Fit cuối và chấm điểm

### Nhân ngược về kWh

```python
ŷ = min( clip(k̂, 0, clip_k) × mẫu_số ,  tran_cong_suat × 1.02 )
ŷ = 0  nếu sin_elevation ≤ 0.05
```

Hệ số **1,02**: đo trên dữ liệu thật, tỷ lệ `sản lượng / trần` cao nhất chỉ **1,007** → rào
này **chưa từng kích hoạt**. Nó chỉ tồn tại để chặn dự báo phi lý. Mọi giá trị ≥ 1,01 cho kết
quả y hệt nhau.

### Phạm vi chấm điểm

Chỉ `energy_source == 'measured'` **và** `is_daylight == True`. Nếu chấm cả ban đêm, mô hình
chỉ cần đoán 0 vào ban đêm là "đúng" hơn nửa số dòng.

### Thước đo

```
WAPE = Σ|ŷ − y| / Σ|y| × 100
```

Dùng WAPE thay MAPE vì MAPE chia cho **từng** giá trị thật — sáng sớm sản lượng gần 0 làm
MAPE nổ lên vô cực. WAPE chia cho **tổng**, ổn định.

---

## 12. Ba cạm bẫy kỹ thuật đã xử lý

### 12.1. Biến phân loại bị hiểu thành số có thứ tự

`site_id_enc`, `weather_condition_enc`, `weather_description_enc` là **mã**, không phải số
lượng. Nếu không khai báo, LightGBM cắt kiểu `mã ≤ 17,5` — vô nghĩa vì thứ tự mã chỉ là thứ
tự bảng chữ cái.

```python
m.fit(X, y, categorical_feature=[c for c in X.columns if c.endswith('_enc')])
```

Khai báo rồi thì LightGBM cắt theo **tập hợp** (`mã ∈ {3, 7, 12}`) và tự coi **−1 là giá trị
thiếu**. Đã kiểm chứng bằng cách đọc cấu trúc cây: 2.131 nút cắt kiểu `==`, 0 nút kiểu `<=`.

### 12.2. Tầm quan trọng đặc trưng phải đọc theo `gain`, không theo số lần cắt

Biến phân loại nhiều giá trị (`site_id_enc` có 42 mức) sẽ được cắt rất nhiều lần, nên nếu
xếp hạng theo **số lần cắt** thì nó luôn đứng đầu — đó là thiên lệch của chỉ số, không phải
tầm quan trọng thật. Notebook dùng `importance_type='gain'` (tổng mức giảm sai số).

### 12.3. GPU OpenCL trên NixOS

Máy dùng NixOS nên thư mục driver OpenCL nằm ở `/run/opengl-driver/etc/OpenCL/vendors`.
Notebook tự dò và đặt `OCL_ICD_VENDORS`, thử train một mô hình 200 dòng để kiểm tra, **lỗi
thì tự lui về CPU** chứ không dừng.

---

## 13. Artifact xuất ra và ý nghĩa từng file

| File | Nội dung | Ai dùng |
|---|---|---|
| `model_h1.pkl` / `model_h4.pkl` | Mô hình + đặc trưng + trung vị + `clip_k` + `eps_elev` + **cơ chế trọng số** | 07, dashboard |
| `ket_qua.json` | Siêu tham số (đề xuất và thực tế), metrics, cấu hình, kết quả quét độ trễ | Đối chiếu, báo cáo |
| `metrics.csv` | Bảng metric ba phạm vi | Báo cáo |
| `du_bao_val.parquet` | Dự báo trên validation | Tính thiên lệch, vẽ hình |
| `06_train/{loss}/h{1,4}/model_config.json` | Bản tương thích cho 07/08 | 07, 08, 07b |

Từ 20/08, hai file đầu ghi thêm `che_do_trong_so`, `experiment`, `mau_so`, `clip_phan_vi` —
trước đây không truy được model nào chạy chế độ nào.

---

## 14. Bộ câu hỏi phòng thủ

| Câu hỏi | Trả lời ngắn |
|---|---|
| Mô hình học kWh hay tỷ lệ? | Tỷ lệ `k`; nhân ngược về kWh khi chấm điểm, khôi phục chính xác (sai số 10⁻¹⁴) |
| `k` từ dữ liệu thật hay mô hình lý thuyết? | Dữ liệu thật: tử số là số đo, mẫu số là phân vị đo được × thiên văn |
| Ngưỡng cắt 1,3587 ở đâu ra? | Phân vị 0,99 của `k` trên tập train, suy lại mỗi lần chạy |
| Sao cắt 1% nhãn, có oan không? | TN2 quét cả mức "không cắt"; TN2b cho thấy khác biệt đảo chiều theo hạt giống → là nhiễu |
| Sao chọn MAE? | WAPE là thước sai số tuyệt đối, nhất quán với trung vị (Gneiting 2011) — MAE ước lượng trung vị. Kết quả xác nhận: MAE < Huber < MSE ở cả hai tầm |
| Có so với baseline không? | Có: Prophet (skill +48,7% ở h1) và persistence (thua ở h1, xem 07b) |
| Mô hình có bị trễ pha không? | Đo bằng phương pháp độ dốc: +2,53 phút, 0/40 trạm vượt ngưỡng 5 phút |
| Bao nhiêu dữ liệu thực sự vào mô hình? | 599.545 dòng × 52 đặc trưng cho h1 (từ 1,55 triệu dòng sau các bộ lọc) |
| Vì sao mất nhiều dòng thế? | Ban đêm (~53%), thiếu lịch sử, dòng ETL điền (w=0), loại 2 trạm |
