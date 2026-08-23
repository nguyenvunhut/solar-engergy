"""
Script render sơ đồ kiến trúc Tầng BI Data Mart & Nguyên tắc Thiết kế UI/UX Gestalt (Slide 14)
cho dự án tốt nghiệp 'The Outliers' bằng Matplotlib & PIL với độ phân giải cao (300 DPI).
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Thiết lập font và style đồ họa
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["figure.dpi"] = 300

fig, ax = plt.subplots(figsize=(24, 14.5), facecolor="#F8FAFC")
ax.set_facecolor("#F8FAFC")
ax.set_xlim(0, 2400)
ax.set_ylim(0, 1450)
ax.axis("off")

def draw_rounded_rect(ax, x, y, w, h, bg_color, border_color, border_width=1.5, radius=12, alpha=1.0, zorder=2):
    fancy = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=bg_color,
        edgecolor=border_color,
        linewidth=border_width,
        alpha=alpha,
        zorder=zorder
    )
    ax.add_patch(fancy)
    return fancy

def draw_arrow(ax, x1, y1, x2, y2, color="#475569", width=2.2, zorder=5):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=width,
            mutation_scale=18,
            shrinkA=2,
            shrinkB=2
        ),
        zorder=zorder
    )

# 1. HEADER BANNER
draw_rounded_rect(ax, 40, 1320, 2320, 100, bg_color="#0F172A", border_color="#1E293B", border_width=2, radius=14)

ax.text(70, 1385, "KIẾN TRÚC TẦNG BI DATA MART & NGUYÊN TẮC THIẾT KẾ UI/UX GESTALT", 
        fontsize=18.5, fontweight="bold", color="#FFFFFF", va="center")
ax.text(70, 1348, "Chuyển đổi tối ưu DWH sang Materialized Views | Bảng màu ngữ nghĩa WCAG 2.1 AA | Tối ưu hóa Tableau Dashboards (< 100 ms)", 
        fontsize=12, color="#94A3B8", va="center")

# Top Right Badge
draw_rounded_rect(ax, 2010, 1345, 320, 48, bg_color="#1E293B", border_color="#38BDF8", border_width=1.5, radius=8)
ax.text(2170, 1369, "PHẦN 3: SLIDE 14 — THE OUTLIERS", fontsize=11.5, fontweight="bold", color="#38BDF8", ha="center", va="center")

# ==================== 3 CỘT CHÍNH ====================
top_y = 50
col_h = 1240

# --- CỘT 1: DWH TRANSFORMATION & TABLEAU INTEGRATION ---
c1_x = 40
c1_w = 720
draw_rounded_rect(ax, c1_x, top_y, c1_w, col_h, bg_color="#F1F5F9", border_color="#64748B", border_width=2, radius=14)
# Header Cột 1
draw_rounded_rect(ax, c1_x, top_y + col_h - 60, c1_w, 60, bg_color="#334155", border_color="#64748B", border_width=1, radius=12)
ax.text(c1_x + c1_w/2, top_y + col_h - 22, "1. CHUYỂN ĐỔI DWH & TỐI ƯU TRUY VẤN", fontsize=13.5, fontweight="bold", color="#FFFFFF", ha="center", va="center")
ax.text(c1_x + c1_w/2, top_y + col_h - 44, "So sánh kiến trúc & Kết nối khai thác trực tiếp từ Tableau", fontsize=10, color="#CBD5E1", ha="center", va="center")

# Box 1.1: So sánh giải pháp (DWH Transformation)
draw_rounded_rect(ax, c1_x + 20, 830, c1_w - 40, 325, bg_color="#FFFFFF", border_color="#CBD5E1", border_width=1.5, radius=10)
ax.text(c1_x + 35, 1125, "Chiến Lược Lựa Chọn Kiến Trúc Tầng BI", fontsize=12, fontweight="bold", color="#0F172A")

# 3 Phương án So sánh
# PA 1: Standard View (Loại bỏ)
draw_rounded_rect(ax, c1_x + 35, 1025, c1_w - 70, 75, bg_color="#FEF2F2", border_color="#EF4444", border_width=1.2, radius=8)
draw_rounded_rect(ax, c1_x + 48, 1066, 24, 22, bg_color="#EF4444", border_color="none", radius=4)
ax.text(c1_x + 60, 1077, "X", fontsize=10, fontweight="bold", color="#FFFFFF", ha="center", va="center")
ax.text(c1_x + 80, 1077, "Standard View (View Thường) — [Loại Bỏ]", fontsize=10.5, fontweight="bold", color="#B91C1C", va="center")
txt_pa1 = "• Tải lại toàn bộ truy vấn JOIN trên 3.5M dòng mỗi lần tương tác lọc\n• Độ trễ rất cao (5 – 10 giây/thao tác) | Nguy cơ nghẽn CPU/RAM Supabase"
ax.text(c1_x + 50, 1045, txt_pa1, fontsize=9.5, color="#7F1D1D", va="center", linespacing=1.3)

# PA 2: Physical Tables (Loại bỏ)
draw_rounded_rect(ax, c1_x + 35, 935, c1_w - 70, 75, bg_color="#FFFBEB", border_color="#F59E0B", border_width=1.2, radius=8)
draw_rounded_rect(ax, c1_x + 48, 976, 24, 22, bg_color="#F59E0B", border_color="none", radius=4)
ax.text(c1_x + 60, 987, "!", fontsize=11, fontweight="bold", color="#FFFFFF", ha="center", va="center")
ax.text(c1_x + 80, 987, "Bảng Vật Lý Riêng (Separate Physical Table) — [Loại Bỏ]", fontsize=10.5, fontweight="bold", color="#B45309", va="center")
txt_pa2 = "• Dễ phát sinh sai lệch đồng bộ (Desynchronization) khi DWH cập nhật\n• Nhân đôi dung lượng lưu trữ | Quy trình ETL phức tạp, dễ gãy vỡ"
ax.text(c1_x + 50, 955, txt_pa2, fontsize=9.5, color="#78350F", va="center", linespacing=1.3)

# PA 3: Materialized Views (Lựa chọn)
draw_rounded_rect(ax, c1_x + 35, 845, c1_w - 70, 75, bg_color="#ECFDF5", border_color="#10B981", border_width=1.5, radius=8)
draw_rounded_rect(ax, c1_x + 48, 886, 24, 22, bg_color="#10B981", border_color="none", radius=4)
ax.text(c1_x + 60, 897, "V", fontsize=10, fontweight="bold", color="#FFFFFF", ha="center", va="center")
ax.text(c1_x + 80, 897, "PostgreSQL Materialized Views — [Giải Pháp Cốt Lõi]", fontsize=10.5, fontweight="bold", color="#047857", va="center")
txt_pa3 = "• Lưu cache kết quả tiền tổng hợp (Pre-aggregated) vào đĩa vật lý\n• Tích hợp sẵn Unique Composite Index | Phản hồi Tableau < 100 ms"
ax.text(c1_x + 50, 865, txt_pa3, fontsize=9.5, color="#064E3B", va="center", linespacing=1.3)

# Box 1.2: DWH Input Data (Nguồn Dữ liệu DWH)
draw_rounded_rect(ax, c1_x + 20, 500, c1_w - 40, 310, bg_color="#FFFFFF", border_color="#CBD5E1", border_width=1.5, radius=10)
ax.text(c1_x + 35, 785, "Dữ Liệu Đầu Vào Từ Schema datawarehouse (3.5M Dòng)", fontsize=12, fontweight="bold", color="#1E3A8A")

txt_dwh = (
    "• fact_solar_energy_gen (2.731.946 dòng):\n"
    "  - Chu kỳ 15 phút, khóa chính: gen_id\n"
    "  - FK: site_id, geo_id, date_id, time_id\n"
    "  - energy_generated_kwh, gmm_if_outlier_flag\n\n"
    "• fact_weather (850.752 dòng ERA5-Land):\n"
    "  - Chu kỳ 1 giờ, khóa chính: weather_id\n"
    "  - FK: geo_id, date_id, time_id, weather_type_id\n"
    "  - shortwave_radiation, temp_c, cloud_cover, wind_speed\n\n"
    "• 5 Conformed Dimensions chung:\n"
    "  dim_solar_site, dim_geography, dim_date, dim_time, dim_weather_type"
)
ax.text(c1_x + 35, 650, txt_dwh, fontsize=10, color="#1E293B", va="center", linespacing=1.35)

# Box 1.3: Tableau Native Connection & Serving Layer
draw_rounded_rect(ax, c1_x + 20, 70, c1_w - 40, 410, bg_color="#EFF6FF", border_color="#3B82F6", border_width=1.8, radius=10)
ax.text(c1_x + 35, 455, "Tầng Khai Thác Tableau Desktop & Server", fontsize=12, fontweight="bold", color="#1D4ED8")

txt_tab = (
    "• Cổng Kết Nối: PostgreSQL Pooler IPv4\n"
    "  (aws-1-ap-southeast-1.pooler.supabase.com:5432 / SSL TLS)\n\n"
    "• Phân Quyền An Toàn (Principle of Least Privilege):\n"
    "  Tài khoản dịch vụ tableau_user (Chỉ cấp quyền SELECT trên bi_mart)\n\n"
    "• Tableau Relationships (1:N N-Grain Preservation):\n"
    "  Liên kết trực tiếp MV với Dimension tables, triệt tiêu lỗi Fan-out\n\n"
    "• Phục Vụ 3 Dashboards Chuyên Biệt:\n"
    "  1. Executive Overview (Tổng quan điều hành, BANs, Bản đồ trạm)\n"
    "  2. Efficiency & Loss Analysis (Tổn thất nhiệt, Xếp hạng thiết bị)\n"
    "  3. Anomaly Detection & O&M (Cờ GMM-IF, Dòng rò ban đêm)\n\n"
    "• Tốc độ phản hồi tương tác: < 100 ms (Zero Lag)"
)
ax.text(c1_x + 35, 265, txt_tab, fontsize=10, color="#0F172A", va="center", linespacing=1.32)


# --- CỘT 2: CẤU TRÚC 2 MATERIALIZED VIEWS LÕI (SCHEMA bi_mart) ---
c2_x = 790
c2_w = 810
draw_rounded_rect(ax, c2_x, top_y, c2_w, col_h, bg_color="#F0FDF4", border_color="#16A34A", border_width=2, radius=14)
# Header Cột 2
draw_rounded_rect(ax, c2_x, top_y + col_h - 60, c2_w, 60, bg_color="#15803D", border_color="#16A34A", border_width=1, radius=12)
ax.text(c2_x + c2_w/2, top_y + col_h - 22, "2. CẤU TRÚC TẦNG BI DATA MART (MATERIALIZED VIEWS)", fontsize=13.5, fontweight="bold", color="#FFFFFF", ha="center", va="center")
ax.text(c2_x + c2_w/2, top_y + col_h - 44, "Schema bi_mart: mv_bi_mart_hourly_measures & mv_bi_mart_daily_kpis", fontsize=10, color="#DCFCE7", ha="center", va="center")

# Sub-card 2.1: MV Hourly Measures
draw_rounded_rect(ax, c2_x + 20, 655, c2_w - 40, 500, bg_color="#FFFFFF", border_color="#22C55E", border_width=1.8, radius=10)
# Sub-header
draw_rounded_rect(ax, c2_x + 20, 1105, c2_w - 40, 50, bg_color="#DCFCE7", border_color="#22C55E", border_width=1, radius=8)
ax.text(c2_x + 35, 1130, "[1] bi_mart.mv_bi_mart_hourly_measures (Đo Lường Cấp Giờ - 1h)", fontsize=12, fontweight="bold", color="#14532D")

txt_mv1 = (
    "• Cơ Chế Nén Độ Hạt: Nén 4 mốc 15m (fact_solar_energy_gen) về cùng 1 khung giờ 1h (hourly_bucket)\n"
    "• Ghép Nối Thời Tiết Nhân Quả: Causal Join với fact_weather theo (geo_id, date_id, weather_hour)\n\n"
    "• Các Nhóm Đo Lường & Chỉ Số Kỹ Thuật Lõi:\n"
    "  - Đo lường vật lý: e_hourly (kWh), shortwave_radiation (GHI), temperature_c, wind_speed\n"
    "  - Nhiệt độ ô pin: t_cell = temperature_c + (shortwave_radiation * 0.035)\n"
    "  - Sản lượng STC danh định: e_stc_hourly = p_stc * (GHI / 1000.0) [khi GHI >= 100 W/m²]\n"
    "  - Suy hao do nhiệt độ: loss_temp = (t_cell - 25) * 0.004 [khi t_cell > 25°C]\n"
    "  - Hệ số hiệu suất thực tế & điều chỉnh: pr_actual = e_hourly / e_stc | pr_adjusted = 0.78 * (1 - loss_temp)\n"
    "  - Sản lượng kỳ vọng: e_expected = e_stc_hourly * pr_adjusted\n\n"
    "• Chỉ Số Kinh Doanh, Tài Chính & Môi Trường:\n"
    "  - estimated_revenue = e_hourly * fit_rate (Biểu giá FiT 1.938 VNĐ/kWh)\n"
    "  - cost_of_underperformance = (e_expected - e_hourly) * fit_rate (Chi phí thiếu hụt công suất)\n"
    "  - co2_avoided_kg = e_hourly * 0.533 kg | equivalent_trees_planted = co2_avoided / 21.8 kg\n\n"
    "• Cờ Dị Thường GMM-IF & Phân Loại Lỗi O&M: gmm_if_outlier_flag, gmm_if_outlier_reason\n"
    "• Chỉ Mục Duy Nhất (Unique Index): idx_mv_hourly_unique (date_id, site_id, hourly_bucket)"
)
ax.text(c2_x + 35, 878, txt_mv1, fontsize=9.8, color="#0F172A", va="center", linespacing=1.33)

# Sub-card 2.2: MV Daily KPIs
draw_rounded_rect(ax, c2_x + 20, 70, c2_w - 40, 560, bg_color="#FFFFFF", border_color="#22C55E", border_width=1.8, radius=10)
# Sub-header
draw_rounded_rect(ax, c2_x + 20, 580, c2_w - 40, 50, bg_color="#DCFCE7", border_color="#22C55E", border_width=1, radius=8)
ax.text(c2_x + 35, 605, "[2] bi_mart.mv_bi_mart_daily_kpis (Chỉ Số Cấp Ngày & Time-Intelligence)", fontsize=12, fontweight="bold", color="#14532D")

txt_mv2 = (
    "• Cơ Chế Tổng Hợp: Aggregation trực tiếp từ mv_bi_mart_hourly_measures nhóm theo (date_id, site_id)\n\n"
    "• Chỉ Số Tổng Hợp & Hiệu Suất Ngày:\n"
    "  - e_daily (Tổng sản lượng ngày), e_stc_daily, e_target_daily\n"
    "  - daily_revenue, daily_cost_underperformance, daily_co2_avoided, daily_trees_planted\n"
    "  - daily_pr_actual = e_daily / e_stc_daily (PR thực tế ngày)\n"
    "  - daily_pr_adjusted = e_target_daily / e_stc_daily (PR hiệu chỉnh nhiệt độ ngày)\n"
    "  - capacity_factor (CF) = e_daily / (p_stc * 24h) | specific_yield = e_daily / p_stc\n"
    "  - yield_fulfillment_ratio = e_daily / e_target_daily (Tỷ lệ đạt kế hoạch kỳ vọng)\n\n"
    "• Phân Tích Chuỗi Thời Gian Lũy Kế (Time-Intelligence Window Functions):\n"
    "  - wtd_energy: Lũy kế Tuần-đến-nay (Week-to-Date PARTITION BY week)\n"
    "  - mtd_energy & mtd_revenue: Lũy kế Tháng-đến-nay (Month-to-Date PARTITION BY month)\n"
    "  - ytd_energy & ytd_revenue: Lũy kế Năm-đến-nay (Year-to-Date PARTITION BY year)\n\n"
    "• Giám Sát Bất Thường Cấp Trạm: has_gmm_outlier (bool_or), daily_gmm_outlier_reasons\n"
    "• Cơ Chế Cập Nhật Dữ Liệu Định Kỳ: REFRESH MATERIALIZED VIEW CONCURRENTLY\n"
    "• Chỉ Mục Duy Nhất (Unique Index): idx_mv_daily_unique (date_id, site_id)"
)
ax.text(c2_x + 35, 325, txt_mv2, fontsize=9.8, color="#0F172A", va="center", linespacing=1.33)


# --- CỘT 3: UI/UX GESTALT & SEMANTIC COLOR PALETTE ---
c3_x = 1630
c3_w = 730
draw_rounded_rect(ax, c3_x, top_y, c3_w, col_h, bg_color="#FDF2F8", border_color="#DB2777", border_width=2, radius=14)
# Header Cột 3
draw_rounded_rect(ax, c3_x, top_y + col_h - 60, c3_w, 60, bg_color="#9D174D", border_color="#DB2777", border_width=1, radius=12)
ax.text(c3_x + c3_w/2, top_y + col_h - 22, "3. NGUYÊN TẮC THIẾT KẾ UI/UX GESTALT & BẢNG MÀU", fontsize=13.5, fontweight="bold", color="#FFFFFF", ha="center", va="center")
ax.text(c3_x + c3_w/2, top_y + col_h - 44, "Tối ưu hóa tỷ số Data-Ink & Chuẩn tương phản WCAG 2.1 AA (≥ 4.5:1)", fontsize=10, color="#FCE7F3", ha="center", va="center")

# Box 3.1: Nguyên tắc Gestalt & Data-Ink
draw_rounded_rect(ax, c3_x + 20, 680, c3_w - 40, 475, bg_color="#FFFFFF", border_color="#F472B6", border_width=1.5, radius=10)
ax.text(c3_x + 35, 1125, "Nguyên Tắc Thiết Kế Giao Diện Gestalt & Tỷ Số Data-Ink", fontsize=12, fontweight="bold", color="#831843")

txt_gestalt = (
    "1. Luật Gần Nhau (Law of Proximity):\n"
    "   - Cấu trúc Card-based Container Layout gọn gàng, có viền (#E2E8F0)\n"
    "   - Gom cụm thông tin có liên quan mật thiết vào từng thẻ độc lập:\n"
    "     [Khối BANs KPI Top Banner]  [Khối Bản đồ Campus & Xếp hạng]\n"
    "     [Khối Xu hướng Sản lượng]   [Khối Ma trận Tổn thất & Dị thường]\n\n"
    "2. Luật Đồng Nhất (Law of Similarity):\n"
    "   - Các phần tử cùng bản chất chia sẻ chung hình dáng, kích thước và màu sắc\n"
    "   - Mọi cờ dị thường đều là điểm nút tròn màu Đỏ (#E15759)\n"
    "   - Mọi đường tham chiếu chuẩn đều là nét đứt màu Xám (#79706E)\n\n"
    "3. Tối Đa Hóa Tỷ Số Data-Ink (Tufte Data-Ink Ratio):\n"
    "   - Triệt tiêu hoàn toàn rác thị giác (Chartjunk) & màu nền lòe loẹt\n"
    "   - Làm mờ/loại bỏ đường lưới phụ (minor gridlines), chỉ giữ đường gốc (Zero-line)\n"
    "   - Tập trung 100% sự chú ý thị giác vào biến thiên đường cong và điểm lỗi\n\n"
    "4. Bố Cục Quét Thị Giác F-Pattern:\n"
    "   - BANs chỉ số cốt lõi đặt tại dải trên cùng (Top Banner, font 18–24pt)\n"
    "   - Luồng quan sát tự nhiên: Tổng quan cấp cao -> Bản đồ -> Khoan sâu chi tiết"
)
ax.text(c3_x + 35, 915, txt_gestalt, fontsize=9.8, color="#0F172A", va="center", linespacing=1.32)

# Box 3.2: Bảng Màu Ngữ Nghĩa WCAG 2.1 AA
draw_rounded_rect(ax, c3_x + 20, 70, c3_w - 40, 590, bg_color="#FFFFFF", border_color="#F472B6", border_width=1.5, radius=10)
ax.text(c3_x + 35, 630, "Bảng Màu Ngữ Nghĩa Chuẩn Tương Phản WCAG 2.1 AA (≥ 4.5:1)", fontsize=12, fontweight="bold", color="#831843")

# 5 Color Items
colors_spec = [
    {
        "name": "Classic Teal / Navy (#4E79A7 & #76B7B2)",
        "role": "Sản lượng Thực tế Chuẩn & BANs Cốt lõi",
        "desc": "Đường xu hướng e_hourly, BANs tổng sản lượng, đường hiệu suất điều chỉnh nhiệt pr_adjusted (Tương phản: 7.2:1)",
        "color": "#4E79A7",
        "y": 515
    },
    {
        "name": "Solar Orange / Yellow (#F28E2B & #EDC948)",
        "role": "Bức Xạ Mặt Trời & Tổn Thất Nhiệt Độ",
        "desc": "Bức xạ sóng ngắn GHI, nhiệt độ ô pin t_cell, cảnh báo suy giảm nhẹ 50% <= PR < 75% (Tương phản: 4.8:1)",
        "color": "#F28E2B",
        "y": 410
    },
    {
        "name": "Alert Danger Red (#E15759)",
        "role": "Sự Cố Dị Thường GMM-IF & Dòng Rò Ban Đêm",
        "desc": "ĐỘC QUYỀN đánh dấu cờ bất thường GMM-IF, vết rò rỉ điện ban đêm (E > 0), sụt giảm nặng PR < 50% (Tương phản: 5.1:1)",
        "color": "#E15759",
        "y": 305
    },
    {
        "name": "Eco Success Green (#59A14F)",
        "role": "Trạng Thái Tối Ưu & Tín Chỉ Môi Trường",
        "desc": "Hệ số công suất CF, trạng thái PR >= 75%, sản lượng lũy kế WTD/MTD/YTD, CO2 tránh phát thải & Cây xanh (Tương phản: 4.9:1)",
        "color": "#59A14F",
        "y": 200
    },
    {
        "name": "Neutral Slate Gray (#79706E & #E2E8F0)",
        "role": "Đường Chuẩn Tham Chiếu & Khung Thẻ Card",
        "desc": "Trục tọa độ, Reference Lines chuẩn, khung viền Container thẻ Card, nhãn phụ trợ (Tương phản: 4.6:1)",
        "color": "#79706E",
        "y": 95
    }
]

for item in colors_spec:
    iy = item["y"]
    # Box viền màu
    draw_rounded_rect(ax, c3_x + 35, iy, c3_w - 70, 95, bg_color="#FAFAFA", border_color="#E2E8F0", border_width=1.2, radius=8)
    # Color badge
    draw_rounded_rect(ax, c3_x + 50, iy + 48, 36, 36, bg_color=item["color"], border_color="#1E293B", border_width=1, radius=6)
    ax.text(c3_x + 95, iy + 68, item["name"], fontsize=10.5, fontweight="bold", color="#0F172A")
    ax.text(c3_x + 95, iy + 48, item["role"], fontsize=9.5, fontweight="bold", color=item["color"])
    ax.text(c3_x + 50, iy + 22, item["desc"], fontsize=8.8, color="#475569", va="center")


# ==================== DATA FLOW ARROWS ====================
# Arrow DWH to Materialized Views (Cột 1 -> Cột 2)
draw_arrow(ax, c1_x + c1_w - 20, 655, c2_x + 20, 905, color="#15803D", width=2.8)
# Badge on Arrow 1
draw_rounded_rect(ax, 725, 770, 100, 26, bg_color="#DCFCE7", border_color="#16A34A", border_width=1, radius=5)
ax.text(775, 783, "Nén 15m -> 1h", fontsize=8.5, fontweight="bold", color="#14532D", ha="center", va="center")

# Arrow Materialized Views internal: Hourly to Daily
draw_arrow(ax, c2_x + c2_w/2, 655, c2_x + c2_w/2, 630, color="#15803D", width=2.6)

# Arrow Materialized Views to Tableau Serving (Cột 2 -> Cột 1 bottom)
draw_arrow(ax, c2_x + 20, 350, c1_x + c1_w - 20, 275, color="#2563EB", width=2.8)
# Badge on Arrow 2
draw_rounded_rect(ax, 720, 300, 110, 26, bg_color="#EFF6FF", border_color="#3B82F6", border_width=1, radius=5)
ax.text(775, 313, "Query < 100 ms", fontsize=8.5, fontweight="bold", color="#1D4ED8", ha="center", va="center")

# Arrow Gestalt & Colors to Tableau Serving (Cột 3 -> Cột 2/1)
draw_arrow(ax, c3_x + 20, 915, c2_x + c2_w - 20, 915, color="#DB2777", width=2.5)

# Lưu ảnh kết quả
repo_root = Path("D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt")
out_diagrams_1 = repo_root / "reports" / "diagrams" / "diagram_5_1_bi_mart_architecture.png"
out_diagrams_2 = repo_root / "reports" / "diagrams" / "bi_mart_architecture.png"
out_figures_1 = repo_root / "reports" / "figures" / "diagram_5_1_bi_mart_architecture.png"
out_figures_2 = repo_root / "reports" / "figures" / "bi_mart_architecture.png"

out_diagrams_1.parent.mkdir(parents=True, exist_ok=True)
out_figures_1.parent.mkdir(parents=True, exist_ok=True)

plt.tight_layout()
plt.savefig(out_diagrams_1, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig(out_diagrams_2, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig(out_figures_1, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig(out_figures_2, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")

# Sao chép sang images nếu có
try:
    import shutil
    target_img = Path("D:/Learning/FPT_polytechnic/Sem6/images/diagram_5_1_bi_mart_architecture.png")
    target_img.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(out_diagrams_1, target_img)
except Exception as e:
    pass

print("SUCCESSFULLY_RENDERED_BI_MART_ARCHITECTURE")
