import requests
from bs4 import BeautifulSoup
import json

def fetch_kakao_products(kwd, page):
    url = f"https://store.kakao.com/a/search/products?q={kwd}&sort=POPULAR&timestamp=1719163445273&page={page}&size=100&_=1719163445274"

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Referer': 'https://store.kakao.com/search/result/product?q=%EB%83%89%EB%A9%B4',
        'X-Shopping-Referrer': 'https://store.kakao.com/?__ld__=&oldRef=https:%2F%2Fwww.google.com%2F',
        'X-Shopping-Tab-Id': '7c4f069c14b67002faa0e1',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return None

# 예제 실행
if __name__ == "__main__":
    kwd = "냉면"  # 검색 키워드
    page = 1  # 페이지 번호

    products_data = fetch_kakao_products(kwd, page)

    if products_data:
        # 데이터를 적절히 처리
        print(json.dumps(products_data, indent=4, ensure_ascii=False))
