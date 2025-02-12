import requests
import warnings
from requests.exceptions import RequestException, Timeout, TooManyRedirects
from urllib3.exceptions import InsecureRequestWarning
from requests.exceptions import Timeout, TooManyRedirects, RequestException, ConnectionError, HTTPError, URLRequired, MissingSchema, InvalidURL, SSLError
from bs4 import BeautifulSoup

import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logger(name='root', log_level=logging.INFO):
    """
    기본 로거 설정 함수 (날짜별로 로그 기록)
    :param name: 로거 이름 (기본은 'root')
    :param log_level: 로그 레벨 (기본은 INFO)
    :return: 설정된 로거 객체
    """
    # 로그 형식 설정
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 콘솔 핸들러 설정 (콘솔 출력)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    # 파일 핸들러 설정 (날짜별 로그 파일 기록)
    # 하루마다 로그 파일을 새로 만듭니다.
    # 7일치 로그만 보관하고, 그 이전의 로그 파일은 삭제합니다.
    file_handler = TimedRotatingFileHandler('app.log', when='midnight', interval=1, backupCount=7)
    file_handler.setFormatter(log_formatter)

    # 로거 설정
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# 로거 설정 (애플리케이션 시작 시 한 번만 호출)
logger = setup_logger()

# InsecureRequestWarning 경고 무시 설정
warnings.simplefilter('ignore', InsecureRequestWarning)

def main_request(page, timeout=30):

    # HTTP 요청 헤더 설정
    headers = {
        'authority': 'en.zalando.de',
        'method': 'GET',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko,en;q=0.9,en-US;q=0.8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'
    }

    # 요청할 URL 설정
    url = 'https://en.zalando.de/womens-clothing/'

    # 요청할 페이로드 설정
    payload = {
        'p': page
    }

    try:

        # POST 요청을 보내고 응답 받기
        response = requests.post(url, headers=headers, data=payload, verify=True, timeout=timeout)

        # 응답의 인코딩을 UTF-8로 설정
        response.encoding = 'utf-8'

        # HTTP 상태 코드가 200이 아닌 경우 예외 처리
        response.raise_for_status()

        # 상태 코드가 200인 경우 응답 JSON 반환
        if response.status_code == 200:
            return response.text  # JSON 형식으로 응답 반환
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


def process_data(html):
    data_list = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        board_list = soup.find('div', class_='_5qdMrS _75qWlu iOzucJ') if soup else None

        if not board_list:
            logger.error("Board list not found")
            return []

        if len(board_list) > 0:

            for index, view in enumerate(board_list):
                a_tag = view.find('a', class_='_LM tCiGa7 ZkIJC- JT3_zV CKDt_l CKDt_l LyRfpJ')

                if a_tag:
                    href_text = a_tag['href'] if 'href' in a_tag.attrs else ''
                    logger.info(href_text)
                    data_list.append(href_text)

    except Exception as e:
        logger.error(f"Error : {e}")
    finally:
        return data_list



def main():
    html = main_request(1)
    if html:
        data_list = process_data(html)
        logger.info(len(data_list))
    else:
        return None



if __name__ == '__main__':
    main()
