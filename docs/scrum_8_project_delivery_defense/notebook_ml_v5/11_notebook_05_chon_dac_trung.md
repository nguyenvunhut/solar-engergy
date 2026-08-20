# Notebook 05 — Chọn đặc trưng (chi tiết đầy đủ)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy ngày 19/08 hoặc
> trưa 20/08. Giá trị **hiện hành** và lý do từng con số thay đổi được liệt kê đầy đủ ở
> [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md). Đọc file đó trước khi
> trích bất kỳ con số nào vào báo cáo.


> Notebook quyết định **mô hình được nhìn thấy cái gì**. Mọi lựa chọn ở đây phải giải thích
> được, vì đây là chỗ dễ vô tình để rò rỉ dữ liệu nhất.

- **Vào:** `03_3_features_aggregate/v5_train_features.parquet` (~90 cột) + `04_diagnostics/feature_diagnostics.csv`
- **Ra:** `selected_features.json`, `feature_scores.csv`, và các tập `v5_*_selected.parquet`

---

## 1. Ba tầng lọc, theo thứ tự

```
~90 cột ứng viên
   ↓  TẦNG 1: danh sách cấm (deny list) — cấm TRƯỚC khi chấm điểm
~60 cột
   ↓  TẦNG 2: chấm điểm bằng Mutual Information, lấy Top-35
35 cột
   ↓  TẦNG 3: bù nhóm bảo vệ (đặc trưng bắt buộc theo nghiệp vụ)
39 cột  →  selected_features.json
```

Thứ tự này quan trọng: **cấm trước, chấm sau**. Nếu chấm trước rồi mới cấm, một cột rò rỉ có
điểm cao sẽ chiếm chỗ và đẩy cột hợp lệ ra ngoài Top-K.

---

## 2. Tầng 1 — Bảy nhóm bị cấm và lý do

| Nhóm | Ví dụ | Vì sao cấm |
|---|---|---|
| **Mục tiêu** | `energy_generated_kwh`, `y_muc_tieu` | Chính là đáp án |
| **Nguồn gốc / cờ outlier** | `energy_source`, `gmm_if_outlier_flag`, `outlier_group` | Chỉ tồn tại **sau khi** đã biết sản lượng. Ở thời điểm dự báo thật, chưa ai biết dòng tương lai là `measured` hay `etl_imputed` |
| **Cờ ban ngày dùng để chấm** | `is_daylight` | Thuộc khâu đánh giá, không phải đầu vào |
| **Khoá định danh** | `gen_id`, `weather_id`, `date_id`, `time_id` | Chỉ là số thứ tự tăng dần; mô hình học được là học vẹt theo thứ tự dòng |
| **Cột chữ thô** | `weather_condition`, `panel`, `inverter` | Đã có bản mã hoá `*_enc` |
| **Thời gian thô** | `timestamp`, `full_date`, `year` | Mô hình sẽ học "năm 2021 thì thế này" thay vì học quy luật vật lý |
| **Cộng tuyến cấu trúc** | `site_scale`, `pv_clr_lonij`, `clearsky_proxy`, `con_cach_tran`, `dni_ratio` | **Là thành phần của mẫu số chuẩn hoá.** Đưa vào là rò rỉ gián tiếp: nhãn `k = y/(site_scale × sin)`, nếu mô hình biết `site_scale` thì nó biết một nửa công thức nhãn |

**Câu hỏi thường gặp:** *"Cấm `site_scale` mà vẫn dùng nó làm mẫu số, có mâu thuẫn không?"*
Không. Mẫu số là **phép biến đổi nhãn**, không phải đầu vào. Mô hình đoán `k`, rồi mình nhân
ngược bằng `site_scale` — mô hình không cần và không được biết con số đó.

---

## 3. Tầng 2 — Mutual Information

### 3.1. MI là gì

Đo **lượng thông tin chung** giữa một đặc trưng và mục tiêu: biết đặc trưng thì giảm được bao
nhiêu bất định về mục tiêu.

**Vì sao dùng MI thay vì hệ số tương quan:** tương quan Pearson chỉ bắt quan hệ **tuyến tính**.
Quan hệ giữa bức xạ và sản lượng **không tuyến tính** — có đoạn bão hoà khi inverter cắt đỉnh.
MI bắt được cả quan hệ phi tuyến.

### 3.2. Ba chi tiết ẩn

```python
MI_SAMPLE_SIZE = 100_000
RANDOM_STATE   = 42
HORIZON_MI     = 1
```

1. **Lấy mẫu 100.000 dòng**: MI tính trên 1,5 triệu dòng × 60 cột rất chậm. Mẫu 100.000 đủ để
   thứ hạng ổn định, và cố định hạt giống để tái lập.

2. **Chỉ chấm trên dòng hợp lệ.** Nếu chấm cả dòng ban đêm (hơn nửa dữ liệu, giá trị 0), mọi
   đặc trưng đều "dự đoán được" số 0 → bảng xếp hạng thành vô nghĩa.

3. **Chấm trên nhãn tại T+h, không phải T** *(sửa 20/08)*:
   ```python
   df_clean['y_muc_tieu'] = df_clean.groupby('site_id')['energy_generated_kwh'].shift(-1)
   ```
   Trước đây MI chấm với sản lượng **tại T**, trong khi mô hình học `y(T+h)`. Hai đại lượng
   tương quan rất cao ở lưới 15 phút nên thứ hạng gần giống nhau, nhưng về nguyên tắc phải
   chấm đúng mục tiêu thật của bài toán. Sau khi sửa, output in ra:
   `Dich muc tieu sang T+1 buoc: bo 42 dong cuoi moi tram`.

---

## 4. Tầng 3 — Nhóm bảo vệ

```python
TOP_K_FEATURES = 35
```

Một số đặc trưng **bắt buộc phải có** vì lý do nghiệp vụ, dù thứ hạng MI có thể thấp — chủ
yếu là nhóm hình học mặt trời. Lý do: chúng là **xương sống vật lý** của bài toán; thiếu
chúng thì mô hình mất khả năng ngoại suy sang mùa/giờ chưa gặp.

Kết quả: 35 (Top-MI) + 4 (bảo vệ bị Top-K cắt) = **39 đặc trưng**.

---

## 5. Bộ 39 không cố định — và đó là điều bình thường

Bộ đặc trưng **được suy từ dữ liệu**, nên dữ liệu đổi thì bộ đổi. Hai lần thay đổi đã ghi
nhận:

| Lần | Đổi gì | Nguyên nhân |
|---|---|---|
| 20/08 sáng | `cloud_cover_low` ra, `inverter_enc` vào | Tầng ETL điền 846.973 ô trống của `cloud_cover_low` → phân phối đổi → điểm MI tụt. Nó vốn đứng hạng 34/35, sát vạch cắt |
| 20/08 chiều | `hour_sin` ra | Sau khi sửa MI chấm trên `y(T+1)`, thứ hạng xê dịch |

**Hệ quả dây chuyền của lần thứ hai:** `hour_sin` rời bộ 39 → cột `hour_sin_mt` không được
sinh ra nữa → tổng đặc trưng vào mô hình từ **53 xuống 52**.

Nguyên tắc xử lý: **ghi nhận, không sửa tay để ép về bộ cũ.** Sửa tay là biến kết quả thành
thứ mình muốn thấy chứ không phải thứ dữ liệu nói.

---

## 6. Ba con số dễ nhầm

| Con số | Nghĩa |
|---|---|
| **39** | Đặc trưng được chọn, ghi trong `selected_features.json` |
| **48** | Số **cột** trong file `*_selected.parquet` = 39 đặc trưng + 9 cột phụ (`site_id`, `timestamp`, `energy_generated_kwh`, `energy_source`, `is_daylight`, `site_scale`, `sin_elevation`, `tran_cong_suat`, `outlier_group`). Cột phụ **không** vào mô hình, chỉ để dựng nhãn và chấm điểm |
| **52** | Đặc trưng thực sự vào LightGBM = 39 + 13 cột `_mt` (sinh ở notebook 06) |

---

## 7. Bộ câu hỏi phòng thủ

| Câu hỏi | Trả lời |
|---|---|
| Vì sao chọn 35 mà không phải 40 hay 50? | Thí nghiệm 8 trong 05b quét K = 25/30/35/40/45 và so WAPE. *(Lưu ý trung thực: các mức K > 35 hiện chỉ mang tính đối chiếu hình thức vì tập đọc vào đã bị cắt còn 39 cột — đây là hạn chế đã ghi nhận)* |
| Sao cấm `site_id` thô nhưng vẫn dùng `site_id_enc`? | Cấm cột định danh thô để chống học vẹt theo thứ tự. Bản mã hoá được **khai báo là biến phân loại**, LightGBM cắt theo tập hợp chứ không theo thứ tự số |
| MI có phải cách chọn tốt nhất không? | Không phải duy nhất, nhưng phù hợp: bắt được quan hệ phi tuyến, rẻ, dễ giải thích. Nhược điểm là chấm **từng đặc trưng độc lập**, không thấy tương tác — nên mới cần notebook 04 (VIF) bổ trợ |
| Sao bộ 39 lại đổi giữa các lần chạy? | Vì nó suy từ dữ liệu chứ không viết cứng. Dữ liệu đổi (ETL điền thêm) thì thứ hạng đổi. Đã ghi nhận đầy đủ hai lần đổi |
| Chọn đặc trưng trên tập train cuối rồi áp cho các fold sớm — có rò rỉ không? | Có một mức độ: bộ đặc trưng được chọn bằng dữ liệu của toàn tập train, trong khi fold 1 chỉ dùng phần đầu. Đây là **hạn chế đã ghi nhận**; ảnh hưởng nhỏ vì việc chọn chỉ dựa trên thứ hạng MI chứ không dựa trên điểm số mô hình |
