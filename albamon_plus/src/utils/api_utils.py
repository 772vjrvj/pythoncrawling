# api_utils.py

import logging
from typing import Optional, Union
import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import (
    Timeout, TooManyRedirects, ConnectionError, HTTPError,
    URLRequired, RequestException
)


class APIClient:
    def __init__(
            self,
            timeout: int = 30,             # 요청 타임아웃 기본 30초
            verify: bool = True,           # SSL 인증서 검증 여부
            retries: int = 3,              # 실패 시 재시도 횟수
            backoff: float = 0.3,          # 재시도 간 딜레이 계수
            use_cache: bool = False        # 캐시 사용 여부 (기본 꺼짐)
    ):
        self.timeout = timeout
        self.verify = verify
        self.session = requests.Session()  # 하나의 Session 객체로 연결 재사용

        if use_cache:
            self._enable_cache()  # 캐시 기능 활성화 (설치된 경우만)

        self._mount_retry_adapter(retries, backoff)  # Retry 기능 적용

    def _enable_cache(self):
        """
        캐시를 활성화하는 함수. requests_cache가 설치된 경우만 동작.
        """
        try:
            import requests_cache
            requests_cache.install_cache('api_cache', expire_after=300)  # 5분 유효
            logging.info("✅ requests_cache 활성화됨 (5분)")
        except ImportError:
            logging.warning("⚠️ requests_cache 미설치 → 캐시 비활성화됨.")

    def _mount_retry_adapter(self, retries: int, backoff: float):
        """
        Retry 전략을 Session에 적용.
        HTTP 상태코드가 429, 5xx일 때 자동 재시도.
        """
        retry = Retry(
            total=retries,
            backoff_factor=backoff,  # 0.3이면 재시도 간격은 0.3, 0.6, 1.2초 등으로 증가
            status_forcelist=[429, 500, 502, 503, 504],  # 재시도 대상 상태코드
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PATCH", "DELETE"]  # 적용 메서드
        )
        adapter = HTTPAdapter(max_retries=retry)

        # 모든 HTTP/HTTPS 요청에 대해 이 adapter를 적용
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get(self, url: str, headers: dict = None, params: dict = None) -> Optional[Union[dict, str]]:
        """GET 요청 전용 메서드"""
        return self._request("GET", url, headers=headers, params=params)

    def post(self, url: str, headers: dict = None, data: dict = None, json: dict = None) -> Optional[Union[dict, str]]:
        """POST 요청 전용 메서드"""
        return self._request("POST", url, headers=headers, data=data, json=json)

    def patch(self, url: str, headers: dict = None, data: dict = None, json: dict = None) -> Optional[Union[dict, str]]:
        """PATCH 요청 전용 메서드"""
        return self._request("PATCH", url, headers=headers, data=data, json=json)

    def delete(self, url: str, headers: dict = None, params: dict = None) -> Optional[Union[dict, str]]:
        """DELETE 요청 전용 메서드"""
        return self._request("DELETE", url, headers=headers, params=params)

    def cookie_set(self, name, value):
        if name and value:
            self.session.cookies.set(name,value)

    def _request(
            self,
            method: str,
            url: str,
            headers: dict = None,
            params: dict = None,
            data: dict = None,
            json: dict = None
    ) -> Optional[Union[dict, str]]:
        """
        실제 요청을 처리하는 내부 공통 함수.
        응답 타입에 따라 JSON, HTML, 일반 텍스트 자동 처리.
        """
        try:
            # HTTP 요청 수행
            response: Response = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                timeout=self.timeout,
                verify=self.verify
            )

            response.encoding = 'utf-8'  # 인코딩 설정
            response.raise_for_status()  # HTTP 4xx, 5xx 에러 시 예외 발생

            # 요청 성공 로깅 (선택)
            logging.debug(f"✅ {method} {url} | {response.status_code} | {len(response.content)} bytes")

            # 응답 Content-Type에 따라 자동 처리
            content_type = response.headers.get("Content-Type", "")

            if 'application/json' in content_type:
                return response.json()
            elif 'text/html' in content_type or 'application/xhtml+xml' in content_type:
                return response.text
            else:
                # content-type이 애매하면 json 먼저 시도 후 실패하면 텍스트로 반환
                try:
                    return response.json()
                except ValueError:
                    return response.text

        # 아래는 모든 주요 예외 처리 로직
        except Timeout:
            logging.error("⏰ 요청 시간이 초과되었습니다.")
        except TooManyRedirects:
            logging.error("🔁 리다이렉션이 너무 많습니다.")
        except ConnectionError:
            logging.error("🌐 네트워크 연결 오류입니다.")
        except HTTPError as e:
            logging.error(f"📛 HTTP 오류 발생: {e}")
        except URLRequired:
            logging.error("❗ 유효한 URL이 필요합니다.")
        except RequestException as e:
            logging.error(f"🚨 요청 실패: {e}")
        except Exception as e:
            logging.error(f"❗ 예기치 못한 오류: {e}")

        return None  # 실패 시 None 반환
