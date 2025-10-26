import requests
from bs4 import BeautifulSoup

def get_msgmon_view_and_review(post_id: str):
    """
    https://msgmon.com/shop/read/{post_id}
    페이지에서 조회수와 리뷰수 추출
    """
    url = f"https://msgmon.com/shop/read/{post_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://msgmon.com/",
    }

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    view_count = None
    review_count = None

    # 조회수 span
    view_img = soup.find("img", {"alt": "조회수"})
    if view_img and view_img.find_next("span"):
        try:
            view_count = int(view_img.find_next("span").get_text(strip=True).replace(",", ""))
        except ValueError:
            pass

    # 리뷰수 span
    review_img = soup.find("img", {"alt": "리뷰수"})
    if review_img and review_img.find_next("span"):
        try:
            review_count = int(review_img.find_next("span").get_text(strip=True).replace(",", ""))
        except ValueError:
            pass

    return view_count, review_count


if __name__ == "__main__":
    v, r = get_msgmon_view_and_review("176")
    print("VIEW_COUNT:", v)   # → VIEW_COUNT: 7133
    print("REVIEW_COUNT:", r) # → REVIEW_COUNT: 4
