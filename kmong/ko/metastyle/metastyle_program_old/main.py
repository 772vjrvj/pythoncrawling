from src.utils.singleton import GlobalState
import requests
import logging
import time
from typing import Any
from requests.exceptions import (
    Timeout, TooManyRedirects, ConnectionError,
    HTTPError, URLRequired, SSLError, RequestException
)

DEFAULT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate",
    "accept-language": "ko,en;q=0.9,en-US;q=0.8",
    "connection": "keep-alive",
    "host": "vjrvj.cafe24.com",
    "sec-gpc": "1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
}

base_url = "https://vjrvj.cafe24.com/product-info"
base_url = "http://localhost:80/product-info"

def request_api(self,
                method: str,
                url: str,
                headers: dict = None,
                params: dict = None,
                data: dict = None,
                json: Any = None,
                timeout: int = 30,
                verify: bool = True
                ):
    start_time = time.time()
    try:
        merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
        print(f"[API 요청] {method.upper()} {url}")
        if params:
            print(f" - 쿼리 파라미터: {params}")
        if json:
            print(f" - JSON 바디: {json}")

        response = requests.request(
            method=method.upper(),
            url=url,
            headers=merged_headers,
            params=params,
            data=data,
            json=json,
            timeout=timeout,
            verify=verify,
        )

        duration = round(time.time() - start_time, 2)
        print(f"[응답 수신 완료] 상태코드: {response.status_code}, 소요시간: {duration}s")

        response.encoding = 'utf-8'
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')

        if 'application/json' in content_type:
            try:
                return response.json()
            except ValueError:
                print("⚠️ JSON 파싱 실패")
                return None
        else:
            return response.text

    except Timeout:
        print("⏱️ 요청 타임아웃 발생")
    except TooManyRedirects:
        print("🔁 리다이렉트 횟수 초과")
    except SSLError:
        print("🔒 SSL 인증 오류")
    except ConnectionError:
        print("📡 네트워크 연결 오류")
    except HTTPError as e:
        print(f"❌ HTTP 오류: {e}")
    except URLRequired:
        print("📎 URL이 필요합니다.")
    except RequestException as e:
        print(f"🚫 요청 실패: {e}")
    except Exception as e:
        print(f"❗예기치 못한 예외: {e}")

    return None

# ---------------------------------
# ProductInfo 관련 CRUD API 호출
# ---------------------------------

def get_all_products():
    url = f"{base_url}/select-all"
    return request_api("GET", url)

def get_product_by_key(product_key: str):
    url = f"{base_url}/{product_key}"
    return request_api("GET", url)

def add_products(product_list: list[dict]):
    url = f"{base_url}/add"
    return request_api("POST", url, json=product_list)

def update_products(product_list: list[dict]):
    url = f"{base_url}/update"
    return request_api("PUT", url, json=product_list)

def delete_product(product_key: str):
    url = f"{base_url}/{product_key}"
    return request_api("DELETE", url)


if __name__ == "__main__":
    product_list = [
        {
            "website": "&OTHER STORIES",
            "brandType": "Competitive Brand",
            "category": "WOMEN",
            "categorySub": "All New Arrivals",
            "url": "https://www.stories.com/en_usd",
            "categoryFull": "WOMEN _ All New Arrivals",
            "country": "US",
            "brand": "&OTHER STORIES",
            "productUrl": "https://www.stories.com/en_usd/clothing/dresses/maxi-dresses/product.satin-slip-midi-dress-black.1267042002.html",
            "product": "Satin Slip Midi Dress",
            "productId": 1267042002,
            "productNo": 1,
            "description": "Midi slip dress crafted in a glossy satin finish. Designed with thin spaghetti straps, a delicate cowl neck, and a fitted waist that falls into a gentle flare. Finished with a scooped back secured with a self-tie closure.",
            "price": "$109",
            "imageNo": 1,
            "imageUrl": "https://lp.stories.com/app005prod?...ef9424a3e85e0ec358014d211b16cf446fb513ce.jpg...",
            "imageName": "1267042002_1.jpg",
            "success": "Y",
            "regDate": "2025.03.31",
            "page": "05:09:53",
            "error": "",
            "imageYn": "Y",
            "imagePath": "ai-designer-ml-external/&OTHER STORIES/WOMEN _ All New Arrivals/1267042002_1.jpg",
            "projectId": "styleai-373423",
            "bucket": "ai-designer-ml-external",
            "imageUrlModified": "",
            "productKey": "&OTHER STORIES_1267042002"
        },
        {
            "website": "&OTHER STORIES",
            "brandType": "Competitive Brand",
            "category": "WOMEN",
            "categorySub": "All New Arrivals",
            "url": "https://www.stories.com/en_usd",
            "categoryFull": "WOMEN _ All New Arrivals",
            "country": "US",
            "brand": "&OTHER STORIES",
            "productUrl": "https://www.stories.com/en_usd/clothing/skirts/mini-skirts/product.bubble-mini-skirt-black.1264190001.html",
            "product": "Bubble Mini Skirt",
            "productId": 1264190001,
            "productNo": 2,
            "description": "Mini skirt designed in a puffed bubble shape. Crafted from a lightweight poplin fabric. Featuring invisible side seam pockets and an elastic waist for an easy slip-on effect.",
            "price": "$89",
            "imageNo": 1,
            "imageUrl": "https://lp.stories.com/app005prod?...60f25c2cb3309d089389368deb10e9655e6f5f64.jpg...",
            "imageName": "1264190001_1.jpg",
            "success": "Y",
            "regDate": "2025.03.31",
            "page": "05:09:58",
            "error": "",
            "imageYn": "Y",
            "imagePath": "ai-designer-ml-external/&OTHER STORIES/WOMEN _ All New Arrivals/1264190001_1.jpg",
            "projectId": "styleai-373423",
            "bucket": "ai-designer-ml-external",
            "imageUrlModified": "",
            "productKey": "&OTHER STORIES_1264190001"
        }
    ]
    add_products(product_list)


