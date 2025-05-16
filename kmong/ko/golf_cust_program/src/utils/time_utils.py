from datetime import datetime
from src.utils.log_util import log

def get_current_yyyymmddhhmmss():
    # 현재 날짜와 시간 가져오기
    now = datetime.now()

    # 날짜와 시간을 'yyyymmddhhmmss' 형식으로 포맷팅
    formatted_datetime = now.strftime("%Y%m%d%H%M%S")

    return formatted_datetime

def get_current_formatted_datetime():
    # 현재 날짜와 시간 가져오기
    now = datetime.now()

    # 날짜와 시간을 'YYYY.MM.DD HH:MM:SS' 형식으로 포맷팅
    formatted_datetime = now.strftime("%Y.%m.%d %H:%M:%S")

    return formatted_datetime

def get_today_date():
    return datetime.now().strftime("%Y/%m/%d")


def to_iso_format(kst_str):
    try:
        # '20250530102000' → datetime 객체로 파싱
        dt = datetime.strptime(kst_str, "%Y%m%d%H%M%S")
        # ISO 포맷 + 한국 시간대 오프셋
        return dt.isoformat() + "+09:00"
    except Exception as e:
        log(f"❗ 날짜 변환 오류: {e}")
        return kst_str