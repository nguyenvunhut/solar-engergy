import logging
import os
import warnings

from dotenv import load_dotenv
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine, text

warnings.filterwarnings("ignore")
load_dotenv()


# THƯ MỤC XUẤT FILE KẾT QUẢ

OUTPUT_DIR = "pipeline_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def export_csv(df: pd.DataFrame, filename: str):
    """Xuất DataFrame ra file CSV vào OUTPUT_DIR."""
    path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(path, index=False)
    log.info(f"  💾 Đã xuất: {path}  ({len(df):,} dòng)")


# CẤU HÌNH KẾT NỐI SUPABASE

SUPABASE_HOST = os.getenv("DB_HOST")
SUPABASE_PORT = os.getenv("DB_PORT", "5432")
SUPABASE_DB = os.getenv("DB_NAME", "postgres")
SUPABASE_USER = os.getenv("DB_USER")
SUPABASE_PASSWORD = os.getenv("DB_PASSWORD")

SCHEMA = "staging"

# Cấu hình Logging theo format của bạn
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger()

# Ngưỡng phân loại khoảng trống (Gap size) theo số dòng 15-phút
GAP_LINEAR_MAX = 2  # ≤ 2 dòng (≤ 30 phút) → Linear
GAP_CUBIC_MAX = 8  # 3-8 dòng (≤ 2 tiếng) → Cubic Spline
# > 8 dòng (> 2 tiếng) → Regression

NIGHT_START = 18  # 18:30 → Bắt đầu ban đêm
NIGHT_END = 5  # 05:30 → Kết thúc ban đêm


# KHỞI TẠO KẾT NỐI DATABASE


def get_engine():
    url = (
        f"postgresql+psycopg2://{SUPABASE_USER}:{SUPABASE_PASSWORD}"
        f"@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DB}"
        f"?sslmode=require"
    )
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    log.info("Kết nối Supabase thành công\n")
    return engine


# THUẬT TOÁN XỬ LÝ TOÁN HỌC & LOGIC PHÂN TÍCH


def get_null_gaps(series: pd.Series):
    """Phát hiện và trả về list[(start_idx, end_idx, gap_size)] của các chuỗi NaN."""
    gaps = []
    in_gap = False
    start = None
    for i, v in enumerate(series):
        if pd.isna(v):
            if not in_gap:
                start = i
                in_gap = True
        else:
            if in_gap:
                gaps.append((start, i - 1, i - start))
                in_gap = False
    if in_gap:
        gaps.append((start, len(series) - 1, len(series) - start))
    return gaps


def rule_based_night_zero(
    solar_df: pd.DataFrame, weather_df: pd.DataFrame, site_key: int
) -> tuple:
    """Giai đoạn 1: Ép về 0 nếu là ban đêm hoặc bức xạ sóng ngắn = 0."""
    gen = solar_df["energy_generated_kwh"].copy()
    ts = solar_df["timestamp"]

    hour = ts.dt.hour + ts.dt.minute / 60
    is_night = (hour >= NIGHT_START + 0.5) | (hour < NIGHT_END + 0.5)

    w = weather_df[weather_df["sitekey"] == site_key][
        ["timestamp", "shortwave_radiation", "is_day"]
    ].copy()
    w = w.rename(columns={"timestamp": "timestamp"})
    w["timestamp"] = pd.to_datetime(w["timestamp"])

    merged = pd.merge_asof(
        solar_df[["timestamp"]].reset_index(),
        w.sort_values("timestamp"),
        on="timestamp",
        tolerance=pd.Timedelta("30min"),
        direction="nearest",
    ).set_index("index")

    zero_radiation = (merged["shortwave_radiation"].fillna(0) == 0) | (
        merged["is_day"].fillna(0) == 0
    )
    mask_zero = is_night.values | zero_radiation.values

    n_filled = (mask_zero & gen.isna()).sum()
    gen[mask_zero & gen.isna()] = 0.0
    return gen, n_filled


def regression_imputation_large_gaps_strict(
    solar_sub: pd.DataFrame,
    weather_df: pd.DataFrame,
    site_key: int,
    large_gap_indices: set,
) -> tuple:
    """Giai đoạn 2c: Hồi quy đa biến cô lập, chỉ điền vào các vị trí thuộc Large Gaps ban đầu."""
    FEATURES = [
        "shortwave_radiation",
        "direct_normal_irradiance",
        "diffuse_solar_radiation",
        "temperature_c",
    ]

    w = weather_df[weather_df["sitekey"] == site_key][["timestamp"] + FEATURES].copy()
    w = w.rename(columns={"timestamp": "timestamp"})
    w["timestamp"] = pd.to_datetime(w["timestamp"])

    merged = pd.merge_asof(
        solar_sub[["timestamp", "energy_generated_kwh"]].reset_index(),
        w.sort_values("timestamp"),
        on="timestamp",
        tolerance=pd.Timedelta("60min"),
        direction="nearest",
    ).set_index("index")

    train_mask = merged["energy_generated_kwh"].notna() & merged[FEATURES].notna().all(
        axis=1
    )
    pred_mask = merged["energy_generated_kwh"].isna() & merged[FEATURES].notna().all(
        axis=1
    )

    filled = 0
    if train_mask.sum() < 10:
        return solar_sub["energy_generated_kwh"].values, 0

    X_train = merged.loc[train_mask, FEATURES].values
    y_train = merged.loc[train_mask, "energy_generated_kwh"].values

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)

    model = LinearRegression()
    model.fit(X_train_sc, y_train)

    if pred_mask.sum() > 0:
        X_pred = merged.loc[pred_mask, FEATURES].values
        X_pred_sc = scaler.transform(X_pred)
        y_pred = model.predict(X_pred_sc)

        result = solar_sub["energy_generated_kwh"].copy()
        pred_indices = merged[pred_mask].index.tolist()

        for pos, idx in enumerate(pred_indices):
            local_pos = solar_sub.index.get_loc(idx) if idx in solar_sub.index else None
            # Chỉ điền nếu index này thuộc danh sách mảng khuyết lớn diện rộng
            if local_pos is not None and local_pos in large_gap_indices:
                result.iloc[local_pos] = max(0.0, y_pred[pos])
                filled += 1

        return result.values, filled
    return solar_sub["energy_generated_kwh"].values, 0


# CHƯƠNG TRÌNH CHÍNH (MAIN )


def main():
    log.info("=" * 65)
    log.info("  SOLAR DATA PIPELINE — SUPABASE INTEGRATION")
    log.info("=" * 65)

    # 1. Khởi tạo kết nối DB
    try:
        engine = get_engine()
    except Exception as e:
        log.error(f"Không thể kết nối đến Supabase: {e}")
        return

    # 2. Đọc dữ liệu từ schema 'staging' của Supabase
    log.info("[LOAD] Đang tải dữ liệu từ Supabase...")

    solar_df = pd.read_sql_query(
        f"SELECT * FROM {SCHEMA}.fact_solar_energy_gen", con=engine
    )
    weather_df = pd.read_sql_query(f"SELECT * FROM {SCHEMA}.fact_weather", con=engine)

    # 3. Chuẩn hóa thời gian
    solar_df["timestamp"] = pd.to_datetime(solar_df["timestamp"], errors="coerce")
    solar_df = (
        solar_df.dropna(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    weather_df["timestamp"] = pd.to_datetime(weather_df["timestamp"], errors="coerce")
    weather_df = (
        weather_df.dropna(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    total_null = solar_df["energy_generated_kwh"].isna().sum()
    total_rows = len(solar_df)
    log.info(
        f"[SUMMARY] Tổng số dòng: {total_rows:,} | Số ô NULL ban đầu: {total_null:,} ({total_null / total_rows * 100:.1f}%)"
    )

    # 4. Thực hiện vòng lặp xử lý cho từng sitekey theo chiến lược Hybrid Strict
    results = []
    results_after_rule = []
    results_after_linear = []
    results_after_cubic = []
    results_after_regression = []
    site_keys = sorted(solar_df["sitekey"].unique())

    for site in site_keys:
        sub = solar_df[solar_df["sitekey"] == site].copy().reset_index(drop=True)
        ts_index = pd.DatetimeIndex(sub["timestamp"])

        if sub["energy_generated_kwh"].isna().sum() == 0:
            results.append(sub)
            continue

        # Bước 1: Gán 0 cho ban đêm / không bức xạ (Lọc vật lý)
        null_before_rule = sub["energy_generated_kwh"].isna().sum()
        gen, n_rule = rule_based_night_zero(sub, weather_df, site)
        sub["energy_generated_kwh"] = gen
        null_after_rule = sub["energy_generated_kwh"].isna().sum()
        log.info(
            f"  Site {site:>2} | [Rule-Based Night] NULL trước: {null_before_rule:,}  →  sau: {null_after_rule:,}  (đã điền: {n_rule:,})"
        )
        results_after_rule.append(sub.copy())

        # Chuyển đổi thành chuỗi dữ liệu độc lập để tính toán chỉ số khoảng khuyết
        s_ts = pd.Series(
            sub["energy_generated_kwh"].values, index=ts_index, dtype=float
        )
        gaps = get_null_gaps(s_ts.values)

        # Phân loại mảng tọa độ Index độc lập dựa trên kích thước khoảng trống ban đầu
        linear_indices = []
        cubic_indices = []
        large_gap_indices = set()

        for start, end, size in gaps:
            indices = list(range(start, end + 1))
            if size <= GAP_LINEAR_MAX:
                linear_indices.extend(indices)  # Chỉ định khoảng trống ngắn
            elif size <= GAP_CUBIC_MAX:
                cubic_indices.extend(indices)  # Chỉ định khoảng trống vừa
            else:
                large_gap_indices.update(indices)  # Chỉ định khoảng trống diện rộng

        n_lin = len(linear_indices)
        n_cub = len(cubic_indices)

        # Giai đoạn 2a: Nội suy tuyến tính (Chỉ áp dụng và lưu đè lên mảng tọa độ ngắn)
        null_before_lin = int(s_ts.isna().sum())
        if linear_indices:
            full_linear = s_ts.interpolate(method="time")
            for idx in linear_indices:
                s_ts.iloc[idx] = full_linear.iloc[idx]
        null_after_lin = int(s_ts.isna().sum())
        log.info(
            f"  Site {site:>2} | [Linear Interp]    NULL trước: {null_before_lin:,}  →  sau: {null_after_lin:,}  (đã điền: {null_before_lin - null_after_lin:,})"
        )
        sub_lin = sub.copy()
        sub_lin["energy_generated_kwh"] = s_ts.values
        results_after_linear.append(sub_lin)

        # Giai đoạn 2b: Nội suy Cubic Spline (Chỉ áp dụng và lưu đè lên mảng tọa độ vừa)
        if cubic_indices:
            # Điền tuyến tính tạm thời vào một bản sao ẩn để tránh hiện tượng sập nhiễu ma trận khi gặp mảng trống lớn lân cận
            temp_ts = s_ts.interpolate(method="linear")
            full_cubic = temp_ts.interpolate(method="cubic")
            for idx in cubic_indices:
                s_ts.iloc[idx] = full_cubic.iloc[idx]

        null_after_cub = int(s_ts.isna().sum())
        log.info(
            f"  Site {site:>2} | [Cubic Spline]     NULL trước: {null_after_lin:,}  →  sau: {null_after_cub:,}  (đã điền: {null_after_lin - null_after_cub:,})"
        )
        sub_cub = sub.copy()
        sub_cub["energy_generated_kwh"] = s_ts.values
        results_after_cubic.append(sub_cub)

        # Cập nhật kết quả tính toán chuỗi đơn biến vào bảng
        sub["energy_generated_kwh"] = s_ts.values

        # Giai đoạn 2c: Hồi quy đa biến (Chỉ áp dụng cho các khoảng trống diện rộng)
        null_before_reg = sub["energy_generated_kwh"].isna().sum()
        n_reg = 0
        if large_gap_indices:
            vals_reg, n_reg = regression_imputation_large_gaps_strict(
                sub, weather_df, site, large_gap_indices
            )
            sub["energy_generated_kwh"] = vals_reg
        null_after_reg = sub["energy_generated_kwh"].isna().sum()
        log.info(
            f"  Site {site:>2} | [Regression]       NULL trước: {null_before_reg:,}  →  sau: {null_after_reg:,}  (đã điền: {n_reg:,})"
        )
        results_after_regression.append(sub.copy())

        # Hậu xử lý: Đảm bảo không sinh giá trị âm ngoài ý muốn
        sub["energy_generated_kwh"] = sub["energy_generated_kwh"].clip(lower=0)
        results.append(sub)

        null_after_rule = sub["energy_generated_kwh"].isna().sum()
        null_after_lin = sum(
            1
            for i in range(len(sub))
            if pd.isna(sub["energy_generated_kwh"].iloc[i])
            and i in set(linear_indices + cubic_indices + list(large_gap_indices))
        )
        null_remaining = sub["energy_generated_kwh"].isna().sum()
        log.info(
            f"  Site {site:>2} | "
            f"Rule→ {n_rule:,} ô  | "
            f"Lin→ {n_lin:,} ô  | "
            f"Cubic→ {n_cub:,} ô  | "
            f"Reg→ {n_reg:,} ô  | "
            f"NULL còn lại: {null_remaining:,}"
        )

    # 5. Tổng hợp kết quả và đẩy ngược trở lại Supabase
    solar_cleaned = pd.concat(results, ignore_index=True)
    null_after = solar_cleaned["energy_generated_kwh"].isna().sum()
    filled_total = total_null - null_after

    log.info("")
    log.info("─" * 65)
    log.info("  [TỔNG KẾT QUÁ TRÌNH XỬ LÝ NULL]")
    log.info(
        f"  NULL ban đầu       : {total_null:,}  ({total_null / total_rows * 100:.1f}%)"
    )
    log.info(
        f"  Đã điền được       : {filled_total:,}  ({filled_total / total_null * 100:.1f}% số NULL)"
    )
    log.info(
        f"  NULL còn lại       : {null_after:,}  ({null_after / total_rows * 100:.2f}% toàn bộ dữ liệu)"
    )
    log.info("─" * 65)

    # ── Xuất file CSV kết quả từng giai đoạn ──────────────────
    log.info("")
    log.info("[EXPORT CSV] Đang xuất file kết quả từng giai đoạn...")
    export_csv(
        pd.concat(results_after_rule, ignore_index=True),
        "result_01_rule_based_night.csv",
    )
    export_csv(
        pd.concat(results_after_linear, ignore_index=True),
        "result_02_linear_interpolation.csv",
    )
    export_csv(
        pd.concat(results_after_cubic, ignore_index=True), "result_03_cubic_spline.csv"
    )
    export_csv(
        pd.concat(results_after_regression, ignore_index=True),
        "result_04_regression.csv",
    )
    export_csv(solar_cleaned, "result_05_final_cleaned.csv")
    log.info("")

    log.info(
        f"[EXPORT] Đang đẩy dữ liệu sạch lên Supabase table: {SCHEMA}.fact_solar_energy_gen..."
    )
    solar_cleaned.to_sql(
        name="fact_solar_energy_gen",
        con=engine,
        schema=SCHEMA,
        if_exists="replace",
        index=False,
        chunksize=5000,
    )
    log.info("Pipeline hoàn tất dữ liệu sạch đã được lưu trữ an toàn tại Supabase.")
    log.info("=" * 65)


if __name__ == "__main__":
    main()
