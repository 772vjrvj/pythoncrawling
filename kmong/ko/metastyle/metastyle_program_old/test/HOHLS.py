import os
import glob
import requests
import csv
from bs4 import BeautifulSoup
import sys
import re

# CATEGORY = 'Nine West Blouses'
# CATEGORY = 'Womens Sonoma Goods for Life Blouses'
# CATEGORY = "Croft & Barrow Blouses"
# CATEGORY = "LC Lauren Conrad Blouses"
# CATEGORY = "Simply Vera Vera Wang Blouses"

# CATEGORY = "Women's Nine West Pants"
# CATEGORY = "Sonoma Goods for Life Women's Pants"
# CATEGORY = "Croft & Barrow Pants for Women"
# CATEGORY = "LC Lauren Conrad Pants"
# CATEGORY = "Simply Vera Vera Wang Pants"

# CATEGORY = "Womens Nine West Skirts & Skorts"
# CATEGORY = "Womens Sonoma Goods For Life Skirts & Skorts"
# CATEGORY = "Women's Croft & Barrow Skirts"
# CATEGORY = "Womens LC Lauren Conrad Skirts & Skorts"
# CATEGORY = "Simply Vera Vera Wang Skirts"

# CATEGORY = "Nine West Shorts"
# CATEGORY = "Women's Sonoma Goods for Life Shorts"
# CATEGORY = "Women's Croft & Barrow Shorts"
# CATEGORY = "LC Lauren Conrad Shorts"
# CATEGORY = "Simply Vera Vera Wang Shorts"

# CATEGORY = "Nine West Dresses"
# CATEGORY = "Women's Sonoma Goods for Life Dresses"
# CATEGORY = "Croft & Barrow Dresses"
# CATEGORY = "Women's LC Lauren Conrad Dresses"
# CATEGORY = "Women's Simply Vera Vera Wang Dresses"

# CATEGORY = "Men's Sonoma Goods for Life Button Down Shirts"
# CATEGORY = "Mens Sonoma Goods For Life Casual Pants"
# CATEGORY = "Men's Sonoma Goods for Life Shorts"
# CATEGORY = "Apt. 9 Button Down Shirts for Men"
# CATEGORY = "Mens Apt. 9 Casual Pants"




# HTML 파일이 있는 디렉토리 경로
HTML_DIR = os.path.join(r"D:\GIT\pythoncrawling\kmong\ko\metastyle\metastyle_program_old\downloads", CATEGORY)

# 이미지 저장 디렉토리
IMAGE_DIR = os.path.join(os.getcwd(), "images", "KOHLS", CATEGORY)

# CSV 파일 경로
CSV_FILE = os.path.join(os.getcwd(), f"{CATEGORY}.csv")

WEB_SITE_NAME = "KOHL'S"
WEB_SITE = 'https://www.kohls.com'

# 이미지 저장 폴더 생성
os.makedirs(IMAGE_DIR, exist_ok=True)

class Product:
    def __init__(self, product_id, product_url, image_url, product_name):
        self.product_id = product_id
        self.product_url = product_url
        self.image_url = image_url
        self.image_name = None
        self.product_name = product_name
        self.category = CATEGORY
        self.image_success = "N"
        self.web_site = WEB_SITE
        self.web_site_name = WEB_SITE_NAME

def extract_product_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser', from_encoding='utf-8')

    # ul 태그의 id="productsContainer" 찾기
    products_container = soup.find('ul', id='productsContainer')
    if not products_container:
        return []

    products = []

    for li in products_container.find_all('li'):
        product_id = li.get("data-id")

        # product_url 추출
        left_container = li.find(class_="products-container-left")
        product_url = ""
        if left_container:
            prod_img_block = left_container.find(class_="prod_img_block")
            if prod_img_block:
                a_tag = prod_img_block.find('a', href=True)
                if a_tag:
                    href = a_tag['href']
                    product_url = href if "https://www.kohls.com" in href else "https://www.kohls.com" + href

        # image_url 추출
        image_url = ""
        if a_tag:
            img_tags = a_tag.find_all('img')
            if img_tags:
                img_tag = img_tags[0] if len(img_tags) == 1 else img_tags[1]  # 1개면 첫 번째, 2개면 두 번째 선택
                srcset = img_tag.get('srcset', '')
                if srcset:
                    first_src = srcset.split(',')[0].split('?')[0]
                    image_url = f"{first_src}?wid=1500&hei=1500&op_sharpen=1&qlt=60 1500w"

        # product_name 추출
        product_name = ""
        right_container = li.find(class_="products-container-right")
        if right_container:
            name_block = right_container.find(class_="prod_nameBlock")
            if name_block:
                product_name = name_block.get_text(strip=True)

        if product_id and product_url and image_url and product_name:
            products.append(Product(product_id, product_url, image_url, product_name))

    return products


def download_image(product):
    try:
        img_url = product.image_url.split()[0]  # 실제 이미지 URL만 추출

        # URL이 '//'로 시작하면 'https:' 추가
        if img_url.startswith("//"):
            img_url = "https:" + img_url

        response = requests.get(img_url, stream=True)
        if response.status_code == 200:

            # 특수문자를 안전한 형식으로 변환 (파일명에서 사용할 수 없는 문자 → '_')
            safe_product_name = re.sub(r'[\\/*?:"<>|]', '_', product.product_name)

            # 기본 이미지 파일명
            base_image_name = f"{safe_product_name}_{product.product_id}"
            image_name = f"{base_image_name}.jpg"
            file_path = os.path.join(IMAGE_DIR, image_name)

            # 중복 파일명 방지
            counter = 1
            while os.path.exists(file_path):
                image_name = f"{base_image_name}({counter}).jpg"
                file_path = os.path.join(IMAGE_DIR, image_name)
                counter += 1

            # 이미지 저장
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            print(f"Downloaded: {file_path}")
            product.image_success = "Y"
            product.image_name = image_name
        else:
            print(f"Failed to download {img_url}, Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading {product.image_url}: {e}")


def save_to_csv(products):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["web_site", "web_site_name", "category", "product_id", "product_url", "product_name","image_url", "image_name", "image_success"])
        for product in products:
            writer.writerow([product.web_site, product.web_site_name, product.category, product.product_id, product.product_url, product.product_name, product.image_url, product.image_name, product.image_success])
    print(f"CSV file saved: {CSV_FILE}")

def main():
    html_files = glob.glob(os.path.join(HTML_DIR, "*.html"))
    all_products = []

    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
            products = extract_product_data(html_content)
            all_products.extend(products)

    for index, product in enumerate(all_products):
        print(f'product_id : {product.product_id}, product_name : {product.product_name}, index : {index}')
        download_image(product)

    save_to_csv(all_products)

if __name__ == "__main__":
    main()
    sys.exit(0)
