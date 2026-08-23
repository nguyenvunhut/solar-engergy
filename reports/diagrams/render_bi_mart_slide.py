"""
Script render sơ đồ kiến trúc BI Data Mart ánh xạ 1:1 cho Slide
(ĐÃ LOẠI BỎ TOÀN BỘ CÁC CHỈ SỐ DOANH THU/TÀI CHÍNH - TẬP TRUNG HOÀN TOÀN VÀO VẬN HÀNH, KỸ THUẬT VÀ MÔI TRƯỜNG ESG)
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Cấu hình đồ họa chuẩn trình chiếu slide
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["figure.dpi"] = 300

fig, ax = plt.subplots(figsize=(16, 9), facecolor="#F8FAFC")
ax.set_facecolor("#F8FAFC")
ax.set_xlim(0, 1600)
ax.set_ylim(0, 900)
ax.axis("off")

def draw_rounded_rect(ax, x, y, w, h, bg_color, border_color, border_width=1.8, radius=10, alpha=1.0, zorder=2):
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

def draw_arrow_down(ax, x, y_start, y_end, label="", color="#15803D", width=3.2):
    ax.annotate(
        "",
        xy=(x, y_end),
        xytext=(x, y_start),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=width,
            mutation_scale=24,
            shrinkA=3,
            shrinkB=3
        ),
        zorder=5
    )
    if label:
        mid_y = (y_start + y_end) / 2
        lbl_w = len(label) * 12.2 + 36
        draw_rounded_rect(ax, x - lbl_w/2, mid_y - 18, lbl_w, 36, bg_color="#FFFFFF", border_color=color, border_width=1.5, radius=7, zorder=6)
        ax.text(x, mid_y, label, fontsize=12.2, fontweight="bold", color=color, ha="center", va="center", zorder=7)

# 1. HEADER BANNER (TOP)
draw_rounded_rect(ax, 35, 808, 1530, 74, bg_color="#0F172A", border_color="#1E293B", border_width=2, radius=10)
ax.text(65, 856, "KIẾN TRÚC TẦNG BI DATA MART (ÁNH XẠ CHỈ SỐ THEO DASHBOARD)", 
        fontsize=18.5, fontweight="bold", color="#FFFFFF", va="center")
ax.text(65, 828, "Phân nhóm chỉ số tính toán sẵn tại tầng BI Mart phục vụ trực tiếp cho từng Dashboard Tableau", 
        fontsize=12.2, color="#94A3B8", va="center")

# Badge Slide 14
draw_rounded_rect(ax, 1340, 822, 205, 46, bg_color="#1E293B", border_color="#38BDF8", border_width=1.6, radius=7)
ax.text(1442, 845, "SLIDE 14 — BI MART", fontsize=12.2, fontweight="bold", color="#38BDF8", ha="center", va="center")


# ==================== 1. TẦNG DATA WAREHOUSE (DWH: h = 190) ====================
dwh_y = 600
dwh_h = 190
draw_rounded_rect(ax, 35, dwh_y, 1530, dwh_h, bg_color="#EFF6FF", border_color="#3B82F6", border_width=2.2, radius=10)

# DWH Title bar
draw_rounded_rect(ax, 35, dwh_y + dwh_h - 36, 1530, 36, bg_color="#1D4ED8", border_color="#3B82F6", border_width=1, radius=8)
ax.text(800, dwh_y + dwh_h - 18, "1. TẦNG KHO DỮ LIỆU (SCHEMA: datawarehouse)", 
        fontsize=13.8, fontweight="bold", color="#FFFFFF", ha="center", va="center")

# 2 Thẻ DWH (h = 132)
draw_rounded_rect(ax, 60, dwh_y + 12, 715, 132, bg_color="#FFFFFF", border_color="#93C5FD", border_width=1.5, radius=8)
ax.text(80, dwh_y + 112, "fact_solar_energy_gen (Dữ liệu phát điện)", fontsize=13.5, fontweight="bold", color="#1E3A8A")
txt_dwh1 = (
    "• Chu kỳ đo 15 phút từ hệ thống cảm biến 42 trạm phát PV\n"
    "• Lưu trữ chi tiết lịch sử sản lượng thực tế (2.73 triệu dòng)\n"
    "• Định danh khóa chính và các khóa ngoại liên kết đa chiều"
)
ax.text(80, dwh_y + 44, txt_dwh1, fontsize=11.8, color="#334155", linespacing=1.35)

draw_rounded_rect(ax, 825, dwh_y + 12, 715, 132, bg_color="#FFFFFF", border_color="#93C5FD", border_width=1.5, radius=8)
ax.text(845, dwh_y + 112, "fact_weather & Các bảng Chiều (Dimensions)", fontsize=13.5, fontweight="bold", color="#1E3A8A")
txt_dwh2 = (
    "• Chu kỳ 1 giờ: Bức xạ mặt trời (GHI), Nhiệt độ, Mây, Gió (ERA5)\n"
    "• 850.752 bản ghi khí tượng viễn thám độ chính xác cao\n"
    "• Bảng chiều dùng chung: Trạm phát, Khuôn viên, Thời gian, Thời tiết"
)
ax.text(845, dwh_y + 44, txt_dwh2, fontsize=11.8, color="#334155", linespacing=1.35)


# ==================== MŨI TÊN 1 ====================
draw_arrow_down(ax, 800, dwh_y, 540, label="Nén dữ liệu 15 phút -> 1 giờ & Ghép nối dữ liệu khí tượng", color="#15803D", width=3.2)


# ==================== 2. TẦNG BI DATA MART (h = 240) ====================
bi_y = 300
bi_h = 240
draw_rounded_rect(ax, 35, bi_y, 1530, bi_h, bg_color="#F0FDF4", border_color="#16A34A", border_width=2.2, radius=10)

# BI Title bar
draw_rounded_rect(ax, 35, bi_y + bi_h - 36, 1530, 36, bg_color="#15803D", border_color="#16A34A", border_width=1, radius=8)
ax.text(800, bi_y + bi_h - 18, "2. TẦNG SIÊU THỊ DỮ LIỆU (SCHEMA: bi_mart — mv_bi_mart_hourly_measures)", 
        fontsize=13.8, fontweight="bold", color="#FFFFFF", ha="center", va="center")

# 3 Cột chỉ số tương ứng 3 Dashboard (h = 184)
cw = 475
ch = 184
c_gap = 25
c_start = 60

col_metrics = [
    {
        "title": "Nhóm Chỉ Số Cho Dashboard 1",
        "sub": "(Tổng Quan Vận Hành & Môi Trường)",
        "items": [
            "• Sản lượng phát thực tế theo giờ (e_hourly)",
            "• Khối lượng CO2 giảm phát thải (co2_avoided)",
            "• Số cây xanh quy đổi tương đương (trees_planted)",
            "• Hệ số hiệu suất thực tế trạm (pr_actual)",
            "• Công suất định mức danh định (p_stc)"
        ],
        "bg_hdr": "#1E40AF",
        "border": "#3B82F6"
    },
    {
        "title": "Nhóm Chỉ Số Cho Dashboard 2",
        "sub": "(Hiệu Suất Kỹ Thuật & Tổn Thất Nhiệt)",
        "items": [
            "• Bức xạ mặt trời GHI & Nhiệt độ môi trường",
            "• Nhiệt độ ô pin (t_cell) & Tổn thất quá nhiệt (loss_temp)",
            "• Sản lượng định mức lý thuyết chuẩn STC (e_stc_hourly)",
            "• Hiệu suất đã bù trừ nhiệt độ (pr_adjusted)",
            "• Chênh lệch sản lượng suy giảm (delta_underperformance)"
        ],
        "bg_hdr": "#0F766E",
        "border": "#14B8A6"
    },
    {
        "title": "Nhóm Chỉ Số Cho Dashboard 3",
        "sub": "(Giám Sát Dị Thường & Chẩn Đoán O&M)",
        "items": [
            "• Cờ phát hiện dị thường GMM-IF (outlier_flag)",
            "• Danh mục 6 mã lý do kỹ thuật (outlier_reason)",
            "• Cờ nhận diện dòng rò phát đêm (is_day = false)",
            "• Độ lệch sản lượng so với kỳ vọng (delta_baseline)",
            "• Tốc độ gió, độ che phủ mây tại thời điểm lỗi"
        ],
        "bg_hdr": "#9D174D",
        "border": "#EC4899"
    }
]

for i, cm in enumerate(col_metrics):
    cx = c_start + i * (cw + c_gap)
    draw_rounded_rect(ax, cx, bi_y + 10, cw, ch, bg_color="#FFFFFF", border_color=cm["border"], border_width=1.6, radius=8)
    draw_rounded_rect(ax, cx, bi_y + 10 + ch - 44, cw, 44, bg_color=cm["bg_hdr"], border_color="none", radius=6)
    ax.text(cx + cw/2, bi_y + 10 + ch - 15, cm["title"], fontsize=12.6, fontweight="bold", color="#FFFFFF", ha="center", va="center")
    ax.text(cx + cw/2, bi_y + 10 + ch - 31, cm["sub"], fontsize=10.2, color="#E2E8F0", ha="center", va="center")
    
    txt_block = "\n".join(cm["items"])
    ax.text(cx + 16, bi_y + 68, txt_block, fontsize=11.4, color="#0F172A", va="center", linespacing=1.38)


# ==================== MŨI TÊN 2: KẾT NỐI TRỰC TIẾP ====================
draw_arrow_down(ax, 800, bi_y, 240, label="Kết nối trực tiếp (Direct Connection)", color="#2563EB", width=3.2)


# ==================== 3. TẦNG TABLEAU DASHBOARDS (h = 220) ====================
app_y = 20
app_h = 220
draw_rounded_rect(ax, 35, app_y, 1530, app_h, bg_color="#FAF5FF", border_color="#8B5CF6", border_width=2.2, radius=10)

# App Title bar
draw_rounded_rect(ax, 35, app_y + app_h - 36, 1530, 36, bg_color="#6D28D9", border_color="#8B5CF6", border_width=1, radius=8)
ax.text(800, app_y + app_h - 18, "3. TẦNG TRỰC QUAN HÓA & PHÂN TÍCH (TABLEAU DASHBOARDS)", 
        fontsize=13.8, fontweight="bold", color="#FFFFFF", ha="center", va="center")

# 3 Dashboards (h = 166)
d_list = [
    {
        "title": "Dashboard 1: Executive Overview",
        "sub": "Tổng Quan Vận Hành & Môi Trường (ESG)",
        "desc": "• Báo cáo tổng quan sản lượng toàn bộ 42 trạm phát\n• Thẻ chỉ số BANs & Bản đồ phân bố địa lý khuôn viên\n• Theo dõi khối lượng giảm phát thải khí nhà kính CO2\n• Đánh giá mức độ đóng góp năng lượng xanh theo kỳ",
        "bg_hdr": "#1E40AF",
        "border": "#3B82F6"
    },
    {
        "title": "Dashboard 2: Operational Efficiency",
        "sub": "Hiệu Suất Kỹ Thuật & Tổn Thất Nhiệt",
        "desc": "• Phân tích tương quan Sản lượng — Bức xạ — Nhiệt độ\n• Bản đồ nhiệt (Heatmap) nhận diện tổn thất quá nhiệt\n• Đánh giá và xếp hạng hiệu suất thiết bị biến tần\n• Phát hiện sớm các cụm pin bị suy hao hiệu suất",
        "bg_hdr": "#0F766E",
        "border": "#14B8A6"
    },
    {
        "title": "Dashboard 3: Anomaly Diagnostic",
        "sub": "Giám Sát Bất Thường & Bảo Trì O&M",
        "desc": "• Giám sát chuỗi thời gian các điểm bất thường GMM-IF\n• Khoanh vùng hiện tượng dòng rò ban đêm (E > 0)\n• Phân loại nguyên nhân sự cố hỗ trợ đội ngũ bảo trì\n• Tối ưu hóa kế hoạch bảo dưỡng định kỳ trạm phát",
        "bg_hdr": "#9D174D",
        "border": "#EC4899"
    }
]

for i, d in enumerate(d_list):
    dx = c_start + i * (cw + c_gap)
    draw_rounded_rect(ax, dx, app_y + 10, cw, 166, bg_color="#FFFFFF", border_color=d["border"], border_width=1.5, radius=8)
    draw_rounded_rect(ax, dx, app_y + 10 + 166 - 42, cw, 42, bg_color=d["bg_hdr"], border_color="none", radius=6)
    ax.text(dx + cw/2, app_y + 10 + 166 - 15, d["title"], fontsize=12.6, fontweight="bold", color="#FFFFFF", ha="center", va="center")
    ax.text(dx + cw/2, app_y + 10 + 166 - 30, d["sub"], fontsize=10.2, color="#E2E8F0", ha="center", va="center")
    ax.text(dx + 16, app_y + 56, d["desc"], fontsize=11.4, color="#1E293B", va="center", linespacing=1.4)

# Lưu ảnh kết quả
repo_root = Path("D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt")
out_slide_1 = repo_root / "reports" / "diagrams" / "bi_mart_slide.png"
out_slide_2 = repo_root / "reports" / "diagrams" / "diagram_5_1_bi_mart_slide.png"
out_fig_1 = repo_root / "reports" / "figures" / "bi_mart_slide.png"
out_fig_2 = repo_root / "reports" / "figures" / "diagram_5_1_bi_mart_slide.png"

out_slide_1.parent.mkdir(parents=True, exist_ok=True)
out_fig_1.parent.mkdir(parents=True, exist_ok=True)

plt.tight_layout()
plt.savefig(out_slide_1, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig(out_slide_2, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig(out_fig_1, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig(out_fig_2, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")

print("SUCCESSFULLY_REMOVED_FINANCIAL_METRICS")
