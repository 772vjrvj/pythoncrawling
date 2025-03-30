import os
import pandas as pd
from pandas.errors import EmptyDataError

class CsvAppender:
    def __init__(self, file_path, log_func):
        self.file_path = file_path
        self.log_func  = log_func

        # 파일이 없으면 빈 CSV 생성
        if not os.path.exists(self.file_path):
            pd.DataFrame().to_csv(self.file_path, index=False, encoding='utf-8-sig')


    # 0    1      <- index 0번 행의 product_id는 1이다
    # 1    2      <- index 1번 행의 product_id는 2이다
    # Name: product_id, dtype: int64
    # ↑           ↑
    # 컬럼명     데이터 타입 (정수)

    # 데이터를 csv파일에 한줄씩 추가 (동일한 값이 있으면 update)
    def append_row(self, row, id_column="product_id"):
        try:
            try:
                df = pd.read_csv(self.file_path, encoding='utf-8-sig', dtype={id_column: str})
            except (FileNotFoundError, EmptyDataError):
                df = pd.DataFrame()  # 파일 없거나 빈 파일이면 새로 생성

            # ID를 문자열로 강제 변환
            row_id = str(row[id_column])
            row[id_column] = row_id  # 혹시 row가 숫자였다면 여기서 str로 변환

            row_df = pd.DataFrame([row])
            df = self._sync_columns(df, row_df)

            # df의 ID 컬럼도 문자열로 변환 (혹시 누락된 경우 대비)
            df[id_column] = df[id_column].astype(str)

            # row가 있는지 확인
            if id_column in df.columns and row_id in df[id_column].values:
                # df[id_column] product_id의 값들을 series로 가져와서 내부에 row[id_column]가 있는지 확인
                # “같은 product_id 가진 행이 있으면 → 그 행을 새 값으로 업데이트 해줘”
                # update문
                df.loc[df[id_column] == row_id, row_df.columns] = row_df.values
            # 없으면 추가
            else:
                df = pd.concat([df, row_df], ignore_index=True)

            # ID를 포함한 전체 데이터프레임을 문자열로 저장 (지수 표기 방지)
            df[id_column] = df[id_column].astype(str)
            df.to_csv(self.file_path, index=False, encoding='utf-8-sig')
        except Exception as e:
            row["error"] = str(e)

    def _sync_columns(self, df, row_df):
        """row_df에만 있는 컬럼이 있다면 df에도 추가"""
        for col in row_df.columns:
            if col not in df.columns:
                df[col] = None  # 새로운 컬럼을 추가
        return df


    def load_rows(self):
        """CSV 파일 내용을 객체(dict) 리스트로 반환"""
        if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
            try:
                df = pd.read_csv(self.file_path, encoding='utf-8-sig')
                return df.to_dict(orient="records")
            except Exception as e:
                self.log_func(f"CSV 읽기 실패: {e}")
                return []
        else:
            return []

    def set_file_path(self, new_file_path):
        self.file_path = new_file_path

        # 새 파일이 없다면 빈 CSV 생성
        if not os.path.exists(self.file_path):
            pd.DataFrame().to_csv(self.file_path, index=False, encoding='utf-8-sig')


    def merge_all_csv_from_directory(self, root_dir="DB", output_filename="metastyle_all.csv"):
        """DB 폴더 내 기존 metastyle_all.csv 삭제 후, 모든 CSV 파일 병합하여 metastyle_all.csv로 저장"""

        output_path = os.path.join(root_dir, output_filename)

        # 1. 기존 metastyle_all.csv 파일이 존재하면 삭제
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                self.log_func(f"🗑️ 기존 파일 삭제: {output_path}")
            except Exception as e:
                self.log_func(f"❌ 삭제 실패: {output_path} - {e}")
                return  # 삭제 실패 시 병합 진행하지 않음

        all_dataframes = []

        # 2. CSV 병합 수행
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.csv') and file != output_filename:
                    file_path = os.path.join(root, file)
                    try:
                        df = pd.read_csv(file_path, encoding='utf-8-sig')
                        all_dataframes.append(df)
                        self.log_func(f"✅ 읽음: {file_path}")
                    except Exception as e:
                        self.log_func(f"❌ 실패: {file_path} - {e}")

        if not all_dataframes:
            self.log_func("⚠️ 병합할 CSV가 없습니다.")
            return

        # 3. 병합 후 저장
        merged_df = pd.concat(all_dataframes, ignore_index=True)
        merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        self.log_func(f"✅ 병합 완료: {output_path} (총 {len(merged_df)} rows)")