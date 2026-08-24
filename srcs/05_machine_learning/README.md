# PHÂN HỆ MÔ HÌNH HỌC MÁY DỰ BÁO CÔNG SUẤT (05_MACHINE_LEARNING)

Phân hệ `srcs/05_machine_learning/` chứa toàn bộ đường ống huấn luyện, tối ưu hóa siêu tham số, suy luận đa bước và kiểm định tính giải thích (XAI) cho mô hình dự báo sản lượng điện mặt trời ngắn hạn.

---

## 1. KIẾN TRÚC MÔ HÌNH & KỸ THUẬT NỔI BẬT

1. **Chuẩn hóa Mục tiêu Vật lý (Physics-Guided Normalization):**
   Biến đổi mục tiêu $k(t) = \frac{E(t)}{P_{\text{stc}} \cdot \sin(\alpha(t))}$ nhằm loại bỏ quy luật nhật động hình sin theo góc nâng mặt trời, giúp mô hình tập trung học tương tác phi tuyến của mây và nhiệt độ.
2. **Kỹ nghệ 52 Đặc trưng (Feature Engineering):**
   - Biến khí tượng: $GHI, DNI, DHI$, nhiệt độ môi trường $T_{\text{ambient}}$, tốc độ gió, độ che phủ mây.
   - Biến thiên văn: Góc nâng mặt trời $\alpha$, góc thiên đỉnh, Air Mass ($AM1.5$).
   - Biến chuỗi thời gian: Lags ($15\text{p}, 30\text{p}, 1\text{h}, 24\text{h}$), Rolling Mean/Std ($1\text{h}, 3\text{h}$).
   - Sàng lọc đa cộng tuyến bằng chỉ số VIF (loại bỏ $VIF \ge 10$).
3. **Mô hình Cốt lõi & Hàm Mất mát:**
   - Thuật toán cây tăng cường **LightGBM Regressor**.
   - Hàm mất mát kháng ngoại lai **Huber Loss ($\delta = 1{,}0$)**.
   - Tối ưu hóa siêu tham số bằng **Optuna Bayesian Optimization (TPE)**.
   - Kiểm định bằng **5-Fold Time-Series Cross Validation**.

---

## 2. HIỆU NĂNG DỰ BÁO TRÊN TẬP KIỂM THỬ NIÊM PHONG

| Tầm Dự Báo | WAPE (%) | Hệ số Xác định ($R^2$) | RMSE (kWh) | MAE (kWh) |
| :--- | :---: | :---: | :---: | :---: |
| **$H_1$ ($T + 15\text{ phút}$)** | **$17{,}74\%$** | **$0{,}9243$** | $3{,}414$ | $1{,}379$ |
| **$H_4$ ($T + 60\text{ phút}$)** | **$22{,}62\%$** | **$0{,}8864$** | $4{,}183$ | $1{,}759$ |
| **Mô hình Cơ sở Prophet** | $35{,}12\%$ | $0{,}6410$ | $6{,}780$ | $2{,}730$ |

> *Kết quả: LightGBM giúp giảm **$49{,}5\%$** sai số so với mô hình cơ sở Prophet.*

---

## 3. HƯỚNG DẪN THỰC THI PIPELINE ML

```bash
# Xem danh sách các giai đoạn:
python -u srcs/05_machine_learning/forcasting_pipeline/run.py --list

# Chạy toàn bộ pipeline huấn luyện và đánh giá:
python -u srcs/05_machine_learning/forcasting_pipeline/run.py --stage all
```
