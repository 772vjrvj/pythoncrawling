import mimetypes
import os
import ssl
import time
from io import BytesIO
import json

import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from google.cloud import storage
from google.oauth2 import service_account
from selenium import webdriver

from src.utils.time_utils import get_current_yyyymmddhhmmss, get_current_formatted_datetime
from src.utils.number_utils import divide_and_truncate

ssl._create_default_https_context = ssl._create_unverified_context

image_main_directory = 'metastyle_images'
company_name = 'metastyle'
site_name = 'MYTHERESA'
excel_filename = ''
baseUrl = "https://www.mytheresa.com"


# API
class ApiMytheresaSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)         # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널

    # 초기화
    def __init__(self, checked_list):
        super().__init__()
        self.baseUrl = baseUrl
        self.sess = requests.Session()
        self.checked_list = checked_list
        self.log_signal.emit(f"checked_list : {checked_list}")
        self.running = True  # 실행 상태 플래그 추가

    # 프로그램 실행
    def run(self):
        global image_main_directory, company_name, site_name, excel_filename, baseUrl
        result_list = []
        self.log_signal.emit("크롤링 시작")

        if self.checked_list:
            self.log_signal.emit("크롤링 사이트 인증을 시도중입니다. 잠시만 기다려주세요.")
            self.login()
            self.log_signal.emit("크롤링 사이트 인증에 성공하였습니다.")
            current_time = get_current_yyyymmddhhmmss()
            excel_filename = f"{company_name}_{current_time}.xlsx"
            current_cnt = 0
            now_per = 0

            ## 전체 갯수 계산
            self.log_signal.emit(f"전체 상품수 계산을 시작합니다. 잠시만 기다려주세요.")
            check_obj_list = self.total_cnt_cal()
            total_cnt = sum(int(obj['total_item_cnt']) for obj in check_obj_list)

            self.log_signal.emit(f"전체 항목수 {len(self.checked_list)}개")
            self.log_signal.emit(f"전체 상품수 {total_cnt} 개")

            for index, check_obj in enumerate(check_obj_list, start=1):
                item = check_obj['name']
                total_pages = int(check_obj['total_page_cnt'])
                start_page = int(check_obj['start_page'])
                end_page = int(check_obj['end_page'])

                if not self.running:  # 실행 상태 확인
                    break

                self.log_signal.emit(f'{site_name}({total_cnt})[{now_per}]  {item}({index}/{len(check_obj_list)})')
                category, slug, main_url = self.get_url_info(item)

                for page in range(start_page, end_page + 1):
                    if not self.running:  # 실행 상태 확인
                        self.log_signal.emit("크롤링이 중지되었습니다.")
                        break

                    response_json = self.get_api_request(category, slug, page)
                    if isinstance(response_json, dict):
                        data = response_json.get('data', {}).get('xProductListingPage', {})
                        products = data.get('products', [])
                        self.log_signal.emit(f'{site_name}({current_cnt}/{total_cnt})[{now_per}]  {item}({index}/{len(check_obj_list)})  Page({page}/{total_pages})')
                        if not products:
                            self.log_signal.emit(f"No more data for category {category} at page {page}")
                            break

                        # products 배열에서 각 item의 'name' 값을 출력
                        for idx, product in enumerate(products, start=1):
                            if not self.running:  # 실행 상태 확인
                                break

                            current_cnt += 1
                            now_per = divide_and_truncate(current_cnt, total_cnt)
                            self.log_signal.emit(f'{site_name}({current_cnt}/{total_cnt})[{now_per}]  {item}({index}/{len(check_obj_list)})  Page({page}/{total_pages})  Product({idx}/{len(products)})')

                            detail_url = f'{main_url}{product.get("slug")}'
                            images, brand_name, product_name, detail = self.get_detail_data(detail_url)

                            if images:
                                for ix, image_url in enumerate(images, start=1):
                                    if not self.running:  # 실행 상태 확인
                                        break

                                    self.log_signal.emit(f'{site_name}({current_cnt}/{total_cnt})[{now_per}]  {item}({index}/{len(check_obj_list)})  Page({page}/{total_pages})  Product({idx}/{len(products)})  Image({ix}/{len(images)})')
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
                            self.progress_signal.emit(now_per, pro_value)
                            now_per = pro_value

        self.log_signal.emit(f"=============== 처리 데이터 수 : {len(result_list)}")
        self.log_signal.emit("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 프로그램 중단
    def stop(self):
        self.running = False

    # 로그인 쿠키가져오기
    def login(self):
        webdriver_options = webdriver.ChromeOptions()

        # 이 옵션은 Chrome이 자동화 도구(예: Selenium)에 의해 제어되고 있다는 것을 감지하지 않도록 만듭니다.
        # AutomationControlled 기능을 비활성화하여 webdriver가 브라우저를 자동으로 제어하는 것을 숨깁니다.
        # 이는 일부 웹사이트에서 자동화 도구가 감지되는 것을 방지하는 데 유용합니다.
        ###### 자동 제어 감지 방지 #####
        webdriver_options.add_argument('--disable-blink-features=AutomationControlled')

        # Chrome 브라우저를 실행할 때 자동으로 브라우저를 최대화 상태로 시작합니다.
        # 이 옵션은 사용자가 브라우저를 처음 실행할 때 크기가 자동으로 최대로 설정되도록 합니다.
        ##### 화면 최대 #####
        webdriver_options.add_argument("--start-maximized")

        # headless 모드로 Chrome을 실행합니다.
        # 이는 화면을 표시하지 않고 백그라운드에서 브라우저를 실행하게 됩니다.
        # 브라우저 UI 없이 작업을 수행할 때 사용하며, 서버 환경에서 유용합니다.
        ##### 화면이 안보이게 함 #####
        webdriver_options.add_argument("--headless")

        #이 설정은 Chrome의 자동화 기능을 비활성화하는 데 사용됩니다.
        #기본적으로 Chrome은 자동화가 활성화된 경우 브라우저의 콘솔에 경고 메시지를 표시합니다.
        #이 옵션을 설정하면 이러한 경고 메시지가 나타나지 않도록 할 수 있습니다.
        ##### 자동 경고 제거 #####
        webdriver_options.add_experimental_option('useAutomationExtension', False)

        # 이 옵션은 브라우저의 로깅을 비활성화합니다.
        # enable-logging을 제외시키면, Chrome의 로깅 기능이 활성화되지 않아 불필요한 로그 메시지가 출력되지 않도록 할 수 있습니다.
        ##### 로깅 비활성화 #####
        webdriver_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # 이 옵션은 enable-automation 스위치를 제외시킵니다.
        # enable-automation 스위치가 활성화되면,
        # 자동화 도구를 사용 중임을 알리는 메시지가 브라우저에 표시됩니다.
        # 이를 제외하면 자동화 도구의 사용이 감지되지 않습니다.
        ##### 자동화 도구 사용 감지 제거 #####
        webdriver_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.driver = webdriver.Chrome(options=webdriver_options)
        self.driver.set_page_load_timeout(120)
        self.driver.get(self.baseUrl)
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.sess.cookies.set(cookie['name'], cookie['value'])
        self.version = self.driver.capabilities["browserVersion"]
        self.headers = {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.version}"
        }
        self.driver.quit()

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
    def get_detail_data(self, url):

        images = ""
        brand_name = ""
        product_name = ""
        detail = ""

        try:
            response = requests.get(url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # 'product__gallery__carousel' 클래스를 가진 div 안에서 'swiper-slide' 클래스를 가진 div를 찾기
            carousel_div = soup.find('div', class_='product__gallery__carousel') if soup else None

            if not carousel_div:
                self.log_signal.emit("carousel_div not found")
                return []

            swiper_slides = carousel_div.find_all('div', class_='swiper-slide')

            # 'swiper-slide' 안의 img 태그의 src를 배열에 담기
            images = set()  # set을 사용하여 중복 제거
            if swiper_slides:
                for slide in swiper_slides:
                    img_tag = slide.find('img')
                    if img_tag and img_tag.get('src'):  # img 태그가 존재하고 src 속성이 있을 경우
                        images.add(img_tag['src'])  # set에 추가 (중복 자동 제거)

                # 중복 제거된 img_sources 리스트로 변환
                images = list(images)
                images = images[:3]

            product_tag = soup.find('div', class_='product__area__branding__name')
            product_name = product_tag.get_text(strip=True) if product_tag else ''

            brand_tag = soup.find('a', class_='product__area__branding__designer__link')
            brand_name = brand_tag.get_text(strip=True) if brand_tag else ''

            accordion_body_content = soup.find('div', class_='accordion__body__content')

            # ul 안의 li들에서 텍스트를 배열에 담기
            detail = []
            ul_tag = accordion_body_content.find('ul') if accordion_body_content else None
            if ul_tag:
                li_tags = ul_tag.find_all('li')  # li 태그들 찾기
                for li in li_tags:
                    detail.append(li.get_text(strip=True))  # li 안의 텍스트를 가져와서 배열에 담기

        except Exception as e:
            self.log_signal.emit(f"Error : {e}")
        finally:
            return images, brand_name, product_name, detail

    # URL 가져오기
    def get_url_info(self, item):
        global baseUrl
        category = ''
        slug = ''
        main_url = ''

        if item:
            name = item.lower()

            if name == 'men':
                category = 'men'
                slug = '/clothing'
                main_url = f"{baseUrl}/us/en/men"
            elif name == 'women':
                category = 'women'
                slug = '/clothing'
                main_url = f"{baseUrl}/us/en/women"
            elif name == 'boys':
                category = 'kids'
                slug = '/boys/clothing'
                main_url = f"{baseUrl}/us/en/kids"
            elif name == 'girls':
                category = 'kids'
                slug = '/girls/clothing'
                main_url = f"{baseUrl}/us/en/kids"
            elif name == 'baby':
                category = 'kids'
                slug = '/baby/baby-clothing'
                main_url = f"{baseUrl}/us/en/kids"

        return category, slug, main_url

    # 전체 갯수 조회
    def total_cnt_cal(self):
        check_obj_list = []

        for index, checked_obj in enumerate(self.checked_list, start=1):
            name = checked_obj['name']
            start_page = checked_obj['start_page']
            end_page = checked_obj['end_page']

            category, slug, main_url = self.get_url_info(name)
            response_json = self.get_api_request(category, slug, 1)

            total_items_cnt = 0
            total_page = 0
            last_page_cnt = 0

            if isinstance(response_json, dict):
                data = response_json.get('data', {}).get('xProductListingPage', {})
                pagination = data.get('pagination', {})
                total_items_cnt = pagination.get('totalItems')
                total_page = pagination.get('totalPages')
                last_page_cnt = total_items_cnt % 60

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
                    total_items_cnt = ((end_page - start_page) * 60) + last_page_cnt
            if end_page < total_page:
                if start_page >= end_page:
                    start_page = end_page
                    total_items_cnt = 60
                else:
                    total_items_cnt = (end_page - start_page) * 60

            checked_obj['start_page'] = start_page
            checked_obj['end_page'] = end_page
            checked_obj['total_page_cnt'] = total_page
            checked_obj['total_item_cnt'] = total_items_cnt
            checked_obj['item'] = name.lower()
            check_obj_list.append(checked_obj)

        return check_obj_list

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

            # 이미지 이름 변경: URL에서 'media/...' 부분을 'media_'로 변경
            image_name = image_url.split("media/")[-1].replace("/", "_")  # 'media/...'를 'media_...'로 변경

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







