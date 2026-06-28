# %%
# 1. IMPORT THƯ VIỆN
import os
import warnings
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from dotenv import load_dotenv

warnings.filterwarnings('ignore', category=UserWarning)
sns.set_theme(style="whitegrid", palette="muted")
load_dotenv()


# %%
# 2. TẢI DỮ LIỆU
def load_data_from_bi_mart():
    print("Đang kết nối Supabase và tải dữ liệu...")
    engine_url = (
        f"postgresql+psycopg2://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}"
        f"@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT', '5432')}"
        f"/{os.environ.get('DB_NAME')}?sslmode=require"
    )
    engine = create_engine(engine_url)

    query = """
        SELECT e_hourly, e_expected, loss_temp, pr_adjusted
        FROM bi_mart.mv_bi_mart_hourly_measures
        WHERE e_hourly IS NOT NULL;
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    print(f"Đã tải xong {df.shape[0]:,} dòng dữ liệu!")
    return df

# %%
# 3. VẼ BIỂU ĐỒ PHÂN PHỐI — TOÀN BỘ DỮ LIỆU (bao gồm ban đêm)
# Mục đích: xem cấu trúc tổng thể, nhận biết zero-inflation tự nhiên
def plot_full_distribution(df):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(
        'Phân phối Đơn biến các chỉ số cốt lỗi',
        fontsize=15, fontweight='bold'
    )

    configs = [
        (axes[0, 0], 'e_hourly',    'blue',   'Sản lượng điện thực (e_hourly)',           'kWh'),
        (axes[0, 1], 'e_expected',  'orange', 'Sản lượng kỳ vọng (e_expected)',            'kWh'),
        (axes[1, 0], 'loss_temp',   'red',    'Tổn thất do quá nhiệt (loss_temp)',         'Tỷ lệ hao hụt'),
        (axes[1, 1], 'pr_adjusted', 'green',  'Hiệu suất PR hiệu chỉnh (pr_adjusted > 0)', 'PR Ratio'),
    ]

    for ax, col, color, title, xlabel in configs:
        data = df[col] if col != 'pr_adjusted' else df[df[col] > 0][col]
        sns.histplot(data, bins=50, kde=True, ax=ax, color=color, alpha=0.75)
        ax.axvline(data.mean(),   color='black',  linestyle='--', linewidth=1.2,
                   label=f'Mean = {data.mean():.3f}')
        ax.axvline(data.median(), color='orange', linestyle='-',  linewidth=1.2,
                   label=f'Median = {data.median():.3f}')
        ax.set_title(title, fontsize=12)
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Count')
        ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig('univariate_full.png', dpi=150, bbox_inches='tight')
    # plt.show()
    print("Đã lưu: univariate_full.png")

# %%
# 4. VẼ BIỂU ĐỒ PHÂN PHỐI — CHỈ BAN NGÀY (e_hourly > 0)
# Mục đích: loại bỏ nhiễu zero ban đêm, xem phân phối thực khi hệ thống hoạt động
def plot_daytime_distribution(df):
    df_day = df[df['e_hourly'] > 0].copy()
    print(f"Tập ban ngày: {len(df_day):,} dòng / {len(df):,} tổng ({len(df_day)/len(df)*100:.1f}%)")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(
        'Phân phối Đơn biến — Chỉ ban ngày (e_hourly > 0)',
        fontsize=15, fontweight='bold'
    )

    configs = [
        (axes[0, 0], 'e_hourly',    'blue',   'Sản lượng điện thực (e_hourly)',    'kWh'),
        (axes[0, 1], 'e_expected',  'orange', 'Sản lượng kỳ vọng (e_expected)',     'kWh'),
        (axes[1, 0], 'loss_temp',   'red',    'Tổn thất do quá nhiệt (loss_temp)',  'Tỷ lệ hao hụt'),
        (axes[1, 1], 'pr_adjusted', 'green',  'Hiệu suất PR hiệu chỉnh (pr_adjusted)', 'PR Ratio'),
    ]

    for ax, col, color, title, xlabel in configs:
        data = df_day[col]
        sns.histplot(data, bins=50, kde=True, ax=ax, color=color, alpha=0.75)
        ax.axvline(data.mean(),   color='black',  linestyle='--', linewidth=1.2,
                   label=f'Mean = {data.mean():.3f}')
        ax.axvline(data.median(), color='orange', linestyle='-',  linewidth=1.2,
                   label=f'Median = {data.median():.3f}')
        ax.set_title(title, fontsize=12)
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Count')
        ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig('univariate_daytime.png', dpi=150, bbox_inches='tight')
    # plt.show()
    print("Đã lưu: univariate_daytime.png")

# %%
# 5. THỐNG KÊ MÔ TẢ
def print_stats(df):
    df_day = df[df['e_hourly'] > 0]

    print("\n" + "="*60)
    print("THỐNG KÊ MÔ TẢ — TOÀN BỘ DỮ LIỆU")
    print("="*60)
    print(df.describe().round(4))

    print("\n" + "="*60)
    print("THỐNG KÊ MÔ TẢ — CHỈ BAN NGÀY (e_hourly > 0)")
    print("="*60)
    print(df_day.describe().round(4))

    print("\n" + "="*60)
    print("TỶ LỆ BAN NGÀY / BAN ĐÊM")
    print("="*60)
    n_night = (df['e_hourly'] == 0).sum()
    n_day   = (df['e_hourly'] >  0).sum()
    print(f"  Ban đêm (e_hourly = 0): {n_night:>8,}  ({n_night/len(df)*100:.1f}%)")
    print(f"  Ban ngày (e_hourly > 0): {n_day:>7,}  ({n_day/len(df)*100:.1f}%)")

# 6. MAIN
if __name__ == "__main__":
    df = load_data_from_bi_mart()

    print_stats(df)
    plot_full_distribution(df)
    plot_daytime_distribution(df)