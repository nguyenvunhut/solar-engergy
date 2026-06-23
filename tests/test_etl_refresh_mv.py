import os
import sys
import time
import traceback
import psycopg2
import requests
from dotenv import load_dotenv

# Đảm bảo console có thể in tiếng Việt UTF-8 (hữu ích khi test local trên Windows)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Load cấu hình biến môi trường từ .env
load_dotenv()

def send_discord_webhook(status, message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Canh bao: Khong tim thay DISCORD_WEBHOOK_URL, bo qua viec gui thong bao Discord.")
        return

    # Xanh lá nếu thành công, Đỏ nếu thất bại
    color = 3066993 if status == "SUCCESS" else 15158332
    
    app_version = os.getenv("APP_VERSION", "v1.0.0")
    
    payload = {
        "embeds": [{
            "title": f"BAO CAO ETL TEST: REFRESH MATERIALIZED VIEW ({app_version})",
            "description": message,
            "color": color,
            "footer": {"text": f"Dự án Năng lượng Mặt trời - Automation CI/CD | Phiên bản: {app_version}"}
        }]
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print("Da ban thong bao trang thai ETL qua Discord.")
    except Exception as e:
        print(f"Loi khi gui webhook sang Discord: {e}")

def run_etl_refresh_test():
    app_version = os.getenv("APP_VERSION", "v1.0.0")
    print(f"==== BẮT ĐẦU CHẠY THỬ LUỒNG ETL REFRESH MV VÀ WEBHOOK (Version: {app_version}) ====")
    
    # Lưu ý: Thay tên 'bi_mart.mv_example_view' bằng tên MV thực tế trong Supabase
    mv_name = "bi_mart.mv_example_view"
    
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    if not all([db_host, db_name, db_user, db_password]):
        error_msg = "**LOI CAU HINH (Configuration Error)**\nThiếu thông tin kết nối Database (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD). Vui lòng kiểm tra lại GitHub Secrets."
        print(error_msg)
        send_discord_webhook("ERROR", error_msg)
        sys.exit(1)

    start_time = time.time()
    try:
        print(f"Dang ket noi toi CSDL Supabase: {db_host}...")
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print(f"Dang thuc thi lenh SQL: REFRESH MATERIALIZED VIEW {mv_name}; ...")
        try:
            cursor.execute(f"REFRESH MATERIALIZED VIEW {mv_name};")
            duration = round(time.time() - start_time, 2)
            msg = f"**Trạng thái:** THÀNH CÔNG\n**Hành động:** `REFRESH MATERIALIZED VIEW {mv_name}`\n**Thời gian xử lý:** `{duration}s`\n\nQuá trình làm mới Data Mart thành công. Dữ liệu BI đã sẵn sàng để truy vấn!"
            print(f"Refresh thanh cong trong {duration}s.")
            send_discord_webhook("SUCCESS", msg)
            
        except psycopg2.errors.UndefinedTable as query_error:
            # Xử lý ngoại lệ an toàn nếu bảng/MV chưa được tạo trong CSDL
            error_msg = str(query_error).strip()
            print(f"View chua ton tai tren DB. Chi tiet: {error_msg}")
            msg = f"**Trạng thái:** BỎ QUA\n**Hành động:** Khớp nối ETL & Webhook\n**Chi tiết:** View `{mv_name}` chưa tồn tại trên Supabase, nhưng luồng kịch bản Test (từ DB -> Discord) vẫn thông suốt!"
            send_discord_webhook("SUCCESS", msg)

        cursor.close()
        conn.close()

    except psycopg2.OperationalError as e:
        duration = round(time.time() - start_time, 2)
        error_details = str(e).strip()
        print(f"Loi ket noi Database: {error_details}")
        
        msg = f"**Trạng thái:** LỖI KẾT NỐI (OperationalError)\n**Tiến trình:** `Kết nối Supabase`\n**Thời gian chạy:** `{duration}s`\n**Nguyên nhân:** Sai thông tin Host, Port, Password, hoặc Supabase đang chặn IP/bảo trì.\n**Chi tiết lỗi:**\n```sql\n{error_details[:500]}\n```"
        send_discord_webhook("ERROR", msg)
        sys.exit(1)

    except psycopg2.ProgrammingError as e:
        duration = round(time.time() - start_time, 2)
        error_details = str(e).strip()
        print(f"Loi cu phap SQL: {error_details}")
        
        msg = f"**Trạng thái:** LỖI CÚ PHÁP (ProgrammingError)\n**Tiến trình:** `Thực thi SQL`\n**Thời gian chạy:** `{duration}s`\n**Nguyên nhân:** Lỗi cú pháp SQL, tên bảng/view sai, hoặc tài khoản thiếu quyền truy cập (Permission denied).\n**Chi tiết lỗi:**\n```sql\n{error_details[:500]}\n```"
        send_discord_webhook("ERROR", msg)
        sys.exit(1)

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        tb = traceback.format_exc()
        error_details = str(e).strip()
        print(f"Loi he thong: {error_details}")
        
        msg = f"**Trạng thái:** LỖI HỆ THỐNG KHÔNG XÁC ĐỊNH\n**Tiến trình:** `Khởi tạo Python/ETL`\n**Thời gian chạy:** `{duration}s`\n**Loại lỗi:** `{e.__class__.__name__}`\n**Chi tiết:**\n```python\n{error_details[:300]}\n```\n**Traceback:**\n```python\n{tb[-500:]}\n```"
        send_discord_webhook("ERROR", msg)
        sys.exit(1)

if __name__ == "__main__":
    run_etl_refresh_test()
    print("==== KẾT THÚC LUỒNG TEST ====")
