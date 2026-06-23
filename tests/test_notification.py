import os
import sys
import requests

# Đảm bảo console có thể in tiếng Việt UTF-8 (đặc biệt hữu ích khi test local trên Windows)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Thử load biến môi trường từ file .env (hỗ trợ test local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def send_notification():
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        print("❌ LỖI: Không tìm thấy biến môi trường DISCORD_WEBHOOK_URL.")
        sys.exit(1)
        
    payload = {
        "embeds": [{
            "title": "✅ TEST HỆ THỐNG GITHUB ACTIONS & WEBHOOK",
            "description": "Tin nhắn này xác nhận GitHub Actions đã đọc được Secret và bắn webhook thành công sang Discord.\n\n**Trạng thái:** Sẵn sàng cho Data Pipeline chính!",
            "color": 3447003, # Mã màu xanh dương
            "footer": {"text": "Kho dữ liệu Năng lượng Mặt trời - Discord Notification Dry-run"}
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Đã bắn tin nhắn test sang Discord thành công!")
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi khi gửi webhook sang Discord: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("==== BẮT ĐẦU TEST DISCORD WEBHOOK ====")
    send_notification()
    print("==== KẾT THÚC TEST ====")
