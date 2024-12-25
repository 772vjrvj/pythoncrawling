# utils/date_util.py
from datetime import datetime, timedelta

def get_date(offset=0):
    """
    날짜를 반환하는 함수. offset 값에 따라 오늘, 어제, 내일 등을 반환.
    :param offset: 0 -> 오늘, -1 -> 어제, 1 -> 내일
    :return: 날짜 (yyyymmdd 형식)
    """
    target_date = datetime.today() + timedelta(days=offset)
    return target_date.strftime('%Y%m%d')
