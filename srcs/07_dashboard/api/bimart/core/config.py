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
    "temp":    {"ten": "Nhiệt độ cell", "kwh": 510_268, "sau": 0.1140,
                "ty_le_nhom": 0.1480, "nhom": None},
    "clip":    {"ten": "Cắt ngọn inverter", "kwh": 79_298, "sau": 0.0028,
                "ty_le_nhom": 0.0230, "nhom": None},
    "anomaly": {"ten": "Dị thường vận hành", "kwh": 70_330, "sau": 0.0,
                "ty_le_nhom": 0.0204, "nhom": None},
    "tilt":    {"ten": "Góc nghiêng + bùn đáy", "kwh": 71_850, "sau": 0.0,
                "ty_le_nhom": 0.0390, "nhom": "cụm 970 kWp mái bằng"},
    "shade":   {"ten": "Che bóng + quá nhiệt inverter", "kwh": 57_074, "sau": 0.0,
                "ty_le_nhom": 0.0165, "nhom": None},
    "soiling": {"ten": "Bụi bẩn mùa khô", "kwh": 62_060, "sau": 0.0,
                "ty_le_nhom": 0.0180, "nhom": None},
}
for _v in TON_THAT_CO_SO.values():
    _v["ty_le"] = _v["kwh"] / CO_SO["e_baseline_kwh"]

# ═════════════════════════════════════════════════════════════════════════════
#  7 HANG MUC CHECKBOX — brief muc 3, bang tong hop
# ═════════════════════════════════════════════════════════════════════════════
HANG_MUC_CAI_TIEN = {
    "bess": {
        "stt": 1, "ten": "Hệ thống BESS 5 Campus (1MW/2.5MWh)",
        "hieu_suat": "+20,6% hiệu ích", "kwh": 712_182, "aud": 323_164,
        "capex_aud": 1_250_000, "payback": "3,87 năm", "ton_that": "clip",
    },
    "ventilation": {
        "stt": 2, "ten": "Khe hở thông gió mái 10–15 cm",
        "hieu_suat": "+3,40% toàn trạm", "kwh": 117_224, "aud": 23_445,
        "capex_aud": 24_280, "payback": "1,04 năm", "ton_that": "temp",
    },
    "cbm": {
        "stt": 3, "ten": "Bảo trì CBM & AI Anomaly (GMM-IF)",
        "hieu_suat": "+2,04% toàn trạm", "kwh": 70_330, "aud": 29_066,
        "capex_aud": 8_000, "payback": "< 4 tháng", "ton_that": "anomaly",
    },
    "tilt": {
        "stt": 4, "ten": "Nâng khung nghiêng chữ A 15° mái bằng",
        "hieu_suat": "+3,90% nhóm 970 kWp", "kwh": 71_850, "aud": 14_670,
        "capex_aud": 18_000, "payback": "1,23 năm", "ton_that": "tilt",
    },
    "inverter": {
        "stt": 5, "ten": "Mái che Inverter & DC Optimizers",
        "hieu_suat": "+1,65% toàn trạm", "kwh": 57_074, "aud": 11_415,
        "capex_aud": 12_500, "payback": "1,10 năm", "ton_that": "shade",
    },
    "washing": {
        "stt": 6, "ten": "Lịch rửa pin thông minh theo mưa",
        "hieu_suat": "+1,80% mùa khô", "kwh": 62_060, "aud": 18_412,
        "capex_aud": 0, "payback": "Tức thì", "ton_that": "soiling",
    },
    "topcon": {
        "stt": 7, "ten": "Nâng cấp TOPCon (kỳ Repowering)",
        "hieu_suat": "+6,20% toàn trạm", "kwh": 213_761, "aud": 42_752,
        "capex_aud": None, "payback": "Kỳ đại tu", "ton_that": None,
    },
}

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
    },
    "washing": {
        "tieu_de": "Lịch Rửa Pin Thông minh Dựa trên Lượng Mưa",
        "co_che": "Theo dõi cảm biến thời tiết, chỉ rửa thủ công khi chuỗi ngày khô hạn liên tục "
                  "≥ 21 ngày và lượng mưa tích luỹ < 2 mm. Thu hồi 62.060 kWh tổn thất bám bụi "
                  "mùa khô và cắt 3 lần rửa thừa mỗi năm, tiết kiệm 6.000 AUD nhân công.",
        "tac_dong": "ΔE = +62.060 kWh · Loss_soiling giảm 1,80% → 0,0% · "
                    "CapEx 0 AUD (tối ưu quy trình) · hoàn vốn tức thì.",
        "cong_thuc": [],
    },
    "topcon": {
        "tieu_de": "Nâng Cấp Công nghệ Tấm Pin TOPCon / HJT (Kỳ Đại tu Repowering)",
        "co_che": "Thay P-type PERC bằng N-type TOPCon, hiệu suất tăng 18,5% → 22,5%, hệ số nhiệt "
                  "cải thiện −0,38%/°C → −0,30%/°C, triệt tiêu suy thoái quang học Zero LID, "
                  "tỷ lệ lão hoá giảm 0,55% → 0,40%/năm.",
        "tac_dong": "ΔE = +213.761 kWh · PR tăng +4,67% · CapEx tích hợp vào ngân sách đại tu "
                    "định kỳ vòng đời 15–20 năm.",
        "cong_thuc": [],
    },
}


# ═════════════════════════════════════════════════════════════════════════════
#  DON VI TIEN VA TY GIA QUY DOI
# ═════════════════════════════════════════════════════════════════════════════
# Moi con so goc trong tai lieu tinh bang AUD. Cac don vi khac quy doi tu AUD.
# Ty gia dat o day de doi mot cho la doi toan trang.
TIEN_TE = {
    "AUD": {"ten": "Đô la Úc", "ky_hieu": "A$", "ty_gia": 1.0, "so_le": 0},
    "USD": {"ten": "Đô la Mỹ", "ky_hieu": "US$", "ty_gia": 0.65, "so_le": 0},
    "VND": {"ten": "Việt Nam đồng", "ky_hieu": "₫", "ty_gia": 16_500.0, "so_le": 0},
}
TIEN_MAC_DINH = "AUD"


def quy_doi(aud: float, ma_tien: str = TIEN_MAC_DINH) -> float:
    """Quy doi mot gia tri AUD sang don vi tien duoc chon."""
    return aud * TIEN_TE.get(ma_tien, TIEN_TE[TIEN_MAC_DINH])["ty_gia"]


def dinh_dang_tien(aud: float, ma_tien: str = TIEN_MAC_DINH) -> str:
    """Chuoi hien thi kem ky hieu, vi du 'A$ 462.924' hoac '₫ 7.638.246.000'."""
    t = TIEN_TE.get(ma_tien, TIEN_TE[TIEN_MAC_DINH])
    return f"{t['ky_hieu']} {quy_doi(aud, ma_tien):,.{t['so_le']}f}"
