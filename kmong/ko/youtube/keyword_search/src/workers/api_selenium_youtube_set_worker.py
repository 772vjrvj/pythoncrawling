from PyQt5.QtCore import QThread, pyqtSignal
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
import pandas as pd
from datetime import datetime
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from tkinter import messagebox
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import ssl
import psutil


ssl._create_default_https_context = ssl._create_unverified_context


# API
class ApiYoutubeSetLoadWorker(QThread):
    log_signal = pyqtSignal(str)  # 로그 메시지를 전달하는 시그널
    progress_signal = pyqtSignal(float)  # 진행률 업데이트를 전달하는 시그널

    def __init__(self, search_keyword, parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 객체 저장
        self.search_keyword = search_keyword  # URL을 클래스 속성으로 저장
        self.cookies = None

        # 현재 시간을 'yyyymmddhhmmss' 형식으로 가져오기
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")

        self.file_name = f"유튜브_{current_time}.xlsx"

        if search_keyword is None:
            self.log_signal.emit(f'검색어가 없습니다.')
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




    def run(self):
        self.parent.add_log(f"클롤링 시작. 키워드 : {self.search_keyword}")
        url = f"https://www.youtube.com/results?search_query={self.search_keyword}"


        self.driver.get(url)

        # 로딩 처리
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        dats_list = []
        # 스크롤 내리기
        for i in range(1):  # 두 번 스크롤
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)

            video_elements = self.driver.find_elements(By.XPATH, ".//ytd-video-renderer[@class='style-scope ytd-item-section-renderer']")

            # href 속성 추출
            for video in video_elements:
                try:
                    # a 태그(id="thumbnail") 찾기
                    anchor = video.find_element(By.XPATH, ".//a[@id='thumbnail' and contains(@class, 'yt-simple-endpoint')]")
                    link = anchor.get_attribute('href') if anchor else ""

                    # 동영상 제목 (a 태그 id="video-title")
                    title_element = video.find_element(By.XPATH, ".//a[@id='video-title' and contains(@class, 'yt-simple-endpoint')]")
                    title = title_element.get_attribute('title') if title_element else ""

                    # 채널명 (ytd-channel-name > a 태그)
                    channel_element = video.find_element(By.XPATH, ".//div[@id='channel-info']//a[@class='yt-simple-endpoint style-scope yt-formatted-string']")
                    channel_name = channel_element.text if channel_element else ""

                    dats_list.append({"입력한 검색어": self.search_keyword, "영상제목": title, "검색어에 잡힌링크": link, "유튜브채널명": channel_name})

                except NoSuchElementException:
                    self.parent.add_log("썸네일 링크를 찾을 수 없습니다. 다음 요소로 넘어갑니다.")

        self.parent.add_log(f'전체 목록: {dats_list}')
        self.driver.quit()
        self.save_to_excel(dats_list)


    def save_to_excel(self, results):
        self.parent.add_log("엑셀 저장 시작")

        try:
            # 파일이 존재하는지 확인
            if os.path.exists(self.file_name):
                # 파일이 있으면 기존 데이터 읽어오기
                df_existing = pd.read_excel(self.file_name)

                # 새로운 데이터를 DataFrame으로 변환
                df_new = pd.DataFrame(results)

                # 기존 데이터의 마지막 행 인덱스를 기준으로 새로운 데이터의 추가 범위 계산
                last_existing_index = df_existing.shape[0]  # 기존 데이터의 행 개수

                # 새로운 데이터에서 추가할 부분만 선택 (기존 데이터 이후의 데이터)
                df_to_add = df_new.iloc[last_existing_index:]

                # 기존 데이터와 추가할 데이터 합치기
                df_combined = pd.concat([df_existing, df_to_add], ignore_index=True)

                # 엑셀 파일에 데이터 덧붙이기 (index는 제외)
                df_combined.to_excel(self.file_name, index=False)
            else:
                # 파일이 없으면 새로 생성
                df = pd.DataFrame(results)
                df.to_excel(self.file_name, index=False)

            self.parent.add_log(f"엑셀 저장 완료: {self.file_name}")

        except Exception as e:
            # 예기치 않은 오류 처리
            self.parent.add_log(f"엑셀 저장 실패: {e}")

