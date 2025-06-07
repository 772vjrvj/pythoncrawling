import random
import ssl
import pyautogui  # 현재 모니터 해상도 가져오기 위해 사용
import pygetwindow as gw
import time
import threading
import os
import pandas as pd
import pyperclip
import urllib.parse
import re
import subprocess

from PyQt5.QtCore import pyqtSignal
from bs4 import BeautifulSoup
from src.utils.file_utils import FileUtils
from src.workers.api_base_worker import BaseApiWorker

class ApiCoupangSetLoadWorker(BaseApiWorker):

    def __init__(self, setting):
        super().__init__()

        self.result_list = []
        self.current_cnt = 0
        self.current_total_cnt = 0
        self.urls_list = []
        self.keyword = ''
        self.current_url = ''
        self.before_pro_value = 0
        self.file_driver = None
        self.excel_driver = None
        self.running = True
        self.csv_filename = ""
        self.page = 1
        self.site_name = '쿠팡'
        self.columns = ["상품명", "상호명","사업장소재지", "연락처", "URL", "PAGE", "키워드"]
        self.base_url = "https://www.coupang.com"
        self.current_page = 0
        # ✅ 설정값 세팅
        self.html_source_delay_time = self._get_setting_value(setting, "html_source_delay_time")
        self.chrome_delay_time = self._get_setting_value(setting, "chrome_delay_time")


    def _get_setting_value(self, setting_list, code_name):
        for item in setting_list:
            if item.get("code") == code_name:
                return item.get("value")
        return None  # 또는 기본값 0 등



    def init(self):
        
        self.log_signal_func("드라이버 세팅 ========================================")
        self.log_signal_func(f"제품 딜레이 : {self.html_source_delay_time}")
        self.log_signal_func(f"크롬 딜레이 : {self.chrome_delay_time}")

        self.file_driver = FileUtils(self.log_signal_func)

        event = threading.Event()  # OK 버튼 누를 때까지 대기할 이벤트 객체

        # 사용자에게 메시지 창 요청
        self.msg_signal_func("쿠팡 로그인 -> 페이지 검색 후 확인을 눌러주세요", "info", event)

        # 사용자가 OK를 누를 때까지 대기
        self.log_signal_func("📢 사용자 입력 대기 중...")
        event.wait()  # 사용자가 OK를 누르면 해제됨

        # 현재 해상도 가져오기
        screen_width, screen_height = pyautogui.size()

        # 'Chrome'이 포함된 창 리스트 가져오기 (visible 속성 사용)
        chrome_windows = [w for w in gw.getWindowsWithTitle('Chrome') if w.visible]

        if chrome_windows:
            chrome_win = chrome_windows[0]  # 첫 번째 크롬 창 선택
            chrome_win.moveTo(0, 0)
            chrome_win.resizeTo(screen_width // 2, screen_height)
            self.log_signal_func("✅ 크롬 창을 왼쪽 절반으로 이동시켰습니다.")
        else:
            self.log_signal_func("❌ 크롬 창을 찾을 수 없습니다.")

        pyautogui.sleep(1)  # 창 포커싱 대기
        pyautogui.press('home')  # 또는 아래처럼 마우스 휠로도 가능


    # 메인
    def main(self):

        try:
            self.csv_filename = self.file_driver.get_csv_filename(self.site_name)
            df = pd.DataFrame(columns=self.columns)
            df.to_csv(self.csv_filename, index=False, encoding="utf-8-sig")

            # ✅ 첫 페이지 크롤링
            self.log_signal_func(f"메인 시작")
            self.log_signal_func(f"▶ 페이지 {self.page} 진행")
            self.main_crawl()

            # ✅ 다음 페이지부터 자동 반복
            while True:
                if not self.running:  # 실행 상태 확인
                    self.log_signal_func("크롤링이 중지되었습니다.")
                    break

                self.log_signal_func(f'\n\n\n\n')
                self.log_signal_func(f'■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■')
                self.page += 1

                # ✅ current_url의 page 값 수정
                parsed = urllib.parse.urlparse(self.current_url)
                query = urllib.parse.parse_qs(parsed.query)

                keyword_encoded = query.get("q", [""])[0]
                self.keyword = urllib.parse.unquote(keyword_encoded)

                query['page'] = [str(self.page)]

                new_query = urllib.parse.urlencode(query, doseq=True)
                self.current_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"

                # ✅ 브라우저 자동 이동
                pyautogui.hotkey('ctrl', 'l')
                time.sleep(0.3)
                pyperclip.copy(self.current_url)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.3)
                pyautogui.press('enter')
                time.sleep(3)  # 페이지 로딩 대기

                self.log_signal_func(f"▶ 페이지 {self.page} 진행")
                rs = self.main_crawl()
                if not rs:
                    break

                if self.page % 2 == 0:
                    self.log_signal_func(f"감지봇 우회 크롬 강제종료")
                    # 크롬 강제 종료
                    os.system("taskkill /f /im chrome.exe")
                    self.log_signal_func(f"크롬 종료 대기중 입니다. {self.chrome_delay_time}초 후에 열립니다. 다른 작업을 하지마세요.")
                    self.request_chrome_delay()  # 카운트다운 팝업 요청 + sleep
                    # 크롬 실행 (사용자 프로필 유지)
                    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                    subprocess.Popen([chrome_path, self.current_url])
                    time.sleep(2)  # 쿠팡 로딩 대기
                    self.log_signal_func(f"크롬 시작")
                
            if self.result_list:
                df = pd.DataFrame(self.result_list, columns=self.columns)
                df.to_csv(self.csv_filename, mode='a', header=False, index=False, encoding="utf-8-sig")
                self.result_list.clear()

        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")


    # 마무리
    def destroy(self):
        self.progress_signal.emit(self.before_pro_value, 1000000)
        self.log_signal_func("=============== 크롤링 종료중...")
        time.sleep(5)
        self.log_signal_func("=============== 크롤링 종료")
        self.progress_end_signal.emit()


    # 메인 크롤링
    def main_crawl(self):

        # 왼쪽 끝으로 이동
        pyautogui.moveTo(10, 10)
        # 클릭
        pyautogui.click()
        time.sleep(0.5)

        # URL 창 활성화
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.3)
        # URL 복사
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.3)

        if self.page == 1:
            # URL 가져오기
            self.current_url = pyperclip.paste()
            self.log_signal_func(f"📋 현재 URL 확인: {self.current_url}")

            parsed = urllib.parse.urlparse(self.current_url)
            query = urllib.parse.parse_qs(parsed.query)

            keyword_encoded = query.get("q", [""])[0]
            self.keyword = urllib.parse.unquote(keyword_encoded)

        # 스크롤을 위해 내부 html 링크나 버튼 없는 곳 클릭
        pyautogui.moveTo(300, 400)
        pyautogui.click()
        time.sleep(0.3)

        soup = self.get_soup()

        urls = self.extract_product_urls(soup)

        self.current_total_cnt = len(urls)

        if self.urls_list and self.urls_list[-1] == urls:
            return False
        else:
            self.urls_list.append(urls)

        for i, url in enumerate(urls, start=0):
            if not self.running:  # 실행 상태 확인
                self.log_signal_func("크롤링이 중지되었습니다.")
                break
            self.current_cnt += 1
            self.log_signal_func(f'\n\n')
            self.log_signal_func(f'==================================================')
            self.log_signal_func(f'PAGE : {self.page} ({i+1}/{self.current_total_cnt})')
            self.log_signal_func(f'누적 상품수 : {self.current_cnt}')
            self.data_detail_crawl(i, url)
            self.log_signal_func(f'==================================================')

        return True


    # 메인 페이지 url 얻기
    def extract_product_urls(self, soup):

        ul = soup.find('ul', id='product-list')
        if not ul:
            self.log_signal_func("❌ 'product-list' UL 태그를 찾을 수 없습니다.")
            return []

        urls = set()

        for li in ul.find_all('li', attrs={"data-sentry-component": "ProductItem"}):
            a_tag = li.find('a', href=True)
            if a_tag:
                href = a_tag['href']
                if not href.startswith("http"):
                    href = self.base_url + href
                urls.add(href)

        url_list = sorted(list(urls))

        self.log_signal_func(f"✅ 총 {len(url_list)}개 상품 URL 추출됨")
        return url_list

    
    # 상세상품 데이터 크롤링
    def data_detail_crawl(self, i, url):
        # ✅ 브라우저에 URL 입력 후 이동
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.3)
        pyperclip.copy(url)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(3)

        soup = self.get_soup()

        seller_info = {
            "상품명": "",
            "상호명": "",
            "사업장소재지": "",
            "연락처": "",
            "URL": url,
            "PAGE": self.page,
            "키워드": self.keyword
        }

        # ✅ 상품명 추출
        title_tag = soup.find("h1", attrs={"data-sentry-component": "ProductTitle"})
        if title_tag:
            seller_info["상품명"] = title_tag.get_text(strip=True)
        else:
            self.log_signal_func("❌ 상품명을 찾을 수 없습니다.")

        # ✅ 판매자 정보 테이블 추출
        container = soup.find("div", class_="product-item__table product-seller")
        if container:
            table = container.find("table", class_=re.compile(r"prod-delivery-return-policy-table"))
            if table:
                rows = table.find_all("tr")
                for row in rows:
                    ths = row.find_all("th")
                    tds = row.find_all("td")

                    for i in range(min(len(ths), len(tds))):
                        label = ths[i].get_text(strip=True)
                        value = tds[i].get_text(strip=True)

                        if "상호" in label:
                            seller_info["상호명"] = value
                        elif "소재지" in label:
                            seller_info["사업장소재지"] = value
                        elif "연락처" in label:
                            seller_info["연락처"] = value



        self.log_signal_func(f'제품정보 : {seller_info}')
        self.log_signal_func(f'연락처 :{seller_info['연락처']}')

        # ✅ 중복 체크 후 추가
        self.result_list.append(seller_info)

        if len(self.result_list) % 5 == 0:
            df = pd.DataFrame(self.result_list, columns=self.columns)
            if not os.path.exists(self.csv_filename):
                df.to_csv(self.csv_filename, mode='a', header=True, index=False, encoding="utf-8-sig")
            else:
                df.to_csv(self.csv_filename, mode='a', header=False, index=False, encoding="utf-8-sig")
            self.result_list.clear()

        time.sleep(random.uniform(5, 7))
        

    # soup 얻기
    def get_soup(self):

        # ✅ 1단계: 아래 방향키로 20번 빠르게 스크롤
        for _ in range(20):
            pyautogui.press('pagedown')
            time.sleep(0.3)  # 살짝 빠르게, 자연스러운 스크롤

        # ✅ 2단계: 마지막에 스크롤 끝까지 내리기
        for _ in range(3):
            pyautogui.press('end')
            time.sleep(0.3)  # 로딩 대기 시간

        pyautogui.hotkey('ctrl', 'u')
        time.sleep(random.uniform(self.html_source_delay_time, self.html_source_delay_time + 2))
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'w')
        time.sleep(0.5)

        html_source = pyperclip.paste()
        self.log_signal_func(f"HTML 길이: {len(html_source)}")
        self.log_signal_func(f"시작부분: {html_source[:200]}")

        soup = BeautifulSoup(html_source, 'html.parser')

        return soup


    # 크롬 딜레이 카운트
    def request_chrome_delay(self):
        # 👉 UI에게 카운트다운 팝업 요청
        self.show_countdown_signal_func(self.chrome_delay_time)

        # 👉 실제 대기는 worker가 직접 진행
        for remaining in range(self.chrome_delay_time, 0, -1):
            # self.log_signal_func(f"⏳ 남은 시간: {remaining}초")
            time.sleep(1)


    # 정지    
    def stop(self):
        self.running = False

