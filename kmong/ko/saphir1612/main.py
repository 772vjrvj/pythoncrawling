import time

import requests
from bs4 import BeautifulSoup
import pandas as pd

# 요청 헤더 설정


def get_detail(action, product_no):
    url = "https://saphir1612.shop/product/option_preview.html"
    headers = {
        "authority": "saphir1612.shop",
        "method": "POST",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://saphir1612.shop",
        "priority": "u=1, i",
        "referer": "https://saphir1612.shop/category/BEST/45/?page=1",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    payload = {
        "product_no": product_no,
        "action": action
    }

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code != 200:
        print(f"Failed to fetch details for product_no: {product_no}, action: {action}. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    ul = soup.find("ul", class_="xans-element- xans-product xans-product-optionpreviewlist")

    if not ul:
        print(f"No details found for product_no: {product_no}, action: {action}")
        return []

    li_elements = ul.find_all("li")
    return [li.text.strip() for li in li_elements]

def get_str_option(options):

    # 색상과 사이즈를 각각 추출
    colors = set()
    sizes = set()

    for option in options:
        parts = option.split(' / ')
        color = parts[0].split(': ')[1].strip()
        size = parts[1].split(': ')[1].strip()
        colors.add(color)
        sizes.add(size)

    # 원하는 형식으로 출력
    formatted_option = f"색상{{{'|'.join(colors)}}}//사이즈{{{'|'.join(sizes)}}}"
    return formatted_option


def save_to_excel(data, filename="output.xlsx"):
    """데이터를 엑셀 파일에 저장하거나 기존 파일에 추가"""
    try:
        # 기존 파일 읽기
        existing_data = pd.read_excel(filename)
        updated_data = pd.concat([existing_data, pd.DataFrame(data)], ignore_index=True)
    except FileNotFoundError:
        # 파일이 없으면 새로 생성
        updated_data = pd.DataFrame(data)

    # 엑셀 파일로 저장
    updated_data.to_excel(filename, index=False)
    print(f"Data successfully saved to {filename}")


def main():

    headers = {
        "authority": "saphir1612.shop",
        "method": "GET",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }


    base_url = "https://saphir1612.shop/category/BEST/45/?page={}"
    page = 1
    page_data = []

    while True:
        url = base_url.format(page)
        response = requests.get(url, headers=headers)
        if page == 3:
            break

        if response.status_code != 200:
            print(f"Failed to fetch page {page}. Status code: {response.status_code}")
            break

        soup = BeautifulSoup(response.content, "html.parser")
        prd_list = soup.find("ul", class_="prdList grid5")

        if not prd_list:
            print("No more products found. Exiting loop.")
            break

        li_elements = prd_list.find_all("li", recursive=False)

        for li in li_elements:
            obj = {}

            # 상품명 추출
            prdList_item_div = li.find("div", class_="prdList__item")
            description_div = prdList_item_div.find("div", class_="description")
            name_div = description_div.find("div", class_="name")
            name_div_a_tag = name_div.find("a")
            spans = name_div_a_tag.find_all("span", recursive=False)

            if len(spans) > 1:
                obj["상품명"] = spans[1].text.strip()

            # 타입과 ID 추출
            thumbnail_div = li.find("div", class_="thumbnail")
            icon_box = thumbnail_div.find("div", class_="icon__box")
            option_span = icon_box.find("span", class_="option")
            option_span_a_tag = option_span.find("a")

            action = ""
            product_no = ""

            if option_span_a_tag:
                onclick_value = option_span_a_tag.get("onclick", "")
                if onclick_value:
                    parts = onclick_value.split(",")
                    if len(parts) > 2:
                        action = parts[1].strip().replace("'", "")
                        product_no = parts[2].strip().replace("'", "")

            option = get_detail(action, product_no)
            formatted_option = get_str_option(option)
            obj["option"] = formatted_option
            obj["page"] = page
            if obj:
                page_data.append(obj)

            print(f'obj : {obj}')

        # 페이지 데이터 엑셀에 저장
        save_to_excel(page_data)

        print(f"\npage :{page}, page_data : {page_data}")
        page += 1
        time.sleep(1)

    print(page_data)


# 메인함수
if __name__ == "__main__":
    main()