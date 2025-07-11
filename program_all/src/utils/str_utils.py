import re

def split_comma_keywords(keyword_str):
    """콤마로 구분된 키워드 문자열을 리스트로 변환"""
    return [k.strip() for k in keyword_str.split(",") if k.strip()]


def extract_numbers(text):
    """
    문자열에서 모든 숫자(연속된 숫자 덩어리)를 리스트로 반환
    예: "in total 352 albums and 12 tracks" → [352, 12]
    """
    return [int(num) for num in re.findall(r'\d+', text)]