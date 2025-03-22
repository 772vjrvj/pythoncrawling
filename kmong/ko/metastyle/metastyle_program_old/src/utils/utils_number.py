from math import floor


def divide_and_truncate(param1, param2):
    if param2 == 0:
        return 0

    result = param1 / param2  # 나누기 연산
    truncated_result = floor(result * 10000) / 10000  # 소수점 2자리까지 버림
    return truncated_result


def divide_and_truncate_per(param1, param2):
    truncated_result = divide_and_truncate(param1, param2)
    truncate_per = truncated_result * 100
    return truncate_per


def calculate_divmod(total_cnt, divisor=30):
    quotient = total_cnt // divisor  # 몫
    remainder = total_cnt % divisor  # 나머지
    return quotient, remainder
