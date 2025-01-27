import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from urllib.parse import urlparse

# 배송비와 판매가에서 숫자만 추출하고 더하기
def extract_number(text):
    return int(re.sub(r'\D', '', text)) if text else 0

def fetch_product_info(url):
    headers = {
        "authority": "www.coupang.com",
        "method": "GET",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    try:
        # GET 요청을 보냅니다.
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP 에러 상태 코드가 있는 경우 예외 발생

        # HTML 파싱
        soup = BeautifulSoup(response.content, "html.parser")

        # 상품명 추출
        product_name = soup.find(class_="prod-buy-header__title")
        product_name_text = product_name.get_text(strip=True) if product_name else ""

        # 배송비 추출 (배송비가 없을 수 있음)
        delivery_fee = soup.find(class_="delivery-fee-info")
        delivery_fee_text = delivery_fee.get_text(strip=True) if delivery_fee else ""

        # 판매가 추출
        total_price = soup.find(class_="total-price")
        total_price_text = total_price.get_text(strip=True) if total_price else ""

        # 배송비와 판매가에서 숫자만 추출하고 더하기
        delivery_fee_number = extract_number(delivery_fee_text)
        total_price_number = extract_number(total_price_text)

        # 합계 계산
        total = delivery_fee_number + total_price_number
        total_formatted = f"{total:,}원" if total > 0 else ""  # 합계가 0이면 빈 문자열

        # 최근 실행 시간
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 결과 객체
        result = {
            "상품명": product_name_text if product_name_text else "",
            "배송비": delivery_fee_text if delivery_fee_text else "",
            "판매가": total_price_text if total_price_text else "",
            "합계": total_formatted,
            "최근실행시간": current_time
        }

        return result

    except requests.exceptions.RequestException as e:
        # 요청 예외 처리 (예: 네트워크 문제, HTTP 오류 등)
        return {"error": f"요청 오류: {str(e)}"}

    except Exception as e:
        # 기타 예외 처리 (예: HTML 파싱 오류 등)
        return {"error": f"알 수 없는 오류: {str(e)}"}


# 메인 함수
def main(url):
    # URL에서 쿼리 파라미터를 제거하여 새로운 URL 생성
    parsed_url = urlparse(url)
    new_url = parsed_url._replace(query='').geturl()  # 쿼리 파라미터 제거

    # fetch_product_info 함수 호출
    return fetch_product_info(new_url)

if __name__ == "__main__":
    url = "https://www.coupang.com/vp/products/208504201?itemId=618762861&vendorItemId=70763667474&q=%EC%9E%A5%EB%A1%B1&itemsCount=36&searchId=9b8b7ef48bd7490baacc3fe637caa644&rank=7&searchRank=7&isAddedCart="
    result = main(url)
    print(result)
