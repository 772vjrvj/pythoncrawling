import mimetypes
import os
import ssl
import time
from io import BytesIO
import json
import re

import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from google.cloud import storage
from google.oauth2 import service_account
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.utils.utils_time import get_current_yyyymmddhhmmss, get_current_formatted_datetime
from src.utils.utils_number import divide_and_truncate_per
from requests.exceptions import RequestException, Timeout, TooManyRedirects
from urllib.parse import urlparse

ssl._create_default_https_context = ssl._create_unverified_context

image_main_directory = 'zalando_images'
company_name = 'zalando'
site_name = 'ZALANDO'
excel_filename = ''
baseUrl = "https://en.zalando.de"


# API
class ApiZalandoSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)         # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널


    # 초기화
    def __init__(self, checked_list):
        super().__init__()
        self.baseUrl = baseUrl
        self.sess = requests.Session()
        self.checked_list = checked_list
        self.running = True  # 실행 상태 플래그 추가
        self.driver = None


    # 프로그램 실행
    def run(self):
        global image_main_directory, company_name, site_name, excel_filename, baseUrl

        self.log_signal.emit("크롤링 시작")
        current_cnt = 0
        current_page = 0
        before_pro_value = 0
        result_list = []

        if self.checked_list:
            self.log_signal.emit("크롤링 사이트 인증을 시도중입니다. 잠시만 기다려주세요.")
            self.login()
            self.log_signal.emit("크롤링 사이트 인증에 성공하였습니다.")
            current_time = get_current_yyyymmddhhmmss()
            excel_filename = f"{company_name}_{current_time}.xlsx"

            self.log_signal.emit(f"전체 상품수 계산을 시작합니다. 잠시만 기다려주세요.")
            check_obj_list = self.total_cnt_cal()
            total_cnt = sum(int(obj['total_item_cnt']) for obj in check_obj_list)
            total_pages = sum(int(obj['total_page_cnt']) for obj in check_obj_list)

            self.log_signal.emit(f"전체 항목수 {len(self.checked_list)}개")
            self.log_signal.emit(f"전체 상품수 {total_cnt} 개")
            self.log_signal.emit(f"전체 페이지수 {total_pages} 개")
            for index, check_obj in enumerate(check_obj_list, start=1):
                if not self.running:  # 실행 상태 확인
                    self.log_signal.emit("크롤링이 중지되었습니다.")
                    break
                item = check_obj['name']
                start_page = int(check_obj['start_page'])
                end_page = int(check_obj['end_page'])
                main_url, partition = self.get_url_info(item)
                for indx, page in enumerate(range(start_page, end_page + 1), start=1):
                    if not self.running:  # 실행 상태 확인
                        break
                    page_url = f"{main_url}{partition}p={page}"
                    main_html = self.main_request(page_url, 5)
                    if main_html:
                        products, totalPages = self.process_data(main_html)
                        for idx, detail_url in enumerate(products, start=1):
                            if not self.running:  # 실행 상태 확인
                                break
                            current_cnt += 1
                            now_per = divide_and_truncate_per(current_cnt, total_cnt)
                            self.log_signal.emit(f'{site_name}({now_per}%)  {item}({index}/{len(check_obj_list)})  TotalPage({current_page}/{total_pages})  TotalProduct({current_cnt}/{total_cnt})')
                            detail_html = self.sub_request(detail_url)
                            if detail_html:
                                images, brand_name, product_name, detail = self.get_detail_data(detail_html)
                                for ix, image_url in enumerate(images, start=1):
                                    if not self.running:
                                        break
                                    self.log_signal.emit(f'{item}  Page({page}/{end_page})[{indx}/{total_pages}]  Product({idx}/{len(products)})  Image({ix}/{len(images)})')
                                    obj = {
                                        'site_name': site_name,
                                        'category': item,
                                        'brand_name': brand_name,
                                        'product_name': product_name,
                                        'image_name': '',
                                        'image_success': 'O',
                                        'page': page,
                                        'page_index': idx,
                                        'detail': detail,
                                        'images': images,
                                        'main_url': main_url,
                                        'detail_url': detail_url,
                                        'excel_save': 'O',
                                        'error_message': '',
                                        'reg_date': ''
                                    }

                                    # 이미지 다운로드
                                    # self.download_image(image_url, site_name, category, product_name, obj)
                                    # 구글 업로드
                                    self.google_cloud_upload(site_name, item, product_name, image_url, obj)
                                    obj['reg_date'] = get_current_formatted_datetime()
                                    self.save_to_excel_one_by_one([obj], excel_filename, obj)  # 엑셀 파일 경로를 지정
                                    self.log_signal.emit(f'data : {obj}')
                                    result_list.append(obj)
                                    time.sleep(1)
                                pro_value = (current_cnt / total_cnt) * 1000000
                                self.progress_signal.emit(before_pro_value, pro_value)
                                before_pro_value = pro_value

        self.progress_signal.emit(before_pro_value, 1000000)
        self.log_signal.emit(f"=============== 처리 데이터 수 : {len(result_list)}")
        self.log_signal.emit("=============== 크롤링 종료")
        self.progress_end_signal.emit()


    # 프로그램 중단
    def stop(self):
        """스레드 중지를 요청하는 메서드"""
        self.running = False


    # 로그인 쿠키가져오기
    def login(self):
        """
        Selenium 웹 드라이버를 설정하고 반환하는 함수입니다.
        """
        chrome_options = Options()
        ###### 자동 제어 감지 방지 #####
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        ##### 화면 최대 #####
        chrome_options.add_argument("--start-maximized")

        ##### 화면이 안보이게 함 #####
        # chrome_options.add_argument("--headless")

        ##### 자동 경고 제거 #####
        chrome_options.add_experimental_option('useAutomationExtension', False)

        ##### 로깅 비활성화 #####
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        ##### 자동화 탐지 방지 설정 #####
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        ##### 자동으로 최신 크롬 드라이버를 다운로드하여 설치하는 역할 #####

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        ##### CDP 명령으로 자동화 감지 방지 #####
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
            '''
        })

    def main_request(self, url, wait_time):

        try:
            # 웹페이지 요청
            self.driver.get(url)

            # 페이지 로딩 대기 (적절한 대기 시간 필요)
            time.sleep(wait_time)

            # 페이지 소스 가져오기
            html = self.driver.page_source

            # 상태 코드 확인 (브라우저에서 처리하므로 확인할 수 없음, 대신 로딩이 완료되었는지 확인)
            if html:
                return html
            else:
                self.log_signal.emit(f"Failed to retrieve page content for {url}")
                self.driver.quit()
                return None

        except Exception as e:
            self.log_signal.emit(f"Request failed: {e}")
            self.driver.quit()
            return None


    # 페이지 데이터 가져오기
    def get_api_request(self, category, slug, page):

        main_url_api = "https://api.mytheresa.com/api"

        headers = {
            "authority": "api.mytheresa.com",
            "method": "POST",
            "path": "/api",
            "scheme": "https",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en",
            "content-type": "application/json",
            "origin": "https://www.mytheresa.com",
            "referer": "https://www.mytheresa.com/",
            "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
            "x-country": "US",
            "x-geo": "KR",
            "x-nsu": "false",
            "x-region": "BY",
            "x-section": f"{category}",
            "x-store": "US",
        }

        payload = {
            "operationName": "XProductListingPageQuery",
            "variables": {
                "categories": [],
                "colors": [],
                "designers": [],
                "fta": None,
                "page": page,
                "patterns": [],
                "reductionRange": [],
                "saleStatus": None,
                "size": 60,
                "sizesHarmonized": [],
                "slug": f"{slug}",
                "sort": None
            },
            "query": "query XProductListingPageQuery($categories: [String], $colors: [String], $designers: [String], $fta: Boolean, $page: Int, $patterns: [String], $reductionRange: [String], $saleStatus: SaleStatusEnum, $size: Int, $sizesHarmonized: [String], $slug: String, $sort: String) {\n  xProductListingPage(categories: $categories, colors: $colors, designers: $designers, fta: $fta, page: $page, patterns: $patterns, reductionRange: $reductionRange, saleStatus: $saleStatus, size: $size, sizesHarmonized: $sizesHarmonized, slug: $slug, sort: $sort) {\n    id\n    alternateUrls {\n      language\n      store\n      url\n      __typename\n    }\n    breadcrumb {\n      id\n      name\n      slug\n      __typename\n    }\n    combinedDepartmentGroupAndCategoryErpID\n    department\n    designerErpId\n    displayName\n    facets {\n      categories {\n        name\n        options {\n          id\n          name\n          slug\n          children {\n            id\n            name\n            slug\n            children {\n              id\n              name\n              slug\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        activeValue\n        __typename\n      }\n      designers {\n        name\n        options {\n          value\n          slug\n          __typename\n        }\n        activeValue\n        __typename\n      }\n      colors {\n        name\n        options {\n          value\n          __typename\n        }\n        activeValue\n        __typename\n      }\n      fta {\n        activeValue\n        name\n        options {\n          value\n          __typename\n        }\n        visibility\n        __typename\n      }\n      patterns {\n        name\n        options {\n          value\n          __typename\n        }\n        activeValue\n        __typename\n      }\n      reductionRange {\n        activeValue\n        name\n        options {\n          value\n          __typename\n        }\n        unit\n        visibility\n        __typename\n      }\n      saleStatus {\n        activeValue\n        name\n        options {\n          value\n          __typename\n        }\n        visibility\n        __typename\n      }\n      sizesHarmonized {\n        name\n        options {\n          value\n          __typename\n        }\n        activeValue\n        __typename\n      }\n      __typename\n    }\n    isMonetisationExcluded\n    isSalePage\n    pagination {\n      ...paginationData\n      __typename\n    }\n    products {\n      ...productData\n      __typename\n    }\n    sort {\n      currentParam\n      params\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment paginationData on XPagination {\n  currentPage\n  itemsPerPage\n  totalItems\n  totalPages\n  __typename\n}\n\nfragment priceData on XSharedPrice {\n  currencyCode\n  currencySymbol\n  discount\n  discountEur\n  extraDiscount\n  finalDuties\n  hint\n  includesVAT\n  isPriceModifiedByRegionalRules\n  original\n  originalDuties\n  originalDutiesEur\n  originalEur\n  percentage\n  regionalRulesModifications {\n    priceColor\n    __typename\n  }\n  regular\n  vatPercentage\n  __typename\n}\n\nfragment productData on XSharedProduct {\n  color\n  combinedCategoryErpID\n  combinedCategoryName\n  department\n  description\n  designer\n  designerErpId\n  designerInfo {\n    designerId\n    displayName\n    slug\n    __typename\n  }\n  displayImages\n  enabled\n  features\n  fta\n  hasMultipleSizes\n  hasSizeChart\n  hasStock\n  isComingSoon\n  isInWishlist\n  isPurchasable\n  isSizeRelevant\n  labelObjects {\n    id\n    label\n    __typename\n  }\n  labels\n  mainPrice\n  mainWaregroup\n  name\n  price {\n    ...priceData\n    __typename\n  }\n  priceDescription\n  promotionLabels {\n    label\n    type\n    __typename\n  }\n  seasonCode\n  sellerOrigin\n  sets\n  sizeAndFit\n  sizesOnStock\n  sizeTag\n  sizeType\n  sku\n  slug\n  variants {\n    allVariants {\n      availability {\n        hasStock\n        lastStockQuantityHint\n        __typename\n      }\n      isInWishlist\n      size\n      sizeHarmonized\n      sku\n      __typename\n    }\n    availability {\n      hasStock\n      lastStockQuantityHint\n      __typename\n    }\n    isInWishlist\n    price {\n      currencyCode\n      currencySymbol\n      discount\n      discountEur\n      extraDiscount\n      includesVAT\n      isPriceModifiedByRegionalRules\n      original\n      originalEur\n      percentage\n      regionalRulesModifications {\n        priceColor\n        __typename\n      }\n      vatPercentage\n      __typename\n    }\n    size\n    sizeHarmonized\n    sku\n    __typename\n  }\n  __typename\n}\n"
        }

        try:
            # POST 요청 보내기
            res = self.sess.post(main_url_api, headers=headers, json=payload)

            # 응답 상태 확인
            if res.status_code == 200:
                try:
                    response_json = res.json()  # JSON 응답 파싱
                    return response_json
                except ValueError as e:
                    # JSON 파싱 실패
                    self.log_signal.emit(f"JSON 파싱 에러: {e}")
                    return None
            else:
                # 상태 코드가 200이 아닌 경우
                self.log_signal.emit(f"HTTP 요청 실패: 상태 코드 {res.status_code}, 내용: {res.text}")
                return None

        except Exception as e:
            # 네트워크 에러 또는 기타 예외 처리
            self.log_signal.emit(f"요청 중 에러 발생: {e}")
            return None


    # 상세보기 데이터 가져오기
    def get_detail_data(self, html):
        images = []
        brand_name = ''
        product_name = ''
        detail = []
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 이미지 다운로드 [시작] ====================
            img_list = soup.find_all('li', class_='LiPgRT DlJ4rT S3xARh') if soup else []

            if len(img_list) < 1:
                self.log_signal.emit("Image list not found")

            images = set()
            for index, view in enumerate(img_list):
                img = view.find('img')

                if img:
                    img_url = img['src'] if 'src' in img.attrs else ''
                    images.add(img_url)

            images = list(images)
            images = images[:2]

            product_tag = soup.find('span', class_='EKabf7 R_QwOV')
            product_name = product_tag.get_text(strip=True) if product_tag else ''

            brand_tag = soup.find('span', class_='OBkCPz Z82GLX m3OCL3 HlZ_Tf _5Yd-hZ')
            brand_name = brand_tag.get_text(strip=True) if brand_tag else ''

            # <div> 태그 중 'data-testid' 속성이 'pdp-accordion-details'인 요소 찾기
            accordion_details = soup.find('div', {'data-testid': 'pdp-accordion-details'})

            # <dl> 태그 안의 모든 <div>를 찾아서 텍스트 추출
            dl_items = accordion_details.find_all('div', class_='qMOFyE') if accordion_details else []

            # 텍스트를 담을 배열 초기화

            # <dl> 안의 모든 <div>에서 <dt>와 <dd> 텍스트를 결합하여 배열에 담기
            for item in dl_items:
                dt = item.find('dt')  # <dt> 요소
                dd = item.find('dd')  # <dd> 요소
                if dt and dd:
                    # dt와 dd의 텍스트를 결합하여 하나의 문자열로 만들고, 이를 배열에 추가
                    detail.append(f'{dt.get_text(strip=True)} {dd.get_text(strip=True)}')
        except Exception as e:
            self.log_signal.emit(f"Error in process_detail_data: {e}")
        finally:
            return images, brand_name, product_name, detail


    # URL 가져오기
    def get_url_info(self, item):
        global baseUrl

        main_url = ''
        partition = ''

        if item:
            name = item.lower()

            if name == 'men':
                main_url = f"{baseUrl}/mens-clothing"
                partition = '/?'
            elif name == 'women':
                main_url = f"{baseUrl}/womens-clothing"
                partition = '/?'
            elif name == 'boys':
                main_url = f"{baseUrl}/kids/?gender=25"
                partition = '&'
            elif name == 'girls':
                main_url = f"{baseUrl}/kids/?gender=26"
                partition = '&'
            elif name == 'baby':
                main_url = f"{baseUrl}/kids/?gender=4"
                partition = '&'

        return main_url, partition


    # 카테고리별 전체 개수
    def process_total_data(self, html):
        total_cnt = 0
        total_page = 0
        try:
            soup = BeautifulSoup(html, 'html.parser')

            product_count_tag = soup.find('span', class_='voFjEy _2kjxJ6 m3OCL3 Yb63TQ lystZ1 m3OCL3') if soup else None

            if product_count_tag:
                total_cnt = re.sub(r'\D', '', product_count_tag.text)  # 숫자만 추출


            total_page_element = soup.find('span', class_='voFjEy _2kjxJ6 m3OCL3 HlZ_Tf jheIXc Gj7Swn') if soup else None

            # 숫자 추출
            if total_page_element:
                # "Page 2 of 428"에서 마지막 숫자 추출
                match = re.search(r'\b\d[\d,]*$', total_page_element.text.strip())
                if match:
                    # 콤마 제거
                    total_page = match.group().replace(',', '')

        except Exception as e:
            self.log_signal.emit(f"Error : {e}")
        finally:
            return int(total_cnt), int(total_page)


    # 상세리스트 가져오기
    def process_data(self, html):
        data_list = []
        total_page = 0
        try:
            soup = BeautifulSoup(html, 'html.parser')
            board_list = soup.find_all('div', class_='_5qdMrS _75qWlu iOzucJ') if soup else None

            if not board_list:
                self.log_signal.emit("Board list not found")
                return []

            if len(board_list) > 0:

                for index, view in enumerate(board_list):
                    a_tag = view.find('a', class_='_LM tCiGa7 ZkIJC- JT3_zV CKDt_l CKDt_l LyRfpJ')

                    if a_tag:
                        href_text = a_tag['href'] if 'href' in a_tag.attrs else ''
                        data_list.append(href_text)

            total_page_element = soup.find('span', class_='voFjEy _2kjxJ6 m3OCL3 HlZ_Tf jheIXc Gj7Swn') if soup else None

            # 숫자 추출
            if total_page_element:
                # "Page 2 of 428"에서 마지막 숫자 추출
                match = re.search(r'\b\d[\d,]*$', total_page_element.text.strip())
                if match:
                    # 콤마 제거
                    total_page = match.group().replace(',', '')
        except Exception as e:
            self.log_signal.emit(f"Error : {e}")
        finally:
            return data_list, total_page


    # 전체 갯수 조회
    def total_cnt_cal(self):
        check_obj_list = []
        for index, checked_obj in enumerate(self.checked_list, start=1):
            name = checked_obj['name']
            start_page = checked_obj['start_page']
            end_page = checked_obj['end_page']

            main_url, partition = self.get_url_info(name)
            main_html = self.main_request(main_url, 3)
            total_items_cnt, total_page = self.process_total_data(main_html)

            last_page_cnt = total_items_cnt % 84

            if not end_page:
                end_page = total_page

            if not start_page:
                start_page = 1

            if end_page >= total_page:
                end_page = total_page
                if start_page >= end_page:
                    start_page = end_page
                    total_items_cnt = last_page_cnt
                elif start_page != 1:
                    total_items_cnt = ((end_page - start_page) * 84) + last_page_cnt
            if end_page < total_page:
                if start_page >= end_page:
                    start_page = end_page
                    total_items_cnt = 84
                else:
                    total_items_cnt = (end_page - start_page + 1) * 84

            checked_obj['start_page'] = start_page
            checked_obj['end_page'] = end_page
            checked_obj['total_page_cnt'] = end_page - start_page + 1
            checked_obj['total_item_cnt'] = total_items_cnt
            checked_obj['item'] = name.lower()

            check_obj_list.append(checked_obj)

        return check_obj_list



    def sub_request(self, url, timeout=30):

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
                self.log_signal.emit(f"Unexpected status code: {response.status_code}")
                return None

        # 타임아웃 오류 처리
        except Timeout:
            self.log_signal.emit("Request timed out")
            return None

        # 너무 많은 리다이렉트 발생 시 처리
        except TooManyRedirects:
            self.log_signal.emit("Too many redirects")
            return None

        # 네트워크 연결 오류 처리
        except ConnectionError:
            self.log_signal.emit("Network connection error")
            return None

        # 기타 모든 예외 처리
        except RequestException as e:
            self.log_signal.emit(f"Request failed: {e}")
            return None

        # 예상치 못한 예외 처리
        except Exception as e:
            self.log_signal.emit(f"Unexpected exception: {e}")
            return None


    # 엑셀 한껀씩 저장
    def save_to_excel_one_by_one(self, results, file_name, obj, sheet_name='Sheet1'):
        try:
            # 결과 데이터가 비어있는지 확인
            if not results:
                self.log_signal.emit("결과 데이터가 비어 있습니다.")
                obj['excel_save'] = 'X'
            else:
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

                    self.log_signal.emit('엑셀 추가 성공')

                else:
                    # 파일이 없으면 새로 생성
                    df = pd.DataFrame(results)
                    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        self.log_signal.emit('엑셀 추가 성공')

                obj['excel_save'] = 'O'

        except Exception as e:
            # 예기치 않은 오류 처리
            self.log_signal.emit(f'엑셀 에러 발생: {e}')
            obj['excel_save'] = 'X'
            obj['error_message'] = e


    # 구글 클라우드 업로드
    def google_cloud_upload(self, site_name, category, product_name, image_url, obj):
        try:
            # 프로그램 실행 경로 기준으로 파일 경로 설정
            base_path = os.getcwd()
            service_account_path = os.path.join(base_path, "styleai-ai-designer-ml-external.json")
            user_config_path = os.path.join(base_path, "user.json")

            # user.json에서 설정 값 로드
            with open(user_config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)

            project_id = user_config.get("project_id")
            bucket_name = user_config.get("bucket")

            if not project_id or not bucket_name:
                raise ValueError("Invalid configuration in user.json. Check 'project_id' and 'bucket' fields.")

            # GCP 클라우드 스토리지 클라이언트 생성 (서비스 계정 인증 사용)
            credentials = service_account.Credentials.from_service_account_file(service_account_path)
            storage_client = storage.Client(credentials=credentials, project=project_id)
            bucket = storage_client.bucket(bucket_name)

            # 다운로드할 이미지 URL에서 이미지 데이터 가져오기
            response = requests.get(image_url)
            response.raise_for_status()  # 오류 발생 시 예외 처리

            # 이미지 데이터를 메모리에서 처리
            image_data = BytesIO(response.content)

            # URL 파싱
            parsed_url = urlparse(image_url)

            # path의 마지막 부분 추출
            image_name = parsed_url.path.split('/')[-1]

            # 업로드할 경로 설정: site_name/category/product_name/media_...
            # blob_name = f"test_program_20250117/{site_name}/{category}_{image_name}"
            blob_name = f"{site_name}/{category}/{category}_{image_name}"

            # 이미지의 MIME 타입을 자동으로 감지
            mime_type, _ = mimetypes.guess_type(image_url)
            if not mime_type:
                mime_type = "application/octet-stream"  # MIME 타입을 감지할 수 없는 경우 기본값 설정

            # Cloud Storage에 이미지 업로드
            blob = bucket.blob(blob_name)
            blob.upload_from_file(image_data, content_type=mime_type)

            # 이미지 업로드 확인
            if blob.exists():  # 업로드 확인
                self.log_signal.emit(f"success {image_url} -> {bucket_name}/{blob_name}.")
                obj['image_name'] = f"{category}_{image_name}"
            else:
                obj['error_message'] = f"Image upload failed for {image_url}. Check the destination bucket."
                obj['image_success'] = 'X'
                self.log_signal.emit(f"Image upload failed for {image_url}. Check the destination bucket.")

        except requests.RequestException as e:
            self.log_signal.emit(f"Error downloading image from {image_url}: {str(e)}")
            obj['error_message'] = f"Error downloading image from {image_url}: {str(e)}"
            obj['image_success'] = 'X'
        except json.JSONDecodeError:
            self.log_signal.emit("Error reading or parsing user.json. Check its content.")
            obj['error_message'] = "Error reading or parsing user.json. Check its content."
            obj['image_success'] = 'X'
        except FileNotFoundError as e:
            self.log_signal.emit(f"File not found: {str(e)}")
            obj['error_message'] = f"File not found: {str(e)}"
            obj['image_success'] = 'X'
        except ValueError as e:
            self.log_signal.emit(str(e))
            obj['error_message'] = f"{str(e)}"
            obj['image_success'] = 'X'
        except Exception as e:
            self.log_signal.emit(f"An unexpected error occurred: {str(e)}")
            obj['error_message'] = f"An unexpected error occurred: {str(e)}"
            obj['image_success'] = 'X'


        # 해당 경로에 있는 모든 이미지 목록 출력 (site_name/category/product_name/ 경로)
        # blobs = list(bucket.list_blobs(prefix=f"{site_name}"))  # 경로 내의 모든 파일 나열
        # if any(blob.name == blob_name for blob in blobs):
        #     self.log_signal.emit(f"업로드 완료: {blob_name}")
        # else:
        #     self.log_signal.emit(f"업로드 실패: {blob_name}이 존재하지 않습니다.")


    # 이미지 로컬 다운로드
    def download_image(self, image_url, site_name, category, product_name, obj):
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







