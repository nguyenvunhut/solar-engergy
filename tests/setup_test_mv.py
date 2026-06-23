import os
import sys
import psycopg2
from dotenv import load_dotenv

# Hỗ trợ hiển thị tiếng Việt trên Windows Console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

def setup_test_environment():
    print("==== BAT DAU TAO BANG TEST VA MATERIALIZED VIEW ====")
    
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    if not all([db_host, db_name, db_user, db_password]):
        print("Loi: Thieu thong tin cau hinh ket noi Database (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD).")
        sys.exit(1)

    try:
        print(f"Dang ket noi Database: {db_host}...")
        conn = psycopg2.connect(
            host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_password
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("1. Khoi tao Schema va Table Staging...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS staging;")
        cursor.execute("""
            DROP TABLE IF EXISTS staging.test_daily_solar_data CASCADE;
            CREATE TABLE staging.test_daily_solar_data (
                report_date DATE,
                site_id INT,
                p_stc NUMERIC,
                e_daily NUMERIC,
                e_target_daily NUMERIC,
                daily_revenue NUMERIC,
                daily_co2_avoided NUMERIC
            );
        """)

        print("2. Load Sample Data vao Staging...")
        # Insert dữ liệu mẫu kéo dài trong vài ngày để test các hàm Window (WTD, MTD, YTD)
        sample_data = """
            INSERT INTO staging.test_daily_solar_data (report_date, site_id, p_stc, e_daily, e_target_daily, daily_revenue, daily_co2_avoided)
            VALUES 
            ('2024-01-01', 1, 100, 450, 480, 872100, 325.5),
            ('2024-01-02', 1, 100, 500, 480, 969000, 361.1),
            ('2024-01-03', 1, 100, 420, 480, 813960, 303.3),
            ('2024-01-01', 2, 200, 950, 1000, 1841100, 686.0),
            ('2024-01-02', 2, 200, 1050, 1000, 2034900, 758.3);
        """
        cursor.execute(sample_data)

        print("3. Khoi tao Schema BI Mart va Materialized View...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS bi_mart;")
        cursor.execute("DROP MATERIALIZED VIEW IF EXISTS bi_mart.mv_example_view CASCADE;")
        
        # Tạo MV lấy dữ liệu từ staging, có cấu trúc và logic giống hệt daily kpi
        mv_sql = """
        CREATE MATERIALIZED VIEW bi_mart.mv_example_view AS
        WITH daily_base AS (
            SELECT 
                report_date,
                site_id,
                p_stc,
                e_daily,
                e_target_daily,
                daily_revenue,
                daily_co2_avoided
            FROM staging.test_daily_solar_data
        ),
        kpi_calc AS (
            SELECT 
                *,
                -- KPI 1: Capacity Factor (CF)
                CASE 
                    WHEN p_stc > 0 THEN e_daily / (p_stc * 24)
                    ELSE 0
                END AS capacity_factor,
                
                -- KPI 2: Yield Fulfillment Ratio
                CASE 
                    WHEN e_target_daily > 0 THEN (e_daily / e_target_daily)
                    ELSE 0
                END AS yield_fulfillment_ratio,
                
                -- KPI 3: Time-Intelligence (WTD, MTD, YTD)
                SUM(e_daily) OVER (
                    PARTITION BY site_id, DATE_TRUNC('week', report_date) 
                    ORDER BY report_date
                ) AS wtd_energy,
                
                SUM(e_daily) OVER (
                    PARTITION BY site_id, DATE_TRUNC('month', report_date) 
                    ORDER BY report_date
                ) AS mtd_energy,
                
                SUM(e_daily) OVER (
                    PARTITION BY site_id, DATE_TRUNC('year', report_date) 
                    ORDER BY report_date
                ) AS ytd_energy
            FROM daily_base
        )
        SELECT * FROM kpi_calc;
        """
        cursor.execute(mv_sql)

        print("Thanh cong! Da tao bang staging, insert data sample va build bi_mart.mv_example_view xong.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Loi trong qua trinh tao: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_test_environment()
