import logging
from pathlib import Path
from sqlalchemy import text
import yaml

log = logging.getLogger("pipeline.bi_view")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BI_PARAMS_CONFIG = _REPO_ROOT / "config" / "04_machine_learning" / "01_bi_mart_params.yaml"

with _BI_PARAMS_CONFIG.open() as _f:
    _bi_cfg = yaml.safe_load(_f)

_FIT_RATE = _bi_cfg["financial"]["fit_rate_vnd_per_kwh"]
_CO2_FACTOR = _bi_cfg["environmental"]["co2_emission_factor_kg_per_kwh"]
_TREES_FACTOR = _bi_cfg["environmental"]["co2_per_tree_kg"]
_NOMINAL_PR = _bi_cfg["performance"]["nominal_pr"]
_TEMP_COEFF = _bi_cfg["performance"]["temp_coefficient_per_deg"]
_NOCT_FACTOR = _bi_cfg["performance"]["noct_radiation_factor"]
_MIN_RADIATION = _bi_cfg["performance"]["min_radiation_threshold_wm2"]

def build_bi_view(engine) -> None:
    """
    Tạo View nén cấp Giờ cho BI Mart trên Supabase.
    Sử dụng tham số từ file cấu hình YAML.
    """
    log.info(f"Đang đắp View vào host: {engine.url.host}, database: {engine.url.database}")
    sql_logic = text(f"""
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
                COALESCE(d.capacity_kw, 0) AS p_stc,
                {_FIT_RATE} AS fit_rate
            FROM bi_mart.fact_solar_performance_hourly f
            LEFT JOIN bi_mart.dim_solar_site d 
                ON f.site_id = d.site_id
        ),
        
        -- Bước 2: Tính toán các chỉ số vật lý trung gian & PR thực tế
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
        
        -- Bước 3: Tính toán hệ số sụt giảm do quá nhiệt
        adjusted_calc AS (
            SELECT 
                *,
                CASE 
                    WHEN t_cell > 25 THEN (t_cell - 25) * {_TEMP_COEFF} 
                    ELSE 0 
                END AS loss_temp
            FROM efficiency_calc
        ),
        
        -- BƯỚC 3.5: Tính chuẩn PR Adjusted
        pr_adj_calc AS (
            SELECT 
                *,
                CASE 
                    WHEN g_hourly < {_MIN_RADIATION} THEN 0 
                    ELSE ({_NOMINAL_PR} * (1 - loss_temp)) 
                END AS pr_adjusted
            FROM adjusted_calc
        )
        
        -- Bước 4: Trình bày các Measure cuối cùng phục vụ BI Tool
        SELECT 
            date_id,
            hourly_bucket,
            site_id,
            
            e_hourly,
            pr_actual,
            pr_adjusted,
            loss_temp,
            
            (p_stc * (g_hourly / 1000.0) * pr_adjusted) AS e_expected,
            (e_hourly - (p_stc * (g_hourly / 1000.0) * pr_adjusted)) AS delta_baseline,
            
            (e_hourly * fit_rate) AS estimated_revenue,
            CASE 
                WHEN (p_stc * (g_hourly / 1000.0) * pr_adjusted) > e_hourly 
                THEN ((p_stc * (g_hourly / 1000.0) * pr_adjusted) - e_hourly) * fit_rate
                ELSE 0 
            END AS cost_of_underperformance,
            
            (e_hourly * {_CO2_FACTOR}) AS co2_avoided_kg,
            ((e_hourly * {_CO2_FACTOR}) / {_TREES_FACTOR}) AS equivalent_trees_planted
            
        FROM pr_adj_calc;
    """)

    try:
        with engine.begin() as conn:
            conn.execute(sql_logic)
        log.info("Đã tạo BI Mart View thành công.")
    except Exception as e:
        log.error(f"Lỗi khi thực thi SQL tạo BI Mart View: {e}")
        raise
