import re
from urllib.parse import urlparse, parse_qs

def split_comma_keywords(keyword_str):
    """콤마로 구분된 키워드 문자열을 리스트로 변환"""
    return [k.strip() for k in keyword_str.split(",") if k.strip()]


def extract_numbers(text):
    """
    문자열에서 모든 숫자(연속된 숫자 덩어리)를 리스트로 반환
    예: "in total 352 albums and 12 tracks" → [352, 12]
    """
    return [int(num) for num in re.findall(r'\d+', text)]


def get_query_params(url, name):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get(name, [None])[0]


NBSP_RE = re.compile(r"[\u00a0\u200b]")  # NBSP, zero-width space

def str_norm(s: str) -> str:
    """NBSP/zero-width 제거 후 strip"""
    if s is None:
        return ""
    return NBSP_RE.sub(" ", s).strip()


def str_clean(s: str) -> str:
    return (s or "").replace("\u00a0", " ").strip()
