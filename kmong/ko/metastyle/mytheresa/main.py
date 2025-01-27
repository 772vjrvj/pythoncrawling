import mimetypes
import ssl
import sys
import time
from io import BytesIO
import os

import requests
from bs4 import BeautifulSoup
from google.cloud import storage
from google.oauth2 import service_account

from selenium import webdriver
from datetime import datetime
import pandas as pd
from openpyxl import load_workbook

image_main_directory = 'metastyle_images'
company_name = 'metastyle'
excel_filename = ''

# 는 현재 디렉토리를 모듈 검색 경로에 추가하여, 현재 디렉토리 내의 파일을 모듈로 임포트할 수 있게 합니다.
sys.path.append("./")

# 인증서 검증을 하지 않도록 설정할 수 있습니다. 이로 인해 서버의 SSL 인증서가 유효하지 않거나 신뢰되지 않더라도 연결을 허용합니다.
ssl._create_default_https_context = ssl._create_unverified_context

class Mytheresa:
    def __init__(self, url):
        self.baseUrl = url
        self.sess = requests.Session()

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
        webdriver_options.add_argument("headless")

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


def main():
    global excel_filename

    site_name = 'mytheresa'
    category = 'women'
    page = 1

    url = "https://www.mytheresa.com"
    sub_url = f'/us/en/{category}'
    main_url = f"{url}{sub_url}?page={page}"

    mytheresa = Mytheresa(url)
    mytheresa.login()

    current_time = get_current_datetime_2()
    excel_filename = f"{company_name}_{current_time}.xlsx"


    # 1 페이지인 경우 get방식


    # res = mytheresa.sess.get(main_url, headers=mytheresa.headers)

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
            "slug": "/clothing",
            "sort": None
        },
        "query": "query XProductListingPageQuery($categories: [String], $colors: [String], $designers: [String], $fta: Boolean, $page: Int, $patterns: [String], $reductionRange: [String], $saleStatus: SaleStatusEnum, $size: Int, $sizesHarmonized: [String], $slug: String, $sort: String) {\n  xProductListingPage(categories: $categories, colors: $colors, designers: $designers, fta: $fta, page: $page, patterns: $patterns, reductionRange: $reductionRange, saleStatus: $saleStatus, size: $size, sizesHarmonized: $sizesHarmonized, slug: $slug, sort: $sort) {\n    id\n    alternateUrls {\n      language\n      store\n      url\n      __typename\n    }\n    breadcrumb {\n      id\n      name\n      slug\n      __typename\n    }\n    combinedDepartmentGroupAndCategoryErpID\n    department\n    designerErpId\n    displayName\n    facets {\n      categories {\n        name\n        options {\n          id\n          name\n          slug\n          children {\n            id\n            name\n            slug\n            children {\n              id\n              name\n              slug\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        activeValue\n        __typename\n      }\n      designers {\n        name\n        options {\n          value\n          slug\n          __typename\n        }\n        activeValue\n        __typename\n      }\n      colors {\n        name\n        options {\n          value\n          __typename\n        }\n        activeValue\n        __typename\n      }\n      fta {\n        activeValue\n        name\n        options {\n          value\n          __typename\n        }\n        visibility\n        __typename\n      }\n      patterns {\n        name\n        options {\n          value\n          __typename\n        }\n        activeValue\n        __typename\n      }\n      reductionRange {\n        activeValue\n        name\n        options {\n          value\n          __typename\n        }\n        unit\n        visibility\n        __typename\n      }\n      saleStatus {\n        activeValue\n        name\n        options {\n          value\n          __typename\n        }\n        visibility\n        __typename\n      }\n      sizesHarmonized {\n        name\n        options {\n          value\n          __typename\n        }\n        activeValue\n        __typename\n      }\n      __typename\n    }\n    isMonetisationExcluded\n    isSalePage\n    pagination {\n      ...paginationData\n      __typename\n    }\n    products {\n      ...productData\n      __typename\n    }\n    sort {\n      currentParam\n      params\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment paginationData on XPagination {\n  currentPage\n  itemsPerPage\n  totalItems\n  totalPages\n  __typename\n}\n\nfragment priceData on XSharedPrice {\n  currencyCode\n  currencySymbol\n  discount\n  discountEur\n  extraDiscount\n  finalDuties\n  hint\n  includesVAT\n  isPriceModifiedByRegionalRules\n  original\n  originalDuties\n  originalDutiesEur\n  originalEur\n  percentage\n  regionalRulesModifications {\n    priceColor\n    __typename\n  }\n  regular\n  vatPercentage\n  __typename\n}\n\nfragment productData on XSharedProduct {\n  color\n  combinedCategoryErpID\n  combinedCategoryName\n  department\n  description\n  designer\n  designerErpId\n  designerInfo {\n    designerId\n    displayName\n    slug\n    __typename\n  }\n  displayImages\n  enabled\n  features\n  fta\n  hasMultipleSizes\n  hasSizeChart\n  hasStock\n  isComingSoon\n  isInWishlist\n  isPurchasable\n  isSizeRelevant\n  labelObjects {\n    id\n    label\n    __typename\n  }\n  labels\n  mainPrice\n  mainWaregroup\n  name\n  price {\n    ...priceData\n    __typename\n  }\n  priceDescription\n  promotionLabels {\n    label\n    type\n    __typename\n  }\n  seasonCode\n  sellerOrigin\n  sets\n  sizeAndFit\n  sizesOnStock\n  sizeTag\n  sizeType\n  sku\n  slug\n  variants {\n    allVariants {\n      availability {\n        hasStock\n        lastStockQuantityHint\n        __typename\n      }\n      isInWishlist\n      size\n      sizeHarmonized\n      sku\n      __typename\n    }\n    availability {\n      hasStock\n      lastStockQuantityHint\n      __typename\n    }\n    isInWishlist\n    price {\n      currencyCode\n      currencySymbol\n      discount\n      discountEur\n      extraDiscount\n      includesVAT\n      isPriceModifiedByRegionalRules\n      original\n      originalEur\n      percentage\n      regionalRulesModifications {\n        priceColor\n        __typename\n      }\n      vatPercentage\n      __typename\n    }\n    size\n    sizeHarmonized\n    sku\n    __typename\n  }\n  __typename\n}\n"
    }

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

    main_url_api = "https://api.mytheresa.com/api"

    # post 방식
    res = mytheresa.sess.post(main_url_api, headers=headers, json=payload)

    result_list = []

    # 응답이 정상적인지 확인
    if res.status_code == 200:
        response_json = res.json()  # JSON 응답 파싱

        # 'products' 배열이 'data' -> 'xProductListingPage' 안에 있으므로 접근
        products = response_json.get('data', {}).get('xProductListingPage', {}).get('products', [])

        # products 배열에서 각 item의 'name' 값을 출력
        for index, product in enumerate(products, start=0):

            if index == 1:
                break
            detail_url = f'{url}{sub_url}{product.get('slug')}'
            images, product_name, detail = get_detail_data(detail_url)

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

                # 이미지 다운로드
                download_image(image_url, site_name, category, product_name, obj)

                # 구글 업로드
                # google_cloud_upload(site_name, category, product_name, image_url)

                result_list.append(obj)

                save_to_excel_one_by_one([obj], excel_filename)  # 엑셀 파일 경로를 지정

                time.sleep(1)

    else:
        print(f"Request failed with status code {res.status_code}")


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


def get_current_datetime_1():
    # 현재 날짜와 시간 가져오기
    now = datetime.now()

    # 날짜와 시간을 'yyyy.mm.dd hh:mm:ss' 형식으로 포맷팅
    formatted_datetime = now.strftime("%Y.%m.%d %H:%M:%S")

    return formatted_datetime


def get_current_datetime_2():
    # 현재 날짜와 시간 가져오기
    now = datetime.now()

    # 날짜와 시간을 'yyyymmddhhmmss' 형식으로 포맷팅
    formatted_datetime = now.strftime("%Y%m%d%H%M%S")

    return formatted_datetime


# 구글 클라우드 업로드
def google_cloud_upload(site_name, category, product_name, image_url):
    # GCP 설정
    project_id = "vue2-study"  # 새 프로젝트 ID
    bucket_name = "772vjrvj"  # 새 버킷 이름"
    service_account_path = "D:/GitHub/pythoncrawling/vue2-study-0d4d51baa885.json"  # 서비스 계정 키 파일 경로 설정

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
    blob_name = f"{site_name}/{category}/{product_name}/{image_name}"

    # 이미지의 MIME 타입을 자동으로 감지
    mime_type, _ = mimetypes.guess_type(image_url)
    if not mime_type:
        mime_type = "application/octet-stream"  # MIME 타입을 감지할 수 없는 경우 기본값 설정

    # Cloud Storage에 이미지 업로드
    blob = bucket.blob(blob_name)
    blob.upload_from_file(image_data, content_type=mime_type)

    print(f"Image from {image_url} has been uploaded to {bucket_name}/{blob_name}.")

    # 해당 경로에 있는 모든 이미지 목록 출력 (site_name/category/product_name/ 경로)
    blobs = bucket.list_blobs(prefix=f"{site_name}/{category}/{product_name}/")  # 경로 내의 모든 파일 나열
    print(f"Images in {site_name}/{category}/{product_name} directory:")
    for blob in blobs:
        print(f"- {blob.name}")


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


def get_detail_data(url):

    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    # 'product__gallery__carousel' 클래스를 가진 div 안에서 'swiper-slide' 클래스를 가진 div를 찾기
    carousel_div = soup.find('div', class_='product__gallery__carousel')
    swiper_slides = carousel_div.find_all('div', class_='swiper-slide')

    # 'swiper-slide' 안의 img 태그의 src를 배열에 담기
    images = set()  # set을 사용하여 중복 제거
    for slide in swiper_slides:
        img_tag = slide.find('img')
        if img_tag and img_tag.get('src'):  # img 태그가 존재하고 src 속성이 있을 경우
            images.add(img_tag['src'])  # set에 추가 (중복 자동 제거)

    # 중복 제거된 img_sources 리스트로 변환
    images = list(images)
    images = images[:3]

    product_name = soup.find('div', class_='product__area__branding__name').get_text(strip=True)

    # 'accordion__body__content' 클래스 중 첫 번째 div 찾기
    accordion_body_content = soup.find('div', class_='accordion__body__content')

    # ul 안의 li들에서 텍스트를 배열에 담기
    detail = []
    if accordion_body_content:
        ul_tag = accordion_body_content.find('ul')  # ul 태그 찾기
        if ul_tag:
            li_tags = ul_tag.find_all('li')  # li 태그들 찾기
            for li in li_tags:
                detail.append(li.get_text(strip=True))  # li 안의 텍스트를 가져와서 배열에 담기

    return images, product_name, detail


if __name__ == '__main__':
    main()

