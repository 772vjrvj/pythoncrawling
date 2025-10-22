from datetime import datetime
from typing import  Optional
from src.utils.logger import log_error

def to_iso_kst_format(kst_str: str) -> Optional[str]:
    """
    'YYYYMMDDHHMMSS' 형식의 문자열을 ISO 8601 KST 포맷으로 변환.
    예: '20250629013000' → '2025-06-29T01:30:00+09:00'
    """
    try:
        dt = datetime.strptime(kst_str, "%Y%m%d%H%M%S")
        return dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")
    except Exception as e:
        log_error(f"날짜 변환 오류: {e}")
        return None

def compact(obj, always_include=None):
    if always_include is None:
        always_include = []

    return {
        k: v for k, v in obj.items()
        if k in always_include or (
                v is not None and
                v != '' and
                v != [] and
                not (k == 'paymentAmount' and v == 0)
        )
    }