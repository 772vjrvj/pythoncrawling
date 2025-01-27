# utils/date_util.py
from datetime import datetime, timedelta
from utils.logger import logger

def get_date(offset=0):
    """
    날짜를 반환하는 함수. offset 값에 따라 오늘, 어제, 내일 등을 반환.
    :param offset: 0 -> 오늘, -1 -> 어제, 1 -> 내일
    :return: 날짜 (yyyymmdd 형식)
    """
    target_date = datetime.today() + timedelta(days=offset)
    return target_date.strftime('%Y%m%d')


def convert_to_yyyymmdd(date_str, type):
    """
    yyyy-mm-dd 형식의 날짜를 yyyymmdd 형식으로 변환하는 함수
    :param date_str: yyyy-mm-dd 형식의 날짜 문자열
    :return: yyyymmdd 형식의 날짜 문자열
    """
    try:
        date_obj = None
        if type == '-':
            # 문자열을 datetime 객체로 변환
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        elif type == '.':
            date_obj = datetime.strptime(date_str, '%Y.%m.%d')
        else:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')

        # datetime 객체를 yyyymmdd 형식의 문자열로 변환하여 반환
        return date_obj.strftime('%Y%m%d')
    except ValueError:
        # 잘못된 형식일 경우 처리 (에러 메시지 출력 또는 None 반환)
        logger.error(f'잘못된 날짜 형식: {date_str}')
        return ''



def get_current_time():
    """현재 시간 가져오기"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_yyyy():
    """현재 연도를 반환하는 함수"""
    return datetime.now().year

def get_current_yymmddhhmm():
    """현재 날짜와 시간을 'YYMMDDHHMM' 형식으로 반환하는 함수"""
    now = datetime.now()
    return now.strftime('%y%m%d%H%M')