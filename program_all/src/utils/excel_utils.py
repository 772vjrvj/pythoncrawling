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