# -*- coding: utf-8 -*-
import requests

def main():
    url = "https://store.kakao.com/a/f-s/home/talk-deal/products"

    # === 최소 안전 헤더 (크롤링 감지 최소화용) ===
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/141.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://store.kakao.com/home/talkdeal/category/0",
        "X-Requested-With": "XMLHttpRequest",
    }

    params = {
        "timestamp": "1761568900980",
        "page": "23",
        "size": "20",
        "sortType": "USER_COUNT",
        "isBestArea": "false",
        "searchGroupId": "0",
        "_": "1761568900980"
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    print(response.json())

if __name__ == "__main__":
    main()
