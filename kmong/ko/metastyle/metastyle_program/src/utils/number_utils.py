from math import floor

def divide_and_truncate(param1, param2):
    """
    두 숫자를 나누어 소수점 2자리까지 버림하여 반환하는 함수.
    
    :param param1: 분자 (numerator)
    :param param2: 분모 (denominator)
    :return: 나눈 결과를 소수점 2자리까지 버림한 값 (float)
    """
    if param2 == 0:
        return 0

    result = param1 / param2  # 나누기 연산
    truncated_result = floor(result * 100) / 100  # 소수점 2자리까지 버림
    return truncated_result
