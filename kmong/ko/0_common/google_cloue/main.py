import mimetypes
from io import BytesIO

import requests
from google.cloud import storage
from google.oauth2 import service_account


# 구글 클라우드 업로드
def google_cloud_upload(site_name, category, product_name, image_url):
    # GCP 설정
    project_id = "vue2-study"  # 새 프로젝트 ID
    bucket_name = "772vjrvj"  # 새 버킷 이름"
    service_account_path = "D:/GitHub/pythoncrawling/vue2-study-0d4d51baa885.json"  # 서비스 계정 키 파일 경로 설정

    # GCP 클라우드 스토리지 클라이언트 생성 (서비스 계정 인증 사용)
    credentials = service_account.Credentials.from_service_account_file(service_account_path)
    storage_client = storage.Client(credentials=credentials, project=project_id)
    bucket = storage_client.bucket(bucket_name)

    # 다운로드할 이미지 URL에서 이미지 데이터 가져오기
    response = requests.get(image_url)
    response.raise_for_status()  # 오류 발생 시 예외 처리

    # 이미지 데이터를 메모리에서 처리
    image_data = BytesIO(response.content)

    # 이미지 이름 변경: URL에서 'media/...' 부분을 'media_'로 변경
    image_name = image_url.split("media/")[-1].replace("/", "_")  # 'media/...'를 'media_...'로 변경

    # 업로드할 경로 설정: site_name/category/product_name/media_...
    blob_name = f"{site_name}/{category}/{product_name}/{image_name}"

    # 이미지의 MIME 타입을 자동으로 감지
    mime_type, _ = mimetypes.guess_type(image_url)
    if not mime_type:
        mime_type = "application/octet-stream"  # MIME 타입을 감지할 수 없는 경우 기본값 설정

    # Cloud Storage에 이미지 업로드
    blob = bucket.blob(blob_name)
    blob.upload_from_file(image_data, content_type=mime_type)

    print(f"Image from {image_url} has been uploaded to {bucket_name}/{blob_name}.")

    # 해당 경로에 있는 모든 이미지 목록 출력 (site_name/category/product_name/ 경로)
    blobs = bucket.list_blobs(prefix=f"{site_name}/{category}/{product_name}/")  # 경로 내의 모든 파일 나열
    print(f"Images in {site_name}/{category}/{product_name} directory:")
    for blob in blobs:
        print(f"- {blob.name}")

