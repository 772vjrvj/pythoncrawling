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


from src.utils.time_utils import get_current_yyyymmddhhmmss, get_current_formatted_datetime

ssl._create_default_https_context = ssl._create_unverified_context

image_main_directory = 'albamon_images'
company_name = '알바몬'
site_name = 'albamon'
excel_filename = ''
baseUrl = "https://www.albamon.com/"


# API
class ApiAlbamonSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)         # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널

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
        self.log_signal.emit("크롤링 사이트 인증에 성공하였습니다.")
        self.log_signal.emit(f"전체 회사수 계산을 시작합니다. 잠시만 기다려주세요.")
        self.total_cnt_cal()
        self.log_signal.emit(f"전체 회사수 {self.total_cnt} 개")
        self.log_signal.emit(f"전체 페이지수 {self.total_pages} 개")

        csv_filename = os.path.join(os.getcwd(), f"알바몬_{get_current_yyyymmddhhmmss()}.csv")
        columns = ["NO", "사업체명", "채용담당자명", "휴대폰 번호", "근무지 주소", "급여 정보", "근무 기간",
                   "근무 요일", "근무 시간", "고용 형태", "복리후생 정보", "업직종", "업종", "대표자명", "기업주소"]
        df = pd.DataFrame(columns=columns)
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")

        for page in range(1, self.total_pages + 1):
            self.log_signal.emit(f"현재 페이지 {page}")
            time.sleep(1)
            if not self.running:  # 실행 상태 확인
                self.log_signal.emit("크롤링이 중지되었습니다.")
                break

            collection, pagination = self.main_request(page, "I000", "FULL_TIME")

            for index, data in enumerate(collection):
                time.sleep(1)
                obj = {
                    "NO": data.get('recruitNo', ''),
                    "사업체명": data.get('companyName', ''),
                    "채용담당자명": '',
                    "휴대폰 번호": data.get('managerPhoneNumber', ''),
                    "근무지 주소": data.get('workplaceAddress', ''),
                    "급여 정보": data.get('pay', ''),
                    "근무 기간": data.get('workingPeriod', ''),
                    "근무 요일": data.get('workingWeek', ''),
                    "근무 시간": data.get('workingTime', ''),
                    "고용 형태": data.get('recruitType', {}).get('description', ''),
                    "복리후생 정보": data.get('filterTotal', ''),
                    "업직종": data.get('parts', '')
                }

                detail_data = self.get_api_request(data['recruitNo'])
                obj['채용담당자명'] = detail_data.get('viewData',{}).get('recruiter','')
                obj['업종'] = detail_data.get('companyData',{}).get('jobTypeName','')
                obj['대표자명'] = detail_data.get('companyData',{}).get('representativeName','')
                obj['기업주소'] = detail_data.get('companyData',{}).get('fullAddress','')

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
        self.log_signal.emit("=============== 크롤링 종료")
        self.progress_end_signal.emit()

    # 프로그램 중단
    def stop(self):
        """스레드 중지를 요청하는 메서드"""
        self.running = False

    # 로그인 쿠키가져오기
    def login(self):
        webdriver_options = webdriver.ChromeOptions()

        # 이 옵션은 Chrome이 자동화 도구(예: Selenium)에 의해 제어되고 있다는 것을 감지하지 않도록 만듭니다.
        # AutomationControlled 기능을 비활성화하여 webdriver가 브라우저를 자동으로 제어하는 것을 숨깁니다.
        # 이는 일부 웹사이트에서 자동화 도구가 감지되는 것을 방지하는 데 유용합니다.
        ###### 자동 제어 감지 방지 #####
        webdriver_options.add_argument('--disable-blink-features=AutomationControlled')

        # Chrome 브라우저를 실행할 때 자동으로 브라우저를 최대화 상태로 시작합니다.
        # 이 옵션은 사용자가 브라우저를 처음 실행할 때 크기가 자동으로 최대로 설정되도록 합니다.
        ##### 화면 최대 #####
        webdriver_options.add_argument("--start-maximized")

        # headless 모드로 Chrome을 실행합니다.
        # 이는 화면을 표시하지 않고 백그라운드에서 브라우저를 실행하게 됩니다.
        # 브라우저 UI 없이 작업을 수행할 때 사용하며, 서버 환경에서 유용합니다.
        ##### 화면이 안보이게 함 #####
        webdriver_options.add_argument("--headless")

        #이 설정은 Chrome의 자동화 기능을 비활성화하는 데 사용됩니다.
        #기본적으로 Chrome은 자동화가 활성화된 경우 브라우저의 콘솔에 경고 메시지를 표시합니다.
        #이 옵션을 설정하면 이러한 경고 메시지가 나타나지 않도록 할 수 있습니다.
        ##### 자동 경고 제거 #####
        webdriver_options.add_experimental_option('useAutomationExtension', False)

        # 이 옵션은 브라우저의 로깅을 비활성화합니다.
        # enable-logging을 제외시키면, Chrome의 로깅 기능이 활성화되지 않아 불필요한 로그 메시지가 출력되지 않도록 할 수 있습니다.
        ##### 로깅 비활성화 #####
        webdriver_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # 이 옵션은 enable-automation 스위치를 제외시킵니다.
        # enable-automation 스위치가 활성화되면,
        # 자동화 도구를 사용 중임을 알리는 메시지가 브라우저에 표시됩니다.
        # 이를 제외하면 자동화 도구의 사용이 감지되지 않습니다.
        ##### 자동화 도구 사용 감지 제거 #####
        webdriver_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.driver = webdriver.Chrome(options=webdriver_options)
        self.driver.set_page_load_timeout(120)
        self.driver.get(self.baseUrl)
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.sess.cookies.set(cookie['name'], cookie['value'])
        self.driver.quit()

    # 채용 리스트
    def main_request(self, page=1, areas="I000", employment_types="FULL_TIME"):
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
            "referer": "https://www.albamon.com/jobs/area?areas=I000&employmentTypes=FULL_TIME&page=2",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        }

        payload = {
            "pagination": {
                "page": page,
                "size": 10000
            },
            "recruitListType": "AREA",
            "sortTabCondition": {
                "searchPeriodType": "ALL",
                "sortType": "DEFAULT"
            },
            "condition": {
                "areas": [{"si": "I000", "gu": "", "dong": ""}],
                "employmentTypes": ["FULL_TIME"],
                "excludeKeywords": [],
                "excludeBar": False,
                "excludeNegoAge": False,
                "excludeNegoWorkWeek": False,
                "excludeNegoWorkTime": False,
                "excludeNegoGender": False,
                "parts": [],
                "similarDongJoin": False,
                "workDayTypes": [],
                "workPeriodTypes": [],
                "workTimeTypes": [],
                "workWeekTypes": [],
                "endWorkTime": "",
                "startWorkTime": "",
                "includeKeyword": "",
                "excludeKeywordList": [],
                "age": 0,
                "genderType": "NONE",
                "moreThanEducation": False,
                "educationType": "ALL",
                "selectedArea": {"si": "", "gu": "", "dong": ""}
            }
        }

        response = self.sess.post(url, headers=headers, json=payload, timeout=10)


        if response.status_code == 200:
            data = response.json()

            # collection 리스트 추출
            collection_list = data.get("base", {}).get("normal", {}).get("collection", [])

            # pagination 정보 추출
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
            # 네트워크 에러 또는 기타 예외 처리
            self.log_signal.emit(f"요청 중 에러 발생: {e}")
            return None

    # 전체 갯수 조회
    def total_cnt_cal(self):
        try:
            collection, pagination = self.main_request(1, "I000", "FULL_TIME")

            total_count = pagination.get('totalCount', 0)
            page_size = pagination.get('size', 1)  # 0 방지

            total_page_cnt = math.ceil(total_count / page_size)
            total_product_cnt = total_count

            self.total_cnt = total_product_cnt
            self.total_pages = total_page_cnt

        except Exception as e:
            print(f"Error calculating total count: {e}")
            return 0, 0
