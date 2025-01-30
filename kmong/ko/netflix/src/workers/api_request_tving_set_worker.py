import json
import os
import random
import re
import ssl
import time
from datetime import datetime

import pandas as pd
import psutil
import requests
from PyQt5.QtCore import QThread, pyqtSignal, QEventLoop
from PyQt5.QtWidgets import QMessageBox
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

ssl._create_default_https_context = ssl._create_unverified_context


# API
class ApiRequestTvingSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)  # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float, float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널
    msg_signal = pyqtSignal(str, str)
    msg_response_signal = pyqtSignal(bool)  # 부모가 메시지 응답(확인/취소)을 전달하는 시그널
    finally_finished_signal = pyqtSignal(str)

    # 초기화
    def __init__(self, url_list):
        super().__init__()
        self.url_list = url_list  # URL을 클래스 속성으로 저장
        self.result_list = []
        self.before_pro_value = 0
        self.running = True  # 실행 상태 플래그 추가
        self.sess = requests.Session()
        self.baseUrl = "https://www.tving.com"
        self.driver  = None
        self.response = None  # 사용자의 응답을 저장할 변수
        self.msg_response_signal.connect(self.handle_message_response)  # 부모 응답 처리 함수 연결
        self.loop = None  # 이벤트 루프 객체

        # 현재 시간을 'yyyymmddhhmmss' 형식으로 가져오기
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        self.file_name = f"티빙_{current_time}.csv"
        if len(self.url_list) <= 0:
            self.log_signal.emit(f'등록된 url이 없습니다.')
        else:
            self.driver = self._setup_driver()

    # 실행
    def run(self):
        if len(self.url_list) > 0:
            self._main()
        else:
            self.log_signal.emit("url를 입력하세요.")

    # 로그인
    def _main(self):
        try:
            # 필요한 쿠키 키 목록
            required_cookies = [
                "authToken",
                "accessToken",
                "refreshToken",
            ]
            cookies = self._get_cookies_from_browser(self.baseUrl)
            if all(key in cookies for key in required_cookies):
                self.cookies = cookies
                self.log_signal.emit("회원 확인.")
                self.cookies = cookies
                self.log_signal.emit("쿠키 확인 성공.")
                self._crawling()
                return True
            else:
                self.msg_signal.emit("로그인 필요", "로그인 후 확인을 눌러주세요.")
                return False
        except Exception as e:
            self.log_signal.emit(f"넷플릭스 로그인 중 에러 발생 : {e}")
            return False

    # 크롤링
    def _crawling(self):
        self.log_signal.emit("크롤링 시작")
        self.result_list = []
        for idx, url in enumerate(self.url_list, start=1):
            if not self.running:  # 실행 상태 확인
                self.log_signal.emit("크롤링이 중지되었습니다.")
                break

            # 10개의 항목마다 임시로 엑셀 저장
            if (idx - 1) % 10 == 0 and self.result_list:
                self._save_to_csv_append(self.result_list)  # 임시 엑셀 저장 호출
                self.log_signal.emit(f"엑셀 {idx - 1}개 까지 임시저장")
                self.result_list = []  # 저장 후 초기화

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

            self.result_list.append(result)
            time.sleep(random.uniform(0.5, 1))
        self.progress_end_signal.emit()

    # 메시지 응답
    def handle_message_response(self, confirmed):
        self.response = confirmed  # True: 확인, False: 취소
        if self.response:
            if self.isRunning():  # 스레드가 실행 중이면 중지 후 재시작
                self.stop()  # 기존 스레드 중지
                self.wait()  # 스레드가 완전히 종료될 때까지 대기
            self.start()  # 새로운 스레드 시작

    # 데이터 요청 분기 처리
    def _fetch_place_info(self, url, result):
        error_urls = [
            "/m.tving.com/app/",
            "/m.tving.com/event/",
            "/api.tving.com/",
            "/ocn.tving.com/",
            "/otvn.tving.com/",
            "/mall.tving.com/goods/",
            "/event.tving.com/",
            "/olive.tving.com/",
            "/ocnseries.tving.com/",
            # "/program.tving.com/catchon/",
            # "/program.tving.com/ocn/",
            # "/program.tving.com/ocnthrills/",
            # "/program.tving.com/ogn/",
            # "/program.tving.com/olive/",
            # "/program.tving.com/ongamenet/",
            # "/program.tving.com/onstyle/",
            # "/program.tving.com/lifestyler/",
            # "/program.tving.com/Program/",
            # "/program.tving.com/program/",
            # "/program.tving.com/Rss/",
            # "/program.tving.com/rss/",
            # "/program.tving.com/xtm/",
            # "/program.tving.com/xtvn/",
            # "/program.tving.com/Board/",
            # "/program.tving.com/chcgv/",
            # "/program.tving.com/cj_concert/",
            # "/program.tving.com/Content/",
            # "/program.tving.com/kcontv/",
            # "/program.tving.com/mnet/",
            # "/program.tving.com/superaction/",
            # "/program.tving.com/funbakery/",
            # "/program.tving.com/tooniverse/",
            # "/program.tving.com/dims/",
            # "/program.tving.com/tvndrama/",
            # "/program.tving.com/tvnshow/",
            # "/program.tving.com/tvnsports/",
            "/tvn.tving.com/Error",
            "/tvn.tving.com/tvn",
            # "/tvn.tving.com/tvn/program",
            # "/tvn.tving.com/tvn/Schedule",
            # "/tvn.tving.com/tvn/schedule",
            # "/tvn.tving.com/tvn/VOD/",
            # "/tvn.tving.com/tvn/event",
            # "/tvn.tving.com/tvn/vod/",
            "/www.tving.com/tv/player/",
            "/www.tving.com/list/theme/",
            "/www.tving.com/theme/",
            "/www.tving.com/kbo/contents/20"
        ]

        # 예외 케이스 점검
        if any(error_url in url for error_url in error_urls):
            result.update({'success': "X", 'error': "O", 'message': "404 Error"})
        elif any(x in url for x in ["/program.tving.com/","/program.m.tving.com/"]):
            if any(x in url for x in ["/program.tving.com/tvnstory/","/program.tving.com/tvn/", "/program.tving.com/otvn/", "/program.m.tving.com/tvn/"]):
                title, episode = self._extract_title_episode(url)
                result['episode_seq'] = episode
                new_url = f'https://tvn.cjenm.com/ko/{title}'
                self._api_tving_cjenm(new_url, result)
            else:
                result.update({'success': "X", 'error': "O", 'message': "404 Error"})
        elif any(x in url for x in ["/program.tving.com/tvnstory/","/program.tving.com/tvn/", "/program.tving.com/otvn/", "/program.m.tving.com/tvn/"]):
            title, episode = self._extract_title_episode(url)
            result['episode_seq'] = episode
            new_url = f'https://tvn.cjenm.com/ko/{title}'
            self._api_tving_cjenm(new_url, result)
        elif "/program.tving.com/zhtv/" in url:
            title, episode = self._extract_title_episode(url)
            result['episode_seq'] = episode
            new_url = f'https://zhtv.cjenm.com/ko/{title}'
            self._api_tving_cjenm(new_url, result)
        elif "/kbo/contents/" in url:
            new_url = url
            self._api_tving_contents(new_url, result)
        elif "/player/" in url:
            contents_id = ''
            # 첫 번째 '/player/' 이후의 값을 가져옴
            match = re.search(r'/player/(.+)', url)
            if match:
                contents_id = match.group(1)  # '/player/' 뒤의 값 반환
            if '/' in contents_id:
                # '/'로 나누고 첫 번째 부분 가져오기
                contents_id = contents_id.split('/')[0]
                # '.#' 제거
                contents_id = contents_id.replace('.', '').replace('#', '')
            new_url = f"https://www.tving.com/player/{contents_id}"
            self._api_tving_player(new_url, result)
        elif any(x in url for x in ["/program/", "/contents/"]):
            contents_id = ''
            # 첫 번째 '/program/' 이후의 값을 가져옴
            match = re.search(r'/program/(.+)', url)
            if match:
                contents_id = match.group(1)  # '/player/' 뒤의 값 반환
            if '/' in contents_id:
                # '/'로 나누고 첫 번째 부분 가져오기
                contents_id = contents_id.split('/')[0]
                # '.#' 제거
                contents_id = contents_id.replace('.', '').replace('#', '')
            new_url = f"http://www.tving.com/contents/{contents_id}"
            self._api_tving_contents(new_url, result)


    def _extract_title_episode(self, url):
        pattern = r"https?://program(?:\.m)?\.tving\.com/\w+/([^/]+)(?:/([^/]+))?"
        match = re.search(pattern, url)
        if match:
            title = match.group(1)
            episode = match.group(2) if match.group(2) and match.group(2).isdigit() else None
            return title, episode
        return '', ''

    # tving api contents
    def _api_tving_cjenm(self, new_url, result):
        result['url'] = new_url

        try:
            # HTML 요청
            response = requests.get(new_url)
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

    # tving api player
    def _api_tving_player(self, new_url, result):
        result['url'] = new_url

        try:
            self.driver.get(new_url)
            time.sleep(1)
            # 페이지 로드 후 HTML 가져오기
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

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

        except WebDriverException as e:
            result['message'] = f"WebDriver Error: {str(e)}"
        except Exception as e:
            result['message'] = str(e)

    # tving api contents
    def _api_tving_contents(self, new_url, result):
        result['url'] = new_url

        headers = {
            "authority": "www.tving.com",
            "method": "GET",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "referer": "https://user.tving.com/",
            "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
        }

        try:
            # HTML 요청
            response = requests.get(new_url, headers=headers, cookies=self.cookies)
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

    # json 데이터 세팅
    def _data_set_json_info(self, json_data, result):
        try:
            # JSON 내 필요한 데이터 접근
            pageProps = json_data.get("props", {}).get("pageProps", {})

            content = pageProps.get("streamData", {}).get("body", {}).get("content", {})

            menu_tit_tag_cnts = pageProps.get("pageInfo", {}).get("pageInfo", {}).get("menuTitTagCnts", {})

            content_info         = pageProps.get("contentInfo", {})
            content_info_message = content_info.get("message", {})
            content_info_content = content_info.get("content", {})

            if "/kbo/contents/" in result['url']:
                result['title']             = pageProps.get("metaProps", {}).get("title", {})
            elif menu_tit_tag_cnts:
                result['title']             = menu_tit_tag_cnts
            elif content:
                info = content.get("info", {})
                schedule = info.get("schedule", {})
                if schedule:
                    program = schedule.get("program", {})
                    episode = schedule.get("episode", {})
                else:
                    program = info.get("program", {})
                    episode = info.get("episode", {})

                result['title']             = content.get("program_name", {})
                result['episode_title']     = content.get("episode_name", {})
                result['episode_seq']       = content.get("frequency", "")

                if program:
                    result['summary']           = program.get("synopsis", {}).get("ko", "")
                    result['cast']              = ", ".join(program.get("actor", []))
                    result['director']          = ", ".join(program.get("director", []))
                    result['episode_season']    = program.get("season_pgm_no", "")
                    result['season']            = program.get("season_pgm_no", "")
                    result['year']              = program.get("product_year", "")
                    result['rating']            = '19+' if program.get("adult_yn", "") == "Y" else 'All'''

                    result['episode_synopsis']  = program.get("synopsis", {}).get("ko", "")
                    category1_name = program.get("category1_name", {}).get("ko", "")
                    category2_name = program.get("category2_name", {}).get("ko", "")
                    if category1_name and category2_name:
                        category = f"{category1_name}, {category2_name}"
                    else:
                        category = category1_name
                    result['genre'] = category

                if episode:
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
            elif content_info_message:
                result['success']           = "O"
                result['message']           = content_info_message
                result['error']             = "X"
            elif content_info_content:
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
        except json.JSONDecodeError:
            result['success'] = "X"
            result['error'] = "O"
            result['message'] = "Failed to parse JSON"

    # [공통] 브라우저 닫기
    def _close_chrome_processes(self):
        """모든 Chrome 프로세스를 종료합니다."""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    proc.kill()  # Chrome 프로세스를 종료
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    # [공통] 셀레니움 세팅
    def _setup_driver(self):
        try:
            self._close_chrome_processes()

            chrome_options = Options()
            user_data_dir = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data"
            profile = "Default"

            chrome_options.add_argument(f"user-data-dir={user_data_dir}")
            chrome_options.add_argument(f"profile-directory={profile}")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--start-maximized")
            # chrome_options.add_argument("--headless")  # Headless 모드 추가

            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            chrome_options.add_argument(f'user-agent={user_agent}')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            download_dir = os.path.abspath("downloads")
            os.makedirs(download_dir, exist_ok=True)

            chrome_options.add_experimental_option('prefs', {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            script = '''
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' });
            '''
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})

            return driver
        except WebDriverException as e:
            print(f"Error setting up the WebDriver: {e}")
            return None

    # [공통] 브라우저에서 쿠키 가져오기
    def _get_cookies_from_browser(self, url):
        self.driver.get(url)
        cookies = self.driver.get_cookies()

        if not cookies:  # 쿠키가 없는 경우
            return None

        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        return cookie_dict

    # [공통] 에러 메시지 로그
    def _error_chk(self, result):
        if result['error'] == 'Y':
            self.log_signal.emit(result['message'])
            return True
        return False

    # [공통] csv 남은 데이터 처리
    def _remain_data_set(self):
        # 남은 데이터 저장
        if self.result_list:
            self._save_to_csv_append(self.result_list)

        # CSV 파일을 엑셀 파일로 변환
        try:
            excel_file_name = self.file_name.replace('.csv', '.xlsx')  # 엑셀 파일 이름으로 변경
            self.log_signal.emit(f"CSV 파일을 엑셀 파일로 변환 시작: {self.file_name} → {excel_file_name}")
            df = pd.read_csv(self.file_name)  # CSV 파일 읽기
            df.to_excel(excel_file_name, index=False)  # 엑셀 파일로 저장

            # 마지막 세팅
            pro_value = 1000000
            self.progress_signal.emit(self.before_pro_value, pro_value)
            self.log_signal.emit(f"엑셀 파일 변환 완료: {excel_file_name}")

        except Exception as e:
            self.log_signal.emit(f"엑셀 파일 변환 실패: {e}")

    # [공통] csv 데이터 추가
    def _save_to_csv_append(self, results):
        self.log_signal.emit("CSV 저장 시작")

        try:
            # 파일이 존재하는지 확인
            if not os.path.exists(self.file_name):
                # 파일이 없으면 새로 생성 및 저장
                df = pd.DataFrame(results)
                df.to_csv(self.file_name, index=False, encoding='utf-8-sig')

                self.log_signal.emit(f"새 CSV 파일 생성 및 저장 완료: {self.file_name}")
            else:
                # 파일이 있으면 append 모드로 데이터 추가
                df = pd.DataFrame(results)
                df.to_csv(self.file_name, mode='a', header=False, index=False, encoding='utf-8-sig')
                self.log_signal.emit(f"기존 CSV 파일에 데이터 추가 완료: {self.file_name}")

        except Exception as e:
            # 예기치 않은 오류 처리
            self.log_signal.emit(f"CSV 저장 실패: {e}")

    # [공통] 프로그램 중단
    def stop(self):
        if not self.running:
            return  # 이미 중단된 경우 중복 실행 방지

        self.running = False  # 실행 상태 변경
        self._remain_data_set()

        if self.driver:
            try:
                self.driver.quit()  # 브라우저 정상 종료
                if self.driver.service.process:
                    self.driver.service.process.wait()  # 프로세스가 완전히 종료될 때까지 대기 (선택적)
            except Exception as e:
                self.log_signal.emit(f"Selenium 종료 중 예외 발생: {e}")

        self.quit()  # QThread 이벤트 루프 종료 요청
        self.wait()  # QThread가 완전히 종료될 때까지 대기
        self.finally_finished_signal.emit('크롤링 종료 및 자원해재 완료!')