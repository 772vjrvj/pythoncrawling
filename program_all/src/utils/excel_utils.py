import pandas as pd
import os

class ExcelUtils:
    def __init__(self, log_func=None):
        self.log_func = log_func

    def append_to_csv(self, filename, data_list, columns):

        if not data_list:
            return

        df = pd.DataFrame(data_list, columns=columns)
        df.to_csv(filename, mode='a', header=False, index=False, encoding="utf-8-sig")
        data_list.clear()


    def append_to_excel(self, filename, data_list, columns, sheet_name="Sheet1"):
        if not data_list:
            return

        df = pd.DataFrame(data_list, columns=columns)

        if os.path.exists(filename):
            with pd.ExcelWriter(filename, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
                start_row = writer.sheets[sheet_name].max_row if sheet_name in writer.sheets else 0
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=start_row)
        else:
            with pd.ExcelWriter(filename, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=True)

        data_list.clear()


    def convert_csv_to_excel_and_delete(self, csv_filename, sheet_name="Sheet1"):
        """
        CSV 파일을 엑셀 파일로 변환한 후, 원본 CSV 파일을 삭제합니다.
        엑셀 파일명은 CSV와 동일하고 확장자만 .xlsx 로 바뀝니다.
        """
        if not os.path.exists(csv_filename):
            if self.log_func:
                self.log_func(f"❌ CSV 파일이 존재하지 않습니다: {csv_filename}")
            return

        try:
            df = pd.read_csv(csv_filename, encoding="utf-8-sig")

            if df.empty:
                if self.log_func:
                    self.log_func(f"⚠️ CSV에 데이터가 없습니다: {csv_filename}")
                return

            # 엑셀 파일 이름은 CSV와 동일하게 (확장자만 .xlsx)
            excel_filename = os.path.splitext(csv_filename)[0] + ".xlsx"

            with pd.ExcelWriter(excel_filename, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name=sheet_name)

            os.remove(csv_filename)

            if self.log_func:
                self.log_func(f"✅ 엑셀 파일 저장 완료: {excel_filename}")
                self.log_func(f"🗑️ CSV 파일 삭제 완료: {csv_filename}")

        except Exception as e:
            if self.log_func:
                self.log_func(f"❌ 변환 중 오류 발생: {e}")

