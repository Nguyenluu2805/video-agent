from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import os
import uuid
import re
import requests
import http.cookiejar

def get_youtube_id(url):
    parsed = urlparse(url)
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
    elif parsed.hostname in ['youtu.be']:
        return parsed.path[1:]
    elif parsed.hostname in ['www.youtube.com', 'youtube.com'] and parsed.path.startswith('/embed/'):
        return parsed.path.split('/')[2]
    return None

def get_youtube_transcript(video_id):
    session = requests.Session()
    if os.path.exists('cookies.txt'):
        try:
            cj = http.cookiejar.MozillaCookieJar('cookies.txt')
            cj.load(ignore_discard=True, ignore_expires=True)
            session.cookies.update(cj)
        except Exception as e:
            print(f"Lỗi load cookies: {e}")
            
    api = YouTubeTranscriptApi(http_client=session)
    t_list = api.list(video_id)
    # Lấy phụ đề tiếng việt hoặc tiếng anh, ưu tiên cái nào có sẵn
    transcript = t_list.find_transcript(['vi', 'en'])
    data = transcript.fetch()
    return " ".join([t.text for t in data])

def process_video(url):
    video_id = get_youtube_id(url)
    
    if video_id:
        try:
            full_text = get_youtube_transcript(video_id)
            print(f"✅ Đã trích xuất được {len(full_text)} ký tự văn bản từ phụ đề YouTube.")
            return {'type': 'text', 'content': full_text}
        except Exception as e:
            print(f"⚠️ Video YouTube không có phụ đề hoặc bị lỗi lấy phụ đề: {str(e)}")
            raise RuntimeError(f"Không thể lấy phụ đề từ YouTube. Bạn có thể cần bổ sung tính năng tải luồng nếu thực sự video không có phụ đề.")
    else:
        if '/folders/' in url:
            raise RuntimeError("Vui lòng nhập link file video trực tiếp, không sử dụng link thư mục (Folder).")
            
        print("▶️ Link không phải YouTube (Drive). Dùng yt-dlp tải...")
        temp_filename = f"temp_video_{uuid.uuid4().hex[:8]}.mp4"
        ydl_opts = {
            'format': 'best[height<=480]/worst',
            'outtmpl': temp_filename,
            'quiet': True,
            'no_warnings': True
        }
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([url])
                if os.path.exists(temp_filename):
                    print(f"✅ Đã tải xong Audio/Video: {temp_filename}")
                    return {'type': 'audio', 'path': temp_filename}
                else:
                    raise RuntimeError("yt_dlp chạy xong nhưng không thấy file.")
            except Exception as e:
                raise RuntimeError(f"Lỗi khi tải Drive: {str(e)}")
