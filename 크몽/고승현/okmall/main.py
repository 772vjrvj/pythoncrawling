import requests
from bs4 import BeautifulSoup

def fetch_product_name(url):
    """
    주어진 URL에서 상품 이름을 가져옵니다.

    Args:
        url (str): 상품 페이지 URL

    Returns:
        str: 상품 이름 텍스트 (성공 시), 없으면 None
    """
    # 요청에 필요한 헤더 설정 (쿠키 제외)
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

    # GET 요청 보내기
    response = requests.get(url, headers=headers)

    # 요청 성공 여부 확인
    if response.status_code != 200:
        print(f"페이지를 불러오는 데 실패했습니다. 상태 코드: {response.status_code}")
        return None

    # BeautifulSoup을 사용해 HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")

    # id가 'ProductNameArea'인 요소에서 class가 'prd_name'인 텍스트 가져오기
    product_name_element = soup.find(id="ProductNameArea")
    if product_name_element:
        product_name = product_name_element.find(class_="prd_name")
        if product_name:
            return product_name.get_text(strip=True)

    # 상품 이름을 찾지 못한 경우
    print("상품 이름을 찾을 수 없습니다.")
    return None

def main():
    url = "https://www.okmall.com/products/view?no=766569&item_type=&cate=20008666&uni=M"
    product_name = fetch_product_name(url)
    if product_name:
        print(f"상품 이름: {product_name}")

if __name__ == "__main__":
    main()
