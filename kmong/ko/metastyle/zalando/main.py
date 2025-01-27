import logging
import time
from logging.handlers import TimedRotatingFileHandler

from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from requests.exceptions import RequestException, Timeout, TooManyRedirects
from selenium import webdriver
import os
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


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


def setup_driver():
    """
    Selenium 웹 드라이버를 설정하고 반환하는 함수입니다.
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 사용자 에이전트 설정
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # 자동화 탐지 방지 설정
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 크롬 드라이버 실행 및 자동화 방지 우회
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })

    # 브라우저 위치와 크기 설정
    driver.set_window_position(0, 0)  # 왼쪽 위 (0, 0) 위치로 이동
    driver.set_window_size(1200, 900)  # 크기를 500x800으로 설정

    return driver


def sub_request(url, timeout=30):

    # HTTP 요청 헤더 설정
    headers = {
        'method': 'GET',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko,en;q=0.9,en-US;q=0.8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
    }

    try:

        # POST 요청을 보내고 응답 받기
        # response = requests.get(url, headers=headers, params=payload, timeout=timeout)
        response = requests.get(url, headers=headers, timeout=timeout)

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
        board_list = soup.find_all('div', class_='_5qdMrS _75qWlu iOzucJ') if soup else None

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

def main_request(url, driver, wait_time):

    try:
        # 웹페이지 요청
        driver.get(url)

        # 페이지 로딩 대기 (적절한 대기 시간 필요)
        time.sleep(wait_time)

        # 페이지 소스 가져오기
        html = driver.page_source

        # 상태 코드 확인 (브라우저에서 처리하므로 확인할 수 없음, 대신 로딩이 완료되었는지 확인)
        if html:
            return html
        else:
            logging.error(f"Failed to retrieve page content for {url}")
            driver.quit()
            return None

    except Exception as e:
        logging.error(f"Request failed: {e}")
        driver.quit()
        return None


def process_data_selenium(driver):
    data_list = []
    try:
        # 웹페이지에서 필요한 요소 찾기
        board_list = driver.find_elements(By.CSS_SELECTOR, 'div._5qdMrS._75qWlu.iOzucJ')

        if not board_list:
            logger.error("Board list not found")
            return []

        if len(board_list) > 0:
            for index, view in enumerate(board_list):
                # 각 항목에서 a 태그 찾기
                a_tag = view.find_element(By.CSS_SELECTOR, 'a._LM.tCiGa7.ZkIJC-.JT3_zV.CKDt_l.CKDt_l.LyRfpJ')

                if a_tag:
                    href_text = a_tag.get_attribute('href')  # href 속성 가져오기
                    logger.info(href_text)
                    data_list.append(href_text)

    except Exception as e:
        logger.error(f"Error : {e}")
    finally:
        return data_list


def process_data(html):
    data_list = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        board_list = soup.find_all('div', class_='_5qdMrS _75qWlu iOzucJ') if soup else None

        if not board_list:
            logger.error("Board list not found")
            return []

        if len(board_list) > 0:

            for index, view in enumerate(board_list):
                a_tag = view.find('a', class_='_LM tCiGa7 ZkIJC- JT3_zV CKDt_l CKDt_l LyRfpJ')

                if a_tag:
                    href_text = a_tag['href'] if 'href' in a_tag.attrs else ''
                    if not href_text.startswith('https://en.zalando.de'):
                        href_text = 'https://en.zalando.de' + href_text
                    logger.info(href_text)
                    data_list.append(href_text)

    except Exception as e:
        logger.error(f"Error : {e}")
    finally:
        return data_list


def modify_img_url(img_url):
    # URL 파싱
    parsed_url = urlparse(img_url)
    # 쿼리 파라미터 추출
    query_params = parse_qs(parsed_url.query)

    # mwidth 값 수정
    if 'imwidth' in query_params:
        query_params['imwidth'] = ['1800']

    # 수정된 쿼리 파라미터를 다시 URL로 변환
    modified_query = urlencode(query_params, doseq=True)
    modified_url = urlunparse(parsed_url._replace(query=modified_query))

    return modified_url

def process_detail_data(html, download_folder="images_download"):
    detail_data = []
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # 이미지 다운로드 [시작] ====================
        img_list = soup.find_all('li', class_='LiPgRT DlJ4rT S3xARh') if soup else None
        logger.info(f'img_list : {len(img_list)}')
        if not img_list:
            logger.error("Image list not found")
            return []

        if len(img_list) > 0:
            if not os.path.exists(download_folder):
                os.makedirs(download_folder)  # 이미지 저장 폴더가 없으면 생성
            img_result_list = []

            for index, view in enumerate(img_list):
                time.sleep(1)
                img = view.find('img')

                if img:
                    img_url = img['src'] if 'src' in img.attrs else ''
                    logger.info(f'img_url : {img_url}')

                    if img_url:
                        # 이미지 파일 이름 생성 (index + 1로 이름 지정)
                        img_url = modify_img_url(img_url)
                        logger.info(f"Modified img_url: {img_url}")
                        img_filename = os.path.join(download_folder, f"image_{index + 1}.jpg")

                        # 이미지 다운로드
                        try:
                            img_response = requests.get(img_url, stream=True)
                            if img_response.status_code == 200:
                                with open(img_filename, 'wb') as file:
                                    for chunk in img_response.iter_content(1024):
                                        file.write(chunk)
                                logger.info(f"Image {index + 1} saved to {img_filename}")
                                img_result_list.append(img_filename)  # 저장한 파일 경로를 detail_data에 추가
                            else:
                                logger.error(f"Failed to download image {index + 1}: {img_url}")
                        except Exception as e:
                            logger.error(f"Error downloading image {index + 1}: {e}")
        # 이미지 다운로드 [종료] ====================







    except Exception as e:
        logger.error(f"Error in process_detail_data: {e}")
    finally:
        return detail_data



def main():
    # 셀레니움 드라이버 초기화
    driver = setup_driver()

    # 단위 테스트 이미지 다운로드
    # detail = 'https://en.zalando.de/bershka-trousers-bordeaux-bej21a0vs-g11.html'
    # detail_html = sub_request(detail)
    # if detail_html:
    #     detail_data = process_detail_data(detail_html)


    page = 1
    url = f'https://en.zalando.de/womens-clothing/?p={page}'

    html = main_request(url, driver, 5)
    if html:
        detail_list = process_data(html)
        logger.info(len(detail_list))
        for index, detail in enumerate(detail_list):
            detail_html = sub_request(detail)

            if detail_html:
                detail_data = process_detail_data(detail_html)

    else:
        return None

    # 드라이버 종료
    driver.quit()


if __name__ == '__main__':
    main()

