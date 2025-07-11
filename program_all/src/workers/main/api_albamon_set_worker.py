import json
import math
import threading
import time
from urllib.parse import urlparse, parse_qs, unquote

import pandas as pd
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.core.global_state import GlobalState
from src.utils.api_utils import APIClient
from src.utils.excel_utils import ExcelUtils
from src.utils.file_utils import FileUtils
from src.utils.selenium_utils import SeleniumUtils
from src.workers.api_base_worker import BaseApiWorker
import random


class ApiAlbamonSetLoadWorker(BaseApiWorker):

    # 초기화
    def __init__(self):
        super().__init__()
        self.base_login_url = "https://www.albamon.com/user-account/login"
        self.base_main_url   = "https://www.albamon.com/jobs/total"

        self.excludeKeywords = ""
        self.includeKeyword = ""

        self.running = True  # 실행 상태 플래그 추가
        self.driver = None

        self.total_cnt = 0
        self.total_pages = 0
        self.current_page = 0
        self.current_cnt = 0
        self.before_pro_value = 0

        self.file_driver = None
        self.selenium_driver = None
        self.excel_driver = None
        self.sess = None
        self.running = True
        self.driver = None
        self.base_url = None
        self.before_pro_value = 0
        self.api_client = APIClient(use_cache=False)


    def init(self):

        self.log_signal_func("크롤링 시작 ========================================")

        self.driver_set()

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

        self.log_signal_func("크롤링 사이트 인증에 성공하였습니다.")
        self.log_signal_func(f"전체 회사수 계산을 시작합니다. 잠시만 기다려주세요.")
        self.total_cnt_cal()
        self.log_signal_func(f"전체 회사수 {self.total_cnt} 개")
        self.log_signal_func(f"전체 페이지수 {self.total_pages} 개")

        csv_filename = self.file_driver.get_csv_filename("알바몬")

        # columns = ["NO", "사업체명", "채용담당자명", "휴대폰 번호", "근무지 주소", "지역1", "지역2", "지역3", "급여 정보", "근무 기간", "등록일",
        #            "근무 요일", "근무 시간", "고용 형태", "복리후생 정보", "업직종", "업종", "대표자명", "기업주소"]

        columns = ["NO", "사업체명", "채용담당자명", "휴대폰 번호","포함 키워드", "제외 키워드"]

        df = pd.DataFrame(columns=columns)
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")

        for page in range(1, self.total_pages + 1):
            self.log_signal_func(f"현재 페이지 {page}")

            if not self.running:  # 실행 상태 확인
                self.log_signal_func("크롤링이 중지되었습니다.")
                break

            collection, pagination = self.main_request(page)

            for index, data in enumerate(collection):

                if not self.running:  # 실행 상태 확인
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break

                time.sleep(1)

                # 폰번호가 없는경우
                # if data.get('managerPhoneNumber', '') == '':
                #     self.log_signal_func(f"번호 없음 Skip")
                #     self.current_cnt = self.current_cnt + 1
                #     pro_value = (self.current_cnt / self.total_cnt) * 1000000
                #     self.progress_signal.emit(self.before_pro_value, pro_value)
                #     self.before_pro_value = pro_value
                #     self.log_signal_func(f"현재 페이지 {self.current_cnt}/{self.total_cnt}")
                #     continue

                scraped_date = data.get("scrapedDate", "")

                # 서울 강서구 마곡동
                workplace_area = data.get("workplaceArea", "").strip()
                area_parts = workplace_area.split() if workplace_area else []

                obj = {
                    "NO": data.get('recruitNo', ''),
                    # "사업체명": data.get('companyName', ''),
                    "채용담당자명": '',
                    "휴대폰 번호": data.get('managerPhoneNumber', ''),
                    # "근무지 주소": data.get('workplaceAddress', ''),
                    # "지역": data.get('workplaceArea', ''),    # 서울 중구
                    # "급여 정보": data.get('pay', ''),
                    # "등록일": scraped_date,
                    # "근무 기간": data.get('workingPeriod', ''),
                    # "근무 요일": data.get('workingWeek', ''),
                    # "근무 시간": data.get('workingTime', ''),
                    # "고용 형태": data.get('recruitType', {}).get('description', ''),
                    # "복리후생 정보": data.get('filterTotal', ''),
                    # "업직종": data.get('parts', ''),
                    # "지역1": area_parts[0] if len(area_parts) > 0 else "",
                    # "지역2": area_parts[1] if len(area_parts) > 1 else "",
                    # "지역3": area_parts[2] if len(area_parts) > 2 else "",
                    # "사업체명": "",
                    # "업종": "",
                    # "대표자명": "",
                    # "기업주소": "",
                    "포함 키워드": self.includeKeyword,
                    "제외 키워드": self.excludeKeywords,
                }

                detail_data = self.get_api_request(data.get('recruitNo', ''))

                if detail_data:
                    obj['채용담당자명'] = detail_data.get('viewData', {}).get('recruiter', '')
                    # obj['등록일'] = detail_data.get('viewData', {}).get('pcSortDate', '')
                    # obj['사업체명'] = detail_data.get('viewData',{}).get('recruitCompanyName','')
                    obj['사업체명'] = detail_data.get('companyData', {}).get('companyName', '')
                    # obj['업종'] = detail_data.get('companyData', {}).get('jobTypeName', '')
                    # obj['대표자명'] = detail_data.get('companyData', {}).get('representativeName', '')
                    # obj['기업주소'] = detail_data.get('companyData', {}).get('fullAddress', '')

                self.log_signal_func(f"현재 채용 정보 : {obj}")

                result_list.append(obj)

                if (index + 1) % 5 == 0:
                    self.excel_driver.append_to_csv(csv_filename, result_list, columns)

                self.current_cnt = self.current_cnt + 1

                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

                self.log_signal_func(f"현재 페이지 {self.current_cnt}/{self.total_cnt}")

                time.sleep(random.uniform(1, 3))

            time.sleep(random.uniform(5, 7))

        if result_list:
            self.excel_driver.append_to_csv(csv_filename, result_list, columns)


    # 마무리
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
        # 쿠키 설정
        cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
        for name, value in cookies.items():
            self.api_client.cookie_set(name, value)


        # 사용자가 OK를 눌렀을 경우 실행
        self.log_signal_func("✅ 사용자가 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")

        self.driver.get(self.base_main_url)

        time.sleep(2)  # 예제용

        # "상세조건" 텍스트를 가진 span을 포함하는 외부 span을 찾고 클릭
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[.//span[text()="상세조건"]]'))
        ).click()

        self.log_signal_func("🚀 작업 완료!")


    def wait_for_select_confirmation(self):
        """사용자가 확인(alert) 창에서 OK를 누를 때까지 대기"""
        event = threading.Event()  # OK 버튼 누를 때까지 대기할 이벤트 객체

        # 사용자에게 메시지 창 요청
        self.msg_signal.emit("키워드(포함/제외) 추가 후 OK를 눌러주세요(아래 목록이 나오는걸 확인하세요)", "info", event)

        # 사용자가 OK를 누를 때까지 대기
        self.log_signal_func("📢 사용자 입력 대기 중...")
        event.wait()  # 사용자가 OK를 누르면 해제됨

        # 사용자가 OK를 눌렀을 경우 실행
        self.log_signal_func("✅ 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")

        # 현재 URL 가져오기
        current_url = self.driver.current_url
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)

        # 키워드 추출 및 저장
        exclude = query_params.get("excludeKeywords", [""])[0]
        include = query_params.get("includeKeyword", [""])[0]

        self.excludeKeywords = unquote(exclude)
        self.includeKeyword = unquote(include)

        self.log_signal_func(f"🔍 제외 키워드: {self.excludeKeywords}")
        self.log_signal_func(f"🔍 포함 키워드: {self.includeKeyword}")

        time.sleep(2)  # 예제용
        self.log_signal_func("🚀 작업 완료!")


    def main_request(self, page=1):
        """현재 브라우저 URL을 기반으로 API 요청"""
        url = "https://bff-general.albamon.com/recruit/search"

        headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        }

        # self.excludeKeywords: 쉼표 구분된 문자열이라고 가정
        exclude_keywords_list = [kw.strip() for kw in self.excludeKeywords.split(',')] if self.excludeKeywords else []
        include_keyword = self.includeKeyword if self.includeKeyword else ""


        # 현재 브라우저 URL을 기반으로 payload 생성
        payload = {
            "pagination": {
                "page": page,  # page는 외부에서 전달받음
                "size": 50
            },
            "recruitListType": "NORMAL_ALL",
            "sortTabCondition": {
                "searchPeriodType": "ALL",
                "sortType": "DEFAULT"
            },
            "condition": {
                "age": 0,
                "areas": [],
                "educationType": "ALL",
                "employmentTypes": [],
                "endWorkTime": "",
                "excludeBar": False,
                "excludeKeywordList": exclude_keywords_list,
                "excludeKeywords": exclude_keywords_list,
                "excludeNegoAge": False,
                "excludeNegoGender": False,
                "excludeNegoWorkTime": False,
                "excludeNegoWorkWeek": False,
                "genderType": "NONE",
                "includeKeyword": include_keyword,
                "moreThanEducation": False,
                "parts": [],
                "similarDongJoin": False,
                "startWorkTime": "",
                "workDayTypes": [],
                "workPeriodTypes": [],
                "workTimeTypes": [],
                "workWeekTypes": [],
            }
        }

        self.log_signal_func(f"payload : {payload}")

        res = self.api_client.post(url=url, headers=headers, json=payload)

        if res:
            collection_list = res.get("base", {}).get("normal", {}).get("collection", [])
            pagination = res.get("base", {}).get("pagination", {})
            return collection_list, pagination
        else:
            return [], {}

    # 페이지 데이터 가져오기
    def get_api_request(self, recruit_no):
        url = f"https://www.albamon.com/jobs/detail/{recruit_no}?logpath=7&productCount=1"

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }
        result = None
        try:
            res = self.api_client.get(url=url, headers=headers)

            # 응답 상태 확인
            if res:
                soup = BeautifulSoup(res, "html.parser")
                script_tag = soup.find("script", {"id": "__NEXT_DATA__", "type": "application/json"})
                if script_tag:
                    json_data = json.loads(script_tag.string)
                    data = json_data.get("props", {}).get("pageProps", {}).get("data", {})
                    self.log_signal_func(f"회사정보 가져오기 성공")
                    result = data
                else:
                    print("JSON 데이터를 찾을 수 없습니다.")

        except Exception as e:
            print(f'error : {e}')
            # 네트워크 에러 또는 기타 예외 처리
            self.log_signal_func(f"요청 중 에러 발생: {e}")
        return result

    # 전체 갯수 조회
    def total_cnt_cal(self):
        try:
            collection, pagination = self.main_request(1)

            total_count = pagination.get('totalCount', 0)
            page_size = pagination.get('size', 1)  # 0 방지

            total_page_cnt = math.ceil(total_count / page_size)
            total_product_cnt = total_count

            self.total_cnt = total_product_cnt
            self.total_pages = total_page_cnt

        except Exception as e:
            print(f"Error calculating total count: {e}")
            return 0, 0


    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()
