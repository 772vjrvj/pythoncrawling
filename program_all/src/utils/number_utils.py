# ============================================
# 2) ./src/utils/number_utils.py  (이름은 예시)
# ============================================
from math import floor
import re


def divide_and_truncate(param1, param2):
    if param2 == 0:
        return 0

    result = param1 / param2  # 나누기 연산
    truncated_result = floor(result * 10000) / 10000  # 소수점 2자리까지 버림
    return truncated_result


def divide_and_truncate_per(param1, param2):
    if param2 == 0:
        return 0
    result = param1 / param2  # 나누기 연산
    truncated_result = floor(result * 10000) / 10000  # 소수점 2자리까지 버림
    truncate_per = truncated_result * 100
    return truncate_per


def calculate_divmod(total_cnt, divisor=30):
    quotient = total_cnt // divisor  # 몫
    remainder = total_cnt % divisor  # 나머지
    return quotient, remainder


def to_int_digits(s: str) -> int:
    """'1,234원' -> 1234"""
    if not s:
        return 0
    nums = re.findall(r"\d+", s)
    return int("".join(nums)) if nums else 0


# ==========================================================
# === 신규 === KRX/NEXTRADE에서 쓰던 변환 유틸도 여기에 추가
# ==========================================================
def to_int(v):
    try:
        return int(str(v).replace(",", ""))
    except Exception:
        return 0


def to_float(v):
    try:
        return float(str(v).replace(",", ""))
    except Exception:
        return None
