import requests
import logging
import warnings
from requests.exceptions import RequestException, Timeout, TooManyRedirects
from urllib3.exceptions import InsecureRequestWarning


def reviews_request(page, timeout=30):

    # HTTP 요청 헤더 설정
    headers = {

    }

    # 요청할 URL 설정
    url = "https://smartstore.naver.com/i/v1/contents/reviews/query-pages"

    # 요청할 페이로드 설정
    payload = {
        "checkoutMerchantNo": 511111508,  # 상점 번호
        "originProductNo": 5590313137,  # 제품 번호
        "page": page,  # 요청할 페이지 번호
        "pageSize": 20,  # 한 페이지에 담을 리뷰 수
        "reviewSearchSortType": "REVIEW_RANKING"  # 리뷰 정렬 기준 (랭킹 순)
    }
    proxies = {
        "http": "http://27.77.79.174:8080",  # HTTP 프록시
        "https": "https://27.77.79.174:8080"  # HTTPS 프록시
    }

    try:

        # POST 요청을 보내고 응답 받기
        # response = requests.post(url, headers=headers, json=payload, timeout=timeout, proxies=proxies)
        response = requests.post(url, headers=headers, data=payload, verify=True, timeout=timeout)

        # 응답의 인코딩을 UTF-8로 설정
        response.encoding = 'utf-8'

        # HTTP 상태 코드가 200이 아닌 경우 예외 처리
        response.raise_for_status()

        # 상태 코드가 200인 경우 응답 JSON 반환
        if response.status_code == 200:
            return response.json()  # JSON 형식으로 응답 반환
        else:
            # 상태 코드가 200이 아닌 경우 로그 기록
            logging.error(f"Unexpected status code: {response.status_code}")
            return None

    # 타임아웃 오류 처리
    except Timeout:
        logging.error("Request timed out")
        return None

    # 너무 많은 리다이렉트 발생 시 처리
    except TooManyRedirects:
        logging.error("Too many redirects")
        return None

    # 네트워크 연결 오류 처리
    except ConnectionError:
        logging.error("Network connection error")
        return None

    # HTTP 응답 코드가 4xx 또는 5xx일 경우 처리
    except HTTPError as e:
        logging.error(f"HTTP error occurred: {e}")
        return None

    # URL이 유효하지 않거나 제공되지 않았을 경우 처리
    except URLRequired:
        logging.error("A valid URL is required")
        return None

    # SSL 인증서 오류 처리
    except SSLError:
        logging.error("SSL certificate verification failed")
        return None

    # 기타 모든 예외 처리
    except RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

    # 예상치 못한 예외 처리
    except Exception as e:
        logging.error(f"Unexpected exception: {e}")
        return None
