import requests
from bs4 import BeautifulSoup
import re

def fetch_item_ids(sw, pg):
    url = f"https://domeggook.com/main/item/itemList.php?sfc=id&sf=id&sw={sw}&sz=100&pg={pg}"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "host": "domeggook.com",
        "referer": f"https://domeggook.com/main/item/itemList.php?sfc=id&sf=id&sw={sw}&sz=100&pg={pg-1}",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("페이지를 불러오지 못했습니다.")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    item_list = []

    # ol 태그 내의 li 요소 찾기
    ol_tag = soup.find("ol", class_="lItemList")
    if ol_tag:
        li_tags = ol_tag.find_all("li")

        for li in li_tags:
            # li 내부의 a 태그 class="thumb" 찾기
            a_tag = li.find("a", class_="thumb")
            if a_tag and "href" in a_tag.attrs:
                href = a_tag["href"]

                # 정규식을 사용하여 숫자만 추출
                match = re.search(r"/(\d+)", href)
                if match:
                    item_list.append(match.group(1))

    print(item_list)
    return item_list

# 테스트 실행
fetch_item_ids("huigone7589", 3)
