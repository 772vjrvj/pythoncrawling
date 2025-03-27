import requests
import logging
from requests.exceptions import (
    Timeout, TooManyRedirects, ConnectionError,
    HTTPError, URLRequired, SSLError, RequestException
)

def request_api(
        method: str,
        url: str,
        headers: dict = None,
        params: dict = None,
        data: dict = None,
        json: dict = None,
        timeout: int = 30,
        verify: bool = True
):
    """
    HTTP 요청을 수행하고 상태 코드, 응답 타입을 자동 처리하여 결과만 반환하는 함수

    :return:
        - JSON 응답일 경우: dict
        - HTML 응답일 경우: str (html)
        - 기타 텍스트 응답일 경우: str
        - 실패 시: None
    """
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            data=data,
            json=json,
            timeout=timeout,
            verify=verify
        )

        response.encoding = 'utf-8'
        response.raise_for_status()  # 4xx, 5xx 응답 시 예외 발생

        # 상태 코드 체크
        if response.status_code != 200:
            logging.error(f"Unexpected status code: {response.status_code}")
            return None

        # Content-Type 판별
        content_type = response.headers.get('Content-Type', '')

        if 'application/json' in content_type:
            return response.json()
        elif 'text/html' in content_type or 'application/xhtml+xml' in content_type:
            return response.text
        else:
            return response.text  # 기타 텍스트 형식

    # 예외 처리
    except Timeout:
        logging.error("Request timed out")
    except TooManyRedirects:
        logging.error("Too many redirects")
    except ConnectionError:
        logging.error("Network connection error")
    except HTTPError as e:
        logging.error(f"HTTP error occurred: {e}")
    except URLRequired:
        logging.error("A valid URL is required")
    except SSLError:
        logging.error("SSL certificate verification failed")
    except RequestException as e:
        logging.error(f"Request failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected exception: {e}")

    return None