"""
Script render sơ đồ kiến trúc hệ thống dữ liệu (System Architecture Diagram)
cho dự án tốt nghiệp 'The Outliers' bằng Matplotlib & PIL với độ phân giải cao.
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Thiết lập font và style đồ họa
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Segoe UI Emoji", "Arial", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["figure.dpi"] = 300

fig, ax = plt.subplots(figsize=(24, 13.5), facecolor="#F8FAFC")
ax.set_facecolor("#F8FAFC")
ax.set_xlim(0, 2400)
ax.set_ylim(0, 1350)
ax.axis("off")

def draw_rounded_rect(ax, x, y, w, h, bg_color, border_color, border_width=1.5, radius=14, alpha=1.0, zorder=2):
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

def draw_arrow(ax, x1, y1, x2, y2, color="#64748B", width=2.2, zorder=5):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=width,
            mutation_scale=18,
            shrinkA=4,
            shrinkB=4
        ),
        zorder=zorder
    )

# 1. HEADER BANNER
draw_rounded_rect(ax, 40, 1230, 2320, 95, bg_color="#0F172A", border_color="#1E293B", border_width=2, radius=12)

ax.text(70, 1290, "KIẾN TRÚC HỆ THỐNG DỮ LIỆU TẬP TRUNG (END-TO-END DATA ARCHITECTURE)", 
        fontsize=18, fontweight="bold", color="#FFFFFF", va="center")
ax.text(70, 1255, "Dự án Tốt nghiệp Chuyên ngành Xử lý Dữ liệu — The Outliers | Nền tảng Supabase PostgreSQL & Python Pipeline", 
        fontsize=11.5, color="#94A3B8", va="center")

# Top Right Badge
draw_rounded_rect(ax, 2030, 1255, 300, 42, bg_color="#1E293B", border_color="#38BDF8", border_width=1.5, radius=8)
ax.text(2180, 1276, "GALAXY SCHEMA & DUAL MARTS", fontsize=11, fontweight="bold", color="#38BDF8", ha="center", va="center")

# Cột chiều rộng và vị trí X
col_w = 435
col_gap = 35
start_x = 40
top_y = 60
lane_h = 1140

cols_info = [
    {
        "num": "1",
        "title": "1. RAW DATA LAYER",
        "subtitle": "Nguồn Dữ Liệu Thô & Quản Trị Storage",
        "bg": "#F8FAFC",
        "border": "#64748B",
        "header_bg": "#475569",
        "text_color": "#0F172A"
    },
    {
        "num": "2",
        "title": "2. STAGING & BUFFER",
        "subtitle": "Làm Sạch & Chuẩn Hóa (Schema: staging)",
        "bg": "#FFFBEB",
        "border": "#D97706",
        "header_bg": "#B45309",
        "text_color": "#78350F"
    },
    {
        "num": "3",
        "title": "3. DATA WAREHOUSE",
        "subtitle": "Galaxy Schema (Schema: datawarehouse)",
        "bg": "#EEF2FF",
        "border": "#4338CA",
        "header_bg": "#3730A3",
        "text_color": "#1E1B4B"
    },
    {
        "num": "4",
        "title": "4. DATA MART LAYER",
        "subtitle": "Phục Vụ Đa Mục Tiêu (bi_mart & ml_mart)",
        "bg": "#F0FDF4",
        "border": "#16A34A",
        "header_bg": "#15803D",
        "text_color": "#14532D"
    },
    {
        "num": "5",
        "title": "5. APPLICATION & CONSUMPTION",
        "subtitle": "Trực Quan Hóa & Dự Báo Thông Minh",
        "bg": "#FDF2F8",
        "border": "#DB2777",
        "header_bg": "#9D174D",
        "text_color": "#831843"
    }
]

# Vẽ 5 Swimlanes
for i, c in enumerate(cols_info):
    cx = start_x + i * (col_w + col_gap)
    # Background Lane
    draw_rounded_rect(ax, cx, top_y, col_w, lane_h, bg_color=c["bg"], border_color=c["border"], border_width=2, radius=12)
    # Header box
    draw_rounded_rect(ax, cx, top_y + lane_h - 68, col_w, 68, bg_color=c["header_bg"], border_color=c["border"], border_width=1, radius=10)
    ax.text(cx + col_w / 2, top_y + lane_h - 26, c["title"], fontsize=13, fontweight="bold", color="#FFFFFF", ha="center", va="center")
    ax.text(cx + col_w / 2, top_y + lane_h - 50, c["subtitle"], fontsize=9.5, color="#E2E8F0", ha="center", va="center")

# ==================== NỘI DUNG TỪNG CỘT ====================

# ----------------- CỘT 1: RAW DATA -----------------
c1_x = start_x
# Box 1.1: CSV Files
draw_rounded_rect(ax, c1_x + 20, 870, col_w - 40, 220, bg_color="#FFFFFF", border_color="#94A3B8", border_width=1.5, radius=10)
ax.text(c1_x + 35, 1055, "[Source 1] IoT PV Sensors (CSV Files)", fontsize=11.5, fontweight="bold", color="#0369A1")
txt_c1_1 = (
    "• Solar_Energy_Generation.csv (15m)\n"
    "  (2.731.947 bản ghi sản lượng thực tế)\n"
    "• Solar_Site_Details.csv (42 trạm phát PV)\n"
    "• campus_meta.csv (5 campuses tại Úc)\n"
    "• calender.csv (Lịch nghỉ lễ & mùa thi)"
)
ax.text(c1_x + 35, 960, txt_c1_1, fontsize=10.5, color="#334155", va="center", linespacing=1.4)

# Box 1.2: API
draw_rounded_rect(ax, c1_x + 20, 610, col_w - 40, 230, bg_color="#FFFFFF", border_color="#94A3B8", border_width=1.5, radius=10)
ax.text(c1_x + 35, 805, "[Source 2] Open-Meteo Archive API", fontsize=11.5, fontweight="bold", color="#0284C7")
txt_c1_2 = (
    "• Chuỗi thời gian khí tượng theo Giờ (1h)\n"
    "• Bức xạ sóng ngắn (GHI / Shortwave)\n"
    "• Bức xạ trực tiếp & Bức xạ khuếch tán\n"
    "• Nhiệt độ không khí 2m, Tốc độ gió\n"
    "• Độ che phủ mây, Lượng mưa, Nắng"
)
ax.text(c1_x + 35, 705, txt_c1_2, fontsize=10.5, color="#334155", va="center", linespacing=1.4)

# Box 1.3: DVC & S3
draw_rounded_rect(ax, c1_x + 20, 360, col_w - 40, 220, bg_color="#EFF6FF", border_color="#3B82F6", border_width=1.5, radius=10)
ax.text(c1_x + 35, 545, "[Storage] Quản Trị DVC & S3", fontsize=11.5, fontweight="bold", color="#1D4ED8")
txt_c1_3 = (
    "• Data Version Control (DVC)\n"
    "• S3 Object Storage (Supabase Buckets)\n"
    "• Quản lý phiên bản tệp Parquet & CSV\n"
    "• Tách biệt kho Git và dữ liệu lớn\n"
    "• Đảm bảo khả năng tái lập (Reproducibility)"
)
ax.text(c1_x + 35, 450, txt_c1_3, fontsize=10.5, color="#1E3A8A", va="center", linespacing=1.4)

# Box 1.4: Thống kê thô
draw_rounded_rect(ax, c1_x + 20, 100, col_w - 40, 230, bg_color="#F1F5F9", border_color="#CBD5E1", border_width=1.2, radius=10)
ax.text(c1_x + 35, 295, "[Summary] Quy Mô Dữ Liệu Ban Đầu", fontsize=11, fontweight="bold", color="#475569")
txt_c1_4 = (
    "• Tổng dung lượng thô: ~250 MB\n"
    "• Thời gian ghi nhận: 2020 – 2022\n"
    "• Cơ chế chống Rate-Limit (Sleep 60s)\n"
    "• Pure Python DB Driver: pg8000\n"
    "• Kết nối qua Supabase Pooler IPv4"
)
ax.text(c1_x + 35, 195, txt_c1_4, fontsize=10, color="#475569", va="center", linespacing=1.45)


# ----------------- CỘT 2: STAGING & BUFFER -----------------
c2_x = start_x + 1 * (col_w + col_gap)
# Box 2.1: Raw Tables
draw_rounded_rect(ax, c2_x + 20, 870, col_w - 40, 220, bg_color="#FEF3C7", border_color="#F59E0B", border_width=1.5, radius=10)
ax.text(c2_x + 35, 1055, "[Staging] Raw String Tables (VARCHAR)", fontsize=11.5, fontweight="bold", color="#92400E")
txt_c2_1 = (
    "• stg_solar_energy_generation\n"
    "• stg_open_meteo_weather_raw\n"
    "• stg_solar_site_details\n"
    "• stg_campus_meta\n"
    "• stg_calender\n"
    "→ Nạp nguyên bản dữ liệu chuỗi thô"
)
ax.text(c2_x + 35, 960, txt_c2_1, fontsize=10.5, color="#78350F", va="center", linespacing=1.35)

# Box 2.2: ETL Process
draw_rounded_rect(ax, c2_x + 20, 540, col_w - 40, 300, bg_color="#FFFFFF", border_color="#D97706", border_width=2, radius=10)
ax.text(c2_x + 35, 805, "[Engine] Python ETL Pipeline (Transform)", fontsize=11.5, fontweight="bold", color="#B45309")
txt_c2_2 = (
    "1. Ép kiểu dữ liệu (Cast Types sang chuẩn)\n"
    "2. Điền khuyết (Hybrid Imputation):\n"
    "   - Interpolation chuỗi thời gian\n"
    "   - Phục hồi lỗ hổng cảm biến\n"
    "3. Lọc nhiễu ban đêm (Night-time noise):\n"
    "   - Triệt tiêu dòng rò rỉ khi bức xạ = 0\n"
    "4. Nhận diện bất thường (Outlier Detection):\n"
    "   - Rolling IQR theo từng trạm\n"
    "   - GMM & Isolation Forest kết hợp"
)
ax.text(c2_x + 35, 670, txt_c2_2, fontsize=10.5, color="#0F172A", va="center", linespacing=1.35)

# Box 2.3: Mirror Buffer Tables
draw_rounded_rect(ax, c2_x + 20, 220, col_w - 40, 290, bg_color="#FEF3C7", border_color="#F59E0B", border_width=1.5, radius=10)
ax.text(c2_x + 35, 475, "[Buffer] Mirror Buffer Tables (Đã làm sạch)", fontsize=11.5, fontweight="bold", color="#92400E")
txt_c2_3 = (
    "• staging.dim_solar_site (Định danh trạm)\n"
    "• staging.dim_geography (Tọa độ địa lý)\n"
    "• staging.dim_date (Trục ngày chuẩn hóa)\n"
    "• staging.dim_time (Trục giờ & phút 15p)\n"
    "• staging.dim_weather_type (Mã thời tiết)\n"
    "• staging.fact_solar_energy_gen\n"
    "• staging.fact_weather"
)
ax.text(c2_x + 35, 350, txt_c2_3, fontsize=10.5, color="#78350F", va="center", linespacing=1.35)

# Box 2.4: Safe Transactions
draw_rounded_rect(ax, c2_x + 20, 100, col_w - 40, 95, bg_color="#FDE68A", border_color="#D97706", border_width=1.5, radius=10)
ax.text(c2_x + 35, 160, "[Integrity] QA/QC & Giao Dịch An Toàn", fontsize=11, fontweight="bold", color="#92400E")
ax.text(c2_x + 35, 130, "MD5 Fingerprint • Anti-Join Check • Dry-run Mode", fontsize=10, color="#78350F")


# ----------------- CỘT 3: DATA WAREHOUSE -----------------
c3_x = start_x + 2 * (col_w + col_gap)
# Box 3.1: Dimensions
draw_rounded_rect(ax, c3_x + 20, 790, col_w - 40, 300, bg_color="#E0E7FF", border_color="#6366F1", border_width=1.8, radius=10)
ax.text(c3_x + 35, 1055, "[Dimensions] 5 Conformed Dimensions", fontsize=11.5, fontweight="bold", color="#3730A3")
txt_c3_1 = (
    "• dim_solar_site (PK: site_id)\n"
    "  (42 trạm, công suất kWp, panel, inverter)\n"
    "• dim_geography (PK: geo_id)\n"
    "  (Tọa độ lat/lon, tên cơ sở La Trobe)\n"
    "• dim_date (PK: date_id)\n"
    "  (full_date, ngày, tháng, năm, kỳ lễ/thi)\n"
    "• dim_time (PK: time_id)\n"
    "  (Lưới 15 phút: 96 mốc thời gian/ngày)\n"
    "• dim_weather_type (PK: weather_type_id)\n"
    "  (Mã WMO chuẩn hóa, cờ is_day)"
)
ax.text(c3_x + 35, 920, txt_c3_1, fontsize=10.5, color="#1E1B4B", va="center", linespacing=1.35)

# Box 3.2: Fact PV
draw_rounded_rect(ax, c3_x + 20, 480, col_w - 40, 280, bg_color="#FFFFFF", border_color="#4F46E5", border_width=2, radius=10)
ax.text(c3_x + 35, 725, "[Fact 1] fact_solar_energy_gen", fontsize=11.5, fontweight="bold", color="#4338CA")
txt_c3_2 = (
    "• Khóa chính: gen_id\n"
    "• Khóa ngoại: site_id, geo_id, date_id, time_id\n"
    "• Chỉ số đo: energy_generated_kwh\n"
    "• Cờ bất thường: gmm_if_outlier_flag\n"
    "• Thuật toán điền: fill_null_algorithm\n"
    "• Tần suất: Chu kỳ 15 phút (2.73M dòng)"
)
ax.text(c3_x + 35, 600, txt_c3_2, fontsize=10.5, color="#1E1B4B", va="center", linespacing=1.35)

# Box 3.3: Fact Weather
draw_rounded_rect(ax, c3_x + 20, 190, col_w - 40, 260, bg_color="#FFFFFF", border_color="#4F46E5", border_width=2, radius=10)
ax.text(c3_x + 35, 415, "[Fact 2] fact_weather", fontsize=11.5, fontweight="bold", color="#4338CA")
txt_c3_3 = (
    "• Khóa chính: weather_id\n"
    "• Khóa ngoại: geo_id, date_id, time_id, type_id\n"
    "• Chỉ số: shortwave_radiation, temp_c,\n"
    "  cloud_cover, wind_speed, precipitation\n"
    "• Tần suất: Chu kỳ 1 giờ (367K dòng)"
)
ax.text(c3_x + 35, 305, txt_c3_3, fontsize=10.5, color="#1E1B4B", va="center", linespacing=1.35)

# Box 3.4: Galaxy Schema
draw_rounded_rect(ax, c3_x + 20, 100, col_w - 40, 65, bg_color="#C7D2FE", border_color="#4338CA", border_width=1.5, radius=10)
ax.text(c3_x + col_w / 2, 132, "Galaxy Schema: Đồng bộ độ hạt (Granularity)", fontsize=10.5, fontweight="bold", color="#312E81", ha="center", va="center")


# ----------------- CỘT 4: DATA MART LAYER -----------------
c4_x = start_x + 3 * (col_w + col_gap)
# Box 4.1: BI Mart
draw_rounded_rect(ax, c4_x + 20, 600, col_w - 40, 490, bg_color="#DCFCE7", border_color="#22C55E", border_width=1.8, radius=10)
ax.text(c4_x + 35, 1055, "[Data Mart 1] BI Mart (Schema: bi_mart)", fontsize=11.5, fontweight="bold", color="#15803D")
txt_c4_1 = (
    "• fact_solar_performance_hourly:\n"
    "  Nén dữ liệu về cùng chu kỳ 1 giờ\n\n"
    "• Materialized Views tối ưu hóa:\n"
    "  - mv_bi_mart_hourly_measures\n"
    "  - mv_bi_mart_daily_kpis\n"
    "  - vw_bi_mart_hourly_measures_replace\n\n"
    "• Hệ thống Measures & KPIs kinh doanh:\n"
    "  - Performance Ratio (PR: Hiệu suất thực/chuẩn)\n"
    "  - Capacity Factor (CF: Tỷ lệ công suất)\n"
    "  - Doanh thu bán điện FIT (1.938 VNĐ/kWh)\n"
    "  - Tín chỉ môi trường (CO2 Offset & Cây xanh)"
)
ax.text(c4_x + 35, 810, txt_c4_1, fontsize=10.5, color="#14532D", va="center", linespacing=1.35)

# Box 4.2: ML Mart
draw_rounded_rect(ax, c4_x + 20, 100, col_w - 40, 470, bg_color="#DCFCE7", border_color="#22C55E", border_width=1.8, radius=10)
ax.text(c4_x + 35, 535, "[Data Mart 2] ML Mart (Schema: ml_mart)", fontsize=11.5, fontweight="bold", color="#15803D")
txt_c4_2 = (
    "• base_build & v3_final_cleaned.parquet:\n"
    "  Bảng cơ sở nạp trực tiếp vào Model ML\n\n"
    "• Vá ghép thời tiết nhân quả (Causal Join):\n"
    "  Triệt tiêu 100% rò rỉ thời tiết tương lai\n\n"
    "• Feature Engineering Store (40 biến):\n"
    "  - Hình học mặt trời lý thuyết (Solar Geo)\n"
    "  - Biến trễ (Lags: t-1, t-4, t-96) & Rolling\n"
    "  - Tương tác khí quyển & Nhiệt độ tấm pin\n"
    "  - Sàng lọc qua kiểm định VIF & Mutual Info"
)
ax.text(c4_x + 35, 310, txt_c4_2, fontsize=10.5, color="#14532D", va="center", linespacing=1.35)


# ----------------- CỘT 5: APPLICATION LAYER -----------------
c5_x = start_x + 4 * (col_w + col_gap)
# Box 5.1: Tableau Dashboards
draw_rounded_rect(ax, c5_x + 20, 600, col_w - 40, 490, bg_color="#FCE7F3", border_color="#EC4899", border_width=1.8, radius=10)
ax.text(c5_x + 35, 1055, "[BI Tool] Tableau BI Dashboards", fontsize=11.5, fontweight="bold", color="#BE185D")
txt_c5_1 = (
    "• Dashboard 1: Executive Overview\n"
    "  - Tổng quan sản lượng toàn mạng lưới\n"
    "  - Xếp hạng công suất 42 trạm phát PV\n"
    "  - Lũy kế doanh thu & Cắt giảm CO2\n\n"
    "• Dashboard 2: Hiệu suất & Khí hậu\n"
    "  - Phân tích tương quan bức xạ & nhiệt độ\n"
    "  - Suy hao nhiệt độ (Thermal Degradation)\n\n"
    "• Dashboard 3: Bất thường & Bảo trì\n"
    "  - Phát hiện lỗi Inverter & Bám bẩn\n"
    "  - Giám sát rò rỉ dòng điện ban đêm"
)
ax.text(c5_x + 35, 815, txt_c5_1, fontsize=10.5, color="#831843", va="center", linespacing=1.3)

# Box 5.2: ML Models
draw_rounded_rect(ax, c5_x + 20, 100, col_w - 40, 470, bg_color="#FCE7F3", border_color="#EC4899", border_width=1.8, radius=10)
ax.text(c5_x + 35, 535, "[AI/ML] Machine Learning Serving", fontsize=11.5, fontweight="bold", color="#BE185D")
txt_c5_2 = (
    "• Mô hình vô địch: LightGBM Regressor\n"
    "  - Tối ưu siêu tham số với Optuna\n"
    "  - Hàm mất mát kháng nhiễu: Huber Loss\n"
    "  - Tầm dự báo: 1 giờ & 2 giờ tới (Horizons)\n\n"
    "• Mô hình đối chứng Baseline:\n"
    "  - Meta Prophet & Chuỗi thời gian ARIMA\n\n"
    "• Giải thích mô hình (Explainable AI):\n"
    "  - SHAP Values & Đóng góp đặc trưng\n"
    "  - Xác thực độ lệch pha trạm thời gian thực"
)
ax.text(c5_x + 35, 315, txt_c5_2, fontsize=10.5, color="#831843", va="center", linespacing=1.3)


# ==================== CÁC MŨI TÊN KẾT NỐI (DATA FLOW) ====================
# Cột 1 -> Cột 2
draw_arrow(ax, c1_x + col_w - 20, 970, c2_x + 20, 970, color="#64748B", width=2.4)
draw_arrow(ax, c1_x + col_w - 20, 720, c2_x + 20, 920, color="#64748B", width=2.4)
draw_arrow(ax, c1_x + col_w - 20, 470, c2_x + 20, 680, color="#2563EB", width=2.4)

# Cột 2 nội bộ
draw_arrow(ax, c2_x + col_w / 2, 870, c2_x + col_w / 2, 840, color="#D97706", width=2.2)
draw_arrow(ax, c2_x + col_w / 2, 540, c2_x + col_w / 2, 510, color="#D97706", width=2.2)

# Cột 2 -> Cột 3 (Load DW)
draw_arrow(ax, c2_x + col_w - 20, 360, c3_x + 20, 920, color="#4338CA", width=2.6)

# Cột 3 -> Cột 4 (DW to Marts)
draw_arrow(ax, c3_x + col_w - 20, 620, c4_x + 20, 840, color="#16A34A", width=2.6)
draw_arrow(ax, c3_x + col_w - 20, 320, c4_x + 20, 340, color="#16A34A", width=2.6)

# Cột 4 -> Cột 5 (Marts to Apps)
draw_arrow(ax, c4_x + col_w - 20, 840, c5_x + 20, 840, color="#DB2777", width=2.6)
draw_arrow(ax, c4_x + col_w - 20, 340, c5_x + 20, 340, color="#DB2777", width=2.6)

# Lưu ảnh ra các thư mục
out_figures = Path("reports/figures/system_architecture.png")
out_diagrams = Path("reports/diagrams/system_architecture.drawio.png")

out_figures.parent.mkdir(parents=True, exist_ok=True)
out_diagrams.parent.mkdir(parents=True, exist_ok=True)

plt.tight_layout()
plt.savefig(out_figures, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig(out_diagrams, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")

# Copy sang thư mục images chung nếu có
try:
    import shutil
    target_img = Path("D:/Learning/FPT_polytechnic/Sem6/images/system_architecture.png")
    target_img.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(out_figures, target_img)
except Exception as e:
    pass

sys.stdout.buffer.write(b"SUCCESS_RENDERED_SYSTEM_ARCHITECTURE\n")
