import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

class SheetManager:
    def __init__(self, sheet_url, credentials_path="credentials.json"):
        """Khởi tạo kết nối tới Google Sheets qua URL"""
        self.scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        import json
        
        # Thử đọc từ biến môi trường (khi chạy trên Cloud)
        google_creds_json = os.getenv("GOOGLE_CREDENTIALS")
        if google_creds_json:
            creds_dict = json.loads(google_creds_json)
            self.creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, self.scope)
        else:
            # Chạy ở máy local
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"Không tìm thấy file {credentials_path} và không có biến môi trường GOOGLE_CREDENTIALS.")
            self.creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, self.scope)
            
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_url(sheet_url).sheet1

    def get_unprocessed_videos(self):
        """Lấy danh sách các dòng có URL ở cột 4 nhưng chưa có Nhận xét ở cột 7"""
        values = self.sheet.get_all_values()
        unprocessed = []
        for i, row in enumerate(values):
            # Bỏ qua dòng tiêu đề (nếu có)
            if i == 0 and ("Tên" in row[0] or "Nhóm" in row[0]):
                continue
                
            # Đảm bảo dòng có đủ dữ liệu tới cột URL (cột 4, index 3)
            if len(row) > 3:
                url = row[3].strip()
                # Kiểm tra nếu là link hợp lệ (youtube hoặc drive)
                if url.startswith("http"):
                    # Cột Nhận Xét sẽ nằm ở cột 7 (index 6)
                    comment = row[6].strip() if len(row) > 6 else ""
                    # Nếu chưa có nhận xét (hoặc đang báo lỗi), ta đưa vào danh sách cần xử lý
                    if not comment or comment.startswith("Đang") or comment.startswith("Lỗi"):
                        unprocessed.append({
                            'row_index': i + 1, # Index trong Google Sheets bắt đầu từ 1
                            'url': url
                        })
        return unprocessed

    def update_result(self, row_index, status, comment):
        """Cập nhật kết quả vào Google Sheets (Chỉ ghi vào cột cuối - cột 7)"""
        # Nếu có comment (Thành công), ghi comment. Nếu không, ghi status để báo quá trình.
        text_to_write = comment if comment else status
        self.sheet.update_cell(row_index, 7, text_to_write)
