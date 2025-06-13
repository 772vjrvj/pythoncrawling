from collections import defaultdict
from bs4 import BeautifulSoup
import urllib.parse
import time
import pyautogui
import pandas as pd

from selenium.webdriver.common.by import By

from src.core.global_state import GlobalState
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker


class ApiSotongSetLoadWorker(BaseApiWorker):

    def __init__(self, setting):
        super().__init__()
        self.running = True
        self.total_pages = 0
        self.current_page = 0
        self.before_pro_value = 0
        self.login_id = "sotong"
        self.login_pw = "sotong"
        self.fr_date = self.get_setting_value(setting, "fr_date")
        self.to_date = self.get_setting_value(setting, "to_date")
        self.driver = None
        self.file_driver = None
        self.excel_driver = None
        self.selenium_driver = None
        self.login_url = "https://tongclinic.com/bbs/login.php"

    # 초기화
    def init(self):
        try:
            self.driver_set()
            state = GlobalState()
            user = state.get("user")
            self.driver = self.selenium_driver.start_driver(1200, user)
            screen_width, screen_height = pyautogui.size()
            self.driver.set_window_size(screen_width // 2, screen_height)
            self.driver.set_window_position(0, 0)
            return True
        except Exception as e:
            self.log_signal_func(f"초기화 처리중 오류 발생: {e}")
            return False

    # 메인
    def main(self):
        try:

            if not self.fr_date or not self.to_date:
                self.msg_signal_func("날짜를 세팅에서 입력하세요.", "info", None)
                self.stop()
                return False

            login_result = self.login()
            if not login_result:
                return False

            keyword_counter = self.extract_keywords_from_pages()
            if not keyword_counter:
                return False

            visit_data = self.get_visit_data()
            if not visit_data:
                return False

            self.log_signal_func("[키워드별 방문자 수]")
            for keyword, count in visit_data.items():
                self.log_signal_func(f"{keyword} : {count}")

            csv_filename = self.file_driver.get_excel_filename("소통")
            self.save_to_excel(visit_data, keyword_counter, csv_filename)
            return True
        except Exception as e:
            self.log_signal_func(f"메인 처리중 오류 발생: {e}")
        return False

    # 종료
    def destroy(self):
        try:
            self.progress_signal.emit(self.before_pro_value, 1000000)
            self.log_signal_func("크롤링 종료중")
            time.sleep(5)
            self.log_signal_func("크롤링 종료")
            self.progress_end_signal.emit()
        except Exception as e:
            self.log_signal_func(f"종료 처리중 오류 발생: {e}")

    def get_setting_value(self, setting_list, code_name):
        for item in setting_list:
            if item.get("code") == code_name:
                return item.get("value")
        return None

    # 드라이버 세팅
    def driver_set(self):
        self.log_signal_func("드라이버 세팅")
        self.excel_driver = ExcelUtils(self.log_signal_func)
        self.file_driver = FileUtils(self.log_signal_func)
        self.selenium_driver = SeleniumUtils(headless=False)

    # 정지
    def stop(self):
        self.running = False
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.log_signal_func(f"❌ 드라이버 종료 중 오류: {e}")

    # 로그인
    def login(self):
        try:
            self.driver.get(self.login_url)
            time.sleep(2)
            self.log_signal_func("크롤링 사이트 인증에 성공하였습니다.")

            id_input = self.selenium_driver.wait_element(self.driver, By.ID, "login_id", timeout=5)
            if not id_input:
                return False
            id_input.clear()
            id_input.send_keys(self.login_id)
            time.sleep(0.5)

            pw_input = self.selenium_driver.wait_element(self.driver, By.ID, "login_pw", timeout=5)
            if not pw_input:
                return False
            pw_input.clear()
            pw_input.send_keys(self.login_pw)
            time.sleep(0.5)

            login_btn = self.selenium_driver.wait_element(self.driver, By.CSS_SELECTOR, "button.btn_submit", timeout=5)
            if not login_btn:
                return False
            login_btn.click()
            time.sleep(0.5)
            return True

        except Exception as e:
            self.log_signal_func(f"로그인 처리중 오류 발생: {e}")
            return False

    # 키워드
    def extract_keywords_from_pages(self):
        keyword_counter = defaultdict(int)
        page = 1

        try:
            while True:
                url = f"https://tongclinic.com/adm/visit_list.php?fr_date={self.fr_date}&to_date={self.to_date}&page={page}"
                self.driver.get(url)
                soup = BeautifulSoup(self.driver.page_source, "html.parser")

                if page == 1:
                    end_page_link = soup.find("a", class_="pg_page pg_end")
                    if end_page_link:
                        href = end_page_link.get("href")
                        query = urllib.parse.urlparse(href).query
                        page_dict = urllib.parse.parse_qs(query)
                        page_value = page_dict.get("page", [0])[0]
                        self.log_signal_func(f"맨끝 페이지 번호: {page_value}")
                        self.total_pages = int(page_value) + 1
                    else:
                        self.log_signal_func("맨끝 링크가 없습니다.")

                empty_tag = soup.find("td", class_="empty_table")
                if empty_tag and "자료가 없거나" in empty_tag.text:
                    self.log_signal_func(f"페이지 {page} → 데이터 없음 메시지 확인됨. 종료")
                    break

                table_wrap = soup.find("div", class_="tbl_head01 tbl_wrap")
                if not table_wrap:
                    self.log_signal_func(f"페이지 {page} → 테이블 구조 없음. 종료")
                    break

                tbody = table_wrap.find("tbody")
                if not tbody:
                    self.log_signal_func(f"페이지 {page} → tbody 없음. 종료")
                    break

                rows = tbody.find_all("tr")
                if not rows:
                    self.log_signal_func(f"페이지 {page} → tr 구조 없음. 종료")
                    break

                for row in rows:
                    tds = row.find_all("td")
                    if len(tds) < 2:
                        continue
                    a_tag = tds[1].find("a")
                    if a_tag:
                        text_url = a_tag.get_text(strip=True)
                        parsed_url = urllib.parse.urlparse(text_url)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        for key in ['query', 'q']:
                            if key in query_params:
                                for kw in query_params[key]:
                                    keyword = kw.strip()
                                    if keyword:
                                        keyword_counter[keyword] += 1

                self.page_progress()
                page += 1
                time.sleep(1.2)

        except Exception as e:
            self.log_signal_func(f"❌ 키워드 추출 중 오류 발생: {e}")

        return keyword_counter

    def page_progress(self):
        self.current_page += 1
        pro_value = (self.current_page / self.total_pages) * 1000000
        self.progress_signal.emit(self.before_pro_value, pro_value)
        self.before_pro_value = pro_value
        self.log_signal_func(f"현재 페이지 {self.current_page}/{self.total_pages}")

    # 방문자
    def get_visit_data(self):
        visit_data = {}
        try:
            url = f'https://tongclinic.com/adm/visit_domain.php?fr_date={self.fr_date}&to_date={self.to_date}'
            self.driver.get(url)
            time.sleep(2)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            table_wrap = soup.find("div", class_="tbl_head01 tbl_wrap")
            if not table_wrap:
                self.log_signal_func("⚠️ 테이블 구조가 없습니다.")
                return {}

            tbody = table_wrap.find("tbody")
            if not tbody:
                self.log_signal_func("⚠️ tbody가 없습니다.")
                return {}

            rows = tbody.find_all("tr")
            if not rows:
                self.log_signal_func(f"⚠️ tr이 없습니다.")
                return {}

            for row in rows:
                columns = row.find_all("td")
                if len(columns) >= 4:
                    domain = columns[1].get_text(strip=True)
                    count_text = columns[3].get_text(strip=True).replace(",", "")
                    try:
                        count = int(count_text)
                        visit_data[domain] = count
                    except ValueError:
                        self.log_signal_func(f"⚠️ 숫자 변환 실패: '{count_text}'")
                        continue

        except Exception as e:
            self.log_signal_func(f"❌ 방문자 데이터 수집 중 오류: {e}")

        return visit_data

    # 엑셀 저장
    def save_to_excel(self, source_data, keyword_data, filename):
        try:
            df1 = pd.DataFrame([
                {"유입 소스/매체": k, "사용자": v}
                for k, v in sorted(source_data.items(), key=lambda x: x[1], reverse=True)
            ])

            df2 = pd.DataFrame([
                {"키워드": k, "사용자": v}
                for k, v in sorted(keyword_data.items(), key=lambda x: x[1], reverse=True)
            ])

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df1.to_excel(writer, sheet_name="유입소스", index=False)
                df2.to_excel(writer, sheet_name="키워드", index=False)

            self.log_signal_func(f"✅ 엑셀 저장 완료: {filename}")
        except Exception as e:
            self.log_signal_func(f"❌ 엑셀 저장 중 오류: {e}")
