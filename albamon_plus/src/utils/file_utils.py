import os  # 운영체제 관련 기능을 제공하는 표준 모듈
from src.utils.time_utils import get_current_yyyymmddhhmmss  # 현재 날짜 및 시간 문자열을 반환하는 유틸 함수 임포트

class FileUtils:

    def __init__(self, log_func):
        """
        FileUtils 클래스 생성자

        :param log_func: 로그 출력을 위한 함수. 문자열을 인자로 받아 출력 (ex: print 또는 사용자 정의 로깅 함수)
        """
        self.log_func = log_func  # 전달받은 로그 출력 함수를 인스턴스 변수로 저장

    def create_folder(self, folder_name):
        """
        현재 파일이 위치한 디렉토리 기준으로 지정한 폴더를 생성 (존재하지 않을 경우)

        :param folder_name: 생성할 폴더명 (상대경로)
        :return: 생성된 폴더의 전체 경로 문자열
        """
        folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), folder_name)
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
