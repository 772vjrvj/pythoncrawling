import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd


# 함수화한 요청 함수
def get_review_links(page):
    url = f"https://ecostore.imweb.me/review/?q=YToyOntzOjEyOiJrZXl3b3JkX3R5cGUiO3M6MzoiYWxsIjtzOjQ6InBhZ2UiO2k6OTt9&page={page}&only_photo=Y"
    headers = {
        "authority": "ecostore.imweb.me",
        "method": "GET",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve data from page {page}")
        return None

# 리뷰의 HTML에서 데이터를 추출하는 함수
# 리뷰의 HTML에서 데이터를 추출하는 함수
def parse_review_details(html):
    soup = BeautifulSoup(html, 'html.parser')

    # 이미지 리스트 추출 (class="item-image" 의 src 값)
    images = [img['src'] for img in soup.select('.item-image')]

    # 작성자(author)와 날짜(date) 추출 (class="inline-blocked" 중 첫번째는 작성자, 두번째는 날짜)
    author_element = soup.select('.inline-blocked')
    author = author_element[0].text.strip() if len(author_element) > 0 else ''
    date = author_element[1].text.strip() if len(author_element) > 1 else ''

    # 리뷰 내용(content) 추출 (class="txt" 안의 텍스트)
    content_element = soup.select_one('.txt')
    content = content_element.text.strip() if content_element else ''

    # 제품 이름(product) 추출 (class="prod_name" 안 a 태그의 텍스트)
    product_element = soup.select_one('.prod_name a')
    product = product_element.text.strip() if product_element else ''

    # 별점 갯수(count) 추출 (class="bts bt-star active"의 갯수)
    star_count = len(soup.select('.bts.bt-star.active'))

    return {
        'author': author,
        'date': date,
        'content': content,
        'product': product,
        'images': images,
        'star_count': star_count
    }



# 링크에서 POST.viewReviewPostDetail의 파라미터 추출하는 함수
def extract_review_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    review_data = []

    # 모든 a 태그 중 class가 post_link_wrap _fade_link인 것을 찾음
    links = soup.find_all('a', class_='post_link_wrap _fade_link')

    for link in links:
        onclick_content = link.get('onclick', '')

        # 정규식을 사용하여 POST.viewReviewPostDetail의 파라미터 추출
        match = re.search(r"POST\.viewReviewPostDetail\('(\d+)','(.*?)'\)", onclick_content)
        if match:
            idx = match.group(1)
            board_code = match.group(2)
            review_data.append({
                'idx': idx,
                'board_code': board_code
            })

    return review_data

# POST 요청을 보내고 필요한 데이터를 추출하는 함수
def get_review_details(review):
    url = "https://ecostore.imweb.me/ajax/review_post_detail_view.cm"
    headers = {
        "authority": "ecostore.imweb.me",
        "method": "POST",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        # "cookie": 'IMWEBVSSID=b00orohltaflgvdpar5meula0f25enac2f0ubb97uartcmg5o3a5assvpv58n1lipeo3fvr263hr69deh6l6mv7it4vqth3frh5eot2; al=KR; FB_EXTERNAL_ID=u201902115c60f0dbbd2ba20241003abec0e5ed3f60; _kmpid=km|ecostore.imweb.me|1727881299971|8cbd81c4-da5e-4917-9b2b-a35bca1f5a28; _kmpid=km|imweb.me|1727881299971|8cbd81c4-da5e-4917-9b2b-a35bca1f5a28; _gcl_au=1.1.1625530018.1727881301; _ga=GA1.1.989162612.1727881301; _fwb=91d9esOH3XToJFBCPsB3ox.1727881300808; _fbp=fb.1.1727881300899.9774071720206871; keepgrowUserData={"kg_user":{"uuid":"89f6b0ec-bbdb-48ac-95ed-c5ffd43358d8","is_member":"","member_type":"","create_date":"","last_login_date":""},"kg_product":{"page_view_count":0,"last_create_date":""},"kg_order":{"initiate_checkout":0,"payment_count":0,"last_create_date":""}}; SITE_STAT_SID=2024100366fd605345af34.35230200; SITE_STAT_SID_m20221012538707013dece=2024100366fd605345b143.74494053; _CHAT_DEVICEID=1924DC04DE8; CUR_STAMP=1727881301479; wcs_bt=s_4714e909390a:1727882106; _ga_ENMT163G5Y=GS1.1.1727881300.1.1.1727882890.60.0.0',
        "origin": "https://ecostore.imweb.me",
        "referer": "https://ecostore.imweb.me/review/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    payload = {
        'idx': review['idx'],
        'board_code': review['board_code']
    }

    print(f'payload : {payload}')

    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.content  # 바이트 데이터 반환
    else:
        print(f"Failed to retrieve details for idx: {review['idx']}")
        return None

# 응답 받은 데이터를 처리하는 함수
def process_response(response):
    # 바이트 데이터를 UTF-8로 디코딩
    decoded_response = response.decode('utf-8')

    # JSON 형식으로 응답 데이터 파싱
    response_json = json.loads(decoded_response)

    # HTML 데이터를 추출
    html_data = response_json.get("html", "")

    # HTML 데이터를 BeautifulSoup으로 파싱
    soup = BeautifulSoup(html_data, 'html.parser')

    # 이미지 리스트 추출 (class="item-image" 의 src 값)
    images = [img['src'] for img in soup.select('.item-image')]

    # 작성자(author)와 날짜(date) 추출 (class="inline-blocked" 중 첫번째는 작성자, 두번째는 날짜)
    author_element = soup.select('.inline-blocked')
    author = author_element[0].text.strip() if len(author_element) > 0 else ''
    date = author_element[1].text.strip() if len(author_element) > 1 else ''

    # 리뷰 내용(content) 추출 (class="txt" 안의 텍스트)
    content_element = soup.select_one('.txt')
    content = content_element.text.strip() if content_element else ''

    # 제품 이름(product) 추출 (class="prod_name" 안 a 태그의 텍스트)
    product_element = soup.select_one('.prod_name a')
    product = product_element.text.strip() if product_element else ''

    # 별점 갯수(count) 추출 (class="bts bt-star active"의 갯수)
    star_count = len(soup.select('.bts.bt-star.active'))

    # 추출한 데이터를 반환
    return {
        'author': author,
        'date': date,
        'content': content,
        'product': product,
        'images': images,
        'star_count': star_count
    }

# 메인 함수에 추가하여 엑셀로 출력하는 부분
def save_to_excel(review_data_list):
    # 리뷰 데이터를 저장할 리스트
    review_list = []

    # 각 리뷰 데이터를 엑셀에 맞게 처리
    for review_data in review_data_list:
        # 엑셀에 넣을 형식으로 변환
        excel_data = {
            '글번호': review_data['no'],
            '작성자': review_data['author'],
            '작성일자': review_data['date'],
            '상품명': review_data['product'],
            '글내용': review_data['content'],
            '평점': review_data['star_count']
        }

        # 이미지 URL들을 별도로 처리
        for i, image_url in enumerate(review_data['images']):
            excel_data[f'이미지URL ({i+1})'] = image_url

        review_list.append(excel_data)

    # DataFrame 생성
    df = pd.DataFrame(review_list)

    # 엑셀 파일로 저장
    df.to_excel('review_data.xlsx', index=False)
    print("Excel file created successfully.")


# 메인 함수
def main():
    all_reviews = []
    collected_reviews = []  # 리뷰 데이터를 저장할 리스트

    # 1부터 27페이지까지 반복
    for page in range(1, 28):
        html = get_review_links(page)
        if html:
            page_reviews = extract_review_data(html)
            all_reviews.extend(page_reviews)

    print(f'총 갯수: {len(all_reviews)}')

    # 각 리뷰에 대해 상세 정보 요청
    for index, review in enumerate(all_reviews, start=1):
        detail_response = get_review_details(review)
        if detail_response:
            review_data = process_response(detail_response)
            review_data['no'] = review['idx']

            print(f'index : {index}')
            print(f'review : {review_data}')

            # 수집한 리뷰 데이터를 리스트에 추가
            collected_reviews.append(review_data)

    # 수집한 데이터를 엑셀로 저장
    save_to_excel(collected_reviews)


if __name__ == "__main__":
    main()
