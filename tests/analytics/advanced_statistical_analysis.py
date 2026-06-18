"""
Advanced statistical analysis for warehouse data.
Includes distribution analysis, outlier detection preparation, and time-series patterns.
"""

import os
import ssl
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from dotenv import load_dotenv
from sqlalchemy import create_engine

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


class DistributionAnalyzer:
    """Statistical distribution analysis of warehouse data."""

    def __init__(self, engine):
        self.engine = engine

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query."""
        return pd.read_sql_query(query, con=self.engine)

    def analyze_energy_distribution(self) -> None:
        """Analyze energy generation distribution by site and time."""
        print("\n" + "="*80)
        print("ENERGY GENERATION DISTRIBUTION ANALYSIS")
        print("="*80)

        query = """
        SELECT
            ds.campus_name,
            dt.hour,
            fse.energy_generated_kwh
        FROM datawarehouse.fact_solar_energy_gen fse
        JOIN datawarehouse.dim_solar_site ds ON fse.site_id = ds.site_id
        JOIN datawarehouse.dim_time dt ON fse.time_id = dt.time_id
        WHERE fse.energy_generated_kwh IS NOT NULL
        """

        df = self.execute_query(query)
        print(f"\nTotal non-null energy records: {len(df):,}")

        # Overall distribution
        print("\n>>> Overall Energy Distribution:")
        energy = df['energy_generated_kwh']
        print(f"  Mean: {energy.mean():.4f} kWh")
        print(f"  Median: {energy.median():.4f} kWh")
        print(f"  Std Dev: {energy.std():.4f} kWh")
        print(f"  Skewness: {stats.skew(energy):.4f}")
        print(f"  Kurtosis: {stats.kurtosis(energy):.4f}")

        # Percentiles
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        print(f"\n  Percentiles:")
        for p in percentiles:
            val = np.percentile(energy, p)
            print(f"    {p}th: {val:.4f} kWh")

        # Normality test
        _, p_value = stats.normaltest(energy)
        print(f"\n  Normality Test (p-value): {p_value:.6f}")
        print(f"    Distribution is {'normally distributed' if p_value > 0.05 else 'NOT normally distributed'}")

        # By site
        print("\n>>> Distribution by Site:")
        for site in df['campus_name'].unique():
            site_energy = df[df['campus_name'] == site]['energy_generated_kwh']
            print(f"\n  {site}:")
            print(f"    Count: {len(site_energy):,}")
            print(f"    Mean: {site_energy.mean():.4f}")
            print(f"    Std: {site_energy.std():.4f}")
            print(f"    CV: {(site_energy.std() / site_energy.mean()):.4f}")  # Coefficient of variation

        # By hour
        print("\n>>> Distribution by Hour (Peak Analysis):")
        hourly = df.groupby('hour')['energy_generated_kwh'].agg([
            ('mean', 'mean'),
            ('std', 'std'),
            ('min', 'min'),
            ('max', 'max'),
            ('count', 'count'),
            ('cv', lambda x: x.std() / x.mean() if x.mean() > 0 else np.nan)
        ]).round(4)
        print(hourly.sort_values('mean', ascending=False).head(10))

    def outlier_analysis(self) -> None:
        """Prepare outlier detection analysis."""
        print("\n" + "="*80)
        print("OUTLIER DETECTION PREPARATION")
        print("="*80)

        query = """
        SELECT
            fse.gen_id, fse.site_id, fse.date_id, fse.time_id,
            fse.energy_generated_kwh,
            ds.campus_name, dt.hour, dd.month,
            CASE
                WHEN dt.hour >= 6 AND dt.hour < 18 THEN 'Day'
                ELSE 'Night'
            END as period
        FROM datawarehouse.fact_solar_energy_gen fse
        JOIN datawarehouse.dim_solar_site ds ON fse.site_id = ds.site_id
        JOIN datawarehouse.dim_time dt ON fse.time_id = dt.time_id
        JOIN datawarehouse.dim_date dd ON fse.date_id = dd.date_id
        WHERE fse.energy_generated_kwh IS NOT NULL
        """

        df = self.execute_query(query)

        # IQR method
        print("\n>>> IQR Method (Outliers beyond 1.5*IQR):")
        Q1 = df['energy_generated_kwh'].quantile(0.25)
        Q3 = df['energy_generated_kwh'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = df[
            (df['energy_generated_kwh'] < lower_bound) |
            (df['energy_generated_kwh'] > upper_bound)
        ]

        print(f"  IQR: {IQR:.4f}")
        print(f"  Bounds: [{lower_bound:.4f}, {upper_bound:.4f}]")
        print(f"  Outliers: {len(outliers):,} ({len(outliers)/len(df)*100:.2f}%)")

        # Z-score method
        print("\n>>> Z-Score Method (|z| > 3):")
        z_scores = np.abs(stats.zscore(df['energy_generated_kwh']))
        z_outliers = df[z_scores > 3]
        print(f"  Z-score outliers: {len(z_outliers):,} ({len(z_outliers)/len(df)*100:.2f}%)")

        # By site and hour
        print("\n>>> Anomalies by Site and Hour:")
        anomaly_counts = df.groupby(['campus_name', 'hour']).apply(
            lambda x: len(x[(
                (x['energy_generated_kwh'] < lower_bound) |
                (x['energy_generated_kwh'] > upper_bound)
            )]) if len(x) > 0 else 0
        )
        top_anomalies = anomaly_counts[anomaly_counts > 0].sort_values(ascending=False)
        if len(top_anomalies) > 0:
            print(top_anomalies.head(10))
        else:
            print("  No anomalies detected with IQR method")

        # Daytime vs nighttime
        print("\n>>> Daytime vs Nighttime Analysis:")
        for period in ['Day', 'Night']:
            period_data = df[df['period'] == period]['energy_generated_kwh']
            print(f"\n  {period}:")
            print(f"    Count: {len(period_data):,}")
            print(f"    Mean: {period_data.mean():.4f} kWh")
            print(f"    Std: {period_data.std():.4f} kWh")
            print(f"    Max: {period_data.max():.4f} kWh")

    def time_series_patterns(self) -> None:
        """Analyze time-series patterns in energy generation."""
        print("\n" + "="*80)
        print("TIME-SERIES PATTERNS ANALYSIS")
        print("="*80)

        query = """
        SELECT
            dd.full_date,
            dt.hour,
            ds.campus_name,
            SUM(fse.energy_generated_kwh) as daily_energy,
            AVG(fse.energy_generated_kwh) as avg_energy,
            COUNT(*) as record_count,
            COUNT(CASE WHEN fse.energy_generated_kwh IS NOT NULL THEN 1 END) as non_null_count
        FROM datawarehouse.fact_solar_energy_gen fse
        JOIN datawarehouse.dim_solar_site ds ON fse.site_id = ds.site_id
        JOIN datawarehouse.dim_time dt ON fse.time_id = dt.time_id
        JOIN datawarehouse.dim_date dd ON fse.date_id = dd.date_id
        GROUP BY dd.full_date, dt.hour, ds.campus_name
        ORDER BY dd.full_date, dt.hour, ds.campus_name
        """

        df = self.execute_query(query)
        df['full_date'] = pd.to_datetime(df['full_date'])

        print(f"\nTotal time-series records: {len(df):,}")
        print(f"Date range: {df['full_date'].min()} to {df['full_date'].max()}")
        print(f"Days covered: {df['full_date'].dt.date.nunique()}")

        # Daily aggregation
        daily_agg = df.groupby(df['full_date'].dt.date).agg({
            'daily_energy': 'sum',
            'avg_energy': 'mean',
            'record_count': 'sum'
        })

        print("\n>>> Daily Energy Totals:")
        print(f"  Mean daily total: {daily_agg['daily_energy'].mean():.2f} kWh")
        print(f"  Std daily total: {daily_agg['daily_energy'].std():.2f} kWh")
        print(f"  Min daily total: {daily_agg['daily_energy'].min():.2f} kWh")
        print(f"  Max daily total: {daily_agg['daily_energy'].max():.2f} kWh")
        print(f"  CV: {(daily_agg['daily_energy'].std() / daily_agg['daily_energy'].mean()):.4f}")

        # Week-over-week patterns
        df['week'] = df['full_date'].dt.isocalendar().week
        df['day_of_week'] = df['full_date'].dt.day_name()

        print("\n>>> Hourly Consistency Across Days:")
        hourly_pattern = df.groupby('hour')['avg_energy'].agg(['mean', 'std', 'min', 'max'])
        print(hourly_pattern.round(4))

        # Data availability
        print("\n>>> Data Availability:")
        null_rate = 1 - (df['non_null_count'] / df['record_count'])
        print(f"  Overall null rate: {null_rate.mean()*100:.2f}%")
        print(f"  Max null rate in any hour: {null_rate.max()*100:.2f}%")
        print(f"  Hours with >50% missing: {len(df[null_rate > 0.5])}")

    def correlation_within_sites(self) -> None:
        """Analyze correlations between sites."""
        print("\n" + "="*80)
        print("INTER-SITE CORRELATION ANALYSIS")
        print("="*80)

        query = """
        SELECT
            dd.full_date,
            ds.campus_name,
            AVG(fse.energy_generated_kwh) as avg_energy
        FROM datawarehouse.fact_solar_energy_gen fse
        JOIN datawarehouse.dim_solar_site ds ON fse.site_id = ds.site_id
        JOIN datawarehouse.dim_date dd ON fse.date_id = dd.date_id
        WHERE fse.energy_generated_kwh IS NOT NULL
        GROUP BY dd.full_date, ds.campus_name
        """

        df = self.execute_query(query)

        if len(df) == 0:
            print("  Insufficient data")
            return

        pivot_df = df.pivot_table(
            index='full_date',
            columns='campus_name',
            values='avg_energy'
        )

        if pivot_df.shape[1] < 2:
            print("  Only one site available")
            return

        print(f"\nCross-site correlation matrix:")
        corr_matrix = pivot_df.corr()
        print(corr_matrix.round(4))

        # Identify strongest correlations
        print(f"\nStrongest correlations (excluding diagonal):")
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                site1, site2 = corr_matrix.columns[i], corr_matrix.columns[j]
                corr_val = corr_matrix.iloc[i, j]
                corr_pairs.append((site1, site2, corr_val))

        corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        for site1, site2, corr_val in corr_pairs[:5]:
            print(f"  {site1} <-> {site2}: {corr_val:.4f}")


def main():
    """Run all advanced analyses."""
    print("Starting Advanced Statistical Analysis...")

    analyzer = DistributionAnalyzer(engine)
    analyzer.analyze_energy_distribution()
    analyzer.outlier_analysis()
    analyzer.time_series_patterns()
    analyzer.correlation_within_sites()

    print("\n" + "="*80)
    print("Advanced Analysis Complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
