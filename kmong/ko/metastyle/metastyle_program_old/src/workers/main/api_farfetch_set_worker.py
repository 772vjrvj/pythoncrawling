import time

from PyQt5.QtCore import QThread, pyqtSignal
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from src.utils.config import SITE_CONFIGS
from src.utils.utils_excel_appender import CsvAppender
from src.utils.utils_file import FilePathBuilder
from src.utils.utils_google_cloud_upload import GoogleUploader
from src.utils.utils_selenium import SeleniumDriverManager
from src.utils.utils_time import get_current_formatted_datetime

import re


# API
class ApiFarfetchSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)         # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널

    # 초기화
    def __init__(self, checked_list):
        super().__init__()
        self.name = "FARFETCH"
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
        self.seen_keys = set()

        # 프로그램 실행

    # 실행
    def run(self):
        if self.checked_list:
            self.log_func("크롤링 시작")
            self.log_func(f"checked_list : {self.checked_list}")
            self.driver_manager = SeleniumDriverManager(headless=True)
            config = SITE_CONFIGS.get(self.name)
            self.base_url = config.get("base_url")
            self.brand_type = config.get("brand_type")
            self.country = config.get("country")

            self.driver = self.driver_manager.start_driver(self.base_url, 1200, True)
            self.sess = self.driver_manager.get_session()
            self.google_uploader = GoogleUploader(self.log_func, self.sess)

            # farfetch 추가 시작 ======
            self.refresh_if_429()
            self.click_close_button()
            self.selenium_set_region()
            # farfetch 추가 종료 ======

            for index, check_obj in enumerate(self.checked_list, start=1):
                if not self.running:
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
                csv_path = FilePathBuilder.build_csv_path("DB", self.name, name)
                if index == 1:
                    self.csv_appender = CsvAppender(csv_path, self.log_func)
                else:
                    self.csv_appender.set_file_path(csv_path)
                site_url = config.get('check_list', {}).get(name, "")
                main_url = f"{config.get("base_url")}{site_url}"

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


    def click_close_button(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="btnClose"]')))
            close_btn.click()
            self.log_func("✅ 닫기 버튼 클릭 완료")
        except Exception as e:
            self.log_func(f"❌ 닫기 버튼 없음")


    def refresh_if_429(self):
        wait_time = 5  # 초기 대기 시간 (초)
        max_wait = 60  # 최대 대기 시간 제한 (원하는 만큼 조절 가능)

        while True:
            try:
                h1 = self.driver.find_element(By.TAG_NAME, "h1")
                if "429 Too Many Requests" in h1.text:
                    self.log_func(f"⏳ 429 감지됨. {wait_time}초 대기 후 새로고침합니다.")
                    time.sleep(wait_time)
                    self.driver.refresh()
                    wait_time = min(wait_time + 1, max_wait)  # 1초씩 증가, 최대 max_wait
                else:
                    self.log_func("✅ 429 메시지 없음. 정상 접속됨.")
                    break
            except Exception:
                self.log_func(f"❌ h1 태그가 없음")
                break  # 예외 발생 시 루프 종료 (필요 시 continue로 바꿀 수 있음)


    def selenium_set_region(self):

        wait = WebDriverWait(self.driver, 10)

        try:
            # 1. flash-notification 버튼 클릭
            flash_btn = wait.until(EC.element_to_be_clickable((By.ID, "flash-notification")))
            flash_btn.click()
            time.sleep(1)  # 1초 대기

            # 2. TabList에서 두 번째 버튼 (Region) 클릭
            tab_list = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-component="TabList"]')))
            tabs = tab_list.find_elements(By.TAG_NAME, "button")
            if len(tabs) >= 2:
                tabs[1].click()
            else:
                self.log_func("Tab 버튼이 2개 미만입니다.")
                return

            # 3. PopperContainer 안의 input에 'us' 입력
            search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-component="PopperContainer"] input[data-component="SearchInputControlled"]')))
            search_input.clear()
            search_input.send_keys("us")

            # 4. 'United States' 버튼 클릭
            us_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="btn-region-us"]')))
            us_button.click()
            time.sleep(2)

            self.log_func("✅ 지역이 United States로 변경되었습니다.")

        except Exception as e:
            self.log_func(f"❌ 지역 화면 없음", )

    # 제품 목록 가져오기
    def selenium_get_product_list(self, product_url):
        page = 1
        while True:
            if product_url.endswith("items.aspx"):
                url = f'{product_url}?page={page}'
            else:
                url = f'{product_url}&page={page}'
            self.driver.get(url)
            time.sleep(3)  # 페이지 로딩 대기
            self.refresh_if_429()
            self.driver_manager.selenium_scroll_smooth(0.5, 200, 6)
            time.sleep(3)
            try:
                product_list = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//li[@data-testid='productCard']"))
                )
            except TimeoutException:
                self.log_func("🔴 상품을 찾을 수 없습니다. 종료합니다.")
                break  # 상품이 없으면 종료
            time.sleep(3)
            for product in product_list:
                try:
                    a_tag = product.find_element(By.TAG_NAME, "a")
                    if a_tag:
                        href = a_tag.get_attribute("href")
                        if href:
                            if not href.startswith(self.base_url):
                                href = self.base_url + href

                            # 정규식을 사용하여 product_id 추출 (숫자만 찾기)
                            product_id_match = re.search(r"item-(\d+)", href)
                            product_id = product_id_match.group(1) if product_id_match else ""

                            key = (product_id, href)
                            if not product_id or not href or key in self.seen_keys:
                                continue  # 중복이면 건너뜀

                            self.product_list.append({
                                "product_id": product_id,
                                "url": href
                            })
                            self.seen_keys.add(key)

                except (NoSuchElementException, TimeoutException):
                    self.log_func("⚠️ a 태그를 찾을 수 없습니다. 다음 상품으로 넘어갑니다.")
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
            self.refresh_if_429()
            time.sleep(2)  # 페이지 로딩 대기

            # 첫번째 이미지 가져오기
            try:
                image_containers = self.driver.find_elements(By.CSS_SELECTOR, '.ltr-bjn8wh.ed0fyxo0')
                if len(image_containers) >= 2:
                    img = image_containers[1].find_element(By.TAG_NAME, 'img')
                    img_src = img.get_attribute('src')
                else:
                    img_src = None

            except NoSuchElementException as e:
                img_src = ""
                error = f'이미지 src 추출 실패 : {e}'
            except Exception:
                self.log_func(f"이미지 src 추출 실패")
                content = ""

            # 제품명
            try:
                product_name = self.driver.find_element(By.CSS_SELECTOR, '.ltr-13ze6d5-Body.efhm1m90').text.strip()
            except NoSuchElementException as e:
                error = f'제품명 추출 실패 : {e}'
                product_name = ""
            except Exception:
                self.log_func(f"제품명 없음")
                content = ""

            # 가격
            try:
                price = self.driver.find_element(By.CSS_SELECTOR, '.ltr-s7112i-Heading.ehhcbme0').text.strip()
            except NoSuchElementException as e:
                error = f'가격 추출 실패 : {e}'
                price = ""
            except Exception:
                self.log_func(f"가격 없음")
                content = ""

            # 설명
            try:
                desc_block = self.driver.find_element(By.CSS_SELECTOR, 'div.ltr-fzg9du.e1yiqd0 ul._fdc1e5')
                desc_items = desc_block.find_elements(By.TAG_NAME, 'li')
                content = [li.text.strip() for li in desc_items]
            except NoSuchElementException:
                content = ""
            except Exception:
                self.log_func(f"설명 없음")
                content = ""

            # brand
            try:
                brand = self.driver.find_element(By.CSS_SELECTOR, '.ltr-183yg4m-Body-Heading-HeadingBold.e1h8dali1').text.strip()
            except NoSuchElementException:
                brand = ""
            except Exception:
                self.log_func(f"brand 없음")
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
                "brand": brand,
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