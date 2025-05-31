from src.vo.singleton import GlobalState
import requests
import time
from typing import Any
from requests.exceptions import (
    Timeout, TooManyRedirects, ConnectionError,
    HTTPError, URLRequired, SSLError, RequestException
)

class ApiServer:

    def __init__(self, log_func):
        if not callable(log_func):
            raise ValueError("log_func must be callable.")
        self.log = log_func
        state = GlobalState()
        self.cookies = state.get("cookies")
        self.base_url = "http://vjrvj.cafe24.com/product-info"
        self.session = requests.Session()

        # 쿠키가 있으면 세션에 적용
        if self.cookies:
            for k, v in self.cookies.items():
                self.session.cookies.set(k, v)

        self.DEFAULT_HEADERS = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

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
            full_url = url if url.startswith("http") else f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"

            self.log(f"[API 요청] {method.upper()} {full_url}")
            if params:
                self.log(f" - 쿼리 파라미터: {params}")
            if json:
                self.log(f" - JSON 바디: {json}")

            response = self.session.request(
                method=method.upper(),
                url=full_url,
                headers=merged_headers,
                params=params,
                data=data,
                json=json,
                timeout=timeout,
                verify=verify
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
                    self.log(f"{response.text}")
                    return None
            else:
                return None

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
        return self.request_api("GET", "select-all")

    def get_product_by_key(self, product_key: str):
        return self.request_api("GET", product_key)

    def add_products(self, product_list: list[dict]):
        return self.request_api("POST", "add", json=product_list)

    def update_products(self, product_list: list[dict]):
        return self.request_api("PUT", "update", json=product_list)

    def delete_product(self, product_key: str):
        return self.request_api("DELETE", product_key)

    def get_products_after_reg_date(self, reg_date: str):
        """
        특정 regDate(yyyy.MM.dd) 이후의 상품 목록 조회
        """
        params = {"regDate": reg_date}
        return self.request_api("GET", "select-after", params=params)