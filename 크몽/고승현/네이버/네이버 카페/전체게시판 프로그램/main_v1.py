import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QDateEdit, QMessageBox, QProgressBar, QTextEdit, QSpinBox
from PyQt5.QtCore import QDate, QThread, pyqtSignal, Qt
import time
import requests
import re
from datetime import datetime, timedelta
import pandas as pd
import random
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urlencode

global_cookies = {}

# 셀레니움 드라이버 세팅
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver

# 네이버 로그인
class LoginThread(QThread):
    login_complete = pyqtSignal(dict, str)  # 로그인 성공 시 쿠키와 메시지를 전달

    def run(self):
        global global_cookies  # 전역 변수를 사용하기 위해 global 키워드 사용
        try:
            driver = setup_driver()
            driver.get("https://nid.naver.com/nidlogin.login")  # 네이버 로그인 페이지로 이동

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "id"))
            )

            # 로그인 여부를 주기적으로 체크
            logged_in = False
            max_wait_time = 300  # 최대 대기 시간 (초)
            start_time = time.time()

            while not logged_in:
                time.sleep(1)
                elapsed_time = time.time() - start_time

                if elapsed_time > max_wait_time:
                    warning_message = "로그인 실패: 300초 내에 로그인하지 않았습니다."
                    self.login_complete.emit({}, warning_message)
                    break

                cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

                if 'NID_AUT' in cookies and 'NID_SES' in cookies:
                    success_message = "로그인 성공: 정상 로그인 되었습니다."
                    global_cookies = cookies
                    self.login_complete.emit(cookies, success_message)
                    logged_in = True
                    break

        except Exception as e:
            error_message = f"로그인 중 오류가 발생했습니다: {str(e)}"
            self.login_complete.emit({}, error_message)
        finally:
            driver.quit()

# 로그인 초기화
def reset_login():
    global global_cookies
    global_cookies = {}
    window.log_output.append("로그인 정보가 초기화되었습니다.")
    QMessageBox.information(None, "초기화", "로그인 정보가 초기화되었습니다.")

# 새롭게 정의된 함수: 기간 입력에 따른 요청 처리
def search_articles_by_period(cafe_url, query, searchdate, min_read_count):
    try:
        cafe_id = get_cafe_id(cafe_url)
        if not cafe_id:
            return None, "카페 ID를 가져올 수 없습니다."

        page = 1
        all_articles = []  # 모든 페이지에서 수집한 결과를 저장할 리스트

        while True:
            articles = fetch_naver_cafe_articles(
                clubid=cafe_id,
                searchdate=searchdate,
                searchBy=1,
                query=query,
                sortBy='date',
                userDisplay=50,
                media=0,
                option=0,
                page=page,
                min_read_count=min_read_count
            )

            if not articles:  # articles가 빈 리스트이면 반복 종료
                break

            all_articles.extend(articles)  # 수집한 기사들을 리스트에 추가
            page += 1  # 다음 페이지로 넘어감

        # 결과를 엑셀 파일로 저장
        if all_articles:
            df = pd.DataFrame(all_articles)
            now = datetime.now().strftime('%Y%m%d%H%M')
            file_name = f"cafe_articles_{now}.xlsx"
            df.to_excel(file_name, index=False)
            print(f"결과가 {file_name}에 저장되었습니다.")
            return file_name, None
        else:
            print("수집된 결과가 없습니다.")
            return None, "수집된 결과가 없습니다."

    except Exception as e:
        print(f"검색 중 오류 발생: {e}")
        return None, str(e)

# 기존 함수와 연결된 fetch_naver_cafe_articles 호출
def fetch_naver_cafe_articles(clubid, searchdate, searchBy, query, sortBy, userDisplay, media, option, page, min_read_count):
    time.sleep(random.uniform(2, 4))
    # 기본 URL
    base_url = "https://cafe.naver.com/ArticleSearchList.nhn"

    # URL 파라미터 설정 (쿼리 파라미터에 한글을 그대로 사용)
    params = {
        'search.clubid': clubid,
        'search.searchdate': searchdate,
        'search.searchBy': searchBy,
        'search.query': query,  # 한글 검색어를 그대로 사용
        'search.defaultValue': 1,
        'search.includeAll': '',
        'search.exclude': '',
        'search.include': '',
        'search.exact': '',
        'search.sortBy': sortBy,
        'userDisplay': userDisplay,
        'search.media': media,
        'search.option': option,
        'search.page': page
    }

    # 전체 URL 생성
    full_url = f"{base_url}?{urlencode(params, encoding='euc-kr')}"  # 'euc-kr' 인코딩 사용
    print(f"Requesting URL: {full_url}")

    # 헤더 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }

    # HTTP 요청 보내기
    response = requests.get(full_url, headers=headers, cookies=global_cookies)

    # 응답 인코딩을 'euc-kr'로 설정
    response.encoding = 'euc-kr'

    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(response.text, 'html.parser')

    # 클래스 이름이 'article-board m-tcol-c'인 두 번째 요소 찾기
    article_boards = soup.find_all('div', class_='article-board m-tcol-c')

    articles = []

    # 두 번째 'article-board m-tcol-c' 요소에서 tr 태그를 찾기
    if len(article_boards) >= 2:
        second_board = article_boards[1]
        rows = second_board.find_all('tr')

        # 각 tr 태그 내용을 추출하여 articles 리스트에 추가
        for row in rows:
            link_tag = row.find('a', class_='article')
            date_tag = row.find('td', class_='td_date')
            title_tag = link_tag
            view_tag = row.find('td', class_='td_view')

            if link_tag and date_tag and title_tag and view_tag:
                # 조회수를 숫자로 변환
                view_count = int(view_tag.get_text(strip=True).replace(',', ''))

                # 조회수가 min_read_count 이상인 경우만 추가
                if view_count >= min_read_count:
                    article = {
                        "링크": f"https://cafe.naver.com{link_tag['href']}",
                        "포스팅 날짜": date_tag.get_text(strip=True),
                        "제목": title_tag.get_text(strip=True),
                        "조회수": view_count,
                        "키워드": query
                    }
                    articles.append(article)
    else:
        print("두 번째 'article-board m-tcol-c' 요소를 찾을 수 없습니다.")
        return articles

    print(f"articles : {articles}")

    return articles

# 카페 ID 가져오기
def get_cafe_id(cafe_url):
    try:
        club_url = cafe_url.split('/')[-1]
        api_url = f"https://apis.naver.com/cafe-web/cafe2/CafeGateInfo.json?cluburl={club_url}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(api_url, headers=headers, cookies=global_cookies)
        if response.status_code == 200:
            data = response.json()
            cafe_id = data.get("message", {}).get("result", {}).get("cafeInfoView", {}).get("cafeId", None)
            if cafe_id:
                return cafe_id
            else:
                print("카페 ID를 찾을 수 없습니다.")
                return None
        else:
            print(f"API 요청 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"카페 ID를 가져오는 중 오류 발생: {e}")
        return None

# 게시글 목록 가져오기
def get_article_list(cafe_id, query, page, userDisplay, start_date, end_date):
    try:
        url = f"https://apis.naver.com/cafe-web/cafe-mobile/CafeMobileWebArticleSearchListV4"
        params = {
            "cafeId": cafe_id,
            "searchBy": 1,
            "query": query,
            "defaultValue": 1,
            "sortBy": "date",
            "perPage": userDisplay,
            "page": page,
            "adUnit": "MW_CAFE_BOARD",
            "ad": "false",
            "startDate": start_date,
            "endDate": end_date
        }

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, cookies=global_cookies, params=params)

        if response.status_code == 200:
            data = response.json()
            if "message" in data and "result" in data["message"]:
                articles = data["message"]["result"]["articleList"]
                total_articles = data["message"]["result"]["totalArticleCount"]
                return articles, total_articles
            else:
                print("게시글 목록을 가져올 수 없습니다.")
                return [], 0
        else:
            print(f"API 요청 실패: {response.status_code}")
            return [], 0
    except Exception as e:
        print(f"게시글 목록을 가져오는 중 오류 발생: {e}")
        return [], 0


def get_article_list_all(cafe_id, page, userDisplay):
    try:
        url = f"https://apis.naver.com/cafe-web/cafe2/ArticleListV2dot1.json"
        params = {
            "search.clubid": cafe_id,
            "search.queryType": "lastArticle",
            "search.page": page,
            "search.perPage": userDisplay,
            "ad": "false",
            "adUnit": "MW_CAFE_ARTICLE_LIST_RS",
        }

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, cookies=global_cookies, params=params)

        if response.status_code == 200:
            data = response.json()
            if "message" in data and "result" in data["message"]:
                articles = data["message"]["result"]["articleList"]
                return articles, 0
            else:
                print("게시글 목록을 가져올 수 없습니다.")
                return [], 0
        else:
            print(f"API 요청 실패: {response.status_code}")
            return [], 0
    except Exception as e:
        print(f"게시글 목록을 가져오는 중 오류 발생: {e}")
        return [], 0



# 날짜 형식 변환 함수
def parse_date(date_str):
    try:
        date_str = re.sub(r' KST', '', date_str)
        date_obj = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
        return date_obj.strftime('%Y.%m.%d.'), date_obj
    except Exception as e:
        print(f"날짜 형식 변환 중 오류 발생: {e}")
        return "", None

# 검색 스레드 클래스
class SearchThread(QThread):
    progress = pyqtSignal(int, int, int)
    finished = pyqtSignal(str, str)

    def __init__(self, cafe_url, query, period, start_date, end_date, min_read_count):
        super().__init__()
        self.cafe_url = cafe_url
        self.query = query
        self.period = period
        self.start_date = start_date
        self.end_date = end_date
        self.min_read_count = min_read_count
        self.total_articles = 0
        self.results = []
        self.stop_requested = False

    def run(self):
        file_name, error = self.search_articles()
        self.finished.emit(file_name, error)

    def search_articles(self):
        try:
            cafe_id = get_cafe_id(self.cafe_url)
            if not cafe_id:
                return None, "카페 ID를 가져올 수 없습니다."

            userDisplay = 50
            page = 1
            processed_articles = 0

            while not self.stop_requested:
                time.sleep(random.uniform(2, 4))

                if not self.query:
                    articles, total_articles = get_article_list_all(cafe_id, page, userDisplay)
                else:
                    articles, total_articles = get_article_list(cafe_id, self.query, page, userDisplay, self.start_date, self.end_date)

                if not articles:
                    break

                if page == 1:
                    self.total_articles = total_articles

                for article in articles:
                    if self.stop_requested:
                        return self.save_results_to_excel(self.results)

                    subject_clean = re.sub('<[^<]+?>', '', article['subject'])
                    date_str = article.get('addDate')
                    if not date_str:
                        timestamp = article.get('writeDateTimestamp')
                        if timestamp:
                            # 타임스탬프를 datetime 객체로 변환 (밀리초 단위이므로 1000으로 나눕니다)
                            date_obj = datetime.fromtimestamp(timestamp / 1000)
                            # 날짜를 'YYYY.MM.DD.' 형식으로 포맷팅
                            formatted_date = date_obj.strftime('%Y.%m.%d.')
                        else:
                            print(f"Warning: 'addDate'와 'writeDateTimestamp' 필드를 찾을 수 없습니다. 다음 기사로 넘어갑니다.")
                            continue
                    else:
                        formatted_date, date_obj = parse_date(date_str)

                    if self.period and date_obj and self.is_date_outside_period(date_obj):
                        return self.save_results_to_excel(self.results)

                    # self.period 값이 없을 경우에만 날짜 조건을 체크
                    if not self.period and date_obj:
                        # 날짜가 종료일보다 크면 continue
                        if date_obj > datetime.strptime(self.end_date, '%Y%m%d'):
                            continue

                        # 날짜가 시작 날짜보다 작으면 검색 중지
                        if date_obj < datetime.strptime(self.start_date, '%Y%m%d'):
                            return self.save_results_to_excel(self.results)

                    if article['readCount'] >= self.min_read_count:
                        articleId = article['articleId']
                        full_url = f"{self.cafe_url}?iframe_url_utf8=%2FArticleRead.nhn%3Fclubid%3D{cafe_id}%26articleid%3D{articleId}"
                        result = {
                            "키워드": self.query,
                            "조회수": article['readCount'],
                            "제목": subject_clean,
                            "링크": full_url,
                            "포스팅 날짜": formatted_date,
                        }
                        self.results.append(result)

                processed_articles += len(articles)
                page += 1

                progress_percent = int((processed_articles / self.total_articles) * 100) if self.total_articles > 0 else 0
                time_per_request = 3
                estimated_time_remaining = (self.total_articles - processed_articles) * time_per_request // userDisplay
                self.progress.emit(progress_percent, processed_articles, estimated_time_remaining)

            return self.save_results_to_excel(self.results)
        except Exception as e:
            print(f"검색 중 오류 발생: {e}")
            return None, str(e)

    def is_date_outside_period(self, date_obj):
        cutoff_date = None
        if self.period == '1d':
            cutoff_date = datetime.now() - timedelta(days=1)
        elif self.period == '1w':
            cutoff_date = datetime.now() - timedelta(weeks=1)
        elif self.period == '1m':
            cutoff_date = datetime.now() - timedelta(weeks=4)
        elif self.period == '6m':
            cutoff_date = datetime.now() - timedelta(weeks=24)
        elif self.period == '1y':
            cutoff_date = datetime.now() - timedelta(weeks=52)

        return cutoff_date and date_obj < cutoff_date

    def save_results_to_excel(self, results):
        now = datetime.now().strftime('%Y%m%d%H%M')
        file_name = f"cafe_articles_{now}.xlsx"
        df = pd.DataFrame(results)
        df.to_excel(file_name, index=False)
        return file_name, None

    def stop(self):
        self.stop_requested = True

# PyQt5 앱 클래스
class CafeSearchApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('카페 게시글 검색기')
        self.setGeometry(100, 100, 800, 720)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                font-family: Arial, sans-serif;
            }
            QLabel {
                color: #333333;
                font-size: 11px;
                font-weight: bold;
            }
            QLineEdit, QComboBox, QDateEdit, QSpinBox, QTextEdit {
                padding: 4px;
                font-size: 11px;
                border: 1px solid #aaaaaa;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QProgressBar {
                border: 1px solid #aaaaaa;
                border-radius: 5px;
                text-align: center;
                font-size: 11px;
                color: #000000;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 16px;
            }
            QDateEdit QAbstractItemView:enabled {
                color: #000000;
            }
            QDateEdit QAbstractItemView QHeaderView::section {
                color: #000000;
            }
            QDateEdit QAbstractItemView {
                color: #000000;
            }
            QDateEdit QComboBox QAbstractItemView {
                color: #000000; /* 텍스트를 흰색으로 설정 */
            }
            QDateEdit QToolButton {
                color: #000000; /* 텍스트를 흰색으로 설정 */
            }
        """)

        layout = QVBoxLayout()

        hbox1 = QHBoxLayout()
        self.login_button = QPushButton('로그인', self)
        self.login_button.clicked.connect(self.on_login_click)
        self.reset_button = QPushButton('로그인 초기화', self)
        self.reset_button.clicked.connect(self.on_reset_click)
        self.cafe_url_label = QLabel('카페 주소:')
        self.cafe_url_input = QLineEdit(self)
        self.query_label = QLabel('검색어:')
        self.query_input = QLineEdit(self)
        hbox1.addWidget(self.login_button)
        hbox1.addWidget(self.reset_button)
        hbox1.addWidget(self.cafe_url_label)
        hbox1.addWidget(self.cafe_url_input)
        hbox1.addWidget(self.query_label)
        hbox1.addWidget(self.query_input)

        hbox2 = QHBoxLayout()
        self.min_read_count_label = QLabel('최소 조회수:')
        self.min_read_count_input = QSpinBox(self)
        self.min_read_count_input.setRange(0, 1000000)
        self.min_read_count_input.setValue(50)
        self.period_label = QLabel('기간 선택:')
        self.period_combo = QComboBox(self)
        self.period_combo.addItems(['전체기간', '1일', '1주', '1개월', '6개월', '1년', '기간 입력'])
        self.period_combo.currentIndexChanged.connect(self.update_date_edit_status)
        hbox2.addWidget(self.min_read_count_label)
        hbox2.addWidget(self.min_read_count_input)
        hbox2.addWidget(self.period_label)
        hbox2.addWidget(self.period_combo)

        hbox3 = QHBoxLayout()
        self.start_date_label = QLabel('시작 날짜:')
        self.start_date_input = QDateEdit(self)
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_input.setEnabled(False)
        self.end_date_label = QLabel('종료 날짜:')
        self.end_date_input = QDateEdit(self)
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())
        self.end_date_input.setEnabled(False)
        hbox3.addWidget(self.start_date_label)
        hbox3.addWidget(self.start_date_input)
        hbox3.addWidget(self.end_date_label)
        hbox3.addWidget(self.end_date_input)

        hbox4 = QHBoxLayout()
        self.search_button = QPushButton('검색', self)
        self.search_button.clicked.connect(self.on_search_click)
        hbox4.addWidget(self.search_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        self.progress_label = QLabel("", self)
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: black; font-weight: bold;")

        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)

        layout.addLayout(hbox1)
        layout.addLayout(hbox2)
        layout.addLayout(hbox3)
        layout.addLayout(hbox4)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def update_date_edit_status(self):
        if self.period_combo.currentText() == '기간 입력':
            self.start_date_input.setEnabled(True)
            self.end_date_input.setEnabled(True)
        else:
            self.start_date_input.setEnabled(False)
            self.end_date_input.setEnabled(False)

    def on_login_click(self):
        self.log_output.append("로그인 정보를 입력하고 로그인을 완료하세요.")
        self.login_thread = LoginThread()
        self.login_thread.login_complete.connect(self.on_login_complete)
        self.login_thread.start()

    def on_login_complete(self, cookies, message):
        if cookies:
            global global_cookies
            global_cookies = cookies
            self.log_output.append("로그인 성공: 네이버 계정으로 로그인되었습니다.")
        self.log_output.append(message)
        QMessageBox.information(self, "로그인 상태", message)

    def on_reset_click(self):
        reset_login()

    def on_search_click(self):
        cafe_url = self.cafe_url_input.text()
        query = self.query_input.text()
        period = self.period_combo.currentText()
        min_read_count = self.min_read_count_input.value()

        if not cafe_url:
            QMessageBox.warning(self, '경고', '카페 주소와 검색어를 입력해주세요.')
            return

        period_mapping = {
            '전체기간': 'all',
            '1일': '1d',
            '1주': '1w',
            '1개월': '1m',
            '6개월': '6m',
            '1년': '1y',
            '기간 입력': ''
        }

        period_code = period_mapping.get(period, '')

        # 초기화 및 버튼 상태 변경 (검색 시작 시 즉시 변경)
        self.search_button.setText("중지")
        self.search_button.setStyleSheet("background-color: #FF0000; color: white;")
        self.search_button.clicked.disconnect()
        self.search_button.clicked.connect(self.on_stop_click)


        if not query:
            if period_code:
                searchdate = period_code
            else:
                # 날짜 형식 YYYYMMDDYYYYMMDD으로 변환
                start_date = self.start_date_input.date().toString('yyyy-MM-dd')
                end_date = self.end_date_input.date().toString('yyyy-MM-dd')
                searchdate = f"{start_date}/{end_date}"
                self.log_output.append(f"기간 입력으로 검색합니다: {searchdate}")
        else:
            if period_code:
                searchdate = period_code
            else:
                # 날짜 형식 YYYYMMDDYYYYMMDD으로 변환
                start_date = self.start_date_input.date().toString('yyyy-MM-dd')
                end_date = self.end_date_input.date().toString('yyyy-MM-dd')
                searchdate = f"{start_date}{end_date}"
                self.log_output.append(f"기간 입력으로 검색합니다: {searchdate}")
                # 검색 수행
                file_name, error = search_articles_by_period(cafe_url, query, searchdate, min_read_count)
                self.on_search_finished(file_name, error)
                return

        self.log_output.clear()
        self.progress_bar.setValue(0)

        self.log_output.append("검색 시작...")
        self.log_output.append(f"카페 주소: {cafe_url}")
        self.log_output.append(f"검색어: {query}")
        self.log_output.append(f"기간: {searchdate}")
        self.log_output.append(f"최소 조회수: {min_read_count}")

        self.search_thread = SearchThread(cafe_url, query, period_code, self.start_date_input.date().toString('yyyyMMdd'), self.end_date_input.date().toString('yyyyMMdd'), min_read_count)
        self.search_thread.progress.connect(self.update_progress)
        self.search_thread.finished.connect(self.on_search_finished)
        self.search_thread.start()

        # 모든 로그를 화면에 찍어줌
        self.search_thread.finished.connect(lambda file_name, error: self.log_output.append(f"검색이 완료되었습니다. 저장된 파일: {file_name if file_name else '저장 실패'}"))

    def on_stop_click(self):
        if self.search_thread.isRunning():
            self.search_thread.stop()
            self.log_output.append("중지 버튼이 눌렸습니다. 현재까지의 데이터를 저장합니다...")
            self.search_button.setDisabled(True)

    def update_progress(self, progress_percent, processed_articles, estimated_time_remaining):
        self.progress_bar.setValue(progress_percent)
        progress_text = f"진행률: {progress_percent}%, 처리된 게시글: {processed_articles}/{self.search_thread.total_articles}, 남은 시간: {estimated_time_remaining}초"
        self.progress_label.setText(progress_text)
        self.log_output.append(progress_text)

    def on_search_finished(self, file_name, error):
        if error:
            QMessageBox.critical(self, '에러', error)
            self.log_output.append(f"에러 발생: {error}")
        else:
            QMessageBox.information(self, '완료', f'결과가 {file_name}로 저장되었습니다.')
            self.log_output.append(f"검색 완료. 결과 파일: {file_name}")

        # 검색 버튼 상태로 복구 및 초기화
        self.search_button.setText("검색")
        self.search_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.search_button.clicked.disconnect()
        self.search_button.clicked.connect(self.on_search_click)
        self.search_button.setDisabled(False)

        # 기간 입력, 최소 조회수 초기화
        self.min_read_count_input.setValue(50)
        self.period_combo.setCurrentIndex(0)
        self.start_date_input.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_input.setDate(QDate.currentDate())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CafeSearchApp()
    window.show()
    sys.exit(app.exec_())
