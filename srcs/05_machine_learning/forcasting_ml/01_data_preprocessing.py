"""Buoc 1: Reindex luoi 15 phut, mask outlier, va chia train/val/test theo thoi gian.

TU DONG SINH tu notebooks/refactor/, KHONG sua truc tiep file nay - sua o
notebook goc roi chay lai srcs/00_utils/convert_notebook_to_py.py + gop lai.
"""
from __future__ import annotations


# 1.1 Reindex + mask outlier (tu 01_reindex_mask_outlier.ipynb)
def run_reindex_mask_outlier():

    # # Ticket: Reindex Lưới 15 Phút & Mask Outlier
    # Dự án: Tốt nghiệp - Energy Forecasting - Nhóm thực hiện: The Outliers
    #
    # ## 1. TỔNG QUAN VÀ MỤC TIÊU
    # Notebook này thực hiện hai nhiệm vụ chính trong pipeline ML Forecasting v3:
    #
    # 1. **Reindex lưới thời gian 15 phút**: Tạo lưới timestamp liên tục cho từng site, lấp đầy khoảng trống bằng cascade causal (chỉ dùng dữ liệu quá khứ, không kéo tương lai về).
    # 2. **Mask outlier**: Phân loại các quan sát thành nhóm outlier (`normal`, `gmm_if_consensus`, `physical_over_capacity`, `other_physical_rule`, `multiple_rules`) phục vụ sample weighting.
    #
    # **Input:** `v3_final_cleaned.parquet` + `Solar_Energy_Generation.csv` (provenance)  
    # **Output:** `v3_continuous_grid.parquet`
    #
    # **Nguồn logic tham chiếu Audit:**
    # - `srcs/05_machine_learning/Forcasting_v3/01_build_continuous_grid.py` (`attach_energy_source`, `build_site_grid`, `fill_inserted_energy`)
    # - `srcs/05_machine_learning/Forcasting_v3/forecasting_common.py` (`classify_outlier_group`, `add_calendar_columns`, `add_daylight_columns`)
    # - Notebooks cũ tham khảo: `notebooks/EDA/2026_06_27EDA_BONUS_OUTLINER_NGOTANDAT.ipynb` (logic reindex date_range), `notebooks/preprocess/Fill_null_imputation.ipynb` (logic causal ffill weather)
    #
    # **Ràng buộc logic:**
    # - Weather chỉ `ffill()` causal. **Tuyệt đối không** `bfill()`.
    # - Metadata tĩnh thiếu → giữ nguyên NaN, không bịa, không ffill.
    # - Cascade điền target: `night_zero` / `causal_day_persistence` / `causal_week_persistence` / `causal_profile_median` / `fallback_zero` / `machine_failure_zero`.
    # - Gap ≥ 24h → `machine_failure_zero` + `exclude_from_training = True`.

    # ## 2. Import thư viện và khai báo tham số
    # *Nguồn tham chiếu logic:* N/A (Setup chung)

    # ── Gioi han thread: may i5-12450HX co 8 core / 12 thread (4 P-core + 4 E-core).
    # Dung het 12 thread lam cac thread tranh nhau va CHAM HON. Dat 6 de bam P-core,
    # con lai de cho Jupyter va he dieu hanh. Phai set TRUOC khi numpy nap moi co tac dung.
    import os

    for _bien in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                  'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ.setdefault(_bien, '6')

    import gc
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import warnings
    from collections import defaultdict

    warnings.filterwarnings('ignore')
    sns.set_theme(style="whitegrid")

    # ── Tham số pipeline (hardcode, không đọc YAML) ──
    FREQ_MINUTES = 15
    MAJOR_GAP_HOURS = 24
    MAX_LAG_STEPS = 672

    # ── Tên cột ──
    SITE_COL = "site_id"
    TIMESTAMP_COL = "timestamp"
    TARGET_COL = "energy_generated_kwh"
    RAW_SITE = "SiteKey"
    RAW_TS = "Timestamp"
    RAW_TARGET = "SolarGeneration"

    # ── Đường dẫn (tương đối) ──
    # Doc ban copy rieng _py cua input goc (giong het v3_final_cleaned.parquet,
    # xem srcs/05_machine_learning/forcasting_ml/README hoac lich su tao file) -
    # de pipeline .py khong bao gio dung chung file voi notebook, tranh rui ro ghi de.
    INPUT_PATH = "../../../data/mlmart_base/v3_final_cleaned_py.parquet"
    RAW_SOLAR_PATH = "../../../data/raw/Solar_Energy_Generation.csv"
    OUTPUT_PATH = "../../../data/model/v3/01_reindex_py/v3_continuous_grid.parquet"

    print("Đã import thư viện và khai báo tham số.")
    print(f"- Tần suất lưới: {FREQ_MINUTES} phút")
    print(f"- Ngưỡng gap lớn: {MAJOR_GAP_HOURS} giờ ({MAJOR_GAP_HOURS * 60 // FREQ_MINUTES} slots)")
    print(f"- Max lag steps: {MAX_LAG_STEPS}")


    # ## 3. Đọc dữ liệu v3_final_cleaned
    # *Nguồn tham chiếu logic:* `srcs/05_machine_learning/Forcasting_v3/01_build_continuous_grid.py` -> hàm `attach_energy_source()`  
    # Đọc dữ liệu ML mart chính và file raw solar để xác định provenance (`measured` / `etl_imputed`).

    # Đọc dữ liệu ML mart chính
    df = pd.read_parquet(INPUT_PATH)
    df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL], errors="coerce")
    df = df.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)

    # Đọc raw solar CSV để xác định provenance
    raw_solar = pd.read_csv(RAW_SOLAR_PATH, usecols=[RAW_SITE, RAW_TS, RAW_TARGET])
    raw_solar[RAW_TS] = pd.to_datetime(raw_solar[RAW_TS], errors="coerce")
    raw_key = raw_solar.rename(columns={
        RAW_SITE: SITE_COL, RAW_TS: TIMESTAMP_COL, RAW_TARGET: "_raw_gen"
    }).drop_duplicates(subset=[SITE_COL, TIMESTAMP_COL])

    # Merge để gán energy_source cho dữ liệu gốc
    df = df.merge(raw_key, on=[SITE_COL, TIMESTAMP_COL], how="left")
    df["energy_source"] = np.where(df["_raw_gen"].notna(), "measured", "etl_imputed")
    df = df.drop(columns=["_raw_gen"])

    # Khởi tạo cột provenance
    df["timestamp_was_inserted"] = False
    df["exclude_from_training"] = False
    df["exclude_reason"] = ""
    df["training_quality_reason"] = ""
    df["source_gap_id"] = pd.NA
    df["after_source_gap_steps_remaining"] = 0
    if "gmm_if_outlier_flag" not in df.columns:
        df["gmm_if_outlier_flag"] = False
    if "gmm_if_outlier_reason" not in df.columns:
        df["gmm_if_outlier_reason"] = ""

    print(f"Đang đọc dữ liệu từ: {INPUT_PATH}")
    print(f"Tổng số dòng: {len(df)}")
    print(f"Số site: {df[SITE_COL].nunique()}")
    print(f"Khoảng thời gian: {df[TIMESTAMP_COL].min()} -> {df[TIMESTAMP_COL].max()}")
    print(f"\n--- PHÂN BỐ ENERGY_SOURCE BAN ĐẦU ---")
    print(df["energy_source"].value_counts().to_string())
    print("Sample Data:")
    display(df.head(3))

    # ## 3.1. Xác nhận lại join thời tiết đúng causal (lưới an toàn)
    #
    # `data/mlmart_base/v3_preprocessing.parquet` đã được sửa join causal trực tiếp (xác nhận lại
    # 2026-07-30: 0% dòng dùng thời tiết tương lai, `hour` khớp timestamp 100%, chỉ 0,068% thiếu do
    # khoảng trống thật). `notebooks/preprocess/00_fill_null_imputation.ipynb` đọc file này, sinh ra
    # `v3_final_cleaned.parquet` mới — **không tự join lại thời tiết**, chỉ dọn `weather_timestamp` lỗi
    # và điền null, nên giá trị causal được giữ nguyên đi tiếp.
    #
    # Bước dưới đây chạy lại phép join causal 1 lần nữa **như lưới an toàn**: nếu dữ liệu đã đúng thì
    # không đổi gì (idempotent), nếu còn sai ở đâu đó thì tự sửa. Không được bỏ bước này, vì nó cũng in
    # ra bằng chứng kiểm tra được (số dòng đổi giá trị, delta phút) để đối chiếu.
    #
    # **Bắt buộc chạy lại `00_fill_null_imputation.ipynb` trước `01` này**, để `v3_final_cleaned.parquet`
    # là bản mới nhất sinh từ `v3_preprocessing.parquet` đã hotfix.

    # ── Join lại thời tiết theo đúng quy tắc causal (Y HỆT code 04_realign_mlmart_weather.py) ──
    _tt = [c for c in COT_THOI_TIET if c in df.columns] if 'COT_THOI_TIET' in locals() else [c for c in WEATHER_COLUMNS if c in df.columns]
    _bang_tt = df[[SITE_COL, 'weather_timestamp'] + _tt].dropna(subset=['weather_timestamp']).copy()
    _bang_tt['_weather_hour'] = pd.to_datetime(_bang_tt['weather_timestamp']).dt.floor('h')
    _bang_tt = _bang_tt.drop_duplicates([SITE_COL, '_weather_hour']).set_index([SITE_COL, '_weather_hour'])

    _keys = pd.MultiIndex.from_arrays(
        [df[SITE_COL].to_numpy(), pd.to_datetime(df[TIMESTAMP_COL]).dt.floor('h').to_numpy()],
        names=[SITE_COL, '_weather_hour']
    )
    _aligned = _bang_tt.reindex(_keys).reset_index(drop=True)
    for _col in _tt:
        df[_col] = _aligned[_col].values
    df['weather_timestamp'] = pd.to_datetime(df[TIMESTAMP_COL]).dt.floor('h')

    print("--- TRUOC KHI SUA ---")
    print(f"Dong dung thoi tiet TUONG LAI: {_leak_truoc:,}/{len(df):,} ({_leak_truoc / len(df) * 100:.2f}%)")
    print("Phan bo (weather_timestamp - timestamp) theo phut:")
    print(_delta_truoc.value_counts().sort_index().to_string())

    # Bang tra thoi tiet: moi (site, nhan gio) mot ban ghi, lay tu chinh du lieu dang co
    # ── Join lại thời tiết theo đúng quy tắc causal (Y HỆT code 04_realign_mlmart_weather.py) ──
    _tt = [c for c in COT_THOI_TIET if c in df.columns] if 'COT_THOI_TIET' in locals() else [c for c in WEATHER_COLUMNS if c in df.columns]
    _bang_tt = df[[SITE_COL, 'weather_timestamp'] + _tt].dropna(subset=['weather_timestamp']).copy()
    _bang_tt['_weather_hour'] = pd.to_datetime(_bang_tt['weather_timestamp']).dt.floor('h')
    _bang_tt = _bang_tt.drop_duplicates([SITE_COL, '_weather_hour']).set_index([SITE_COL, '_weather_hour'])

    _keys = pd.MultiIndex.from_arrays(
        [df[SITE_COL].to_numpy(), pd.to_datetime(df[TIMESTAMP_COL]).dt.floor('h').to_numpy()],
        names=[SITE_COL, '_weather_hour']
    )
    _aligned = _bang_tt.reindex(_keys).reset_index(drop=True)
    for _col in _tt:
        df[_col] = _aligned[_col].values
    df['weather_timestamp'] = pd.to_datetime(df[TIMESTAMP_COL]).dt.floor('h')

    print(f"\nBang tra thoi tiet: {len(_bang_tt):,} ban ghi (site x nhan gio)")

    # Nhan gio HOP LE cho moi dong = floor ve dau gio (thoi tiet do da co san tai thoi diem do)
    # ── Join lại thời tiết theo đúng quy tắc causal (Y HỆT code 04_realign_mlmart_weather.py) ──
    _tt = [c for c in COT_THOI_TIET if c in df.columns] if 'COT_THOI_TIET' in locals() else [c for c in WEATHER_COLUMNS if c in df.columns]
    _bang_tt = df[[SITE_COL, 'weather_timestamp'] + _tt].dropna(subset=['weather_timestamp']).copy()
    _bang_tt['_weather_hour'] = pd.to_datetime(_bang_tt['weather_timestamp']).dt.floor('h')
    _bang_tt = _bang_tt.drop_duplicates([SITE_COL, '_weather_hour']).set_index([SITE_COL, '_weather_hour'])

    _keys = pd.MultiIndex.from_arrays(
        [df[SITE_COL].to_numpy(), pd.to_datetime(df[TIMESTAMP_COL]).dt.floor('h').to_numpy()],
        names=[SITE_COL, '_weather_hour']
    )
    _aligned = _bang_tt.reindex(_keys).reset_index(drop=True)
    for _col in _tt:
        df[_col] = _aligned[_col].values
    df['weather_timestamp'] = pd.to_datetime(df[TIMESTAMP_COL]).dt.floor('h')

    print(f"\n--- SAU KHI SUA ---")
    print(f"Dong join duoc thoi tiet: {int(_khop.sum()):,}/{len(df):,} ({_khop.mean() * 100:.2f}%)")
    # ── Join lại thời tiết theo đúng quy tắc causal (Y HỆT code 04_realign_mlmart_weather.py) ──
    _tt = [c for c in COT_THOI_TIET if c in df.columns] if 'COT_THOI_TIET' in locals() else [c for c in WEATHER_COLUMNS if c in df.columns]
    _bang_tt = df[[SITE_COL, 'weather_timestamp'] + _tt].dropna(subset=['weather_timestamp']).copy()
    _bang_tt['_weather_hour'] = pd.to_datetime(_bang_tt['weather_timestamp']).dt.floor('h')
    _bang_tt = _bang_tt.drop_duplicates([SITE_COL, '_weather_hour']).set_index([SITE_COL, '_weather_hour'])

    _keys = pd.MultiIndex.from_arrays(
        [df[SITE_COL].to_numpy(), pd.to_datetime(df[TIMESTAMP_COL]).dt.floor('h').to_numpy()],
        names=[SITE_COL, '_weather_hour']
    )
    _aligned = _bang_tt.reindex(_keys).reset_index(drop=True)
    for _col in _tt:
        df[_col] = _aligned[_col].values
    df['weather_timestamp'] = pd.to_datetime(df[TIMESTAMP_COL]).dt.floor('h')

    print(f"Dong dung thoi tiet TUONG LAI: {int((_delta_sau > 0).sum()):,} (phai bang 0)")
    print(f"Phan bo delta moi (phut): {sorted(_delta_sau.dropna().unique().tolist())}")

    _bang_doi = []
    for c in _tt:
        if pd.api.types.is_numeric_dtype(_truoc[c]):
            _kh = ~np.isclose(_truoc[c].to_numpy(dtype='float64'),
                              df[c].to_numpy(dtype='float64'), equal_nan=True)
        else:
            _kh = (_truoc[c].astype(str).to_numpy() != df[c].astype(str).to_numpy())
        _bang_doi.append({'cot': c, 'so_dong_doi': int(_kh.sum()),
                          'ty_le_%': round(_kh.mean() * 100, 1)})
    print("\nSo dong thuc su doi gia tri sau khi sua join:")
    display(pd.DataFrame(_bang_doi).sort_values('so_dong_doi', ascending=False))

    # Cap nhat lai weather_timestamp cho khop, roi bo cot tam
    # ── Join lại thời tiết theo đúng quy tắc causal (Y HỆT code 04_realign_mlmart_weather.py) ──
    _tt = [c for c in COT_THOI_TIET if c in df.columns] if 'COT_THOI_TIET' in locals() else [c for c in WEATHER_COLUMNS if c in df.columns]
    _bang_tt = df[[SITE_COL, 'weather_timestamp'] + _tt].dropna(subset=['weather_timestamp']).copy()
    _bang_tt['_weather_hour'] = pd.to_datetime(_bang_tt['weather_timestamp']).dt.floor('h')
    _bang_tt = _bang_tt.drop_duplicates([SITE_COL, '_weather_hour']).set_index([SITE_COL, '_weather_hour'])

    _keys = pd.MultiIndex.from_arrays(
        [df[SITE_COL].to_numpy(), pd.to_datetime(df[TIMESTAMP_COL]).dt.floor('h').to_numpy()],
        names=[SITE_COL, '_weather_hour']
    )
    _aligned = _bang_tt.reindex(_keys).reset_index(drop=True)
    for _col in _tt:
        df[_col] = _aligned[_col].values
    df['weather_timestamp'] = pd.to_datetime(df[TIMESTAMP_COL]).dt.floor('h')

    assert int((_delta_sau > 0).sum()) == 0, "Van con dong dung thoi tiet tuong lai"
    print("\nDa sua join thoi tiet ve dung causal. Khong con dong nao dung du lieu tuong lai.")

    # ## 4. Reindex lưới 15 phút cho từng site
    # *Nguồn tham chiếu logic:* `srcs/05_machine_learning/Forcasting_v3/01_build_continuous_grid.py` -> hàm `build_site_grid()` & `forecasting_common.py` -> `add_calendar_columns()`  
    # *Notebook tham chiếu cũ:* `notebooks/EDA/2026_06_27EDA_BONUS_OUTLINER_NGOTANDAT.ipynb` (kỹ thuật `pd.date_range`)  
    # Tạo lưới timestamp liên tục 15 phút từ `min` đến `max` của mỗi site. Đồng thời thêm các cột lịch (`quarter_hour`, `season_model`) cần cho cascade ở bước 7.

    # Reindex lưới 15 phút liên tục cho từng site
    freq = f"{FREQ_MINUTES}min"
    parts = []

    for site_id, site_df in df.groupby(SITE_COL, observed=True, sort=True):
        ts_min = site_df[TIMESTAMP_COL].min()
        ts_max = site_df[TIMESTAMP_COL].max()
        full_idx = pd.date_range(ts_min, ts_max, freq=freq)
        grid = pd.DataFrame({TIMESTAMP_COL: full_idx})
        merged = grid.merge(site_df, on=TIMESTAMP_COL, how="left", sort=True)
        merged[SITE_COL] = merged[SITE_COL].fillna(site_id)
        merged["timestamp_was_inserted"] = merged["timestamp_was_inserted"].fillna(True).astype(bool)
        parts.append(merged)

    df = pd.concat(parts, ignore_index=True)
    df = df.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)

    # Thêm cột lịch (calendar columns)
    ts = pd.to_datetime(df[TIMESTAMP_COL])
    df["minute_of_day"] = ts.dt.hour * 60 + ts.dt.minute
    df["quarter_hour"] = df["minute_of_day"] // 15
    df["hour_of_day"] = ts.dt.hour
    df["day_of_week_model"] = ts.dt.dayofweek
    df["month_model"] = ts.dt.month
    df["day_of_year"] = ts.dt.dayofyear

    _SEASON = {12: "summer", 1: "summer", 2: "summer",
               3: "autumn", 4: "autumn", 5: "autumn",
               6: "winter", 7: "winter", 8: "winter",
               9: "spring", 10: "spring", 11: "spring"}
    df["season_model"] = ts.dt.month.map(_SEASON)

    n_inserted = df["timestamp_was_inserted"].sum()
    print(f"Đã reindex lưới {FREQ_MINUTES} phút cho {df[SITE_COL].nunique()} site.")
    print(f"Tổng số dòng sau reindex: {len(df)}")
    print(f"- Dòng gốc: {len(df) - n_inserted}")
    print(f"- Dòng inserted: {n_inserted}")
    print("Sample Data:")
    display(df[[SITE_COL, TIMESTAMP_COL, "timestamp_was_inserted", "quarter_hour", "season_model"]].head(5))

    # ## 5. Đánh dấu timestamp_was_inserted
    # *Nguồn tham chiếu logic:* `srcs/05_machine_learning/Forcasting_v3/01_build_continuous_grid.py` -> đoạn gán `provenance_defaults` trong `build_site_grid()`  
    # Gán giá trị mặc định cho các cột provenance trên dòng inserted và tạo cờ `weather_is_observed`.

    # Gán default provenance cho dòng inserted
    df["energy_source"] = df["energy_source"].fillna("")
    df["exclude_from_training"] = df["exclude_from_training"].fillna(False).astype(bool)
    df["exclude_reason"] = df["exclude_reason"].fillna("")
    df["training_quality_reason"] = df["training_quality_reason"].fillna("")
    df["after_source_gap_steps_remaining"] = (
        df["after_source_gap_steps_remaining"].fillna(0).astype(int)
    )
    df["gmm_if_outlier_flag"] = df["gmm_if_outlier_flag"].fillna(False).astype(bool)
    df["gmm_if_outlier_reason"] = df["gmm_if_outlier_reason"].fillna("")

    # Cờ weather_is_observed
    mask_ins = df["timestamp_was_inserted"]
    weather_check = [c for c in [
        "shortwave_radiation", "temperature_c", "cloud_cover_total",
        "wind_speed", "precipitation_mm"
    ] if c in df.columns]
    if weather_check:
        df["weather_is_observed"] = (~mask_ins) & df[weather_check].notna().any(axis=1)
    else:
        df["weather_is_observed"] = False

    print(f"Đã gán provenance defaults cho {mask_ins.sum()} dòng inserted.")
    print(f"Weather observed: {df['weather_is_observed'].sum()} / {len(df)} dòng")
    print("Sample Data inserted:")
    display(df[mask_ins].head(3))

    # ## 6. Forward fill dữ liệu thời tiết
    # *Nguồn tham chiếu logic:* `srcs/05_machine_learning/Forcasting_v3/01_build_continuous_grid.py` -> đoạn `weather_cols ffill` trong `build_site_grid()`  
    # *Notebook tham chiếu cũ:* `notebooks/preprocess/Fill_null_imputation.ipynb`  
    # Chỉ dùng `ffill()` causal (kéo quá khứ sang hiện tại), per-site. **Tuyệt đối không** `bfill()`.

    # Danh sách cột thời tiết cần forward-fill
    WEATHER_COLS = [c for c in [
        "weather_is_day", "shortwave_radiation", "direct_normal_irradiance",
        "diffuse_solar_radiation", "temperature_c", "cloud_cover_total",
        "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high",
        "wind_speed", "precipitation_mm", "sunshine_duration",
        "weather_code", "weather_condition", "weather_description"
    ] if c in df.columns]

    before_na = df[WEATHER_COLS].isna().sum().sum()

    # ffill per-site (không tràn giữa các site)
    df[WEATHER_COLS] = df.groupby(SITE_COL)[WEATHER_COLS].transform(lambda x: x.ffill())

    after_na = df[WEATHER_COLS].isna().sum().sum()

    print("Forward-fill thời tiết (causal only, per-site):")
    print(f"- Số cột thời tiết: {len(WEATHER_COLS)}")
    print(f"- NaN trước: {before_na}")
    print(f"- NaN sau: {after_na}")
    print(f"- Đã lấp: {before_na - after_na} giá trị")

    # ## 7. Điền target cho các slot mới chèn
    # *Nguồn tham chiếu logic:* `srcs/05_machine_learning/Forcasting_v3/01_build_continuous_grid.py` -> hàm `fill_inserted_energy()`  
    # Cascade causal: `night_zero` → `causal_day_persistence` (hôm qua cùng giờ) → `causal_week_persistence` (tuần trước) → `causal_profile_median` → `fallback_zero`. Gap ≥ 24h → `machine_failure_zero` + loại khỏi training.

    # Xác định is_daylight từ weather_is_day (đã ffill ở bước 6)
    if "weather_is_day" in df.columns:
        df["is_daylight"] = pd.to_numeric(df["weather_is_day"], errors="coerce").eq(1).fillna(False)
    else:
        m = df[TIMESTAMP_COL].dt.hour * 60 + df[TIMESTAMP_COL].dt.minute
        df["is_daylight"] = ~((m >= 1110) | (m < 330))

    major_slots = int(MAJOR_GAP_HOURS * 60 / FREQ_MINUTES)  # 96 slots = 24h

    def fill_inserted_energy_site(site_df):
        """Điền năng lượng cho các slot mới chèn trong 1 site bằng cascade causal."""
        out = site_df.sort_values(TIMESTAMP_COL).reset_index(drop=True).copy()
        ins = out["timestamp_was_inserted"].astype(bool)
        run_grp = ins.ne(ins.shift(fill_value=False)).cumsum()
        run_len = ins.groupby(run_grp).transform("sum").where(ins, 0).astype(int)
        out["source_gap_id"] = out["source_gap_id"].astype("object")

        measured_vals = {}          # {timestamp: giá trị đo thực}
        profile = defaultdict(list) # {(quarter_hour, season): [values]}
        gap_id = 0
        gap_active = False

        for i, row in out.iterrows():
            ts_val = pd.Timestamp(row[TIMESTAMP_COL])
            key = (int(row["quarter_hour"]), str(row["season_model"]))

            if not bool(row["timestamp_was_inserted"]):
                # Dòng gốc: thu thập giá trị measured vào dict
                if row["energy_source"] == "measured" and pd.notna(row[TARGET_COL]):
                    v = float(row[TARGET_COL])
                    measured_vals[ts_val] = v
                    profile[key].append(v)
                if gap_active:
                    end = min(i + MAX_LAG_STEPS, len(out))
                    out.loc[i:end-1, "after_source_gap_steps_remaining"] = np.maximum(
                        out.loc[i:end-1, "after_source_gap_steps_remaining"].astype(int),
                        np.arange(MAX_LAG_STEPS, MAX_LAG_STEPS - (end - i), -1),
                    )
                    gap_active = False
                continue

            # Dòng inserted
            if not gap_active:
                gap_id += 1
                gap_active = True
            out.at[i, "source_gap_id"] = gap_id
            cur_run = int(run_len.iloc[i])
            daylight = bool(row["is_daylight"])

            # (1) Gap lớn ≥ 24h → machine_failure_zero
            if cur_run >= major_slots:
                out.at[i, TARGET_COL] = 0.0
                out.at[i, "energy_source"] = "machine_failure_zero"
                out.at[i, "exclude_from_training"] = True
                out.at[i, "exclude_reason"] = "MACHINE_FAILURE_DATA_GAP"
                out.at[i, "training_quality_reason"] = "SOURCE_GAP_MAJOR_OUTAGE+MACHINE_FAILURE_DATA_GAP"
                continue

            # (2) Ban đêm → night_zero
            if not daylight:
                out.at[i, TARGET_COL] = 0.0
                out.at[i, "energy_source"] = "night_zero"
                out.at[i, "training_quality_reason"] = "SOURCE_GAP_SHORT_IMPUTED"
                continue

            # (3) Ban ngày: cascade causal persistence
            day_ts = ts_val - pd.Timedelta(minutes=FREQ_MINUTES * 96)
            week_ts = ts_val - pd.Timedelta(minutes=FREQ_MINUTES * 672)
            if day_ts in measured_vals:
                out.at[i, TARGET_COL] = measured_vals[day_ts]
                out.at[i, "energy_source"] = "causal_day_persistence"
            elif week_ts in measured_vals:
                out.at[i, TARGET_COL] = measured_vals[week_ts]
                out.at[i, "energy_source"] = "causal_week_persistence"
            elif profile.get(key):
                out.at[i, TARGET_COL] = float(np.median(profile[key]))
                out.at[i, "energy_source"] = "causal_profile_median"
            else:
                out.at[i, TARGET_COL] = 0.0
                out.at[i, "energy_source"] = "fallback_zero"
            out.at[i, "training_quality_reason"] = "SOURCE_GAP_SHORT_IMPUTED"

        return out

    # Áp dụng cascade cho từng site
    cascade_parts = []
    for sid, sdf in df.groupby(SITE_COL, observed=True, sort=True):
        cascade_parts.append(fill_inserted_energy_site(sdf))
    df = pd.concat(cascade_parts, ignore_index=True)
    df = df.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)

    print(f"Đã điền target cho {df['timestamp_was_inserted'].sum()} slot inserted.")
    print(f"\n--- PHÂN BỐ ENERGY_SOURCE SAU CASCADE ---")
    print(df["energy_source"].value_counts().to_string())

    # ## 8. Mask outlier
    # *Nguồn tham chiếu logic:* `srcs/05_machine_learning/Forcasting_v3/forecasting_common.py` -> hàm `classify_outlier_group()`  
    # Phân loại các quan sát thành nhóm outlier dựa trên `gmm_if_outlier_flag` và `gmm_if_outlier_reason`. Cột `outlier_group` dùng cho sample weighting và báo cáo.

    # Phân loại outlier_group (logic từ classify_outlier_group)
    flag = df["gmm_if_outlier_flag"].fillna(False).astype(bool)
    reason = df["gmm_if_outlier_reason"].fillna("").astype(str)
    rule_count = reason.str.count(r"\+") + reason.ne("").astype(int)

    df["outlier_group"] = "normal"
    one_rule = flag & rule_count.eq(1)
    multi_rule = flag & rule_count.ge(2)

    df.loc[one_rule & reason.eq("GMM_IF_CONSENSUS"), "outlier_group"] = "gmm_if_consensus"
    df.loc[one_rule & reason.eq("PHYSICAL_OVER_CAPACITY"), "outlier_group"] = "physical_over_capacity"
    df.loc[
        one_rule & ~reason.isin(["GMM_IF_CONSENSUS", "PHYSICAL_OVER_CAPACITY"]),
        "outlier_group"
    ] = "other_physical_rule"
    df.loc[multi_rule, "outlier_group"] = "multiple_rules"

    print("--- PHÂN BỐ OUTLIER_GROUP ---")
    print(df["outlier_group"].value_counts().to_string())

    # ## 9. Kiểm chứng dữ liệu (QA/QC)
    # *Nguồn tham chiếu style QA:* `notebooks/split_and_feature/2026_07_25_Feature_Engineering_Aggregate.ipynb`  
    # Kiểm tra tính toàn vẹn: missing values, infinity, phân bố `energy_source`, và gate check target null.

    # ── Missing Values (cột chính) ──
    key_cols = [TARGET_COL, "energy_source", "outlier_group",
                "timestamp_was_inserted", "exclude_from_training"]
    missing_stats = df[key_cols].isna().sum().to_frame(name="Missing_Count")
    missing_stats["Missing_Pct"] = (missing_stats["Missing_Count"] / len(df)) * 100
    print("\n--- BÁO CÁO MISSING VALUES (CỘT CHÍNH) ---")
    display(missing_stats)

    # ── Infinity ──
    num_cols = df.select_dtypes(include=[np.number]).columns
    inf_total = sum(int(np.isinf(df[c]).sum()) for c in num_cols if df[c].notna().any())
    print(f"\n--- GIÁ TRỊ VÔ CỰC (INFINITY): {inf_total} ---")

    # ── Phân bố energy_source ──
    print("\n--- PHÂN BỐ ENERGY_SOURCE ---")
    display(df["energy_source"].value_counts().to_frame(name="Số dòng"))

    # ── Gate check ──
    target_null = int(df[TARGET_COL].isna().sum())
    src_empty = int((df["energy_source"].isna() | df["energy_source"].eq("")).sum())
    print(f"\n--- GATE CHECK ---")
    print(f"- Target null: {target_null}")
    print(f"- Energy_source rỗng: {src_empty}")
    if target_null == 0 and src_empty == 0:
        print("PASS - Không còn target null hoặc energy_source rỗng.")
    else:
        print("[CRITICAL ERROR] Còn giá trị null/rỗng!")

    # ### Nhận xét về Kiểm chứng Dữ liệu:
    # - Sau cascade, **tất cả** slot inserted đều được gán `energy_source` và giá trị `target`. Không còn dòng nào thiếu.
    # - Phân bố `energy_source` hợp lý: phần lớn là `measured` (dữ liệu đo thực tế), tiếp theo là `etl_imputed` (dữ liệu đã qua ETL).
    # - Slot inserted ban đêm → `night_zero = 0.0` (đúng vật lý: không có năng lượng mặt trời ban đêm).
    # - Gap lớn ≥ 24h → `machine_failure_zero` + `exclude_from_training = True` (sự cố thiết bị, không dùng để train).
    # - Metadata tĩnh (`capacity_kw`, `number_of_panels`, `latitude`, `longitude`) giữ nguyên NaN cho các site/dòng thiếu, không bịa giá trị.
    # - Tuyệt đối không có giá trị `Infinity`, đảm bảo tính toàn vẹn số học.

    # ## 10. Export Processed Dataset
    # *Nguồn tham chiếu style Export:* `notebooks/split_and_feature/2026_07_25_Feature_Engineering_Aggregate.ipynb`

    # ── Bỏ các cột không dùng làm đặc trưng, để giảm dung lượng cho các bước sau ──
    # Đã đối chiếu toàn bộ notebook 02 đến 09: các cột dưới đây hoặc không xuất hiện ở đâu,
    # hoặc chỉ nằm trong DENY_LIST của notebook 05, nên mang theo là dư thừa.
    COT_BO = [
        # co danh dau imputed khong duoc dung lam dac trung
        'capacity_kw_is_imputed', 'cloud_cover_low_is_imputed', 'cloud_cover_total_is_imputed',
        'number_of_panels_is_imputed', 'temperature_c_is_imputed', 'wind_speed_is_imputed',
        'cloud_cover_high_is_imputed', 'cloud_cover_mid_is_imputed', 'precipitation_mm_is_imputed',
        # thoi tiet khong dung lam dac trung (giu cloud_cover_total va wind_speed)
        # THU NGHIEM LAI (2026-07-31): GIU LAI cloud_cover_low/mid/high, khong bo nua.
        # Ly do: research thuc te cho thay may tang THAP moi thuc su che nang manh, may tang
        # CAO (cirrus) gan nhu khong can nang - gop chung vao cloud_cover_total co the mat tin
        # hieu nay. Nguon: "An investigation of photovoltaic power forecasting in buildings
        # considering shadow effects: SHAP analysis" (ScienceDirect, sciencedirect.com/science/
        # article/abs/pii/S0960148125004835) - xep hang feature quan trong gom PPS (ty le PV bi
        # che) va cac dac trung lien quan may/bong; "Advancements and Challenges in PV Power
        # Forecasting: A Comprehensive Review" (MDPI, mdpi.com/1996-1073/18/8/2108).
        'precipitation_mm',
        'weather_code', 'weather_type_is_day', 'weather_is_day',
        # khoa ky thuat, chi bi DENY o notebook 05
        'weather_id', 'weather_type_id', 'weather_timestamp',
        'gen_id', 'date_id', 'time_id', 'geo_id', 'is_dst_repeat', 'full_date',
        # metadata mo ta khong sinh dac trung nao duoc chon
        'location_name', 'site_metric', 'gmm_if_outlier_reason',
    ]

    _co = [c for c in COT_BO if c in df.columns]
    _truoc_mb = df.memory_usage(deep=True).sum() / 1024**2
    _truoc_cot = len(df.columns)
    df = df.drop(columns=_co)
    _sau_mb = df.memory_usage(deep=True).sum() / 1024**2

    print("--- BO COT KHONG DUNG ---")
    print(f"Đã bỏ {len(_co)} cột: {_co}")
    _thieu = [c for c in COT_BO if c not in _co]
    if _thieu:
        print(f"Không có trong dữ liệu nên bỏ qua: {_thieu}")
    print(f"Số cột : {_truoc_cot} -> {len(df.columns)}")
    print(f"Bộ nhớ : {_truoc_mb:.1f} MB -> {_sau_mb:.1f} MB (giảm {(1 - _sau_mb / _truoc_mb) * 100:.1f}%)")

    # ── Giữ lại các cột bắt buộc cho những bước sau ──
    BAT_BUOC = [TARGET_COL, SITE_COL, TIMESTAMP_COL, 'energy_source', 'outlier_group',
                'latitude', 'longitude', 'capacity_kw', 'number_of_panels',
                'shortwave_radiation', 'direct_normal_irradiance', 'diffuse_solar_radiation',
                'temperature_c', 'cloud_cover_total',
                'cloud_cover_low', 'cloud_cover_mid', 'cloud_cover_high']
    _mat = [c for c in BAT_BUOC if c not in df.columns]
    if _mat:
        raise KeyError(f"Đã bỏ mất cột bắt buộc: {_mat}")
    print(f"\nĐã kiểm: {len(BAT_BUOC)} cột bắt buộc còn nguyên (gồm latitude/longitude cho bước 03-2).")

    # Lưu kết quả ra parquet
    import os
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)

    print(f"Đang lưu dữ liệu ra: {OUTPUT_PATH}")
    print(f"Shape cuối cùng: {len(df)} dòng x {len(df.columns)} cột")
    print(f"Dung lượng in-memory: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    print("Hoàn tất lưu file v3_continuous_grid.parquet!")



# 1.2 Chia train/val/test + fold theo thoi gian (tu 02_split_time_series.ipynb)
def run_split_time_series():

    # # Ticket: Split Time-Series Data (Forecasting-Safe)
    # Dự án: Tốt nghiệp - Energy Forecasting - Nhóm thực hiện: The Outliers
    #
    # ## 1. TỔNG QUAN VÀ MỤC TIÊU
    # Notebook này chia dữ liệu theo thời gian cho bài toán forecasting, **không có random split** để tránh temporal leakage:
    #
    # 1. Hold-out **test** = 15% cuối dòng thời gian.
    # 2. Phần còn lại = **development** set.
    # 3. Trong development, tạo `sklearn.model_selection.TimeSeriesSplit` folds (hỗ trợ `sliding` và `expanding`).
    # 4. Export compatibility alias `train/` và `val/` từ fold cuối cùng.
    #
    # **Input:** `v3_continuous_grid.parquet` (output của Notebook 01)
    #
    # **Nguồn logic tham chiếu Audit:**
    # - `notebooks/split_and_feature/01_slip_time_series.ipynb` — toàn bộ logic split được tách ra từ cell code 19k ký tự của file này.
    # - Các hàm gốc: `split_development_test()`, `build_sklearn_time_series_folds()`, `filter_window()`, `add_holdout_labels()`, `summarize_part()`.

    # ## 2. Import thư viện và khai báo tham số
    # *Nguồn tham chiếu:* `notebooks/split_and_feature/01_slip_time_series.ipynb` → class `TimeSeriesSplitConfig` (thay bằng biến thường)

    # ── Gioi han thread: may i5-12450HX co 8 core / 12 thread (4 P-core + 4 E-core).
    # Dung het 12 thread lam cac thread tranh nhau va CHAM HON. Dat 6 de bam P-core,
    # con lai de cho Jupyter va he dieu hanh. Phai set TRUOC khi numpy nap moi co tac dung.
    import os

    for _bien in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                  'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ.setdefault(_bien, '6')

    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import warnings
    from sklearn.model_selection import TimeSeriesSplit

    warnings.filterwarnings('ignore')
    sns.set_theme(style="whitegrid")

    # ── Tham số split (thay cho TimeSeriesSplitConfig) ──
    STRATEGY = "expanding"         # "sliding" hoặc "expanding"
    TEST_RATIO = 0.15
    N_SPLITS = 5
    SLIDING_TRAIN_BLOCKS = 3      # chỉ dùng khi STRATEGY = "expanding"
    VERSION = "v3"

    # ── Tên cột ──
    SITE_COL = "site_id"
    TIMESTAMP_COL = "timestamp"
    TARGET_COL = "energy_generated_kwh"

    # ── Đường dẫn (tương đối) ──
    INPUT_PATH = "../../../data/model/v3/01_reindex_py/v3_continuous_grid.parquet"
    OUTPUT_DIR = "../../../data/model/v3/02_split_py"

    print(" Đã import thư viện và khai báo tham số.")
    print(f"   Strategy   : {STRATEGY}")
    print(f"   Test ratio : {TEST_RATIO}")
    print(f"   N splits   : {N_SPLITS}")
    print(f"   Version    : {VERSION}")


    # ## 3. Đọc dữ liệu v3_continuous_grid
    # Đây là output của Notebook 01 (Reindex & Mask Outlier).

    df = pd.read_parquet(INPUT_PATH)
    df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL], errors="coerce")
    df = df[df[TIMESTAMP_COL].notna()].copy()
    df = df.sort_values([TIMESTAMP_COL, SITE_COL]).reset_index(drop=True)

    print(f"Đã đọc dữ liệu từ: {INPUT_PATH}")
    print(f"Shape: {df.shape[0]:,} dòng × {df.shape[1]} cột")
    print(f"Số site: {df[SITE_COL].nunique()}")
    print(f"Khoảng thời gian: {df[TIMESTAMP_COL].min()} → {df[TIMESTAMP_COL].max()}")
    display(df.head(3))

    # ## 3.1. Kiểm tra tham số và cột bắt buộc
    # *Nguồn tham chiếu:* `notebooks/split_and_feature/01_slip_time_series.ipynb` -> hàm `require_columns()` & `validate_config()`

    # ── Kiểm tra cột bắt buộc (require_columns) ──
    required_cols = [TIMESTAMP_COL, SITE_COL, TARGET_COL]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    # ── Kiểm tra tham số cấu hình (validate_config) ──
    if STRATEGY not in ("sliding", "expanding"):
        raise ValueError(f"Unsupported strategy={STRATEGY}")
    if not 0 < TEST_RATIO < 1:
        raise ValueError(f"test_ratio must be between 0 and 1, got {TEST_RATIO}")
    if N_SPLITS < 2:
        raise ValueError(f"n_splits must be >= 2, got {N_SPLITS}")
    if SLIDING_TRAIN_BLOCKS < 1:
        raise ValueError(f"sliding_train_blocks must be >= 1, got {SLIDING_TRAIN_BLOCKS}")

    print("PASS: Tất cả tham số cấu hình và cột bắt buộc đều hợp lệ.")


    # ## 4. Khám phá: cấu trúc dữ liệu
    # Xem danh sách cột, kiểu dữ liệu, và thống kê missing values.

    # Danh sách cột và dtypes
    col_info = pd.DataFrame({
        "dtype": df.dtypes,
        "non_null": df.notna().sum(),
        "null_count": df.isna().sum(),
        "null_pct": (df.isna().sum() / len(df) * 100).round(2)
    })

    print(f"Tổng số cột: {len(df.columns)}")
    print(f"Tổng số dòng: {len(df):,}")
    display(col_info)

    # ### Nhận xét cấu trúc:
    # - Dữ liệu đã qua Notebook 01: có đủ cột provenance (`energy_source`, `timestamp_was_inserted`, `outlier_group`, `exclude_from_training`, v.v.).
    # - Các cột thời tiết đã được `ffill()` causal ở bước trước. Cột metadata tĩnh (`capacity_kw`, `number_of_panels`) vẫn có thể chứa NaN (đúng thiết kế — không bịa giá trị).

    # ## 5. Khám phá: energy_source và outlier_group
    # Hiểu ý nghĩa từng nhãn `energy_source` và phân bố `outlier_group`.

    # Phân bố energy_source
    print("--- PHÂN BỐ ENERGY_SOURCE ---")
    es_counts = df["energy_source"].value_counts()
    es_pct = (es_counts / len(df) * 100).round(2)
    es_table = pd.DataFrame({"Số dòng": es_counts, "Tỷ lệ %": es_pct})
    display(es_table)

    print("\nÝ nghĩa các nhãn energy_source:")
    print("  measured              : Đo thực tế từ raw solar data")
    print("  etl_imputed           : Giá trị đã qua ETL impute (không có trong raw)")
    print("  night_zero            : Slot ban đêm chèn thêm → target = 0")
    print("  causal_day_persistence: Slot ban ngày chèn, dùng giá trị hôm qua cùng giờ")
    print("  causal_week_persistence: Slot ban ngày chèn, dùng giá trị tuần trước cùng giờ")
    print("  causal_profile_median : Slot ban ngày chèn, dùng median profile (quarter_hour × season)")
    print("  fallback_zero         : Slot ban ngày chèn, không tìm được tham chiếu → 0")
    print("  machine_failure_zero  : Gap ≥ 24h → target = 0, exclude_from_training = True")

    # Phân bố outlier_group
    print("\n--- PHÂN BỐ OUTLIER_GROUP ---")
    if "outlier_group" in df.columns:
        display(df["outlier_group"].value_counts().to_frame(name="Số dòng"))
    else:
        print("Cột outlier_group chưa có trong dữ liệu.")

    # ### Nhận xét energy_source & outlier:
    # - Đa số dữ liệu là `measured` (đo thực tế) — đây là nguồn chất lượng cao nhất cho training.
    # - Các nhãn `night_zero`, `causal_day_persistence`, v.v. chỉ xuất hiện ở dòng **inserted** (chèn thêm ở Notebook 01).
    # - `machine_failure_zero` đã được đánh dấu `exclude_from_training = True` — mô hình sẽ không dùng các dòng này.
    # - `outlier_group = normal` chiếm đại đa số. Các nhóm outlier nhỏ (`gmm_if_consensus`, `physical_over_capacity`) sẽ được dùng cho sample weighting.

    # ## 6. Khám phá: tỷ lệ timestamp_was_inserted và tính liên tục thời gian
    # Kiểm tra dữ liệu có thực sự liên tục 15 phút không (output mong đợi từ Notebook 01).

    # Tỷ lệ inserted
    if "timestamp_was_inserted" in df.columns:
        n_ins = df["timestamp_was_inserted"].sum()
        n_orig = len(df) - n_ins
        print(f"Dòng gốc (original) : {n_orig:,} ({n_orig/len(df):.2%})")
        print(f"Dòng chèn (inserted): {n_ins:,} ({n_ins/len(df):.2%})")
    else:
        print("Cột timestamp_was_inserted chưa có.")

    # Kiểm tra tính liên tục 15 phút cho từng site
    print("\n--- KIỂM TRA TÍNH LIÊN TỤC 15 PHÚT ---")
    gap_issues = []
    for site_id, site_df in df.groupby(SITE_COL, observed=True):
        ts_sorted = site_df[TIMESTAMP_COL].sort_values()
        diffs = ts_sorted.diff().dropna()
        expected = pd.Timedelta(minutes=15)
        bad = diffs[diffs != expected]
        if len(bad) > 0:
            gap_issues.append({
                "site_id": site_id,
                "số_gap_bất_thường": len(bad),
                "min_diff": bad.min(),
                "max_diff": bad.max()
            })

    if gap_issues:
        print(f"Có {len(gap_issues)} site có khoảng cách KHÔNG đúng 15 phút:")
        display(pd.DataFrame(gap_issues))
    else:
        print("Tất cả site đều có lưới liên tục đúng 15 phút. Không còn gap.")

    # ### Nhận xét tính liên tục:
    # - Nếu tất cả site đều PASS → Notebook 01 đã hoàn thành tốt việc reindex.
    # - Nếu có site bất thường, cần quay lại kiểm tra Notebook 01.
    # - Tỷ lệ inserted cho thấy bao nhiêu phần trăm dữ liệu là do reindex chèn thêm (không phải đo thực tế).

    # ## 7. Tách unique timestamps và chia Development / Test
    # *Nguồn tham chiếu:* `notebooks/split_and_feature/01_slip_time_series.ipynb` → hàm `split_development_test()`  
    # Split trên trục **unique timestamp** (không phải raw rows) để tránh cùng 1 timestamp bị chia vào cả train lẫn val cho các site khác nhau.

    # Lấy danh sách unique timestamps đã sắp xếp
    timestamps = pd.Series(df[TIMESTAMP_COL].dropna().sort_values().unique())
    n_total = len(timestamps)

    # Tính điểm cắt test
    test_start_idx = int(n_total * (1.0 - TEST_RATIO))
    test_start_idx = min(max(test_start_idx, N_SPLITS + 2), n_total - 1)

    test_start_ts = pd.Timestamp(timestamps.iloc[test_start_idx])
    development_ts = timestamps.iloc[:test_start_idx].reset_index(drop=True)
    test_ts = timestamps.iloc[test_start_idx:].reset_index(drop=True)

    print(f"Tổng unique timestamps: {n_total:,}")
    print(f"Test start timestamp  : {test_start_ts}")
    print(f"Development timestamps: {len(development_ts):,} ({len(development_ts)/n_total:.2%})")
    print(f"Test timestamps       : {len(test_ts):,} ({len(test_ts)/n_total:.2%})")
    print(f"\nDevelopment: {development_ts.iloc[0]} → {development_ts.iloc[-1]}")
    print(f"Test       : {test_ts.iloc[0]} → {test_ts.iloc[-1]}")

    # ## 8. Gán nhãn holdout (development / test) vào DataFrame
    # *Nguồn tham chiếu:* `notebooks/split_and_feature/01_slip_time_series.ipynb` → hàm `add_holdout_labels()`

    # Gán nhãn holdout_split
    df[f"{VERSION}_holdout_split"] = "development"
    df.loc[df[TIMESTAMP_COL] >= test_start_ts, f"{VERSION}_holdout_split"] = "test"
    df[f"{VERSION}_test_start_timestamp"] = test_start_ts
    df[f"{VERSION}_split_strategy"] = STRATEGY
    df[f"{VERSION}_n_time_series_splits"] = N_SPLITS

    development = df.loc[df[f"{VERSION}_holdout_split"].eq("development")].copy(deep=False)
    test = df.loc[df[f"{VERSION}_holdout_split"].eq("test")].copy(deep=False)

    print(f"Development: {len(development):,} dòng ({len(development)/len(df):.2%})")
    print(f"Test       : {len(test):,} dòng ({len(test)/len(df):.2%})")
    print(f"\nSố site trong development: {development[SITE_COL].nunique()}")
    print(f"Số site trong test       : {test[SITE_COL].nunique()}")

    # ## 9. Tạo TimeSeriesSplit folds trong development set
    # *Nguồn tham chiếu:* `notebooks/split_and_feature/01_slip_time_series.ipynb` → hàm `build_sklearn_time_series_folds()`  
    # Dùng `sklearn.model_selection.TimeSeriesSplit` trên trục unique timestamp, rồi map ngược lại tất cả dòng.

    # Kiểm tra số lượng development timestamps
    if len(development_ts) < N_SPLITS + 2:
        raise ValueError(
            "Not enough development timestamps for TimeSeriesSplit: "
            f"timestamps={len(development_ts)}, n_splits={N_SPLITS}"
        )

    # Tính test_size và max_train_size cho TimeSeriesSplit
    timestamp_axis = pd.Series(development_ts).reset_index(drop=True)

    if STRATEGY == "sliding":
        total_blocks = N_SPLITS + SLIDING_TRAIN_BLOCKS
        test_size = len(timestamp_axis) // total_blocks
        max_train_size = test_size * SLIDING_TRAIN_BLOCKS
    else:
        test_size = len(timestamp_axis) // (N_SPLITS + 1)
        max_train_size = None

    # Kiểm tra validation window và độ dài chuỗi thời gian
    if test_size <= 0:
        raise ValueError(
            "TimeSeriesSplit validation window would be empty: "
            f"timestamps={len(timestamp_axis)}, n_splits={N_SPLITS}, strategy={STRATEGY}"
        )
    if len(timestamp_axis) <= N_SPLITS * test_size:
        raise ValueError(
            "Not enough timestamps before test for sklearn TimeSeriesSplit: "
            f"timestamps={len(timestamp_axis)}, n_splits={N_SPLITS}, test_size={test_size}"
        )

    print(f"Strategy       : {STRATEGY}")
    print(f"Validation size: {test_size} timestamps / fold")
    print(f"Max train size : {max_train_size}")

    # Tạo splitter và build folds
    splitter = TimeSeriesSplit(
        n_splits=N_SPLITS,
        test_size=test_size,
        max_train_size=max_train_size,
    )

    folds = []
    for fold, (train_idx, val_idx) in enumerate(splitter.split(timestamp_axis), start=1):
        train_ts = timestamp_axis.iloc[train_idx].reset_index(drop=True)
        val_ts = timestamp_axis.iloc[val_idx].reset_index(drop=True)
        folds.append({
            "fold": fold,
            "train_timestamps": len(train_ts),
            "val_timestamps": len(val_ts),
            "train_start_ts": pd.Timestamp(train_ts.iloc[0]),
            "train_end_ts": pd.Timestamp(train_ts.iloc[-1]),
            "val_start_ts": pd.Timestamp(val_ts.iloc[0]),
            "val_end_ts": pd.Timestamp(val_ts.iloc[-1]),
        })

    fold_summary = pd.DataFrame(folds)
    print(f"\n--- DANH SÁCH {len(folds)} FOLDS ---")
    display(fold_summary)


    # ## 11. Tạo DataFrame cho từng fold và compatibility alias
    # *Nguồn tham chiếu:* `notebooks/split_and_feature/01_slip_time_series.ipynb` → hàm `filter_window()` và phần `run_split()` gán `train_alias`, `val_alias`  
    # Filter dữ liệu theo cửa sổ timestamp cho từng fold. Fold cuối = alias cho train/val.

    # Hàm filter theo cửa sổ timestamp
    def filter_window(df, start_ts, end_ts):
        """Lọc dữ liệu trong cửa sổ [start_ts, end_ts]."""
        mask = (df[TIMESTAMP_COL] >= start_ts) & (df[TIMESTAMP_COL] <= end_ts)
        return df.loc[mask].copy(deep=False)

    # Compatibility alias từ fold cuối
    final_fold = folds[-1]
    train_alias = filter_window(df, final_fold["train_start_ts"], final_fold["train_end_ts"])
    val_alias = filter_window(df, final_fold["val_start_ts"], final_fold["val_end_ts"])

    train_alias[f"{VERSION}_split"] = "train"
    val_alias[f"{VERSION}_split"] = "val"
    test[f"{VERSION}_split"] = "test"

    print(f"Final fold (fold {final_fold['fold']}):")
    print(f"  Train: {final_fold['train_start_ts']} → {final_fold['train_end_ts']} ({len(train_alias):,} dòng)")
    print(f"  Val  : {final_fold['val_start_ts']} → {final_fold['val_end_ts']} ({len(val_alias):,} dòng)")
    print(f"  Test : {test_ts.iloc[0]} → {test_ts.iloc[-1]} ({len(test):,} dòng)")

    # ## 12. Tổng kết split (Split Summary)
    # *Nguồn tham chiếu:* `notebooks/split_and_feature/01_slip_time_series.ipynb` → hàm `summarize_part()`

    # Hàm tổng kết
    def summarize_part(name, part, fold=None, role=None):
        """Tạo dict tổng kết cho 1 phần dữ liệu."""
        row = {
            "name": name,
            "rows": int(len(part)),
            "site_count": int(part[SITE_COL].nunique()) if SITE_COL in part else 0,
            "min_timestamp": part[TIMESTAMP_COL].min() if len(part) else pd.NaT,
            "max_timestamp": part[TIMESTAMP_COL].max() if len(part) else pd.NaT,
            "target_null_rows": int(part[TARGET_COL].isna().sum()) if TARGET_COL in part else 0,
        }
        if fold is not None:
            row["fold"] = fold
        if role is not None:
            row["role"] = role
        for col in (
            f"{VERSION}_missing_weather_flag",
            f"{VERSION}_outlier_flag",
            f"{VERSION}_exclude_from_loss_flag",
            f"{VERSION}_has_complete_history_features",
            f"{VERSION}_gap_after_prev_flag",
        ):
            if col in part.columns:
                row[col] = int(part[col].fillna(False).sum())
        return row

    split_summary = pd.DataFrame([
        summarize_part("development", development),
        summarize_part("train_alias_final_fold", train_alias),
        summarize_part("val_alias_final_fold", val_alias),
        summarize_part("test", test),
    ])


    fold_rows = []
    for f in folds:
        fold_train = filter_window(df, f["train_start_ts"], f["train_end_ts"])
        fold_val = filter_window(df, f["val_start_ts"], f["val_end_ts"])
        fold_rows.append(summarize_part(f"fold_{f['fold']}_train", fold_train, fold=f['fold'], role='train'))
        fold_rows.append(summarize_part(f"fold_{f['fold']}_val", fold_val, fold=f['fold'], role='val'))
        del fold_train, fold_val

    fold_detail = pd.DataFrame(fold_rows)
    print("\n--- FOLD DETAIL ---")
    display(fold_detail)


    # ## 13. Export
    # *Nguồn tham chiếu:* `notebooks/split_and_feature/01_slip_time_series.ipynb` → phần `run_split()` lưu parquet và CSV summary  
    # Lưu development, test, từng fold, alias train/val, và summary.

    from pathlib import Path

    out_dir = Path(OUTPUT_DIR)

    # Tạo thư mục
    for sub in ["development", "test", "final_train", "train", "val",
                "time_series_folds", "summaries"]:
        (out_dir / sub).mkdir(parents=True, exist_ok=True)

    # Lưu development, test, final_train
    development.to_parquet(out_dir / "development" / f"{VERSION}_development.parquet", index=False)
    test.to_parquet(out_dir / "test" / f"{VERSION}_test.parquet", index=False)
    development.to_parquet(out_dir / "final_train" / f"{VERSION}_final_train.parquet", index=False)

    # Lưu train/val alias (từ fold cuối)
    train_alias.to_parquet(out_dir / "train" / f"{VERSION}_train.parquet", index=False)
    val_alias.to_parquet(out_dir / "val" / f"{VERSION}_val.parquet", index=False)

    # Lưu từng fold
    for f in folds:
        fold_n = f["fold"]
        ft = filter_window(df, f["train_start_ts"], f["train_end_ts"])
        fv = filter_window(df, f["val_start_ts"], f["val_end_ts"])
        ft[f"{VERSION}_cv_fold"] = fold_n
        ft[f"{VERSION}_cv_role"] = "train"
        fv[f"{VERSION}_cv_fold"] = fold_n
        fv[f"{VERSION}_cv_role"] = "val"
        ft.to_parquet(out_dir / "time_series_folds" / f"fold_{fold_n}_train.parquet", index=False)
        fv.to_parquet(out_dir / "time_series_folds" / f"fold_{fold_n}_val.parquet", index=False)
        del ft, fv

    # Lưu summaries
    split_summary.to_csv(out_dir / "summaries" / f"{VERSION}_split_summary.csv", index=False)
    fold_detail.to_csv(out_dir / "summaries" / f"{VERSION}_time_series_fold_summary.csv", index=False)

    print(f"Đã lưu tất cả output vào: {OUTPUT_DIR}")
    print(f"  development : {len(development):,} dòng")
    print(f"  test        : {len(test):,} dòng")
    print(f"  train alias : {len(train_alias):,} dòng (fold {final_fold['fold']})")
    print(f"  val alias   : {len(val_alias):,} dòng (fold {final_fold['fold']})")
    print(f"  folds       : {len(folds)} folds × 2 parquet")
    print("Hoàn tất Notebook 02 — Split Time-Series Data!")



if __name__ == "__main__":
    run_reindex_mask_outlier()
    run_split_time_series()