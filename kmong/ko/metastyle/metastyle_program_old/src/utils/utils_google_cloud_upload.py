import os, json, requests, mimetypes
from io import BytesIO
from google.cloud import storage
from google.oauth2 import service_account

class GoogleUploader:
    def __init__(self, log_func):
        if not callable(log_func):
            raise ValueError("log_func must be callable.")
        self.log = log_func

        base_path = os.getcwd()
        self.service_account_path = os.path.join(base_path, "client_secrets.json")
        self.user_config_path = os.path.join(base_path, "user.json")

        with open(self.user_config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)

        self.project_id = user_config.get("project_id")
        self.bucket_name = user_config.get("bucket")

        if not self.project_id or not self.bucket_name:
            raise ValueError("Invalid configuration in user.json")

        credentials = service_account.Credentials.from_service_account_file(self.service_account_path)
        self.client = storage.Client(credentials=credentials, project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)

    def upload(self, obj):
        image_url = obj['image_url']
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = BytesIO(response.content)

            blob_name = f"{obj['brand']}/{obj['category_full']}/{obj['image_name']}"
            mime_type, _ = mimetypes.guess_type(image_url)
            mime_type = mime_type or "application/octet-stream"

            blob = self.bucket.blob(blob_name)
            blob.upload_from_file(image_data, content_type=mime_type)

            # 해당 경로에 있는 모든 이미지 목록 출력 (site_name/category/product_name/ 경로)
            # blobs = list(bucket.list_blobs(prefix=f"{site_name}"))  # 경로 내의 모든 파일 나열
            # if any(blob.name == blob_name for blob in blobs):
            #     self.log_signal.emit(f"업로드 완료: {blob_name}")
            # else:
            #     self.log_signal.emit(f"업로드 실패: {blob_name}이 존재하지 않습니다.")

            if blob.exists():
                self.log(f'success {image_url} -> {self.bucket_name}/{blob_name}.')
                obj['image_path'] = f"{self.bucket_name}/{blob_name}"
            else:
                raise RuntimeError(f"Upload failed for {image_url}")

        except Exception as e:
            self.log(f"[업로드 실패] {image_url} - {str(e)}")
            obj['error'] = str(e)
            obj['image_yn'] = 'N'