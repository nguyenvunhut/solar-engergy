#!/usr/bin/env python3
"""Unified Database Initializer.
Replaces the scattered script files with a single entry point for setting up database schemas.
"""

import argparse
from pathlib import Path
import sys
import importlib.util

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def load_module(filename: str, module_name: str, folder: str = ""):
    module_path = PROJECT_ROOT / "srcs" / folder / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

db_utils = load_module("01_database.py", "database", folder="00_utils")

def execute_sql_file(conn, sql_filename: str):
    sql_file = Path(__file__).parent / "sql" / sql_filename
    if not sql_file.is_file():
        print(f"[ERROR] Cannot find SQL file: {sql_file}")
        return False
    
    try:
        print(f"  -> Executing {sql_filename}...")
        with conn.cursor() as cur:
            cur.execute(sql_file.read_text(encoding="utf-8"))
        conn.commit()
        return True
    except Exception as exc:
        conn.rollback()
        print(f"  [ERROR] Lỗi khi chạy {sql_filename}: {exc}")
        return False

def run(args: argparse.Namespace) -> int:
    conn = db_utils.get_psycopg2_connection()
    success = True
    print("=== DATABASE INITIALIZATION ===")
    
    if args.staging or args.all:
        print("\n[1/3] Khởi tạo bảng Staging...")
        if not execute_sql_file(conn, "create_staging.sql"): success = False

    if args.buffers or args.all:
        print("\n[2/3] Khởi tạo bảng Buffers...")
        if not execute_sql_file(conn, "create_buffers.sql"): success = False

    if args.dwh or args.all:
        print("\n[3/3] Khởi tạo bảng Data Warehouse...")
        if not execute_sql_file(conn, "create_datawarehouse.sql"): success = False

    if args.drop_staging:
        print("\n[!] Đang xóa toàn bộ bảng Staging...")
        try:
            with conn.cursor() as cur:
                cur.execute("DROP SCHEMA IF EXISTS staging CASCADE;")
            conn.commit()
            print("  -> Đã xóa thành công Schema Staging!")
        except Exception as e:
            print(f"  [ERROR] {e}")
            success = False

    conn.close()
    
    if success:
        print("\n[OK] Hoàn tất quá trình khởi tạo Database!")
        return 0
    else:
        print("\n[FAILED] Quá trình có lỗi xảy ra.")
        return 1

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified script to initialize Database structures.")
    parser.add_argument("--staging", action="store_true", help="Chỉ tạo bảng Staging")
    parser.add_argument("--buffers", action="store_true", help="Chỉ tạo bảng Buffers")
    parser.add_argument("--dwh", action="store_true", help="Chỉ tạo bảng Data Warehouse")
    parser.add_argument("--all", action="store_true", help="Tạo TOÀN BỘ các bảng (Staging -> Buffers -> DWH)")
    parser.add_argument("--drop-staging", action="store_true", help="Xóa Schema Staging")
    return parser.parse_args()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Nếu không truyền tham số, mặc định chạy `--all` để thuận tiện
        sys.argv.append("--all")
    sys.exit(run(parse_args()))
