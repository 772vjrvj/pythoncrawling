import requests
import math

def fetch_kakao_products(kwd, page):
    url = f"https://store.kakao.com/a/search/products?q={kwd}&sort=POPULAR&page={page}&size=100"

    print(f"page : {page}")
    print(f"url : {url}")

    headers = {
        'X-Shopping-Referrer': 'https://store.kakao.com/?__ld__=&oldRef=https:%2F%2Fwww.google.com%2F',
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return None


def calculate_total_pages(total_count):
    return math.ceil(total_count / 100)

def extract_product_ids(data):
    ids = []
    contents = data.get('data', {}).get('contents', [])
    for item in contents:
        product_id = item.get('productId')
        if product_id is not None:
            ids.append(product_id)
    return ids

# 예제 실행
if __name__ == "__main__":
    kwd = "냉면"  # 검색 키워드
    initail_page = 1  # 페이지 번호

    products_data = fetch_kakao_products(kwd, initail_page)

    if products_data:
        # 데이터를 적절히 처리
        print(f"products_data {products_data}")

        totalCount = int(products_data.get('data', {}).get('totalCount', []))

        total_pages = calculate_total_pages(totalCount)

        print(f'total_pages : {total_pages}')

        total_pages = 1
        ids = set()

        # 모든 페이지에 대해 for 문을 돌면서 id 값을 수집합니다.
        for page in range(1, total_pages + 1):
            result_values = fetch_kakao_products(kwd, page)
            extract_product_ids = extract_product_ids(result_values)

            ids.update(extract_product_ids)  # set을 사용하여 중복을 자동으로 제거합니다.

        # 상세페이지에 email이 없어서 일단 보류


