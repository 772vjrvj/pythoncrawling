import requests
from bs4 import BeautifulSoup
import time

def get_url(gost_code):
    url = f"https://gostperevod.com/{gost_code.replace('.', '-').replace(' ', '-').lower()}.html"
    print(f"Fetching URL: {url}")  # 디버깅용 출력
    r = requests.get(url)
    return r

def get_description(gost_code):
    response = get_url(gost_code)
    soup = BeautifulSoup(response.text, 'html.parser')
    description_tag = soup.find('h2', class_='h6 my-0 font-weight-normal')
    if description_tag:
        return description_tag.get_text(strip=True)
    else:
        return "Description not found"


def main():

    # GOST 코드 목록
    gost_codes = [
        "GOST 12.1.018-93",
        "GOST 34.603-92",
        # 여기에 더 많은 GOST 코드를 추가하세요
    ]

    for code in gost_codes:
        try:
            description = get_description(code)
            print(f"{code}: {description}")
        except Exception as e:
            print(f"An error occurred for {code}: {e}")
        time.sleep(1)  # 너무 빠른 요청을 방지하기 위해 1초

if __name__ == "__main__":
    main()