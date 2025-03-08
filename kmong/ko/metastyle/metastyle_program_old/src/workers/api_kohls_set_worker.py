import os
import re
import ssl
import time

import pandas as pd
import psutil
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

from src.utils.time_utils import get_current_yyyymmddhhmmss, get_current_formatted_datetime

ssl._create_default_https_context = ssl._create_unverified_context

image_folder = 'images'
image_main_directory = 'oldnavy_images'
company_name = 'kohls'
site_name = 'KOHLS'
excel_filename = ''
baseUrl = "https://www.kohls.com/"
db_folder = 'DB'
file_path = os.path.join(db_folder, f'{site_name}.csv')

# API
class ApiKohlsSetLoadWorker(QThread):
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

        self.checked_model_list = []
        self.main_model = None
        self.product_info_list = []
        self.csv_product_list = []
        self.product_list = []
        self.total_cnt = 0
        self.total_pages = 0
        self.current_page = 0
        self.current_cnt = 0
        self.before_pro_value = 0

        self.columns = [
            'product_id', 'product_name', 'product_url', 'product_title',
            'product_sub_title', 'product_features', 'product_fabric_care',
            'product_img_1', 'product_img_2', 'product_img_3', 'product_img_4',
            'data_success', 'img_success', 'img_path', 'success', 'error'
        ]


    # 프로그램 실행
    def run(self):
        global image_main_directory, company_name, site_name, excel_filename, baseUrl

        self.log_signal.emit("크롤링 시작")

        self.csv_product_list = self.load_products()

        if self.checked_list:
            self.log_signal.emit("크롤링 사이트 드라이버 세팅중입니다. 잠시만 기다려주세요.")
            self._set_driver()
            self.log_signal.emit("크롤링 사이트 드라이버 세팅에 성공했습니다.")

            self.log_signal.emit(f"전체 상품수 계산을 시작합니다. 잠시만 기다려주세요.")
            check_obj_list = self.total_cnt_cal()
            self.total_cnt = sum(int(obj['total_product_cnt']) for obj in check_obj_list)
            self.total_pages = sum(int(obj['total_page_cnt']) for obj in check_obj_list)

            self.log_signal.emit(f"전체 항목수 {len(check_obj_list)}개")
            self.log_signal.emit(f"전체 상품수 {self.total_cnt} 개")
            self.log_signal.emit(f"전체 페이지수 {self.total_pages} 개")

            for index, checked_model in enumerate(self.checked_list, start=1):
                if not self.running:  # 실행 상태 확인
                    self.log_signal.emit("크롤링이 중지되었습니다.")
                    break

                self.current_cnt = (int(checked_model['start_page']) - 1) * 48
                self.current_page = int(checked_model['start_page'])
                base_url = checked_model['url']

                for indx, page in enumerate(range(int(checked_model['start_page']) - 1, int(checked_model['end_page'])), start=1):
                    if not self.running:
                        break

                    time.sleep(0.5)
                    self.log_signal.emit(f'{checked_model["name"]}({index}/{len(self.checked_list)})  TotalPage({self.current_page}/{self.total_pages})')
                    
                    ws_value = page * 48
                    page_url = f"{base_url}&WS={ws_value}"
                    self.get_products_from_page(page_url, checked_model)

                    self.current_page = self.current_page + 1




        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal.emit("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal.emit("=============== 크롤링 종료")
        self.progress_end_signal.emit()


    # 이미지 다운로드 함수
    def download_images(self, product):
        product_id = product['product_id']
        category_path = os.path.join(image_folder, site_name, product['category_name'].replace("'", "").replace(" ", "").replace("/", "_").strip())
        os.makedirs(category_path, exist_ok=True)

        img_urls = [product['product_img_1'], product['product_img_2'], product['product_img_3'], product['product_img_4']]
        img_paths = []

        for idx, img_url in enumerate(img_urls, start=1):
            if img_url:
                img_filename = f"{product_id}_{idx}.jpg"
                img_filepath = os.path.join(category_path, img_filename)

                try:
                    response = requests.get(img_url, stream=True)
                    if response.status_code == 200:
                        with open(img_filepath, 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                        img_paths.append(img_filepath)
                    else:
                        self.log_signal.emit(f"이미지 다운로드 실패: {img_url}")
                except Exception as e:
                    self.log_signal.emit(f"이미지 다운로드 오류: {e}")

        product['img_path'] = img_paths
        if len(img_paths) == 4:
            product['img_success'] = 'Y'

        return product


    # CSV에 새로운 행 추가하는 함수
    def append_to_csv(self, new_rows):
        df = pd.DataFrame(new_rows, columns=self.columns)  # 명시적으로 컬럼 순서 지정
        if not os.path.exists(file_path):
            df.to_csv(file_path, index=False, mode='w', encoding='utf-8-sig')
        else:
            df.to_csv(file_path, index=False, mode='a', header=False, encoding='utf-8-sig')

    # 프로그램 중단
    def stop(self):
        """스레드 중지를 요청하는 메서드"""
        self.running = False

    # 크롬 끄기
    def _close_chrome_processes(self):
        """모든 Chrome 프로세스를 종료합니다."""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    proc.kill()  # Chrome 프로세스를 종료
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    # 셀레니움 드라이버 세팅
    def _set_driver(self):
        try:
            self._close_chrome_processes()

            chrome_options = Options()
            user_data_dir = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data"
            profile = "Default"

            chrome_options.add_argument(f"user-data-dir={user_data_dir}")
            chrome_options.add_argument(f"profile-directory={profile}")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--start-maximized")
            # chrome_options.add_argument("--headless")  # Headless 모드 추가

            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            chrome_options.add_argument(f'user-agent={user_agent}')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            download_dir = os.path.abspath("downloads")
            os.makedirs(download_dir, exist_ok=True)

            chrome_options.add_experimental_option('prefs', {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            script = '''
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' });
            '''
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})

            self.driver = driver
        except WebDriverException as e:
            print(f"Error setting up the WebDriver: {e}")
            self.driver = None

    # 셀레니움 드라이버 세팅
    def set_driver(self):
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
        # webdriver_options.add_argument("--headless")

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
        self.driver.get(self.baseUrl)

    # 전체 갯수 가져오기
    def get_total_count(self, url):
        self.driver.get(url)
        time.sleep(3)
        count_element = self.driver.find_element(By.CSS_SELECTOR, "span.result_count")
        total_cnt = int(re.sub(r'[^0-9]', '', count_element.text)) if count_element else 0
        return total_cnt

    # 전체 갯수 조회
    def total_cnt_cal(self):
        check_obj_list = []
        for index, checked_obj in enumerate(self.checked_list, start=1):
            name = checked_obj['name']
            url = self.get_url(name)

            total_cnt = self.get_total_count(url)
            total_pages = (total_cnt // 48) + (1 if total_cnt % 48 > 0 else 0)

            checked_obj['url'] = url
            checked_obj['total_page_cnt'] = total_pages
            checked_obj['total_product_cnt'] = total_cnt
            check_obj_list.append(checked_obj)
            time.sleep(0.5)

        self.log_signal.emit(f"check_obj_list : {check_obj_list}")

        return check_obj_list


    def get_product_details(self, product_url):
        self.driver.get(product_url)

        # 페이지 로딩 대기
        time.sleep(3)

        # 현재 페이지의 HTML을 가져와서 BeautifulSoup으로 파싱
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        product_details = {}

        # 🔹 제품명 추출
        product_title_tag = soup.select_one("h1.product-title")
        product_details['product_title'] = product_title_tag.text.strip() if product_title_tag else ""

        # 🔹 서브 제품명 추출
        product_sub_title_tag = soup.select_one("div.sub-product-title a")
        product_details['product_sub_title'] = product_sub_title_tag.text.strip() if product_sub_title_tag else ""

        # 🔹 See More 버튼 클릭 (셀레니움 사용)
        try:
            see_more_button = self.driver.find_element(By.CSS_SELECTOR, ".seemoreParentDiv button")
            self.driver.execute_script("arguments[0].click();", see_more_button)
            time.sleep(2)  # 페이지 갱신 대기 후 다시 BeautifulSoup으로 파싱
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        except Exception as e:
            self.log_signal.emit(f"See More 버튼 클릭 실패: {e}")

        # 🔹 FEATURES 목록 추출
        product_features = []
        features_section = soup.find("p", text="FEATURES")
        if features_section:
            ul = features_section.find_next_sibling("ul")
            if ul:
                product_features = [li.text.strip() for li in ul.find_all("li")]

        if not product_features:
            features_section = soup.find("p", text="PRODUCT FEATURES")
            if features_section:
                ul = features_section.find_next_sibling("ul")
                if ul:
                    product_features = [li.text.strip() for li in ul.find_all("li")]

        product_details['product_features'] = product_features

        # 🔹 FABRIC & CARE 목록 추출
        fabric_care = []
        fabric_care_section = soup.find("p", text="FABRIC & CARE")
        if fabric_care_section:
            ul = fabric_care_section.find_next_sibling("ul")
            if ul:
                fabric_care = [li.text.strip() for li in ul.find_all("li")]

        product_details['product_fabric_care'] = fabric_care

        # 🔹 대표 이미지 (고해상도 srcset에서 첫 번째 이미지 가져오기)
        product_details['product_img_1'] = ""
        product_details['product_img_2'] = ""
        product_details['product_img_3'] = ""
        product_details['product_img_4'] = ""

        main_image = soup.select_one(".pdp-large-hero-image img")
        if main_image:
            srcset = main_image.get("srcset")
            if srcset:
                first_img = srcset.split(",")[0].strip().split(" ")[0]  # 첫 번째 이미지 URL 추출
                product_details['product_img_1'] = first_img
            else:
                product_details['product_img_1'] = main_image.get("src", "")

        # 🔹 추가 이미지 (최대 3개)
        image_elements = soup.select(".pdp-large-alt-images .large-alt-image:not(.video) img")
        for idx, img in enumerate(image_elements[:3]):
            product_details[f'product_img_{idx + 2}'] = img.get("src", "")

        return product_details

    # 상세정보
    def _get_product_details(self, product_url):
        self.driver.get(product_url)

        # 페이지 로딩 대기
        time.sleep(3)

        product_details = {}

        # 🔹 제품명 추출
        try:
            product_details['product_title'] = self.driver.find_element(
                By.CSS_SELECTOR, "h1.product-title"
            ).text.strip()
        except:
            product_details['product_title'] = ""

        # 🔹 서브 제품명 추출
        try:
            product_details['product_sub_title'] = self.driver.find_element(
                By.CSS_SELECTOR, "div.sub-product-title a"
            ).text.strip()
        except:
            product_details['product_sub_title'] = ""

        try:
            see_more_button = self.driver.find_element(By.CSS_SELECTOR, ".seemoreParentDiv button")
            self.driver.execute_script("arguments[0].click();", see_more_button)
            time.sleep(2)  # 페이지가 갱신될 시간을 확보
        except Exception as e:
            self.log_signal.emit(f"See More 버튼 클릭 실패: {e}")

        # 🔹 FEATURES 목록 추출
        try:
            features_section = self.driver.find_element(By.XPATH, "//p[text()='FEATURES']/following-sibling::ul")
            product_details['product_features'] = [li.text.strip() for li in features_section.find_elements(By.TAG_NAME, "li")]
        except:
            product_details['product_features'] = []

        # 🔹 FABRIC & CARE 목록 추출
        try:
            fabric_care_section = self.driver.find_element(By.XPATH, "//p[text()='FABRIC & CARE']/following-sibling::ul")
            product_details['product_fabric_care'] = [li.text.strip() for li in fabric_care_section.find_elements(By.TAG_NAME, "li")]
        except:
            product_details['product_fabric_care'] = []

        # 🔹 대표 이미지 (고해상도 srcset에서 첫 번째 이미지 가져오기)
        try:
            main_image = self.driver.find_element(By.CSS_SELECTOR, ".pdp-large-hero-image img")
            srcset = main_image.get_attribute("srcset")

            if srcset:
                # srcset을 리스트로 변환 후 첫 번째 이미지 선택
                first_img = srcset.split(",")[0].strip().split(" ")[0]  # 첫 번째 이미지의 URL만 추출
                product_details['product_img_1'] = first_img
            else:
                # srcset이 없으면 일반 src 사용
                product_details['product_img_1'] = main_image.get_attribute("src")

        except Exception as e:
            self.log_signal.emit(f"대표 이미지 가져오기 실패: {e}")
            product_details['product_img_1'] = ""

        # 🔹 추가 이미지 (최대 3개)
        product_details['product_img_2'] = ""
        product_details['product_img_3'] = ""
        product_details['product_img_4'] = ""

        try:
            image_elements = self.driver.find_elements(By.CSS_SELECTOR, ".pdp-large-alt-images .large-alt-image:not(.video) img")
            for idx, img in enumerate(image_elements[:3]):
                product_details[f'product_img_{idx + 2}'] = img.get_attribute("src")
        except:
            pass

        return product_details


    def load_products(self):
        if not os.path.exists(file_path):
            self.log_signal.emit(f"파일이 존재하지 않습니다: {file_path}")
            return []

        df = pd.read_csv(file_path, dtype=str)  # 모든 데이터를 문자열로 읽음
        products = []
        for _, row in df.iterrows():
            product = {
                'product_id': row.get('product_id', ''),
                'product_name': row.get('product_name', ''),
                'product_url': row.get('product_url', ''),
                'product_title': row.get('product_title', ''),
                'product_sub_title': row.get('product_sub_title', ''),
                'product_features': row.get('product_features', '').split('|'),  # 리스트 형태로 변환
                'product_fabric_care': row.get('product_fabric_care', '').split('|'),  # 리스트 형태로 변환
                'product_img_1': row.get('product_img_1', ''),
                'product_img_2': row.get('product_img_2', ''),
                'product_img_3': row.get('product_img_3', ''),
                'product_img_4': row.get('product_img_4', ''),
                'data_success': row.get('data_success', 'N'),  # 성공 여부 추가
                'img_success': row.get('img_success', 'N'),  # 성공 여부 추가
                'img_path': row.get('img_path', []),  # 성공 여부 추가
                'success': row.get('success', 'N'),  # 성공 여부 추가
                'error': row.get('error', '')  # 성공 여부 추가
            }
            products.append(product)

        return products


    def skip_products(self, new_product_id):
        for product in self.csv_product_list:
            if product['product_id'] == new_product_id:
                return product['data_success'] == 'Y'
        return False  # 기본적으로 N으로 간주


    def get_products_from_page(self, url, checked_model):
        self.driver.get(url)
        time.sleep(3)  # 페이지가 완전히 로드될 시간을 확보

        # 🔹 페이지 끝까지 스크롤 다운 (Lazy Loading 처리)
        self.scroll_to_bottom()
        time.sleep(2)  # 스크롤 이후 페이지 로딩 대기

        # 🔹 현재 페이지의 HTML을 가져와서 BeautifulSoup으로 파싱
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # 🔹 상품 목록 가져오기
        product_elements = soup.select("#productsContainer > li")

        for product in product_elements:
            self.current_cnt += 1
            try:
                # 🔹 제품 ID 가져오기
                product_id = product.get("data-id")
                product_element_id = product.get("id")

                skip = self.skip_products(product_id)

                if skip or not product_element_id or "scroll_id_" not in product_element_id:
                    continue

                # 🔹 제품명 가져오기
                product_name = product.select_one(".products-container-right .prod_nameBlock p")
                product_name = product_name.text.strip() if product_name else ""

                # 🔹 제품 상세 페이지 URL 가져오기
                product_link_element = product.select_one(".prod_img_block > a")
                product_url = product_link_element["href"] if product_link_element else ""

                if product_url and not product_url.startswith("https://www.kohls.com"):
                    product_url = "https://www.kohls.com" + product_url

                # 🔹 제품 상세 정보 가져오기
                product_details = self.get_product_details(product_url)

                product_data = {
                    "category_name": checked_model['name'],
                    "category_url": checked_model['url'],
                    "product_id": product_id,
                    "product_name": product_name,
                    "product_url": product_url,
                    **product_details
                }

                if all([
                    product_data['product_id'],
                    product_data['product_name'],
                    product_data['product_url'],
                    product_data['product_sub_title'],
                    product_data['product_features'],
                    product_data['product_img_1']
                ]):
                    product_data['data_success'] = 'Y'

                updated_product = self.download_images(product_data)
                self.append_to_csv([updated_product])
                self.log_signal.emit(f'{updated_product}')
                self.product_list.append(product_data)

                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value
                self.log_signal.emit(f'{checked_model["name"]} TotalProduct({self.current_cnt}/{self.total_cnt})')

            except Exception as e:
                self.log_signal.emit(f"Error processing product: {e}")
                continue


    def scroll_to_bottom(self):
        """ 페이지의 끝까지 스크롤하여 모든 제품을 로딩 """
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # 로딩 대기
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break
            last_height = new_height

    # URL 가져오기
    def get_url(self, name):
        url = ""
        if name:
            if name == 'Women / Bottoms / Pants':
                url = "https://www.kohls.com/catalog/womens-pants-bottoms-clothing.jsp?CN=Gender:Womens+Product:Pants+Category:Bottoms+Department:Clothing&cc=wms-TN3.0-S-pants&kls_sbp=05864698454350754950882754362888169186"
            elif name == 'Women / Bottoms / Skirts & Skorts':
                url = "https://www.kohls.com/catalog/womens-skirts-skorts-bottoms-clothing.jsp?CN=Gender:Womens+Product:Skirts%20%26%20Skorts+Category:Bottoms+Department:Clothing&cc=wms-TN3.0-S-skirtsskorts&kls_sbp=05864698454350754950882754362888169186"
            elif name == 'Women / Bottoms / Shorts':
                url = "https://www.kohls.com/catalog/womens-shorts-bottoms-clothing.jsp?CN=Gender:Womens+Product:Shorts+Category:Bottoms+Department:Clothing&kls_sbp=05864698454350754950882754362888169186"
            elif name == 'Women / Dresses & Jumpsuits':
                url = "https://www.kohls.com/catalog/womens-dresses-clothing.jsp?CN=Gender:Womens+Category:Dresses+Department:Clothing&cc=wms-TN2.0-S-dressesjumpsuits&kls_sbp=05864698454350754950882754362888169186"
            elif name == 'Men / Mes’s Tops / Button-Down Shirts':
                url = "https://www.kohls.com/catalog/mens-button-down-shirts-tops-clothing.jsp?CN=Gender:Mens+Silhouette:Button-Down%20Shirts+Category:Tops+Department:Clothing&cc=mens-TN3.0-S-buttondownshirts&kls_sbp=05864698454350754950882754362888169186"
            elif name == 'Men / Mes’s Bottoms / Casual Pants':
                url = "https://www.kohls.com/catalog/mens-casual-pants-bottoms-clothing.jsp?CN=Gender:Mens+Occasion:Casual+Product:Pants+Category:Bottoms+Department:Clothing&cc=mens-TN3.0-S-casualpants&kls_sbp=05864698454350754950882754362888169186"
            elif name == 'Men / Mes’s Bottoms / Shorts':
                url = "https://www.kohls.com/catalog/mens-shorts-bottoms-clothing.jsp?CN=Gender:Mens+Product:Shorts+Category:Bottoms+Department:Clothing&cc=mens-TN3.0-S-shorts&kls_sbp=05864698454350754950882754362888169186"
        return url







    def get_product_info_list(self, checked_model):
        result_list = []

        # CSV 파일 경로 설정
        csv_filename = os.path.join(os.getcwd(), f"{checked_model['name']}_{get_current_yyyymmddhhmmss()}.csv")

        # CSV 파일 초기 생성
        columns = ["name", "product", "product_id" , "product_no", "description", "image_no", "image_url", "image_name", "success", "reg_date", "page", "error"]
        df = pd.DataFrame(columns=columns)
        df.to_csv(csv_filename, index=False)

        for index, product in enumerate(self.product_info_list):

            if not product:  # product가 None인지 확인
                print(f"경고: index {index}의 product가 None입니다. 건너뜁니다.")
                continue

            time.sleep(1)
            obj = self.get_api_product_info(product.get('pid'), product.get('cid'))

            if obj:

                product['product'] = obj.get('product')
                product['description'] = obj.get('description')
                product['img_list'] = obj.get('img_list')
                product['product_id'] = product.get('pid')
                product['product_no'] = index + 1

                # images 폴더 생성
                images_dir = os.path.join(os.getcwd(), 'images')
                os.makedirs(images_dir, exist_ok=True)

                for ix, image_url in enumerate(product.get('img_list'), start=1):
                    if not self.running:
                        break

                    obj_copy = product.copy()  # 객체 복사
                    obj_copy['name'] = checked_model['name']
                    obj_copy['image_no'] = ix + 1
                    obj_copy['image_url'] = image_url
                    obj_copy['success'] = 'N'
                    obj_copy['image_yn'] = 'N'
                    obj_copy['reg_date'] = get_current_formatted_datetime()  # 시간 추가

                    try:
                        # 이미지 다운로드
                        # response = requests.get(image_url, stream=True)
                        # response.raise_for_status()

                        # 이미지 저장 경로
                        img_filename = f"{product.get('pid')}_{ix}.jpg"
                        # img_path = os.path.join(images_dir, img_filename)

                        # 이미지 저장
                        # with open(img_path, 'wb') as file:
                            # for chunk in response.iter_content(1024):
                                # file.write(chunk)

                        # obj_copy['success'] = 'Y'  # 성공하면 Y
                        obj_copy['image_name'] = img_filename
                        self.log_signal.emit(f"성공 {obj_copy}")
                    except Exception as e:
                        print(f"이미지 다운로드 실패: {image_url}, 오류: {e}")
                        obj_copy['success'] = 'N'  # 실패하면 N 유지
                        obj_copy['error'] = e

                    result_list.append(obj_copy)

                self.current_cnt = self.current_cnt + 1
                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

                self.log_signal.emit(f'{checked_model["name"]} TotalPage({self.current_page}/{self.total_pages})  TotalProduct({self.current_cnt}/{self.total_cnt}) Product({index+1}/{len(self.product_info_list)})')

                # 5개마다 CSV에 저장
                if index % 5 == 0 and index > 0:
                    df = pd.DataFrame(result_list, columns=columns)
                    df.to_csv(csv_filename, mode='a', header=False, index=False)
                    result_list.clear()  # 저장 후 리스트 초기화

        # 남은 데이터 저장
        if result_list:
            df = pd.DataFrame(result_list, columns=columns)
            df.to_csv(csv_filename, mode='a', header=False, index=False)





