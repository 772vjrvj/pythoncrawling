import pandas as pd

class ExcelUtils:
    def __init__(self, log_func=None):
        self.log_func = log_func

    def append_to_csv(self, filename, data_list, columns):

        if not data_list:
            return

        df = pd.DataFrame(data_list, columns=columns)
        df.to_csv(filename, mode='a', header=False, index=False, encoding="utf-8-sig")
        data_list.clear()
