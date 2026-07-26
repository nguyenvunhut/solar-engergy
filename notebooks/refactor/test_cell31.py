import pandas as pd
import numpy as np

SITE_COL = "site_id"
TIMESTAMP_COL = "timestamp"
TARGET_COL = "energy_generated_kwh"
VERSION = "v3"
OUTPUT_DIR = "../../data/model/v3/03_features"

try:
    print("Loading train_features")
    train_features = pd.read_parquet(f'{OUTPUT_DIR}/{VERSION}_train_features.parquet')
    print("Loading val_features")
    val_features = pd.read_parquet(f'{OUTPUT_DIR}/{VERSION}_val_features.parquet')

    print("--- KIEM TRA 1: dac trung target deu duoc shift ---")
    chk = train_features.sort_values([SITE_COL, TIMESTAMP_COL]).groupby(SITE_COL).head(200)
    one_site = chk[chk[SITE_COL] == chk[SITE_COL].iloc[0]].reset_index(drop=True)
    ok_lag1 = np.allclose(
        one_site[f'{VERSION}_lag_1'].iloc[1:6].to_numpy(dtype=float),
        one_site[TARGET_COL].iloc[0:5].to_numpy(dtype=float), equal_nan=True)
    print(f"lag_1(t) == target(t-1) tren mau: {'DAT' if ok_lag1 else 'SAI'}")

    print("\n--- KIEM TRA 2: ty le dong co lich su day du ---")
    complete_col = f'{VERSION}_has_complete_history_features'
    for name, df in [('train_alias', train_features), ('val_alias', val_features),
                     ('test', pd.read_parquet(f'{OUTPUT_DIR}/{VERSION}_test_features.parquet', columns=[complete_col]))]:
        r = df[complete_col].fillna(False).mean() * 100
        print(f"- {name:<12}: {r:.2f}% dong co du lich su lien tuc")
except Exception as e:
    import traceback
    traceback.print_exc()

