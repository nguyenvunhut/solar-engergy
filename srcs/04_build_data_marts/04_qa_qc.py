import logging
import os

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# 1. CẤU HÌNH LOGGING
logging.basicConfig(
    level=logging.WARNING, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

load_dotenv(find_dotenv())

# 2. HÀM TẠO KẾT NỐI
def create_db_engine() -> Engine:
    supabase_user = os.getenv("DB_USER")
    supabase_password = os.getenv("DB_PASSWORD")
    supabase_host = os.getenv("DB_HOST")
    supabase_port = os.getenv("DB_PORT", "5432")
    supabase_db = os.getenv("DB_NAME", "postgres")

    if not all([supabase_user, supabase_password, supabase_host]):
        raise ValueError("Missing database credentials in .env")

    url = (
        f"postgresql+psycopg2://{supabase_user}:{supabase_password}"
        f"@{supabase_host}:{supabase_port}/{supabase_db}"
        f"?sslmode=require"
    )

    try:
        engine = create_engine(url, pool_pre_ping=True)
        return engine
    except SQLAlchemyError as e:
        log.error(f"Lỗi khởi tạo kết nối Database: {e}")
        raise

# 3. HÀM THỰC THI QA/QC
def run_qa_qc_check(engine: Engine) -> None:
    qa_qc_sql = text("""
        WITH dwh_15m AS (
            SELECT 
                date_id,
                site_id,
                ROUND(SUM(energy_generated_kwh)::numeric, 4) AS dwh_total_energy
            FROM datawarehouse.fact_solar_energy_gen
            -- WHERE rolling_outlier_flag = FALSE 
            GROUP BY date_id, site_id
        ),
        bi_mart_hourly AS (
            SELECT 
                date_id,
                site_id,
                ROUND(SUM(e_hourly)::numeric, 4) AS bi_total_energy
            FROM bi_mart.vw_bi_mart_hourly_measures
            GROUP BY date_id, site_id
        )
        SELECT 
            COALESCE(d.date_id, b.date_id) AS date_id,
            COALESCE(d.site_id, b.site_id) AS site_id,
            COALESCE(d.dwh_total_energy, 0) AS dwh_total_energy,
            COALESCE(b.bi_total_energy, 0) AS bi_total_energy,
            ROUND((COALESCE(d.dwh_total_energy, 0) - COALESCE(b.bi_total_energy, 0)), 4) AS variance
        FROM dwh_15m d
        FULL OUTER JOIN bi_mart_hourly b 
            ON d.date_id = b.date_id AND d.site_id = b.site_id
        WHERE ABS(COALESCE(d.dwh_total_energy, 0) - COALESCE(b.bi_total_energy, 0)) > 0.001
        ORDER BY date_id DESC, site_id;
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(qa_qc_sql)
            rows = result.fetchall()
            
            print("\n" + "="*60)
            print("KẾT QUẢ KIỂM TRA ĐỐI CHIẾU DỮ LIỆU (QA/QC)")
            print("="*60)
            
            if not rows:
                print("\nTUYỆT VỜI! Dữ liệu khớp 100%.\n")
            else:
                print(f"\nPHÁT HIỆN LỆCH DỮ LIỆU TẠI {len(rows)} DÒNG!")
                print("Dưới đây là 15 dòng lỗi tiêu biểu:\n")
                
                print(f"{'Date ID':<12} | {'Site ID':<10} | {'DWH Total':<15} | {'BI Mart Total':<15} | {'Variance':<10}")
                print("-" * 80)
                
                # Chỉ in tối đa 15 dòng để không bị trôi Terminal
                for row in rows[:15]:
                    print(f"{row.date_id:<12} | {row.site_id:<10} | {row.dwh_total_energy:<15} | {row.bi_total_energy:<15} | {row.variance:<10}")
                print("-" * 80)
                if len(rows) > 15:
                    print(f"... (Còn {len(rows) - 15} dòng lỗi khác bị ẩn)")
                print("\n")
                
    except SQLAlchemyError as e:
        log.error(f"Lỗi khi chạy script QA/QC: {e}")
        raise

# 4. LUỒNG CHẠY CHÍNH
def main() -> None:
    try:
        engine = create_db_engine()
        run_qa_qc_check(engine)
    except Exception as e:
        log.critical(f"Tiến trình bị gián đoạn: {e}")
    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    main()