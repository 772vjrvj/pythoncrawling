from datetime import datetime
from zoneinfo import ZoneInfo
from src.utils.str_utils import str_clean

def get_current_yyyymmddhhmmss():
    # 현재 날짜와 시간 가져오기
    now = datetime.now()

    # 날짜와 시간을 'yyyymmddhhmmss' 형식으로 포맷팅
    formatted_datetime = now.strftime("%Y%m%d%H%M%S")

    return formatted_datetime



def parse_timestamp(ymd_hms_text: str) -> int:
    """'YYYY/MM/DD \\nHH:MM:SS' -> epoch seconds"""
    t = str_clean(ymd_hms_text).replace("\n", " ").replace("  ", " ")
    parts = t.split()
    if len(parts) >= 2:
        ymd, hms = parts[0], parts[1]
    else:
        return 0
    try:
        dt = datetime.strptime(f"{ymd} {hms}", "%Y/%m/%d %H:%M:%S")
        return int(dt.timestamp())
    except Exception:
        return 0



def format_real_date(ts: int) -> str:
    """타임스탬프(int)를 'YYYY-MM-DD HH:MM:SS' 문자열(Asia/Seoul)로 변환"""
    if not ts or ts <= 0:
        return ""
    try:
        return datetime.fromtimestamp(ts, ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""