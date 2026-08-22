# Notebook 02_EDA — Khám phá dữ liệu (`02_EDA.ipynb`)

>  **Về các con số trong file này:** một số giá trị mô tả lượt chạy trước. Giá trị hiện
> hành và lý do từng con số thay đổi: [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md).


> Người đọc mục tiêu: chưa từng làm ML. EDA = Exploratory Data Analysis, "phân tích khám phá
> dữ liệu" — bước NHÌN dữ liệệu trước khi làm bất cứ điều gì với nó.

---

## 1. Vai trò: nhìn trước khi làm

EDA giống bác sĩ khám tổng quát trước khi kê đơn. Không nhìn dữ liệu mà lao vào dựng mô
hình là nguồn gốc của đa số quyết định sai: chọn nhầm thước đo, giữ nhầm cột hỏng, không
biết dữ liệu có "tính cách" gì đặc biệt.

Hai ràng buộc quan trọng của notebook này:

1. **Chỉ nhìn TẬP HUẤN LUYỆN.** Không bao giờ EDA trên tập test — nhìn test rồi thiết kế
   đặc trưng theo những gì thấy được chính là rò rỉ thông tin bằng mắt người.
2. **Chỉ đọc, không ghi dữ liệu** cho bước sau — sản phẩm của nó là hiểu biết, không phải file.

- **Vào:** `02_split/train/v5_train.parquet`
- **Ra:** 2 bảng CSV thống kê + biểu đồ nằm ngay trong notebook

---

## 2. Từng phân tích và cái nó dạy cho dự án

### 2.1. Thống kê mô tả — tách ngày/đêm

Nếu gộp cả đêm, hơn nửa số dòng là 0 (mặt trời lặn), mọi con số trung bình/phân vị đều bị
kéo về gần 0 và chẳng nói lên điều gì. Nên notebook tách: thống kê ban ngày riêng, đêm riêng.

Bài học rút ra cho toàn dự án: **mọi thước đo về sau chỉ tính ban ngày** — nếu chấm điểm cả
đêm, mô hình chỉ cần đoán "0 vào ban đêm" là đã đúng nửa số dòng, điểm đẹp mà vô nghĩa.

### 2.2. Loại trạm 19 và 24 khỏi phạm vi phân tích

Hai trạm này có công suất khai báo (metadata) sai nghiêm trọng: sản lượng đo thật của trạm
19 cao hơn "trần công suất" tính từ metadata tới **4,92 lần** (một nửa số điểm đo vượt trần).
Không phải dữ liệu đo sai — mà là tờ khai công suất sai. Giữ hai trạm này trong phân tích
quy mô sẽ làm mọi thống kê méo mó.

### 2.3. Ngày trời quang vs ngày nhiều mây — vì sao cần ML

Vẽ sản lượng của cùng một trạm trong hai ngày: ngày quang cho đường **hình chuông trơn**
(sáng lên - trưa đỉnh - chiều xuống), ngày mây cho đường **răng cưa** loạn xạ. Cùng giờ,
cùng trạm, cùng mùa — sản lượng khác nhau 4-5 lần chỉ vì mây.

Đây là lý do tồn tại của cả nhánh ML: phần hình chuông thì công thức thiên văn tính được,
phần răng cưa thì phải HỌC từ thời tiết.

### 2.4. ACF/PACF — sản lượng "nhớ" quá khứ bao lâu

ACF (autocorrelation function) đo: giá trị hiện tại giống giá trị cách đây N bước đến mức
nào. Kết quả cho thấy tương quan mạnh ở trễ ngắn (15-60 phút) và một đỉnh cao đúng ở trễ
96 bước = 24 giờ (nhịp ngày). Đây là căn cứ dữ liệu cho việc notebook 03_1 chọn lag 4 và
lag 96 làm đặc trưng — không phải chọn tùy hứng.

### 2.5. Tương quan Spearman — chỉ tính ban ngày

Đo mức độ đồng biến giữa sản lượng và từng biến thời tiết. Dùng **Spearman** (theo thứ
hạng) thay vì Pearson (tuyến tính) vì quan hệ bức xạ→sản lượng có đoạn cong bão hòa —
Spearman bắt được quan hệ đơn điệu bất kể hình dạng đường cong.

Kết quả chính: `shortwave_radiation` tương quan mạnh nhất với sản lượng — củng cố vai trò
biến thời tiết số một của toàn pipeline.

---

## 3. Điều 02_EDA KHÔNG làm (và vì sao đó là thiết kế đúng)

- Không sửa dữ liệu, không loại dòng nào — phát hiện của nó chuyển thành quyết định ở các
  notebook sau (ví dụ: loại 19/24 được thực thi trong bước trọng số của notebook 06).
- Không kết luận nhân quả — tương quan cao không có nghĩa là nguyên nhân; EDA chỉ gợi ý
  hướng, thực nghiệm (nhóm notebook 05x) mới là nơi chứng minh.
