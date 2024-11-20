import sys
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QTableWidgetItem,
                             QCheckBox, QDesktopWidget, QDialog, QTableWidget, QSizePolicy, QHeaderView, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QTime
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd


# 전역 변수
url = ""


# API
class ApiWorker(QThread):
    api_data_received = pyqtSignal(object)  # API 호출 결과를 전달하는 시그널

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url  # URL을 클래스 속성으로 저장

        chrome_options = Options()
        # chrome_options.add_argument("--headless")
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
        self.driver = driver


    def run(self):
        print("Worker started.")  # 디버깅용
        try:
            # 외부 API 호출 (여기서 실제 API URL 사용)
            data = self.fetch_product_info_sele(self.url)
            print("Worker emit signal.")  # 디버깅용
            self.api_data_received.emit(data)  # 데이터를 시그널로 전달
        except Exception as e:
            print(f"Worker exception: {e}")  # 디버깅용
            self.api_data_received.emit({"status": "error", "message": str(e)})


    def fetch_product_info_sele(self, url):
        try:
            # URL 로드
            self.driver.get(url)

            # 상품명 추출
            product_name = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "prod-buy-header__title"))
            ).text

            # 배송비 추출
            try:
                delivery_fee = self.driver.find_element(By.CLASS_NAME, "delivery-fee-info").text
            except:
                delivery_fee = ""

            # 판매가 추출
            try:
                total_price = self.driver.find_element(By.CLASS_NAME, "total-price").text
            except:
                total_price = ""

            # 배송비와 판매가에서 숫자만 추출하고 더하기
            delivery_fee_number = self.extract_number(delivery_fee)
            total_price_number = self.extract_number(total_price)
            total = delivery_fee_number + total_price_number
            total_formatted = f"{total:,}원" if total > 0 else ""

            # 최근 실행 시간
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 결과 객체
            obj = {
                "status": "success",
                "message": "성공",
                "data": {
                    "URL": url,
                    "상품명": product_name,
                    "배송비": delivery_fee,
                    "판매가": total_price,
                    "합계": total_formatted,
                    "최근실행시간": current_time,
                },
            }

            print(f"obj : {obj}")
            return obj

        except Exception as e:
            return {"status": "error", "message": f"에러: {str(e)}", "data": ""}

        finally:
            self.driver.quit()  # 브라우저 종료


    def extract_number(self, text):
        return int(re.sub(r'\D', '', text)) if text else 0

    def fetch_product_info_beatiful(self, url):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }

        try:
            # GET 요청을 보냅니다.
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # HTTP 에러 상태 코드가 있는 경우 예외 발생

            # HTML 파싱
            soup = BeautifulSoup(response.content, "html.parser")

            # 상품명 추출
            product_name = soup.find(class_="prod-buy-header__title")
            product_name_text = product_name.get_text(strip=True) if product_name else ""

            # 배송비 추출 (배송비가 없을 수 있음)
            delivery_fee = soup.find(class_="delivery-fee-info")
            delivery_fee_text = delivery_fee.get_text(strip=True) if delivery_fee else ""

            # 판매가 추출
            total_price = soup.find(class_="total-price")
            total_price_text = total_price.get_text(strip=True) if total_price else ""

            # 배송비와 판매가에서 숫자만 추출하고 더하기
            delivery_fee_number = self.extract_number(delivery_fee_text)
            total_price_number = self.extract_number(total_price_text)

            # 합계 계산
            total = delivery_fee_number + total_price_number
            total_formatted = f"{total:,}원" if total > 0 else ""  # 합계가 0이면 빈 문자열

            # 최근 실행 시간
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 결과 객체

            obj = {
                "status": "success",
                "message": "성공",
                "data": {
                    "URL": url,
                    "상품명": product_name_text,
                    "배송비": delivery_fee_text,
                    "판매가": total_price_text,
                    "합계": total_formatted,
                    "최근실행시간": current_time
                }
            }

            print(f'obj : {obj}')

            return obj

        except requests.exceptions.RequestException as e:
            # 요청 예외 처리 (예: 네트워크 문제, HTTP 오류 등)
            return {"status": "error", "message": f"요청 오류: {str(e)}", "data": ""}


        except Exception as e:
            return {"status": "error", "message": f"알 수 없는 오류: {str(e)}", "data": ""}



# 팝업창 클래스 (URL 입력)
class RegisterPopup(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("쿠팡가격추적 등록하기")
        self.setGeometry(200, 200, 400, 200)  # 팝업 창 크기 설정
        self.setStyleSheet("background-color: white;")

        # 팝업 레이아웃
        popup_layout = QVBoxLayout(self)

        # 제목과 밑줄
        title_layout = QHBoxLayout()
        title_label = QLabel("쿠팡가격추적 등록하기")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.setAlignment(Qt.AlignCenter)
        popup_layout.addLayout(title_layout)


        # URL 입력
        url_label = QLabel("이름 : URL")
        url_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("URL을 입력하세요")
        self.url_input.setStyleSheet("""
            border-radius: 10%;
            border: 2px solid #888888;
            padding: 10px;
            font-size: 14px;
            color: #333333;
        """)
        self.url_input.setFixedHeight(40)



        # 버튼
        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("확인", self)
        self.confirm_button.setStyleSheet("""
            background-color: black;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        self.confirm_button.setFixedHeight(40)
        self.confirm_button.setFixedWidth(140)  # 버튼 너비 설정
        self.confirm_button.clicked.connect(self.on_confirm)

        button_layout.addWidget(self.confirm_button)
        button_layout.setAlignment(Qt.AlignCenter)
        popup_layout.addWidget(self.url_input)
        popup_layout.addLayout(button_layout)

        self.center_window()

    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def on_confirm(self):
        # URL 값을 전역 변수에 저장
        global url
        url = self.url_input.text()
        print(f"입력한 URL: {url}")  # 콘솔에 출력 (디버그용)
        self.accept()  # 팝업 닫기


# 메인 화면 클래스
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.set_layout()
        self.daily_worker = None  # 24시 실행 스레드
        self.on_demand_worker = None  # 요청 시 실행 스레드
        self.setup_ui()

    def set_layout(self):
        self.setWindowTitle("메인 화면")
        self.setGeometry(100, 100, 1000, 600)  # 메인 화면 크기 설정
        self.setStyleSheet("background-color: white;")  # 배경색 흰색

        # 메인 레이아웃
        main_layout = QVBoxLayout()

        # 상단 버튼들 레이아웃
        header_layout = QHBoxLayout()

        # 왼쪽 버튼들 레이아웃
        left_button_layout = QHBoxLayout()
        left_button_layout.setAlignment(Qt.AlignLeft)  # 왼쪽 정렬

        # 버튼 설정
        self.register_button = QPushButton("등록하기")
        self.register_button.setStyleSheet("""
            background-color: black;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.register_button.setFixedWidth(150)  # 고정된 너비
        self.register_button.setFixedHeight(40)  # 고정된 높이
        self.register_button.clicked.connect(self.open_register_popup)

        self.collect_button = QPushButton("수집하기")
        self.collect_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.collect_button.setFixedWidth(150)  # 고정된 너비
        self.collect_button.setFixedHeight(40)  # 고정된 높이
        self.collect_button.clicked.connect(self.start_on_demand_worker)


        self.delete_button = QPushButton("삭제하기")
        self.delete_button.setStyleSheet("""
            background-color: red;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.delete_button.setFixedWidth(150)  # 고정된 너비
        self.delete_button.setFixedHeight(40)  # 고정된 높이

        left_button_layout.addWidget(self.register_button)
        left_button_layout.addWidget(self.collect_button)
        left_button_layout.addWidget(self.delete_button)

        # 오른쪽 엑셀 다운로드 버튼 레이아웃
        right_button_layout = QHBoxLayout()
        right_button_layout.setAlignment(Qt.AlignRight)  # 오른쪽 정렬

        # 엑셀 다운로드 버튼
        self.excel_button = QPushButton("엑셀 다운로드")
        self.excel_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 15%;;
            font-size: 16px;
            padding: 10px;
        """)
        self.excel_button.setFixedWidth(150)  # 고정된 너비
        self.excel_button.setFixedHeight(40)  # 고정된 높이
        self.excel_button.clicked.connect(self.excel_down_load)
        right_button_layout.addWidget(self.excel_button)


        # 헤더에 "쿠팡(추적상품)" 텍스트 추가
        header_label = QLabel("쿠팡(추적상품)")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; background-color: white; color: black; padding: 10px;")

        # 테이블 만들기
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["선택", "URL", "상품명", "판매가", "배송비", "합계", "최근실행시간"])


        # 테이블을 부모 위젯 크기에 맞게 늘어나게 설정
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 열 크기 균등하게 설정
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)  # 모든 열을 균등하게 늘리기

        # URL 표시 레이블
        self.url_label = QLabel("URL : ")
        self.url_label.setAlignment(Qt.AlignCenter)
        self.url_label.setStyleSheet("font-size: 16px; color: black; padding: 10px;")

        # 레이아웃에 요소 추가
        header_layout.addLayout(left_button_layout)  # 왼쪽 버튼 레이아웃 추가
        header_layout.addLayout(right_button_layout)  # 오른쪽 엑셀 다운로드 버튼 추가

        main_layout.addLayout(header_layout)
        main_layout.addWidget(header_label)
        main_layout.addWidget(self.url_label)  # URL을 표시할 레이블 추가

        main_layout.addWidget(self.table)

        # 레이아웃 설정
        self.setLayout(main_layout)

        self.center_window()

    def excel_down_load(self):
        # 데이터 추출
        row_count = self.table.rowCount()
        column_count = self.table.columnCount()
        data = []

        for row in range(row_count):
            row_data = []
            for col in range(column_count):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)

        # 데이터프레임 생성
        df = pd.DataFrame(data, columns=[self.table.horizontalHeaderItem(i).text() for i in range(column_count)])

        # 엑셀 파일 저장
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "엑셀 파일 저장", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if file_path:
            df.to_excel(file_path, index=False, sheet_name="Table Data")
            print(f"엑셀 파일 저장 완료: {file_path}")

    def setup_ui(self):
        # UI 구성 (생략 - 버튼 추가 등)
        self.daily_timer = QTimer(self)
        self.daily_timer.timeout.connect(self.start_daily_worker)
        self.start_daily_timer()

    def start_daily_timer(self):
        """24시에 실행되도록 타이머 설정"""
        now = QTime.currentTime()
        target_time = QTime(0, 0)  # 자정 (24시)
        # target_time = QTime(1, 44)  # 테스트용 타겟 시간: 0시 32분

        interval = now.msecsTo(target_time)

        if interval <= 0:
            interval += 24 * 60 * 60 * 1000  # 이미 자정을 지났으면 다음 날 자정으로 설정

        # 첫 실행: 정확히 자정에 작업 실행
        QTimer.singleShot(interval, self.start_daily_worker)

        # 이후 매일 반복 실행: 24시간 간격으로 타이머 시작
        self.daily_timer.start(24 * 60 * 60 * 1000)

        # self.daily_timer.start(60 * 1000)  # 5분 간격으로 실행 # 테스트용

    def start_daily_worker(self):
        print('test')
        """24시에 실행되는 ApiWorker 시작"""
        if self.daily_worker is not None and self.daily_worker.isRunning():
            print("Stopping existing daily_worker...")

            self.daily_worker.terminate()
            self.daily_worker.wait()
        if url:
            self.get_api('a')

    def start_on_demand_worker(self):
        global url
        """사용자 요청 시 실행되는 ApiWorker 시작"""
        if self.on_demand_worker is not None and self.on_demand_worker.isRunning():
            self.on_demand_worker.terminate()
            self.on_demand_worker.wait()
        if url:
            self.get_api('b')

    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def open_register_popup(self):
        # 등록 팝업창 열기
        popup = RegisterPopup()
        popup.exec_()

        # 팝업창에서 URL을 입력 후 확인 버튼을 누르면 URL을 메인 화면에 표시
        self.update_url_label()

    def update_url_label(self):
        # URL을 레이블에 표시
        global url
        if url:  # URL이 존재하면
            self.url_label.setText(f"URL : {url}")
            print(f'{url}')
        else:
            self.url_label.setText("URL : ")

    def get_api(self, type):
        global url
        print(f'api 호출 : {url}')

        if url:  # URL이 존재하면

            # URL에서 쿼리 파라미터를 제거하여 새로운 URL 생성
            parsed_url = urlparse(url)
            new_url = parsed_url._replace(query='').geturl()  # 쿼리 파라미터 제거

            if type == 'a':
                print(f'type a')
                self.daily_worker = ApiWorker(new_url)
                self.daily_worker.api_data_received.connect(self.set_result)
                self.daily_worker.start()
            else:
                print(f'type b')
                self.on_demand_worker = ApiWorker(url)
                self.on_demand_worker.api_data_received.connect(self.set_result)
                self.on_demand_worker.start()

    def set_result(self, result):
        print(f'result : {result}')
        if result["status"] == "success":
            print(f'success')
            result_data = result["data"]
            row_position = self.table.rowCount()  # 현재 테이블의 마지막 행 위치를 얻음
            self.table.insertRow(row_position)  # 새로운 행을 추가

            # 체크박스 추가 (삭제 시 사용)
            check_box = QCheckBox()
            check_box.setStyleSheet("QCheckBox { margin-left: auto; margin-right: auto; }")  # 가운데 정렬
            self.table.setCellWidget(row_position, 0, check_box)

            # 데이터 추가
            self.table.setItem(row_position, 1, QTableWidgetItem(result_data["URL"]))  # 첫 번째 열은 체크박스라 1부터 시작
            self.table.setItem(row_position, 2, QTableWidgetItem(result_data["상품명"]))
            self.table.setItem(row_position, 3, QTableWidgetItem(result_data["판매가"]))
            self.table.setItem(row_position, 4, QTableWidgetItem(result_data["배송비"]))
            self.table.setItem(row_position, 5, QTableWidgetItem(result_data["합계"]))
            self.table.setItem(row_position, 6, QTableWidgetItem(result_data["최근실행시간"]))
        else:
            print(f'fail')
            self.show_warning(result["message"])

    def show_warning(self, message):
        # QMessageBox 생성
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)  # 경고 아이콘 설정
        msg.setWindowTitle("경고")  # 창 제목 설정
        msg.setText(message)  # 메시지 내용 설정
        msg.setStandardButtons(QMessageBox.Ok)  # 버튼 설정 (OK 버튼만 포함)
        msg.exec_()  # 메시지 박스 표시


# 로그인 API 요청을 처리하는 스레드 클래스
class LoginThread(QThread):
    # 로그인 성공 시 메인 화면을 띄우기 위한 시그널
    login_success = pyqtSignal()

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password

    def run(self):
        # 여기서 로그인 API 호출 시뮬레이션
        print(f"로그인 시도: {self.username}, {self.password}")
        time.sleep(3)  # 실제 API 요청 시에는 time.sleep()을 API 호출로 대체

        # 로그인 성공 후 메인 화면 전환 시그널 발생
        self.login_success.emit()


# 로그인 화면 클래스
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("로그인 화면")
        self.setGeometry(100, 100, 500, 300)  # 화면 크기 설정
        self.setStyleSheet("background-color: #ffffff;")  # 배경색 흰색

        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)  # 레이아웃의 외부 마진을 설정
        layout.setSpacing(20)  # 위젯 간 간격 설정

        # ID 입력
        self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText("ID를 입력하세요")
        self.id_input.setStyleSheet("""
            border-radius: 20px; 
            border: 2px solid #888888;
            padding: 10px;
            font-size: 14px;
            color: #333333;
        """)
        self.id_input.setFixedHeight(40)
        self.id_input.setFixedWidth(300)  # 너비를 화면의 절반 정도로 설정

        # 비밀번호 입력
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("비밀번호를 입력하세요")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            border-radius: 20px; 
            border: 2px solid #888888;
            padding: 10px;
            font-size: 14px;
            color: #333333;
        """)
        self.password_input.setFixedHeight(40)
        self.password_input.setFixedWidth(300)  # 너비를 화면의 절반 정도로 설정

        # 로그인 버튼
        button_layout = QHBoxLayout()

        self.login_button = QPushButton("로그인", self)
        self.login_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        self.login_button.setFixedHeight(40)
        self.login_button.setFixedWidth(140)  # 버튼 너비 설정
        self.login_button.clicked.connect(self.login)

        # 비밀번호 변경 버튼
        self.change_password_button = QPushButton("비밀번호 변경", self)
        self.change_password_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        self.change_password_button.setFixedHeight(40)
        self.change_password_button.setFixedWidth(140)  # 버튼 너비 설정
        self.change_password_button.clicked.connect(self.change_password)

        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.change_password_button)
        button_layout.setSpacing(20)  # 버튼 간의 간격을 설정

        # 레이아웃에 요소 추가
        layout.addWidget(self.id_input)
        layout.addWidget(self.password_input)
        layout.addLayout(button_layout)
        self.center_window()

    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def login(self):
        # ID와 비밀번호를 가져옴
        username = self.id_input.text()
        password = self.password_input.text()

        # 로그인 요청을 비동기적으로 처리하는 스레드 생성
        self.login_thread = LoginThread(username, password)
        self.login_thread.login_success.connect(self.main_window)  # 로그인 성공 시 메인 화면으로 전환
        self.login_thread.start()  # 스레드 실행

    def change_password(self):
        # 비밀번호 변경 함수 (비워두기)
        print("비밀번호 변경 시도")

    def main_window(self):
        # 로그인 성공 시 메인 화면을 새롭게 생성
        self.close()  # 로그인 화면 종료
        self.main_screen = MainWindow()
        self.main_screen.show()


# 프로그램 실행
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
