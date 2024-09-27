import requests
from bs4 import BeautifulSoup
import json
import pandas as pd



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
            all_reviews.append(review)

        # 다음 페이지로 이동
        page += 1

        # pageCount에 도달하면 중단
        if page > data.get("pageCount", 0):
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
            "글내용": review.get("review_content", "")
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

