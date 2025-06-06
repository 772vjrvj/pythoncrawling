import os
from src.utils.time_utils import get_current_yyyymmddhhmmss

class FileUtils:
    def __init__(self, log_func):
        self.log_func = log_func

    def get_timestamped_filepath(self, prefix, ext, label):
        filename = f"{prefix}_{get_current_yyyymmddhhmmss()}.{ext}"
        path = os.path.join(os.getcwd(), filename)
        self.log_func(f"{label} 파일 경로 생성됨: {path}")
        return path

    def get_csv_filename(self, prefix):
        return self.get_timestamped_filepath(prefix, "csv", "CSV")

    def get_excel_filename(self, prefix):
        return self.get_timestamped_filepath(prefix, "xlsx", "Excel")
