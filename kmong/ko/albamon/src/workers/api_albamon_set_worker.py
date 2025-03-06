import os
import ssl
import time
import json

import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium import webdriver
import math
from datetime import datetime  # 수정 추가
import threading
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
import urllib.parse

from src.utils.time_utils import get_current_yyyymmddhhmmss, get_current_formatted_datetime
from selenium.webdriver.common.alert import Alert

ssl._create_default_https_context = ssl._create_unverified_context

image_main_directory = 'albamon_images'
company_name = '알바몬'
site_name = 'albamon'
excel_filename = ''
baseUrl = "https://www.albamon.com/jobs/area"
select_baseUrl = ""


# API
class ApiAlbamonSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)         # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널
    msg_signal = pyqtSignal(str, str, object)

    # 초기화
    def __init__(self, checked_list):
        super().__init__()
        self.baseUrl = baseUrl
        self.sess = requests.Session()
        self.checked_list = checked_list

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

    # 프로그램 실행
    def run(self):
        global image_main_directory, company_name, site_name, excel_filename, baseUrl

        self.log_signal.emit("크롤링 시작")
        result_list = []
        self.log_signal.emit("크롤링 사이트 인증을 시도중입니다. 잠시만 기다려주세요.")
        self.login()
        self.wait_for_user_confirmation()

        self.log_signal.emit("크롤링 사이트 인증에 성공하였습니다.")
        self.log_signal.emit(f"전체 회사수 계산을 시작합니다. 잠시만 기다려주세요.")
        self.total_cnt_cal()
        self.log_signal.emit(f"전체 회사수 {self.total_cnt} 개")
        self.log_signal.emit(f"전체 페이지수 {self.total_pages} 개")

        csv_filename = os.path.join(os.getcwd(), f"알바몬_{get_current_yyyymmddhhmmss()}.csv")
        columns = ["NO", "사업체명", "채용담당자명", "휴대폰 번호", "근무지 주소", "지역1", "지역2", "지역3", "급여 정보", "근무 기간", "등록일",
                   "근무 요일", "근무 시간", "고용 형태", "복리후생 정보", "업직종", "업종", "대표자명", "기업주소"]
        df = pd.DataFrame(columns=columns)
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")

        for page in range(1, self.total_pages + 1):
            self.log_signal.emit(f"현재 페이지 {page}")
            time.sleep(1)
            if not self.running:  # 실행 상태 확인
                self.log_signal.emit("크롤링이 중지되었습니다.")
                break

            collection, pagination = self.main_request(page)

            for index, data in enumerate(collection):

                if not self.running:  # 실행 상태 확인
                    self.log_signal.emit("크롤링이 중지되었습니다.")
                    break

                time.sleep(1)

                # 폰번호가 없는경우
                if data.get('managerPhoneNumber', '') == '':
                    self.log_signal.emit(f"번호 없음 Skip")
                    self.current_cnt = self.current_cnt + 1
                    pro_value = (self.current_cnt / self.total_cnt) * 1000000
                    self.progress_signal.emit(self.before_pro_value, pro_value)
                    self.before_pro_value = pro_value
                    self.log_signal.emit(f"현재 페이지 {self.current_cnt}/{self.total_cnt}")
                    continue

                scraped_date = data.get("scrapedDate", "")

                # 서울 강서구 마곡동
                workplace_area = data.get("workplaceArea", "").strip()
                area_parts = workplace_area.split() if workplace_area else []

                obj = {
                    "NO": data.get('recruitNo', ''),
                    # "사업체명": data.get('companyName', ''),
                    "채용담당자명": '',
                    "휴대폰 번호": data.get('managerPhoneNumber', ''),
                    "근무지 주소": data.get('workplaceAddress', ''),
                    "지역": data.get('workplaceArea', ''),    # 서울 중구
                    "급여 정보": data.get('pay', ''),
                    "등록일": scraped_date,
                    "근무 기간": data.get('workingPeriod', ''),
                    "근무 요일": data.get('workingWeek', ''),
                    "근무 시간": data.get('workingTime', ''),
                    "고용 형태": data.get('recruitType', {}).get('description', ''),
                    "복리후생 정보": data.get('filterTotal', ''),
                    "업직종": data.get('parts', ''),
                    "지역1": area_parts[0] if len(area_parts) > 0 else "",
                    "지역2": area_parts[1] if len(area_parts) > 1 else "",
                    "지역3": area_parts[2] if len(area_parts) > 2 else "",
                    "사업체명": "",
                    "업종": "",
                    "대표자명": "",
                    "기업주소": "",
                }

                detail_data = self.get_api_request(data.get('recruitNo', ''))

                if detail_data:
                    obj['채용담당자명'] = detail_data.get('viewData', {}).get('recruiter', '')
                    obj['등록일'] = detail_data.get('viewData', {}).get('pcSortDate', '')
                    # obj['사업체명'] = detail_data.get('viewData',{}).get('recruitCompanyName','')
                    obj['사업체명'] = detail_data.get('companyData', {}).get('companyName', '')
                    obj['업종'] = detail_data.get('companyData', {}).get('jobTypeName', '')
                    obj['대표자명'] = detail_data.get('companyData', {}).get('representativeName', '')
                    obj['기업주소'] = detail_data.get('companyData', {}).get('fullAddress', '')

                self.log_signal.emit(f"현재 채용 정보 : {obj}")

                result_list.append(obj)

                if (index + 1) % 5 == 0:
                    df = pd.DataFrame(result_list, columns=columns)
                    df.to_csv(csv_filename, mode='a', header=False, index=False, encoding="utf-8-sig")
                    result_list.clear()

                self.current_cnt = self.current_cnt + 1

                pro_value = (self.current_cnt / self.total_cnt) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value
                self.log_signal.emit(f"현재 페이지 {self.current_cnt}/{self.total_cnt}")

            if result_list:
                df = pd.DataFrame(result_list, columns=columns)
                df.to_csv(csv_filename, mode='a', header=False, index=False, encoding="utf-8-sig")

        self.progress_signal.emit(self.before_pro_value, 1000000)
        time.sleep(3)
        self.log_signal.emit("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 프로그램 중단
    def stop(self):
        """스레드 중지를 요청하는 메서드"""

        self.running = False

    def wait_for_user_confirmation(self):
        """사용자가 확인(alert) 창에서 OK를 누를 때까지 대기"""
        event = threading.Event()  # OK 버튼 누를 때까지 대기할 이벤트 객체

        # 사용자에게 메시지 창 요청
        self.msg_signal.emit("옵션을 선택 후 OK를 눌러주세요", "info", event)

        # 사용자가 OK를 누를 때까지 대기
        self.log_signal.emit("📢 사용자 입력 대기 중...")
        event.wait()  # 사용자가 OK를 누르면 해제됨

        # 사용자가 OK를 눌렀을 경우 실행
        self.log_signal.emit("✅ 사용자가 확인 버튼을 눌렀습니다. 다음 작업 진행 중...")
        time.sleep(2)  # 예제용
        self.log_signal.emit("🚀 작업 완료!")

        # 현재 브라우저의 URL을 가져와 저장
        self.select_baseUrl = self.driver.current_url
        self.log_signal.emit(f"🌐 현재 브라우저 URL 저장됨: {self.select_baseUrl}")


    def login(self):
        webdriver_options = webdriver.ChromeOptions()

        ###### 자동 제어 감지 방지 #####
        webdriver_options.add_argument('--disable-blink-features=AutomationControlled')

        ##### 화면 최대 #####
        # webdriver_options.add_argument("--start-maximized")  # 최대화 대신 크기 조절 사용

        ##### headless 모드 비활성화 (브라우저 UI 보이게) #####
        # webdriver_options.add_argument("--headless")

        ##### 자동 경고 제거 #####
        webdriver_options.add_experimental_option('useAutomationExtension', False)

        ##### 로깅 비활성화 #####
        webdriver_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        ##### 자동화 도구 사용 감지 제거 #####
        webdriver_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        # 드라이버 실행
        self.driver = webdriver.Chrome(options=webdriver_options)
        self.driver.set_page_load_timeout(120)

        # 현재 모니터 해상도 가져오기
        screen_width, screen_height = pyautogui.size()

        # 창 크기를 너비 절반, 높이 전체로 설정
        self.driver.set_window_size(screen_width // 2, screen_height)

        # 창 위치를 왼쪽 상단에 배치
        self.driver.set_window_position(0, 0)

        # 웹사이트 열기
        self.driver.get(self.baseUrl)

        # 쿠키 설정
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.sess.cookies.set(cookie['name'], cookie['value'])


    def parse_albamon_url(self, url):
        """Albamon 검색 URL을 분석하여 payload에 맞는 데이터를 추출"""
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # page 제외하고 기본 payload 설정
        payload = {
            "pagination": {
                "page": 1,  # page는 외부에서 전달받음
                "size": 50
            },
            "recruitListType": "AREA",
            "sortTabCondition": {
                "searchPeriodType": "ALL",
                "sortType": "DEFAULT"
            },
            "condition": {
                "areas": [],
                "employmentTypes": query_params.get("employmentTypes", []),
                "excludeKeywords": [],
                "excludeBar": False,
                "excludeNegoAge": query_params.get("excludeNegoAge", ["False"])[0] == "true",
                "excludeNegoWorkWeek": query_params.get("excludeNegoWorkWeek", ["False"])[0] == "true",
                "excludeNegoWorkTime": query_params.get("excludeNegoWorkTime", ["False"])[0] == "true",
                "excludeNegoGender": False,
                "parts": query_params.get("parts", []),
                "similarDongJoin": False,
                "workDayTypes": query_params.get("workDayTypes", []),
                "workPeriodTypes": query_params.get("workPeriodTypes", []),
                "workTimeTypes": query_params.get("workTimeTypes", []),
                "workWeekTypes": query_params.get("workWeekTypes", []),
                "endWorkTime": query_params.get("endWorkTime", [""])[0],
                "startWorkTime": query_params.get("startWorkTime", [""])[0],
                "includeKeyword": query_params.get("includeKeyword", [""])[0],
                "excludeKeywordList": query_params.get("excludeKeywordList", []),
                "age": int(query_params.get("age", [0])[0]),
                "genderType": query_params.get("genderType", ["NONE"])[0],
                "moreThanEducation": False,
                "educationType": query_params.get("educationType", ["ALL"])[0],
                "selectedArea": {"si": "", "gu": "", "dong": ""}
            }
        }

        # areas 파싱
        areas = query_params.get("areas", [""])
        parsed_areas = []

        # areas를 ',' 기준으로 나누어 리스트로 변환
        split_areas = []
        for area_group in areas:
            split_areas.extend(area_group.split(","))


        for area in split_areas:
            if not area:
                continue

            si = area[:1] + "000"  # 시 (첫 번째 자리 + '000')
            gu = area[:4] if len(area) >= 4 else ""  # 4자리 구
            dong = area if len(area) >= 8 else ""  # 6자리 동

            # 만약 시 코드(G000)만 존재한다면 gu와 dong을 빈 문자열로 설정
            if area == si:
                gu = ""
                dong = ""

            parsed_areas.append({"si": si, "gu": gu, "dong": dong})

        payload["condition"]["areas"] = parsed_areas

        return payload

    def main_request(self, page=1):
        """현재 브라우저 URL을 기반으로 API 요청"""
        url = "https://bff-general.albamon.com/recruit/search"

        headers = {
            "authority": "bff-general.albamon.com",
            "method": "POST",
            "path": "/recruit/search",
            "scheme": "https",
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "albamon-domain-type": "pc",
            "content-type": "application/json",
            "origin": "https://www.albamon.com",
            "priority": "u=1, i",
            # "referer": self.driver.current_url,
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        }

        # 현재 브라우저 URL을 기반으로 payload 생성
        payload = self.parse_albamon_url(self.driver.current_url)
        payload["pagination"]["page"] = page  # page는 따로 받음

        response = self.sess.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            collection_list = data.get("base", {}).get("normal", {}).get("collection", [])
            pagination = data.get("base", {}).get("pagination", {})
            return collection_list, pagination
        else:
            print(f"Error: {response.status_code}")
            return [], {}



    # 페이지 데이터 가져오기
    def get_api_request(self, recruit_no):
        url = f"https://www.albamon.com/jobs/detail/{recruit_no}?logpath=7&productCount=1"

        headers = {
            "authority": "www.albamon.com",
            "method": "GET",
            "path": "/jobs/detail/107967948?logpath=7&productCount=1",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cookie": "_ga=GA1.1.1589651135.1739978839; ConditionId=1187621C-98D0-44C9-AE4E-D1D3869438EF; ab.storage.deviceId.7a5f1472-069a-4372-8631-2f711442ee40=%7B%22g%22%3A%22c3f5d6c8-3939-dca6-cfae-3a6ade1a2651%22%2C%22c%22%3A1739978837484%2C%22l%22%3A1740054277046%7D; AM_USER_UUID=b0949b94-81f4-40d0-9821-b06f97df5dfa",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }


        try:
            res = self.sess.get(url, headers=headers, timeout=10)

            # 응답 상태 확인
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                script_tag = soup.find("script", {"id": "__NEXT_DATA__", "type": "application/json"})
                if script_tag:
                    json_data = json.loads(script_tag.string)
                    data = json_data.get("props", {}).get("pageProps", {}).get("data", {})
                    self.log_signal.emit(f"회사정보 가져오기 성공")
                    return data
                else:
                    print("JSON 데이터를 찾을 수 없습니다.")
            else:
                # 상태 코드가 200이 아닌 경우
                self.log_signal.emit(f"HTTP 요청 실패: 상태 코드 {res.status_code}, 내용: {res.text}")
                return None

        except Exception as e:
            print(f'error : {e}')
            # 네트워크 에러 또는 기타 예외 처리
            self.log_signal.emit(f"요청 중 에러 발생: {e}")
            return None

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
