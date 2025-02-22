from datetime import datetime

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