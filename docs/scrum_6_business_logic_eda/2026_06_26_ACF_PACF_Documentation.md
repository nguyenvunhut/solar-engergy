# Tài Liệu Hướng Dẫn Kỹ Thuật: Phân Tích Biểu Đồ ACF và PACF

**Dự án:** DATN Outliers Hệ Thống Năng Lượng Mặt Trời (HS NLMT)
**Giai đoạn:** Khám phá dữ liệu (EDA) - Sub-task 3.7
**Mục đích:** Hướng dẫn chi tiết về lý thuyết, vai trò thực tiễn và kỹ thuật vẽ/đọc biểu đồ ACF và PACF cho mô hình dự báo chuỗi thời gian (ARIMA).

---

## 1. Định Nghĩa Lý Thuyết (Bổ sung cơ sở toán học)

Trong phân tích chuỗi thời gian (Time-Series), dữ liệu thường có sự liên kết với quá khứ. Ví dụ, sản lượng điện của ngày hôm nay ($Y_t$) chịu ảnh hưởng bởi ngày hôm qua ($Y_{t-1}$), tuần trước ($Y_{t-7}$), v.v. Các khoảng thời gian lùi lại này được gọi là **Lag** ($k$).

### 1.1 ACF (Autocorrelation Function - Hàm tự tương quan)
- **Định nghĩa:** ACF đo lường mức độ tương quan tổng thể giữa giá trị hiện tại $Y_t$ và giá trị trong quá khứ $Y_{t-k}$.
- **Bản chất:** Sự tương quan này bao gồm cả tác động **trực tiếp** và các tác động **gián tiếp** (hiệu ứng gợn sóng qua các khoảng thời gian trung gian).
- **Công thức toán học:**  
  Với chuỗi dừng, hệ số tự tương quan tại độ trễ $k$ (ký hiệu là $\rho_k$) được tính bằng tỷ số giữa Hiệp phương sai (Covariance) tại độ trễ $k$ và Phương sai (Variance) của chuỗi:
  
  $$ \rho_k = \frac{\text{Cov}(Y_t, Y_{t-k})}{\text{Var}(Y_t)} = \frac{\sum_{t=k+1}^T (Y_t - \bar{Y})(Y_{t-k} - \bar{Y})}{\sum_{t=1}^T (Y_t - \bar{Y})^2} $$
  
  *(Trong đó: $\bar{Y}$ là giá trị trung bình của chuỗi thời gian, $T$ là tổng số quan sát)*

### 1.2 PACF (Partial Autocorrelation Function - Hàm tự tương quan riêng phần)
- **Định nghĩa:** PACF chỉ đo lường sự tương quan **trực tiếp** giữa $Y_t$ và $Y_{t-k}$.
- **Bản chất:** Để tính PACF, ta phải loại bỏ hoàn toàn nhiễu (ảnh hưởng) từ các biến thời gian trung gian như $Y_{t-1}, Y_{t-2}, \dots, Y_{t-k+1}$.
- **Công thức toán học:**  
  Hệ số tự tương quan riêng phần tại độ trễ $k$ (ký hiệu là $\phi_{kk}$) được tính dựa trên hệ số tương quan có điều kiện (loại bỏ đi tác động tuyến tính của các biến trung gian):
  
  $$ \phi_{kk} = \text{Corr}(Y_t, Y_{t-k} | Y_{t-1}, Y_{t-2}, \dots, Y_{t-k+1}) $$
  
  Trong thực tế tính toán, $\phi_{kk}$ thường được ước lượng thông qua hệ phương trình Yule-Walker. Ở các bậc đầu tiên:
  - Lag 1: $\phi_{11} = \rho_1$
  - Lag 2: $\phi_{22} = \frac{\rho_2 - \rho_1^2}{1 - \rho_1^2}$

---

## 2. Vai Trò và Lý Do Áp Dụng Trong Dự Án

Đối với dữ liệu sản lượng điện mặt trời ở cấp độ giờ của hệ thống, việc vẽ ACF và PACF giải quyết 2 mục tiêu mang tính sống còn:

### 2.1 Xác nhận tính chu kỳ mùa vụ (Seasonality)
- Biểu đồ ACF giúp nhóm nhìn thấy rõ ràng các đỉnh (spikes) lặp lại đều đặn mỗi 24 giờ (chu kỳ ngày - đêm) hoặc 8760 giờ (chu kỳ năm). 
- **Ý nghĩa:** Điều này chứng minh bằng toán học rằng các yếu tố thời tiết và sản lượng điện hoàn toàn tuân theo quy luật tự nhiên, không phải là các biến động ngẫu nhiên.

### 2.2 Định vị tham số cho mô hình ARIMA
- Mô hình phân tích chuỗi thời gian ARIMA($p, d, q$) yêu cầu phải xác định chính xác các tham số đầu vào.
- **Biểu đồ PACF:** Dùng để xác định bậc **$p$** (Auto-Regressive - AR).
- **Biểu đồ ACF:** Dùng để xác định bậc **$q$** (Moving Average - MA).
- **Hệ quả:** Nếu bỏ qua hoặc phân tích sai hai biểu đồ này, mô hình AI (ARIMA) sẽ chỉ dự báo theo dạng "mò mẫm" ngẫu nhiên và sinh ra sai số (Delta) cực lớn.

---

## 3. Hướng Dẫn Thực Thi Kỹ Thuật

Đây là hướng dẫn cụ thể dành cho kỹ sư dữ liệu để triển khai code Python bằng thư viện `statsmodels`.

### Bước 1: Chuẩn bị dữ liệu đầu vào
- **Điều kiện bắt buộc:** Dữ liệu đưa vào vẽ ACF/PACF phải là **chuỗi dừng (Stationary Time Series)**.
- **Xử lý:** Nếu dữ liệu (sản lượng điện) có xu hướng tăng/giảm rõ rệt theo thời gian, bắt buộc phải thực hiện phép sai phân (Differencing - tương ứng với tham số $d$ trong ARIMA) trước khi tiến hành vẽ biểu đồ.

### Bước 2: Đoạn mã Python tham khảo
Sử dụng module `tsaplots` từ `statsmodels` để vẽ đồ thị:

```python
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# Giả sử 'hourly_energy' là series dữ liệu sản lượng điện ĐÃ ĐƯỢC LÀM DỪNG
# Khởi tạo khung chứa với 2 biểu đồ đặt cạnh nhau
fig, axes = plt.subplots(1, 2, figsize=(16, 5))

# 1. Vẽ biểu đồ ACF với độ trễ (lag) tối đa 48 giờ (tương đương 2 ngày)
plot_acf(
    df['hourly_energy'].dropna(), 
    lags=48, 
    ax=axes[0], 
    title="Autocorrelation Function (ACF)"
)

# 2. Vẽ biểu đồ PACF với độ trễ (lag) tối đa 48 giờ
plot_pacf(
    df['hourly_energy'].dropna(), 
    lags=48, 
    ax=axes[1], 
    title="Partial Autocorrelation (PACF)"
)

# Hiển thị biểu đồ
plt.show()
```

### Bước 3: Tiêu chuẩn nghiệm thu và Cách đọc biểu đồ
- **Vùng tin cậy:** Trên biểu đồ sẽ xuất hiện một dải mờ màu xanh dương. Đây là vùng tin cậy 95% (Confidence Interval).
- **Đánh giá ý nghĩa:** Bất kỳ thanh dọc (Lag) nào vượt ra ngoài vùng màu xanh dương này đều được coi là có ý nghĩa thống kê (Significant).
- **Chốt tham số:** Đội ngũ cần đếm số lượng các thanh vượt ngưỡng ở những Lag đầu tiên (trước khi đồ thị tiệm cận vào trong dải xanh) để chốt hệ số $p$ (dựa vào PACF) và $q$ (dựa vào ACF) trước khi đưa vào huấn luyện mô hình.
