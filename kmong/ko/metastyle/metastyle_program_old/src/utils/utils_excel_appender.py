import os
import pandas as pd

class CsvAppender:
    def __init__(self, file_path):
        self.file_path = file_path

        # 파일이 없으면 빈 CSV 생성
        if not os.path.exists(file_path):
            pd.DataFrame().to_csv(file_path, index=False, encoding='utf-8-sig')
    
    # 데이터를 csv파일에 한줄씩 추가
    def append_row(self, row: dict, id_column="product_id"):
        # CSV 로드
        if os.path.exists(self.file_path):
            df = pd.read_csv(self.file_path, encoding='utf-8-sig')
        else:
            df = pd.DataFrame()

        # DataFrame으로 변환
        row_df = pd.DataFrame([row])

        # 컬럼 동기화 (새로운 키 자동 반영)
        df = self._sync_columns(df, row_df)

        # product_id 기준으로 업데이트 또는 추가
        if id_column in df.columns and row[id_column] in df[id_column].values:
            df.loc[df[id_column] == row[id_column], row_df.columns] = row_df.values
        else:
            df = pd.concat([df, row_df], ignore_index=True)

        # 저장
        df.to_csv(self.file_path, index=False, encoding='utf-8-sig')

    def _sync_columns(self, df, row_df):
        """row_df에만 있는 컬럼이 있다면 df에도 추가"""
        for col in row_df.columns:
            if col not in df.columns:
                df[col] = None  # 새로운 컬럼을 추가
        return df


    def load_rows(self) -> list[dict]:
        """CSV 파일 내용을 객체(dict) 리스트로 반환"""
        if os.path.exists(self.file_path):
            df = pd.read_csv(self.file_path, encoding='utf-8-sig')
            return df.to_dict(orient="records")
        else:
            return []


    def set_file_path(self, new_file_path):
        self.file_path = new_file_path

        # 새 파일이 없다면 빈 CSV 생성
        if not os.path.exists(self.file_path):
            pd.DataFrame().to_csv(self.file_path, index=False, encoding='utf-8-sig')