import os
import sys
import time
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
        print("⚠️ Cảnh báo: Không tìm thấy DISCORD_WEBHOOK_URL, bỏ qua việc gửi thông báo Discord.")
        return

    # Xanh lá nếu thành công, Đỏ nếu thất bại
    color = 3066993 if status == "SUCCESS" else 15158332
    
    payload = {
        "embeds": [{
            "title": "🔄 BÁO CÁO ETL TEST: REFRESH MATERIALIZED VIEW",
            "description": message,
            "color": color,
            "footer": {"text": "Dự án Năng lượng Mặt trời - Automation CI/CD"}
        }]
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Đã bắn thông báo trạng thái ETL qua Discord.")
    except Exception as e:
        print(f"❌ Lỗi khi gửi webhook sang Discord: {e}")

def run_etl_refresh_test():
    print("==== BẮT ĐẦU CHẠY THỬ LUỒNG ETL REFRESH MV VÀ WEBHOOK ====")
    
    # Lưu ý: Thay tên 'bi_mart.mv_example_view' bằng tên MV thực tế trong Supabase
    mv_name = "bi_mart.mv_example_view"
    
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    if not all([db_host, db_name, db_user, db_password]):
        print("❌ Lỗi: Thiếu thông tin kết nối DB (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD).")
        sys.exit(1)

    start_time = time.time()
    try:
        print(f"🔌 Đang kết nối tới CSDL Supabase: {db_host}...")
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print(f"⚙️ Đang thực thi lệnh SQL: REFRESH MATERIALIZED VIEW {mv_name}; ...")
        try:
            cursor.execute(f"REFRESH MATERIALIZED VIEW {mv_name};")
            duration = round(time.time() - start_time, 2)
            msg = f"✅ **Trạng thái:** THÀNH CÔNG\n📌 **Hành động:** `REFRESH MATERIALIZED VIEW {mv_name}`\n⏱ **Thời gian xử lý:** `{duration}s`\n\nQuá trình làm mới Data Mart thành công. Dữ liệu BI đã sẵn sàng để truy vấn!"
            print(f"✅ Refresh thành công trong {duration}s.")
            send_discord_webhook("SUCCESS", msg)
            
        except psycopg2.errors.UndefinedTable as query_error:
            # Xử lý ngoại lệ an toàn nếu bảng/MV chưa được tạo trong CSDL
            error_msg = str(query_error).strip()
            print(f"⚠️ View chưa tồn tại trên DB. Chi tiết: {error_msg}")
            msg = f"⚠️ **Trạng thái:** BỎ QUA\n📌 **Hành động:** Khớp nối ETL & Webhook\n📝 **Chi tiết:** View `{mv_name}` chưa tồn tại trên Supabase, nhưng luồng kịch bản Test (từ DB -> Discord) vẫn thông suốt!"
            send_discord_webhook("SUCCESS", msg)

        cursor.close()
        conn.close()

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        error_details = str(e).strip()
        print(f"❌ Quá trình ETL gặp lỗi: {error_details}")
        
        msg = f"❌ **Trạng thái:** THẤT BẠI\n📌 **Tiến trình:** Kết nối DB & Refresh MV\n⏱ **Thời gian xử lý:** `{duration}s`\n⚠️ **Chi tiết lỗi:**\n```sql\n{error_details[:500]}\n```"
        send_discord_webhook("ERROR", msg)
        sys.exit(1)

if __name__ == "__main__":
    run_etl_refresh_test()
    print("==== KẾT THÚC LUỒNG TEST ====")
