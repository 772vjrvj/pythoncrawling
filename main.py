import requests
from bs4 import BeautifulSoup

def fetch_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def parse_product_name(soup):
    try:
        product_name = soup.select_one('.prd_detail_basic.clearfix .info .title').get_text(strip=True)
        return product_name
    except AttributeError:
        print("Error parsing product name")
        return None

def parse_product_info(soup):
    product_info = {}
    try:
        for tr in soup.select('.event-viewgood-info tbody tr'):
            th = tr.select_one('th')
            td = tr.select_one('td')
            if th and td:
                th_text = th.get_text(strip=True)
                td_text = td.get_text(strip=True)
                if th_text == '상품코드':
                    product_info['상품코드'] = td_text
                elif th_text == '상품정보':
                    product_info['상품정보'] = td_text
                elif th_text == '배송비':
                    product_info['배송비'] = td_text
                elif th_text == '상품상태':
                    product_info['상품상태'] = td_text
    except AttributeError:
        print("Error parsing product info")
    return product_info

def parse_main_image(soup):
    try:
        main_image = soup.select_one('.main_image img')['src']
        return main_image
    except (AttributeError, TypeError):
        print("Error parsing main image")
        return None

def parse_detail_images(soup):
    detail_images = []
    try:
        for idx, img_tag in enumerate(soup.select('.goods_component.position-fixed img'), start=1):
            detail_images.append((f"상세설명 이미지{idx}", img_tag['src']))
    except AttributeError:
        print("Error parsing detail images")
    return detail_images

def main(url):
    html = fetch_html(url)
    if not html:
        return

    soup = BeautifulSoup(html, 'html.parser')

    product_name = parse_product_name(soup)
    if product_name:
        print(f"상품명: {product_name}")

    product_info = parse_product_info(soup)
    for key, value in product_info.items():
        print(f"{key}: {value}")

    main_image = parse_main_image(soup)
    if main_image:
        print(f"상품 이미지: {main_image}")

    detail_images = parse_detail_images(soup)
    for img_desc, img_src in detail_images:
        print(f"{img_desc}: {img_src}")

if __name__ == "__main__":
    url = 'https://www.feelway.com/view_goods.php?g_no=7138101250'
    main(url)
