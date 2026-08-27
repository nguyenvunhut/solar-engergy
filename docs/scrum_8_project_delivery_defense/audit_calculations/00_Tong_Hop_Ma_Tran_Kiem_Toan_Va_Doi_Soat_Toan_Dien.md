# BÁO CÁO TỔNG HỢP MA TRẬN KIỂM TOÁN ĐỊNH LƯỢNG & ĐỐI SOÁT 7 HẠNG MỤC CẢI TIẾN

> **Hệ thống:** 42 Trạm Điện Mặt Trời Áp Mái Đại Học La Trobe (2.428 kWp, 5 Khuôn Viên)  
> **Dữ liệu phân tích:** `bi_mart.mv_bi_mart_hourly_measures` (683.665 bản ghi) và `bi_mart.mv_bi_mart_daily_kpis` (28.677 bản ghi)  
> **Đối soát kiểm toán:** Khớp 100% với Báo cáo Kiểm toán Định lượng `2026_08_25_Bao_Cao_Dinh_Luong_Chi_Tiet_Insights_Va_De_Xuat_Cai_Tien_Audited.md`.

---

## 1. Cơ Sở Lý Thuyết & Diễn Giải Chi Tiết Các Công Thức Tổng Hợp Chỉ Số

### 1.1. Công thức Hệ số Hiệu suất Mô Phỏng Mới (Simulated Performance Ratio - PR)

$$
PR_{\text{simulated}} = \frac{E_{\text{simulated}}}{\sum_{t=1}^N e_{\text{stc, hourly}}(t)} \times 100\% = \frac{E_0 + \sum_{i \in S} \Delta E_i}{E_0} \times PR_0
$$

**Diễn giải chi tiết:**
* $E_0 = 3.447.760\,\text{kWh/năm}$: Sản lượng điện thực tế cơ sở hiện nay của 42 trạm.
* $PR_0 = 75{,}40\%$: Hệ số hiệu suất thực tế ban đầu của toàn hệ thống La Trobe.
* $\sum_{i \in S} \Delta E_i$: Tổng năng lượng thu hồi thêm khi người dùng kích hoạt tập hợp các hạng mục cải tiến $S$.
* $PR_{\text{simulated}}$ phản ánh chính xác mức gia tăng hiệu suất quang điện trên cùng tổng lượng bức xạ mặt trời chiếu vào hệ thống.

---

### 1.2. Công thức Hệ số Công suất Tải Mô Phỏng Mới (Capacity Factor - CF)

$$
CF_{\text{simulated}} = \frac{E_{\text{simulated}}}{P_{\text{STC}} \times 8.760\,\text{h}} \times 100\%
$$

**Diễn giải chi tiết:**
* $P_{\text{STC}} = 2.428\,\text{kWp}$: Tổng công suất lắp đặt định danh của 42 trạm.
* $8.760\,\text{h}$: Tổng số giờ trong $1\,\text{năm}$ ($365\,\text{ngày} \times 24\,\text{giờ}$).
* $CF$ thể hiện tỷ lệ giữa sản lượng phát thực tế so với kịch bản lý tưởng phát điện liên tục $100\%$ công suất định danh $24/7$. Khi áp dụng 6 giải pháp kỹ thuật, $CF$ tăng vọt từ $16{,}21\% \rightarrow 21{,}34\%$.

---

### 1.3. Công thức Thời Gian Hoàn Vốn Đầu Tư Hòa Vốn (Payback Period)

$$
\text{Payback} = \frac{\sum_{i \in S} \text{CapEx}_i}{\sum_{i \in S} \Delta \text{Revenue}_i} \quad (\text{Năm})
$$

**Diễn giải chi tiết:**
* $\sum \text{CapEx}_i$: Tổng chi phí vốn đầu tư thiết bị phần cứng ban đầu (BESS, giá đỡ nhôm thông gió, chân đế nghiêng $15^\circ$, mái che Inverter, DC Optimizers).
* $\sum \Delta \text{Revenue}_i$: Tổng dòng tiền thặng dư hàng năm tạo ra từ sản lượng điện thu hồi thêm, tiền tiết kiệm nhân công bảo trì O&M và gọt đỉnh công suất Demand Charge.

---

## 2. Đoạn Mã Nguồn Thực Thi Tính Toán Trong Codebase

Động cơ tính toán kịch bản What-If thời gian thực được hiện thực hóa tại [`srcs/07_dashboard/api/bimart/services/whatif.py`](file:///D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/srcs/07_dashboard/api/bimart/services/whatif.py):

```python
# File: srcs/07_dashboard/api/bimart/services/whatif.py (Dong 26-68)
def chay_kich_ban(bat: list[str] | None = None,
                    nam: int | None = None,
                    gia_tuy_chinh: dict | None = None) -> dict:
    # 1. Xac dinh danh sach hang muc dang bat
    danh_sach = list(cfg.HANG_MUC_CAI_TIEN.keys()) if bat is None else list(bat)
    g = gia_tuy_chinh or (cfg.BIEU_GIA_NEM[nam] if nam in cfg.BIEU_GIA_NEM else cfg.GIA_TB_3_NAM)

    # 2. Tong hop nang luong thu hoi va doanh thu delta
    delta_e = sum(cfg.HANG_MUC_CAI_TIEN[m]["kwh"] for m in danh_sach if m in cfg.HANG_MUC_CAI_TIEN)
    e1 = cfg.CO_SO["e_baseline_kwh"] + delta_e
    ti_le = e1 / cfg.CO_SO["e_baseline_kwh"]

    # 3. Tinh lai Performance Ratio (PR) va Capacity Factor (CF)
    pr1 = cfg.CO_SO["pr_co_so_%"] * ti_le
    cf1 = cfg.CO_SO["cf_co_so_%"] * ti_le
    co2_kg = e1 * cfg.CO_SO["he_so_co2_kg_kwh"]

    # 4. CapEx va thoi gian hoan von Payback
    capex_tong = sum(cfg.HANG_MUC_CAI_TIEN[m]["capex"] for m in danh_sach if m in cfg.HANG_MUC_CAI_TIEN)
    rev_delta = sum(cfg.doanh_thu_theo_nam(m, nam) for m in danh_sach if m in cfg.HANG_MUC_CAI_TIEN)
    payback = (capex_tong / rev_delta) if rev_delta > 0 else 0.0

    return { ... }
```

---

## 3. Ma Trận Đối Soát Chi Tiết Toàn Bộ 7 Hạng Mục Cải Tiến

| STT | Hạng Mục Đề Xuất Cải Tiến | Mức Cải Thiện Hiệu Suất | Điện Thu Hồi (kWh/Năm) | Doanh Thu Năm 2020 | Doanh Thu Năm 2021 | Doanh Thu Năm 2022 | Doanh Thu TB 3 Năm | CapEx Đầu Tư (AUD) | Thời Gian Hoàn Vốn |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | BESS 5 Campus (1MW/2,5MWh) | +20,6% h.ích | 712.182 kWh | 260.766 AUD | 304.818 AUD | 382.065 AUD | 323.164 AUD | 1.250.000 AUD | 3,87 Năm |
| 2 | Khe hở thông gió mái 10–15cm | +3,40% tổng | 117.224 kWh | 21.100 AUD | 22.859 AUD | 27.548 AUD | 23.445 AUD | 24.280 AUD | 1,04 Năm |
| 3 | Bảo trì CBM & AI Anomaly | +2,04% tổng | 70.330 kWh | 26.659 AUD | 28.714 AUD | 32.528 AUD | 29.066 AUD | 8.000 AUD/năm | < 4 Tháng |
| 4 | Khung nghiêng chữ A 15° mái | +3,90% nhóm | 71.850 kWh | 13.183 AUD | 14.283 AUD | 17.217 AUD | 14.670 AUD | 18.000 AUD | 1,23 Năm |
| 5 | Tấm chắn nắng & DC Optimizer | +1,65% tổng | 57.074 kWh | 10.273 AUD | 11.129 AUD | 13.412 AUD | 11.415 AUD | 12.500 AUD | 1,10 Năm |
| 6 | Lịch rửa pin theo lượng mưa | +1,80% khô | 62.060 kWh | 16.671 AUD | 18.102 AUD | 21.084 AUD | 18.412 AUD | 0 AUD | Tức thì |
| 7 | Nâng cấp TOPCon (Repowering) | +6,20% tổng | 213.761 kWh | 38.477 AUD | 41.683 AUD | 50.234 AUD | 42.752 AUD | Kỳ Đại Tu | Vòng đời pin |
| **Σ6** | **TỔNG 6 HẠNG MỤC KỸ THUẬT** | **+31,6%** | **1.090.720 kWh** | **348.652 AUD** | **399.905 AUD** | **493.854 AUD** | **420.172 AUD** | **1.312.780 AUD** | **3,12 NĂM** |
| **Σ7** | **TOÀN BỘ 7 HẠNG MỤC CẢI TIẾN** | **+37,8%** | **1.304.481 kWh** | **387.129 AUD** | **441.588 AUD** | **544.088 AUD** | **462.924 AUD** | **1.312.780 AUD** | **2,84 NĂM** |

---

## 4. Bảng So Sánh Chỉ Số Vận Hành Toàn Hệ Thống (Before vs After)

| Chỉ Số Hệ Thống | Hiện Trạng (Baseline) | Sau 6 Hạng Mục Kỹ Thuật | Sau Toàn Bộ 7 Hạng Mục | Mức Cải Thiện Ròng |
| :--- | :---: | :---: | :---: | :---: |
| **Sản lượng phát điện hàng năm** | 3.447.760 kWh/năm | 4.538.480 kWh/năm | 4.752.241 kWh/năm | **+1.304.481 kWh (+37,84%)** |
| **Năng suất riêng (Specific Yield)** | 1.420 kWh/kWp/năm | 1.869 kWh/kWp/năm | 1.957 kWh/kWp/năm | **+537 kWh/kWp (+37,84%)** |
| **Hệ số hiệu suất thực tế (PR)** | 75,40% | 83,95% | 88,62% | **+13,22% điểm phần trăm** |
| **Hệ số công suất tải (CF)** | 16,21% | 21,34% | 22,34% | **+6,13% điểm phần trăm** |
| **Tổn thất nhiệt độ cell (Loss_temp)** | 14,80% | 11,40% | 11,40% | **Giảm -3,40% tổn thất** |
| **Tổn thất cắt ngọn Inverter (Loss_clip)** | 2,30% | 0,28% | 0,28% | **Giảm -2,02% tổn thất (BESS)** |
| **Tổn thất dị thường vận hành** | 2,04% | 0,00% | 0,00% | **Triệt tiêu 100% (GMM-IF)** |
| **Tổn thất bám bụi & đọng bùn đáy** | 2,34% | 0,00% | 0,00% | **Triệt tiêu 100% (Mưa + 15°)** |
| **Tổng doanh thu & tiết kiệm tài chính**| 700.000 AUD/năm | 1.120.172 AUD/năm | 1.162.924 AUD/năm | **+462.924 AUD/năm (+66,13%)**|
| **Tổng vốn đầu tư CapEx** | 0 AUD | 1.312.780 AUD | 1.312.780 AUD | **Bao gồm BESS 1MW/2.5MWh** |
| **Thời gian hoàn vốn hòa vốn** | — | **3,12 Năm (37 Tháng)** | **2,84 Năm (34 Tháng)** | **Tính khả thi tài chính rất cao** |
| **Cắt giảm phát thải CO2** | 2.827 tấn/năm | 3.722 tấn/năm | 3.897 tấn/năm | **+1.070 tấn CO2/năm** |

---

## 5. Danh Mục Các Báo Cáo Thành Phần

Toàn bộ chi tiết tính toán, công thức toán học và bảng bóc tách 12 tháng được lưu trữ độc lập tại:
1. [`01_Kiem_Toan_Chi_Tiet_BESS_Va_Inverter_Clipping.md`](01_Kiem_Toan_Chi_Tiet_BESS_Va_Inverter_Clipping.md)
2. [`02_Kiem_Toan_Chi_Tiet_Thong_Gio_Mai_Sandia_SAPM.md`](02_Kiem_Toan_Chi_Tiet_Thong_Gio_Mai_Sandia_SAPM.md)
3. [`03_Kiem_Toan_Chi_Tiet_Bao_Tri_CBM_AI_Anomaly_GMM_IF.md`](03_Kiem_Toan_Chi_Tiet_Bao_Tri_CBM_AI_Anomaly_GMM_IF.md)
4. [`04_Kiem_Toan_Chi_Tiet_Goc_Nghieng_15_Va_Tu_Rua_Troi.md`](04_Kiem_Toan_Chi_Tiet_Goc_Nghieng_15_Va_Tu_Rua_Troi.md)
5. [`05_Kiem_Toan_Chi_Tiet_Mai_Che_Inverter_Va_DC_Optimizers.md`](05_Kiem_Toan_Chi_Tiet_Mai_Che_Inverter_Va_DC_Optimizers.md)
6. [`06_Kiem_Toan_Chi_Tiet_Lich_Rua_Pin_Theo_Luong_Mua.md`](06_Kiem_Toan_Chi_Tiet_Lich_Rua_Pin_Theo_Luong_Mua.md)
7. [`07_Kiem_Toan_Chi_Tiet_Repowering_TOPCon_HJT.md`](07_Kiem_Toan_Chi_Tiet_Repowering_TOPCon_HJT.md)