def split_comma_keywords(keyword_str):
    """콤마로 구분된 키워드 문자열을 리스트로 변환"""
    return [k.strip() for k in keyword_str.split(",") if k.strip()]