import os, json, mimetypes
from google.cloud import storage
from google.oauth2 import service_account
import re
from io import BytesIO
from PIL import ImageGrab
import pyautogui
import time

class GoogleUploader:
    def __init__(self, log_func, sess, driver):
        if not callable(log_func):
            raise ValueError("log_func must be callable.")
        self.log = log_func
        self.sess = sess
        self.driver = driver

        base_path = os.getcwd()
        self.service_account_path = os.path.join(base_path, "styleai-ai-designer-ml-external.json")
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


    def upload_content(self, obj, content: bytes):
        if not content:
            return None

        image_url = obj.get('image_url', 'unknown')

        try:
            image_data = BytesIO(content)

            blob_name = f"{obj['website']}/{obj['categoryFull']}/{obj['imageName']}"
            mime_type = obj.get("imageContentType", "")# 이미 저장해뒀다면 우선 사용
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(image_url)
                mime_type = mime_type or "application/octet-stream"

            blob = self.bucket.blob(blob_name)
            blob.upload_from_file(image_data, content_type=mime_type)

            if blob.exists():
                self.log(f'✅ 구글 업로드 성공: {image_url} → {self.bucket_name}/{blob_name}')
                obj['imagePath'] = f"{self.bucket_name}/{blob_name}"
                obj['projectId'] = self.project_id
                obj['bucket'] = self.bucket_name
                obj['imageYn'] = 'Y'

        except Exception as e:
            self.log(f"[업로드 실패] {image_url} - {str(e)}")
            obj['error'] = str(e)
            obj['imageYn'] = 'N'


    def upload_direct(self, obj):
        try:
            image_url = obj['imageUrl']
            self.log(f"ARITZIA 이미지 처리 시작: {image_url}")

            # 1. 이미지 띄우기
            self.driver.get(image_url)
            self.log("브라우저에서 이미지 띄움")

            time.sleep(2)  # 이미지 로딩 대기

            # 2. 화면 중앙 클릭 (이미지 가운데로 마우스 이동)

            screenWidth, screenHeight = pyautogui.size()
            centerX, centerY = screenWidth // 2, screenHeight // 2
            pyautogui.moveTo(centerX, centerY, duration=0.5)
            pyautogui.rightClick()
            time.sleep(0.5)

            # 3. 아래 방향키 2번 → 이미지 복사 → 엔터
            for _ in range(3):  # 이미지 복사 메뉴가 3번째일 경우
                pyautogui.press('down')
                time.sleep(0.1)
            pyautogui.press('enter')
            self.log("이미지 복사 완료")

            time.sleep(1)  # 복사 안정화 시간

            # 4. 클립보드에서 이미지 추출

            image = ImageGrab.grabclipboard()
            if image is None:
                self.log("❌ 클립보드에 이미지 없음")
                obj['imageYn'] = 'N'
                return

            # 5. 메모리에 저장 후 업로드
            image_bytes = BytesIO()
            image.save(image_bytes, format='PNG')
            image_bytes.seek(0)
            obj['imageContentType'] = 'image/png'

            self.upload_content(obj, image_bytes.read())

        except Exception as e:
            self.log(f"[ARITZIA 업로드 실패] {obj.get('imageUrl', '')} - {str(e)}")
            obj['error'] = str(e)
            obj['imageYn'] = 'N'


    def upload(self, obj):
        if obj['website'] in ['ARITZIA']:
            self.upload_direct(obj)
        else:
            image_url = obj['imageUrl']
            try:
                # 1. 헤더 설정
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
                }

                # 2. 세션 기반 요청 (self.sess가 있으면 사용)
                response = self.sess.get(image_url, headers=headers)

                response.raise_for_status()
                image_data = BytesIO(response.content)

                # 3. 경로 및 MIME 설정
                blob_name = f"{obj['website']}/{obj['categoryFull']}/{obj['imageName']}"
                mime_type, _ = mimetypes.guess_type(image_url)
                mime_type = mime_type or "application/octet-stream"

                # 4. 업로드 전 존재 여부 확인
                blob = self.bucket.blob(blob_name)

                if blob.exists():
                    self.log(f"⚠️ 이미 존재하는 이미지: {self.bucket_name}/{blob_name} → 업로드 생략")
                    obj['imagePath'] = f"{self.bucket_name}/{blob_name}"
                    obj['projectId'] = self.project_id
                    obj['bucket'] = self.bucket_name
                    obj['imageYn'] = 'Y'
                else:
                    blob.upload_from_file(image_data, content_type=mime_type)
                    if blob.exists():
                        self.log(f'✅ 구글 업로드 성공: {image_url} → {self.bucket_name}/{blob_name}')
                        obj['imagePath'] = f"{self.bucket_name}/{blob_name}"
                        obj['projectId'] = self.project_id
                        obj['bucket'] = self.bucket_name
                        obj['imageYn'] = 'Y'

            except Exception as e:
                self.log(f"[업로드 실패] {image_url} - {str(e)}")
                obj['error'] = str(e)
                obj['imageYn'] = 'N'


    def get_product_id(self, path):
        # 정규표현식을 사용하여 숫자 추출
        product_id = ""
        match = re.search(r'/(\d+)_', path)
        if match:
            product_id = match.group(1)
        return product_id


    def verify_upload(self, obj):
        self.log(f"구글 업로드 데이터 확인 시작")
        blob_product_ids = []
        """업로드 경로에 이미지가 실제 존재하는지 확인하고 로그"""
        prefix_path = f"{obj.get('website', '')}/{obj.get('categoryFull', '')}/"  # 슬래시 꼭 필요

        try:
            blobs = list(self.bucket.list_blobs(prefix=prefix_path))

            if blobs:
                for index, blob in enumerate(blobs, start=1):
                    # self.log(f"{index} - {blob.name}")
                    product_id = self.get_product_id(blob.name)
                    # self.log(f"{index} - {product_id}")
                    blob_product_ids.append(product_id)
            else:
                self.log(f"{prefix_path}에 목록이 없습니다.")

            self.log(f"구글 업로드 데이터 수 ({prefix_path }) : {len(blob_product_ids)}")
            self.log(f"구글 업로드 데이터 확인 끝")
            return blob_product_ids

        except Exception as e:
            self.log(f"[오류] 업로드 확인 중 문제 발생: {str(e)}")


    def delete(self, obj):
        prefix_path = ""
        """GCS에서 폴더 내 이미지들 전체 삭제"""
        try:
            prefix_path = f"{obj.get('website', '')}/{obj.get('categoryFull', '')}/"  # 슬래시 꼭 필요
            blobs = list(self.bucket.list_blobs(prefix=prefix_path))

            if not blobs:
                self.log(f"[삭제 실패] {self.bucket_name}/{prefix_path} - 삭제할 파일이 없습니다.")
                return

            for index, blob in enumerate(blobs, start=1):
                blob.delete()
                self.log(f"[{index}] [삭제 완료] {blob.name}")

        except Exception as e:
            self.log(f"[삭제 오류] {prefix_path} - {str(e)}")


    def delete_image(self, obj):
        """GCS에서 특정 이미지 1개 삭제"""
        blob_name= ""
        try:
            # 전체 blob 경로 구성
            blob_name = f"{obj.get('website', '')}/{obj.get('categoryFull', '')}/{obj.get('imageName', '')}"
            blob = self.bucket.blob(blob_name)

            if blob.exists():
                blob.delete()
                self.log(f"[삭제 완료] {blob_name}")
            else:
                self.log(f"[삭제 실패] {blob_name} - 존재하지 않는 이미지입니다.")

        except Exception as e:
            self.log(f"[삭제 오류] {blob_name} - {str(e)}")



    def download_all_in_folder(self, obj, save_dir="downloads"):
        """GCS에서 폴더 내 모든 이미지 로컬에 저장"""
        prefix_path = ""
        try:
            prefix_path = f"{obj.get('website', '')}/{obj.get('categoryFull', '')}/"  # 꼭 / 로 끝나야 함

            # 로컬 저장 폴더 생성
            local_folder = os.path.join(save_dir, obj.get('brand', ''), obj.get('categoryFull', ''))
            os.makedirs(local_folder, exist_ok=True)

            blobs = self.bucket.list_blobs(prefix=prefix_path)
            count = 0

            for blob in blobs:
                # 파일 이름 추출
                filename = os.path.basename(blob.name)
                save_path = os.path.join(local_folder, filename)

                blob.download_to_filename(save_path)
                self.log(f"[다운로드 완료] {blob.name} → {save_path}")
                count += 1

            if count == 0:
                self.log(f"[알림] {prefix_path} 경로에 다운로드할 이미지가 없습니다.")
            else:
                self.log(f"[총 {count}개 파일 다운로드 완료] {prefix_path}")

        except Exception as e:
            self.log(f"[전체 다운로드 오류] {prefix_path} - {str(e)}")