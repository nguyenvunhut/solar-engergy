# PHÂN HỆ TIỀN XỬ LÝ & NHẬN DIỆN DỊ THƯỜNG (02_TRANSFORM)

Phân hệ `srcs/02_transform/` là hạt nhân xử lý dữ liệu của hệ thống, thực hiện làm sạch dữ liệu, điền khuyết nhân quả 4 cấp độ và nhận diện dị thường vận hành bằng mô hình lai GMM-IF kết hợp 5 rào chắn vật lý.

---

## 1. CÁC MODULE TRỌNG TÂM

### 1.1. Điền khuyết Nhân quả Đa tầng (`02_run_hybrid_imputation.py`)
Xử lý $1.536.000$ ô khuyết ($35{,}99\%$) theo chuỗi 4 cấp độ tuân thủ chiều thời gian:
1. **Cấp 1 — Cắt Đêm Vật Lý ($E = 0{,}0\,\text{kWh}$):** Áp dụng góc nâng mặt trời $\alpha \le -0{,}833^\circ$ hoặc $GHI \le 20\,\text{W/m}^2$ $\to$ Xử lý $1.383.493$ ô khuyết ($90{,}05\%$).
2. **Cấp 2 — Nội suy Tuyến tính ($Gap \le 30\,\text{phút}$):** Dựa trên hệ số tự tương quan $r_1 > 0{,}98$ $\to$ Xử lý $53.684$ ô khuyết ($3{,}49\%$).
3. **Cấp 3 — PCHIP Cubic Spline ($45\text{p} \le Gap \le 2\text{h}$):** Nội suy bảo toàn tính đơn điệu không vọt âm $\to$ Xử lý $50.704$ ô khuyết ($3{,}30\%$).
4. **Cấp 4 — Khung mẫu Lịch sử KNN Khí tượng ($Gap > 2\text{h}$):** Khôi phục từ ngày quá khứ tương đồng $\to$ Xử lý $48.519$ ô khuyết ($3{,}16\%$).

### 1.2. Nhận diện Dị thường Lai GMM-IF & 5 Rào chắn Vật lý (`02_run_apply_outlier_flags.py`)
- **Tầng 1 (CART):** Phân đoạn không gian thời tiết thành các vùng lá đồng nhất ($R^2 \approx 0{,}758$).
- **Tầng 2 (GMM):** Đánh giá mật độ xác suất cục bộ $p(x) < 0{,}02$.
- **Tầng 3 (Isolation Forest):** Lọc ngoại lai toàn cục với contamination $3\%$.
- **Tầng 4 (5 Rào chắn Vật lý):** Kiểm định các quy tắc vật lý (`PHYSICAL_NIGHT_POSITIVE`, `PHYSICAL_OVER_CAPACITY`, `PHYSICAL_ZERO_DAYLIGHT`, `PHYSICAL_LOW_ENERGY_STRONG_SUN`, `PHYSICAL_DISTRIBUTION_JUMP`).
- **Kết quả:** Định vị và dán nhãn $104$ giờ ngoại lai ($0{,}45\%$ dữ liệu toàn mạng lưới).

---

## 2. HƯỚNG DẪN THỰC THI

```bash
# Thực hiện điền khuyết nhân quả:
python srcs/02_transform/02_run_hybrid_imputation.py

# Áp dụng bộ lọc dị thường lai GMM-IF:
python srcs/02_transform/02_run_apply_outlier_flags.py
```
