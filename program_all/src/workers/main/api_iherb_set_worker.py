import re
import time
import random

import pyautogui
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.core.global_state import GlobalState
from src.workers.api_base_worker import BaseApiWorker
from datetime import datetime

class ApiIherbSetLoadWorker(BaseApiWorker):


    # 초기화
    def __init__(self):
        super().__init__()
        self.blog_id = None
        self.setting = None
        self.cookies = None
        self.keyword = None
        self.base_main_url = "https://kr.iherb.com/pr"
        self.sub_url = "https://kr.iherb.com/pr/doctor-s-best-alpha-lipoic-acid-150-150-mg-120-veggie-caps"
        self.site_name = "iherb"

        self.running = True  # 실행 상태 플래그 추가
        self.driver = None

        self.total_cnt = 0
        self.total_pages = 0
        self.current_cnt = 0

        self.file_driver = None
        self.selenium_driver = None
        self.excel_driver = None
        self.running = True
        self.driver = None
        self.before_pro_value = 0

    # 초기화
    def init(self):

        self.log_signal_func("크롤링 시작 ========================================")

        self.driver_set(False)

        # 현재 모니터 해상도 가져오기
        screen_width, screen_height = pyautogui.size()

        # 창 크기를 너비 절반, 높이 전체로 설정
        self.driver.set_window_size(screen_width, screen_height)

        # 창 위치를 왼쪽 상단에 배치
        self.driver.set_window_position(0, 0)

        # 로그인 열기
        self.driver.get(self.base_main_url)

        return True

    # 국가 통화 설정
    def selected_country(self):
        wait = WebDriverWait(self.driver, 10)

        # 1. 설정 버튼 클릭
        button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "selected-country-wrapper")))
        button.click()

        # 2. 팝업 등장 대기
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "selection-list-wrapper")))

        # 3. 각 텍스트 항목을 클릭 없이 선택만 처리
        texts = ["일본", "한국어", "USD ($)", "미터법(kg, cm)"]

        for idx, text in enumerate(texts):
            # 3️⃣ 4개의 input 중 순서에 따라 선택
            inputs = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "input.search-input.gh-dropdown-search.gh-fake-input")
            ))
            if idx >= len(inputs):
                self.log_signal_func(f"⚠️ 입력 박스 부족: idx={idx}, inputs={len(inputs)}")
                break

            inp = inputs[idx]
            inp.click()
            inp.clear()
            inp.send_keys(text)
            inp.send_keys(Keys.ENTER)
            self.log_signal_func(f"✅ '{text}' 선택 입력 및 엔터 완료")
            time.sleep(1.5)  # UI 반응 대기


    # 4. 저장 버튼 클릭
        save_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.save-selection.gh-btn.gh-btn-primary")))
        save_button.click()

    # 프로그램 실행
    def main(self):
        try:
            self.selected_country()
            time.sleep(3)

            st_page = int(self.get_setting_value(self.setting, "st_page"))-1
            ed_page = int(self.get_setting_value(self.setting, "ed_page"))-1

            self.log_signal_func(f"st_page : {st_page}")
            self.log_signal_func(f"st_page : {ed_page}")

            numbers = self.file_driver.read_numbers_from_file("numbers.txt")
            numbers = numbers[st_page:ed_page + 1]

            self.log_signal_func(f"numbers : {numbers}")

            self.total_cnt = len(numbers)
            self.log_signal_func(f"전체 수 {self.total_cnt} 개")

            excel_filename = self.file_driver.get_excel_filename(self.site_name)
            columns = ["품번", "할인기간", "할인 %", "가격", "재고"]

            df = pd.DataFrame(columns=columns)
            df.to_excel(excel_filename, index=False)
            result_list = []
            for index, num in enumerate(numbers):
                if not self.running:  # 실행 상태 확인
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break

                obj = self.data_set(num)
                result_list.append(obj)

                if (index + 1) % 5 == 0:
                    self.excel_driver.append_to_excel(excel_filename, result_list, columns)

                time.sleep(random.uniform(1, 1.5))

                self.current_cnt = self.current_cnt + 1
                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

            if result_list:
                self.excel_driver.append_to_excel(excel_filename, result_list, columns)

            return True
        except Exception as e:
            self.log_signal_func(f"🚨 예외 발생: {e}")
            return False

    # data_set_selenium
    def data_set(self, num):
        sub_url = f"{self.sub_url}/{num}"
        self.driver.get(sub_url)

        obj = {}

        # ✅ 1. 품번은 index 기준으로 부여
        obj['품번'] = num
        obj['할인기간'] = "해당없음"
        obj['할인 %'] = "해당없음"

        try:
            title_text = ""
            expiration_date_span_text = ""

            # 할인 제목
            try:
                title_div = self.driver.find_element(By.CSS_SELECTOR, "div.discount-title")
                title_text = title_div.text.strip()
            except:
                pass

            try:
                expiration_date_span = self.driver.find_element(By.CSS_SELECTOR, "span.expiration-date")
                expiration_date_span_text = expiration_date_span.text.strip()
            except:
                pass

            full_text = f"{title_text} {expiration_date_span_text}"

            # 할인기간 추출
            if "슈퍼 세일" in full_text:
                obj['할인기간'] = "SS"
            else:
                # 날짜 형식 감지 및 변환
                date_match = re.search(
                    r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*(오전|오후)\s*(\d{1,2})시(?:에)?",
                    full_text
                )

                if date_match:
                    year, month, day, am_pm, hour = date_match.groups()
                    hour = int(hour)
                    if am_pm == "오후" and hour != 12:
                        hour += 12
                    elif am_pm == "오전" and hour == 12:
                        hour = 0

                    # 날짜 객체 생성
                    dt = datetime(int(year), int(month), int(day), hour)
                    obj['할인기간'] = dt.strftime('%Y-%m-%d')
                else:
                    obj['할인기간'] = "해당없음"

            # 할인 % 추출
            percent_match = re.search(r"(\d+%)", full_text)
            if percent_match:
                obj['할인 %'] = percent_match.group(1)
            else:
                obj['할인 %'] = "해당없음"

        except:
            pass

        # ✅ 4. 가격: 현재 페이지에서 가격 태그가 필요한데, 예시가 없으므로 임시 처리
        try:
            obj['가격'] = "해당없음"  # 기본값

            # 1차 시도: span.list-price 목록에서 첫 번째 유효한 텍스트
            price_els = self.driver.find_elements(By.CSS_SELECTOR, "span.list-price")
            for el in price_els:
                text = el.text.strip()
                if text:
                    obj['가격'] = text
                    break

            # 2차 시도: div.price-inner-text > p (for문 없이 단일 처리)
            if obj['가격'] == "해당없음":
                fallback_el = self.driver.find_element(By.CSS_SELECTOR, "div.price-inner-text > p")
                text = fallback_el.text.strip()
                if text:
                    obj['가격'] = text

        except:
            pass

        # ✅ "해당 국가 판매 제외 상품"이 있는 경우 가격 무효 처리
        try:
            prohibited = self.driver.find_element(By.CSS_SELECTOR, "span.title.title-prohibited")
            if "판매 제외" in prohibited.text:
                obj['가격'] = "해당없음"
        except:
            pass


        # ✅ 5. 재고: <strong class="text-primary">
        try:
            stock_el = self.driver.find_element(By.CSS_SELECTOR, "strong.text-primary")
            obj['재고'] = stock_el.text.strip()
        except:
            obj['재고'] = "해당없음"

        self.log_signal_func(f"📦 수집 결과: {obj}")

        return obj

    # data_set_bs
    def data_set_bs(self, num):
        url = f"{self.sub_url}/{num}"
        self.driver.get(url)

        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        obj = {"품번": num}

        full_text = ''
        title_div = soup.select_one("div.discount-title")
        cart_span = soup.select_one("span.discount-cart")

        if title_div:
            full_text += title_div.get_text(strip=True)
        if cart_span:
            full_text += ' ' + cart_span.get_text(strip=True)

        if "슈퍼 세일" in full_text:
            obj['할인기간'] = "SS"
        else:
            date_match = re.search(r"\d{4} 년 \d{2} 월 \d{2} 일 [오전|오후] \d{1,2}시", full_text)
            obj['할인기간'] = date_match.group(0) if date_match else "해당없음"

        percent_match = re.search(r"(\d+%)", full_text)
        obj['할인 %'] = percent_match.group(1) if percent_match else "해당없음"

        for el in soup.select("span.list-price"):
            price = el.get_text(strip=True)
            if price:
                obj['가격'] = price
                break
        else:
            obj['가격'] = "해당없음"

        stock = soup.select_one("strong.text-primary")
        obj['재고'] = stock.get_text(strip=True) if stock else "해당없음"

        self.log_signal_func(f"📦 수집 결과: {obj}")
        return obj

    # 드라이버 세팅
    def driver_set(self, headless):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 파일 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # 셀레니움 초기화
        self.selenium_driver = SeleniumUtils(headless)

        self.driver = self.selenium_driver.start_driver(1200)

    # 마무리
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 중지
    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()
