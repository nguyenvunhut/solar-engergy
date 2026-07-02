import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Kế thừa chuẩn khai báo log của pipeline
log = logging.getLogger("pipeline.bi_view")

# Lấy đường dẫn gốc và đọc file config YAML
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BI_PARAMS_CONFIG = _REPO_ROOT / "config" / "04_machine_learning" / "01_bi_mart_params.yaml"

with _BI_PARAMS_CONFIG.open(encoding="utf-8") as _f:
    _bi_cfg = yaml.safe_load(_f)

# Gán các biến từ file config để thay thế hardcode
_FIT_RATE = _bi_cfg["financial"]["fit_rate_vnd_per_kwh"]
_CO2_FACTOR = _bi_cfg["environmental"]["co2_emission_factor_kg_per_kwh"]
_TREES_FACTOR = _bi_cfg["environmental"]["co2_per_tree_kg"]
_NOMINAL_PR = _bi_cfg["performance"]["nominal_pr"]
_TEMP_COEFF = _bi_cfg["performance"]["temp_coefficient_per_deg"]
_NOCT_FACTOR = _bi_cfg["performance"]["noct_radiation_factor"]
_MIN_RADIATION = _bi_cfg["performance"]["min_radiation_threshold_wm2"]

def build_bi_views(engine) -> None:
    """
    Tạo View nén cấp Giờ và cấp Ngày cho BI Mart trên Supabase.
    Sử dụng tham số từ file cấu hình YAML. Nhận engine từ file điều phối bên ngoài.
    """
    log.info(f"Đang đắp View vào host: {engine.url.host}, database: {engine.url.database}")
    
    # -------------------------------------------------------------------------
    # 1. SQL TẠO VIEW CẤP GIỜ (Đã thay thế tham số YAML)
    # -------------------------------------------------------------------------
    sql_hourly = text(f"""
        CREATE OR REPLACE VIEW bi_mart.vw_bi_mart_hourly_measures_replace AS
        
        WITH hourly_base AS (
            SELECT 
                f.date_id,
                f.hourly_bucket,
                f.site_id,
                f.total_energy AS e_hourly,
                f.shortwave_radiation AS g_hourly,
                f.temperature_c AS t_ambient,
                COALESCE(d.capacity_kw, 0) AS p_stc,
                {_FIT_RATE} AS fit_rate
            FROM bi_mart.fact_solar_performance_hourly f
            LEFT JOIN bi_mart.dim_solar_site d 
                ON f.site_id = d.site_id
        ),
        efficiency_calc AS (
            SELECT 
                *,
                (t_ambient + (g_hourly * {_NOCT_FACTOR})) AS t_cell,
                CASE 
                    WHEN g_hourly < {_MIN_RADIATION} THEN 0 
                    ELSE e_hourly / NULLIF(p_stc * (g_hourly / 1000.0), 0) 
                END AS pr_actual
            FROM hourly_base
        ),
        adjusted_calc AS (
            SELECT 
                *,
                CASE 
                    WHEN t_cell > 25 THEN (t_cell - 25) * {_TEMP_COEFF} 
                    ELSE 0 
                END AS loss_temp
            FROM efficiency_calc
        ),
        pr_adj_calc AS (
            SELECT 
                *,
                CASE 
                    WHEN g_hourly < {_MIN_RADIATION} THEN 0 
                    ELSE ({_NOMINAL_PR} * (1 - loss_temp)) 
                END AS pr_adjusted
            FROM adjusted_calc
        )
        
        SELECT 
            date_id,
            hourly_bucket,
            site_id,
            p_stc,
            
            -- Operational Measures
            e_hourly,
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
            (e_hourly * {_CO2_FACTOR}) AS co2_avoided_kg,
            ((e_hourly * {_CO2_FACTOR}) / {_TREES_FACTOR}) AS equivalent_trees_planted
            
        FROM pr_adj_calc;
    """)

    # -------------------------------------------------------------------------
    # 2. SQL TẠO VIEW CẤP NGÀY VÀ TÍCH LŨY
    # -------------------------------------------------------------------------
    sql_daily = text("""
        CREATE OR REPLACE VIEW bi_mart.vw_bi_mart_daily_kpis_replace AS
        
        WITH daily_base AS (
            SELECT 
                to_date(date_id::text, 'YYYYMMDD') AS report_date,
                site_id,
                MAX(p_stc) AS p_stc,
                SUM(e_hourly) AS e_daily,
                SUM(e_expected) AS e_target_daily,
                SUM(estimated_revenue) AS daily_revenue,
                SUM(co2_avoided_kg) AS daily_co2_avoided
            FROM bi_mart.vw_bi_mart_hourly_measures_replace
            GROUP BY to_date(date_id::text, 'YYYYMMDD'), site_id
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
    """)

    # -------------------------------------------------------------------------
    # 3. THỰC THI CHUỖI LỆNH TRONG 1 TRANSACTION
    # -------------------------------------------------------------------------
    try:
        with engine.begin() as conn:
            conn.execute(sql_hourly)
            log.info("Đã cập nhật thành công: vw_bi_mart_hourly_measures_replace")
            
            conn.execute(sql_daily)
            log.info("Đã cập nhật thành công: vw_bi_mart_daily_kpis_replace")
            
    except Exception as e:
        log.error(f"Lỗi khi thực thi SQL tạo BI Mart View: {e}")
        raise


def build_bi_view(engine) -> None:
    """Backward-compatible alias for older pipeline calls."""
    build_bi_views(engine)
