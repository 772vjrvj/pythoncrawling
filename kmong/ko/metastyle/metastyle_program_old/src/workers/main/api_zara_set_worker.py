import time

from PyQt5.QtCore import QThread, pyqtSignal
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.utils.config import SITE_CONFIGS
from src.utils.utils_excel_appender import CsvAppender
from src.utils.utils_file import FilePathBuilder
from src.utils.utils_google_cloud_upload import GoogleUploader
from src.utils.utils_selenium import SeleniumDriverManager
from src.utils.utils_time import get_current_formatted_datetime


# API
class ApiZaraSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)         # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널

    # 초기화
    def __init__(self, checked_list):
        super().__init__()
        self.name = "ZARA"
        self.sess = None
        self.checked_list = checked_list
        self.running = True  # 실행 상태 플래그 추가
        self.driver = None
        self.base_url = ""
        self.brand_type = ""
        self.country = ""
        self.product_list = []
        self.before_pro_value = 0
        self.csv_appender = None
        self.google_uploader = None

        # 프로그램 실행
    def run(self):
        self.log("크롤링 시작")
        self.log(f"checked_list : {self.checked_list}")

        driver_manager = SeleniumDriverManager(headless=True)

        # 2. 원하는 URL로 드라이버 실행
        config = SITE_CONFIGS.get(self.name)
        self.base_url = config.get("base_url")
        self.brand_type = config.get("brand_type")
        self.country = config.get("country")

        self.driver = driver_manager.start_driver(self.base_url)
        self.sess = driver_manager.get_session()
        self.log("드라이버 실행 완료")

        self.google_uploader = GoogleUploader(self.log)

        filename = self.checked_list[0]["name"] if self.checked_list else "default"
        csv_path = FilePathBuilder.build_csv_path("DB", self.name, filename)
        self.csv_appender = CsvAppender(csv_path)

        if self.checked_list:
            for index, check_obj in enumerate(self.checked_list, start=1):
                if not self.running:  # 실행 상태 확인
                    self.log("크롤링이 중지되었습니다.")
                    break

                name = check_obj['name']
                site_url = config.get('check_list', {}).get(name, "")
                self.driver.get(f"{config.get("base_url")}{site_url}")

                if index == 1:
                    csv_path = FilePathBuilder.build_csv_path("DB", self.name, name)
                    self.csv_appender = CsvAppender(csv_path)
                else:
                    self.csv_appender.set_file_path(name)

                time.sleep(3)
                self.selenium_init_button_click()
                self.selenium_scroll()
                self.selenium_get_product_list()
                self.selenium_get_product_detail_list(name)

        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 로그
    def log(self, msg):
        self.log_signal.emit(msg)

    # 프로그램 중단
    def stop(self):
        self.running = False

    # 셀레니움 초기 버튼 클릭
    def selenium_init_button_click(self):
        # 쿠키 수락 버튼 클릭
        try:
            accept_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            accept_button.click()
            time.sleep(1)
            self.log("쿠키 수락 버튼 클릭 완료")
        except Exception as e:
            self.log(f"쿠키 수락 버튼 클릭 중 오류 발생: {e}", )

        # 국가 유지 버튼 클릭
        try:

            stay_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-qa-action='stay-in-store']"))
            )
            stay_button.click()
            time.sleep(1)
            self.log("국가 유지 버튼 클릭 완료")
        except Exception as e:
            self.log(f"국가 유지 버튼 클릭 중 오류 발생: {e}", )

        # "3" 버튼 클릭
        try:
            button = self.driver.find_element(By.CSS_SELECTOR, "span.view-option-selector-button__option")
            if button.text.strip() == "3":
                button.click()
            ActionChains(self.driver).move_to_element(button).click().perform()
            time.sleep(2)
        except Exception as e:
            self.log(f"3 버튼 클릭 실패: {e}")

    # 스크롤 내리기 (데이터가 늘어날 때까지)
    def selenium_scroll(self):

        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)  # 페이지 끝까지 스크롤
            time.sleep(2)  # 로딩 대기

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:  # 새로운 데이터가 없으면 종료
                break
            last_height = new_height

    # 제품 목록 가져오기
    def selenium_get_product_list(self):

        product_list = self.driver.find_elements(By.CSS_SELECTOR, "li.product-grid-product")
        # 결과 저장 리스트

        for product in product_list:
            try:
                # 1. info-wrapper가 없으면 건너뛰기
                try:
                    info_wrapper = product.find_element(By.CSS_SELECTOR, "div.product-grid-product__data > div.product-grid-product__info-wrapper")
                except NoSuchElementException:
                    continue

                # 2. "LOOK"인 경우 건너뛰기
                try:
                    name_tag = info_wrapper.find_element(By.CSS_SELECTOR, "a.product-grid-product-info__name")
                    product_name = name_tag.text.strip()
                    if product_name == "LOOK":
                        continue
                except NoSuchElementException:
                    continue

                # 3. 링크 및 상품 ID 수집
                try:
                    link_tag = product.find_element(By.CSS_SELECTOR, "div.product-grid-product__figure a.product-grid-product__link")
                    href = link_tag.get_attribute("href")
                    product_id = product.get_attribute("data-productid")
                    if href and product_id:
                        self.product_list.append({
                            "url": href,
                            "product_id": product_id
                        })
                except NoSuchElementException:
                    continue

            except Exception as e:
                self.log(f"상품 처리 중 오류 발생: {e}")

    # 상세목록
    def selenium_get_product_detail_list(self, name):

        # 상세 정보 저장 리스트
        product_details = []

        # 기존 csv 파일에서 기존 데이터 로드
        loaded_objs = self.csv_appender.load_rows()
        uploaded_ids = {obj["product_id"] for obj in loaded_objs if obj.get("success") == "Y"}


        for no, product in enumerate(self.product_list, start=1):
            error = ""
            url = product["url"]
            product_id = product["product_id"]

            # ✅ 이미 업로드된 항목이면 스킵
            if product_id in uploaded_ids:
                self.log(f"[SKIP] 이미 성공적으로 처리된 product_id: {product_id}")
                continue

            self.driver.get(url)
            time.sleep(2)  # 페이지 로딩 대기

            # 1. 지역 선택 버튼 클릭 (있다면)
            try:
                stay_btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa-action='stay-in-store']"))
                )
                stay_btn.click()
                self.log("지역 선택 버튼 클릭")
                time.sleep(1)
            except Exception as e:
                error = f"국가 유지 버튼 클릭 중 오류 발생: {e}"
                self.log(error)

            # 2. product-detail-view__main-content 영역
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-detail-view__main-content"))
            )

            # 이미지 src 추출
            try:
                img_tag = self.driver.find_element(By.CSS_SELECTOR,
                                              "div.product-detail-view__main-content button.product-detail-image img")
                img_src = img_tag.get_attribute("src")
            except NoSuchElementException as e:
                error = e
                img_src = None

            # 제품명
            try:
                product_name = self.driver.find_element(By.CSS_SELECTOR,
                                           "div.product-detail-view__main-info .product-detail-info__header-name").text.strip()
            except NoSuchElementException as e:
                error = e
                product_name = ""

            # 가격
            try:
                price = self.driver.find_element(By.CSS_SELECTOR,
                                            "div.product-detail-view__main-info .money-amount__main").text.strip()
            except NoSuchElementException as e:
                error = e
                price = ""

            # 설명
            try:
                content = self.driver.find_element(By.CSS_SELECTOR,
                                              "div.product-detail-view__main-info .expandable-text__inner-content").text.strip()
            except NoSuchElementException as e:
                error = e
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
                "product": product_name,
                "product_id": product_id,
                "product_no": no,
                "description": content,
                "price": price,
                "image_no": '1',
                "image_url": img_src,
                "image_name": f'{product_id}_1',
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

            if obj['error']:
                obj['success'] = "N"

            self.csv_appender.append_row(obj)

            self.log(f"no : {no}, product_id : {product_id} : {obj}")
            product_details.append(obj)

            pro_value = (no / len(self.product_list)) * 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.before_pro_value = pro_value
            self.log(f'{name} : TotalProduct({no}/{len(self.product_list)})')