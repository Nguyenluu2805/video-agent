import time
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
sys.stdout.reconfigure(encoding='utf-8')

from sheet_manager import SheetManager
from video_processor import process_video
from ai_agent import analyze_video_content

# Tên file Google Sheets bạn muốn kết nối (phải được share quyền với Service Account)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1gwl8-0ppnQwouHA9F6CylzTPSLKo072FIvGLC1QaCWo/edit?gid=0#gid=0"
CREDENTIALS_PATH = "credentials.json"

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Robot is running 24/7!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

def process_all_videos():
    try:
        print("Đang kết nối với Google Sheets...")
        manager = SheetManager(SHEET_URL, CREDENTIALS_PATH)
    except Exception as e:
        print(f"Lỗi khởi tạo SheetManager: {e}")
        return

    videos = manager.get_unprocessed_videos()
    if not videos:
        print("Không có video nào cần xử lý lúc này.")
        return

    print(f"Tìm thấy {len(videos)} video cần xử lý.")

    for item in videos:
        row_idx = item['row_index']
        url = item['url']
        print(f"\n[{row_idx}] Đang xử lý: {url}")
        
        try:
            # 1. Tải video / Lấy transcript
            manager.update_result(row_idx, "Đang xử lý", "")
            video_data = process_video(url)
            
            # 2. Gửi cho AI phân tích
            manager.update_result(row_idx, "Đang phân tích AI", "")
            comment = analyze_video_content(video_data)
            
            # 3. Ghi kết quả
            manager.update_result(row_idx, "Thành công", comment)
            print(f"✅ Hoàn thành: {url}")
            
        except Exception as e:
            print(f"❌ Lỗi xử lý {url}: {e}")
            manager.update_result(row_idx, "Lỗi", str(e))
            
        # Nghỉ 5 giây giữa các lượt để tránh bị rate limit (nếu có)
        time.sleep(5)

def main():
    # Khôi phục file cookies.txt từ biến môi trường (nếu có) để vượt qua bộ lọc bot của YouTube
    youtube_cookies = os.environ.get("YOUTUBE_COOKIES")
    if youtube_cookies:
        with open("cookies.txt", "w", encoding="utf-8") as f:
            f.write(youtube_cookies)
            
    # Bật server ảo luồng phụ để Render Web Service không bị báo lỗi cổng
    server_thread = threading.Thread(target=run_dummy_server, daemon=True)
    server_thread.start()
    
    check_interval = 300 # 5 phút
    
    print("🤖 Robot tự động chấm điểm đã khởi động! Sẵn sàng trực 24/7.")
    print(f"⏳ Cứ mỗi {check_interval//60} phút hệ thống sẽ tự động quét Google Sheet một lần.")
    
    while True:
        print("\n" + "="*50)
        print(f"🔄 Bắt đầu chu kỳ quét mới: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        process_all_videos()
        
        print(f"💤 Chu kỳ hoàn tất. Robot vào chế độ ngủ. Sẽ quét lại sau {check_interval//60} phút nữa...")
        time.sleep(check_interval)

if __name__ == "__main__":
    main()
