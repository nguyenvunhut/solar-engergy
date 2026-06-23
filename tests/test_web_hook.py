import os
import requests
import sys

# Đảm bảo console Windows có thể in tiếng Việt (UnicodeEncodeError)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Thử load biến môi trường từ file .env (khi chạy local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
def send_test_alert():
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        print("❌ LỖI: Không tìm thấy DISCORD_WEBHOOK_URL trong biến môi trường.")
        sys.exit(1)
        
    payload = {
        "embeds": [{
            "title": "🧪 TEST HỆ THỐNG GITHUB ACTIONS & WEBHOOK",
            "description": "Tin nhắn này xác nhận GitHub Actions của nhóm đã đọc được Secret và kết nối thành công với Discord.\n\n**Trạng thái:** Sẵn sàng tích hợp vào luồng Data Pipeline chính!",
            "color": 3447003, # Mã màu xanh dương an toàn
            "footer": {"text": "Dự án Kho dữ liệu Năng lượng - The Outliers"}
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Đã bắn tin nhắn test sang Discord thành công!")
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi khi gửi webhook: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("==== BẮT ĐẦU TEST WEBHOOK ====")
    send_test_alert()
    print("==== KẾT THÚC TEST ====")