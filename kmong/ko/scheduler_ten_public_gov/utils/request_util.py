import requests
import logging
import warnings
from requests.exceptions import RequestException, Timeout, TooManyRedirects
from urllib3.exceptions import InsecureRequestWarning

# InsecureRequestWarning 경고 무시 설정
warnings.simplefilter('ignore', InsecureRequestWarning)

def common_request(url, payload=None, timeout=30):

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }

    """
    공통적인 GET 요청을 처리하는 함수.
    :param url: 요청할 URL
    :param headers: 요청 헤더
    :param payload: GET 요청 시 사용할 파라미터
    :param timeout: 요청 타임아웃 설정 (초)
    :return: 요청 응답 텍스트 또는 None
    """
    try:
        # GET 요청
        if payload:
            response = requests.get(url, headers=headers, verify=False, params=payload, timeout=timeout)
        else:
            response = requests.get(url, headers=headers, verify=False, timeout=timeout)

        # 응답 인코딩을 UTF-8로 강제 설정
        response.encoding = 'utf-8'

        # 상태 코드 200이 아닌 경우 처리
        response.raise_for_status()

        if response.status_code == 200:
            return response.text
        else:
            logging.error(f"Unexpected status code: {response.status_code}")
            return None

    except Timeout:
        logging.error("Request timed out")
        return None
    except TooManyRedirects:
        logging.error("Too many redirects")
        return None
    except RequestException as e:
        logging.error(f"Request failed: {e}")
        return None
