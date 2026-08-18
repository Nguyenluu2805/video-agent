import sys
sys.stdout.reconfigure(encoding='utf-8')
from video_processor import process_youtube
from ai_agent import analyze_video_content

def test():
    # Thử với một video YouTube (có thể sửa thành video khác)
    # Ví dụ một video ngắn: https://www.youtube.com/watch?v=jNQXAC9IVRw (Me at the zoo)
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    
    print(f"\n[1] Đang xử lý video: {url}")
    try:
        video_data = process_youtube(url)
        print(f"-> Phương thức trích xuất: {video_data['type']}")
        
        print("\n[2] Đang gửi cho AI phân tích...")
        result = analyze_video_content(video_data)
        
        print("\n========= NHẬN XÉT CỦA AI =========")
        print(result)
        print("===================================\n")
        
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    test()
