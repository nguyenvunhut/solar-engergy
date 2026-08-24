# THƯ VIỆN NOTEBOOKS THỰC NGHIỆM VÀ PHÂN TÍCH (NOTEBOOKS)

Thư mục `notebooks/` chứa các sổ tay tương tác Jupyter Notebook phục vụ quá trình khám phá dữ liệu (EDA), thử nghiệm thuật toán điền khuyết, phát hiện dị thường và xây dựng các phiên bản tiền thân của Pipeline Machine Learning.

---

## 1. PHÂN BỐ CÁC THƯ MỤC THỰC NGHIỆM

| Thư mục | Vai trò và Nội dung Thực nghiệm |
| :--- | :--- |
| **`EDA/`** | **Phân tích Khám phá Dữ liệu Toàn diện:**<br/>- Khảo sát phân bố sản lượng điện mặt trời 42 trạm phát và tương quan với các biến bức xạ ($GHI, DNI, DHI$).<br/>- Đánh giá hiện tượng suy hao nhiệt độ ($\gamma = -0{,}38\%/^\circ\text{C}$) và nghịch lý mùa vụ của hệ số hiệu suất $PR$.<br/>- Phân tích chu kỳ ngày - đêm và phân đoạn vi khí hậu tại 5 cơ sở trường học. |
| **`forcasting_v3_energy/`** | **Bộ Notebook Kiểm định Tính Nhân quả & Tiền xử lý v3:**<br/>- `00_hotfix_join_causal_audit.ipynb`: Kiểm toán rò rỉ dữ liệu khí tượng (Data Leakage Audit), xác nhận $100\%$ không có bản ghi nào bị rò rỉ tương lai.<br/>- Thực nghiệm các phương pháp điền khuyết (Linear Interpolation, PCHIP Spline, KNN Khí tượng). |
| **`forcasting_v4_energy/`** | **Thực nghiệm Kỹ nghệ Đặc trưng & Sàng lọc Đa cộng tuyến v4:**<br/>- Trích xuất 52 biến trễ chuỗi thời gian, biến thiên văn (góc nâng $\alpha$, góc thiên đỉnh) và biến tương tác bức xạ.<br/>- Kiểm định hệ số phóng đại phương sai (VIF Diagnostics) và kiểm tra tương quan tuyến tính/phi tuyến. |
| **`forecasting/`** | **Thực nghiệm Huấn luyện & Đối chứng Mô hình:**<br/>- Xây dựng mô hình cơ sở (Baseline Prophet, Baseline ARIMA).<br/>- Tối ưu hóa mô hình cây tăng cường LightGBM Regressor với hàm mất mát kháng ngoại lai Huber Loss ($\delta = 1{,}0$).<br/>- Đánh giá năng lực dự báo đa bước H1 ($15\text{p}$, WAPE = $17{,}74\%$) và H4 ($60\text{p}$, WAPE = $22{,}62\%$). |

---

## 2. NGUYÊN TẮC QUẢN LÝ VÀ CHUYỂN GIAO MÃ NGUỒN

1. **Từ Prototype sang Production:** Toàn bộ các thuật toán và hàm tính toán sau khi được kiểm định thành công trong `notebooks/` đã được tái cấu trúc thành mã nguồn Python chuẩn mực trong thư mục [`srcs/`](../srcs/) để phục vụ vận hành tự động.
2. **Tính Tái lập (Reproducibility):** Các notebook sử dụng dữ liệu đã được làm sạch hoặc dữ liệu xuất từ Data Marts với seed ngẫu nhiên cố định nhằm đảm bảo kết quả phân tích có thể tái tạo chính xác.
