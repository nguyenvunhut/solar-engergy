# Notebook 07 — Mở tập test (chi tiết đầy đủ)

>  **Về các con số trong file này:** một số giá trị mô tả lượt chạy ngày 19/08 hoặc
> trưa 20/08. Giá trị **hiện hành** và lý do từng con số thay đổi được liệt kê đầy đủ ở
> [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md). Đọc file đó trước khi
> trích bất kỳ con số nào vào báo cáo.


> **Lần duy nhất** trong toàn dự án tập test được mở. Con số ở đây là con số đưa vào báo cáo
> và đưa ra hội đồng.

- **Vào:** `05_selected/v5_test_selected.parquet` + mô hình thắng cuộc do 06_4 chọn
- **Ra:** `07_final_test/{h1,h4}/metrics_overall.json`, `metrics_by_site.csv`, `prediction_audit.parquet`

---

## 1. Vì sao chỉ được mở một lần

Tập test mô phỏng "tương lai chưa từng thấy". Nếu xem kết quả rồi quay lại chỉnh tham số và
chạy lại, nó biến thành **tập kiểm định thứ hai** — mọi con số mất tính trung thực.

Đây không phải quy tắc hình thức. Chạy test 10 lần rồi báo cáo lần tốt nhất thì con số đó
phản ánh **may mắn**, không phản ánh năng lực mô hình.

**Trong dự án này:** mọi quyết định (chọn loss, chọn tham số, chọn đặc trưng) đều đã khoá ở
06_4 dựa trên **tập kiểm định**, trước khi 07 chạy.

---

## 2. Logic ẩn 1 — Notebook phải TỰ dựng lại các cột `_mt`

Notebook 06 sinh cột `_mt` cho tập train/val nhưng **không xuất ra** cho tập test (vì test
không được mở ở giai đoạn đó). Nên 07 phải tự tính lại:

```python
COT_TAT_DINH = ['solar_elevation', 'solar_azimuth', 'azimuth_sin', 'azimuth_cos',
                'sin_elevation', 'ghi_cs', 'ky_vong', 'ty_le_bao_hoa',
                'minute_of_day', 'hour', 'hour_sin', 'hour_cos', 'doy_sin', 'doy_cos']
out[f'{c}_mt'] = out.groupby('site_id')[c].shift(-h)
```

Thiếu bước này, LightGBM báo lỗi kiểu *"số đặc trưng trong dữ liệu khác lúc huấn luyện"*.

> Số cột `_mt` **không cố định**: chỉ đại lượng nào nằm trong bộ 39 mới được sinh bản `_mt`.
> Lượt hiện hành là **13 cột** (tổng 52 đặc trưng); lượt trước là 14 cột (tổng 53). Danh sách
> phải khớp **chính xác** với notebook 06 của cùng lượt chạy, nếu không mô hình nhận đầu vào sai.

**Đây là chỗ dễ sai nhất của cả notebook** — nếu danh sách cột hoặc phép dịch không khớp
chính xác với notebook 06, mô hình sẽ nhận đầu vào sai mà không báo lỗi (nếu số cột tình cờ
đúng).

---

## 3. Logic ẩn 2 — Đọc tham số từ artifact, KHÔNG viết lại

```python
with open(f'{win_model_dir}/model_config.json') as f:
    cfg = json.load(f)
clip_k   = cfg['clip_k']          # KHÔNG hardcode 1.3587
eps_elev = cfg['eps_elev']
features = cfg['features']
medians  = cfg['feature_medians']
```

Vì sao quan trọng: `clip_k` được **suy từ dữ liệu** ở notebook 06 và đổi theo mỗi lần chạy.
Nếu 07 viết cứng một con số, chỉ cần lệch là toàn bộ kết quả sai **mà không có gì báo lỗi** —
dự báo vẫn ra số, chỉ là sai.

Notebook có kiểm tra: nếu `model_config.json` thiếu `clip_k` thì **dừng và báo lỗi** thay vì
lặng lẽ dùng giá trị mặc định.

---

## 4. Ba phạm vi chấm điểm

| Phạm vi | Điều kiện | Vai trò |
|---|---|---|
| `all` | Mọi dòng hợp lệ | Tham khảo |
| `measured` | Chỉ dòng đo thật | Tham khảo |
| **`measured_daylight`** | Đo thật **và** ban ngày **và** không vượt trần vật lý | **Con số chính thức** |

Ba lớp điều kiện của phạm vi chính thức:

```python
mask = (energy_source == 'measured')
     & (is_daylight == True)
     & (outlier_group != 'physical_over_capacity')
```

**Vì sao không được nới lỏng để "có nhiều dữ liệu hơn"**: mỗi điều kiện loại một loại dòng
mà mô hình **không được tính điểm**: dòng ETL bịa (không phải sự thật), dòng ban đêm (đoán 0
là đúng, quá dễ), dòng vượt trần vật lý (bất khả thi, thường do lỗi cảm biến).

---

## 5. File `prediction_audit.parquet` — bốn cột mốc thời gian

Mỗi dòng lưu: `y_true`, `y_pred`, phần dư, và **bốn** cột thời gian:

| Cột | Nghĩa |
|---|---|
| `source_timestamp_h*` | Thời điểm T — nơi lấy đặc trưng |
| `target_timestamp_h*` | T + h — tính bằng phép cộng cơ học |
| `label_timestamp_h*` | Mốc **thực tế** của dòng bị dịch tới |
| `plot_timestamp_h*` | Mốc dùng khi vẽ biểu đồ |

**Vì sao cần tới bốn cột:** để phát hiện lệch tâm thời gian. Nếu `target_timestamp` (cộng cơ
học) khác `label_timestamp` (mốc thật) thì có lỗ hổng dữ liệu ở chỗ đó và phép dịch đã lấy
nhầm dòng. Đây là cách bắt lỗi trễ pha ở mức từng dòng.

---

## 6. Kết quả lần chạy 20/08 (bản không tune, để đối chiếu)

| | h1 | h4 |
|---|---|---|
| WAPE (đo thật, ban ngày) | 17,7273 | 22,5781 |
| R² | 0,9283 | 0,8964 |
| Thiên lệch ME | +0,0632 kWh (+0,81%) | +0,0563 kWh (+0,71%) |

So bản 19/08 (cơ chế trọng số cũ): WAPE 17,9694 / 22,6751 và thiên lệch **+4,06% / +4,08%**.

---

## 7. Bộ câu hỏi phòng thủ

| Câu hỏi | Trả lời |
|---|---|
| Đã chạy test bao nhiêu lần? | Mỗi chu kỳ dữ liệu một lần, sau khi mọi quyết định đã khoá ở 06_4 |
| Có chỉnh gì sau khi xem kết quả test không? | Không. Mọi thay đổi tham số đều dựa trên tập kiểm định |
| Vì sao con số test (17,73%) **tốt hơn** kiểm định (22,04%)? | Hai tập khác nhau về thời gian: giai đoạn test rơi vào mùa có thời tiết ổn định hơn. Đây là hiện tượng bình thường, và là lý do phải báo cáo cả hai |
| Mô hình có thiên lệch không? | Có, +0,81% ở h1 — đã đo và công bố. Trước khi đổi cơ chế trọng số là +4,06% |
| Sao chỉ chấm trên dòng đo thật ban ngày? | Dòng điền không phải sự thật; dòng ban đêm đoán 0 là đúng nên làm đẹp điểm số giả tạo |
