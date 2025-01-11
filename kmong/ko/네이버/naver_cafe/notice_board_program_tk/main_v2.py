import sys
import os
import re
import time
import threading
import requests
import json
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QProgressBar, QComboBox, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# 전역 변수
cafe_id = ""
menu_list = []
menuid = ""
global_cookies = {}
extracted_data = []

# Selenium 드라이버 설정 함수
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")
    chrome_options.add_argument("user-agent=Mozilla/5.0")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
    })
    return driver

# 로그인 스레드 클래스
class LoginThread(QThread):
    login_success = pyqtSignal(dict)
    login_failure = pyqtSignal()

    def run(self):
        global global_cookies

        driver = setup_driver()
        driver.get("https://nid.naver.com/nidlogin.login")

        start_time = time.time()
        max_wait_time = 300  # 최대 대기 시간 (초)
        logged_in = False

        while not logged_in:
            time.sleep(1)
            elapsed_time = time.time() - start_time

            if elapsed_time > max_wait_time:
                self.login_failure.emit()
                driver.quit()
                return

            cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
            if 'NID_AUT' in cookies and 'NID_SES' in cookies:
                logged_in = True
                global_cookies = cookies
                self.login_success.emit(global_cookies)

        driver.quit()

# 메인 애플리케이션
class CafeExtractorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("N 카페 게시글 추출기")
        self.setGeometry(100, 100, 600, 700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 로그인 섹션
        login_layout = QHBoxLayout()
        self.login_button = QPushButton("로그인")
        self.login_button.clicked.connect(self.start_login)
        login_layout.addWidget(self.login_button)
        layout.addLayout(login_layout)

        # 카페 URL 및 메뉴 선택 섹션
        cafe_layout = QVBoxLayout()

        self.cafe_url_label = QLabel("카페 URL:")
        self.cafe_url_entry = QLineEdit()
        self.cafe_url_fetch_button = QPushButton("가져오기")
        self.cafe_url_fetch_button.clicked.connect(self.fetch_cafe_info)

        cafe_url_layout = QHBoxLayout()
        cafe_url_layout.addWidget(self.cafe_url_label)
        cafe_url_layout.addWidget(self.cafe_url_entry)
        cafe_url_layout.addWidget(self.cafe_url_fetch_button)

        self.menu_dropdown = QComboBox()
        self.menu_dropdown.currentIndexChanged.connect(self.select_menu)

        cafe_layout.addLayout(cafe_url_layout)
        cafe_layout.addWidget(self.menu_dropdown)
        layout.addLayout(cafe_layout)

        # 추출 섹션
        extract_layout = QVBoxLayout()

        self.start_page_label = QLabel("시작 페이지:")
        self.start_page_entry = QLineEdit()
        self.end_page_label = QLabel("종료 페이지:")
        self.end_page_entry = QLineEdit()
        self.extract_button = QPushButton("추출 시작")
        self.extract_button.clicked.connect(self.start_extraction)

        page_layout = QHBoxLayout()
        page_layout.addWidget(self.start_page_label)
        page_layout.addWidget(self.start_page_entry)
        page_layout.addWidget(self.end_page_label)
        page_layout.addWidget(self.end_page_entry)

        extract_layout.addLayout(page_layout)
        extract_layout.addWidget(self.extract_button)

        self.progress_bar = QProgressBar()
        extract_layout.addWidget(self.progress_bar)

        layout.addLayout(extract_layout)

        # 저장 섹션
        save_layout = QVBoxLayout()

        self.file_name_label = QLabel("파일명:")
        self.file_name_entry = QLineEdit()
        self.file_name_entry.setText("추출 결과")
        self.save_button = QPushButton("저장")
        self.save_button.clicked.connect(self.save_data)

        save_file_layout = QHBoxLayout()
        save_file_layout.addWidget(self.file_name_label)
        save_file_layout.addWidget(self.file_name_entry)

        save_layout.addLayout(save_file_layout)
        save_layout.addWidget(self.save_button)

        layout.addLayout(save_layout)
        self.setLayout(layout)

    def start_login(self):
        self.login_thread = LoginThread()
        self.login_thread.login_success.connect(self.on_login_success)
        self.login_thread.login_failure.connect(self.on_login_failure)
        self.login_thread.start()

    def on_login_success(self, cookies):
        QMessageBox.information(self, "로그인 성공", "정상적으로 로그인되었습니다.")

    def on_login_failure(self):
        QMessageBox.warning(self, "로그인 실패", "300초 내에 로그인하지 않았습니다.")

    def fetch_cafe_info(self):
        pass  # 카페 URL 정보 가져오기 로직 추가 필요

    def select_menu(self):
        global menuid
        selected_menu = self.menu_dropdown.currentText()
        for menu in menu_list:
            if menu['menuName'] == selected_menu:
                menuid = menu['menuId']
                break

    def start_extraction(self):
        pass  # 데이터 추출 로직 추가 필요

    def save_data(self):
        file_name = self.file_name_entry.text()
        if not file_name:
            QMessageBox.warning(self, "경고", "파일명을 입력해주세요.")
            return

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", file_name, "Excel Files (*.xlsx);;CSV Files (*.csv);;Text Files (*.txt)", options=options)

        if file_path:
            df = pd.DataFrame(extracted_data)
            if file_path.endswith(".xlsx"):
                df.to_excel(file_path, index=False)
            elif file_path.endswith(".csv"):
                df.to_csv(file_path, index=False, encoding="utf-8-sig")
            elif file_path.endswith(".txt"):
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(json.dumps(extracted_data, indent=4, ensure_ascii=False))

            QMessageBox.information(self, "저장 완료", f"데이터가 {file_path}에 저장되었습니다.")

# 실행
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CafeExtractorApp()
    window.show()
    sys.exit(app.exec_())
