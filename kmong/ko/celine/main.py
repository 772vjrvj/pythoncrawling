import requests
from bs4 import BeautifulSoup

# 원하는 데이터를 가져오는 함수
def get_price_content(url):
    # URL 요청
    response = requests.get(url)

    # HTTP 요청 성공 여부 확인
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # 클래스 "o-product__product" 안에서 "prices" 클래스 찾기
        product_section = soup.find(class_="o-product__product")
        if product_section:
            prices_section = product_section.find(class_="prices")
            if prices_section:
                # 가격 정보를 담고 있는 strong 태그를 찾아 data-description이 'value'인 것의 content 속성 값 가져오기
                price_tag = prices_section.find("strong", {"data-description": "value"})
                if price_tag and price_tag.has_attr('content'):
                    print(price_tag['content'])  # content 속성 값 출력
                else:
                    print("가격 정보를 찾을 수 없습니다.")
            else:
                print('가격 섹션을 찾을 수 없습니다.')
        else:
            print('제품 섹션을 찾을 수 없습니다.')
    else:
        print("웹 페이지를 불러오는 데 실패했습니다.")

# main 함수
def main():
    url = "https://www.celine.com/fr-fr/celine-boutique-femme/pret-a-porter/vestes/veste-capuche-laine-fourrure-triomphe-2Y78G602T.18NK.html"
    get_price_content(url)

if __name__ == "__main__":
    main()
