import pandas as pd

class ExcelUtils:
    def __init__(self, log_func=None):
        self.log_func = log_func

    def append_to_csv(self, filename, data_list, columns):
        """
        data_list: dict의 리스트
        filename: 저장할 CSV 파일 경로
        columns: 저장할 열 순서
        """
        if not data_list:
            return

        df = pd.DataFrame(data_list, columns=columns)
        df.to_csv(filename, mode='a', header=False, index=False, encoding="utf-8-sig")
        data_list.clear()
        if self.log_func:
            self.log_func(f"CSV에 {len(data_list)}개 행 저장 완료: {filename}")
