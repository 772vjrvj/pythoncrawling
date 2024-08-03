import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

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

def main(urls):
    data = []

    for url in urls:
        html = fetch_html(url)
        if not html:
            continue

        soup = BeautifulSoup(html, 'html.parser')

        product_name = parse_product_name(soup)
        product_info = parse_product_info(soup)
        main_image = parse_main_image(soup)
        detail_images = parse_detail_images(soup)

        product_data = {
            'URL': url,
            '상품명': product_name,
            '상품코드': product_info.get('상품코드'),
            '상품정보': product_info.get('상품정보'),
            '배송비': product_info.get('배송비'),
            '상품상태': product_info.get('상품상태'),
            '상품 이미지': main_image,
            '상세설명 이미지': ", ".join([img_src for _, img_src in detail_images])
        }

        data.append(product_data)

        # 1~2초 사이의 랜덤한 시간 동안 지연
        time.sleep(random.uniform(1, 2))

    df = pd.DataFrame(data)
    df.to_excel('상품정보.xlsx', index=False)
    print("엑셀 파일로 저장되었습니다: 상품정보.xlsx")

if __name__ == "__main__":
    urls = [
        'https://www.feelway.com/view_goods.php?g_no=6867303432',
        'https://www.feelway.com/view_goods.php?g_no=7250078152',
        'https://www.feelway.com/view_goods.php?g_no=6676335772',
        'https://www.feelway.com/view_goods.php?g_no=6781577307',
        'https://www.feelway.com/view_goods.php?g_no=7266878906',
        'https://www.feelway.com/view_goods.php?g_no=6861214462',
        'https://www.feelway.com/view_goods.php?g_no=6780211086',
        'https://www.feelway.com/view_goods.php?g_no=6464706594',
        'https://www.feelway.com/view_goods.php?g_no=6915182512',
        'https://www.feelway.com/view_goods.php?g_no=7138101250'
    ]
    main(urls)
