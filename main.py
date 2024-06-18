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
    def __init__(self,
                 temporarilyOutOfStock,
                 no,
                 category,
                 manage_code,
                 product_code,
                 name,
                 wholesale_price,
                 option,
                 features,
                 manufacturer,
                 material,
                 packaging,
                 size,
                 color,
                 delivery,
                 weight,
                 main_slide_images,
                 main_images,
                 detail_image,
                 country_of_origin):
        self.temporarilyOutOfStock = temporarilyOutOfStock
        self.no = no
        self.category = category
        self.manage_code = manage_code
        self.product_code = product_code
        self.name = name
        self.wholesale_price = wholesale_price

        self.option = option

        self.features = features
        self.manufacturer = manufacturer
        self.material = material
        self.packaging = packaging
        self.size = size
        self.color = color
        self.delivery = delivery
        self.weight = weight

        self.main_slide_images = main_slide_images
        self.main_images = main_images
        self.detail_image = detail_image
        self.country_of_origin = country_of_origin

    def __str__(self):
        # main_images_str = ', '.join(self.main_images[:100])
        # main_slide_images_str = ', '.join(self.main_slide_images[:100])
        return (f"구매가능: {self.temporarilyOutOfStock}\n"
                f"번호: {self.no}\n"
                f"카테고리: {self.category}\n"
                f"관리코드: {self.manage_code}\n"
                f"상품코드: {self.product_code}\n"
                f"상품명: {self.name}\n"
                f"도매가: {self.wholesale_price}\n"
                f"옵션: {len(self.option)}\n"
                f"대표 슬라이드 이미지 수: {len(self.main_slide_images)}\n"
                f"대표이미지 수: {len(self.main_images)}\n"
                f"상세이미지 수: {len(self.detail_image)}\n"
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


def get_info(table, th_string):
    th_element = table.find('th', string=th_string)
    if th_element:
        td_element = th_element.find_next_sibling('td')
        if td_element:
            # 모든 텍스트를 추출하여 태그를 무시합니다.
            return td_element.get_text(separator=' ', strip=True)
    return ''


def fetch_product_details(values, search_text):
    products = []
    for idx, value in enumerate(values):
        print(f"== 순서 : {idx + 1}====================")
        print(f"== value : {value}====================")
        url = f"https://dometopia.com/goods/view?no={value}&code="
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        goods_codes = soup.find_all(class_="goods_code")
        if len(goods_codes) < 2:
            print(f"Error: Not enough 'goods_code' elements found for product {value}")
            continue

        # 구매가능
        temporarilyOutOfStock = soup.find('span', class_='button bgred')
        if temporarilyOutOfStock:
            temporarilyOutOfStock = temporarilyOutOfStock.get_text().strip()

        # 상품 고유 번호 value

        # 카테고리 search_text

        # 상품코드 (모델명)
        product_code = goods_codes[0].text.strip()
        if product_code.find("GKM") != -1:
            print("GKM은 포함할수 없습니다.")
            continue

        # 옵션
        doto_option_hide_div = soup.find('div', class_='doto-option-hide')
        if doto_option_hide_div:
            doto_option_hide_div = str(doto_option_hide_div)

        # 상세내용
        table = soup.find('table', class_='table-01')

        features = get_info(table, '상품용도 및 특징')
        manufacturer = get_info(table, '제조자/수입자')
        material = get_info(table, '상품재질')
        packaging = get_info(table, '포장방법')
        size = get_info(table, '사이즈')
        color = get_info(table, '색상종류')
        delivery = get_info(table, '배송기일')
        weight = get_info(table, '무게(포장포함)')


        # 관리코드
        manage_code = goods_codes[1].text.strip()


        # 상품명
        name = soup.find(class_="pl_name").h2.text.strip()


        # 도매가

        # class="fl tc w20 list2 lt_line" 요소 찾기
        list2_elements = soup.find_all(class_="fl tc w20 list2 lt_line")

        # 요소가 존재하는지 확인
        price_text = ''
        if not list2_elements:
            if len(goods_codes) > 2:
                wholesale_price = re.sub(r'\D', '', goods_codes[2].text.strip())
            else:
                wholesale_price = "0"
        else:
            # class="fl tc w20 list2 lt_line" 중 첫 번째 요소 찾기
            first_list2_element = list2_elements[0]

            # 첫 번째 요소 안에서 class="price_red" 찾기
            price_red_element = first_list2_element.find(class_="price_red")

            # 텍스트 추출
            price_text = price_red_element.get_text()
            wholesale_price = re.sub(r'\D', '', price_text)



        # 대표 슬라이드 이미지 전체
        main_slide_images = []
        slides_container = soup.find('div', class_='slides_container hide')
        if slides_container:
            for img_tag in slides_container.find_all('img')[:100]:
                src = img_tag.get('src')
                if src:
                    main_slide_images.append(src)

        # 대표이미지 전체
        main_images = []
        pagination = soup.find('ul', class_='pagination clearbox')
        if pagination:
            for img_tag in pagination.find_all('img')[:100]:
                src = img_tag.get('src')
                if src:
                    main_images.append(src)

        # 상세이미지 전체
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

        # 제조국
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

        product = Product(
            temporarilyOutOfStock=temporarilyOutOfStock,
            no=value,
            category=search_text,
            manage_code=manage_code,
            product_code=product_code,
            name=name,
            wholesale_price=wholesale_price,
            option=doto_option_hide_div,

            features=features,
            manufacturer=manufacturer,
            material=material,
            packaging=packaging,
            size=size,
            color=color,
            delivery=delivery,
            weight=weight,

            main_slide_images=main_slide_images,
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
    for i in range(1, page + 1):
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
    headers = (['구매가능여부',
               'NO',
               '카테고리',
               '관리코드',
               '상품코드 (모델명)',
               '상품명',
               '도매가',
               '옵션',

               '상품용도 및 특징',
               '제조자/수입자',
               '상품재질',
               '포장방법',
               '사이즈',
               '색상종류',
               '배송기일',
               '무게(포장포함)',

               '제조국',
               '상세이미지']
               + [f'대표 슬라이드 이미지{i+1}' for i in range(100)]
               + [f'대표이미지{i+1}' for i in range(100)])
    sheet.append(headers)

    for product in products:
        row = [
            product.temporarilyOutOfStock,
            product.no,
            product.category,
            product.manage_code,
            product.product_code,
            product.name,
            product.wholesale_price,
            product.option,

            product.features,
            product.manufacturer,
            product.material,
            product.packaging,
            product.size,
            product.color,
            product.delivery,
            product.weight,

            product.country_of_origin,
            product.detail_image
        ]

        row.extend(product.main_slide_images[:100])
        row.extend([''] * (100 - len(product.main_slide_images)))

        row.extend(product.main_images[:100])
        row.extend([''] * (100 - len(product.main_images)))
        sheet.append(row)

    workbook.save(filename)

def main():

    main_start_time = time.time()  # 시작 시간 기록
    get_current_time()

    # page = 1
    # page = 53
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

    # 테스크 케이스 다른경우 3가지
    # values = ['192874', '55235', '181042']
    # search_text = "GT"

    products = fetch_product_details(values, search_text)
    save_to_excel(products)

    main_end_time = time.time()  # 종료 시간 기록
    get_current_time()
    main_total_time = main_end_time - main_start_time  # 총 걸린 시간 계산
    print(f"전체 걸린시간: {main_total_time} 초")

if __name__ == "__main__":
    main()