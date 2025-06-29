import logging
import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests_cache
from requests.exceptions import (
    Timeout, TooManyRedirects, ConnectionError, HTTPError,
    URLRequired, RequestException
)


class APIClient:
    def __init__(self, timeout=30, verify=True, retries=3, backoff=0.3, use_cache=False, log_func=None):
        self.timeout = timeout
        self.verify = verify
        self.session = requests.Session()

        if use_cache:
            self._enable_cache()

        self._mount_retry_adapter(retries, backoff)
        self.log_func = log_func

    def _enable_cache(self):
        try:
            requests_cache.install_cache('api_cache', expire_after=300)
            self.log_func("✅ requests_cache 활성화됨 (5분)")
        except ImportError:
            self.log_func("⚠️ requests_cache 미설치 → 캐시 비활성화됨.")

    def _mount_retry_adapter(self, retries, backoff):
        retry = Retry(
            total=retries,
            backoff_factor=backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PATCH", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get(self, url, headers=None, params=None):
        return self._request("GET", url, headers=headers, params=params)

    def post(self, url, headers=None, data=None, json=None):
        return self._request("POST", url, headers=headers, data=data, json=json)

    def patch(self, url, headers=None, data=None, json=None):
        return self._request("PATCH", url, headers=headers, data=data, json=json)

    def delete(self, url, headers=None, params=None):
        return self._request("DELETE", url, headers=headers, params=params)

    def cookie_set(self, name, value):
        if name and value:
            self.session.cookies.set(name, value)

    def _request(self, method, url, headers=None, params=None, data=None, json=None):
        try:
            res = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                timeout=self.timeout,
                verify=self.verify
            )

            res.encoding = 'utf-8'
            res.raise_for_status()
            logging.debug(f"✅ {method} {url} | {res.status_code} | {len(res.content)} bytes")

            ctype = res.headers.get("Content-Type", "")

            if 'application/json' in ctype:
                return res.json()
            elif 'text/html' in ctype or 'application/xhtml+xml' in ctype:
                return res.text
            else:
                try:
                    return res.json()
                except ValueError:
                    return res.text

        except Timeout:
            self.log_func("⏰ 요청 시간이 초과되었습니다.")
        except TooManyRedirects:
            self.log_func("🔁 리다이렉션이 너무 많습니다.")
        except ConnectionError:
            self.log_func("🌐 네트워크 연결 오류입니다.")
        except HTTPError as e:
            self.log_func(f"📛 HTTP 오류 발생: {e}")
        except URLRequired:
            self.log_func("❗ 유효한 URL이 필요합니다.")
        except RequestException as e:
            self.log_func(f"🚨 요청 실패: {e}")
        except Exception as e:
            self.log_func(f"❗ 예기치 못한 오류: {e}")

        return None
