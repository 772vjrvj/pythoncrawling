import time

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import messagebox
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver



def scrape_page_items(page_number):
    url = f"https://ecoandcompany.com/shop/?&page={page_number}&sort=recent"
    # 헤더 설정 (cookie 제외)
    headers = {
        'authority': 'ecoandcompany.com',
        'method': 'GET',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'referer': 'https://ecoandcompany.com/shop',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to retrieve page {page_number}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    items = []
    shop_items = soup.find_all('div', class_='shop-item _shop_item')

    for item in shop_items:
        a_tag = item.find('a', href=True)
        h2_tag = item.find('h2')

        if a_tag and 'href' in a_tag.attrs:
            href = a_tag['href']
            # Extract id from the href, assuming the format is '/shop/?idx=196'
            idx = href.split('=')[-1]

            # Extract title from the h2 tag
            title = h2_tag.get_text(strip=True) if h2_tag else "No title"

            # Append result to list
            items.append({
                'id': idx,
                'title': title
            })

    return items

def scrape_all_pages():
    page_number = 1
    all_items = []
    previous_items = None  # 직전 페이지의 아이템을 저장할 변수

    while True:
        items = scrape_page_items(page_number)

        if not items or items == previous_items:
            # Stop when no items are found or items are the same as the previous page
            break

        all_items.extend(items)
        print(f"Page {page_number} scraped.")

        # 직전 페이지 아이템을 현재 페이지 아이템으로 업데이트
        previous_items = items

        page_number += 1

    return all_items


def fetch_reviews(result_id, result_title):
    all_reviews = []
    page = 1  # page 1부터 시작

    while True:
        url = f"https://rgapi.seoulventures.net/api/business/894/reviews"
        payload = {
            "business_id": "894",
            "content_id": result_id,
            "limit": 20,
            "page": page,
            "review_type": "all"
        }
        headers = {
            'authority': 'rgapi.seoulventures.net',
            'method': 'POST',
            'scheme': 'https',
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://ecoandcompany.com',
            'priority': 'u=1, i',
            'referer': 'https://ecoandcompany.com/',
            'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        }

        response = requests.post(url, headers=headers, json=payload)

        # 200 또는 201 상태 코드를 성공으로 간주
        if response.status_code not in [200, 201]:
            print(f"Failed to retrieve reviews for ID {result_id}, Page {page}. Status code: {response.status_code}")
            try:
                print(f"Response content: {response.content.decode('utf-8')}")
            except Exception as e:
                print(f"Error reading response: {e}")
            break

        data = response.json()

        # 리뷰가 없으면 중단
        if not data.get("reviews") or data.get("count") == 0 or data.get("pageCount") == 0:
            print(f"No more reviews for ID {result_id} on page {page}. Stopping.")
            break

        # reviews에 id와 title 추가
        for review in data["reviews"]:
            review["id"] = result_id
            review["title"] = result_title
            review["store"] = '스마트스토어'
            all_reviews.append(review)

        # 다음 페이지로 이동
        page += 1

        # pageCount에 도달하면 중단
        if page > data.get("pageCount", 0):
            break

    return all_reviews

def fetch_reviews_2(driver, result_id, result_title):
    # URL 설정
    url = f"https://ecoandcompany.com/shop/?idx={result_id}#prod_detail_review"

    try:
        # 해당 URL로 이동
        driver.get(url)

        time.sleep(3)

        # 'list_review_wrap' 두 번째 요소를 찾음
        reviews_section = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'list_review_wrap'))
        )[1]  # 두 번째 list_review_wrap 선택

    except Exception as e:
        print(f"리뷰 섹션을 찾는 동안 오류가 발생했습니다: {e}")
        return []  # 실패 시 빈 리스트 반환

    # 리뷰 정보를 담을 리스트
    reviews = []

    # li 요소들 추출 후 반복문 시작
    try:
        li_elements = reviews_section.find_elements(By.TAG_NAME, 'li')
    except Exception as e:
        print(f"리뷰 목록을 가져오는 동안 오류가 발생했습니다: {e}")
        return []  # 실패 시 빈 리스트 반환

    for li in li_elements:
        # 리뷰 내용을 담을 딕셔너리
        review_data = {}

        review_data['id'] = result_id
        review_data['title'] = result_title
        review_data['store'] = 'N pay'

        # 리뷰 텍스트 추출
        try:
            review_content_elem = li.find_element(By.CSS_SELECTOR, '.txt._txt._review_body._block_')
            review_content = review_content_elem.text.strip()
            review_data['review_content'] = review_content
        except Exception as e:
            print(f"리뷰 내용을 추출하는 동안 오류가 발생했습니다: {e}")
            review_data['review_content'] = ''  # 기본값 설정

        # 리뷰 날짜 추출
        try:
            review_reg_date_elem = li.find_element(By.CSS_SELECTOR, '.table-cell.vertical-top.width-5.text-13.use_summary div:nth-child(2)')
            review_reg_date = review_reg_date_elem.text.strip()
            review_data['review_reg_date'] = review_reg_date
        except Exception as e:
            print(f"리뷰 날짜를 추출하는 동안 오류가 발생했습니다: {e}")
            review_data['review_reg_date'] = ''  # 기본값 설정

        # 리뷰 이미지 URL 추출
        review_images = []
        try:
            img_wrap_elem = li.find_element(By.CSS_SELECTOR, '.thumb_detail_img_wrap.margin-top-xl.margin-bottom-xxxl._review_img._block_')
            img_elements = img_wrap_elem.find_elements(By.TAG_NAME, 'img')
            for img in img_elements:
                review_images.append(img.get_attribute('src'))
        except Exception as e:
            print(f"리뷰 이미지를 추출하는 동안 오류가 발생했습니다: {e}")

        review_data['review_images'] = review_images

        # 결과 리스트에 추가
        reviews.append(review_data)

    # 리뷰 데이터 출력 (혹은 원하는 데이터 가공 후 반환)
    for review in reviews:
        print(review)

    return reviews

def fetch_reviews_3(result_id, result_title):
    url = f"https://ecoandcompany.com/ajax/shop/get_photo_review_list.cm?prod_idx={result_id}"

    headers = {
        'authority': 'ecoandcompany.com',
        'method': 'GET',
        'path': f'/ajax/shop/get_photo_review_list.cm?prod_idx={result_id}',
        'scheme': 'https',
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'referer': f'https://ecoandcompany.com/shop/?idx={result_id}',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin'
    }

    # GET 요청 보내기
    response = requests.get(url, headers=headers)
    all_reviews = []
    if response.status_code == 200:
        # JSON 디코딩
        data = response.json()

        # photo_review_list를 가져옴
        photo_review_list = data.get('photo_review_list', [])

        # 리뷰 리스트를 순회하면서 출력
        for review in photo_review_list:
            print(f"리뷰 이미지: {review['photo_review_image']}")
            print(f"리뷰 내용: {review['photo_review_contents']}")
            print(f"리뷰 평점: {review['photo_review_rating']}")
            print(f"리뷰 인덱스: {review['photo_review_idx']}")
            print('-' * 40)

        for review in photo_review_list:
            review["id"] = result_id
            review["title"] = result_title
            review["store"] = 'N Pay'
            all_reviews.append(review)

        return all_reviews

    else:
        print(f"요청에 실패했습니다. 상태 코드: {response.status_code}")
        return all_reviews

def fetch_reviews_4(result_id, result_title):

    all_reviews = []
    previous_reviews = []  # 직전 페이지 데이터를 저장할 리스트

    url = "https://ecoandcompany.com/shop/prod_review_pc_html.cm"

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    page = 1  # 시작 페이지
    while True:
        # Payload 설정
        payload = {
            'prod_idx': result_id,
            'review_page': page,
            'qna_page': 1,
            'only_photo': 'N',
            'rating': 0
        }

        # POST 요청
        response = requests.post(url, data=payload, headers=headers)

        if response.status_code == 200:
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')

            # 'list_review_wrap' 클래스를 가진 요소 내의 li들 찾기
            review_list = soup.find(class_='list_review_wrap')

            # 더 이상 리뷰가 없으면 종료
            if not review_list:
                print(f"페이지 {page}: 더 이상 리뷰가 없습니다.")
                break

            li_elements = review_list.find_all('li')

            # 리뷰가 없으면 종료
            if not li_elements:
                print(f"페이지 {page}: 더 이상 리뷰가 없습니다.")
                break

            # 직전 페이지 데이터와 현재 페이지 데이터가 동일하면 루프 종료
            current_reviews = [li.get_text(strip=True) for li in li_elements]
            if current_reviews == previous_reviews:
                print(f"페이지 {page}: 직전 페이지와 동일한 데이터 발견, 루프 종료.")
                break

            # li 요소 순회
            for li in li_elements:
                review_data = {}

                review_data["id"] = result_id
                review_data["title"] = result_title
                review_data["store"] = 'N Pay'

                # 리뷰 내용 추출 (class 이름이 tw-whitespace-pre-line인 요소의 텍스트)
                review_content_elem = li.find(class_='tw-whitespace-pre-line')
                review_content = review_content_elem.get_text(strip=True) if review_content_elem and review_content_elem.get_text(strip=True) else ""

                print(f'test1 : {review_content}')
                # tw-whitespace-pre-line 내부에 텍스트가 없으면 'txt _txt _review_body _block_'에서 텍스트 추출
                if not review_content:
                    review_content_elem_alt = li.find('span', class_='_review_body')

                    # 'dummy' 클래스 내부를 제거한 텍스트만 추출
                    if review_content_elem_alt:
                        # `div` 태그의 내용을 제외한 나머지 텍스트 추출
                        for dummy_div in review_content_elem_alt.find_all('div', class_='dummy _dummy'):
                            dummy_div.decompose()  # 'dummy' div 제거

                        review_content = review_content_elem_alt.get_text(strip=True)  # 남은 텍스트 추출
                        print(f'test2 : {review_content}')

                review_data['review_content'] = review_content

                # 리뷰 등록 날짜 추출 (class 이름이 use_summary인 요소의 두 번째 div의 텍스트)
                review_reg_date_elem = li.find(class_='use_summary')
                if review_reg_date_elem:
                    review_reg_date = review_reg_date_elem.find_all('div')[1].get_text(strip=True)
                else:
                    review_reg_date = ""
                review_data['review_reg_date'] = review_reg_date

                # 리뷰 이미지 URL 추출 (thumb_detail_img_wrap 내부 img 태그들의 src)
                images = []
                img_wrap_elem = li.find(class_='thumb_detail_img_wrap')
                if img_wrap_elem:
                    img_elements = img_wrap_elem.find_all('img')
                    for img in img_elements:
                        images.append(img.get('src'))
                review_data['review_images'] = images

                # 리뷰 데이터 출력
                print(review_data)

                all_reviews.append(review_data)

            # 직전 페이지 리뷰를 저장
            previous_reviews = current_reviews

            # 다음 페이지로 이동
            page += 1
        else:
            print(f"페이지 {page}에서 데이터를 가져오는 데 실패했습니다. 상태 코드: {response.status_code}")
            break

    return all_reviews


def main():
    results = scrape_all_pages()
    all_reviews_combined = []  # 모든 리뷰 데이터를 합칠 리스트

    for result in results:
        print(f"ID: {result['id']}, Title: {result['title']}")
        review_data = fetch_reviews(result['id'], result['title'])

        if review_data:
            all_reviews_combined.extend(review_data)  # 리뷰 데이터를 합침

        review_data_4 = fetch_reviews_4(result['id'], result['title'])

        if review_data_4:
            all_reviews_combined.extend(review_data_4)  # 리뷰 데이터를 합침



    # Excel에 넣을 데이터를 준비
    data_for_excel = []
    max_images = 0  # 최대 이미지 수를 추적

    for review in all_reviews_combined:
        # 리뷰 이미지 추출
        review_images = review.get("review_images", [])
        max_images = max(max_images, len(review_images))  # 최대 이미지 개수 추적

        # 기본 리뷰 데이터 구성
        review_data = {
            "글번호": review.get("id", ""),
            "작성일자": review.get("review_reg_date", ""),
            "상품명": review.get("title", ""),
            "글내용": review.get("review_content", ""),
            "스토어": review.get("store", "")
        }

        # 이미지 URL 동적으로 추가
        for i, img_url in enumerate(review_images):
            review_data[f"이미지URL ({i + 1})"] = img_url

        data_for_excel.append(review_data)

    # DataFrame 생성
    df = pd.DataFrame(data_for_excel)

    # 누락된 이미지 컬럼을 처리 (동적 이미지 수에 맞게 컬럼을 추가)
    for i in range(1, max_images + 1):
        if f"이미지URL ({i})" not in df.columns:
            df[f"이미지URL ({i})"] = None

    # 엑셀 파일로 저장
    output_file_path = "reviews_data_dynamic.xlsx"
    df.to_excel(output_file_path, index=False)

    print(f"Excel file has been saved to {output_file_path}")

if __name__ == "__main__":
    main()

