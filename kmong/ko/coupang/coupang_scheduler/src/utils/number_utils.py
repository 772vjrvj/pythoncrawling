import re

def extract_number(text):
    """주어진 문자열에서 숫자만 추출하여 정수로 반환"""
    return int(re.sub(r'\D', '', text)) if text else 0