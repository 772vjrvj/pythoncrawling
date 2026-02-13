import logging
import requests
import requests_cache
from bs4 import UnicodeDammit
from requests.adapters import HTTPAdapter
from requests.exceptions import (
    Timeout, TooManyRedirects, ConnectionError, HTTPError,
    URLRequired, RequestException
)
from urllib3.util.retry import Retry


class APIClient:
    def __init__(self, timeout=30, verify=True, retries=3, backoff=0.3, use_cache=False, log_func=None, encoding=None):
        """
        encoding: 기본 강제 인코딩 (예: "euc-kr"). None이면 자동 추론 사용
        """
        self.timeout = timeout
        self.verify = verify
        self.session = requests.Session()
        self.log_func = log_func
        self.default_encoding = encoding  # None → 자동 추론

        if use_cache:
            self._enable_cache()

        self._mount_retry_adapter(retries, backoff)

    def _enable_cache(self):
        # GET 요청만 캐시, 5분 TTL, Cache-Control 존중, 에러 시 stale 허용
        try:
            requests_cache.install_cache(
                'api_cache',
                expire_after=300,                 # 5분
                allowable_methods=('GET',),       # ✅ GET만 캐시
                cache_control=True,               # 서버 Cache-Control 헤더 존중
                stale_if_error=True               # 원 서버 에러 시 캐시된 응답 사용
            )
            if self.log_func:
                self.log_func("✅ cache ON: GET-only / TTL=5m / stale-if-error")
        except Exception as e:
            if self.log_func:
                self.log_func(f"⚠️ cache 설정 실패: {e}")

    def _mount_retry_adapter(self, retries, backoff):
        # 멱등 메서드만 재시도 + 지수 백오프 + Retry-After 존중
        retry = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=backoff,                       # 0.3 → 0.6 → 1.2 …
            status_forcelist=[408, 429, 500, 502, 503, 504],  # 408/429 포함
            allowed_methods=["HEAD", "GET", "OPTIONS"],   # ✅ 멱등 메서드만
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        # 커넥션 풀 확장(대량 크롤링 안정성/성능)
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=100,   # 호스트 풀 캐시 개수
            pool_maxsize=100        # 호스트별 동시 커넥션 한도
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    # ---------- 퍼블릭 메서드 ----------
    def get(self, url, headers=None, params=None, encoding=None, return_bytes=False):
        return self._request("GET", url, headers=headers, params=params, encoding=encoding, return_bytes=return_bytes)

    def post(self, url, headers=None, data=None, json=None, encoding=None, return_bytes=False):
        return self._request("POST", url, headers=headers, data=data, json=json, encoding=encoding, return_bytes=return_bytes)

    def patch(self, url, headers=None, data=None, json=None, encoding=None, return_bytes=False):
        return self._request("PATCH", url, headers=headers, data=data, json=json, encoding=encoding, return_bytes=return_bytes)

    def delete(self, url, headers=None, params=None, encoding=None, return_bytes=False):
        return self._request("DELETE", url, headers=headers, params=params, encoding=encoding, return_bytes=return_bytes)

    def cookie_set(self, name, value):
        if name and value:
            self.session.cookies.set(name, value)

    def cookie_set_dict(self, c):
        # c: selenium driver.get_cookies()의 원소(dict)
        if not c:
            return
        name = c.get("name")
        value = c.get("value")
        if not name or value is None:
            return

        domain = c.get("domain") or ".band.us"
        path = c.get("path") or "/"

        # domain 앞에 점(.) 없으면 서브도메인 공유가 안 될 수 있어서 보정
        if domain and not domain.startswith(".") and domain.endswith("band.us"):
            domain = "." + domain

        self.session.cookies.set(name, value, domain=domain, path=path)


    def cookie_get(self, name=None, domain=None, path=None, as_dict=False):
        """
        세션 쿠키 필터링 반환.
        - name/domain/path 조건 매칭
        - as_dict=True: dict 리스트로 반환
        """
        jar = self.session.cookies
        matched = []
        for c in jar:
            if name is not None and c.name != name:
                continue
            if domain is not None and (c.domain or "").lstrip(".") != domain.lstrip("."):
                continue
            if path is not None and (c.path or "/") != path:
                continue
            matched.append(c)

        if as_dict:
            return [
                {
                    "name": c.name,
                    "value": c.value,
                    "domain": c.domain,
                    "path": c.path,
                    "secure": c.secure,
                    "expires": c.expires,
                    "rest": getattr(c, "rest", {}),
                }
                for c in matched
            ]
        return matched

    # ---------- 인코딩 디코더 ----------
    def _to_text(self, res, force_encoding):
        """
        텍스트 payload를 바이트 기준으로 안전하게 디코딩.
        - force_encoding 지정 시 강제 디코딩 (euc-kr/cp949/utf-8 등)
        - None이면 UnicodeDammit로 자동 추론
        """
        raw = res.content  # 항상 bytes
        if force_encoding:
            try:
                return raw.decode(force_encoding, errors="replace")
            except Exception as e:
                if self.log_func:
                    self.log_func(f"⚠️ 강제 인코딩 실패({force_encoding}): {e} → 자동 추론으로 전환")

        dammit = UnicodeDammit(raw, is_html=True)
        text = dammit.unicode_markup
        if not text:
            # 최후 수단
            try:
                return raw.decode(res.apparent_encoding or "utf-8", errors="replace")
            except Exception:
                return raw.decode("utf-8", errors="replace")
        return text

    # ---------- 핵심 요청 ----------
    def _request(self, method, url, headers=None, params=None, data=None, json=None, encoding=None, return_bytes=False):
        try:
            res = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                timeout=self.timeout,
                verify=self.verify,
            )
            res.raise_for_status()

            logging.debug(f"✅ {method} {url} | {res.status_code} | {len(res.content)} bytes")
            if return_bytes:
                return res.content  # 원시 바이트 그대로

            ctype = (res.headers.get("Content-Type") or "").lower()

            # JSON 우선
            if "application/json" in ctype or "application/ld+json" in ctype:
                return res.json()

            # HTML/XML/Text 류 안전 디코딩
            if (
                    "text/html" in ctype
                    or "application/xhtml+xml" in ctype
                    or "application/xml" in ctype
                    or "text/xml" in ctype
                    or "text/plain" in ctype
            ):
                force = encoding if encoding is not None else self.default_encoding
                return self._to_text(res, force_encoding=force)

            # 기타: JSON 시도 → 실패 시 텍스트 디코딩
            try:
                return res.json()
            except ValueError:
                force = encoding if encoding is not None else self.default_encoding
                return self._to_text(res, force_encoding=force)

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
