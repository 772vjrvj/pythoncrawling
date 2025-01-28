import os
import random
import re
import ssl
import time
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
import json

import pandas as pd
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from selenium import webdriver

ssl._create_default_https_context = ssl._create_unverified_context


# API
class ApiRequestTvingSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)  # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널

    def __init__(self, url_list):
        super().__init__()
        self.url_list = url_list  # URL을 클래스 속성으로 저장
        self.before_pro_value = 0
        self.running = True  # 실행 상태 플래그 추가
        self.sess = requests.Session()
        self.baseUrl = "https://www.tving.com"

        self.driver  = None
        self.version = None
        self.headers = None

        # 현재 시간을 'yyyymmddhhmmss' 형식으로 가져오기
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        self.file_name = f"티빙_{current_time}.xlsx"
        if len(self.url_list) <= 0:
            self.log_signal.emit(f'등록된 url이 없습니다.')


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
        self.version = self.driver.capabilities["browserVersion"]
        self.headers = {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.version}"
        }
        self.driver.quit()


    def run(self):
        if len(self.url_list) > 0:
            self.login()
            self.log_signal.emit("크롤링 시작")
            result_list = []
            for idx, url in enumerate(self.url_list, start=1):

                if not self.running:  # 실행 상태 확인
                    self.log_signal.emit("크롤링이 중지되었습니다.")
                    break

                # 10개의 항목마다 임시로 엑셀 저장
                if (idx - 1) % 10 == 0 and result_list:
                    self._save_to_csv_append(result_list)  # 임시 엑셀 저장 호출
                    self.log_signal.emit(f"엑셀 {idx - 1}개 까지 임시저장")
                    result_list = []  # 저장 후 초기화

                result = {
                    "origin_url": url,
                    "url": "",
                    "title": "",
                    "episode_synopsis": "",
                    "episode_title": "",
                    "episode_seq": "",
                    "episode_season": "",
                    "year": "",
                    "season": "",
                    "rating": "",
                    "genre": "",
                    "summary": "",
                    "cast": "",
                    "director": "",
                    "success": "X",
                    "message": "",
                    "error": "X"
                }

                self.log_signal.emit(f'번호 : {idx}, 시작')
                self._fetch_place_info(url, result)
                self._error_chk(result)
                self.log_signal.emit(f'번호 : {idx}, 데이터 : {result}')

                pro_value = (idx / len(self.url_list)) * 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)
                self.before_pro_value = pro_value

                result_list.append(result)
                time.sleep(random.uniform(0.5, 1))

            # 남은 데이터 저장
            if result_list:
                self._save_to_csv_append(result_list)

            # CSV 파일을 엑셀 파일로 변환
            try:
                csv_file_name = self.file_name  # 기존 CSV 파일 이름
                excel_file_name = csv_file_name.replace('.csv', '.xlsx')  # 엑셀 파일 이름으로 변경

                self.log_signal.emit(f"CSV 파일을 엑셀 파일로 변환 시작: {csv_file_name} → {excel_file_name}")
                df = pd.read_csv(csv_file_name)  # CSV 파일 읽기
                df.to_excel(excel_file_name, index=False)  # 엑셀 파일로 저장

                # 마지막 세팅
                pro_value = 1000000
                self.progress_signal.emit(self.before_pro_value, pro_value)

                self.log_signal.emit(f"엑셀 파일 변환 완료: {excel_file_name}")
                self.progress_end_signal.emit()

            except Exception as e:
                self.log_signal.emit(f"엑셀 파일 변환 실패: {e}")

        else:
            self.log_signal.emit("url를 입력하세요.")


    def _error_chk(self, result):
        if result['error'] == 'Y':
            self.log_signal.emit(result['message'])
            return True
        return False


    def _save_to_csv_append(self, results):
        self.log_signal.emit("CSV 저장 시작")

        try:
            # 파일이 존재하는지 확인
            if not os.path.exists(self.file_name):
                # 파일이 없으면 새로 생성 및 저장
                df = pd.DataFrame(results)
                df.to_csv(self.file_name, index=False)
                self.log_signal.emit(f"새 CSV 파일 생성 및 저장 완료: {self.file_name}")
            else:
                # 파일이 있으면 append 모드로 데이터 추가
                df = pd.DataFrame(results)
                df.to_csv(self.file_name, mode='a', header=False, index=False)
                self.log_signal.emit(f"기존 CSV 파일에 데이터 추가 완료: {self.file_name}")

        except Exception as e:
            # 예기치 않은 오류 처리
            self.log_signal.emit(f"CSV 저장 실패: {e}")


    def _extract_id_from_url(self, url):
        # URL을 파싱
        parsed_url = urlparse(url)

        # path에서 play/ 또는 titles/ 다음에 오는 값을 정규식으로 추출
        match = re.search(r'/(play|titles)/([^/]+)', parsed_url.path)

        # 값 반환 (없으면 None)
        return match.group(2) if match else None


    def _fetch_place_info(self, url, result):
        # CASE1
        if "/player/" in url:
            contents_id = ''
            # 첫 번째 '/player/' 이후의 값을 가져옴
            match = re.search(r'/player/(.+)', url)
            if match:
                contents_id = match.group(1)  # '/player/' 뒤의 값 반환
            new_url = f"https://www.tving.com/player/{contents_id}"
            print(f'player new_url : {new_url}')
            self._api_tving_contents(new_url, result)

        # CASE2
        elif "/program/" in url:
            contents_id = ''
            # 첫 번째 '/program/' 이후의 값을 가져옴
            match = re.search(r'/program/(.+)', url)
            if match:
                contents_id = match.group(1)  # '/player/' 뒤의 값 반환
            new_url = f"http://www.tving.com/contents/{contents_id}"
            print(f'program new_url : {new_url}')
            self._api_tving_contents(new_url, result)


    def _api_tving_contents(self, new_url, result):
        result['url'] = new_url

        try:
            # HTML 요청
            response = self.sess.get(new_url, headers=self.headers)
            response.raise_for_status()  # HTTP 에러 확인

            # BeautifulSoup로 HTML 파싱
            soup = BeautifulSoup(response.text, "html.parser")

            # <script> 태그에서 JSON 데이터 추출

            script_tags = soup.find_all("script", type="application/json")
            script_tag = None
            for tag in script_tags:
                if tag.get("id") == "__NEXT_DATA__":
                    script_tag = tag
                    break

            if not script_tag or not script_tag.string:
                result['message'] = "JSON script tag not found"

            # JSON 파싱
            json_data = json.loads(script_tag.string)

            self._data_set_json_info(json_data, result)

        except requests.exceptions.RequestException as e:
            result['message'] = str(e)
        except json.JSONDecodeError:
            result['message'] = "Failed to parse JSON"
        except Exception as e:
            result['message'] = str(e)


    def _data_set_json_info(self, json_data, result):
        # JSON 내 필요한 데이터 접근
        pageProps = json_data.get("props", {}).get("pageProps", {})

        content = pageProps.get("streamData", {}).get("body", {}).get("content", {})

        content_info         = pageProps.get("contentInfo", {})
        content_info_message = content_info.get("message", {})
        content_info_content = content_info.get("content", {})

        if content_info_message:
            print('content_info_message')
            result['success']           = "O"
            result['message']           = content_info_message
            result['error']             = "X"
        elif content_info_content:
            print('content_info_content')
            result['title']             = content_info_content.get("title", "")
            result['episode_synopsis']  = content_info_content.get("episode_synopsis", "")
            result['episode_title']     = content_info_content.get("episode_title", "")
            result['episode_seq']       = str(content_info_content.get("frequency", ""))
            result['episode_season']    = content_info_content.get("episode_sort", "")
            result['year']              = str(content_info_content.get("product_year", ""))
            result['season']            = content_info_content.get("season_no", "")
            result['rating']            = ""
            result['genre']             = content_info_content.get("genre_name", "")
            result['summary']           = content_info_content.get("synopsis", "")
            result['cast']              = ", ".join(content_info_content.get("actor", []))
            result['director']          = ", ".join(content_info_content.get("director", []))
            result['success']           = "O"
            result['message']           = "성공"
            result['error']             = "X"
        elif content_info:
            print('content_info_content')
            result['title']             = content_info.get("title", "")
            result['episode_synopsis']  = content_info.get("episode_synopsis", "")
            result['episode_title']     = content_info.get("episode_title", "")
            result['episode_seq']       = str(content_info.get("frequency", ""))
            result['episode_season']    = content_info.get("episode_sort", "")
            result['year']              = str(content_info.get("product_year", ""))
            result['season']            = content_info.get("season_no", "")
            result['rating']            = ""
            result['genre']             = content_info.get("genre_name", "")
            result['summary']           = content_info.get("synopsis", "")
            result['cast']              = ", ".join(content_info.get("actor", []))
            result['director']          = ", ".join(content_info.get("director", []))
            result['success']           = "O"
            result['message']           = "성공"
            result['error']             = "X"
        elif content:
            print('content')
            content_schedule = content.get("info", {}).get("schedule", {})
            program = content_schedule.get("program", {})
            episode = content_schedule.get("episode", {})

            result['title']             = content.get("program_name", {})
            result['episode_title']     = content.get("episode_name", {})
            result['episode_seq']       = content.get("frequency", "")

            result['summary']           = program.get("synopsis", {}).get("ko", "")
            result['cast']              = ", ".join(program.get("actor", []))
            result['director']          = ", ".join(program.get("director", []))
            result['episode_season']    = program.get("season_pgm_no", "")
            result['season']            = program.get("season_pgm_no", "")
            result['year']              = program.get("product_year", "")
            result['rating']            = '19+' if program.get("adult_yn", "") == "Y" else 'All'''

            result['episode_synopsis']  = episode.get("synopsis", {}).get("ko", "")
            category1_name = episode.get("category1_name", {}).get("ko", "")
            category2_name = episode.get("category2_name", {}).get("ko", "")
            if category1_name and category2_name:
                category = f"{category1_name}, {category2_name}"
            else:
                category = category1_name
            result['genre'] = category

            result['success'] = "O"
            result['message'] = "성공"
            result['error']   = "X"


    # 프로그램 중단
    def stop(self):
        """스레드 중지를 요청하는 메서드"""
        self.running = False
