"""
Script render sơ đồ kiến trúc luồng dữ liệu DWH -> BI Mart (Hourly) -> Tableau
(Lược bỏ phần Daily KPIs theo yêu cầu người dùng) với độ phân giải cao 300 DPI.
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

fig, ax = plt.subplots(figsize=(18, 16.5), facecolor="#F8FAFC")
ax.set_facecolor("#F8FAFC")
ax.set_xlim(0, 1800)
ax.set_ylim(0, 1650)
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

def draw_arrow_down(ax, x, y_start, y_end, label="", color="#15803D", width=3.0, badge_bg="#DCFCE7", badge_fg="#14532D"):
    ax.annotate(
        "",
        xy=(x, y_end),
        xytext=(x, y_start),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=width,
            mutation_scale=22,
            shrinkA=2,
            shrinkB=2
        ),
        zorder=5
    )
    if label:
        mid_y = (y_start + y_end) / 2
        lbl_w = len(label) * 11 + 30
        draw_rounded_rect(ax, x - lbl_w/2, mid_y - 18, lbl_w, 36, bg_color=badge_bg, border_color=color, border_width=1.2, radius=6, zorder=6)
        ax.text(x, mid_y, label, fontsize=10.5, fontweight="bold", color=badge_fg, ha="center", va="center", zorder=7)

# 1. HEADER BANNER
draw_rounded_rect(ax, 40, 1520, 1720, 95, bg_color="#0F172A", border_color="#1E293B", border_width=2, radius=14)
ax.text(70, 1582, "SƠ ĐỒ KIẾN TRÚC TẦNG BI DATA MART (HOURLY STREAMLINED)", 
        fontsize=18, fontweight="bold", color="#FFFFFF", va="center")
ax.text(70, 1548, "Chuyển đổi dữ liệu DWH sang Materialized View Cấp Giờ (mv_bi_mart_hourly_measures) phục vụ Tableau (< 100 ms)", 
        fontsize=11.5, color="#94A3B8", va="center")

# Top Right Badge
draw_rounded_rect(ax, 1460, 1545, 270, 44, bg_color="#1E293B", border_color="#38BDF8", border_width=1.5, radius=8)
ax.text(1595, 1567, "SCHEMA: DWH -> BI MART", fontsize=11, fontweight="bold", color="#38BDF8", ha="center", va="center")

# ==================== KHỐI 1: SCHEMA DATAWAREHOUSE (TOP) ====================
top_dwh_y = 1260
dwh_h = 220
draw_rounded_rect(ax, 40, top_dwh_y, 1720, dwh_h, bg_color="#EFF6FF", border_color="#3B82F6", border_width=2, radius=14)

# Header DWH
draw_rounded_rect(ax, 40, top_dwh_y + dwh_h - 48, 1720, 48, bg_color="#1D4ED8", border_color="#3B82F6", border_width=1, radius=12)
ax.text(900, top_dwh_y + dwh_h - 24, "SCHEMA: datawarehouse (LƯỢC ĐỒ THIÊN HÀ — GALAXY SCHEMA | 3.5M DÒNG)", 
        fontsize=13, fontweight="bold", color="#FFFFFF", ha="center", va="center")

# 2 Sub-boxes in DWH
# Left Sub-box: fact_solar_energy_gen
draw_rounded_rect(ax, 70, top_dwh_y + 20, 770, 135, bg_color="#FFFFFF", border_color="#93C5FD", border_width=1.5, radius=10)
ax.text(90, top_dwh_y + 128, "fact_solar_energy_gen (Chu kỳ 15 Phút — 2.731.946 Dòng)", fontsize=11.5, fontweight="bold", color="#1E3A8A")
txt_fgen = (
    "• Khóa chính / Khóa ngoại: PK gen_id | FK site_id, geo_id, date_id, time_id\n"
    "• Đo lường: energy_generated_kwh (Sản lượng điện 15m)\n"
    "• Giám sát dị thường: gmm_if_outlier_flag, fill_null_algorithm"
)
ax.text(90, top_dwh_y + 70, txt_fgen, fontsize=10, color="#1E293B", linespacing=1.35)

# Right Sub-box: fact_weather & dims
draw_rounded_rect(ax, 880, top_dwh_y + 20, 850, 135, bg_color="#FFFFFF", border_color="#93C5FD", border_width=1.5, radius=10)
ax.text(900, top_dwh_y + 128, "fact_weather (Chu kỳ 1 Giờ — 850.752 Dòng) & 5 Conformed Dimensions", fontsize=11.5, fontweight="bold", color="#1E3A8A")
txt_fw = (
    "• Khóa chính / Khóa ngoại: PK weather_id | FK geo_id, date_id, time_id, weather_type_id\n"
    "• Khí tượng ERA5-Land: shortwave_radiation (GHI), temperature_c, cloud_cover, wind_speed\n"
    "• Bảng chiều dùng chung: dim_solar_site, dim_geography, dim_date, dim_time, dim_weather_type"
)
ax.text(900, top_dwh_y + 70, txt_fw, fontsize=10, color="#1E293B", linespacing=1.35)


# ==================== MŨI TÊN 1: DWH -> BI MART ====================
draw_arrow_down(ax, 900, top_dwh_y, 1160, label="Nén 15m -> 1h (hourly_bucket) & Ghép nối Causal Join khí tượng", color="#15803D", width=3.2, badge_bg="#DCFCE7", badge_fg="#14532D")


# ==================== KHỐI 2: SCHEMA BI_MART (MIDDLE) ====================
bi_y = 440
bi_h = 720
draw_rounded_rect(ax, 40, bi_y, 1720, bi_h, bg_color="#F0FDF4", border_color="#16A34A", border_width=2.2, radius=14)

# Header BI Mart
draw_rounded_rect(ax, 40, bi_y + bi_h - 52, 1720, 52, bg_color="#15803D", border_color="#16A34A", border_width=1, radius=12)
ax.text(900, bi_y + bi_h - 26, "SCHEMA: bi_mart (TẦNG BI DATA MART — MATERIALIZED VIEW CẤP GIỜ TỐI ƯU HÓA)", 
        fontsize=13.5, fontweight="bold", color="#FFFFFF", ha="center", va="center")

# Main Container inside BI Mart: mv_bi_mart_hourly_measures
draw_rounded_rect(ax, 70, bi_y + 30, 1660, 615, bg_color="#FFFFFF", border_color="#22C55E", border_width=1.8, radius=12)

# Title of the Materialized View
draw_rounded_rect(ax, 70, bi_y + 595, 1660, 50, bg_color="#DCFCE7", border_color="#22C55E", border_width=1, radius=10)
ax.text(100, bi_y + 620, "bi_mart.mv_bi_mart_hourly_measures (Materialized View Cấp Giờ — 1h Granularity)", 
        fontsize=13, fontweight="bold", color="#14532D", va="center")

# Right Badge on MV Title: Index Info
draw_rounded_rect(ax, 1220, bi_y + 602, 480, 36, bg_color="#15803D", border_color="none", radius=6)
ax.text(1460, bi_y + 620, "UNIQUE INDEX: idx_mv_hourly_unique (date_id, site_id, hourly_bucket)", 
        fontsize=9.2, fontweight="bold", color="#FFFFFF", ha="center", va="center")

# 4 Detailed Attribute Panels (2x2 Grid)
panel_w = 780
panel_h = 245

# Panel 1: Physical Measures & Solar Geometry (Top-Left)
p1_x = 100
p1_y = bi_y + 330
draw_rounded_rect(ax, p1_x, p1_y, panel_w, panel_h, bg_color="#F8FAFC", border_color="#CBD5E1", border_width=1.2, radius=8)
draw_rounded_rect(ax, p1_x, p1_y + panel_h - 36, panel_w, 36, bg_color="#334155", border_color="none", radius=6)
ax.text(p1_x + 20, p1_y + panel_h - 18, "1. ĐO LƯỜNG VẬT LÝ, THỜI TIẾT & THÔNG SỐ TRẠM", fontsize=11, fontweight="bold", color="#FFFFFF", va="center")
txt_p1 = (
    "• e_hourly (kWh) : Tổng sản lượng phát thực tế theo giờ (SUM 4 mốc 15 phút)\n"
    "• shortwave_radiation (W/m²) : Bức xạ sóng ngắn mặt phẳng ngang (GHI)\n"
    "• temperature_c (°C), wind_speed (m/s), precipitation_mm, sunshine_duration\n"
    "• is_day (BOOLEAN) : Cờ phân định ban ngày (true khi hourly_bucket từ 6h–18h)\n"
    "• p_stc (kWp) : Công suất danh định chuẩn của 42 trạm phát PV\n"
    "• t_cell (°C) = temperature_c + (shortwave_radiation * 0.035) (Nhiệt độ ô pin thực tế)"
)
ax.text(p1_x + 20, p1_y + 105, txt_p1, fontsize=9.6, color="#0F172A", va="center", linespacing=1.35)

# Panel 2: Technical Performance & Loss (Top-Right)
p2_x = 920
p2_y = bi_y + 330
draw_rounded_rect(ax, p2_x, p2_y, panel_w, panel_h, bg_color="#F8FAFC", border_color="#CBD5E1", border_width=1.2, radius=8)
draw_rounded_rect(ax, p2_x, p2_y + panel_h - 36, panel_w, 36, bg_color="#0F766E", border_color="none", radius=6)
ax.text(p2_x + 20, p2_y + panel_h - 18, "2. HIỆU SUẤT KỸ THUẬT & SUY HAO NHIỆT ĐỘ", fontsize=11, fontweight="bold", color="#FFFFFF", va="center")
txt_p2 = (
    "• e_stc_hourly = p_stc * (GHI / 1000.0) [khi GHI >= 100 W/m²] (Sản lượng STC)\n"
    "• loss_temp = (t_cell - 25) * 0.004 [khi t_cell > 25°C] (Suy hao do quá nhiệt)\n"
    "• pr_actual = e_hourly / e_stc_hourly (Hệ số hiệu suất thực tế trạm)\n"
    "• pr_adjusted = 0.78 * (1 - loss_temp) (Hiệu suất đã bù trừ tổn thất nhiệt)\n"
    "• e_expected = e_stc_hourly * pr_adjusted (Sản lượng mục tiêu kỳ vọng)\n"
    "• delta_baseline = e_hourly - e_expected (Chênh lệch thực tế so với kỳ vọng)"
)
ax.text(p2_x + 20, p2_y + 105, txt_p2, fontsize=9.6, color="#0F172A", va="center", linespacing=1.35)

# Panel 3: Financial & Environmental Metrics (Bottom-Left)
p3_x = 100
p3_y = bi_y + 55
draw_rounded_rect(ax, p3_x, p3_y, panel_w, panel_h, bg_color="#F8FAFC", border_color="#CBD5E1", border_width=1.2, radius=8)
draw_rounded_rect(ax, p3_x, p3_y + panel_h - 36, panel_w, 36, bg_color="#B45309", border_color="none", radius=6)
ax.text(p3_x + 20, p3_y + panel_h - 18, "3. CHỈ SỐ KINH DOANH, TÀI CHÍNH & MÔI TRƯỜNG", fontsize=11, fontweight="bold", color="#FFFFFF", va="center")
txt_p3 = (
    "• fit_rate = 1.938 VNĐ/kWh (Biểu giá mua điện mặt trời FiT chuẩn hóa)\n"
    "• estimated_revenue = e_hourly * fit_rate (Doanh thu thương mại ước tính)\n"
    "• cost_of_underperformance = (e_expected - e_hourly) * fit_rate [khi thiếu hụt]\n"
    "• co2_avoided_kg = e_hourly * 0.533 kg (Khối lượng CO2 giảm phát thải)\n"
    "• equivalent_trees_planted = co2_avoided_kg / 21.8 kg (Quy đổi cây xanh tương đương)\n"
    "• Tự động cập nhật định kỳ qua REFRESH MATERIALIZED VIEW CONCURRENTLY"
)
ax.text(p3_x + 20, p3_y + 105, txt_p3, fontsize=9.6, color="#0F172A", va="center", linespacing=1.35)

# Panel 4: Anomaly Detection & Maintenance (Bottom-Right)
p4_x = 920
p4_y = bi_y + 55
draw_rounded_rect(ax, p4_x, p4_y, panel_w, panel_h, bg_color="#F8FAFC", border_color="#CBD5E1", border_width=1.2, radius=8)
draw_rounded_rect(ax, p4_x, p4_y + panel_h - 36, panel_w, 36, bg_color="#BE185D", border_color="none", radius=6)
ax.text(p4_x + 20, p4_y + panel_h - 18, "4. GIÁM SÁT BẤT THƯỜNG GMM-IF & PHÂN LOẠI LỖI O&M", fontsize=11, fontweight="bold", color="#FFFFFF", va="center")
txt_p4 = (
    "• gmm_if_outlier_flag (BOOLEAN) : Cờ phát hiện dị thường từ mô hình GMM-IF\n"
    "• gmm_if_outlier_reason (VARCHAR) : 6 mã lý do kỹ thuật chuẩn hóa:\n"
    "  1. GMM_IF_CONSENSUS (Đồng thuận ML) | 2. PHYSICAL_OVER_CAPACITY (Vượt trần)\n"
    "  3. PHYSICAL_HIGH_ENERGY_NO_SUN (Phát đêm) | 4. HIGH_ENERGY_LOW_RAD\n"
    "  5. LOW_ENERGY_STRONG_SUN (Mất phát trưa) | 6. PHYSICAL_DISTRIBUTION_JUMP\n"
    "• Cung cấp dữ liệu trực tiếp cho hệ thống cảnh báo sớm và bảo trì O&M"
)
ax.text(p4_x + 20, p4_y + 105, txt_p4, fontsize=9.6, color="#0F172A", va="center", linespacing=1.35)


# ==================== MŨI TÊN 2: BI MART -> TABLEAU ====================
draw_arrow_down(ax, 900, bi_y, 340, label="Tableau Relationships (1:N) & PostgreSQL Native Query (< 100 ms)", color="#2563EB", width=3.2, badge_bg="#EFF6FF", badge_fg="#1D4ED8")


# ==================== KHỐI 3: TẦNG ỨNG DỤNG TABLEAU (BOTTOM) ====================
app_y = 50
app_h = 240
draw_rounded_rect(ax, 40, app_y, 1720, app_h, bg_color="#FAF5FF", border_color="#8B5CF6", border_width=2, radius=14)

# Header Tableau
draw_rounded_rect(ax, 40, app_y + app_h - 48, 1720, 48, bg_color="#6D28D9", border_color="#8B5CF6", border_width=1, radius=12)
ax.text(900, app_y + app_h - 24, "TẦNG ỨNG DỤNG TRỰC QUAN HÓA & PHÂN TÍCH TABLEAU DASHBOARDS", 
        fontsize=13, fontweight="bold", color="#FFFFFF", ha="center", va="center")

# 3 Dashboard Cards in Tableau Layer
dash_w = 515
dash_h = 150
dash_gap = 45
dash_start_x = 70

dashboards = [
    {
        "title": "Dashboard 1: Executive Overview",
        "sub": "Tổng Quan Điều Hành & Doanh Thu",
        "desc": "• Thẻ chỉ số BANs: Tổng sản lượng, PR, CF\n• Bản đồ Campus Map phân bố 42 trạm phát\n• Xếp hạng công suất & Doanh thu lũy kế FiT\n• Khối lượng CO2 giảm phát thải & Cây xanh",
        "color": "#1E40AF",
        "border": "#3B82F6"
    },
    {
        "title": "Dashboard 2: Efficiency & Loss",
        "sub": "Hiệu Suất & Phân Rã Tổn Thất Nhiệt",
        "desc": "• Biểu đồ 2 trục: Sản lượng vs GHI vs Nhiệt độ\n• Bản đồ nhiệt Heatmap tổn thất nhiệt theo tháng\n• Xếp hạng hiệu suất thiết bị Inverter/Optimizer\n• Nhận diện trạm bị che bóng hoặc sụt giảm PR",
        "color": "#B45309",
        "border": "#F59E0B"
    },
    {
        "title": "Dashboard 3: Anomaly & O&M",
        "sub": "Giám Sát Bất Thường & Bảo Trì",
        "desc": "• Chuỗi thời gian đánh dấu điểm dị thường GMM-IF\n• Heatmap rò rỉ điện ban đêm (E > 0 lúc 18h30-5h30)\n• Phân loại danh mục sự cố kỹ thuật 6 mã O&M\n• Hỗ trợ kỹ sư khoanh vùng vị trí thiết bị lỗi",
        "color": "#9D174D",
        "border": "#EC4899"
    }
]

for i, d in enumerate(dashboards):
    dx = dash_start_x + i * (dash_w + dash_gap)
    draw_rounded_rect(ax, dx, app_y + 20, dash_w, dash_h, bg_color="#FFFFFF", border_color=d["border"], border_width=1.5, radius=10)
    draw_rounded_rect(ax, dx, app_y + 20 + dash_h - 32, dash_w, 32, bg_color=d["color"], border_color="none", radius=6)
    ax.text(dx + dash_w/2, app_y + 20 + dash_h - 16, d["title"], fontsize=10.5, fontweight="bold", color="#FFFFFF", ha="center", va="center")
    ax.text(dx + 18, app_y + 65, d["desc"], fontsize=9.2, color="#1E293B", linespacing=1.35)

# Lưu ảnh kết quả
repo_root = Path("D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt")
out_diagrams = repo_root / "reports" / "diagrams" / "bi_mart_hourly_flow.png"
out_figures = repo_root / "reports" / "figures" / "bi_mart_hourly_flow.png"
out_diagrams_copy = repo_root / "reports" / "diagrams" / "diagram_5_1_bi_mart_hourly_flow.png"

out_diagrams.parent.mkdir(parents=True, exist_ok=True)
out_figures.parent.mkdir(parents=True, exist_ok=True)

plt.tight_layout()
plt.savefig(out_diagrams, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig(out_figures, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig(out_diagrams_copy, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")

print("SUCCESSFULLY_RENDERED_BI_MART_HOURLY_FLOW")
