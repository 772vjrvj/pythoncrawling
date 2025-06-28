from datetime import datetime
from typing import Any, Dict, Optional, List


def to_iso_kst_format(kst_str: str) -> Optional[str]:
    """
    'YYYYMMDDHHMMSS' 형식의 문자열을 ISO 8601 KST 포맷으로 변환.
    예: '20250629013000' → '2025-06-29T01:30:00+09:00'
    """
    try:
        dt = datetime.strptime(kst_str, "%Y%m%d%H%M%S")
        return dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")
    except Exception as e:
        print(f"날짜 변환 오류: {e}")
        return None


def compact(obj: Dict[str, Any], always_include: List[str] = []) -> Dict[str, Any]:
    """
    빈 값 (None, '', [], paymentAmount == 0)을 제거한 새 dict 반환
    항상 포함시킬 key는 always_include 리스트에 명시
    """
    return {
        k: v for k, v in obj.items()
        if (
                k in always_include or (
                v is not None and
                v != '' and
                v != [] and
                not (k == 'paymentAmount' and v == 0)
        )
        )
    }
