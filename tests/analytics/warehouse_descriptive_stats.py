"""
Descriptive statistics analysis for solar energy data warehouse.
Analyzes dimension and fact tables to understand data distributions, quality, and patterns.
"""

import os
import ssl
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

db_uri = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
engine = create_engine(db_uri, connect_args={"ssl_context": ssl_context})


class WarehouseAnalytics:
    """Descriptive statistics analyzer for solar energy warehouse."""

    def __init__(self, engine):
        self.engine = engine
        self.results = {}

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return DataFrame."""
        return pd.read_sql_query(query, con=self.engine)

    def analyze_dimension_tables(self) -> Dict[str, pd.DataFrame]:
        """Analyze all dimension tables for structure and completeness."""
        print("\n" + "="*80)
        print("DIMENSION TABLES ANALYSIS")
        print("="*80)

        results = {}

        # 1. Geography Dimension
        print("\n>>> DIM_GEOGRAPHY")
        geo_df = self.execute_query("SELECT * FROM datawarehouse.dim_geography")
        print(f"  Shape: {geo_df.shape}")
        print(f"\n  Descriptive Stats:\n{geo_df.describe()}")
        print(f"\n  Data Types:\n{geo_df.dtypes}")
        print(f"  Null Values:\n{geo_df.isnull().sum()}")
        results["dim_geography"] = geo_df

        # 2. Solar Site Dimension
        print("\n>>> DIM_SOLAR_SITE")
        site_df = self.execute_query("SELECT * FROM datawarehouse.dim_solar_site")
        print(f"  Shape: {site_df.shape}")
        print(f"\n  Descriptive Stats:\n{site_df[['capacity_kw', 'number_of_panels']].describe()}")
        print(f"  Null Values:\n{site_df.isnull().sum()}")
        print(f"  Unique Campus Names: {site_df['campus_name'].nunique()}")
        results["dim_solar_site"] = site_df

        # 3. Date Dimension
        print("\n>>> DIM_DATE")
        date_df = self.execute_query("SELECT * FROM datawarehouse.dim_date")
        print(f"  Shape: {date_df.shape}")
        print(f"  Date Range: {date_df['full_date'].min()} to {date_df['full_date'].max()}")
        print(f"  Year Distribution:\n{date_df['year'].value_counts().sort_index()}")
        print(f"  Holidays: {date_df['is_holiday'].sum()} days")
        print(f"  Semester Days: {date_df['is_semester'].sum()} days")
        print(f"  Exam Days: {date_df['is_exam'].sum()} days")
        results["dim_date"] = date_df

        # 4. Time Dimension
        print("\n>>> DIM_TIME")
        time_df = self.execute_query("SELECT * FROM datawarehouse.dim_time")
        print(f"  Shape: {time_df.shape}")
        print(f"  Time Range: {time_df['time_string'].min()} to {time_df['time_string'].max()}")
        print(f"  Hour Distribution:\n{time_df['hour'].value_counts().sort_index()}")
        results["dim_time"] = time_df

        # 5. Weather Type Dimension
        print("\n>>> DIM_WEATHER_TYPE")
        weather_df = self.execute_query("SELECT * FROM datawarehouse.dim_weather_type")
        print(f"  Shape: {weather_df.shape}")
        print(f"  Weather Types:\n{weather_df[['weather_code', 'weather_condition', 'is_day']].value_counts()}")
        results["dim_weather_type"] = weather_df

        return results

    def analyze_fact_solar_energy(self, dims: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Comprehensive analysis of solar energy generation facts."""
        print("\n" + "="*80)
        print("FACT_SOLAR_ENERGY_GEN ANALYSIS")
        print("="*80)

        query = """
        SELECT
            fse.gen_id, fse.site_id, fse.geo_id, fse.date_id, fse.time_id,
            fse.energy_generated_kwh,
            ds.campus_name, dg.location_name,
            dd.full_date, dd.month, dd.year,
            dt.time_string, dt.hour,
            dg.capacity AS location_capacity,
            ds.capacity_kw AS site_capacity
        FROM datawarehouse.fact_solar_energy_gen fse
        JOIN datawarehouse.dim_solar_site ds ON fse.site_id = ds.site_id
        JOIN datawarehouse.dim_geography dg ON fse.geo_id = dg.geo_id
        JOIN datawarehouse.dim_date dd ON fse.date_id = dd.date_id
        JOIN datawarehouse.dim_time dt ON fse.time_id = dt.time_id
        """

        gen_df = self.execute_query(query)
        print(f"  Shape: {gen_df.shape}")
        print(f"  Date Range: {gen_df['full_date'].min()} to {gen_df['full_date'].max()}")

        # Energy Generation Stats
        print(f"\n  Energy Generation (kWh):")
        print(f"    Count: {gen_df['energy_generated_kwh'].notna().sum():,}")
        print(f"    Null: {gen_df['energy_generated_kwh'].isna().sum():,}")
        stats = gen_df['energy_generated_kwh'].describe()
        print(f"\n{stats}")

        # Daily patterns
        print(f"\n  Daily Patterns (by hour):")
        hourly_stats = gen_df.groupby('hour')['energy_generated_kwh'].agg([
            'count', 'mean', 'std', 'min', 'max'
        ]).round(4)
        print(hourly_stats)

        # Site-level analysis
        print(f"\n  Site-level Analysis:")
        site_stats = gen_df.groupby('campus_name').agg({
            'energy_generated_kwh': ['count', 'sum', 'mean', 'std'],
            'site_capacity': 'first'
        }).round(4)
        print(site_stats)

        # Monthly patterns
        print(f"\n  Monthly Patterns:")
        monthly_stats = gen_df.groupby('month')['energy_generated_kwh'].agg([
            'count', 'mean', 'std', 'min', 'max'
        ]).round(4)
        print(monthly_stats)

        # Null analysis
        print(f"\n  Null Value Analysis:")
        null_by_hour = gen_df.groupby('hour')['energy_generated_kwh'].apply(
            lambda x: x.isna().sum()
        )
        print(f"    Hour with most nulls: {null_by_hour.idxmax()} (count: {null_by_hour.max()})")
        print(f"    Null rate by hour:\n{null_by_hour[null_by_hour > 0].sort_values(ascending=False).head()}")

        # Efficiency: actual vs capacity
        gen_df['efficiency_pct'] = (
            (gen_df['energy_generated_kwh'] / gen_df['site_capacity']) * 100
        ).where(gen_df['site_capacity'] > 0, np.nan)

        print(f"\n  Efficiency (Generated / Site Capacity %):")
        print(f"    Mean: {gen_df['efficiency_pct'].mean():.2f}%")
        print(f"    Median: {gen_df['efficiency_pct'].median():.2f}%")
        print(f"    95th Percentile: {gen_df['efficiency_pct'].quantile(0.95):.2f}%")
        print(f"    Max: {gen_df['efficiency_pct'].max():.2f}%")

        self.results["fact_solar_energy_gen"] = gen_df
        return gen_df

    def analyze_fact_weather(self, dims: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Analyze weather fact table."""
        print("\n" + "="*80)
        print("FACT_WEATHER ANALYSIS")
        print("="*80)

        query = """
        SELECT
            fw.weather_id, fw.geo_id, fw.date_id, fw.time_id, fw.weather_type_id,
            fw.temperature_celsius, fw.humidity_percent, fw.precipitation_mm,
            fw.cloud_cover_percent, fw.wind_speed_kmh,
            dg.location_name,
            dd.full_date, dd.month, dd.year,
            dt.time_string, dt.hour,
            dwt.weather_condition
        FROM datawarehouse.fact_weather fw
        JOIN datawarehouse.dim_geography dg ON fw.geo_id = dg.geo_id
        JOIN datawarehouse.dim_date dd ON fw.date_id = dd.date_id
        JOIN datawarehouse.dim_time dt ON fw.time_id = dt.time_id
        JOIN datawarehouse.dim_weather_type dwt ON fw.weather_type_id = dwt.weather_type_id
        """

        weather_df = self.execute_query(query)
        if len(weather_df) == 0:
            print("  No data in fact_weather table")
            return weather_df

        print(f"  Shape: {weather_df.shape}")
        print(f"  Date Range: {weather_df['full_date'].min()} to {weather_df['full_date'].max()}")

        # Temperature Analysis
        print(f"\n  Temperature (°C):")
        print(weather_df['temperature_celsius'].describe().round(2))

        # Humidity Analysis
        print(f"\n  Humidity (%):")
        print(weather_df['humidity_percent'].describe().round(2))

        # Cloud Cover Analysis
        print(f"\n  Cloud Cover (%):")
        print(weather_df['cloud_cover_percent'].describe().round(2))

        # Precipitation Analysis
        print(f"\n  Precipitation (mm):")
        precip_stats = weather_df['precipitation_mm'].describe().round(4)
        print(precip_stats)
        precip_nonzero = weather_df[weather_df['precipitation_mm'] > 0]
        print(f"    Days with precipitation: {len(precip_nonzero):,} out of {len(weather_df):,}")
        if len(precip_nonzero) > 0:
            print(f"    Avg precipitation on rainy days: {precip_nonzero['precipitation_mm'].mean():.2f}mm")

        # Wind Speed Analysis
        print(f"\n  Wind Speed (km/h):")
        print(weather_df['wind_speed_kmh'].describe().round(2))

        # Weather condition distribution
        print(f"\n  Weather Condition Distribution:")
        print(weather_df['weather_condition'].value_counts().head(10))

        # Null values
        print(f"\n  Null Values:")
        print(weather_df.isnull().sum())

        self.results["fact_weather"] = weather_df
        return weather_df

    def correlation_analysis(self, gen_df: pd.DataFrame, weather_df: pd.DataFrame) -> None:
        """Analyze correlation between weather and energy generation."""
        print("\n" + "="*80)
        print("CORRELATION ANALYSIS: WEATHER vs ENERGY")
        print("="*80)

        # Merge data on common keys
        merged = gen_df.merge(
            weather_df[['date_id', 'time_id', 'geo_id', 'temperature_celsius',
                       'humidity_percent', 'precipitation_mm', 'cloud_cover_percent', 'wind_speed_kmh']],
            on=['date_id', 'time_id', 'geo_id'],
            how='inner'
        )

        if len(merged) == 0:
            print("  Insufficient data for correlation analysis")
            return

        numeric_cols = ['energy_generated_kwh', 'temperature_celsius', 'humidity_percent',
                       'precipitation_mm', 'cloud_cover_percent', 'wind_speed_kmh']

        corr_matrix = merged[numeric_cols].corr()
        print(f"\n  Correlation with Energy Generation:")
        print(corr_matrix['energy_generated_kwh'].sort_values(ascending=False).round(4))

        # Hourly temperature vs generation
        print(f"\n  Hourly Analysis (Temperature vs Generation):")
        hourly_merged = merged.groupby('hour').agg({
            'energy_generated_kwh': 'mean',
            'temperature_celsius': 'mean',
            'cloud_cover_percent': 'mean'
        }).round(2)
        print(hourly_merged)

    def data_quality_report(self, dims: Dict[str, pd.DataFrame]) -> None:
        """Generate data quality report."""
        print("\n" + "="*80)
        print("DATA QUALITY REPORT")
        print("="*80)

        # Dimension table completeness
        print("\n>>> Dimension Table Completeness:")
        for table_name, df in dims.items():
            null_rate = df.isnull().sum() / len(df)
            print(f"\n  {table_name}:")
            if null_rate.sum() == 0:
                print("    [OK] No null values")
            else:
                print(f"    Columns with nulls:")
                for col, rate in null_rate[null_rate > 0].items():
                    print(f"      - {col}: {rate*100:.2f}%")

        # Fact table referential integrity
        print("\n>>> Referential Integrity Checks:")

        # Check solar energy facts
        gen_count = self.execute_query(
            "SELECT COUNT(*) as cnt FROM datawarehouse.fact_solar_energy_gen"
        )['cnt'].values[0]

        valid_refs = self.execute_query("""
        SELECT COUNT(*) as cnt FROM datawarehouse.fact_solar_energy_gen fse
        WHERE EXISTS (SELECT 1 FROM datawarehouse.dim_solar_site ds WHERE ds.site_id = fse.site_id)
        AND EXISTS (SELECT 1 FROM datawarehouse.dim_geography dg WHERE dg.geo_id = fse.geo_id)
        AND EXISTS (SELECT 1 FROM datawarehouse.dim_date dd WHERE dd.date_id = fse.date_id)
        AND EXISTS (SELECT 1 FROM datawarehouse.dim_time dt WHERE dt.time_id = fse.time_id)
        """)['cnt'].values[0]

        print(f"  fact_solar_energy_gen: {valid_refs:,} / {gen_count:,} valid references")
        if valid_refs == gen_count:
            print("    [OK] All references valid")
        else:
            print(f"    [ERROR] {gen_count - valid_refs:,} orphaned records")

    def generate_summary(self) -> None:
        """Print analysis summary."""
        print("\n" + "="*80)
        print("ANALYSIS SUMMARY")
        print("="*80)
        print(f"\nAnalyzed {len(self.results)} tables")
        print("Key metrics:")

        if "fact_solar_energy_gen" in self.results:
            gen_df = self.results["fact_solar_energy_gen"]
            print(f"  - Total energy records: {len(gen_df):,}")
            print(f"  - Date range: {gen_df['full_date'].min()} to {gen_df['full_date'].max()}")
            print(f"  - Total generation: {gen_df['energy_generated_kwh'].sum():,.0f} kWh")
            print(f"  - Average generation: {gen_df['energy_generated_kwh'].mean():.2f} kWh")

    def run_full_analysis(self) -> Dict[str, pd.DataFrame]:
        """Execute complete analysis pipeline."""
        print("\nStarting Warehouse Descriptive Statistics Analysis...")

        dims = self.analyze_dimension_tables()
        gen_df = self.analyze_fact_solar_energy(dims)
        weather_df = self.analyze_fact_weather(dims)

        if len(weather_df) > 0:
            self.correlation_analysis(gen_df, weather_df)

        self.data_quality_report(dims)
        self.generate_summary()

        print("\n" + "="*80)
        print("Analysis Complete!")
        print("="*80 + "\n")

        return self.results


def main():
    """Main entry point."""
    analytics = WarehouseAnalytics(engine)
    results = analytics.run_full_analysis()
    return results


if __name__ == "__main__":
    main()
