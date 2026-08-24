"""
Script render sơ đồ kiến trúc pipeline xử lý dữ liệu 6 lớp (6-Layer Data Pipeline)
Loại bỏ hoàn toàn các thuật ngữ Bronze, Silver, Gold; thay bằng Layer 1 đến Layer 6.
Xuất ảnh độ phân giải cao (300 DPI) cho báo cáo đồ án tốt nghiệp The Outliers.
"""

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

def draw_pill(ax, x, y, w, h, bg_color, text, text_color="#FFFFFF", font_size=12, zorder=4):
    pill = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=8",
        facecolor=bg_color,
        edgecolor="none",
        zorder=zorder
    )
    ax.add_patch(pill)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=text_color,
            fontsize=font_size, fontweight="bold", fontfamily="sans-serif", zorder=zorder + 1)

def draw_arrow(ax, x1, y1, x2, y2, color="#334155", width=2.6, zorder=5):
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

# 1. TOP HEADER BANNER
draw_rounded_rect(ax, 40, 1220, 2320, 100, bg_color="#0F172A", border_color="#1E293B", border_width=2, radius=12)

ax.text(80, 1282, "KIẾN TRÚC ĐƯỜNG ỐNG XỬ LÝ DỮ LIỆU ĐA TẦNG (6-LAYER DATA PIPELINE)", 
        fontsize=18.5, fontweight="bold", color="#FFFFFF", va="center")
ax.text(80, 1248, "Điều phối qua Python CLI (srcs/06_run_pipeline/main.py) | Quản lý giao dịch ACID & Tối ưu hóa Supabase DWH", 
        fontsize=12, color="#94A3B8", va="center")

# Top Right Badge
draw_rounded_rect(ax, 2030, 1245, 300, 48, bg_color="#1E293B", border_color="#38BDF8", border_width=1.5, radius=8)
ax.text(2180, 1269, "END-TO-END ARCHITECTURE", fontsize=11, fontweight="bold", color="#38BDF8", ha="center", va="center")

# Cấu hình 6 Cột
col_w = 360
col_gap = 32
start_x = 40
top_y = 50
lane_h = 1140

cols_info = [
    {
        "pill": "LAYER 1",
        "pill_bg": "#1D4ED8",
        "title": "1. INGESTION LAYER",
        "subtitle": "[Nguồn Thu Thập Dữ Liệu]",
        "bg": "#EFF6FF",
        "border": "#3B82F6",
        "header_color": "#1E3A8A",
        "sections": [
            ("UNISOLAR Telemetry", [
                "42 trạm phát quang điện (PV)",
                "Chu kỳ đo vi mô 15 phút",
                "2.731.946 dòng dữ liệu sạch"
            ]),
            ("Open-Meteo REST API", [
                "Chuỗi khí quyển ERA5-Land (1h)",
                "850.752 dòng chuỗi thời gian",
                "11 biến bức xạ, gió, nhiệt, mây",
                "Tích hợp cờ is_day thiên văn"
            ]),
            ("AEMO Victoria NEM", [
                "Biểu giá mua bán điện FiT",
                "Khung giá 0.16 AUD/kWh"
            ]),
            ("Quản trị Lưu trữ", [
                "Data Version Control (DVC)",
                "Supabase S3 Buckets Storage"
            ])
        ]
    },
    {
        "pill": "LAYER 2",
        "pill_bg": "#475569",
        "title": "2. STAGING LAYER",
        "subtitle": "[Vùng Đệm Lưu Trữ]",
        "bg": "#F1F5F9",
        "border": "#64748B",
        "header_color": "#0F172A",
        "sections": [
            ("Supabase S3 Storage", [
                "Bucket raw-data bất biến",
                "Backup tệp nén an toàn"
            ]),
            ("Staging Tables (VARCHAR)", [
                "staging.stg_solar_gen (15m)",
                "staging.stg_weather (1h)",
                "staging.stg_solar_site (42 site)",
                "staging.stg_campus_meta (5 campus)"
            ]),
            ("Cơ chế Resampling Lưới", [
                "Đồng bộ mốc chuẩn 15 phút",
                "Toàn bộ cột kiểu VARCHAR",
                "Ngăn chặn lỗi Type Casting"
            ]),
            ("Kiểm toán QA/QC Toàn vẹn", [
                "Đối soát MD5 Fingerprint",
                "Kiểm tra Anti-Join thất thoát"
            ])
        ]
    },
    {
        "pill": "LAYER 3",
        "pill_bg": "#7C3AED",
        "title": "3. TRANSFORM LAYER",
        "subtitle": "[Làm Sạch & Gán Cờ Dị Thường]",
        "bg": "#F5F3FF",
        "border": "#8B5CF6",
        "header_color": "#5B21B6",
        "sections": [
            ("Điền khuyết Nhân quả Đa tầng", [
                "Ban đêm (is_day=0): Gán 0.0 kWh",
                "Tầng 1 (<=30p): Tuyến tính",
                "Tầng 2 (45p-2h): PCHIP Spline",
                "Tầng 3 (>2h): Hồi quy đa biến"
            ]),
            ("Căn chỉnh Khí quyển Nhân quả", [
                "Floor-Hour Lookup (Δt <= 0)",
                "Triệt tiêu 100% rò rỉ tương lai"
            ]),
            ("Phân lớp Dị thường Lai GMM-IF", [
                "Phân đoạn lá quyết định CART",
                "Mô hình kép GMM + Isolation Forest",
                "5 Rào chắn Giới hạn Vật lý",
                "Gán mã lý do O&M chi tiết"
            ])
        ]
    },
    {
        "pill": "LAYER 4",
        "pill_bg": "#059669",
        "title": "4. DWH CORE LAYER",
        "subtitle": "[Kho Dữ Liệu Chuẩn Hóa]",
        "bg": "#ECFDF5",
        "border": "#10B981",
        "header_color": "#065F46",
        "sections": [
            ("Mô hình Lược đồ Thiên hà", [
                "Galaxy Schema (Kimball)",
                "Đồng bộ hóa 2 mức độ hạt"
            ]),
            ("2 Bảng Sự kiện Lõi (Facts)", [
                "datawarehouse.fact_solar_gen",
                "datawarehouse.fact_weather"
            ]),
            ("5 Bảng Chiều Chung (Dimensions)", [
                "dim_solar_site (42 trạm, kWp)",
                "dim_geography (5 campuses Úc)",
                "dim_date (full_date, mùa vụ)",
                "dim_time (96 mốc 15 phút)",
                "dim_weather_type (Mã chuẩn WMO)"
            ]),
            ("Tối ưu Hóa Cơ sở Dữ liệu", [
                "Partitioning vật lý theo Năm",
                "Composite Indexes trên khóa ngoại"
            ])
        ]
    },
    {
        "pill": "LAYER 5",
        "pill_bg": "#D97706",
        "title": "5. DATA MARTS LAYER",
        "subtitle": "[Siêu Thị Dữ Liệu Chuyên Biệt]",
        "bg": "#FFFBEB",
        "border": "#F59E0B",
        "header_color": "#92400E",
        "sections": [
            ("BI Mart (Phân tích Tableau)", [
                "Nén 4 block 15p về cấp 1 giờ",
                "Materialized View duy nhất:",
                "bi_mart.mv_bi_mart_hourly_measures",
                "Tiền tính toán toàn bộ Metrics:",
                "  • PR actual, PR adjusted, PR correct",
                "  • Loss_temp (14.8% - 17.5%)",
                "  • Doanh thu FiT & Giảm thải CO2"
            ]),
            ("ML Mart (Học máy LightGBM)", [
                "Feature Store 52 đặc trưng:",
                "  • Solar Geometry (Zenith, Azimuth)",
                "  • Biến trễ Lags (t-1, t-4, t-96)",
                "  • Thống kê trượt Rolling Windows",
                "  • 13 đặc trưng mục tiêu T+h"
            ])
        ]
    },
    {
        "pill": "LAYER 6",
        "pill_bg": "#DC2626",
        "title": "6. SERVING LAYER",
        "subtitle": "[Ứng Dụng Trực Quan & Dự Báo]",
        "bg": "#FEF2F2",
        "border": "#EF4444",
        "header_color": "#991B1B",
        "sections": [
            ("Tableau Desktop (BI Reporting)", [
                "Kết nối Supabase Pooler Port 6543",
                "Tài khoản Read-only: tableau_user",
                "Dashboard 1: Executive Overview",
                "  (CF, Sản lượng 7.50 - 9.06 GWh, ESG)",
                "Dashboard 2: Efficiency & Loss",
                "  (Dual-Axis, Heatmap suy hao nhiệt)",
                "Dashboard 3: Anomaly & CBM",
                "  (Cảnh báo O&M, Rò rỉ điện ban đêm)"
            ]),
            ("Machine Learning (AI Serving)", [
                "LightGBM Regressor (Huber/MAE)",
                "Tầm dự báo: 15 phút & 1 giờ tới",
                "WAPE: 17.46% (15p), 21.60% (1h)",
                "Skill Score: +50.09% so với Prophet",
                "Giải thích mô hình: SHAP Values"
            ])
        ]
    }
]

# Vẽ 6 Swimlanes
for i, c in enumerate(cols_info):
    cx = start_x + i * (col_w + col_gap)
    # Background Lane
    draw_rounded_rect(ax, cx, top_y, col_w, lane_h, bg_color=c["bg"], border_color=c["border"], border_width=2, radius=12)
    
    # Pill Badge (LAYER 1, LAYER 2...)
    draw_pill(ax, cx + 20, top_y + lane_h - 48, col_w - 40, 32, bg_color=c["pill_bg"], text=c["pill"], font_size=11.5)
    
    # Title & Subtitle
    ax.text(cx + col_w / 2, top_y + lane_h - 75, c["title"], fontsize=12.5, fontweight="bold", color=c["header_color"], ha="center", va="center")
    ax.text(cx + col_w / 2, top_y + lane_h - 98, c["subtitle"], fontsize=10.2, fontweight="bold", color="#64748B", ha="center", va="center")
    
    # Đường kẻ ngăn cách header và body
    ax.plot([cx + 20, cx + col_w - 20], [top_y + lane_h - 116, top_y + lane_h - 116], color=c["border"], lw=1.2, ls="--", zorder=3)
    
    # Render các sub-boxes bên trong cột để lấp đầy không gian cân đối
    cur_y = top_y + lane_h - 135
    total_sections = len(c["sections"])
    available_h = cur_y - (top_y + 20)
    
    for sec_title, sec_items in c["sections"]:
        # Tính chiều cao phù hợp cho từng sub-box
        item_count = len(sec_items)
        box_h = 42 + item_count * 24.5
        
        draw_rounded_rect(ax, cx + 14, cur_y - box_h, col_w - 28, box_h, bg_color="#FFFFFF", border_color=c["border"], border_width=1.2, radius=8, zorder=2)
        
        # Sub-box title
        ax.text(cx + 26, cur_y - 20, f"• {sec_title}", fontsize=10.5, fontweight="bold", color=c["header_color"], va="center", zorder=3)
        
        # Sub-box items
        item_y = cur_y - 42
        for it in sec_items:
            ax.text(cx + 36, item_y, f"- {it}", fontsize=9.8, color="#334155", va="center", zorder=3)
            item_y -= 24.5
            
        cur_y -= (box_h + 14)

# Vẽ các mũi tên kết nối tuần tự giữa 6 lớp
for i in range(5):
    cx1 = start_x + i * (col_w + col_gap) + col_w
    cx2 = start_x + (i + 1) * (col_w + col_gap)
    mid_y = top_y + lane_h / 2
    draw_arrow(ax, cx1, mid_y, cx2, mid_y, color="#475569", width=2.6)

# Lưu ảnh ra các thư mục báo cáo và diagrams
out_diagrams = Path("D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/reports/diagrams/pipeline_sodo_kientruc.png")
out_figures = Path("D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/reports/figures/pipeline_sodo_kientruc.png")
out_diag_3_1 = Path("D:/Learning/FPT_polytechnic/Sem6/datn_outlier_hs_nlmt/reports/figures/diagram_3_1_pipeline_architecture.png")

out_diagrams.parent.mkdir(parents=True, exist_ok=True)
out_figures.parent.mkdir(parents=True, exist_ok=True)

plt.tight_layout()
plt.savefig(out_diagrams, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig(out_figures, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
plt.savefig(out_diag_3_1, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")

sys.stdout.buffer.write(b"SUCCESS_RENDERED_PIPELINE_SODO_KIENTRUC\n")
