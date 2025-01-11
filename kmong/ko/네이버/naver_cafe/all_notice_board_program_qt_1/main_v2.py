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
import os  # os 모듈 import


# 전역 변수로 쿠키 저장
global_cookies = {}

# 셀레니움 드라이버 설정 함수
def setup_driver():
    """
    Selenium 웹 드라이버를 설정하고 반환하는 함수입니다.
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")

    # 사용자 에이전트 설정
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # 자동화 탐지 방지 설정
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 크롬 드라이버 실행 및 자동화 방지 우회
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver

# 네이버 로그인 스레드
class LoginThread(QThread):
    # 로그인 완료 시 쿠키와 메시지를 전달하는 시그널
    login_complete = pyqtSignal(dict, str)

    def run(self):
        """
        네이버 로그인 과정을 처리하고, 완료 시 쿠키와 메시지를 emit하는 함수입니다.
        """
        global global_cookies
        try:
            driver = setup_driver()
            driver.get("https://nid.naver.com/nidlogin.login")  # 네이버 로그인 페이지로 이동

            time.sleep(2)
            # 로그인 화면의 ID 입력란이 로드될 때까지 대기
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

                # 쿠키 가져오기
                cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

                # 네이버 로그인 완료 확인
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

# 로그인 초기화 함수
def reset_login():
    """
    로그인 정보를 초기화하는 함수입니다.
    """
    global global_cookies
    global_cookies = {}
    window.log_output.append("로그인 정보가 초기화되었습니다.")
    QMessageBox.information(None, "초기화", "로그인 정보가 초기화되었습니다.")

# 특정 기간에 따른 검색 및 엑셀 파일 저장 함수
def search_articles_by_period(cafe_url, query, searchdate, min_read_count):
    """
    지정된 기간에 따라 네이버 카페에서 게시글을 검색하고 결과를 엑셀 파일로 저장합니다.
    """
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

# 네이버 카페 게시글 수집 함수
def fetch_naver_cafe_articles(clubid, searchdate, searchBy, query, sortBy, userDisplay, media, option, page, min_read_count):
    """
    네이버 카페에서 특정 조건에 따라 게시글을 수집하는 함수입니다.
    """
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
                try:
                    view_count = int(view_tag.get_text(strip=True).replace(',', ''))
                except ValueError:
                    print(f"조회수를 숫자로 변환할 수 없습니다: {view_tag.get_text(strip=True)}")
                    continue

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

# 네이버 카페 ID 가져오기 함수
def get_cafe_id(cafe_url):
    """
    네이버 카페 URL에서 카페 ID를 가져오는 함수입니다.
    """
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
                window.log_output.append("카페 ID를 찾을 수 없습니다.")
                return ""
        else:
            window.log_output.append(f"API 요청 실패: {response.status_code}")
            return ""
    except Exception as e:
        window.log_output.append(f"카페 ID를 가져오는 중 오류 발생: {e}")
        return ""

# 게시글 목록 가져오기
def get_article_list(cafe_id, query, page, userDisplay, searchdate):
    """
    특정 카페 ID에서 주어진 검색어와 기간에 따라 게시글 목록을 가져오는 함수입니다.
    """
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
            "searchdate": searchdate
        }

        window.log_output.append(f"get_article_list url: {url}")
        window.log_output.append(f"get_article_list params: {params}")

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, cookies=global_cookies, params=params)

        if response.status_code == 200:
            data = response.json()
            if "message" in data and "result" in data["message"]:
                articles = data["message"]["result"]["articleList"]
                total_articles = data["message"]["result"]["totalArticleCount"]
                return articles, total_articles
            else:
                window.log_output.append("게시글 목록을 가져올 수 없습니다.")
                return [], 0
        else:
            window.log_output.append(f"API 요청 실패: {response.status_code}")
            return [], 0
    except Exception as e:
        window.log_output.append(f"게시글 목록을 가져오는 중 오류 발생: {e}")
        return [], 0

# 전체 게시글 목록 가져오기
def get_article_list_all(cafe_id, page, userDisplay):
    """
    특정 카페 ID에서 전체 게시글 목록을 가져오는 함수입니다.
    """
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
        window.log_output.append(f"get_article_list_all url: {url}")
        window.log_output.append(f"get_article_list_all params: {params}")

        if response.status_code == 200:
            data = response.json()
            if "message" in data and "result" in data["message"]:
                articles = data["message"]["result"]["articleList"]
                return articles, 0
            else:
                window.log_output.append("게시글 목록을 가져올 수 없습니다.")
                return [], 0
        else:
            window.log_output.append(f"API 요청 실패: {response.status_code}")
            return [], 0
    except Exception as e:
        window.log_output.append(f"게시글 목록을 가져오는 중 오류 발생: {e}")
        return [], 0

# 날짜 형식 변환 함수
def parse_date(date_str):
    """
    날짜 문자열을 지정된 형식으로 변환하는 함수입니다.
    """
    try:
        date_str = re.sub(r' KST', '', date_str)
        date_obj = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
        return date_obj.strftime('%Y.%m.%d.'), date_obj
    except Exception as e:
        print(f"날짜 형식 변환 중 오류 발생: {e}")
        return "", None

# 검색 스레드 클래스
class SearchThread(QThread):
    # 진행률과 검색 완료 시그널 정의
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
        self.file_name = None  # file_name 초기화


    def run(self):
        """
        검색을 수행하고 결과를 엑셀 파일로 저장한 후, 완료 시 시그널을 emit합니다.
        """
        file_name, error = self.search_articles()
        self.finished.emit(file_name, error)

    def search_articles(self):
        """
        게시글을 검색하고 결과를 엑셀 파일로 저장하는 함수입니다.
        """
        try:
            cafe_id = get_cafe_id(self.cafe_url)
            if not cafe_id:
                return None, "카페 ID를 가져올 수 없습니다."

            userDisplay = 50
            page = 1
            processed_articles = 0

            while not self.stop_requested:
                time.sleep(random.uniform(2, 4))

                # 검색어가 없는 경우 전체 게시글을 가져옴
                if not self.query:
                    articles, total_articles = get_article_list_all(cafe_id, page, userDisplay)
                else:
                    articles, total_articles = get_article_list(cafe_id, self.query, page, userDisplay, self.period)

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
                            window.log_output.append(f"Warning: 'addDate'와 'writeDateTimestamp' 필드를 찾을 수 없습니다. 다음 기사로 넘어갑니다.")
                            continue
                    else:
                        formatted_date, date_obj = parse_date(date_str)

                    # 기간 필터링 기간 선택이 아닌 값의 범위를 넘어가면 중지
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

                    # 조회수 필터링
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

                if page % 100 == 0:  # 100 페이지마다 저장
                    window.log_output.append(f"100 페이지 마다 업데이트 저장")
                    self.file_name, error = self.save_results_to_excel(self.results)
                    self.results = []  # 저장 후 리스트 초기화

                if self.period == 'all' and self.query:
                    progress_percent = int((processed_articles / self.total_articles) * 100) if self.total_articles > 0 else 0
                    time_per_request = 3
                    estimated_time_remaining = (self.total_articles - processed_articles) * time_per_request // userDisplay
                    self.progress.emit(progress_percent, processed_articles, estimated_time_remaining)

            return self.save_results_to_excel(self.results)
        except Exception as e:
            window.log_output.append(f"검색 중 오류 발생: {e}")
            return None, str(e)

    def is_date_outside_period(self, date_obj):
        """
        날짜가 지정된 기간 외에 있는지 확인하는 함수입니다.
        """
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
        """
        검색 결과를 엑셀 파일에 계속해서 추가하는 함수입니다.
        """
        file_name = self.file_name if hasattr(self, 'file_name') else None

        if not file_name:
            now = datetime.now().strftime('%Y%m%d%H%M')
            file_name = f"cafe_articles_{now}.xlsx"
            self.file_name = file_name

        df = pd.DataFrame(results)

        try:
            if os.path.exists(file_name):
                # 파일이 이미 존재하면, 기존 데이터를 읽어오고 새로운 데이터와 병합
                existing_df = pd.read_excel(file_name)
                df = pd.concat([existing_df, df], ignore_index=True)
            # 병합된 데이터를 파일에 다시 저장
            df.to_excel(file_name, index=False)
        except FileNotFoundError:
            # 파일이 없으면 새로 생성
            df.to_excel(file_name, index=False)

        return file_name, None


    def stop(self):
        """
        검색 중지를 요청하는 함수입니다.
        """
        self.stop_requested = True

# PyQt5 앱 클래스
class CafeSearchApp(QWidget):
    def __init__(self):
        super().__init__()

        # 윈도우 설정
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

        # 레이아웃 설정
        layout = QVBoxLayout()

        # 로그인 및 검색 입력창
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

        # 최소 조회수와 기간 선택
        hbox2 = QHBoxLayout()
        self.min_read_count_label = QLabel('최소 조회수:')
        self.min_read_count_input = QSpinBox(self)
        self.min_read_count_input.setRange(0, 1000000)
        self.min_read_count_input.setValue(1)
        self.period_label = QLabel('기간 선택:')
        self.period_combo = QComboBox(self)
        self.period_combo.addItems(['전체기간', '1일', '1주', '1개월', '6개월', '1년', '기간 입력'])
        self.period_combo.currentIndexChanged.connect(self.update_date_edit_status)
        hbox2.addWidget(self.min_read_count_label)
        hbox2.addWidget(self.min_read_count_input)
        hbox2.addWidget(self.period_label)
        hbox2.addWidget(self.period_combo)

        # 기간 입력
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

        # 검색 버튼
        hbox4 = QHBoxLayout()
        self.search_button = QPushButton('검색', self)
        self.search_button.clicked.connect(self.on_search_click)
        hbox4.addWidget(self.search_button)

        # 진행률 레이블
        self.progress_label = QLabel("전체 기간이고 검색어가 있는 경우만 보여집니다.", self)
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: black; font-weight: bold;")

        # 진행률 표시 바
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        # 로그 출력창
        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)

        # 레이아웃 구성
        layout.addLayout(hbox1)
        layout.addLayout(hbox2)
        layout.addLayout(hbox3)
        layout.addLayout(hbox4)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def update_date_edit_status(self):
        """
        기간 입력 방식에 따라 날짜 입력란 활성화 여부를 조정하는 함수입니다.
        """
        if self.period_combo.currentText() == '기간 입력':
            self.start_date_input.setEnabled(True)
            self.end_date_input.setEnabled(True)
        else:
            self.start_date_input.setEnabled(False)
            self.end_date_input.setEnabled(False)

    def on_login_click(self):
        """
        로그인 버튼 클릭 시 실행되는 함수입니다.
        로그인 스레드를 시작하고 로그인을 완료할 때까지 대기합니다.
        """
        self.log_output.append("로그인 정보를 입력하고 로그인을 완료하세요.")
        self.log_output.append("로그인 대기중...")
        self.login_thread = LoginThread()
        self.login_thread.login_complete.connect(self.on_login_complete)
        self.login_thread.start()

    def on_login_complete(self, cookies, message):
        """
        로그인 완료 시 실행되는 함수입니다.
        로그인 결과에 따라 메시지를 출력하고 로그인 상태를 표시합니다.
        """
        self.log_output.append(message)
        QMessageBox.information(self, "로그인 상태", message)

    def on_reset_click(self):
        """
        로그인 초기화 버튼 클릭 시 실행되는 함수입니다.
        로그인 정보를 초기화하고 로그 창에 메시지를 출력합니다.
        """
        reset_login()

    def on_search_click(self):
        """
        검색 버튼 클릭 시 실행되는 함수입니다.
        입력된 정보에 따라 게시글 검색을 시작합니다.
        """
        self.progress_bar.setDisabled(True)  # 진행률 게이지바 비활성화
        self.progress_label.setText("진행률: 알 수 없음")

        cafe_url = self.cafe_url_input.text()
        query = self.query_input.text()
        period = self.period_combo.currentText()
        min_read_count = self.min_read_count_input.value()

        if not cafe_url:
            QMessageBox.warning(self, '경고', '카페 주소를 입력해주세요.')
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

        if period_code == 'all' and query:
            self.progress_bar.setDisabled(False)  # 진행률 게이지바 활성화
            self.progress_bar.setValue(0)
            self.progress_label.setText("진행률: 0%")
        else:
            self.progress_bar.setDisabled(True)  # 진행률 게이지바 비활성화
            self.progress_label.setText("진행률: 알 수 없음")


        # 초기화 및 버튼 상태 변경 (검색 시작 시 즉시 변경)
        self.search_button.setText("중지")
        self.search_button.setStyleSheet("background-color: #FF0000; color: white;")
        self.search_button.clicked.disconnect()
        self.search_button.clicked.connect(self.on_stop_click)

        if not query:
            if period_code:
                searchdate = period_code
            else:
                # 날짜 형식 YYYYMMDD/YYYYMMDD으로 변환
                start_date = self.start_date_input.date().toString('yyyy-MM-dd')
                end_date = self.end_date_input.date().toString('yyyy-MM-dd')
                searchdate = f"{start_date}/{end_date}"
                self.log_output.append(f"검색어가 없는 기간 입력으로 검색합니다: {searchdate}")
        else:
            if period_code:
                searchdate = period_code
            else:
                # 날짜 형식 YYYYMMDD/YYYYMMDD으로 변환
                start_date = self.start_date_input.date().toString('yyyy-MM-dd')
                end_date = self.end_date_input.date().toString('yyyy-MM-dd')
                searchdate = f"{start_date}{end_date}"
                self.log_output.append(f"기간 입력으로 검색합니다: {searchdate}")
                # 검색 수행
                file_name, error = search_articles_by_period(cafe_url, query, searchdate, min_read_count)
                self.on_search_finished(file_name, error)
                return

        self.log_output.clear()

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
        """
        검색 중지 버튼 클릭 시 실행되는 함수입니다.
        현재 진행 중인 검색을 중지하고 중간 결과를 저장합니다.
        """
        if self.search_thread.isRunning():
            self.search_thread.stop()
            self.log_output.append("중지 버튼이 눌렸습니다. 현재까지의 데이터를 저장합니다...")
            self.search_button.setDisabled(True)

    def update_progress(self, progress_percent, processed_articles, estimated_time_remaining):
        """
        검색 진행률을 업데이트하는 함수입니다.
        진행률에 따라 로그를 출력하고, 게이지바를 업데이트합니다.
        """
        if not self.progress_bar.isEnabled():  # 진행률 게이지바가 비활성화된 경우
            progress_text = "진행률: 알 수 없음"
        else:
            progress_text = f"진행률: {progress_percent}%, 처리된 게시글: {processed_articles}/{self.search_thread.total_articles}, 남은 시간: {estimated_time_remaining}초"
            self.progress_bar.setValue(progress_percent)

        self.progress_label.setText(progress_text)
        self.log_output.append(progress_text)

    def on_search_finished(self, file_name, error):
        """
        검색 완료 시 실행되는 함수입니다.
        검색 결과를 처리하고, 파일 저장 여부에 따라 메시지를 출력합니다.
        """
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
        self.min_read_count_input.setValue(1)
        self.period_combo.setCurrentIndex(0)
        self.start_date_input.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_input.setDate(QDate.currentDate())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CafeSearchApp()
    window.show()
    sys.exit(app.exec_())
