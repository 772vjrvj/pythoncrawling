import re
import math
import time
import threading
import random

import pyautogui
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.core.global_state import GlobalState
from src.workers.api_base_worker import BaseApiWorker


class ApiAlbaSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self):
        super().__init__()
        self.schExcludeText = ""
        self.schIncludeText = ""
        self.base_detail_url   = "https://www.alba.co.kr/job/Main"
        self.base_main_url   = "https://www.alba.co.kr/"

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

        self.file_driver = None
        self.selenium_driver = None
        self.excel_driver = None
        self.sess = None
        self.base_url = None
        self.api_client = APIClient(use_cache=False)


    # 초기화
    def init(self):

        self.driver_set()

        # 현재 모니터 해상도 가져오기
        screen_width, screen_height = pyautogui.size()

        # 창 크기를 너비 절반, 높이 전체로 설정
        self.driver.set_window_size(screen_width // 2, screen_height)

        # 창 위치를 왼쪽 상단에 배치
        self.driver.set_window_position(0, 0)

        # 로그인 열기
        self.driver.get(self.base_main_url)


    # 프로그램 실행
    def main(self):
        result_list = []
        time.sleep(1)
        try:
            login_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".header-link__item.login.member"))
            )
            self.driver.execute_script("arguments[0].click();", login_button)
            self.log_signal_func("✅ JS로 로그인 버튼 클릭 성공")
        except Exception as e:
            self.log_signal_func(f"❌ JS 클릭 실패: {e}")

        self.wait_for_user_confirmation()
        self.wait_for_select_confirmation()

        self.log_signal_func("크롤링 사이트 인증에 성공하였습니다.")
        self.log_signal_func(f"전체 회사수 계산을 시작합니다. 잠시만 기다려주세요.")
        self.total_cnt_cal()
        self.log_signal_func(f"전체 회사수 {self.total_cnt} 개")
        self.log_signal_func(f"전체 페이지수 {self.total_pages} 개")

        csv_filename = self.file_driver.get_csv_filename("알바천국")

        columns = ["NO", "사업체명", "채용담당자명", "휴대폰 번호","포함 키워드", "제외 키워드"]

        df = pd.DataFrame(columns=columns)
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")

        for page in range(1, self.total_pages + 1):
            self.log_signal_func(f"현재 페이지 {page}")
            time.sleep(1)
            if not self.running:  # 실행 상태 확인
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            collection = self.main_request(page)

            for index, recruit_no in enumerate(collection):

                if not self.running:  # 실행 상태 확인
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break

                obj = self.get_api_request(recruit_no)

                self.log_signal_func(f"현재 데이터 :  {obj}")
                time.sleep(1)
                result_list.append(obj)

                if (index + 1) % 5 == 0:
                    self.excel_driver.append_to_csv(csv_filename, result_list, columns)

                self.current_cnt = self.current_cnt + 1

                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

                self.log_signal_func(f"현재 페이지 {self.current_cnt}/{self.total_cnt}")

                time.sleep(random.uniform(2, 3))

            if result_list:
                self.excel_driver.append_to_csv(csv_filename, result_list, columns)

    # 종료
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 드라이버 객체 세팅
    def driver_set(self):
        self.log_signal_func("드라이버 세팅 ========================================")

        # 엑셀 객체 초기화
        self.excel_driver = ExcelUtils(self.log_signal_func)

        # 엑셀 객체 초기화
        self.file_driver = FileUtils(self.log_signal_func)

        # 셀레니움 초기화
        self.selenium_driver = SeleniumUtils(headless=False)

        state = GlobalState()
        user = state.get("user")
        self.driver = self.selenium_driver.start_driver(1200, user)


    def wait_for_user_confirmation(self):
        self.log_signal_func("크롤링 사이트 인증을 시도중입니다. 잠시만 기다려주세요.")

        event = threading.Event()  # OK 버튼 누를 때까지 대기할 이벤트 객체

        # 사용자에게 메시지 창 요청
        self.msg_signal.emit("로그인 후  후 OK를 눌러주세요", "info", event)

        # 사용자가 OK를 누를 때까지 대기
        self.log_signal_func("📢 사용자 입력 대기 중...")
        event.wait()  # 사용자가 OK를 누르면 해제됨

        # 쿠키 설정
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.api_client.cookie_set(cookie['name'], cookie['value'])

        # 사용자가 OK를 눌렀을 경우 실행
        self.log_signal_func("✅ 사용자가 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")

        self.driver.get(self.base_detail_url)

        time.sleep(2)  # 예제용

        self.log_signal_func("🚀 작업 완료!")


    def wait_for_select_confirmation(self):
        """사용자가 확인(alert) 창에서 OK를 누를 때까지 대기"""
        event = threading.Event()  # OK 버튼 누를 때까지 대기할 이벤트 객체

        # 사용자에게 메시지 창 요청
        self.msg_signal.emit("키워드(포함/제외) 추가 후 검색을 눌러주세요(아래 목록이 나오는걸 확인하세요)", "info", event)

        # 사용자가 OK를 누를 때까지 대기
        self.log_signal_func("📢 사용자 입력 대기 중...")
        event.wait()  # 사용자가 OK를 누르면 해제됨

        current_url = self.driver.current_url
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)

        # 사용자가 OK를 눌렀을 경우 실행
        self.log_signal_func("✅ 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")
        # ✅ 쿼리 파라미터 추출
        self.schIncludeText = unquote(query_params.get("schIncludeText", [""])[0])
        self.schExcludeText = unquote(query_params.get("schExcludeText", [""])[0])

        # ✅ 로그 출력
        self.log_signal_func(f"🔍 포함 키워드: {self.schIncludeText}")
        self.log_signal_func(f"🔍 제외 키워드: {self.schExcludeText}")

        time.sleep(2)
        self.log_signal_func("🚀 작업 완료!")


    def main_request(self, page=1, req_type=None):
        """현재 브라우저 URL을 기반으로 API 요청"""
        url = "https://www.alba.co.kr/job/main"

        params = {
            "page": page,
            "pagesize": "50",
            "hidlistview": "LIST",
            "hidsortcnt": "50",
            "hidsortfilter": "Y",
            "hidsearchyn": "Y",
            "schIncludeText": self.schIncludeText,
            "schExcludeText": self.schExcludeText
        }

        headers = {
            "authority": "www.alba.co.kr",
            "method": "GET",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko,en;q=0.9,en-US;q=0.8",
            "sec-ch-ua": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "sec-gpc": "1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
        }


        total_cnt = 0
        total_pages = 0
        imid_list = []

        try:
            res = self.api_client.get(url=url, headers=headers, params=params)

            if not res:
                return total_cnt, total_pages, imid_list

            self.log_signal_func("✅ 요청 성공")
            soup = BeautifulSoup(res, 'html.parser')

            # 1페이지일 경우 숫자도 추출
            strong_tag = soup.find('strong', class_='point-color1')
            if strong_tag:
                total_cnt_text = strong_tag.get_text(strip=True)
                total_cnt = int(re.sub(r'[^\d]', '', total_cnt_text))
                total_pages = math.ceil(total_cnt / 50)

            # 항상 imid_list도 추출
            tbody = soup.find('tbody', class_='observe-job')
            if tbody:
                rows = tbody.find_all('tr')
                for tr in rows:
                    imid = tr.get('data-imid')
                    if imid:
                        imid_list.append(imid)
            else:
                self.log_signal_func("⚠️ <tbody class='observe-job'>를 찾을 수 없습니다.")
        except Exception as e:
            self.log_signal_func(f"🚨 예외 발생: {e}")
        finally:
            if req_type == 'c':
                return total_cnt, total_pages, imid_list
            else:
                return imid_list

    # 페이지 데이터 가져오기
    def get_api_request(self, recruit_no):
        url = f"https://www.alba.co.kr/job/Detail?adid={recruit_no}&listmenucd=ENTIRE"

        headers = {
            "authority": "www.alba.co.kr",
            "method": "GET",
            "path": "/job/main",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko,en;q=0.9,en-US;q=0.8",
            "sec-ch-ua": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "sec-gpc": "1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
        }
        company_info = {
            'NO': recruit_no,
            '사업체명': '',
            '채용담당자명': '',
            '휴대폰 번호': '',
            '포함 키워드': self.schIncludeText,
            '제외 키워드': self.schExcludeText
        }

        try:
            res = self.api_client.get(url=url, headers=headers)

            # 응답 상태 확인
            if res:
                soup = BeautifulSoup(res, "html.parser")

                # 1. 사업체명
                name_tag = soup.find('div', class_='detail-primary__company')
                if name_tag:
                    company_info['사업체명'] = name_tag.get_text(strip=True)

                # 2. 담당자명, 휴대폰번호 (dl 순서 기반)
                info_container = soup.find('div', id='InfoCompany')
                if info_container:
                    def_items = info_container.select('.detail-def__item')
                    for item in def_items:
                        term = item.find('dt')
                        data = item.find('dd')

                        if not term or not data:
                            continue

                        term_text = term.get_text(strip=True)

                        if term_text == '담당자명':
                            company_info['채용담당자명'] = data.get_text(strip=True)

                        elif term_text == '연락처':
                            # 연락처 안에 여러 div가 있을 경우 첫 번째 div만
                            first_div = data.find('div')
                            if first_div and first_div.get_text(strip=True):
                                company_info['휴대폰 번호'] = first_div.get_text(strip=True)
                            else:
                                # div 없으면 전체 텍스트에서 010- 포함되는 것만 추출
                                full_text = data.get_text(strip=True)
                                if full_text:
                                    company_info['휴대폰 번호'] = full_text

                # 3. 보조 처리: td 내부에 '010-' 포함된 경우
                if not company_info.get('휴대폰 번호', '').startswith('010-'):
                    found = False
                    for td in soup.find_all('td'):
                        td_text = td.get_text(strip=True)
                        if td_text.startswith('010-'):
                            company_info['휴대폰 번호'] = td_text
                            found = True
                            break
                        for span in td.find_all('span'):
                            span_text = span.get_text(strip=True)
                            if span_text.startswith('010-'):
                                company_info['휴대폰 번호'] = span_text
                                found = True
                                break
                        if found:
                            break

        except Exception as e:
            print(f'error : {e}')
            # 네트워크 에러 또는 기타 예외 처리
            self.log_signal_func(f"요청 중 에러 발생: {e}")
        finally:
            return company_info

    # 전체 갯수 조회
    def total_cnt_cal(self):
        try:
            total_cnt, total_pages, imid_list = self.main_request(1, 'c')
            self.total_cnt = total_cnt
            self.total_pages = total_pages
        except Exception as e:
            print(f"Error calculating total count: {e}")


    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()