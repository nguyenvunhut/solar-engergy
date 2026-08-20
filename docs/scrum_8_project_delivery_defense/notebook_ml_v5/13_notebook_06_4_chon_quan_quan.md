# Notebook 06_4 — Chọn mô hình quán quân (chi tiết đầy đủ)

> ⚠️ **Về các con số trong file này:** một số giá trị mô tả lượt chạy ngày 19/08 hoặc
> trưa 20/08. Giá trị **hiện hành** và lý do từng con số thay đổi được liệt kê đầy đủ ở
> [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md). Đọc file đó trước khi
> trích bất kỳ con số nào vào báo cáo.


- **Vào:** `06_train/{mae,huber,mse}/{h1,h4}/model_config.json` + dự báo trên tập kiểm định
- **Ra:** `07_final_test/val_model_selection_check.json`, `best_loss.json`
- **Kèm ở cuối:** Thí nghiệm 7 (đường hội tụ Optuna)

---

## 1. Nhiệm vụ trong một câu

Ba mô hình đã huấn luyện xong. Chọn **một** để mang sang tập test — và phải chọn bằng cách
không làm hỏng tính trung thực của con số test.

---

## 2. Nguyên tắc bất di bất dịch: chọn trên KIỂM ĐỊNH

Tập test tuyệt đối không được dùng ở bước này. Lý do:

Nếu chọn mô hình dựa trên điểm test, thì con số test không còn là "ước lượng cho dữ liệu chưa
thấy" — nó đã bị tối ưu gián tiếp. Chọn 1 trong 3 mô hình dựa trên test cũng là một dạng
tuning, chỉ là tuning thô.

Quy trình đúng: **kiểm định để chọn → test để báo cáo**.

---

## 3. Điều kiện bắt buộc của phép so sánh

Ba mô hình phải được chấm trên **cùng một tập dòng**, cùng thước đo, cùng cách nhân ngược về
kWh. Nếu mô hình A chấm trên 289.000 dòng còn mô hình B chấm trên 291.000 dòng thì hai con số
không so được với nhau.

Notebook kiểm tra điều này và **báo lỗi nếu số dòng lệch** thay vì lặng lẽ so sánh.

---

## 4. Dự đoán lý thuyết — nêu TRƯỚC khi chạy

Ba loss ước lượng ba đại lượng khác nhau:

| Loss | Ước lượng | Nhất quán với thước nào |
|---|---|---|
| MAE (l1) | **Trung vị** có điều kiện | Sai số tuyệt đối (MAE, WAPE) |
| MSE (l2) | **Trung bình** có điều kiện | Sai số bình phương (RMSE) |
| Huber | Lai giữa hai cái trên | Tuỳ ngưỡng δ |

Theo nguyên lý nhất quán của Gneiting (2011): thước đo sai số **tuyệt đối** nhất quán với
**trung vị**. Dự án báo cáo bằng **WAPE** (họ tuyệt đối) → **MAE phải thắng**.

Đây là **giả thuyết đăng ký trước**, không phải giải thích sau khi thấy kết quả.

### Kết quả xác nhận (lần chạy 20/08, chưa tune)

| Loss | WAPE h1 | WAPE h4 |
|---|---|---|
| **MAE** | **22,0424** | **26,8018** |
| Huber | 22,4421 | 27,0022 |
| MSE | 22,6962 | 27,1511 |

Đúng thứ tự dự đoán, ở **cả hai tầm**. Đây là loại bằng chứng mạnh: lý thuyết nói trước, số
liệu xác nhận sau.

---

## 5. Phụ lục — Thí nghiệm 7: ngân sách Optuna

Đặt ở cuối notebook này (không phải 05b) vì nó đọc **nhật ký trial in trong output của
06_1/06_2/06_3** — chỉ tồn tại sau khi ba notebook đó chạy.

**Cách làm:** đọc các dòng `[Trial k/20] pooled WAPE ...`, vẽ **đường hội tụ** = WAPE tốt
nhất tính tới trial thứ k. Nếu đường phẳng từ trước trial cuối → ngân sách đã bão hoà.

**Vì sao thí nghiệm này phải nằm SAU:** nó hỏi *"cuộc dò đã hội tụ chưa"* — về mặt logic
không thể trả lời trước khi dò. Nó là **kiểm chứng hậu kiểm**, không đặt ra tham số nào.

Con số 20 được biện minh **trước** bằng đường hội tụ của chu kỳ chạy trước (phẳng sau ~10
trial); TN7 xác nhận lại mỗi lần chạy rằng giả định đó còn đúng.

---

## 6. Bộ câu hỏi phòng thủ

| Câu hỏi | Trả lời |
|---|---|
| Sao chọn MAE? | Nêu dự đoán lý thuyết trước (WAPE ↔ trung vị ↔ MAE), kết quả xác nhận ở cả h1 và h4 |
| Có dùng test để chọn không? | Không. Chọn trên kiểm định, test chỉ mở ở notebook 07 |
| Chênh lệch giữa ba loss có ý nghĩa không? | MAE hơn MSE 0,65 điểm ở h1 — lớn hơn 3σ nhiễu huấn luyện (σ = 0,0741 ở lượt hiện hành, 3σ = 0,2224), nên là khác biệt thật |
| 20 trial đủ chưa? | Đường hội tụ ở phụ lục cho thấy phẳng sau ~10 trial |
