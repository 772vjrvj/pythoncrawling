import time

import requests
from bs4 import BeautifulSoup
import re
import random


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
    ol_tags = soup.find_all("ol", class_="lItemList")
    if ol_tags:
        last_ol_tag = ol_tags[-1]  # 마지막 ol 태그 선택
        li_tags = last_ol_tag.find_all("li")

        for li in li_tags:
            # li 내부의 a 태그 class="thumb" 찾기
            a_tag = li.find("a", class_="thumb")
            if a_tag and "href" in a_tag.attrs:
                href = a_tag["href"]

                # 정규식을 사용하여 숫자만 추출
                match = re.search(r"/(\d+)", href)
                if match:
                    item_list.append(match.group(1))

    return item_list


def fetch_item_cnt(sw):
    url = f"https://domeggook.com/main/item/itemList.php?sfc=id&sf=id&sw={sw}&sz=100&pg=1"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "host": "domeggook.com",
        "referer": f"https://domeggook.com/main/item/itemList.php?sfc=id&sf=id&sw={sw}&sz=100&pg=0",
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
    total_cnt = 0
    total_page = 0
    if response.status_code != 200:
        print("페이지를 불러오지 못했습니다.")
        return total_cnt, total_page

    soup = BeautifulSoup(response.text, "html.parser")

    # div id="lCnt" 내부에서 숫자 찾기
    lcnt_div = soup.find("div", id="lCnt")

    if lcnt_div:
        b_tag = lcnt_div.find("b")  # <b> 태그 직접 찾기
        if b_tag:
            total_cnt = int(b_tag.text.replace(",", ""))  # 콤마 제거 후 정수 변환
            total_page = (total_cnt // 100) + (1 if total_cnt % 100 > 0 else 0)  # 페이지 계산


    return total_cnt, total_page



def fetch_product_details(product_id):
    base_url = "https://domeggook.com/"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "host": "domeggook.com",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    }

    url = f"{base_url}{product_id}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ {product_id} 페이지를 불러오지 못했습니다.")

    soup = BeautifulSoup(response.text, "html.parser")

    product_data = {
        'URL': url
    }

    # ✅ 판매자명 추출
    seller_tag = soup.find("button", id="lBtnShowSellerInfo")
    if seller_tag:
        seller_name = seller_tag.find("b").text.strip()
        product_data["판매자명"] = seller_name
    else:
        product_data["판매자명"] = ""

    # ✅ 상품번호 추출
    product_num_tag = soup.find("div", id="lInfoHeader")
    if product_num_tag:
        match = re.search(r"상품번호\s*:\s*(\d+)", product_num_tag.text)
        if match:
            product_data["상품번호"] = match.group(1)
        else:
            product_data["상품번호"] = ""
    else:
        product_data["상품번호"] = ""

    # ✅ 상품명 추출
    product_name_tag = soup.find("h1", id="lInfoItemTitle")
    product_data["상품명"] = product_name_tag.text.strip() if product_name_tag else ""

    # ✅ 재고수량 추출
    stock_tag = soup.find("td", class_="lInfoItemContent")
    if stock_tag:
        match = re.search(r"([\d,]+)", stock_tag.text)
        if match:
            product_data["재고수량"] = int(match.group(1).replace(",", ""))
        else:
            product_data["재고수량"] = 0
    else:
        product_data["재고수량"] = 0

    return product_data






if __name__ == "__main__":

    total_cnt, total_page = fetch_item_cnt("huigone7589")
    print(f'total_cnt : {total_cnt}')
    print(f'total_page : {total_page}')
    all_item_list = []
    # 테스트 실행
    for i in range(1, total_page + 1):
        print(f'index {i}')
        item_list = fetch_item_ids("huigone7589", i)
        print(f'item_list : {item_list}')
        all_item_list.extend(item_list)
        print(f'all len : {len(all_item_list)}')
        time.sleep(random.uniform(2, 3))

    print(f'all list : {all_item_list}')
    result_list = []

    for product_id in all_item_list:
        obj = fetch_product_details(product_id)
        print(f'obj : {obj}')
        result_list.append(obj)
        print(f'obj list : {result_list}')
        time.sleep(random.uniform(2, 3))

    print(f'{result_list}')
