import time
import requests
from bs4 import BeautifulSoup
import re
import random
from datetime import datetime
import pandas as pd
import os

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
        li_tags = last_ol_tag.find_all("li", recursive=False)
        print(f'li_tags len : {len(li_tags)}')

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
            total_page = (total_cnt // 52) + (1 if total_cnt % 52 > 0 else 0)  # 페이지 계산

    return total_cnt, total_page


def get_current_formatted_datetime():
    # 현재 날짜와 시간 가져오기
    now = datetime.now()

    # 날짜와 시간을 'YYYY.MM.DD HH:MM:SS' 형식으로 포맷팅
    formatted_datetime = now.strftime("%Y.%m.%d %H:%M:%S")

    return formatted_datetime


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
        'URL': url,
        '판매자명': '',
        '상품번호': '',
        '재고수량': '',
        '수집일': get_current_formatted_datetime()
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

    ids = ["huigone7589"]

    for id in ids:

        # 엑셀 파일 id로 읽어서 객체 리스트 old_result_list 담기
        now_result_list = []
        new_result_list = []
        old_result_list = []
        file_name = f"{id}.xlsx"

        # 엑셀 파일이 존재하면 읽어서 old_result_list에 담기
        if os.path.exists(file_name):
            df = pd.read_excel(file_name, engine='openpyxl')
            old_result_list = df.to_dict(orient='records')  # DataFrame을 리스트[dict] 형태로 변환

        print(f'id : {id}')
        total_cnt, total_page = fetch_item_cnt(id)
        print(f'total_cnt : {total_cnt}')
        print(f'total_page : {total_page}')

        all_item_set = set()  # 기존 리스트를 집합(set)으로 변환
        for i in range(1, total_page + 1):
            print(f'index {i}')
            item_list = fetch_item_ids(id, i)
            print(f'item_list : {item_list}')
            all_item_set.update(item_list)  # 중복을 방지하면서 추가
            time.sleep(random.uniform(2, 3))

        all_item_list = list(all_item_set)  # 다시 리스트로 변환
        print(f'all list : {all_item_list}')
        print(f'all list len: {len(all_item_list)}')

        for product_id in all_item_list:
            obj = fetch_product_details(product_id)
            print(f'obj : {obj}')
            now_result_list.append(obj)
            print(f'obj list : {now_result_list}')

            # obj 복사하여 new_obj 생성
            new_obj = obj.copy()
            new_obj['판매량'] = 0
            new_obj['이전수집일'] = ''
            new_obj['이전재고수량'] = 0

            # old_result_list에서 같은 상품번호를 가진 객체 찾기
            old_obj = next((item for item in old_result_list if item['상품번호'] == obj['상품번호']), None)

            if old_obj:
                # old_obj의 재고수량과 obj의 재고수량 차이 계산 (old_obj가 항상 크거나 같음)
                old_stock = int(old_obj['재고수량']) if old_obj['재고수량'] else 0
                current_stock = int(obj['재고수량']) if obj['재고수량'] else 0
                sales_volume = old_stock - current_stock  # 판매량 계산

                # new_obj에 추가 정보 설정
                new_obj['판매량'] = sales_volume
                new_obj['이전수집일'] = old_obj['수집일']
                new_obj['이전재고수량'] = old_stock

            # new_result_list에 추가
            new_result_list.append(new_obj)

            time.sleep(random.uniform(2, 3))

        # 저장할 파일명 (id.xlsx)
        file_name = f"{id}.xlsx"

        # 데이터프레임 생성
        df = pd.DataFrame(new_result_list, columns=['URL', '판매자명', '상품번호', '판매량', '재고수량', '수집일', '이전재고수량', '이전수집일'])

        # 엑셀 파일로 저장 (파일이 있으면 덮어쓰기)
        df.to_excel(file_name, index=False, engine='openpyxl')

        print(f"엑셀 파일 저장 완료: {file_name}")
