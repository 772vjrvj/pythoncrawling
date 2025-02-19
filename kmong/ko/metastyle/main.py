from googleapiclient.discovery import build
from google.oauth2 import service_account

# Google Drive API 인증
SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "credentials.json"  # 서비스 계정 JSON 파일

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=creds)

# ✅ 폴더 ID
FOLDER_ID = "0ADz3hcOEyJ4lUk9PVA"

# ✅ 폴더 정보 가져오기 테스트
try:
    folder = drive_service.files().get(fileId=FOLDER_ID, fields="id, name").execute()
    print(f"✅ 폴더 접근 가능! 폴더명: {folder['name']}")
except Exception as e:
    print(f"❌ 폴더 접근 실패: {e}")
