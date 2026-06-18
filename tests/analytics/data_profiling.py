"""
Data profiling and export utilities for warehouse analysis.
Generate summary reports and export analysis results.
"""

import os
import ssl
from pathlib import Path
from typing import Dict, List
from datetime import datetime

import numpy as np
import pandas as pd
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


class DataProfiler:
    """Comprehensive data profiling for warehouse tables."""

    def __init__(self, engine):
        self.engine = engine

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query."""
        return pd.read_sql_query(query, con=self.engine)

    def profile_numeric_column(self, table: str, column: str, schema: str = "datawarehouse") -> Dict:
        """Generate profile for numeric column."""
        query = f"""
        SELECT
            COUNT(*) as count,
            COUNT(DISTINCT {column}) as unique_count,
            COUNT(*) - COUNT({column}) as null_count,
            MIN({column}) as min_val,
            MAX({column}) as max_val,
            AVG({column}) as mean_val,
            STDDEV({column}) as stddev_val,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {column}) as q1,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {column}) as median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {column}) as q3
        FROM {schema}.{table}
        WHERE {column} IS NOT NULL
        """

        result = self.execute_query(query).iloc[0]
        return result.to_dict()

    def profile_categorical_column(self, table: str, column: str, schema: str = "datawarehouse", top_n: int = 10) -> Dict:
        """Generate profile for categorical column."""
        profile = {}

        # Basic stats
        query_stats = f"""
        SELECT
            COUNT(*) as count,
            COUNT(DISTINCT {column}) as unique_count,
            COUNT(*) - COUNT({column}) as null_count
        FROM {schema}.{table}
        """
        stats = self.execute_query(query_stats).iloc[0].to_dict()
        profile.update(stats)

        # Top values
        query_top = f"""
        SELECT {column}, COUNT(*) as freq
        FROM {schema}.{table}
        WHERE {column} IS NOT NULL
        GROUP BY {column}
        ORDER BY freq DESC
        LIMIT {top_n}
        """
        top_vals = self.execute_query(query_top)
        profile['top_values'] = top_vals.to_dict('records')

        return profile

    def generate_table_profile(self, table: str, schema: str = "datawarehouse") -> Dict:
        """Generate comprehensive profile for a table."""
        print(f"\nProfiling {schema}.{table}...")

        profile = {
            'table': table,
            'schema': schema,
            'timestamp': datetime.now().isoformat(),
            'columns': {}
        }

        # Get column info
        query = f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = '{schema}' AND table_name = '{table}'
        ORDER BY ordinal_position
        """

        columns = self.execute_query(query)
        numeric_types = {'bigint', 'integer', 'smallint', 'numeric', 'real', 'double precision'}
        datetime_types = {'timestamp', 'date', 'time'}

        for _, col in columns.iterrows():
            col_name = col['column_name']
            col_type = col['data_type']
            is_null = col['is_nullable'] == 'YES'

            col_profile = {
                'type': col_type,
                'nullable': is_null
            }

            if any(dt in col_type for dt in numeric_types):
                col_profile.update(self.profile_numeric_column(table, col_name, schema))
            elif any(dt in col_type for dt in datetime_types):
                col_profile['profile_type'] = 'datetime'
            else:
                col_profile.update(self.profile_categorical_column(table, col_name, schema))

            profile['columns'][col_name] = col_profile

        return profile

    def generate_all_profiles(self, schema: str = "datawarehouse") -> Dict[str, Dict]:
        """Generate profiles for all tables in schema."""
        print(f"\nGenerating profiles for all tables in {schema}...")

        query = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{schema}'
        ORDER BY table_name
        """

        tables = self.execute_query(query)['table_name'].tolist()
        profiles = {}

        for table in tables:
            try:
                profiles[table] = self.generate_table_profile(table, schema)
            except Exception as e:
                print(f"  Error profiling {table}: {e}")
                profiles[table] = {'error': str(e)}

        return profiles

    def export_profiles_to_csv(self, profiles: Dict[str, Dict], output_dir: str = "./analysis_output") -> None:
        """Export profiles to CSV files."""
        Path(output_dir).mkdir(exist_ok=True)

        summary_data = []
        for table_name, profile in profiles.items():
            if 'error' in profile:
                continue

            for col_name, col_profile in profile.get('columns', {}).items():
                row = {
                    'table': table_name,
                    'column': col_name,
                    'type': col_profile.get('type', ''),
                    'count': col_profile.get('count', ''),
                    'unique': col_profile.get('unique_count', ''),
                    'nulls': col_profile.get('null_count', ''),
                    'min': col_profile.get('min_val', ''),
                    'max': col_profile.get('max_val', ''),
                    'mean': col_profile.get('mean_val', ''),
                    'stddev': col_profile.get('stddev_val', ''),
                }
                summary_data.append(row)

        summary_df = pd.DataFrame(summary_data)
        output_file = Path(output_dir) / "data_profile_summary.csv"
        summary_df.to_csv(output_file, index=False)
        print(f"\nExported profile to {output_file}")


class AnalysisReportGenerator:
    """Generate structured analysis reports."""

    def __init__(self, engine):
        self.engine = engine
        self.sections = []

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query."""
        return pd.read_sql_query(query, con=self.engine)

    def add_section(self, title: str, content: str) -> None:
        """Add section to report."""
        self.sections.append({
            'title': title,
            'content': content
        })

    def generate_markdown_report(self, profiles: Dict[str, Dict], output_file: str = "warehouse_analysis_report.md") -> None:
        """Generate markdown report."""
        report = f"""# Warehouse Descriptive Statistics Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

This report provides comprehensive descriptive statistics and data quality analysis for the solar energy warehouse.

## Data Overview

"""
        # Get overview stats
        query_tables = """
        SELECT table_name,
               (SELECT count(*) FROM information_schema.columns
                WHERE table_schema = 'datawarehouse' AND t.table_name = table_name) as col_count
        FROM information_schema.tables t
        WHERE table_schema = 'datawarehouse'
        ORDER BY table_name
        """

        tables = self.execute_query(query_tables)
        report += "### Tables\n\n"
        for _, row in tables.iterrows():
            report += f"- **{row['table_name']}**: {row['col_count']} columns\n"

        # Add data quality section based on profiles
        report += "\n## Data Quality Overview\n\n"
        for table_name, profile in profiles.items():
            if 'error' in profile:
                continue

            report += f"### {table_name}\n\n"
            report += "| Column Name | Data Type | Null % | Unique Values |\n"
            report += "|---|---|---|---|\n"

            for col_name, col_profile in profile.get('columns', {}).items():
                null_pct = (col_profile.get('null_count', 0) / col_profile.get('count', 1)) * 100 if col_profile.get('count') else 0
                report += f"| {col_name} | {col_profile.get('type', 'N/A')} | {null_pct:.2f}% | {col_profile.get('unique_count', 'N/A')} |\n"
            report += "\n"

        # Add sections if any exist
        if self.sections:
            report += "\n## Detailed Analysis\n\n"
            for section in self.sections:
                report += f"### {section['title']}\n\n{section['content']}\n\n"

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"Report generated: {output_file}")

    def generate_html_report(self, profiles: Dict[str, Dict], output_file: str = "warehouse_analysis_report.html") -> None:
        """Generate HTML report with interactive tables."""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Warehouse Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ background-color: white; margin: 20px 0; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th {{ background-color: #34495e; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
        tr:hover {{ background-color: #f8f9fa; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #3498db; }}
        .metric-label {{ color: #7f8c8d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Solar Energy Warehouse Analysis Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="section">
        <h2>Data Quality Overview</h2>
"""

        # Add table profiles
        for table_name, profile in profiles.items():
            if 'error' in profile:
                continue

            html_content += f"""
        <h3>{table_name}</h3>
        <table>
            <tr>
                <th>Column Name</th>
                <th>Data Type</th>
                <th>Null %</th>
                <th>Unique Values</th>
            </tr>
"""
            for col_name, col_profile in profile.get('columns', {}).items():
                null_pct = (col_profile.get('null_count', 0) / col_profile.get('count', 1)) * 100 if col_profile.get('count') else 0
                html_content += f"""
            <tr>
                <td>{col_name}</td>
                <td>{col_profile.get('type', 'N/A')}</td>
                <td>{null_pct:.2f}%</td>
                <td>{col_profile.get('unique_count', 'N/A')}</td>
            </tr>
"""
            html_content += "        </table>\n"

        html_content += """
    </div>
</body>
</html>
"""

        with open(output_file, 'w') as f:
            f.write(html_content)

        print(f"HTML report generated: {output_file}")


def main():
    """Generate all profiles and reports."""
    print("Starting data profiling and report generation...")

    profiler = DataProfiler(engine)
    profiles = profiler.generate_all_profiles()
    profiler.export_profiles_to_csv(profiles)

    report_gen = AnalysisReportGenerator(engine)
    report_gen.generate_html_report(profiles)

    print("\nProfiling complete!")


if __name__ == "__main__":
    main()
