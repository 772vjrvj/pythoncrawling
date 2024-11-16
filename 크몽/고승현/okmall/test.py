import requests
from bs4 import BeautifulSoup

def fetch_product_name(url):
    # 요청 헤더 설정
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": "www.okmall.com",
        "Sec-CH-UA": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": "\"Windows\"",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    try:
        # GET 요청 보내기
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
    except requests.RequestException as e:
        print(f"요청 오류 발생: {e}")
        return None

    # 기본 객체 초기화
    obj = {
        '상품링크': url,
        '브랜드': '',
        '상품명': '',
        '가격': '',
        '택 사이즈': []
    }

    # BeautifulSoup을 사용해 HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")

    # 상품명 가져오기
    product_name_element = soup.find(id="ProductNameArea")
    if product_name_element:
        product_name = product_name_element.find(class_="prd_name")
        if product_name:
            obj['상품명'] = product_name.get_text(strip=True)

    # 브랜드 정보 가져오기
    brand_img_box = soup.find(class_="brand_img_box")
    if brand_img_box:
        brand_tit = brand_img_box.find(class_="brand_tit")
        if brand_tit:
            obj['브랜드'] = brand_tit.get_text(strip=True)

    # 가격 정보 가져오기
    real_price = soup.find(class_="real_price")
    if real_price:
        price = real_price.find(class_="price")
        if price:
            obj['가격'] = ''.join(price.find_all(string=True)).strip()

    # 택 사이즈 정보 가져오기
    product_opt_list = soup.find(id="ProductOPTList")
    if product_opt_list:
        table = product_opt_list.find("table", class_="shoes_size")
        if table:
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) > 1:  # 두 번째 <td>가 있는지 확인
                        size_text = cols[1].get_text(strip=True)
                        obj['택 사이즈'].append(size_text)

    # obj를 반환
    return obj

def main():
    url = "https://www.okmall.com/products/view?no=766569&item_type=&cate=20008666&uni=M"
    product_name = fetch_product_name(url)
    if product_name:
        print(f"상품 이름: {product_name}")

if __name__ == "__main__":
    main()

