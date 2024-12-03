import pandas as pd
from PyQt5.QtCore import Qt,  QTimer, QTime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidgetItem,
                             QCheckBox, QDesktopWidget, QTableWidget, QSizePolicy, QHeaderView, QMessageBox,
                             QFileDialog, QTextEdit, QApplication)

from src.workers.api_worker import ApiWorker
from src.workers.check_worker import CheckWorker
from src.workers.countdown_thread import CountdownThread
from src.ui.header_with_checkbox import HeaderWithCheckbox
from src.ui.register_popup import RegisterPopup
from src.ui.all_register_popup import AllRegisterPopup
from datetime import datetime
from src.utils.config import server_url  # 서버 URL 및 설정 정보


class MainWindow(QWidget):
    
    # 초기화
    def __init__(self, cookies):
        super().__init__()
        self.set_layout()
        self.daily_worker = None  # 24시 실행 스레드
        self.on_demand_worker = None  # 요청 시 실행 스레드
        self.setup_timer()
        self.load_excel_to_table("DB.xlsx")  # 원하는 엑셀 파일 경로 지정

        # 세션 관리용 API Worker 초기화
        self.api_worker = CheckWorker(cookies, server_url)
        self.api_worker.api_failure.connect(self.handle_api_failure)
        self.api_worker.start()  # 스레드 시작

    def handle_api_failure(self, error_message):
        """API 요청 실패 처리"""
        QMessageBox.critical(self, "프로그램 종료", f"동일 접속자가 존재해서 프로그램을 종료합니다.\n오류: {error_message}")
        self.api_worker.stop()  # 스레드 중지
        QApplication.instance().quit()  # 프로그램 종료


    def load_excel_to_table(self, file_path):
        """엑셀 파일을 로드하여 테이블에 표시"""

        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(file_path)

            # 빈 값을 공백으로 채우기
            df = df.fillna("")

            # 테이블 초기화
            self.table.setRowCount(0)

            # 필요한 데이터만 테이블에 삽입
            for row_idx, row_data in df.iterrows():
                self.table.insertRow(row_idx)
                # 체크박스 추가
                check_box = QCheckBox()
                check_box_widget = QWidget()
                layout = QHBoxLayout(check_box_widget)
                layout.addWidget(check_box)
                layout.setAlignment(Qt.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                check_box_widget.setLayout(layout)
                self.table.setCellWidget(row_idx, 0, check_box_widget)

                # 데이터 매핑: "최근실행시간", "상품명", "판매가", "배송비", "합계", "URL"
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row_data.get("최근실행시간", ""))))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(row_data.get("상품명", ""))))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(row_data.get("판매가", ""))))
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(row_data.get("배송비", ""))))
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(row_data.get("합계", ""))))
                self.table.setItem(row_idx, 6, QTableWidgetItem(str(row_data.get("URL", ""))))

            print(f"엑셀 파일 '{file_path}' 로드 성공")
        except Exception as e:
            print(f"엑셀 파일 로드 실패: {str(e)}")


    # 레이아웃 설정
    def set_layout(self):
        self.setWindowTitle("메인 화면")
        self.setGeometry(100, 100, 1000, 700)  # 메인 화면 크기 설정
        self.setStyleSheet("background-color: white;")  # 배경색 흰색

        # 메인 레이아웃
        main_layout = QVBoxLayout()

        # 상단 버튼들 레이아웃
        header_layout = QHBoxLayout()

        # 왼쪽 버튼들 레이아웃
        left_button_layout = QHBoxLayout()
        left_button_layout.setAlignment(Qt.AlignLeft)  # 왼쪽 정렬

        # 버튼 설정
        # 개별등록
        self.register_button = QPushButton("개별등록")
        self.register_button.setStyleSheet("""
            background-color: black;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.register_button.setFixedWidth(100)  # 고정된 너비
        self.register_button.setFixedHeight(40)  # 고정된 높이
        self.register_button.setCursor(Qt.PointingHandCursor)  # 마우스 올렸을 때 손가락 커서 설정
        self.register_button.clicked.connect(self.open_register_popup)

        # 전체등록
        self.all_register_button = QPushButton("전체등록")
        self.all_register_button.setStyleSheet("""
                    background-color: black;
                    color: white;
                    border-radius: 15%;
                    font-size: 16px;
                    padding: 10px;
                """)
        self.all_register_button.setFixedWidth(100)  # 고정된 너비
        self.all_register_button.setFixedHeight(40)  # 고정된 높이
        self.all_register_button.setCursor(Qt.PointingHandCursor)
        self.all_register_button.clicked.connect(self.open_all_register_popup)

        # 초기화
        self.reset_button = QPushButton("초기화")
        self.reset_button.setStyleSheet("""
                    background-color: black;
                    color: white;
                    border-radius: 15%;
                    font-size: 16px;
                    padding: 10px;
                """)
        self.reset_button.setFixedWidth(100)  # 고정된 너비
        self.reset_button.setFixedHeight(40)  # 고정된 높이
        self.reset_button.setCursor(Qt.PointingHandCursor)
        self.reset_button.clicked.connect(self.reset_url)

        # 선택수집
        self.collect_button = QPushButton("선택수집")
        self.collect_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.collect_button.setFixedWidth(100)  # 고정된 너비
        self.collect_button.setFixedHeight(40)  # 고정된 높이
        self.collect_button.setCursor(Qt.PointingHandCursor)
        self.collect_button.clicked.connect(self.start_on_demand_worker)

        # 전체수집
        self.start_button = QPushButton("스케줄수집")
        self.start_button.setStyleSheet("""
            background-color: #8A2BE2;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.start_button.setFixedWidth(120)  # 고정된 너비
        self.start_button.setFixedHeight(40)  # 고정된 높이
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self.start_daily_worker)

        # 삭제하기
        self.delete_button = QPushButton("삭제하기")
        self.delete_button.setStyleSheet("""
            background-color: red;
            color: white;
            border-radius: 15%;
            font-size: 16px;
            padding: 10px;
        """)
        self.delete_button.setFixedWidth(100)  # 고정된 너비
        self.delete_button.setFixedHeight(40)  # 고정된 높이
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.clicked.connect(self.delete_table_row)

        # 왼쪽 버튼 레이아웃
        left_button_layout.addWidget(self.register_button)
        left_button_layout.addWidget(self.all_register_button)
        left_button_layout.addWidget(self.reset_button)
        left_button_layout.addWidget(self.collect_button)
        left_button_layout.addWidget(self.start_button)
        left_button_layout.addWidget(self.delete_button)

        # 엑셀 다운로드 버튼
        self.excel_button = QPushButton("엑셀 다운로드")
        self.excel_button.setStyleSheet("""
            background-color: #006400;
            color: white;
            border-radius: 15%;;
            font-size: 16px;
            padding: 10px;
        """)
        self.excel_button.setFixedWidth(150)  # 고정된 너비
        self.excel_button.setFixedHeight(40)  # 고정된 높이
        self.excel_button.setCursor(Qt.PointingHandCursor)
        self.excel_button.clicked.connect(self.excel_down_load)

        # 오른쪽 엑셀 버튼 레이아웃
        right_button_layout = QHBoxLayout()
        right_button_layout.setAlignment(Qt.AlignRight)  # 오른쪽 정렬
        right_button_layout.addWidget(self.excel_button)

        # 헤더에 "쿠팡(추적상품)" 텍스트 추가
        header_label = QLabel("쿠팡(추적상품)")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; background-color: white; color: black; padding: 10px;")

        # 남은 시간 라벨
        self.time_label = QLabel("추적시간 매일 0시 0분 0초")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 15px; background-color: white; color: black; padding: 10px;")

        # 테이블 만들기
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["", "최근실행시간", "상품명", "판매가", "배송비", "합계", "URL"])

        # 커스텀 헤더 설정
        header = HeaderWithCheckbox(Qt.Horizontal, self.table, main_window=self)
        self.table.setHorizontalHeader(header)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        # 테이블을 부모 위젯 크기에 맞게 늘어나게 설정
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 마지막 열 크기 고정
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # 테이블 너비 조정
        self.set_column_widths([10, 20, 20, 20, 20, 20, 10])

        # 로그 창 추가
        self.log_window = QTextEdit(self)
        self.log_window.setReadOnly(True)  # 읽기 전용 설정
        self.log_window.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ccc; padding: 5px;")


        # 열 크기 균등하게 설정
        # header = self.table.horizontalHeader()
        # for i in range(self.table.columnCount()):
        #     header.setSectionResizeMode(i, QHeaderView.Stretch)  # 모든 열을 균등하게 늘리기

        # 레이아웃에 요소 추가
        header_layout.addLayout(left_button_layout)  # 왼쪽 버튼 레이아웃 추가
        header_layout.addLayout(right_button_layout)  # 오른쪽 엑셀 다운로드 버튼 추가

        main_layout.addLayout(header_layout)
        main_layout.addWidget(header_label)
        main_layout.addWidget(self.time_label)

        # 레이아웃에 요소 추가
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.table, stretch=3)
        main_layout.addWidget(self.log_window, stretch=2)  # 로그 창 추가

        # 레이아웃 설정
        self.setLayout(main_layout)

        self.center_window()


    # 로그
    def add_log(self, message):
        """
        로그 메시지를 추가합니다.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_window.append(f"[{timestamp}] {message}")


    # 테이블 컬럼 너비
    def set_column_widths(self, percentages):
        """열 너비를 비율로 설정"""
        total_width = self.table.viewport().width()  # 테이블의 전체 너비
        for col_index, percentage in enumerate(percentages):
            width = total_width * (percentage / 100)
            self.table.setColumnWidth(col_index, int(width))


    # 체크박스 전체 선택
    def toggle_all_checkboxes(self, checked):
        """헤더 체크박스 상태에 따라 모든 행의 체크박스 상태를 변경"""
        for row in range(self.table.rowCount()):
            container_widget = self.table.cellWidget(row, 0)
            if container_widget:
                layout = container_widget.layout()
                if layout and layout.count() > 0:
                    check_box = layout.itemAt(0).widget()
                    if isinstance(check_box, QCheckBox):
                        check_box.setChecked(checked)


    # 엑셀 다운로드
    def excel_down_load(self):
        # 데이터 추출
        row_count = self.table.rowCount()
        column_count = self.table.columnCount()

        # 0번째 열(체크박스)을 제외한 나머지 열의 데이터를 저장
        data = []
        for row in range(row_count):
            row_data = []
            for col in range(1, column_count):  # 1번째 열부터 시작
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)

        # 0번째 열을 제외한 나머지 열의 헤더를 가져옴
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(1, column_count)]

        # 데이터프레임 생성
        df = pd.DataFrame(data, columns=headers)

        # 엑셀 파일 저장
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "엑셀 파일 저장", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if file_path:
            df.to_excel(file_path, index=False, sheet_name="Table Data")

    # 타이머 설정
    def setup_timer(self):
        # UI 구성 (생략 - 버튼 추가 등)
        self.daily_timer = QTimer(self)
        self.daily_timer.timeout.connect(self.start_daily_worker)
        self.start_daily_timer()

    # 매일 12시
    def start_daily_timer(self):
        """24시에 실행되도록 타이머 설정"""
        now = QTime.currentTime()
        target_time = QTime(0, 0)  # 자정 (0시 0분)

        interval = now.msecsTo(target_time)

        if interval <= 0:
            interval += 24 * 60 * 60 * 1000  # 이미 자정을 지났으면 다음 날 자정으로 설정

        # 첫 실행: 정확히 자정에 작업 실행
        QTimer.singleShot(interval, self.start_daily_worker)

        # 이후 매일 반복 실행: 24시간 간격으로 타이머 시작
        self.daily_timer.start(24 * 60 * 60 * 1000)


    def start_daily_worker(self):

        # 기존 스레드 중지
        if hasattr(self, 'countdown_thread') and self.countdown_thread.isRunning():
            self.countdown_thread.running = False
            self.countdown_thread.wait()

        # 새로운 카운트다운 스레드 시작
        self.countdown_thread = CountdownThread()
        self.countdown_thread.time_updated.connect(self.update_time_label)
        self.countdown_thread.start()

        self.add_log(f"스케줄러 수집 시작")
        """24시에 실행되는 ApiWorker 시작"""
        if self.daily_worker is not None and self.daily_worker.isRunning():
            self.daily_worker.terminate()
            self.daily_worker.wait()
        self.get_api('all')


    def update_time_label(self, time_text):
        """타임 라벨 업데이트"""
        self.time_label.setText(f"추적시간 매일 0시 0분 0초 (남은시간 : {time_text})")


    def start_on_demand_worker(self):
        """사용자 요청 시 실행되는 ApiWorker 시작"""
        if self.on_demand_worker is not None and self.on_demand_worker.isRunning():
            self.on_demand_worker.terminate()
            self.on_demand_worker.wait()

        self.get_api('select')



    def get_checked_urls(self):
        """테이블에서 체크박스가 체크된 URL 목록 추출"""
        table_url_list = []

        for row in range(self.table.rowCount()):
            # 첫 번째 열(체크박스 열)의 상태 확인
            container_widget = self.table.cellWidget(row, 0)  # 첫 번째 열에 체크박스가 있는지 확인
            if container_widget:
                layout = container_widget.layout()
                if layout and layout.count() > 0:
                    check_box = layout.itemAt(0).widget()
                    if isinstance(check_box, QCheckBox) and check_box.isChecked():
                        # 체크된 행의 URL 추출 (마지막 열이 URL이라고 가정)
                        url_item = self.table.item(row, 6)
                        if url_item:  # URL 항목이 존재하면 추가
                            table_url_list.append(url_item.text())
                        else:
                            self.add_log(f"행 {row}: URL 이 없습니다.")

        self.add_log(f"체크된 URL 수: {len(table_url_list)}")

        # 디버깅 출력
        return table_url_list


    def get_all_urls(self):
        """테이블에서 모든 URL 추출"""
        table_url_list = []

        for row in range(self.table.rowCount()):
            # URL 열(여기서는 6번 열)을 가져옴
            url_item = self.table.item(row, 6)
            if url_item:  # URL 항목이 존재하면 추가
                url = url_item.text().strip()  # 공백 제거
                if url:  # 빈 문자열이 아닌 경우만 추가
                    table_url_list.append(url)
                else:
                    self.add_log(f"행 {row}: URL 이 없습니다.")

        # 디버깅 출력
        self.add_log(f"전체 URL 수: {len(table_url_list)}")
        return table_url_list

    
    # 화면 중앙
    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    
    # 개별 등록 팝업
    def open_register_popup(self):
        # 등록 팝업창 열기
        popup = RegisterPopup(parent=self)
        popup.exec_()
        self.save_table_to_excel("DB.xlsx")


    # 전체 등록 팝업
    def open_all_register_popup(self):
        # 등록 팝업창 열기
        popup = AllRegisterPopup(parent=self)  # 부모 객체 전달
        popup.exec_()
        self.save_table_to_excel("DB.xlsx")


    def get_api(self, type):
        table_url_list = []
        # 체크된 URL 목록 가져오기
        if type == 'all':
            table_url_list = self.get_all_urls()
        else:
            table_url_list = self.get_checked_urls()

        # 유효성 검사 및 빈 값 제거
        table_url_list = [url for url in table_url_list if url.strip()]

        if table_url_list:
            self.daily_worker = ApiWorker(table_url_list, self)
            self.daily_worker.api_data_received.connect(self.set_result)
            self.daily_worker.start()


    def set_result(self, result_list):
        for result in result_list:
            if result["status"] == "success":
                result_data = result["data"]
                url_to_update = result_data["URL"]

                # 테이블에서 URL 열(6번째 열)을 기준으로 해당 URL이 있는지 확인
                row_to_update = -1  # 업데이트할 행을 저장 (-1은 없음을 의미)
                for row in range(self.table.rowCount()):
                    url_item = self.table.item(row, 6)
                    if url_item and url_item.text() == url_to_update:
                        row_to_update = row
                        break

                if row_to_update != -1:
                    # URL이 이미 테이블에 있는 경우: 데이터를 업데이트
                    self.table.setItem(row_to_update, 1, QTableWidgetItem(result_data["최근실행시간"]))
                    self.table.setItem(row_to_update, 2, QTableWidgetItem(result_data["상품명"]))
                    self.table.setItem(row_to_update, 3, QTableWidgetItem(result_data["판매가"]))
                    self.table.setItem(row_to_update, 4, QTableWidgetItem(result_data["배송비"]))
                    self.table.setItem(row_to_update, 5, QTableWidgetItem(result_data["합계"]))

        # 수집이 끝나면 DB.xlsx 파일 업데이트
        self.save_table_to_excel("DB.xlsx")


    def save_table_to_excel(self, file_path):
        """테이블 데이터를 엑셀 파일로 저장"""
        import pandas as pd

        # 테이블 데이터를 추출
        row_count = self.table.rowCount()
        column_count = self.table.columnCount()
        data = []

        for row in range(row_count):
            row_data = []
            for col in range(column_count):
                # 체크박스 컬럼(0번)은 제외하고 데이터를 가져옴
                if col == 0:
                    continue
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)

        # 데이터프레임 생성
        df = pd.DataFrame(data, columns=[self.table.horizontalHeaderItem(i).text() for i in range(1, column_count)])

        # 엑셀 파일로 저장
        try:
            df.to_excel(file_path, index=False, sheet_name="Table Data")
            self.add_log(f"DB 업데이트 성공: {file_path}")
        except Exception as e:
            self.add_log(f"DB 업데이트 실패: {str(e)}")

                    
    # 경고 alert창
    def show_warning(self, message):
        # QMessageBox 생성
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)  # 경고 아이콘 설정
        msg.setWindowTitle("경고")  # 창 제목 설정
        msg.setText(message)  # 메시지 내용 설정
        msg.setStandardButtons(QMessageBox.Ok)  # 버튼 설정 (OK 버튼만 포함)
        msg.exec_()  # 메시지 박스 표시


    # 테이블 체크박스 된것 삭제
    def delete_table_row(self):
        """체크된 체크박스를 가진 행을 삭제"""
        rows_to_delete = []

        # 모든 행을 확인하여 체크박스가 체크된 행을 찾음
        for row in range(self.table.rowCount()):
            container_widget = self.table.cellWidget(row, 0)  # 첫 번째 열의 컨테이너 위젯 가져오기
            if container_widget:  # 위젯이 존재할 경우
                layout = container_widget.layout()  # 레이아웃 가져오기
                if layout and layout.count() > 0:  # 레이아웃이 있고, 위젯이 포함된 경우
                    check_box = layout.itemAt(0).widget()  # 첫 번째 위젯(QCheckBox) 가져오기
                    if isinstance(check_box, QCheckBox) and check_box.isChecked():  # 체크박스 확인
                        rows_to_delete.append(row)

        # 삭제하려는 행을 역순으로 삭제
        for row in reversed(rows_to_delete):
            self.table.removeRow(row)  # 테이블에서 행 삭제

        # 삭제 결과 출력
        self.add_log(f"{len(rows_to_delete)}개의 행이 삭제되었습니다.")
        self.save_table_to_excel("DB.xlsx")


    # 테이블 초기화
    def reset_url(self):

        self.table.clearContents()  # 테이블 내용 삭제
        self.table.setRowCount(0)   # 행 개수를 0으로 설정

        self.add_log('테이블이 초기화 되었습니다.')
        self.save_table_to_excel("DB.xlsx")
