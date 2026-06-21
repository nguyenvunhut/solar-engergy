import logging
import os

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# 1. CẤU HÌNH LOGGING & MÔI TRƯỜNG
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# Tự động tìm và load các biến từ file .env ở thư mục gốc
load_dotenv(find_dotenv())


# 2. HÀM TẠO KẾT NỐI ĐỘC LẬP
def create_db_engine() -> Engine:
    """Hàm khởi tạo kết nối tới Supabase bằng SQLAlchemy."""
    supabase_user = os.getenv("DB_USER")
    supabase_password = os.getenv("DB_PASSWORD")
    supabase_host = os.getenv("DB_HOST")
    supabase_port = os.getenv("DB_PORT", "5432")
    supabase_db = os.getenv("DB_NAME", "postgres")

    # Kiểm tra an toàn xem có thiếu credentials không
    if not all([supabase_user, supabase_password, supabase_host]):
        log.error("Thiếu thông tin kết nối Supabase trong file .env!")
        raise ValueError("Missing database credentials")

    url = (
        f"postgresql+psycopg2://{supabase_user}:{supabase_password}"
        f"@{supabase_host}:{supabase_port}/{supabase_db}"
        f"?sslmode=require"
    )

    try:
        engine = create_engine(url, pool_pre_ping=True)
        # Test nhẹ connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("Khởi tạo kết nối Supabase thành công!")
        return engine
    except SQLAlchemyError as e:
        log.error(f"Lỗi khởi tạo kết nối Database: {e}")
        raise


# 3. HÀM THỰC THI LOGIC BI MART
def create_bi_mart_hourly_view(engine: Engine) -> None:
    """
    Tạo View nén cấp Giờ cho BI Mart trên Supabase.
    """
    sql_logic = text("""
        -- Chỉ định rõ tạo View trong schema bi_mart
        CREATE OR REPLACE VIEW bi_mart.vw_bi_mart_hourly_measures AS
        
        -- Bước 1: Lấy dữ liệu nền và JOIN để lấy công suất thực tế của từng Site
        WITH hourly_base AS (
            SELECT 
                f.date_id,
                f.hourly_bucket,
                f.site_id,
                f.total_energy AS e_hourly,
                f.shortwave_radiation AS g_hourly,
                f.temperature_c AS t_ambient,
                -- Lấy capacity_kw, nếu NULL thì gán bằng 0 để tránh lỗi toán học
                COALESCE(d.capacity_kw, 0) AS p_stc,
                1938 AS fit_rate     -- Giữ nguyên giả định giá FIT 1938 VNĐ/kWh
            FROM bi_mart.fact_solar_performance_hourly f
            LEFT JOIN bi_mart.dim_solar_site d 
                ON f.site_id = d.site_id
        ),
        
        -- Bước 2: Tính toán các chỉ số vật lý trung gian & PR thực tế
        efficiency_calc AS (
            SELECT 
                *,
                -- Nhiệt độ tấm pin ước tính
                (t_ambient + (g_hourly * 0.03)) AS t_cell,
                
                -- PR thực tế: Lọc nhiễu cảm biến ban đêm (bức xạ < 50 W/m2 coi như bằng 0)
                CASE 
                    WHEN g_hourly < 50 THEN 0 
                    ELSE e_hourly / NULLIF(p_stc * (g_hourly / 1000.0), 0) 
                END AS pr_actual
            FROM hourly_base
        ),
        
        -- Bước 3: Tính toán hệ số sụt giảm do quá nhiệt
        adjusted_calc AS (
            SELECT 
                *,
                CASE 
                    WHEN t_cell > 25 THEN (t_cell - 25) * 0.004 
                    ELSE 0 
                END AS loss_temp
            FROM efficiency_calc
        ),
        
        -- BƯỚC 3.5: Tính chuẩn PR Adjusted
        pr_adj_calc AS (
            SELECT 
                *,
                -- Chốt chặn ĐÚNG: Áp dụng cùng ngưỡng lọc nhiễu < 50 như PR Actual
                CASE 
                    WHEN g_hourly < 50 THEN 0 
                    ELSE (0.85 * (1 - loss_temp)) 
                END AS pr_adjusted
            FROM adjusted_calc
        )
        
        -- Bước 4: Trình bày các Measure cuối cùng phục vụ BI Tool
        SELECT 
            date_id,
            hourly_bucket,
            site_id,
            
            -- Operational Measures
            e_hourly,
            
            -- Efficiency KPIs
            pr_actual,
            pr_adjusted,
            loss_temp,
            
            -- Forecast & Alerts
            (p_stc * (g_hourly / 1000.0) * pr_adjusted) AS e_expected,
            (e_hourly - (p_stc * (g_hourly / 1000.0) * pr_adjusted)) AS delta_baseline,
            
            -- Financial Measures
            (e_hourly * fit_rate) AS estimated_revenue,
            CASE 
                WHEN (p_stc * (g_hourly / 1000.0) * pr_adjusted) > e_hourly 
                THEN ((p_stc * (g_hourly / 1000.0) * pr_adjusted) - e_hourly) * fit_rate
                ELSE 0 
            END AS cost_of_underperformance,
            
            -- Environmental Measures
            (e_hourly * 0.7222) AS co2_avoided_kg,
            ((e_hourly * 0.7222) / 21.77) AS equivalent_trees_planted
            
        FROM pr_adj_calc;
    """)

    try:
        with engine.begin() as conn:
            conn.execute(sql_logic)
        log.info("Đã cập nhật View thành công.")
    except SQLAlchemyError as e:
        log.error(f"Lỗi khi thực thi SQL tạo BI Mart View: {e}")
        raise


# 4. LUỒNG CHẠY CHÍNH
def main() -> None:
    """Luồng thực thi chính của script ETL độc lập."""
    try:
        # Bước 1: Khởi tạo kết nối
        engine = create_db_engine()
        
        # Bước 2: Chạy logic tạo View
        create_bi_mart_hourly_view(engine)
        
    except Exception as e:
        log.critical(f"Tiến trình bị gián đoạn: {e}")
    finally:
        if 'engine' in locals():
            engine.dispose()
            log.info("Đã đóng kết nối và dọn dẹp Connection Pool.")


if __name__ == "__main__":
    main()