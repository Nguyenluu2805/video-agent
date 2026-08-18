import os
from dotenv import load_dotenv
from google import genai
import time

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Thiếu GEMINI_API_KEY trong file .env")

client = genai.Client(api_key=api_key)

def analyze_video_content(video_data):
    """
    Gửi nội dung video (Text hoặc Audio) cho Gemini phân tích.
    """
    system_prompt = """Bạn là một Trợ giảng (Teaching Assistant) chuyên đánh giá chất lượng làm việc nhóm của sinh viên.
Dựa vào nội dung cuộc họp nhóm (âm thanh hoặc phụ đề), hãy đưa ra nhận xét ngắn gọn, súc tích.
Tiêu chí nhận xét bắt buộc phải đánh giá rõ 5 yếu tố sau:
- Tương tác nhóm: (Nhận xét về việc có tương tác với nhau giữa các thành viên không?)
- Kiểm tra bài tập: (Nhận xét về việc có thực hiện kiểm tra bài tập về nhà không?)
- Demo code: (Nhận xét về việc có demo code không?)
- Thảo luận vấn đề: (Nhận xét về việc có hỏi đáp và thảo luận về các vấn đề/khó khăn không?)
- **Đánh giá chung:** (Chỉ một câu ngắn gọn gọn chốt lại tinh thần làm việc, ví dụ: "Buổi làm việc nhóm diễn ra hiệu quả, đúng trọng tâm và thể hiện tinh thần học tập, hỗ trợ lẫn nhau rất cao. Nhóm tiếp tục phát huy cách làm việc này trong các buổi tiếp theo!")
Giọng văn: Khách quan, chuyên nghiệp và mang tính xây dựng đúng chuẩn của một trợ giảng."""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            if video_data['type'] == 'text':
                # Phân tích qua văn bản
                prompt = f"{system_prompt}\n\nDưới đây là phụ đề của video:\n{video_data['content']}"
                response = client.models.generate_content(
                    model='gemini-3.5-flash-lite',
                    contents=prompt,
                )
                return response.text.strip()
                
            elif video_data['type'] == 'audio':
                # Phân tích qua file âm thanh
                audio_path = video_data['path']
                print(f"Đang tải lên file âm thanh {audio_path} cho Gemini...")
                
                # Tải file lên Gemini
                uploaded_file = client.files.upload(file=audio_path)
                
                # Chờ Gemini xử lý file
                print("Đã tải lên xong. Đang chờ Gemini xử lý file", end="")
                while uploaded_file.state.name == "PROCESSING":
                    print(".", end="", flush=True)
                    time.sleep(15)
                    uploaded_file = client.files.get(name=uploaded_file.name)
                print()
                
                if uploaded_file.state.name == "FAILED":
                    raise RuntimeError("Gemini xử lý file thất bại.")
                
                # Gửi yêu cầu phân tích có giới hạn thời gian (chống treo)
                import concurrent.futures
                
                def call_ai():
                    return client.models.generate_content(
                        model='gemini-3.5-flash-lite',
                        contents=[uploaded_file, system_prompt]
                    )
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(call_ai)
                    try:
                        response = future.result(timeout=180) # Giới hạn 3 phút
                    except concurrent.futures.TimeoutError:
                        raise RuntimeError("AI phản hồi quá lâu (Timeout 3 phút). Máy chủ Google có thể đang quá tải.")
                
                # Xóa file sau khi phân tích xong để dọn dẹp
                client.files.delete(name=uploaded_file.name)
                os.remove(audio_path)
                
                return response.text.strip()
                
        except Exception as e:
            error_msg = str(e)
            if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
                if attempt < max_retries - 1:
                    print(f"⚠️ Bị giới hạn API (Rate Limit 429). Chờ 40 giây rồi thử lại (Lần {attempt+1}/{max_retries})...")
                    time.sleep(40)
                    continue
            return f"Lỗi phân tích AI: {error_msg}"
