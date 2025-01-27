import time

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
import pandas as pd

image_main_directory = 'metastyle_images'
company_name = 'metastyle'
excel_filename = ''

def setup_driver():
    """
    Selenium 웹 드라이버를 설정하고 반환하는 함수입니다.
    """
    chrome_options = Options()
    ###### 자동 제어 감지 방지 #####
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    ##### 화면 최대 #####
    chrome_options.add_argument("--start-maximized")

    ##### 화면이 안보이게 함 #####
    chrome_options.add_argument("headless")

    ##### 자동 경고 제거 #####
    chrome_options.add_experimental_option('useAutomationExtension', False)

    ##### 로깅 비활성화 #####
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    ##### 자동화 탐지 방지 설정 #####
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    ##### 자동으로 최신 크롬 드라이버를 다운로드하여 설치하는 역할 #####

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    ##### CDP 명령으로 자동화 감지 방지 #####
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })

    # 브라우저 위치와 크기 설정
    # driver.set_window_position(0, 0)  # 왼쪽 위 (0, 0) 위치로 이동
    # driver.set_window_size(1200, 900)  # 크기를 500x800으로 설정
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
            print(f"Unexpected status code: {response.status_code}")
            return None

    # 타임아웃 오류 처리
    except Timeout:
        print("Request timed out")
        return None

    # 너무 많은 리다이렉트 발생 시 처리
    except TooManyRedirects:
        print("Too many redirects")
        return None

    # 네트워크 연결 오류 처리
    except ConnectionError:
        print("Network connection error")
        return None

    # 기타 모든 예외 처리
    except RequestException as e:
        print(f"Request failed: {e}")
        return None

    # 예상치 못한 예외 처리
    except Exception as e:
        print(f"Unexpected exception: {e}")
        return None


def process_data(html):
    data_list = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        board_list = soup.find_all('div', class_='_5qdMrS _75qWlu iOzucJ') if soup else None

        if not board_list:
            print("Board list not found")
            return []

        if len(board_list) > 0:

            for index, view in enumerate(board_list):
                a_tag = view.find('a', class_='_LM tCiGa7 ZkIJC- JT3_zV CKDt_l CKDt_l LyRfpJ')

                if a_tag:
                    href_text = a_tag['href'] if 'href' in a_tag.attrs else ''
                    print(href_text)
                    data_list.append(href_text)

    except Exception as e:
        print(f"Error : {e}")
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
            print(f"Failed to retrieve page content for {url}")
            driver.quit()
            return None

    except Exception as e:
        print(f"Request failed: {e}")
        driver.quit()
        return None


def process_data_selenium(driver):
    data_list = []
    try:
        # 웹페이지에서 필요한 요소 찾기
        board_list = driver.find_elements(By.CSS_SELECTOR, 'div._5qdMrS._75qWlu.iOzucJ')

        if not board_list:
            print("Board list not found")
            return []

        if len(board_list) > 0:
            for index, view in enumerate(board_list):
                # 각 항목에서 a 태그 찾기
                a_tag = view.find_element(By.CSS_SELECTOR, 'a._LM.tCiGa7.ZkIJC-.JT3_zV.CKDt_l.CKDt_l.LyRfpJ')

                if a_tag:
                    href_text = a_tag.get_attribute('href')  # href 속성 가져오기
                    print(href_text)
                    data_list.append(href_text)

    except Exception as e:
        print(f"Error : {e}")
    finally:
        return data_list


def process_data(html):
    data_list = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        board_list = soup.find_all('div', class_='_5qdMrS _75qWlu iOzucJ') if soup else None

        if not board_list:
            print("Board list not found")
            return []

        if len(board_list) > 0:

            for index, view in enumerate(board_list):
                a_tag = view.find('a', class_='_LM tCiGa7 ZkIJC- JT3_zV CKDt_l CKDt_l LyRfpJ')

                if a_tag:
                    href_text = a_tag['href'] if 'href' in a_tag.attrs else ''
                    if not href_text.startswith('https://en.zalando.de'):
                        href_text = 'https://en.zalando.de' + href_text
                    print(href_text)
                    data_list.append(href_text)

    except Exception as e:
        print(f"Error : {e}")
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

def get_detail_data(html):
    images = set()
    product_name = ''
    detail = []
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # 이미지 다운로드 [시작] ====================
        img_list = soup.find_all('li', class_='LiPgRT DlJ4rT S3xARh') if soup else None
        print(f'img_list : {len(img_list)}')
        if not img_list:
            print("Image list not found")
            return []

        for index, view in enumerate(img_list):
            time.sleep(1)
            img = view.find('img')

            if img:
                img_url = img['src'] if 'src' in img.attrs else ''
                images.add(img_url)

        images = list(images)
        images = images[:2]

        product_name = soup.find('span', class_='EKabf7 R_QwOV').get_text()

        # <div> 태그 중 'data-testid' 속성이 'pdp-accordion-details'인 요소 찾기
        accordion_details = soup.find('div', {'data-testid': 'pdp-accordion-details'})

        # <dl> 태그 안의 모든 <div>를 찾아서 텍스트 추출
        dl_items = accordion_details.find_all('div', class_='qMOFyE')

        # 텍스트를 담을 배열 초기화


        # <dl> 안의 모든 <div>에서 <dt>와 <dd> 텍스트를 결합하여 배열에 담기
        for item in dl_items:
            dt = item.find('dt')  # <dt> 요소
            dd = item.find('dd')  # <dd> 요소
            if dt and dd:
                # dt와 dd의 텍스트를 결합하여 하나의 문자열로 만들고, 이를 배열에 추가
                detail.append(f'{dt.get_text(strip=True)} {dd.get_text(strip=True)}')
    except Exception as e:
        print(f"Error in process_detail_data: {e}")
    finally:
        return images, product_name, detail


# def get_detail_data(html):
#     detail_data = []
#     try:
#         soup = BeautifulSoup(html, 'html.parser')
#
#         # 이미지 다운로드 [시작] ====================
#         img_list = soup.find_all('li', class_='LiPgRT DlJ4rT S3xARh') if soup else None
#         print(f'img_list : {len(img_list)}')
#         if not img_list:
#             print("Image list not found")
#             return []
#
#
#
#
#         if len(img_list) > 0:
#             if not os.path.exists(download_folder):
#                 os.makedirs(download_folder)  # 이미지 저장 폴더가 없으면 생성
#             img_result_list = []
#
#             for index, view in enumerate(img_list):
#                 time.sleep(1)
#                 img = view.find('img')
#
#                 if img:
#                     img_url = img['src'] if 'src' in img.attrs else ''
#                     print(f'img_url : {img_url}')
#
#                     if img_url:
#                         # 이미지 파일 이름 생성 (index + 1로 이름 지정)
#                         img_url = modify_img_url(img_url)
#                         print(f"Modified img_url: {img_url}")
#                         img_filename = os.path.join(download_folder, f"image_{index + 1}.jpg")
#
#                         # 이미지 다운로드
#                         try:
#                             img_response = requests.get(img_url, stream=True)
#                             if img_response.status_code == 200:
#                                 with open(img_filename, 'wb') as file:
#                                     for chunk in img_response.iter_content(1024):
#                                         file.write(chunk)
#                                 print(f"Image {index + 1} saved to {img_filename}")
#                                 img_result_list.append(img_filename)  # 저장한 파일 경로를 detail_data에 추가
#                             else:
#                                 print(f"Failed to download image {index + 1}: {img_url}")
#                         except Exception as e:
#                             print(f"Error downloading image {index + 1}: {e}")
#         # 이미지 다운로드 [종료] ====================
#
#
#
#
#
#
#
#     except Exception as e:
#         print(f"Error in process_detail_data: {e}")
#     finally:
#         return detail_data


def download_image(image_url, site_name, category, product_name, obj):
    global image_main_directory
    local_file_path = ''

    try:
        # 이미지 이름 변경: URL에서 'media/...' 부분을 'media_'로 변경
        # image_name = image_url.split("media/")[-1].replace("/", "_")  # 'media/...'를 'media_...'로 변경
        image_name = image_url.split("/")[-1]
        obj['image_name'] = image_name
        # 현재 작업 디렉토리 경로 설정
        local_directory = os.getcwd()  # 현재 작업 디렉토리

        # 'metastyle_images' 폴더를 최상위로 설정
        image_directory = os.path.join(local_directory, image_main_directory)

        # 로컬 파일 경로 설정: site_name/category/product_name/media_...
        local_file_path = os.path.join(image_directory, site_name, category, product_name, image_name)

        # 로컬 디렉토리 경로가 존재하지 않으면 생성
        if not os.path.exists(os.path.dirname(local_file_path)):
            os.makedirs(os.path.dirname(local_file_path))

        # 이미지 다운로드
        response = requests.get(image_url)
        response.raise_for_status()  # 오류 발생 시 예외 처리 (예: 404, 500 등)

        # 로컬에 이미지 저장
        with open(local_file_path, 'wb') as f:
            f.write(response.content)

    except requests.exceptions.MissingSchema:
        obj['error_message'] = f"Error: Invalid URL {image_url}. The URL format seems incorrect."
        obj['image_success'] = 'X'
    except requests.exceptions.RequestException as e:
        obj['error_message'] = f"Error downloading the image from {image_url}: {e}"
        obj['image_success'] = 'X'
    except OSError as e:
        obj['error_message'] = f"Error saving the image to {local_file_path}: {e}"
        obj['image_success'] = 'X'
    except Exception as e:
        obj['error_message'] = f"Unexpected error: {e}"
        obj['image_success'] = 'X'


def save_to_excel_one_by_one(results, file_name, sheet_name='Sheet1'):
    try:
        # 결과 데이터가 비어있는지 확인
        if not results:
            print("결과 데이터가 비어 있습니다.")
            return False

        # 파일이 존재하는지 확인
        if os.path.exists(file_name):
            # 파일이 있으면 기존 데이터 읽어오기
            df_existing = pd.read_excel(file_name, sheet_name=sheet_name, engine='openpyxl')

            # 새로운 데이터를 DataFrame으로 변환
            df_new = pd.DataFrame(results)

            # 기존 데이터에 새로운 데이터 추가
            for index, row in df_new.iterrows():
                # 기존 DataFrame에 한 행씩 추가하는 부분
                df_existing = pd.concat([df_existing, pd.DataFrame([row])], ignore_index=True)

            # 엑셀 파일에 덧붙이기 (index는 제외)
            with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_existing.to_excel(writer, sheet_name=sheet_name, index=False)

            return True  # 엑셀 파일에 성공적으로 덧붙였으면 True 리턴

        else:
            # 파일이 없으면 새로 생성
            df = pd.DataFrame(results)
            with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            return True  # 새로 생성한 파일에 데이터를 저장했으면 True 리턴

    except Exception as e:
        # 예기치 않은 오류 처리
        print(f'엑셀 에러 발생: {e}')
        return False


def main():
    # 셀레니움 드라이버 초기화
    driver = setup_driver()

    url = 'https://en.zalando.de'
    sub_url = '/womens-clothing/'
    site_name = "zalando"
    category = 'womens-clothing'

    page = 2
    main_url = f'{url}{sub_url}?p={page}'

    html = main_request(main_url, driver, 5)

    result_list = []

    if html:
        detail_list = process_data(html)
        print(len(detail_list))
        for index, detail_url in enumerate(detail_list):

            if index == 1:
                break
            detail_html = sub_request(detail_url)

            if detail_html:
                images, product_name, detail = get_detail_data(detail_html)

                for idx, image_url in enumerate(images, start=0):

                    obj = {
                        'site_name': site_name,
                        'category': category,
                        'product_name': product_name,
                        'image_name': '',
                        'image_success': 'O',
                        'detail': detail,
                        'images': images,
                        'main_url': main_url,
                        'detail_url': detail_url,
                        'error_message': '',
                        'reg_date': ''
                    }

                    download_image(image_url, site_name, category, product_name, obj)

                    result_list.append(obj)

                    save_to_excel_one_by_one([obj], excel_filename)  # 엑셀 파일 경로를 지정

                    time.sleep(1)

    else:
        return None

    # 드라이버 종료
    driver.quit()


if __name__ == '__main__':
    main()

