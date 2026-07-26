import numpy as np
import pandas as pd

def build_time_features(df: pd.DataFrame, timestamp_col: str = 'timestamp') -> pd.DataFrame:
    '''
    Phần A: Tạo các đặc trưng thời gian an toàn (Cyclical & Calendar)
    Không gây rò rỉ dữ liệu.
    '''
    df = df.copy()
    ts = pd.to_datetime(df[timestamp_col])
    
    # 1. Minute of day & Hour Cyclical Encoding
    minute_of_day = ts.dt.hour * 60 + ts.dt.minute
    df['hour_sin'] = np.sin(2 * np.pi * minute_of_day / 1440.0)
    df['hour_cos'] = np.cos(2 * np.pi * minute_of_day / 1440.0)
    
    # 2. Day of Year Cyclical Encoding
    doy = ts.dt.dayofyear
    df['doy_sin'] = np.sin(2 * np.pi * doy / 365.25)
    df['doy_cos'] = np.cos(2 * np.pi * doy / 365.25)
    
    # 3. Calendar Features
    df['day_of_week'] = ts.dt.dayofweek
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # 4. Season Mapping (Lịch Nam bán cầu / Nam Việt Nam)
    month = ts.dt.month
    season_map = {
        12: 'Summer', 1: 'Summer', 2: 'Summer',
        3: 'Autumn', 4: 'Autumn', 5: 'Autumn',
        6: 'Winter', 7: 'Winter', 8: 'Winter',
        9: 'Spring', 10: 'Spring', 11: 'Spring'
    }
    df['season'] = month.map(season_map)
    season_enc_map = {'Spring': 0, 'Summer': 1, 'Autumn': 2, 'Winter': 3}
    df['season_encoded'] = df['season'].map(season_enc_map)
    
    return df

def build_lag_rolling_features(
    df: pd.DataFrame, 
    group_col: str = 'site_id', 
    target_col: str = 'energy_generated_kwh',
    freq_step_per_hour: int = 4 # 15 phút/bước -> 4 bước/giờ
) -> pd.DataFrame:
    '''
    Phần B: Tạo đặc trưng Lag & Rolling bằng Vectorized Operations.
    Đảm bảo SHIFT(1) trước khi Rolling để tránh Data Leakage.
    '''
    df = df.copy()
    # Sắp xếp đúng thứ tự thời gian theo từng site
    df = df.sort_values(by=[group_col, 'timestamp']).reset_index(drop=True)
    
    # Tối ưu Vectorization bằng groupby + shift
    grouped_target = df.groupby(group_col)[target_col]
    
    # 1. Lag Features
    df['lag_1'] = grouped_target.shift(1)
    df['lag_4'] = grouped_target.shift(4)
    df['lag_24'] = grouped_target.shift(1 * 24 * freq_step_per_hour)
    
    # 2. Rolling Features (Luôn shift(1) trước khi rolling)
    shifted_target = grouped_target.shift(1)
    
    # Rolling 1 hour
    window_1h = 1 * freq_step_per_hour
    df['rolling_mean_1h'] = shifted_target.groupby(df[group_col]).transform(
        lambda x: x.rolling(window=window_1h, min_periods=1).mean()
    )
    df['rolling_std_1h'] = shifted_target.groupby(df[group_col]).transform(
        lambda x: x.rolling(window=window_1h, min_periods=1).std()
    )
    
    # Rolling 3 hours
    window_3h = 3 * freq_step_per_hour
    df['rolling_mean_3h'] = shifted_target.groupby(df[group_col]).transform(
        lambda x: x.rolling(window=window_3h, min_periods=1).mean()
    )
    
    return df
