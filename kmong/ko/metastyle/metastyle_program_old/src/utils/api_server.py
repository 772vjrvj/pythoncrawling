from src.utils.singleton import GlobalState
import requests
import logging
import time
from typing import Any
from requests.exceptions import (
    Timeout, TooManyRedirects, ConnectionError,
    HTTPError, URLRequired, SSLError, RequestException
)

class ApiServer:

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

    def __init__(self, log_func):
        if not callable(log_func):
            raise ValueError("log_func must be callable.")
        self.log = log_func
        state = GlobalState()
        self.cookies = state.get("cookies")
        self.base_url = "https://vjrvj.cafe24.com/product-info"

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
            merged_headers = {**self.DEFAULT_HEADERS, **(headers or {})}
            self.log(f"[API 요청] {method.upper()} {url}")
            if params:
                self.log(f" - 쿼리 파라미터: {params}")
            if json:
                self.log(f" - JSON 바디: {json}")

            response = requests.request(
                method=method.upper(),
                url=url,
                headers=merged_headers,
                params=params,
                data=data,
                json=json,
                timeout=timeout,
                verify=verify,
                cookies=self.cookies
            )

            duration = round(time.time() - start_time, 2)
            self.log(f"[응답 수신 완료] 상태코드: {response.status_code}, 소요시간: {duration}s")

            response.encoding = 'utf-8'
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')

            if 'application/json' in content_type:
                try:
                    return response.json()
                except ValueError:
                    self.log("⚠️ JSON 파싱 실패")
                    return None
            else:
                return response.text

        except Timeout:
            self.log("⏱️ 요청 타임아웃 발생")
        except TooManyRedirects:
            self.log("🔁 리다이렉트 횟수 초과")
        except SSLError:
            self.log("🔒 SSL 인증 오류")
        except ConnectionError:
            self.log("📡 네트워크 연결 오류")
        except HTTPError as e:
            self.log(f"❌ HTTP 오류: {e}")
        except URLRequired:
            self.log("📎 URL이 필요합니다.")
        except RequestException as e:
            self.log(f"🚫 요청 실패: {e}")
        except Exception as e:
            self.log(f"❗예기치 못한 예외: {e}")

        return None

    # ---------------------------------
    # ProductInfo 관련 CRUD API 호출
    # ---------------------------------

    def get_all_products(self):
        url = f"{self.base_url}/select-all"
        return self.request_api("GET", url)

    def get_product_by_key(self, product_key: str):
        url = f"{self.base_url}/{product_key}"
        return self.request_api("GET", url)

    def add_products(self, product_list: list[dict]):
        url = f"{self.base_url}/add"
        return self.request_api("POST", url, json=product_list)

    def update_products(self, product_list: list[dict]):
        url = f"{self.base_url}/update"
        return self.request_api("PUT", url, json=product_list)

    def delete_product(self, product_key: str):
        url = f"{self.base_url}/{product_key}"
        return self.request_api("DELETE", url)

    def get_products_after_reg_date(self, reg_date: str):
        """
        특정 regDate(yyyy.MM.dd) 이후의 상품 목록 조회
        """
        url = f"{self.base_url}/select-after"
        params = {"regDate": reg_date}
        return self.request_api("GET", url, params=params)