import requests
from bs4 import BeautifulSoup
import re
import pytz
from datetime import datetime
import time
from openpyxl import Workbook

main_start_time = ""
main_end_time = ""
main_total_time = ""

start_time = ""
end_time = ""
total_time = ""




class Product:
    def __init__(self, no, category, manage_code, product_code, name, wholesale_price, main_images, detail_image, country_of_origin):
        self.no = no
        self.category = category
        self.manage_code = manage_code
        self.product_code = product_code
        self.name = name
        self.wholesale_price = wholesale_price
        self.main_images = main_images
        self.detail_image = detail_image
        self.country_of_origin = country_of_origin

    def __str__(self):
        main_images_str = ', '.join(self.main_images[:50])
        return (f"번호: {self.no}\n"
                f"카테고리: {self.category}\n"
                f"관리코드: {self.manage_code}\n"
                f"상품코드: {self.product_code}\n"
                f"상품명: {self.name}\n"
                f"도매가: {self.wholesale_price}\n"
                f"대표이미지: {main_images_str}\n"
                f"상세이미지: {self.detail_image}\n"
                f"제조국: {self.country_of_origin}")

def get_current_time():
    # 한국 시간대 정의
    korea_tz = pytz.timezone('Asia/Seoul')

    # 현재 시간을 UTC 기준으로 가져오기
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    # 한국 시간으로 변환
    now_korea = now_utc.astimezone(korea_tz)

    # 시간을 "yyyy-mm-dd hh:mm:ss" 형식으로 포맷팅
    formatted_time_korea = now_korea.strftime('%Y-%m-%d %H:%M:%S')
    print(formatted_time_korea)


def fetch_product_details(values, search_text):
    products = []
    for idx, value in enumerate(values):
        print(f"== 순서 : {idx + 1}====================")
        url = f"https://dometopia.com/goods/view?no={value}&code="
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        goods_codes = soup.find_all(class_="goods_code")
        if len(goods_codes) < 2:
            print(f"Error: Not enough 'goods_code' elements found for product {value}")
            continue

        product_code = goods_codes[0].text.strip()
        manage_code = goods_codes[1].text.strip()


        name = soup.find(class_="pl_name").h2.text.strip()

        price_element = soup.find(class_="price_red")
        if price_element:
            wholesale_price = re.sub(r'\D', '', price_element.text.strip())
        else:
            price_element_alt = soup.find_all(class_="goods_code")
            if len(price_element_alt) > 2:
                wholesale_price = re.sub(r'\D', '', price_element_alt[2].text.strip())
            else:
                wholesale_price = "0"

        main_images = []
        pagination = soup.find('ul', class_='pagination clearbox')
        if pagination:
            for img_tag in pagination.find_all('img')[:50]:
                src = img_tag.get('src')
                if src:
                    main_images.append(src)

        detail_images = []
        detail_img_div = soup.find('div', class_='detail-img')
        if detail_img_div:
            img_tags = detail_img_div.find_all('img')
            for img_tag in img_tags:
                src = img_tag.get('src')
                if src:
                    if not src.startswith('http'):
                        src = 'https://dometopia.com' + src
                    detail_images.append(f'<img src="{src}">')
            detail_image = '<div style="text-align: center;">' + ''.join(detail_images) + '<br><br><br></div>'
        else:
            detail_image = ""

        country_text = ""
        gil_table = soup.find('table', class_='gilTable')
        if gil_table:
            th_tags = gil_table.find_all('th')
            for th in th_tags:
                if '원산지' in th.text or '제조국' in th.text:
                    td = th.find_next_sibling('td')
                    if td:
                        country_text = td.text.strip()
                        break

        # if not country_text and search_text == "GK":
        #     country_text = "대한민국"


        product = Product(
            no=value,
            category=search_text,
            manage_code=manage_code,
            product_code=product_code,
            name=name,
            wholesale_price=wholesale_price,
            main_images=main_images,
            detail_image=detail_image,
            country_of_origin=country_text
        )

        # 여기서 출력
        print(product)
        products.append(product)
    return products

def fetch_goods_values(page, search_text):
    values = []
    for i in range(151, page + 1):
        url = f"https://dometopia.com/goods/search?page={i}&search_text={search_text}&popup=&iframe=&category1=&old_category1=&old_search_text={search_text}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        checkboxes = soup.find_all('input', {'class': 'list_goods_chk', 'name': 'goods_seq[]'})
        for checkbox in checkboxes:
            values.append(checkbox['value'])
    return values

def save_to_excel(products, filename='products.xlsx'):
    workbook = Workbook()
    sheet = workbook.active
    headers = ['NO', '카테고리', '관리코드', '상품코드 (모델명)', '상품명', '도매가', '제조국', '상세이미지'] + [f'대표이미지{i+1}' for i in range(50)]
    sheet.append(headers)

    for product in products:
        row = [
            product.no,
            product.manage_code,
            product.product_code,
            product.name,
            product.wholesale_price,
            product.country_of_origin,
            product.detail_image
        ]
        row.extend(product.main_images[:50])
        row.extend([''] * (50 - len(product.main_images)))
        sheet.append(row)

    workbook.save(filename)

def main():

    main_start_time = time.time()  # 시작 시간 기록
    get_current_time()

    # page = 53
    # page = 2
    # search_text = "GK"

    page = 214
    search_text = "GT"




    print(f"======================================")
    start_time = time.time()  # 시작 시간 기록
    get_current_time()

    values = fetch_goods_values(page, search_text)

    print(f"목록 수: {len(values)}")
    end_time = time.time()  # 종료 시간 기록
    total_time = end_time - start_time  # 총 걸린 시간 계산
    print(f"목록 전체조회 걸린시간: {total_time} 초")
    get_current_time()
    print(f"======================================")


    products = fetch_product_details(values, search_text)
    save_to_excel(products)

    main_end_time = time.time()  # 종료 시간 기록
    get_current_time()
    main_total_time = main_end_time - main_start_time  # 총 걸린 시간 계산
    print(f"전체 걸린시간: {main_total_time} 초")

if __name__ == "__main__":
    main()