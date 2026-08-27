# BÁO CÁO KIỂM TOÁN CHI TIẾT: HẠNG MỤC 5 — MÁI CHE NẮNG BIẾN TẦN & BỘ TỐI ƯU HÓA CÔNG SUẤT DC OPTIMIZERS

> **Dự án:** 42 Trạm Điện Mặt Trời Áp Mái La Trobe  
> **Dữ liệu nguồn:** $683.665$ dòng cấp giờ (`temperature_c`, `shortwave_radiation`, `site_id`)  
> **Cơ chế kỹ thuật:** Triệt tiêu hiện tượng Inverter Thermal Derating ($>72^\circ\text{C}$ Heatsink) và MPPT cấp chuỗi cho 6 trạm bóng che.

---

## 1. Cơ Sở Kỹ Thuật & Diễn Giải Chi Tiết Các Công Thức

### 1.1. Công thức Giảm Tải Biến Tần do Quá Nhiệt Tản Nhiệt (Inverter Thermal Derating)

$$
\Delta e_{\text{inv, derate}}(t) = \begin{cases}
0{,}20 \times e_{\text{expected}}(t), & \text{khi } temperature_{\text{c}}(t) \ge 35^\circ\text{C} \text{ và } shortwave_{\text{radiation}}(t) \ge 800\,\text{W/m}^2 \\
0, & \text{ngược lại}
\end{cases}
$$

**Diễn giải chi tiết:**
* Khi nhiệt độ không khí $\ge 35^\circ\text{C}$ kết hợp bức xạ trực xạ mạnh $\ge 800\,\text{W/m}^2$, vỏ kim loại và bộ tản nhiệt (Heatsink) của biến tần ngoài trời bị nung nóng vượt ngưỡng an toàn $72^\circ\text{C}$.
* Thuật toán vi điều khiển Inverter tự động kích hoạt chế độ bảo vệ nhiệt độ: Cắt giảm $20\%$ công suất phát để hạ nhiệt cuộn cảm và module bán dẫn công suất IGBT.
* Việc lắp mái che nhôm phản xạ nắng giúp giảm bức xạ nhiệt chiếu trực tiếp vào vỏ máy, hạ nhiệt Heatsink xuống dưới $65^\circ\text{C}$, triệt tiêu hoàn toàn chế độ Derating và bảo vệ tuổi thọ tụ điện.

---

### 1.2. Công thức Tối ưu hóa Chuỗi Pin Che bóng Cục bộ bằng DC Optimizers

$$
\Delta e_{\text{dc, opt}}(t) = \begin{cases}
0{,}12 \times e_{\text{hourly}}(t), & \text{khi } site_{\text{id}} \in [6\text{ Shaded Sites}] \text{ và } hour(t) \in [8, 10] \cup [15, 17] \\
0, & \text{ngược lại}
\end{cases}
$$

**Diễn giải chi tiết:**
* Tại 6 trạm bị che bóng cục bộ do cây cối hoặc lan can tòa nhà vào đầu giờ sáng và cuối giờ chiều, các tấm pin bị bóng che làm sụt dòng điện toàn bộ chuỗi nối tiếp.
* Bộ tối ưu hóa công suất DC Optimizer gắn tại từng tấm pin cho phép dò điểm cực đại MPPT độc lập ở cấp độ từng module, giúp các tấm pin không bị che phát tối đa công suất mà không bị kìm hãm bởi tấm pin bị che.

---

## 2. Đoạn Mã Nguồn Thực Thi Tính Toán Trong Codebase

Logic quét giờ Derating và tối ưu hóa Inverter được hiện thực hóa tại [`srcs/07_dashboard/api/bimart/services/phan_ra.py`](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/srcs/07_dashboard/api/bimart/services/phan_ra.py):

```python
# File: srcs/07_dashboard/api/bimart/services/phan_ra.py (Dong 141-151)
def gio_derating_theo_thang() -> pd.DataFrame:
    h = repo.doc_hourly()
    d = h.assign(thang=h["date_id"] // 100 % 100)
    # 1. Dieu kien Inverter bi Derating: Nhiet do >= 35C VA Buc xa >= 800 W/m2
    d["nong"] = (d["temperature_c"] >= 35) & (d["shortwave_radiation"] >= 800)
    # 2. Dieu kien canh bao som: Nhiet do >= 30C VA Buc xa >= 700 W/m2
    d["cham_nguong"] = (d["temperature_c"] >= 30) & (d["shortwave_radiation"] >= 700)
    g = (d.groupby("thang").agg(gio_derating=("nong", "sum"), gio_canh_bao=("cham_nguong", "sum"))
           .reindex(range(1, 13)).fillna(0).reset_index())
    g["ten"] = [TEN_THANG[i - 1] for i in g["thang"]]
    return g
```

---

## 3. Thống Kê Số Giờ Chạm Ngưỡng Derating Biến Tần Trong Dữ Liệu Thực Tế

| Tháng | Mùa Vụ | Số Giờ Cảnh Báo (≥30°C & ≥700 W/m²) | Số Giờ Giảm Tải Derating (≥35°C & ≥800 W/m²) | Sản Lượng Thu Hồi Dự Kiến (kWh) |
| :--- | :--- | :---: | :---: | :---: |
| Th1 | Mùa Hè | 4336 giờ | 454 giờ | 12894 kWh |
| Th2 | Mùa Hè | 932 giờ | 38 giờ | 1079 kWh |
| Th3 | Mùa Thu | 175 giờ | 3 giờ | 85 kWh |
| Th4 | Mùa Thu | 20 giờ | 0 giờ | 0 kWh |
| Th5 | Mùa Thu | 0 giờ | 0 giờ | 0 kWh |
| Th6 | Mùa Đông | 0 giờ | 0 giờ | 0 kWh |
| Th7 | Mùa Đông | 0 giờ | 0 giờ | 0 kWh |
| Th8 | Mùa Đông | 0 giờ | 0 giờ | 0 kWh |
| Th9 | Mùa Xuân | 1 giờ | 0 giờ | 0 kWh |
| Th10 | Mùa Xuân | 11 giờ | 0 giờ | 0 kWh |
| Th11 | Mùa Xuân | 429 giờ | 21 giờ | 596 kWh |
| Th12 | Mùa Hè | 1294 giờ | 134 giờ | 3806 kWh |
| **CẢ NĂM** | — | **7,198 Giờ** | **650 Giờ** | **18.450 kWh/NĂM** |

---

## 4. Hiệu Quả Thu Hồi Điện & Bảo Vệ Thiết Bị

* **Thu hồi từ tấm che nắng Inverter:** **$+18.450\,\text{kWh/năm}$** và ngăn ngừa nguy cơ nổ tụ/hỏng sớm 2 bộ Inverter ($16.000\,\text{AUD}$).
* **Thu hồi từ DC Optimizers cho 6 trạm che bóng ($320\,\text{kWp}$):** **$+38.624\,\text{kWh/năm}$**.
* **Tổng điện năng thu hồi:** **$57.074\,\text{kWh/năm}$**.
* **Chi phí đầu tư CapEx:** **$12.500\,\text{AUD}$** (gồm $4.500\,\text{AUD}$ mái che $+ 8.000\,\text{AUD}$ bộ tối ưu DC).
* **Giá trị kinh tế hàng năm:** **$11.415\,\text{AUD/năm}$**.
* **Thời gian hoàn vốn:**

$$
\text{Payback} = \frac{12.500\,\text{AUD}}{11.415\,\text{AUD/năm}} = \mathbf{1{,}10\,\text{Năm}}
$$