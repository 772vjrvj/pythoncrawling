import os
import re

class FilePathBuilder:
    @staticmethod
    def sanitize_filename(name):
        """
        파일명에서 사용할 수 없는 문자 제거
        """
        return re.sub(r'[\\/*?:"<>|]', "_", name)

    @staticmethod
    def build_csv_path(base_dir, sub_dir, filename, ext="csv"):
        """
        안전한 파일 경로를 생성하고, 디렉토리가 없으면 생성
        :param base_dir: 기본 상위 폴더 (예: "DB")
        :param sub_dir: 사이트 또는 하위 폴더 이름 (예: "ZARA")
        :param filename: 파일 이름 (확장자 제외)
        :param ext: 파일 확장자 (기본 csv)
        :return: 생성된 파일 경로 문자열
        """
        safe_filename = FilePathBuilder.sanitize_filename(filename)
        dir_path = os.path.join(base_dir, sub_dir)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        return os.path.join(dir_path, "{}.{}".format(safe_filename, ext))

    @staticmethod
    def build_csv_path_main(base_dir, filename, ext="csv"):
        """
        안전한 파일 경로를 생성하고, 디렉토리가 없으면 생성

        :param base_dir: 저장할 기본 폴더 (예: "DB/ZARA")
        :param filename: 저장할 파일 이름 (확장자 제외)
        :param ext: 확장자 (기본값: csv)
        :return: 전체 경로 문자열
        """
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        safe_filename = filename.replace("/", "_").replace("\\", "_")  # 파일명 안전 처리
        return os.path.join(base_dir, f"{safe_filename}.{ext}")