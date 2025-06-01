import ssl
import threading
import time
from random import random
from urllib.parse import urlparse, parse_qs, unquote

import pandas as pd
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.workers.api_base_worker import BaseApiWorker

ssl._create_default_https_context = ssl._create_unverified_context

image_main_directory = 'albamon_images'
company_name = '알바몬'
site_name = 'albamon'

excel_filename = ''


class ApiCoupangSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self):
        super().__init__()
        self.channel = None
        self.query = None
        self.component = None
        self.base_login_url = "https://login.coupang.com/login/login.pang"
        self.base_main_url   = "https://www.coupang.com"

        self.excludeKeywords = ""
        self.includeKeyword = ""

        self.running = True  # 실행 상태 플래그 추가
        self.driver = None

        self.com_list = []
        self.main_model = None
        self.product_info_list = []

        self.total_cnt = 0
        self.total_pages = 0
        self.current_page = 0
        self.current_cnt = 0
        self.before_pro_value = 0


    def init(self):
        # 현재 모니터 해상도 가져오기
        screen_width, screen_height = pyautogui.size()

        # 창 크기를 너비 절반, 높이 전체로 설정
        self.driver.set_window_size(screen_width // 2, screen_height)

        # 창 위치를 왼쪽 상단에 배치
        self.driver.set_window_position(0, 0)

        # 로그인 열기
        self.driver.get(self.base_login_url)


    # 프로그램 실행
    def main(self):
        result_list = []
        self.wait_for_user_confirmation()
        self.wait_for_select_confirmation()

        self.log_func("크롤링 사이트 인증에 성공하였습니다.")
        self.log_func(f"전체 회사수 계산을 시작합니다. 잠시만 기다려주세요.")
        self.log_func(f"전체 회사수 알수없음")
        self.log_func(f"전체 페이지수 알수없음")

        csv_filename = self.file_driver.get_csv_filename("쿠팡")

        columns = ["상호명", "연락처", "주소", "키워드"]

        df = pd.DataFrame(columns=columns)
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")

        page = 1

        # 키워드에 매핑되는 아이디 수집
        while True:
            if not self.running:  # 실행 상태 확인
                self.log_func("크롤링이 중지되었습니다.")
                break

            urls = self.fetch_product_urls(page)

            if not urls:
                break

            page = page + 1

            for index, url in enumerate(urls, start=1):

                if not self.running:  # 실행 상태 확인
                    self.log_func("크롤링이 중지되었습니다.")
                    break

                obj = self.fetch_product_detail(url)
                result_list.append(obj)

                time.sleep(1)

                if index % 5 == 0:
                    self.excel_driver.append_to_csv(csv_filename, result_list, columns)

            if result_list:
                self.excel_driver.append_to_csv(csv_filename, result_list, columns)


    def wait_for_user_confirmation(self):
        self.log_func("크롤링 사이트 인증을 시도중입니다. 잠시만 기다려주세요.")

        event = threading.Event()  # OK 버튼 누를 때까지 대기할 이벤트 객체

        # 사용자에게 메시지 창 요청
        self.msg_signal.emit("로그인 후  후 OK를 눌러주세요", "info", event)

        # 사용자가 OK를 누를 때까지 대기
        self.log_func("📢 사용자 입력 대기 중...")
        event.wait()  # 사용자가 OK를 누르면 해제됨

        # 쿠키 설정
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.sess.cookies.set(cookie['name'], cookie['value'])

        # 사용자가 OK를 눌렀을 경우 실행
        self.log_func("✅ 사용자가 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")

        self.driver.get(self.base_main_url)

        time.sleep(2)  # 예제용


    
    def wait_for_select_confirmation(self):
        """사용자가 쿠팡에서 키워드 검색 후 OK 누를 때까지 대기"""
        event = threading.Event()  # OK 버튼 누를 때까지 대기할 이벤트 객체
    
        # 사용자에게 메시지 창 요청
        self.msg_signal.emit("쿠팡 검색 후 OK를 눌러주세요 (검색 결과 화면 확인 후)", "info", event)
    
        self.log_func("📢 사용자 입력 대기 중...")
        event.wait()  # 사용자가 OK를 누르면 해제됨
    
        self.log_func("✅ 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")
    
        # 현재 URL 파싱
        current_url = self.driver.current_url
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)
    
        # 필요한 파라미터 추출
        component = query_params.get("component", [""])[0]
        q = query_params.get("q", [""])[0]
        channel = query_params.get("channel", [""])[0]
    
        self.component = unquote(component)
        self.query = unquote(q)
        self.channel = unquote(channel)
    
        self.log_func(f"🔍 검색어: {self.query}")
    
        time.sleep(2)
        self.log_func("🚀 작업 완료!")



    def fetch_product_detail(self, url):
        seller_info = {
            "상호명": "",
            "사업장소재지": "",
            "연락처": "",
            "키워드": self.query
        }

        print(f"🧭 상품 상세 진입: {url}")
        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))

            # 판매자 정보 테이블 영역 대기
            seller_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-item__table product-seller"))
            )

            table = seller_div.find_element(By.CLASS_NAME, "prod-delivery-return-policy-table")
            rows = table.find_elements(By.TAG_NAME, "tr")

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                headers = row.find_elements(By.TAG_NAME, "th")

                for i, th in enumerate(headers):
                    label = th.text.strip()
                    value = cells[i].text.strip() if i < len(cells) else ""

                    if "상호/대표자" in label:
                        seller_info["상호명"] = value
                    elif "사업장 소재지" in label:
                        seller_info["사업장소재지"] = value
                    elif "연락처" in label:
                        seller_info["연락처"] = value
                    # elif "e-mail" in label.lower():
                    #     seller_info["이메일"] = value
                    # elif "통신판매업" in label:
                    #     seller_info["통신판매번호"] = value
                    # elif "사업자번호" in label:
                    #     seller_info["사업자번호"] = value
        except Exception as e:
            print(f"❌ 판매자 정보 추출 오류: {e}")
        return seller_info


    def fetch_product_urls(self, page):
        url = f"https://www.coupang.com/np/search?component=&q={self.query}&page={page}&listSize=72"
        print(f"🔍 상품 URL 조회: {url}")
        try:
            self.driver.get(url)
            time.sleep(2)

            # 페이지네이션 유효성 검사
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'Pagination_pagination')]"))
            )
            pagination_div = self.driver.find_element(By.XPATH, "//div[contains(@class, 'Pagination_pagination')]")
            page_links = pagination_div.find_elements(By.TAG_NAME, "a")

            page_numbers = []
            for link in page_links:
                text = link.text.strip()
                if text.isdigit():
                    page_numbers.append(int(text))

            print(f"📄 페이징 숫자 목록: {page_numbers}")

            if int(page) not in page_numbers:
                print(f"⛔ 현재 페이지 {page}는 존재하지 않음. 종료.")
                return []

            # 상품 URL 추출
            product_list = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "product-list"))
            )
            products = product_list.find_elements(By.XPATH, ".//li[contains(@class, 'ProductUnit_productUnit')]")

            print(f"✅ 상품 개수: {len(products)}")

            urls = set()
            for product in products:
                try:
                    a_tag = product.find_element(By.TAG_NAME, "a")
                    href = a_tag.get_attribute("href")
                    if href:
                        if not href.startswith("https://www.coupang.com"):
                            href = "https://www.coupang.com" + href
                        urls.add(href)
                except Exception:
                    continue

            return list(urls)

        except Exception as e:
            print(f"❌ 상품 URL 조회 중 오류 발생: {e}")
            return []
