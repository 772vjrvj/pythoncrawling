import requests
from bs4 import BeautifulSoup

def get_msgkingdom_review_count(it_id: str) -> int | None:
    """
    https://msgkingdom.com/shop/item.php?ap=1&it_id={it_id}
    페이지에서 <span class="item_use_count">N</span> 의 N만 추출
    """
    url = f"https://msgkingdom.com/shop/item.php?ap=1&it_id={it_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://msgkingdom.com/",
    }

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    span = soup.select_one("span.item_use_count")
    if span:
        try:
            return int(span.get_text(strip=True))
        except ValueError:
            return None
    return None


if __name__ == "__main__":
    # 예시 실행
    review_count = get_msgkingdom_review_count("1692941551")
    print("REVIEW_COUNT:", review_count)  # → REVIEW_COUNT: 13
