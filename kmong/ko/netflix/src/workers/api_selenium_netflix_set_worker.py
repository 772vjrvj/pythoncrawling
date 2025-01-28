import os
import random
import re
import ssl
import time
import pandas as pd
import psutil
import requests
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

ssl._create_default_https_context = ssl._create_unverified_context


# API
class ApiNetflixSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)  # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float)  # 진행률 업데이트를 전달하는 시그널
    progress_end_signal = pyqtSignal()   # 종료 시그널

    def __init__(self, url_list, parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 객체 저장
        self.url_list = url_list  # URL을 클래스 속성으로 저장
        self.cookies = None
        self.running = True  # 실행 상태 플래그 추가

        # 현재 시간을 'yyyymmddhhmmss' 형식으로 가져오기
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")

        self.file_name = f"넷플릭스_{current_time}.csv"

        if len(self.url_list) <= 0:
            self.log_signal.emit(f'등록된 url이 없습니다.')
        else:
            self.driver = self.setup_driver()


    def close_chrome_processes(self):
        """모든 Chrome 프로세스를 종료합니다."""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    proc.kill()  # Chrome 프로세스를 종료
                    # print(f"종료된 프로세스: {proc.info['name']} (PID: {proc.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass


    # 브라우저에서 쿠키를 가져오는 함수
    def get_cookies_from_browser(self, url):
        self.driver.get(url)
        cookies = self.driver.get_cookies()

        if not cookies:  # 쿠키가 없는 경우
            return None

        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        return cookie_dict


    def setup_driver(self):
        try:

            self.close_chrome_processes()

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
            chrome_options.add_argument("--headless")  # Headless 모드 추가

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


    def on_netflix_login(self):
        try:
            netflix_url = "https://www.netflix.com"

            # 필요한 쿠키 키 목록
            required_cookies = [
                "profilesNewSession",
                "NetflixId",
                "OptanonConsent",
                "SecureNetflixId",
                "flwssn",
                "nfvdid"
            ]

            cookies = self.get_cookies_from_browser(netflix_url)

            if all(key in cookies for key in required_cookies):
                self.cookies = cookies
                self.log_signal.emit("★ 유료 결제 회원 확인.")

            if cookies is None:
                self.log_signal.emit("로그인 후 프로그램을 다시 실행하세요.")
                self.driver.quit()
                return False
            else:
                self.cookies = cookies
                self.log_signal.emit("★ 쿠키 확인 성공.")
                self.log_signal.emit("※※※※ ★유료 결제 회원과 ★쿠키가 모두 성공해야 정상적인 크롤링이 진행됩니다.")
                self.driver.quit()
                return True

        except Exception as e:
            self.log_signal.emit(f"넷플릭스 로그인 중 에러 발생 : {e}")
            self.driver.quit()
            return False


    def run(self):
        if len(self.url_list) > 0:
            login = self.on_netflix_login()
            if login:
                self.log_signal.emit("크롤링 시작")
                result_list = []
                for idx, url in enumerate(self.url_list, start=1):
                    if not self.running:  # 실행 상태 확인
                        self.log_signal.emit("크롤링이 중지되었습니다.")
                        break
                    # 100개의 항목마다 임시로 엑셀 저장
                    if (idx - 1) % 10 == 0 and result_list:
                        self.save_to_csv_append(result_list)  # 임시 엑셀 저장 호출
                        self.log_signal.emit(f"엑셀 {idx - 1}개 까지 임시저장")
                        result_list = []  # 저장 후 초기화

                    result = {
                        "url": url,
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
                    soup = self.fetch_place_info(url, result)
                    error_chk = self.error_chk(result)

                    if soup and not error_chk:
                        self.extract_netflix_data(soup, result)
                        self.log_signal.emit(f'번호 : {idx}, 1차 결과 : {result}')
                        error_chk = self.error_chk(result)

                        # 'watch'가 있는지 확인
                        if 'watch' in url:
                            if not error_chk:
                                meta_data = self.get_episode_data(url, result)

                                if meta_data and (episode_data := self.get_episode_json(meta_data)):
                                    result["episode_synopsis"] = episode_data.get('synopsis', "")
                                    result["episode_title"] = episode_data.get('title', "")
                                    result["episode_seq"] = f"{episode_data.get('seq', '')}화"
                                    result["episode_season"] = f"시즌{episode_data.get('episode_season', '')}"
                                else:
                                    result['error'] = 'Y'
                                    result['message'] = '에피소드 데이터를 불러오지 못했습니다.'

                                error_chk = self.error_chk(result)
                                if not error_chk:
                                    result['success'] = 'O'
                        else:
                            result['success'] = 'O'

                    self.log_signal.emit(f'번호 : {idx}, 데이터 : {result}')
                    pro_value = (idx / len(self.url_list)) * 1000000
                    self.progress_signal.emit(pro_value)
                    result_list.append(result)
                    time.sleep(random.uniform(2, 3))

                # 남은 데이터 저장
                if result_list:
                    self.save_to_csv_append(result_list)

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
                self.log_signal.emit("로그인 실패.")
        else:
            self.log_signal.emit("url를 입력하세요.")


    def error_chk(self, result):
        if result['error'] == 'Y':
            self.log_signal.emit(result['message'])
            return True
        return False


    def get_episode_json(self, meta_data):
        # 'video' 키에서 'seasons' 배열 가져오기
        seasons = meta_data.get("video", {}).get("seasons", [])
        currentEpisode = meta_data.get("video", {}).get("currentEpisode")


        # seasons 배열 순회
        for index, season in enumerate(seasons, start=1):
            episodes = season.get("episodes", [])

            # episodes 배열 순회
            for episode in episodes:
                if episode.get("episodeId") == currentEpisode:
                    episode['episode_season'] = index
                    return episode  # 조건에 맞는 객체 반환

        return None  # 조건에 맞는 객체가 없으면 None 반환


    def get_episode_data(self, url, result):
        match = re.search(r'\/(\d+)$', url)
        if match:
            last_number = match.group(1)
        else:
            result['message'] = '잘못된 URL 입니다.'
            result['error'] = 'Y'
            return None

        main_url = f"https://www.netflix.com/nq/website/memberapi/release/metadata?movieid={last_number}"

        headers = {
            "authority": "www.netflix.com",
            "method": "GET",
            "path": f"/nq/website/memberapi/release/metadata?movieid={last_number}",
            "scheme": "https",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "referer": f"https://www.netflix.com/watch/{last_number}",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
        }

        max_retries = 3  # 최대 재시도 횟수
        attempts = 0

        while attempts <= max_retries:
            try:
                response = requests.get(main_url, headers=headers, cookies=self.cookies)
                response.raise_for_status()  # HTTP 오류 발생 시 예외 처리

                # 응답 JSON 파싱 및 출력
                if response.status_code == 200:
                    return response.json()
                else:
                    result['error'] = 'Y'
                    result['message'] = f"json 파싱 에러"
                    return None
            except requests.exceptions.RequestException as e:
                attempts += 1
                if attempts > max_retries:
                    result['error'] = 'Y'
                    result['message'] = f"서버 호출 에러, 최대 재시도 횟수를 초과했습니다.: {e}"
                    return None
                time.sleep(2)  # 2초 대기 후 재시도


    def save_to_csv_append(self, results):
        self.log_signal.add_log("CSV 저장 시작")

        try:
            # 파일이 존재하는지 확인
            if not os.path.exists(self.file_name):
                # 파일이 없으면 새로 생성 및 저장
                df = pd.DataFrame(results)
                df.to_csv(self.file_name, index=False)
                self.log_signal.add_log(f"새 CSV 파일 생성 및 저장 완료: {self.file_name}")
            else:
                # 파일이 있으면 append 모드로 데이터 추가
                df = pd.DataFrame(results)
                df.to_csv(self.file_name, mode='a', header=False, index=False)
                self.log_signal.add_log(f"기존 CSV 파일에 데이터 추가 완료: {self.file_name}")

        except Exception as e:
            # 예기치 않은 오류 처리
            self.log_signal.add_log(f"CSV 저장 실패: {e}")


    def fetch_place_info(self, url, result):
        match = re.search(r'\/(\d+)$', url)
        if match:
            last_number = match.group(1)
        else:
            result['message'] = '잘못된 URL 입니다.'
            result['error'] = 'Y'
            return None

        headers = {
            "authority": "www.netflix.com",
            "method": "GET",
            "path": f"/kr/title/{last_number}",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": "\"\"",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-platform-version": "\"10.0.0\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

        max_retries = 3  # 최대 재시도 횟수
        attempts = 0

        while attempts <= max_retries:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # HTTP 오류 발생 시 예외 처리

                # 만약 404 오류가 발생하면 result에 메시지를 설정하고 종료
                if response.status_code == 404:
                    result['error'] = 'Y'
                    result['message'] = '404 죄송합니다. 해당 페이지를 찾을 수 없습니다. 홈페이지로 이동해 다양한 콘텐츠를 만나보세요.'
                    return None

                soup = BeautifulSoup(response.text, "html.parser")

                # main_container 찾기
                try:
                    main_container = soup.find("div", class_="default-ltr-cache-kiz1b3 em9qa8x3")
                    if not main_container:
                        result['error'] = 'Y'
                        result['message'] = f"페이지 로드 실패."
                        raise Exception("페이지 로드 실패.")
                except Exception as e:
                    attempts += 1
                    if attempts > max_retries:
                        result['error'] = 'Y'
                        result['message'] = f"서버 호출 에러, 최대 재시도 횟수를 초과했습니다.: {e}"
                        return None
                    time.sleep(2)  # 2초 대기 후 재시도
                    continue  # 재시도하려면 continue로 반복문을 다시 실행

                return soup

            except requests.exceptions.RequestException as e:
                # 404을 제외한 다른 오류가 발생하면 처리
                if response.status_code == 404:
                    # 404 오류 처리 - 메시지 출력하고 종료
                    result['error'] = 'Y'
                    result['message'] = '404 죄송합니다. 해당 페이지를 찾을 수 없습니다. 홈페이지로 이동해 다양한 콘텐츠를 만나보세요.'
                    return None
                else:
                    attempts += 1
                    if attempts > max_retries:
                        result['error'] = 'Y'
                        result['message'] = f"서버 호출 에러, 최대 재시도 횟수를 초과했습니다.: {e}"
                        return None
                    time.sleep(2)  # 2초 대기 후 재시도


    def extract_netflix_data(self, soup, result):
        """
        Netflix 페이지에서 필요한 정보를 추출하여 객체로 반환.

        Args:
            soup (BeautifulSoup): HTML 파싱된 BeautifulSoup 객체.

        Returns:
            dict: 추출된 정보를 담은 객체.
        """
        try:
            # 메인 컨테이너
            main_container = soup.find("div", class_="default-ltr-cache-kiz1b3 em9qa8x3")

            # Title (h2 태그)
            title_tag = main_container.find("h2", class_="default-ltr-cache-11jsu7c euy28770")
            result["title"] = title_tag.text.strip() if title_tag else ""

            # Year, Season, Rating, Genre
            details_container = main_container.find("div", class_="default-ltr-cache-56ff39 em9qa8x2")
            details_list = details_container.find("ul", class_="default-ltr-cache-1xty6x8 e32lqeb1") if details_container else None

            if details_list:

                li_tags = details_list.find_all("li", class_="default-ltr-cache-1payn3k e32lqeb0")

                if len(li_tags) == 4:

                    result["year"] = li_tags[0].text.strip() if len(li_tags) > 0 else ""

                    season_text = li_tags[1].text.strip() if len(li_tags) > 1 else ""
                    season_text = season_text.replace('\u2068', '').replace('\u2069', '')
                    result["season"] = season_text

                    rating_text = li_tags[2].text.strip() if len(li_tags) > 2 else ""
                    rating_text = rating_text.replace('\u2068', '').replace('\u2069', '')
                    result["rating"] = rating_text

                    genre_text = li_tags[3].text.strip() if len(li_tags) > 3 else ""
                    genre_text = genre_text.replace('\u2068', '').replace('\u2069', '')
                    result["genre"] = genre_text

                if len(li_tags) == 3:

                    result["year"] = li_tags[0].text.strip() if len(li_tags) > 0 else ""

                    rating_text = li_tags[1].text.strip() if len(li_tags) > 1 else ""
                    rating_text = rating_text.replace('\u2068', '').replace('\u2069', '')
                    result["rating"] = rating_text

                    genre_text = li_tags[2].text.strip() if len(li_tags) > 2 else ""
                    genre_text = genre_text.replace('\u2068', '').replace('\u2069', '')
                    result["genre"] = genre_text

            else:
                result.update({"year": "", "season": "", "rating": "", "genre": ""})


            # Summary (줄거리)
            summary_container = main_container.find("div", class_="default-ltr-cache-18fxwnx em9qa8x0")
            summary_tag = summary_container.find("div", class_="default-ltr-cache-1y7pnva em9qa8x1") if summary_container else None
            summary_span = summary_tag.find("span", class_="default-ltr-cache-v92n84 euy28770") if summary_tag else None
            result["summary"] = summary_span.text.strip() if summary_span else ""

            # Cast and Director
            cast_director_container = summary_container.find("div", class_="default-ltr-cache-1wmy9hl ehsrwgm0") if summary_container else None
            cast_divs = cast_director_container.find_all("div", class_="default-ltr-cache-eywhmi ehsrwgm1") if cast_director_container else []

            # Cast (출연진)
            if len(cast_divs) > 0:
                cast_span = cast_divs[0].find_all("span", class_="default-ltr-cache-3z6sz6 euy28770")
                result["cast"] = cast_span[0].text.strip()
            else:
                result["cast"] = ""

            # Director (감독)
            if len(cast_divs) > 1:
                director_span = cast_divs[1].find_all("span", class_="default-ltr-cache-3z6sz6 euy28770")
                result["director"] = director_span[0].text.strip()
            else:
                result["director"] = ""
        except AttributeError as e:
            result['error'] = 'Y'
            result['message'] = f"데이터 추출 중 오류 발생: {e}"

    # 프로그램 중단
    def stop(self):
        """스레드 중지를 요청하는 메서드"""
        self.running = False
