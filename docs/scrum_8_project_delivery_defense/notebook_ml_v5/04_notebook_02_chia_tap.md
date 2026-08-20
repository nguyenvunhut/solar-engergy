# Notebook 02 — Chia tập theo thời gian (chi tiết đầy đủ)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy trước. Giá trị hiện
> hành và lý do từng con số thay đổi: [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md).


> Chia tập sai là hỏng toàn bộ đánh giá. Với chuỗi thời gian, cách chia thông thường của ML
> (ngẫu nhiên) là **sai nghiêm trọng**.

- **Vào:** `01_reindex/v5_continuous_grid.parquet`
- **Ra:** `02_split/{development, test, train, val, time_series_folds, summaries}/`

---

## 1. Vì sao không được chia ngẫu nhiên

Chia ngẫu nhiên nghĩa là lấy 15% số dòng bất kỳ làm tập test. Với chuỗi thời gian, điều đó
tạo ra tình huống: mô hình được học dữ liệu **ngày 20/03** rồi đi dự báo **ngày 19/03**.

Với dữ liệu 15 phút, hậu quả còn nặng hơn: dòng 10:00 vào tập train, dòng 10:15 vào tập test.
Hai dòng cách nhau 15 phút, gần như giống hệt nhau → mô hình chỉ cần "nhớ" là ra kết quả
tuyệt vời, nhưng vô dụng trong thực tế.

---

## 2. Cắt theo MỐC THỜI GIAN, không cắt theo dòng

```python
TEST_RATIO = 0.15
```

Cách làm: lấy **danh sách mốc thời gian duy nhất**, sắp xếp tăng dần, lấy 15% cuối cùng làm
test.

**Vì sao phải cắt theo mốc, không cắt theo dòng:** nếu cắt theo dòng, trạm A có thể có dữ
liệu tới tháng 5 trong tập train, trong khi trạm B chỉ tới tháng 3. Mô hình học được "tương
lai của trạm A" rồi đi dự báo "hiện tại của trạm B" — dạng rò rỉ chéo giữa các trạm. Cắt
theo mốc đảm bảo **cả 42 trạm cùng bị cắt tại một thời điểm**.

---

## 3. Ba fold kiểu "mở rộng dần"

```python
STRATEGY = "expanding"
N_SPLITS  = 3
```

```
fold 1:  train [────]           val [──]
fold 2:  train [────────]       val [──]
fold 3:  train [────────────]   val [──]
                                     thời gian →
```

Tập huấn luyện **lớn dần**, tập kiểm định luôn nằm **phía sau**. Đây là mô phỏng đúng tình
huống vận hành: càng chạy lâu càng có nhiều lịch sử.

**Khác với k-fold thông thường:** k-fold cho phép tập kiểm định nằm trước tập huấn luyện —
không chấp nhận được với chuỗi thời gian.

### Kích thước thật (sau các bộ lọc của notebook 06)

| Fold | Dòng huấn luyện | Dòng kiểm định |
|---|---|---|
| 1 | 97.107 | 191.547 |
| 2 | 325.275 | 258.363 |
| 3 | 600.483 | 289.348 |

**Vì sao fold 1 nhỏ thế:** giai đoạn đầu dự án chỉ có **13 trạm** hoạt động, sau đó tăng dần
lên 42. Đây là đặc điểm của dữ liệu, không phải lỗi chia tập. Nó cũng giải thích vì sao ngưỡng
cắt nhãn của fold 1 khác hẳn fold 3 (1,88 so với 1,36) — hai giai đoạn có đội trạm khác nhau.

---

## 4. Các bí danh và bẫy đi kèm

| Tên | Là gì | Dùng để |
|---|---|---|
| `train` | Tập huấn luyện của **fold cuối** | Huấn luyện mô hình chính |
| `val` | Tập kiểm định của **fold cuối** | Chọn mô hình, chấm điểm kiểm định |
| `development` | train + val gộp lại | **CHỈ** dùng khi huấn luyện lại mô hình triển khai sau khi đã chốt |
| `test` | 15% cuối theo thời gian | Chỉ mở ở notebook 07 |

**Bẫy:** `development` chứa cả `val`. Nếu lỡ dùng `development` để huấn luyện rồi chấm điểm
trên `val` thì 100% dòng val đã nằm trong tập học → điểm số vô nghĩa. Cấu hình đường dẫn có
ghi cảnh báo này ngay tại chỗ khai báo.

---

## 5. Chồng lấn nhãn ở ranh giới fold

Nhãn của một dòng là `y(T+h)`. Dòng nằm sát cuối fold-train có nhãn **rơi sang** vùng kiểm
định của chính fold đó.

Số đo được (thí nghiệm 9 trong 05b):

| | fold 1 | fold 2 | fold 3 |
|---|---|---|---|
| h1 (T+15 phút) | 30 dòng | 39 dòng | 42 dòng |
| h4 (T+60 phút) | 120 dòng | 156 dòng | 168 dòng |

So với 97.000–600.000 dòng huấn luyện, tỷ lệ là **0,005%–0,03%**. Nhóm quyết định **ghi nhận
và công bố** thay vì cắt, vì cắt sẽ làm lệch so sánh với các kết quả đã có. Khi bảo vệ, đây
là điều nên chủ động nêu ra kèm con số.

---

## 6. Bộ câu hỏi phòng thủ

| Câu hỏi | Trả lời |
|---|---|
| Sao không chia ngẫu nhiên như bình thường? | Chuỗi thời gian: chia ngẫu nhiên cho mô hình học tương lai rồi đoán quá khứ |
| Sao không dùng k-fold? | k-fold cho tập kiểm định nằm trước tập huấn luyện — vi phạm nhân quả |
| Fold 1 ít dữ liệu thế có sao không? | Do đội trạm ban đầu chỉ 13/42; là đặc điểm dữ liệu, và cũng là lý do mỗi fold phải suy ngưỡng cắt riêng |
| Test 15% có đủ không? | 510.468 dòng thô, sau lọc còn ~229.000 dòng đo thật ban ngày cho mỗi tầm — thừa đủ |
| Có chồng lấn giữa train và val không? | Có ở ranh giới, đã đo: 30–42 dòng (h1), 120–168 dòng (h4), tức 0,005–0,03% |
