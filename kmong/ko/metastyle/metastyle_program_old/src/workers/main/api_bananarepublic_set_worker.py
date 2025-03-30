import time

from PyQt5.QtCore import QThread, pyqtSignal
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By

from src.utils.config import SITE_CONFIGS
from src.utils.utils_excel_appender import CsvAppender
from src.utils.utils_file import FilePathBuilder
from src.utils.utils_google_cloud_upload import GoogleUploader
from src.utils.utils_selenium import SeleniumDriverManager
from src.utils.utils_time import get_current_formatted_datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# API
class ApiBananarepublicSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)         # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널

    # 초기화
    def __init__(self, checked_list):
        super().__init__()
        self.name = "BANANAREPUBLIC"
        self.sess = None
        self.checked_list = checked_list
        self.running = True  # 실행 상태 플래그 추가
        self.driver = None
        self.base_url = ""
        self.brand_type = ""
        self.country = ""
        self.product_list = []
        self.blob_product_ids = []
        self.before_pro_value = 0
        self.csv_appender = None
        self.google_uploader = None
        self.driver_manager = None
        self.seen_keys = set()


        # 프로그램 실행

    # 실행
    def run(self):
        if self.checked_list:
            self.log_func("크롤링 시작")
            self.log_func(f"checked_list : {self.checked_list}")

            self.driver_manager = SeleniumDriverManager(headless=True)

            # 2. 원하는 URL로 드라이버 실행
            config = SITE_CONFIGS.get(self.name)
            self.base_url = config.get("base_url")
            self.brand_type = config.get("brand_type")
            self.country = config.get("country")

            self.driver = self.driver_manager.start_driver(self.base_url, 1200, None)
            self.sess = self.driver_manager.get_session()

            self.google_uploader = GoogleUploader(self.log_func, self.sess)

            for index, check_obj in enumerate(self.checked_list, start=1):
                if not self.running:  # 실행 상태 확인
                    self.log_func("크롤링이 중지되었습니다.")
                    break

                name = check_obj['name']

                obj = {
                    "website": self.name,
                    "category_full": name
                }
                # self.google_uploader.delete(obj)
                self.blob_product_ids = self.google_uploader.verify_upload(obj)
                # self.google_uploader.download_all_in_folder(obj)

                site_url = config.get('check_list', {}).get(name, "")
                main_url = f"{config.get("base_url")}{site_url}"
                self.driver.get(main_url)

                csv_path = FilePathBuilder.build_csv_path("DB", self.name, name)
                self.csv_appender = CsvAppender(csv_path, self.log_func)

                self.selenium_get_product_list(main_url)
                self.selenium_get_product_detail_list(name)

            self.progress_signal.emit(self.before_pro_value, 1000000)
            self.log_func("=============== 크롤링 종료중...")
            time.sleep(5)
            self.log_func("=============== 크롤링 종료")
            self.progress_end_signal.emit()
        else:
            self.log_func("선택된 항목이 없습니다.")

    # 로그
    def log_func(self, msg):
        self.log_signal.emit(msg)

    # 프로그램 중단
    def stop(self):
        self.running = False

    # 셀레니움 초기 버튼 클릭
    def selenium_init_button_click(self):
        try:
            # SVG 아이콘이 나타날 때까지 대기 (최대 10초)
            svg_icon = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'svg[data-testid="large-grid-icon"]'))
            )

            # 클릭 가능한 상태인지 확인 후 클릭
            svg_icon.click()
        except Exception as e:
            self.log_func(f"3 버튼 클릭 실패")


    # 제품 목록 가져오기
    def selenium_get_product_list(self, product_url):
        page = 0
        while True:
            if page == 0:
                url = f'{product_url}#pageId={page}' #은 spa방식이라 get(url)로 이동 안됌
                self.driver.get(url)
            else:
                try:
                    # 스크롤 많이 했을 수 있으니 다시 버튼 위치로 스크롤 조정
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Next Page"]'))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)  # 가운데로 가져오기
                    WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Next Page"]')))
                    time.sleep(0.3)
                    next_button.click()
                    self.log_func("다음 페이지 버튼 클릭 성공")
                except TimeoutException:
                    self.log_func("다음 페이지 버튼을 찾을 수 없습니다. 마지막 페이지일 수 있습니다.")
                    break
                except Exception as e:
                    self.log_func(f"다음 페이지 버튼 클릭 중 예외 발생: {str(e)}")
                    break

            time.sleep(2)
            self.selenium_init_button_click()
            time.sleep(1)
            self.driver_manager.selenium_scroll_smooth(0.5, 200, 6)
            time.sleep(2)
            # 1. UL 태그 찾기 class="cat_product-image sitewide-15ltmfs"
            try:
                # 최대 10초 동안 div 요소들이 로드되기를 기다림
                div_elements = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.cat_product-image'))
                )
            except TimeoutException:
                self.log_func("ul 태그를 찾을 수 없습니다. 종료합니다.")
                break  # 상품이 없으면 종료

            if not div_elements:
                self.log_func("ul 태그를 찾을 수 없습니다. 종료합니다.")
                break  # 상품이 없으면 종료

            for div in div_elements:
                try:
                    full_id = div.get_attribute("id")
                    product_id = ""
                    if full_id and full_id.startswith("product"):
                        product_id = full_id[len("product"):]

                    a_tag = div.find_element(By.TAG_NAME, "a")
                    url = a_tag.get_attribute("href")

                    key = (product_id, url)
                    if not product_id or not url or key in self.seen_keys:
                        continue  # 중복이면 건너뜀

                    self.product_list.append({
                        "product_id": product_id,
                        "url": url
                    })
                    self.seen_keys.add(key)

                except NoSuchElementException:
                    self.log_func("li안에 태그를 찾을 수 없습니다. 다음 상품으로 넘어갑니다.")

            page += 1  # 다음 페이지로 이동
        self.log_func('상품목록 수집완료...')

    # 상세목록
    def selenium_get_product_detail_list(self, name):

        # 상세 정보 저장 리스트
        product_details = []

        # 기존 csv 파일에서 기존 데이터 로드
        loaded_objs = self.csv_appender.load_rows()

        success_uploaded_ids = set()
        fail_uploaded_ids = set()

        for obj in loaded_objs:
            pid = str(obj["product_id"])
            result = obj.get("success")
            if result == "Y":
                success_uploaded_ids.add(pid)
            elif result == "N":
                fail_uploaded_ids.add(pid)

        for no, product in enumerate(self.product_list, start=1):
            if not self.running:  # 실행 상태 확인
                self.log_func("크롤링이 중지되었습니다.")
                break
            error = ""
            url = product["url"]
            product_id = product["product_id"]
            csv_type = "추가" # 추가는 I, 덮어 쓰기는 U

            # 버킷에 이미 업로드된 항목이면 스킵
            if product_id in self.blob_product_ids:
                self.log_func(f"[SKIP] 버킷에 이미 성공적으로 처리된 product_id: {product_id}")
                continue

            # ✅ csv에 이미 업로드된 항목이면 스킵
            if product_id in success_uploaded_ids:
                self.log_func(f"[SKIP] csv파일에 이미 성공적으로 처리된 product_id: {product_id}")
                continue

            # ✅ csv에 이미 업로드된 항목이면 스킵
            if product_id in fail_uploaded_ids:
                self.log_func(f"실패로 처리됐으므로 update필요 product_id: {product_id}")
                csv_type = "수정"

            self.driver.get(url)
            time.sleep(2)  # 페이지 로딩 대기

            # 첫번째 이미지 가져오기
            try:
                div = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="grid"]')
                img = div.find_element(By.TAG_NAME, 'img')
                img_src = img.get_attribute('src')
            except NoSuchElementException as e:
                img_src = ""
                error = f'이미지 src 추출 실패 : {e}'

            # 제품명
            try:
                h1 = self.driver.find_element(By.TAG_NAME, 'h1')
                product_name = h1.text.strip()
            except NoSuchElementException as e:
                error = f'제품명 추출 실패 : {e}'
                product_name = ""

            # 가격
            try:
                # 1. div.amount-price 요소 찾기
                div = self.driver.find_element(By.CSS_SELECTOR, 'div.amount-price')
                # 2. 그 안에 있는 span 요소 찾기
                span = div.find_element(By.TAG_NAME, 'span')
                # 3. 텍스트 가져오기
                price = span.text.strip()  # 예: "$120.00"
            except NoSuchElementException as e:
                error = f'가격 추출 실패 : {e}'
                price = ""

            # 설명
            content = ""

            categories = name.split(" _ ")

            obj = {
                "website": self.name,
                "brand_type": self.brand_type,
                "category": categories[0],
                "category_sub": categories[1],
                "url": self.base_url,
                "category_full": name,
                "country": self.country,
                "brand": self.name,
                "product_url": url,
                "product": product_name,
                "product_id": product_id,
                "product_no": no,
                "description": content,
                "price": price,
                "image_no": '1',
                "image_url": img_src,
                "image_name": f'{product_id}_1.jpg',
                "success": "Y",
                "reg_date": get_current_formatted_datetime(),
                "page": "",
                "error": error,
                "image_yn": "Y",
                "image_path": "",
                "project_id": "",
                "bucket": ""
            }

            self.google_uploader.upload(obj)
            self.csv_appender.append_row(obj)

            if obj['error']:
                obj['success'] = "N"

            self.log_func(f"product_id({csv_type}) => {product_id}({no}) : {obj}")
            product_details.append(obj)

            pro_value = (no / len(self.product_list)) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value
            self.log_func(f'{name} : TotalProduct({no}/{len(self.product_list)})')