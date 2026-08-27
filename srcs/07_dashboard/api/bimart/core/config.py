"""Tham so cau hinh cua phan mo phong What-If — nhanh BI Mart.

Tap trung toan bo hang so tai mot noi de bao dam nhat quan giua cac tang
service, API va giao dien.

Nguon tham chieu:
  docs/scrum_8_project_delivery_defense/
    2026_08_26_Brief_Thiet_Ke_Streamlit_What_If_Optimization_Dashboard.md
    2026_08_25_Bao_Cao_Dinh_Luong_Chi_Tiet_Insights_Va_De_Xuat_Cai_Tien_Audited.md
"""
from __future__ import annotations

# ── Bieu gia NEM Victoria, don vi AUD/kWh ────────────────────────────────────
# Nguon: bao cao audited muc 2.2. Giu ca 3 nam de doi chieu, mac dinh dung TB.
BIEU_GIA_NEM = {
    2020: {"retail": 0.195, "fit": 0.102, "tou_peak": 0.285, "bien_bess": 0.183,
           "demand_charge_kw": 13.50, "weighted": 0.180},
    2021: {"retail": 0.210, "fit": 0.075, "tou_peak": 0.310, "bien_bess": 0.235,
           "demand_charge_kw": 14.50, "weighted": 0.195},
    2022: {"retail": 0.255, "fit": 0.052, "tou_peak": 0.365, "bien_bess": 0.313,
           "demand_charge_kw": 17.00, "weighted": 0.235},
}
GIA_TB_3_NAM = {"retail": 0.220, "fit": 0.076, "tou_peak": 0.320, "bien_bess": 0.244,
                "demand_charge_kw": 15.00, "weighted": 0.203}

# ── Khung gio cao diem TOU ───────────────────────────────────────────────────
# Bao cao muc 2.2: "Bieu gia dien gio cao diem toi TOU (17:00 - 21:00)".
GIO_CAO_DIEM = (17, 21)

# ── Hang so BESS ─────────────────────────────────────────────────────────────
ILR = 1.25                  # Inverter Loading Ratio -> P_AC_max = p_stc / 1,25
ETA_RTE = 0.88              # hieu suat vong sac-xa, brief muc 4.2 hang muc 1

# ── Mo hinh nhiet Sandia SAPM (hang muc thong gio mai) ────────────────────────
# Brief muc 4.2 hang muc 2. Hai bo he so cho hai kieu lap dat.
SAPM_FLUSH = {"a": -2.98, "b": -0.0471}     # ap sat mai
SAPM_OPEN = {"a": -3.56, "b": -0.0750}      # co khoang ho thong gio
SAPM_DELTA_T = 3.0                          # do C tren 1000 W/m2

# ── Don vi tien ──────────────────────────────────────────────────────────────
# Bieu gia trong tai lieu tinh bang AUD/kWh. Cot `fit_rate` cua materialized view
# luu theo VND (01_bi_mart_params.yaml: fit_rate_vnd_per_kwh = 1938) nen khong dung
# truc tiep; moi phep quy doi tien deu lay tu BIEU_GIA_NEM / GIA_TB_3_NAM o tren.

# ── He so nhiet ──────────────────────────────────────────────────────────────
# Brief muc 4.2 dung 0,0038 /doC cho cong thuc thong gio mai.
# Cot `loss_temp` cua materialized view duoc sinh voi 0,004 (01_bi_mart_params.yaml).
HE_SO_NHIET_BRIEF = 0.0038
HE_SO_NHIET_MV = 0.004

# ── Pham vi cai dat ──────────────────────────────────────────────────────────
# Brief muc 4.2 cung cap cong thuc tren tung dong cho ba hang muc: BESS, thong gio
# mai va CBM. Bon hang muc con lai duoc mo phong theo so tong hop o muc 3.

# ═════════════════════════════════════════════════════════════════════════════
#  BO THONG SO CO SO — brief muc 2 "HISTORICAL BASELINE METRICS"
#  Bao cao audited muc 2.1
# ═════════════════════════════════════════════════════════════════════════════
CO_SO = {
    "so_tram": 42,
    "cong_suat_dc_kwp": 2428,
    "cum_mai_bang_kwp": 970,
    "cum_mai_bang_kwh": 1_377_400,
    "e_baseline_kwh": 3_447_760,          # kWh/nam
    "yield_kwh_kwp": 1420,
    "pr_baseline": 0.7540,
    "cf_baseline": 0.1621,
    "revenue_baseline_aud": 700_000,
    "co2_baseline_kg": 2_827_163,
    "co2_kg_moi_kwh": 0.82,
    "so_dong_15p": 2_731_946,
    "so_co_if": 6891,
}

# 5 khuon vien — brief muc 2
CAMPUS = {
    "Bundoora":       {"kwp": 1540, "so_tram": 26},
    "Bendigo":        {"kwp": 510,  "so_tram": 8},
    "Albury-Wodonga": {"kwp": 240,  "so_tram": 4},
    "Shepparton":     {"kwp": 78,   "so_tram": 2},
    "Mildura":        {"kwp": 60,   "so_tram": 2},
}

# Cac thanh phan ton that co so — brief muc 2
# `sau`: ty le ton that con lai khi hang muc tuong ung duoc ap dung — brief muc 3,
# phan "Tac dong chi so" cua tung hang muc.
# `ty_le` quy ve MOT mau so chung la E_baseline toan he thong, suy tu `kwh` de sau
# thanh phan so sanh duoc voi nhau tren cung bieu do.
# `ty_le_nhom` la ty le ghi trong tai lieu khi tinh rieng cho nhom tram lien quan —
# vi du goc nghieng tinh tren cum 970 kWp mai bang, khong phai tren ca 2.428 kWp.
TON_THAT_CO_SO = {
    "temp":    {"ten": "Tấm pin bị nóng", "kwh": 510_268, "sau": 0.1140,
                "ty_le_nhom": 0.1480, "nhom": None},
    "clip":    {"ten": "Inverter cắt ngọn giờ nắng gắt", "kwh": 79_298, "sau": 0.0028,
                "ty_le_nhom": 0.0230, "nhom": None},
    "anomaly": {"ten": "Sự cố, hỏng hóc", "kwh": 70_330, "sau": 0.0,
                "ty_le_nhom": 0.0204, "nhom": None},
    "tilt":    {"ten": "Mái phẳng, đọng bùn mép dưới", "kwh": 71_850, "sau": 0.0,
                "ty_le_nhom": 0.0390, "nhom": "cụm 970 kWp mái bằng"},
    "shade":   {"ten": "Bóng che và inverter quá nóng", "kwh": 57_074, "sau": 0.0,
                "ty_le_nhom": 0.0165, "nhom": None},
    "soiling": {"ten": "Bụi bám mùa khô", "kwh": 62_060, "sau": 0.0,
                "ty_le_nhom": 0.0180, "nhom": None},
}
for _v in TON_THAT_CO_SO.values():
    _v["ty_le"] = _v["kwh"] / CO_SO["e_baseline_kwh"]

# ═════════════════════════════════════════════════════════════════════════════
#  7 HANG MUC CHECKBOX — brief muc 3, bang tong hop
# ═════════════════════════════════════════════════════════════════════════════
HANG_MUC_CAI_TIEN = {
    "bess": {
        "stt": 1, "ten": "Lắp pin lưu trữ cho 5 khu (BESS 1MW/2,5MWh)",
        "hieu_suat": "+20,6%", "kwh": 712_182, "aud": 323_164,
        "capex_aud": 1_250_000, "payback": "3,87 năm", "ton_that": "clip",
    },
    "ventilation": {
        "stt": 2, "ten": "Khe hở thông gió mái 10–15 cm",
        "hieu_suat": "+3,40%", "kwh": 117_224, "aud": 23_445,
        "capex_aud": 24_280, "payback": "1,04 năm", "ton_that": "temp",
    },
    "cbm": {
        "stt": 3, "ten": "Máy tự báo hỏng để sửa sớm (CBM + AI)",
        "hieu_suat": "+2,04%", "kwh": 70_330, "aud": 29_066,
        "capex_aud": 8_000, "payback": "Dưới 4 tháng", "ton_that": "anomaly",
    },
    "tilt": {
        "stt": 4, "ten": "Kê khung nghiêng 15° cho mái bằng",
        "hieu_suat": "+3,90%", "kwh": 71_850, "aud": 14_670,
        "capex_aud": 18_000, "payback": "1,23 năm", "ton_that": "tilt",
    },
    "inverter": {
        "stt": 5, "ten": "Che nắng bộ inverter, gắn bộ tối ưu DC",
        "hieu_suat": "+1,65%", "kwh": 57_074, "aud": 11_415,
        "capex_aud": 12_500, "payback": "1,10 năm", "ton_that": "shade",
    },
    "washing": {
        "stt": 6, "ten": "Lịch rửa pin thông minh theo mưa",
        "hieu_suat": "+1,80%", "kwh": 62_060, "aud": 18_412,
        "capex_aud": 0, "payback": "Ngay lập tức", "ton_that": "soiling",
    },
    "topcon": {
        "stt": 7, "ten": "Thay tấm pin đời mới TOPCon",
        "hieu_suat": "+6,20%", "kwh": 213_761, "aud": 42_752,
        "capex_aud": None, "payback": "Khi thay tấm pin (15–20 năm)", "ton_that": None,
    },
}

# ═════════════════════════════════════════════════════════════════════════════
#  HANG MUC 4 — CAN BANG NANG LUONG 12 THANG KHI NANG GOC NGHIENG 15 DO
#
#  Nguon: bao cao dinh luong 2026-08-25 (ban da kiem toan) muc 6.1 — nhom mai
#  bang 970 kWp, san luong co so 1.377.400 kWh/nam. Co so vat ly la mo hinh
#  Sandia (King et al., SAND2004-3535, tai lieu tham khao [4]).
#
#  Day la so DU BAO cho phuong an chua thi cong, khong phai so do duoc: hang muc
#  chua lam thi khong co du lieu de do. Phan doi chieu duoc voi du lieu 42 tram
#  la HINH DANG MUA cua san luong (xem phan_ra.tilt_theo_mua).
#
#  Cot: thang, mua, goc cao mat troi luc trua (do), san luong co so (kWh/thang),
#       ty le thay doi (%), san luong thay doi (kWh/thang), gia tri (AUD)
# ═════════════════════════════════════════════════════════════════════════════
TILT_12_THANG = [
    (1,  "Mùa hè",   75.5, 172_801,  -1.45,  -2_508,   -502),
    (2,  "Mùa hè",   68.0, 147_757,  -1.16,  -1_715,   -343),
    (3,  "Mùa thu",  56.5, 127_723,   1.74,   2_224,    445),
    (4,  "Mùa thu",  44.5,  93_914,   8.22,   7_723,  1_545),
    (5,  "Mùa đông", 34.0,  67_618,  15.96,  10_795,  2_159),
    (6,  "Mùa đông", 29.0,  55_096,  20.80,  11_461,  2_292),
    (7,  "Mùa đông", 31.5,  60_105,  19.16,  11_514,  2_303),
    (8,  "Mùa đông", 39.5,  77_635,  13.74,  10_666,  2_133),
    (9,  "Mùa xuân", 51.0, 101_427,   6.29,   6_379,  1_276),
    (10, "Mùa xuân", 63.5, 130_227,   1.16,   1_512,    302),
    (11, "Mùa hè",   72.5, 157_775,  -1.16,  -1_832,   -366),
    (12, "Mùa hè",   76.5, 185_323,  -1.55,  -2_869,   -574),
]

# Loi ich rieng cua co che tu rua troi bun dong vien day (bao cao muc 6.2):
# goc >= 10-15 do thi mua >= 10 mm cuon troi 95-98% bui, triet tieu dai bun lam
# kich hoat bypass diode. Cong vao 53.350 kWh cua bang tren de ra 71.850 kWh.
TILT_TU_RUA_TROI_KWH = 18_500

# ═════════════════════════════════════════════════════════════════════════════
#  SO LIEU NEN TANG
#  Nguon: 2026_08_25_Bao_Cao_Dinh_Luong_Chi_Tiet_..._Audited.md muc 2.1 va 3.1
# ═════════════════════════════════════════════════════════════════════════════

CONG_SUAT_DC_KWP = 2428              # tong P_STC 42 tram, 5 khuon vien
NANG_SUAT_RIENG = 1420               # kWh/kWp/nam
E_ACTUAL_NAM = 3_447_760             # = 1420 x 2428, dung lam MAU SO moi ty le
SO_DONG_CO_FLAG = 6891               
# Ton that cat ngon — bao cao audited muc 3.1
E_CLIP_NAM = 79_298                  # kWh/nam
TY_LE_CLIP = 0.0230                  # = 79.298 / 3.447.760

# Ket qua tung hang muc — brief muc 3, bang tong hop.
KET_QUA_HANG_MUC = {
    "bess":        {"delta_kwh": 712_182, "delta_revenue_aud": 323_164, "ty_le": 0.206},
    "ventilation": {"delta_kwh": 117_224, "delta_revenue_aud": 23_445,  "ty_le": 0.0340},
    "cbm":         {"delta_kwh": 70_330,  "delta_revenue_aud": 29_066,  "ty_le": 0.0204},
}


# ═════════════════════════════════════════════════════════════════════════════
#  DONG GOP CUA TUNG HANG MUC VAO PERFORMANCE RATIO (diem phan tram)
#
#  PR do bang E / E_STC, nen moi kWh phat THEM se cong vao PR mot luong
#  dE / E_STC, voi E_STC = E_baseline / PR_baseline = 4.572.626 kWh/nam.
#
#  KHONG duoc nhan PR voi ty le san luong (PR x E1/E0): lam vay thi bat ca 7
#  hang muc se ra PR = 103,93%, tuc hieu suat vuot 100% — vo ly ve vat ly.
#  Ly do: 712.182 kWh cua hang muc 1 la tong dien BESS XA RA (nap ban ngay,
#  xa gio cao diem), khong phai dien phat them; chi 69.782 kWh thu hoi tu cat
#  ngon moi that su la san luong moi.
#
#  Doi chieu file kiem toan 00 muc 4: bat 6 hang muc -> PR 83,95%;
#  bat ca 7 -> PR 88,62%. Bon gia tri duoi day co san trong tai lieu
#  (brief muc 3): thong gio 2,56 | CBM 1,54 | goc nghieng 1,57 | TOPCon 4,67.
#  Hai gia tri con lai suy tu dE/E_STC. Hang muc 5 bang 0 — day la cach duy
#  nhat tai lap dung ca hai con so 83,95% va 88,62% cua tai lieu.
# ═════════════════════════════════════════════════════════════════════════════
E_STC_KWH = 4_572_626.0          # = CO_SO["e_baseline_kwh"] / CO_SO["pr_baseline"]

PR_DIEM_HANG_MUC = {
    "bess":        1.526,   # 69.782 / E_STC — chi phan thu hoi cat ngon
    "ventilation": 2.56,    # tai lieu
    "cbm":         1.54,    # tai lieu
    "tilt":        1.57,    # tai lieu
    "inverter":    0.0,     # tai lieu khong neu; xem ghi chu tren
    "washing":     1.357,   # 62.060 / E_STC
    "topcon":      4.67,    # tai lieu
}


# ═════════════════════════════════════════════════════════════════════════════
#  DON GIA DIEN QUY DOI kWh -> AUD
# ═════════════════════════════════════════════════════════════════════════════
# "Don gia dien quy doi binh quan gia quyen" — bao cao audited muc 2.2.
DON_GIA_DIEN = 0.20

# Phan doanh thu KHONG den tu dien (tiet kiem nhan cong, chi phi tranh duoc...):
#   phan_khac = AUD_cong_bo - kWh x DON_GIA_DIEN
# Giu nguyen khi doi nam, vi no khong phu thuoc bieu gia dien.
def tach_doanh_thu(ma: str) -> tuple[float, float]:
    """Tra ve (phan_dien, phan_khac)."""
    v = HANG_MUC_CAI_TIEN[ma]
    phan_dien = v["kwh"] * DON_GIA_DIEN
    return phan_dien, v["aud"] - phan_dien


def doanh_thu_theo_nam(ma: str, nam: int | None) -> float:
    """AUD cua hang muc khi ap gia dien binh quan gia quyen cua nam da chon.

    nam = None -> dung DON_GIA_DIEN (0,20), tuong ung bang tong hop brief muc 3.
    """
    _, phan_khac = tach_doanh_thu(ma)
    g = BIEU_GIA_NEM[nam]["weighted"] if nam in BIEU_GIA_NEM else DON_GIA_DIEN
    return HANG_MUC_CAI_TIEN[ma]["kwh"] * g + phan_khac


# ═════════════════════════════════════════════════════════════════════════════
#  DIEN GIAI TUNG HANG MUC — brief muc 3
# ═════════════════════════════════════════════════════════════════════════════
CHI_TIET_HANG_MUC = {
    "bess": {
        "tieu_de": "Hệ thống Pin Lưu trữ BESS Phân tán 5 Campus (1 MW / 2,5 MWh)",
        "co_che": "Thu hồi 88% năng lượng cắt ngọn biến tần (Inverter Clipping ILR = 1,25) "
                  "qua cấu trúc BESS DC-Coupled, kết hợp chênh lệch giá giờ cao điểm "
                  "(TOU Peak Arbitrage 17:00–21:00) và gọt đỉnh phụ tải (800 kW Demand Charge).",
        "tac_dong": "ΔE = +69.782 kWh (thu hồi cắt ngọn) · Loss_clip giảm 2,30% → 0,28% · "
                    "CapEx 1.250.000 AUD · hoàn vốn 3,87 năm.",
        "cong_thuc": [
            "P_AC_max = p_stc / 1,25",
            "Δe_clip(t) = max(0, e_stc_hourly × pr_adjusted − 0,80 × p_stc)",
            "Δe_thu_hồi(t) = Δe_clip(t) × 0,88",
            "ΔRevenue = Δe × (P_Peak − P_FIT) nếu 17≤h≤21, ngược lại × P_FIT",
        ],
        "cong_thuc_tex": [
            r"P_{AC,\max} \;=\; \frac{p_{stc}}{ILR} \;=\; \frac{p_{stc}}{1{,}25}",
            r"\Delta e_{clip}(t) \;=\; \max\!\Bigl(0,\; e_{stc}(t)\cdot PR_{adj}(t) \;-\; 0{,}80\,p_{stc}\Bigr)",
            r"\Delta e_{\text{thu hồi}}(t) \;=\; \eta_{RTE}\cdot\Delta e_{clip}(t),\qquad \eta_{RTE}=0{,}88",
            r"\Delta R \;=\; \Delta e_{\text{thu hồi}}\cdot\begin{cases}P_{peak}-P_{FIT} & 17\le h\le 21\\[2pt] P_{FIT} & \text{giờ còn lại}\end{cases}",
        ],
    },
    "ventilation": {
        "tieu_de": "Khoảng hở Thông gió Mái 10–15 cm (chuẩn AS/NZS 5033)",
        "co_che": "Lắp giàn khung nhôm nâng cao 150 mm tạo dòng đối lưu không khí tự nhiên "
                  "mặt sau tấm pin, hạ nhiệt độ cell trung bình −8,0°C "
                  "(mùa hè −11°C, mùa đông −4°C).",
        "tac_dong": "ΔE = +117.224 kWh · Loss_temp giảm 14,80% → 11,40% · PR tăng +2,56% · "
                    "CapEx 24.280 AUD · hoàn vốn 1,04 năm (12,4 tháng).",
        "cong_thuc": [
            "T_flush = temperature_c + shortwave × exp(−2,98 − 0,0471 × wind) + shortwave/1000 × 3,0",
            "T_open  = temperature_c + shortwave × exp(−3,56 − 0,0750 × wind) + shortwave/1000 × 3,0",
            "Δloss_temp = 0,0038 × max(0, T_flush − T_open)",
            "Δe = e_hourly × Δloss_temp / (1 − loss_temp)",
        ],
        "cong_thuc_tex": [
            r"T_{cell} \;=\; T_{air} \;+\; G\cdot e^{\,a\,+\,b\,v} \;+\; \frac{G}{1000}\,\Delta T,\qquad \Delta T = 3{,}0\;^\circ C",
            r"(a,b)_{\text{mái sát}} = (-2{,}98;\,-0{,}0471) \qquad(a,b)_{\text{có khe hở}} = (-3{,}56;\,-0{,}0750)",
            r"\Delta L_{temp} \;=\; \gamma\cdot\max\!\bigl(0,\; T_{\text{mái sát}}-T_{\text{có khe hở}}\bigr),\qquad \gamma = 0{,}0038\;^\circ C^{-1}",
            r"\Delta e \;=\; e_{hourly}\cdot\frac{\Delta L_{temp}}{1-L_{temp}}",
        ],
    },
    "cbm": {
        "tieu_de": "Chuyển đổi Bảo trì CBM & AI Anomaly (GMM-IF)",
        "co_che": "Rút ngắn MTTD từ 14–30 ngày xuống dưới 1 giờ và MTTR từ 7–14 ngày xuống "
                  "1–3 ngày làm việc, với 6 mã lỗi vật lý: ngắt quá áp trưa, đứt cầu chì chuỗi, "
                  "dồn gói Modbus, trôi điểm 0 CT, che bóng cục bộ.",
        "tac_dong": "ΔE = +70.330 kWh · Loss_anomaly giảm 2,04% → 0,0% · PR tăng +1,54% · "
                    "CapEx 8.000 AUD/năm (phí AI cloud & drone scan) · hoàn vốn dưới 4 tháng.",
        "cong_thuc": [
            "Δe(t) = max(0, e_expected − e_hourly) khi gmm_if_outlier_flag = TRUE",
            "Δe(t) = 0 khi FALSE",
        ],
        "cong_thuc_tex": [
            r"\Delta e(t) \;=\; \begin{cases}\max\bigl(0,\; e_{\text{kỳ vọng}}(t)-e_{hourly}(t)\bigr) & \text{dòng bị gắn cờ dị thường}\\[2pt]0 & \text{dòng bình thường}\end{cases}",
            r"\Delta E_{\text{khắc phục}} \;=\; f\cdot\sum_{t}\Delta e(t),\qquad f = 0{,}857\ \ (\text{rút thời gian sửa }14\to 2\text{ ngày})",
        ],
    },
    "tilt": {
        "tieu_de": "Nâng Khung Nghiêng chữ A 15° Hướng Bắc cho 970 kWp Mái Bằng",
        "co_che": "Tối ưu hoá quang học theo quỹ đạo mặt trời mùa đông Victoria (37°S): "
                  "mùa đông +44.436 kWh, mùa hè −8.924 kWh, tăng ròng +53.350 kWh/năm. "
                  "Góc dốc tự thoát nước mưa cuốn dải bùn đọng viền nhôm đáy, thu hồi thêm "
                  "+18.500 kWh và tiết kiệm 4.000 AUD nhân công rửa pin.",
        "tac_dong": "ΔE = +71.850 kWh · PR trạm mái bằng +3,90% · PR toàn hệ thống +1,57% · "
                    "CapEx 18.000 AUD · hoàn vốn 1,23 năm.",
        "cong_thuc": [],
        "cong_thuc_tex": [
            r"\Delta E \;=\; \Delta E_{\text{góc nghiêng}} \;+\; \Delta E_{\text{thoát bùn}}\;=\; 53{.}350 \;+\; 18{.}500 \;=\; 71{.}850\ \text{kWh/năm}",
            r"\Delta E_{\text{góc nghiêng}} \;=\; \underbrace{+44{.}436}_{\text{mùa đông}}\;+\;\underbrace{-8{.}924}_{\text{mùa hè}}",
        ],
    },
    "inverter": {
        "tieu_de": "Mái Che Nắng Biến Tần & Bộ Tối Ưu Hoá Công Suất DC Optimizers",
        "co_che": "Tấm che nắng hạ nhiệt bộ tản nhiệt biến tần xuống dưới 72°C, triệt tiêu lỗi "
                  "giảm tải derating (+18.450 kWh/năm) và bảo vệ 2 inverter khỏi hỏng sớm "
                  "(16.000 AUD). DC Optimizers cho 6 trạm che bóng (320 kWp) thu hồi "
                  "+38.624 kWh/năm.",
        "tac_dong": "ΔE = +57.074 kWh · Loss_shade_inv giảm 1,65% → 0,0% · "
                    "CapEx 12.500 AUD · hoàn vốn 1,10 năm.",
        "cong_thuc": [],
        "cong_thuc_tex": [
            r"\Delta E \;=\; \Delta E_{\text{hết giảm tải}} \;+\; \Delta E_{\text{tối ưu DC}}\;=\; 18{.}450 \;+\; 38{.}624 \;=\; 57{.}074\ \text{kWh/năm}",
            r"\text{Điều kiện giảm tải: } T_{\text{tản nhiệt}} > 72\;^\circ C",
        ],
    },
    "washing": {
        "tieu_de": "Lịch Rửa Pin Thông minh Dựa trên Lượng Mưa",
        "co_che": "Theo dõi cảm biến thời tiết, chỉ rửa thủ công khi chuỗi ngày khô hạn liên tục "
                  "≥ 21 ngày và lượng mưa tích luỹ < 2 mm. Thu hồi 62.060 kWh tổn thất bám bụi "
                  "mùa khô và cắt 3 lần rửa thừa mỗi năm, tiết kiệm 6.000 AUD nhân công.",
        "tac_dong": "ΔE = +62.060 kWh · Loss_soiling giảm 1,80% → 0,0% · "
                    "CapEx 0 AUD (tối ưu quy trình) · hoàn vốn tức thì.",
        "cong_thuc": [],
        "cong_thuc_tex": [
            r"\text{Rửa khi: } n_{\text{ngày khô liên tục}} \ge 21\;\;\wedge\;\; \textstyle\sum P_{\text{mưa}} < 2\ \text{mm}",
            r"\Delta E \;=\; \sum_{t} e_{\text{bụi bám}}(t) \;=\; 62{.}060\ \text{kWh/năm}",
        ],
    },
    "topcon": {
        "tieu_de": "Nâng Cấp Công nghệ Tấm Pin TOPCon / HJT (Kỳ Đại tu Repowering)",
        "co_che": "Thay P-type PERC bằng N-type TOPCon, hiệu suất tăng 18,5% → 22,5%, hệ số nhiệt "
                  "cải thiện −0,38%/°C → −0,30%/°C, triệt tiêu suy thoái quang học Zero LID, "
                  "tỷ lệ lão hoá giảm 0,55% → 0,40%/năm.",
        "tac_dong": "ΔE = +213.761 kWh · PR tăng +4,67% · tiền đầu tư gộp vào đợt thay tấm pin "
                    "định kỳ vòng đời 15–20 năm.",
        "cong_thuc": [],
        "cong_thuc_tex": [
            r"P \;=\; P_{STC}\bigl[\,1 + \gamma\,(T_{cell}-25)\,\bigr]",
            r"\Delta\gamma \;=\; |{-0{,}38}| - |{-0{,}30}| \;=\; 0{,}08\ \%/^\circ C",
            r"\Delta e(t) \;=\; \Delta\gamma\cdot\max\bigl(0,\;T_{cell}(t)-25\bigr)\cdot e_{hourly}(t)",
        ],
    },
}


# ═════════════════════════════════════════════════════════════════════════════
#  DON VI TIEN VA TY GIA QUY DOI
# ═════════════════════════════════════════════════════════════════════════════
# Moi con so goc trong tai lieu tinh bang AUD. Cac don vi khac quy doi tu AUD.
# Ty gia dat o day de doi mot cho la doi toan trang.
TIEN_TE = {
    "AUD": {"ten": "Đô la Úc", "ky_hieu": "AUD", "ty_gia": 1.0, "so_le": 0},
    "USD": {"ten": "Đô la Mỹ", "ky_hieu": "USD", "ty_gia": 0.65, "so_le": 0},
    "VND": {"ten": "Việt Nam đồng", "ky_hieu": "₫", "ty_gia": 16_500.0, "so_le": 0},
}
TIEN_MAC_DINH = "AUD"


def quy_doi(aud: float, ma_tien: str = TIEN_MAC_DINH) -> float:
    """Quy doi mot gia tri AUD sang don vi tien duoc chon."""
    return aud * TIEN_TE.get(ma_tien, TIEN_TE[TIEN_MAC_DINH])["ty_gia"]


def dinh_dang_tien(aud: float, ma_tien: str = TIEN_MAC_DINH) -> str:
    """Ky hieu dat SAU con so theo thong le Viet Nam: '462.924 AUD', '7.638.246.000 ₫'."""
    t = TIEN_TE.get(ma_tien, TIEN_TE[TIEN_MAC_DINH])
    return f"{quy_doi(aud, ma_tien):,.{t['so_le']}f} {t['ky_hieu']}"


# ── Anh xa tram -> khuon vien ─────────────────────────────────────────────────
# 42 tram thuoc 5 khuon vien. Lay tu datawarehouse (cot campus_name), khong phai
# suy tu cong suat: materialized view cua bi_mart khong mang cot nay.
# Bang anh xa site_id -> khuon vien DA GO BO ngay 27/08/2026: no chia 27/8/5/1/1
# tram, mau thuan voi CAMPUS o tren (26/8/4/2/2) va voi bang kiem toan file 01
# muc 4. Phan bo theo khuon vien nay lay ty trong CONG SUAT LAP tu CAMPUS
# (xem phan_ra.ho_so_campus).
