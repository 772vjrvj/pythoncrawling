import os
from time_utils import get_current_yyyymmddhhmmss

class FileUtils:
    def __init__(self, log_func):
        self.log_func = log_func

    def get_csv_filename(self, prefix):
        filename = f"{prefix}_{get_current_yyyymmddhhmmss()}.csv"
        path = os.path.join(os.getcwd(), filename)
        self.log_func(f"CSV 파일 경로 생성됨: {path}")
        return path
