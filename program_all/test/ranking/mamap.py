import requests
from bs4 import BeautifulSoup
import re
from typing import Optional

DIGIT_RE = re.compile(r"\d+")

def get_mamap_review_count(item_id: str) -> Optional[int]:
    """
    https://mamap.co.kr/talk/review_all/{item_id} 페이지에서
    <div class="all_nreview_info_left">후기 N건</div>의 N(숫자)만 추출해서 반환.
    찾지 못하면 None.
    """
    url = f"https://mamap.co.kr/talk/review_all/{item_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
                   "image/avif,image/webp,image/apng,*/*;q=0.8,"
                   "application/signed-exchange;v=b3;q=0.7"),
        "Referer": "https://mamap.co.kr/",
    }

    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) 기본: class 정확히 매칭
    div = soup.select_one("div.all_nreview_info_left")
    if div:
        m = DIGIT_RE.search(div.get_text(strip=True))
        if m:
            return int(m.group())

    # 2) 폴백: '후기'와 '건' 포함된 어떤 요소든 숫자 추출
    candidate = soup.find(string=lambda s: s and ("후기" in s and "건" in s))
    if candidate:
        m = DIGIT_RE.search(candidate)
        if m:
            return int(m.group())

    return None


if __name__ == "__main__":
    # 예시: 33985 -> "후기 1건"이면 1 출력
    count = get_mamap_review_count("33985")
    print("REVIEW_COUNT:", count)
