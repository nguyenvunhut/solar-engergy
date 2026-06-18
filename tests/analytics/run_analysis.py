"""
Complete analysis runner for warehouse data.
Executes all analysis modules and generates comprehensive reports.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tests.analytics import (
    WarehouseAnalytics,
    DistributionAnalyzer,
    DataProfiler,
    AnalysisReportGenerator,
)
from sqlalchemy import create_engine
import ssl
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

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


def setup_output_directory(base_dir: str = "./analysis_output") -> Path:
    """Create timestamped output directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(base_dir) / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def run_all_analyses(engine, output_dir: Path) -> None:
    """Execute all analysis modules."""

    print("\n" + "=" * 80)
    print("WAREHOUSE DESCRIPTIVE STATISTICS ANALYSIS")
    print("=" * 80)
    print(f"Output Directory: {output_dir}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. Basic Descriptive Statistics
    print("\n[1/4] Running Basic Descriptive Statistics Analysis...")
    print("-" * 80)
    try:
        warehouse_analytics = WarehouseAnalytics(engine)
        results = warehouse_analytics.run_full_analysis()
        print("[OK] Basic analysis complete")
    except Exception as e:
        print(f"[ERROR] Error in basic analysis: {e}")
        results = {}

    # 2. Advanced Statistical Analysis
    print("\n[2/4] Running Advanced Statistical Analysis...")
    print("-" * 80)
    try:
        distribution_analyzer = DistributionAnalyzer(engine)
        distribution_analyzer.analyze_energy_distribution()
        distribution_analyzer.outlier_analysis()
        distribution_analyzer.time_series_patterns()
        distribution_analyzer.correlation_within_sites()
        print("[OK] Advanced analysis complete")
    except Exception as e:
        print(f"[ERROR] Error in advanced analysis: {e}")

    # 3. Data Profiling
    print("\n[3/4] Running Data Profiling...")
    print("-" * 80)
    try:
        profiler = DataProfiler(engine)
        profiles = profiler.generate_all_profiles()
        profiler.export_profiles_to_csv(profiles, str(output_dir))
        print("[OK] Data profiling complete")
    except Exception as e:
        print(f"[ERROR] Error in data profiling: {e}")
        profiles = {}

    # 4. Report Generation
    print("\n[4/4] Generating Reports...")
    print("-" * 80)
    try:
        report_gen = AnalysisReportGenerator(engine)

        # Generate HTML report
        html_output = str(output_dir / "warehouse_analysis_report.html")
        report_gen.generate_html_report(profiles, html_output)

        # Generate markdown report
        md_output = str(output_dir / "warehouse_analysis_report.md")
        report_gen.generate_markdown_report(profiles, md_output)

        print("[OK] Reports generated")
    except Exception as e:
        print(f"[ERROR] Error in report generation: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nOutput files saved to: {output_dir}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nGenerated files:")
    for file in output_dir.iterdir():
        print(f"  - {file.name}")


def main():
    """Main entry point."""
    try:
        output_dir = setup_output_directory()
        run_all_analyses(engine, output_dir)
        print("\n[OK] All analyses completed successfully!")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
