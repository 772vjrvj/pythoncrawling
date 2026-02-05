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


def parse_yy_mm_dd(d: str) -> str:
    """
    '25.08.25' → '2025-08-25'
    """
    d = (d or "").strip()
    try:
        return datetime.strptime(d, "%y.%m.%d").strftime("%Y-%m-%d")
    except Exception:
        return ""


def parse_date_yyyy_mm_dd(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def parse_finish_dt(dt_str: str) -> str:
    """
    '2025-08-31 23:59:00.0' → '2025-08-31'
    """
    if not dt_str:
        return ""
    try:
        return datetime.strptime(dt_str.split()[0], "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return ""


def parse_datetime_yyyy_mm_dd_hhmmss(s: str):
    """
    '2025-11-11 00:00:00' → datetime 또는 None
    """
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def parse_datetime_to_yyyymmdd(s: str) -> str:
    """
    '2025-11-11' → '20251111'
    '2025-11-11 00:00:00' → '20251111'
    """
    if not s:
        return ""

    s = s.strip()

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y%m%d")
        except ValueError:
            continue

    return ""


def format_yyyymmdd_to_yyyy_mm_dd(s: str) -> str:
    """
    '20251123' → '2025-11-23'
    """
    if not s:
        return ""
    s = s.strip()
    try:
        return datetime.strptime(s, "%Y%m%d").strftime("%Y-%m-%d")
    except Exception:
        return ""
