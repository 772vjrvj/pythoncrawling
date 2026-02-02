import os
from src.utils.time_utils import get_current_yyyymmddhhmmss
import json
import requests

class FileUtils:
    def __init__(self, log_func, api_client=None):
        self.log_func = log_func
        self.api_client = api_client  # === 신규 ===

    def create_folder(self, folder_name):
        """
        현재 파일이 위치한 디렉토리 기준으로 지정한 폴더를 생성 (존재하지 않을 경우)

        :param folder_name: 생성할 폴더명 (상대경로)
        :return: 생성된 폴더의 전체 경로 문자열
        """
        folder_path = os.path.join(os.getcwd(), folder_name)
        # __file__은 현재 파일의 경로, 이를 기준으로 폴더 생성 위치를 정함

        if not os.path.exists(folder_path):  # 해당 경로가 존재하지 않는다면
            os.makedirs(folder_path)  # 폴더 생성 (필요한 상위 폴더까지 포함하여 생성)
            self.log_func(f"📁 폴더 생성됨: {folder_path}")  # 생성되었음을 로그로 출력
        else:
            self.log_func(f"📁 폴더 이미 존재: {folder_path}")  # 이미 존재하면 그대로 로그 출력

        return folder_path  # 생성되었거나 기존 폴더의 경로 반환

    def save_file(self, folder_path, filename, source):
        """
        지정된 폴더에 파일을 저장 (HTML 또는 텍스트 등)

        :param folder_path: 파일을 저장할 폴더 경로
        :param filename: 저장할 파일 이름 (예: example.html)
        :param source: 저장할 텍스트 내용 (HTML 등)
        :return: 저장된 파일의 전체 경로
        """
        save_path = os.path.join(folder_path, filename)

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(source)
            self.log_func(f"💾 파일 저장 완료: {save_path}")
        except Exception as e:
            self.log_func(f"❌ 파일 저장 실패: {save_path} / 오류: {e}")
            raise

        return save_path

    def delete_file(self, file_path):
        """
        지정된 경로의 파일을 삭제 (존재할 경우)

        :param file_path: 삭제할 파일의 전체 경로
        """
        if os.path.exists(file_path):  # 파일이 존재하면
            try:
                os.remove(file_path)  # 파일 삭제
                self.log_func(f"🗑️ 파일 삭제됨: {file_path}")
            except Exception as e:
                self.log_func(f"❌ 파일 삭제 실패: {file_path} / 오류: {e}")
                raise
        else:
            self.log_func(f"⚠️ 삭제 대상 파일이 존재하지 않음: {file_path}")

        return file_path

    def get_timestamped_filepath(self, prefix, ext, label):
        filename = f"{prefix}_{get_current_yyyymmddhhmmss()}.{ext}"
        path = os.path.join(os.getcwd(), filename)
        self.log_func(f"{label} 파일 경로 생성됨: {path}")
        return path

    def get_csv_filename(self, prefix):
        return self.get_timestamped_filepath(prefix, "csv", "CSV")

    def get_excel_filename(self, prefix):
        return self.get_timestamped_filepath(prefix, "xlsx", "Excel")

    def read_numbers_from_file(self, file_path):
        """
        숫자가 한 줄씩 저장된 텍스트 파일을 읽어 정수 리스트로 반환

        :param file_path: 읽을 파일 경로
        :return: 정수 리스트
        """
        numbers = []
        if not os.path.exists(file_path):
            self.log_func(f"❌ 파일이 존재하지 않습니다: {file_path}")
            return numbers

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            numbers.append(int(line))
                        except ValueError:
                            self.log_func(f"⚠️ 정수 변환 실패 (무시됨): '{line}'")
        except Exception as e:
            self.log_func(f"❌ 파일 읽기 실패: {file_path} / 오류: {e}")
            raise

        self.log_func(f"📄 숫자 {len(numbers)}개 읽음: {file_path}")
        return numbers

    def save_image(self, folder_path, filename, image_url, headers=None):
        """
        지정된 폴더에 이미지 저장
        - api_client가 있으면 api_client로 다운로드
        - 없으면 requests로 다운로드(기존 동작 유지)
        """
        save_path = os.path.join(folder_path, filename)

        try:
            resp = self.api_client.get(image_url, headers=headers, return_bytes=True)
            content = getattr(resp, "content", None)
            if content is None:
                content = resp

            with open(save_path, "wb") as f:
                f.write(content)

            self.log_func(f"🖼️ 이미지 저장 완료: {save_path}")
            return save_path

        except Exception as e:
            self.log_func(f"❌ 이미지 저장 실패: {save_path} / 오류: {e}")
            return None

    def read_json_array_from_resources(self, filename):
        """
        resources 폴더 안에서 지정한 JSON 파일을 읽어 배열(list)로 반환

        :param filename: JSON 파일 이름 (예: 'naver_real_estate_data.json')
        :return: JSON 배열 (list), 실패 시 []
        """

        # 프로젝트 루트 기준 resources 폴더 경로
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        resources_dir = os.path.join(base_dir, "resources")
        file_path = os.path.join(resources_dir, filename)

        if not os.path.exists(file_path):
            self.log_func(f"❌ JSON 파일이 존재하지 않습니다: {file_path}")
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                self.log_func(f"⚠️ JSON 배열 형식이 아님: {file_path}")
                return []
            self.log_func(f"📄 JSON 배열 {len(data)}개 읽음: {file_path}")
            return data
        except Exception as e:
            self.log_func(f"❌ JSON 읽기 실패: {file_path} / 오류: {e}")
            return []