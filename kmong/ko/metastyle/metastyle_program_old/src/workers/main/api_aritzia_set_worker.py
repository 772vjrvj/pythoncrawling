import time

from PyQt5.QtCore import QThread, pyqtSignal
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from src.utils.config import SITE_CONFIGS
from src.utils.utils_excel_appender import CsvAppender
from src.utils.utils_file import FilePathBuilder
from src.utils.utils_google_cloud_upload import GoogleUploader
from src.utils.utils_selenium import SeleniumDriverManager
from src.utils.utils_time import get_current_formatted_datetime


# API
class ApiAritziaSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)         # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널

    # 초기화
    def __init__(self, checked_list):
        super().__init__()
        self.name = "ARITZIA"
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

        # 프로그램 실행

    # 실행
    def run(self):
        if self.checked_list:
            self.log_func("크롤링 시작")
            self.log_func(f"checked_list : {self.checked_list}")

            driver_manager = SeleniumDriverManager(headless=True)

            # 2. 원하는 URL로 드라이버 실행
            config = SITE_CONFIGS.get(self.name)
            self.base_url = config.get("base_url")
            self.brand_type = config.get("brand_type")
            self.country = config.get("country")

            self.driver = driver_manager.start_driver(self.base_url, 1200, None)
            self.sess = driver_manager.get_session()

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
                self.driver.get(f"{config.get("base_url")}{site_url}")

                csv_path = FilePathBuilder.build_csv_path("DB", self.name, name)
                self.csv_appender = CsvAppender(csv_path, self.log_func)

                time.sleep(3)
                self.selenium_init_button_click()
                driver_manager.selenium_scroll_smooth(0.1, 100, 3)
                # 💡 스크롤 완료 후 렌더링 대기 (a 태그 같은 요소가 로딩될 시간)
                time.sleep(5)
                self.selenium_get_product_list()
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
        # 쿠키 수락 버튼 클릭
        # "3" 버튼 클릭
        try:
            # Sticky_viewItem__7OMDF 클래스를 가진 요소 찾기 (3개 중 3번째 요소 클릭)
            view_items = self.driver.find_elements(By.CLASS_NAME, "Sticky_viewItem__7OMDF")
            if len(view_items) >= 3:
                view_items[2].click()
                time.sleep(3)

        except Exception as e:
            self.log_func(f"3 버튼 클릭 실패: {e}")


    # 제품 목록 가져오기
    def selenium_get_product_list(self):
        self.log_func('상품목록 수집시작... 1분 이상 소요 됩니다. 잠시만 기다려주세요')
        product_list = self.driver.find_elements(By.CLASS_NAME, "div._13qupa29")
        self.log_func(f'추출 목록 수: {len(product_list)}')
        for product in product_list:
            try:
                product_id = product.get_attribute("data-mpid")
                # 안전한 방식
                a_tag = product.find_element(By.TAG_NAME, "a")
                if a_tag:
                    href = a_tag.get_attribute("href")
                    if not href.startswith("http"):
                        href = self.base_url + href

                    if href:
                        self.product_list.append({
                            "url": href,
                            "product_id": str(product_id)
                        })
                else:
                    self.log_func(f"[경고] a 태그 없음 - product_id: {product_id}")

            except Exception as e:
                self.log_func(f"상품 처리 중 오류 발생: {e}")

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
                img_tag = self.driver.find_element(By.TAG_NAME, "img")
                img_src = img_tag.get_attribute('src')
                if not img_src:
                    img_src = ""
                    error = "이미지 srcset 속성이 비어있습니다."

            except NoSuchElementException as e:
                img_src = ""
                error = f'이미지 src 추출 실패 : {e}'

            # 제품명 class=""
            try:
                name_element = self.driver.find_element(By.CLASS_NAME, "h1.s1b82p51s.s1b82p52g.s1b82p53g.s1b82p52s.s1b82p54o.s1b82p591.s1b82p55g.s1b82p1a4.s1b82p56k.d1hqjy0.d1hqjy3")
                product_name = name_element.text.strip()
            except NoSuchElementException as e:
                error = f'제품명 추출 실패 : {e}'
                product_name = ""

            # 가격
            price = ""
            try:
                element  = self.driver.find_element(By.CSS_SELECTOR, "p.s1b82p51s.s1b82p52g.s1b82p53g.s1b82p52s.s1b82p54o.s1b82p57t.s1b82p55g.d1hqjy0.d1hqjy3")
                if element:
                    price = element.text.strip()
            except NoSuchElementException as e:
                error = f'가격 추출 실패 : {e}'
                price = ""

            # 설명
            try:
                description_element = self.driver.find_element(By.CSS_SELECTOR, "div.s1b82p51s.s1b82p52g.s1b82p53g.s1b82p52s.s1b82p54o.s1b82p591.s1b82p55g.d1hqjy0.d1hqjy2")
                paragraphs = description_element.find_elements(By.TAG_NAME, "p")
                content = paragraphs.text.strip()
            except NoSuchElementException:
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