from google.cloud import storage
from google.oauth2 import service_account
import os
import json

def list_images_in_bucket():
    try:
        # 프로그램 실행 경로 기준으로 파일 경로 설정
        base_path = os.getcwd()
        service_account_path = os.path.join(base_path, "styleai-ai-designer-ml-external.json")
        user_config_path = os.path.join(base_path, "user.json")

        # user.json에서 설정 값 로드
        with open(user_config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)

        project_id = user_config.get("project_id")
        bucket_name = user_config.get("bucket")

        if not project_id or not bucket_name:
            raise ValueError("Invalid configuration in user.json. Check 'project_id' and 'bucket' fields.")

        # GCP 클라이언트 생성
        credentials = service_account.Credentials.from_service_account_file(service_account_path)
        storage_client = storage.Client(credentials=credentials, project=project_id)
        bucket = storage_client.bucket(bucket_name)

        # 특정 경로에 있는 파일 나열
        # prefix = "test_program/MYTHERESA/boys_"  # 검색할 경로
        # prefix = "test_program/MYTHERESA"  # 검색할 경로
        prefix = "test_program"  # 검색할 경로
        blobs = bucket.list_blobs(prefix=prefix)

        # 이미지 파일 목록 수집
        image_list = []
        for blob in blobs:
            image_list.append(blob.name)

        # 출력
        if image_list:
            print(f"Images in bucket path '{prefix}':")
            for image in image_list:
                print(image)
        else:
            print(f"No images found in bucket path '{prefix}'.")

    except FileNotFoundError as e:
        print(f"File not found: {str(e)}")
    except ValueError as e:
        print(f"Configuration error: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

# 실행
list_images_in_bucket()
