"""Fill missing solar generation values using the original hybrid strategy."""

from __future__ import annotations

from io import StringIO
import logging
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sqlalchemy import text
import yaml


warnings.filterwarnings("ignore")
log = logging.getLogger("pipeline.hybrid_imputation")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = (
    PROJECT_ROOT / "config" / "02_transform" / "03_hybrid_imputation.yaml"
)

with CONFIG_FILE.open(encoding="utf-8") as _file:
    _config = yaml.safe_load(_file)

SCHEMA = _config["database"]["schema"]
SOLAR_TABLE = _config["database"]["solar_table"]
WEATHER_TABLE = _config["database"]["weather_table"]

GAP_LINEAR_MAX = int(_config["imputation"]["gap_linear_max_rows"])
GAP_CUBIC_MAX = int(_config["imputation"]["gap_cubic_max_rows"])
NIGHT_START = float(_config["imputation"]["night_start_hour"])
NIGHT_END = float(_config["imputation"]["night_end_hour"])
NIGHT_TOLERANCE = pd.Timedelta(
    _config["imputation"]["night_weather_tolerance"]
)
REGRESSION_TOLERANCE = pd.Timedelta(
    _config["imputation"]["regression_weather_tolerance"]
)
REGRESSION_MIN_TRAINING_ROWS = int(
    _config["imputation"]["regression_min_training_rows"]
)
REGRESSION_FEATURES = list(_config["imputation"]["regression_features"])

OUTPUT_DIR = PROJECT_ROOT / _config["output"]["directory"]
EXPORT_INTERMEDIATE = bool(_config["output"]["export_intermediate_csv"])
FINAL_CSV = OUTPUT_DIR / _config["output"]["final_csv"]
COPY_CHUNK_SIZE = int(_config["runtime"]["database_copy_chunk_size"])
FILL_NULL_ALGORITHM_COLUMN = "fill_null_algorithm"
ALGORITHM_ORIGINAL = "original"
ALGORITHM_RULE_BASED_NIGHT = "rule_based_night"
ALGORITHM_LINEAR = "linear"
ALGORITHM_CUBIC = "cubic"
ALGORITHM_REGRESSION = "regression"


def export_csv(df: pd.DataFrame, filename: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False)
    log.info("Đã xuất %s (%s dòng)", path, f"{len(df):,}")


def get_null_gaps(series: pd.Series) -> list[tuple[int, int, int]]:
    """Return (start, end, size) for every consecutive null gap."""
    gaps: list[tuple[int, int, int]] = []
    in_gap = False
    start = 0
    for index, value in enumerate(series):
        if pd.isna(value):
            if not in_gap:
                start = index
                in_gap = True
        elif in_gap:
            gaps.append((start, index - 1, index - start))
            in_gap = False
    if in_gap:
        gaps.append((start, len(series) - 1, len(series) - start))
    return gaps


def rule_based_night_zero(
    solar_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    site_key: int,
) -> tuple[pd.Series, int, pd.Series]:
    """Set missing generation to zero at night or when radiation is zero."""
    generation = solar_df["energy_generated_kwh"].copy()
    timestamp = solar_df["timestamp"]

    decimal_hour = timestamp.dt.hour + timestamp.dt.minute / 60
    is_night = (decimal_hour >= NIGHT_START) | (decimal_hour < NIGHT_END)

    weather = weather_df[weather_df["sitekey"] == site_key][
        ["timestamp", "shortwave_radiation", "is_day"]
    ].copy()
    weather["timestamp"] = pd.to_datetime(weather["timestamp"])

    merged = pd.merge_asof(
        solar_df[["timestamp"]].reset_index(),
        weather.sort_values("timestamp"),
        on="timestamp",
        tolerance=NIGHT_TOLERANCE,
        direction="nearest",
    ).set_index("index")

    zero_radiation = (
        (merged["shortwave_radiation"].fillna(0) == 0)
        | (merged["is_day"].fillna(0) == 0)
    )
    zero_mask = is_night.values | zero_radiation.values
    fill_mask = zero_mask & generation.isna()
    filled = int(fill_mask.sum())
    generation[fill_mask] = 0.0
    return generation, filled, fill_mask


def regression_imputation_large_gaps_strict(
    solar_sub: pd.DataFrame,
    weather_df: pd.DataFrame,
    site_key: int,
    large_gap_indices: set[int],
) -> tuple[np.ndarray, int, list[int]]:
    """Apply the original per-site regression only to original large gaps."""
    weather = weather_df[weather_df["sitekey"] == site_key][
        ["timestamp", *REGRESSION_FEATURES]
    ].copy()
    weather["timestamp"] = pd.to_datetime(weather["timestamp"])

    merged = pd.merge_asof(
        solar_sub[["timestamp", "energy_generated_kwh"]].reset_index(),
        weather.sort_values("timestamp"),
        on="timestamp",
        tolerance=REGRESSION_TOLERANCE,
        direction="nearest",
    ).set_index("index")

    train_mask = (
        merged["energy_generated_kwh"].notna()
        & merged[REGRESSION_FEATURES].notna().all(axis=1)
    )
    prediction_mask = (
        merged["energy_generated_kwh"].isna()
        & merged[REGRESSION_FEATURES].notna().all(axis=1)
    )

    if train_mask.sum() < REGRESSION_MIN_TRAINING_ROWS:
        return solar_sub["energy_generated_kwh"].values, 0, []

    scaler = StandardScaler()
    x_train = scaler.fit_transform(
        merged.loc[train_mask, REGRESSION_FEATURES].values
    )
    model = LinearRegression()
    model.fit(x_train, merged.loc[train_mask, "energy_generated_kwh"].values)

    result = solar_sub["energy_generated_kwh"].copy()
    filled = 0
    filled_positions: list[int] = []
    if prediction_mask.any():
        predictions = model.predict(
            scaler.transform(
                merged.loc[prediction_mask, REGRESSION_FEATURES].values
            )
        )
        for prediction, index in zip(
            predictions,
            merged[prediction_mask].index.tolist(),
        ):
            local_position = (
                solar_sub.index.get_loc(index)
                if index in solar_sub.index
                else None
            )
            if (
                local_position is not None
                and local_position in large_gap_indices
            ):
                result.iloc[local_position] = max(0.0, prediction)
                filled += 1
                filled_positions.append(local_position)
    return result.values, filled, filled_positions


def build_imputed_solar(
    solar_df: pd.DataFrame,
    weather_df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int], dict[str, pd.DataFrame]]:
    """Run the original hybrid imputation algorithm without database writes."""
    solar_df = solar_df.copy()
    weather_df = weather_df.copy()
    solar_df["timestamp"] = pd.to_datetime(
        solar_df["timestamp"], errors="coerce"
    )
    weather_df["timestamp"] = pd.to_datetime(
        weather_df["timestamp"], errors="coerce"
    )
    solar_df = (
        solar_df.dropna(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    solar_df[FILL_NULL_ALGORITHM_COLUMN] = np.where(
        solar_df["energy_generated_kwh"].notna(),
        ALGORITHM_ORIGINAL,
        pd.NA,
    )
    weather_df = (
        weather_df.dropna(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    total_null = int(solar_df["energy_generated_kwh"].isna().sum())
    results: list[pd.DataFrame] = []
    stage_results: dict[str, list[pd.DataFrame]] = (
        {
            "rule": [],
            "linear": [],
            "cubic": [],
            "regression": [],
        }
        if EXPORT_INTERMEDIATE
        else {}
    )
    counters = {"night": 0, "linear": 0, "cubic": 0, "regression": 0}

    log.info(
        "Hybrid Imputation input | rows=%s | null=%s",
        f"{len(solar_df):,}",
        f"{total_null:,}",
    )

    for site in sorted(solar_df["sitekey"].unique()):
        subset = (
            solar_df[solar_df["sitekey"] == site]
            .copy()
            .reset_index(drop=True)
        )
        if subset["energy_generated_kwh"].isna().sum() == 0:
            results.append(subset)
            continue

        generation, night_filled, night_fill_mask = rule_based_night_zero(
            subset, weather_df, site
        )
        subset["energy_generated_kwh"] = generation
        subset.loc[night_fill_mask, FILL_NULL_ALGORITHM_COLUMN] = (
            ALGORITHM_RULE_BASED_NIGHT
        )
        counters["night"] += night_filled
        if EXPORT_INTERMEDIATE:
            stage_results["rule"].append(subset.copy())

        time_series = pd.Series(
            subset["energy_generated_kwh"].values,
            index=pd.DatetimeIndex(subset["timestamp"]),
            dtype=float,
        )
        linear_indices: list[int] = []
        cubic_indices: list[int] = []
        large_gap_indices: set[int] = set()
        for start, end, size in get_null_gaps(time_series.values):
            indices = list(range(start, end + 1))
            if size <= GAP_LINEAR_MAX:
                linear_indices.extend(indices)
            elif size <= GAP_CUBIC_MAX:
                cubic_indices.extend(indices)
            else:
                large_gap_indices.update(indices)

        before_linear = int(time_series.isna().sum())
        if linear_indices:
            linear_missing_before = time_series.isna()
            interpolated = time_series.interpolate(method="time")
            for index in linear_indices:
                time_series.iloc[index] = interpolated.iloc[index]
            linear_filled_mask = linear_missing_before & time_series.notna()
            linear_filled_positions = [
                index
                for index in linear_indices
                if bool(linear_filled_mask.iloc[index])
            ]
            subset.loc[
                linear_filled_positions,
                FILL_NULL_ALGORITHM_COLUMN,
            ] = ALGORITHM_LINEAR
        counters["linear"] += before_linear - int(time_series.isna().sum())
        if EXPORT_INTERMEDIATE:
            linear_result = subset.copy()
            linear_result["energy_generated_kwh"] = time_series.values
            stage_results["linear"].append(linear_result)

        before_cubic = int(time_series.isna().sum())
        if cubic_indices:
            cubic_missing_before = time_series.isna()
            temporary = time_series.interpolate(method="linear")
            interpolated = temporary.interpolate(method="cubic")
            for index in cubic_indices:
                time_series.iloc[index] = interpolated.iloc[index]
            cubic_filled_mask = cubic_missing_before & time_series.notna()
            cubic_filled_positions = [
                index
                for index in cubic_indices
                if bool(cubic_filled_mask.iloc[index])
            ]
            subset.loc[
                cubic_filled_positions,
                FILL_NULL_ALGORITHM_COLUMN,
            ] = ALGORITHM_CUBIC
        counters["cubic"] += before_cubic - int(time_series.isna().sum())
        if EXPORT_INTERMEDIATE:
            cubic_result = subset.copy()
            cubic_result["energy_generated_kwh"] = time_series.values
            stage_results["cubic"].append(cubic_result)

        subset["energy_generated_kwh"] = time_series.values
        values, regression_filled, regression_filled_positions = (
            regression_imputation_large_gaps_strict(
                subset,
                weather_df,
                site,
                large_gap_indices,
            )
        )
        subset["energy_generated_kwh"] = values
        subset.loc[
            regression_filled_positions,
            FILL_NULL_ALGORITHM_COLUMN,
        ] = ALGORITHM_REGRESSION
        counters["regression"] += regression_filled
        if EXPORT_INTERMEDIATE:
            stage_results["regression"].append(subset.copy())

        subset["energy_generated_kwh"] = subset[
            "energy_generated_kwh"
        ].clip(lower=0)
        results.append(subset)
        log.info(
            "Site %s | night=%s | linear=%s | cubic=%s | regression=%s "
            "| remaining_null=%s",
            site,
            f"{night_filled:,}",
            f"{len(linear_indices):,}",
            f"{len(cubic_indices):,}",
            f"{regression_filled:,}",
            f"{subset['energy_generated_kwh'].isna().sum():,}",
        )

    cleaned = pd.concat(results, ignore_index=True)
    remaining_null = int(cleaned["energy_generated_kwh"].isna().sum())
    counters["input_null"] = total_null
    counters["remaining_null"] = remaining_null
    counters["filled_total"] = total_null - remaining_null

    materialized_stages = {
        name: pd.concat(frames, ignore_index=True)
        for name, frames in stage_results.items()
        if frames
    }
    return cleaned, counters, materialized_stages


def _copy_updates_to_temp_table(connection, cleaned: pd.DataFrame) -> None:
    """COPY cleaned values to a transaction-local table, then update by key."""
    raw_connection = connection.connection
    cursor = raw_connection.cursor()
    try:
        cursor.execute(
            f"""
            ALTER TABLE {SCHEMA}.{SOLAR_TABLE}
            ADD COLUMN IF NOT EXISTS {FILL_NULL_ALGORITHM_COLUMN} VARCHAR(255)
            """
        )
        cursor.execute(
            """
            CREATE TEMP TABLE temp_solar_energy_imputed (
                sitekey text NOT NULL,
                timestamp timestamp without time zone NOT NULL,
                energy_generated_kwh double precision,
                fill_null_algorithm varchar(255)
            ) ON COMMIT DROP
            """
        )
        for start in range(0, len(cleaned), COPY_CHUNK_SIZE):
            chunk = cleaned.iloc[start : start + COPY_CHUNK_SIZE][
                [
                    "sitekey",
                    "timestamp",
                    "energy_generated_kwh",
                    FILL_NULL_ALGORITHM_COLUMN,
                ]
            ]
            buffer = StringIO()
            chunk.to_csv(
                buffer,
                index=False,
                header=False,
                na_rep="\\N",
                date_format="%Y-%m-%d %H:%M:%S",
            )
            buffer.seek(0)
            cursor.copy_expert(
                """
                COPY temp_solar_energy_imputed
                    (
                        sitekey,
                        timestamp,
                        energy_generated_kwh,
                        fill_null_algorithm
                    )
                FROM STDIN WITH (FORMAT CSV, NULL '\\N')
                """,
                buffer,
            )
            log.info(
                "Prepared update rows %s/%s",
                f"{min(start + COPY_CHUNK_SIZE, len(cleaned)):,}",
                f"{len(cleaned):,}",
            )

        cursor.execute(
            f"""
            UPDATE {SCHEMA}.{SOLAR_TABLE} target
            SET
                energy_generated_kwh = source.energy_generated_kwh,
                fill_null_algorithm = source.fill_null_algorithm
            FROM temp_solar_energy_imputed source
            WHERE target.sitekey = source.sitekey
              AND target.timestamp = source.timestamp
            """
        )
        if cursor.rowcount != len(cleaned):
            raise RuntimeError(
                "Hybrid imputation update row mismatch: "
                f"expected={len(cleaned):,}, updated={cursor.rowcount:,}"
            )
    finally:
        cursor.close()


def run_hybrid_imputation(engine, *, execute: bool = True) -> dict[str, int]:
    """Read buffers, apply the original algorithm, and update energy safely."""
    log.info(">> Đang kéo 2.7 triệu dòng Solar từ Cloud về máy... (sẽ mất khoảng 1-3 phút tùy mạng)")
    solar = pd.read_sql_query(
        text(f"SELECT * FROM {SCHEMA}.{SOLAR_TABLE}"),
        con=engine,
    )
    log.info(">> Đã tải xong Solar data. Đang kéo tiếp 2.7 triệu dòng Weather từ Cloud...")
    weather = pd.read_sql_query(
        text(f"SELECT * FROM {SCHEMA}.{WEATHER_TABLE}"),
        con=engine,
    )
    log.info(">> Đã kéo xong toàn bộ data! Đang chạy mô hình AI nội suy (Imputation)...")
    cleaned, counters, stages = build_imputed_solar(solar, weather)

    if EXPORT_INTERMEDIATE:
        export_csv(stages["rule"], "result_01_rule_based_night.csv")
        export_csv(stages["linear"], "result_02_linear_interpolation.csv")
        export_csv(stages["cubic"], "result_03_cubic_spline.csv")
        export_csv(stages["regression"], "result_04_regression.csv")
        export_csv(cleaned, FINAL_CSV.name)

    log.info("─" * 65)
    log.info("  [TỔNG KẾT QUÁ TRÌNH NỘI SUY (IMPUTATION)]")
    log.info(f"  NULL ban đầu       : {counters['input_null']:,}")
    log.info(f"  - Rule-based (đêm) : điền {counters.get('night', 0):,}")
    log.info(f"  - Linear (≤ 2h)    : điền {counters.get('linear', 0):,}")
    log.info(f"  - Cubic (3-8h)     : điền {counters.get('cubic', 0):,}")
    log.info(f"  - Regression (> 8h): điền {counters.get('regression', 0):,}")
    log.info(f"  => TỔNG ĐÃ ĐIỀN    : {counters['filled_total']:,}")
    log.info(f"  NULL còn lại       : {counters['remaining_null']:,}")
    log.info("─" * 65)

    if not execute:
        log.info("Dry-run: database was not modified")
        return counters

    with engine.begin() as connection:
        _copy_updates_to_temp_table(connection, cleaned)
        database_null = connection.execute(
            text(
                f"SELECT COUNT(*) FROM {SCHEMA}.{SOLAR_TABLE} "
                "WHERE energy_generated_kwh IS NULL"
            )
        ).scalar_one()
        if int(database_null) != counters["remaining_null"]:
            raise RuntimeError(
                "Hybrid imputation null validation failed: "
                f"expected={counters['remaining_null']:,}, "
                f"database={int(database_null):,}"
            )
    log.info("Hybrid Imputation committed successfully")
    return counters
