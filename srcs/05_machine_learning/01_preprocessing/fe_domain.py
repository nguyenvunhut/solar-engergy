import numpy as np
import pandas as pd

def build_domain_aggregate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo các đặc trưng tổng hợp dựa trên Domain Knowledge (Vật lý Solar & Metadata).
    Xử lý tinh tế các trường hợp Missing Data (Giữ nguyên NaN thay vì fillna(0) bừa bãi)
    để không làm sai lệch ý nghĩa vật lý.
    
    Args:
        df: DataFrame chứa dữ liệu tiền xử lý (v2).
    Returns:
        DataFrame đã được bổ sung các đặc trưng tổng hợp.
    """
    df_out = df.copy()
    
    # 1. Capacity per Panel (Công suất trung bình/tấm - Metadata Site)
    if 'capacity_kw' in df_out.columns and 'number_of_panels' in df_out.columns:
        # Nếu mẫu số = 0, chuyển thành NaN để kết quả phép chia ra NaN (bảo toàn data)
        # Không dùng fillna(0) để giữ nguyên trạng thái thiếu thông tin metadata
        safe_panels = df_out['number_of_panels'].replace(0, np.nan)
        df_out['capacity_per_panel'] = df_out['capacity_kw'] / safe_panels
        
    # 2. Temperature x Radiation Interaction (Tương tác Nhiệt - Bức xạ)
    if 'temperature_c' in df_out.columns and 'shortwave_radiation' in df_out.columns:
        df_out['temp_x_radiation'] = df_out['temperature_c'] * df_out['shortwave_radiation']
        
    # 3. Thermal Loss Factor (Hệ số tổn thất do nhiệt độ vượt chuẩn STC 25°C)
    if 'temperature_c' in df_out.columns:
        # Giả sử hệ số suy giảm là 0.4% / độ C khi trên ngưỡng tiêu chuẩn
        loss_factor = 1 - 0.004 * (df_out['temperature_c'] - 25)
        # Giới hạn ngưỡng vật lý (VD: nhiệt độ cực đoan), bỏ qua NaN
        df_out['thermal_loss_factor'] = loss_factor.clip(lower=0.5, upper=1.2)
        
    # 4. Inverter Loading Ratio Proxy (Tỷ lệ khai thác công suất trạm)
    if 'energy_generated_kwh' in df_out.columns and 'capacity_kw' in df_out.columns:
        safe_capacity = df_out['capacity_kw'].replace(0, np.nan)
        # Tỷ lệ so với công suất thiết kế: (energy * 4) / capacity
        ilr = (df_out['energy_generated_kwh'] * 4) / safe_capacity
        df_out['inverter_loading_ratio_proxy'] = ilr.clip(lower=0, upper=2.0)
        
    # 5. Diffuse Fraction (Tỷ lệ bức xạ khuếch tán)
    if 'diffuse_solar_radiation' in df_out.columns and 'shortwave_radiation' in df_out.columns:
        safe_shortwave = df_out['shortwave_radiation'].replace(0, np.nan)
        fraction = df_out['diffuse_solar_radiation'] / safe_shortwave
        
        # Xử lý đặc thù ban đêm: cả diffuse và shortwave đều = 0
        # Gán 0 hợp lý về mặt vật lý, nhưng không gán 0 nếu dữ liệu bị khuyết (NaN)
        night_mask = (df_out['shortwave_radiation'] == 0) & (df_out['diffuse_solar_radiation'] == 0)
        fraction.loc[night_mask] = 0.0
        
        df_out['diffuse_fraction'] = fraction.clip(lower=0, upper=1.0)
        
    return df_out
