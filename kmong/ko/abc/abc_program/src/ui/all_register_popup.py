import pandas as pd
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidgetItem,
                             QCheckBox, QDesktopWidget, QDialog, QTableWidget, QSizePolicy, QHeaderView, QScrollArea)

from src.ui.excel_drag_drop_label import ExcelDragDropLabel

url_list = []

# 전체등록
class AllRegisterPopup(QDialog):

    updateList = pyqtSignal(list)  # 파일 경로를 전달하는 시그널

    # 초기화
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 객체 저장
        self.setWindowTitle("엑셀 파일 드래그 앤 드롭")
        self.setGeometry(200, 200, 800, 600)  # 팝업 창 크기 설정
        self.setStyleSheet("background-color: white;")
        self.url_list = []
        # 팝업 레이아웃
        self.layout = QVBoxLayout(self)

        # 드래그 앤 드롭 라벨 추가
        self.drag_drop_label = ExcelDragDropLabel()
        self.drag_drop_label.fileDropped.connect(self.load_excel)  # 시그널 연결

        self.layout.addWidget(self.drag_drop_label)

        # 테이블 뷰 추가 (스크롤 가능)
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(1)  # 컬럼 수를 1개로 설정
        self.table_widget.setHorizontalHeaderLabels(["URL"])  # 컬럼 헤더 이름 설정

        # 헤더의 크기를 창 너비에 맞게 조정
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        # 스크롤 영역 설정
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.table_widget)
        scroll_area.setWidgetResizable(True)
        # scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.layout.addWidget(scroll_area)

        # 확인 버튼
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
        self.confirm_button.setFixedWidth(140)
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.clicked.connect(self.on_confirm)

        button_layout.addWidget(self.confirm_button)
        button_layout.setAlignment(Qt.AlignCenter)
        self.layout.addLayout(button_layout)

        # 연결
        self.center_window()

    # load_excel 함수
    def load_excel(self, file_paths):
        """
        여러 파일에서 첫 번째 컬럼 데이터를 URL 배열로 만드는 메서드
        """
        try:
            # 여러 파일의 데이터를 병합
            combined_data = []  # 데이터프레임을 병합할 리스트

            for file in file_paths:
                if file.endswith('.csv'):
                    df = pd.read_csv(file)  # CSV 파일 읽기
                else:
                    df = pd.read_excel(file)  # 엑셀 파일 읽기
                combined_data.append(df)

            combined_df = pd.concat(combined_data, ignore_index=True)  # 모든 파일 데이터 병합

            # 첫 번째 컬럼 데이터 추출
            self.url_list.clear()  # 기존 URL 리스트 초기화

            # combined_df.iloc[:, 0]: 데이터프레임의 첫 번째 컬럼만 선택.
            # .dropna(): NaN 값을 제거.
            # .astype(str).tolist(): 데이터를 문자열로 변환하고 Python 리스트로 변환.
            self.url_list.extend(combined_df.iloc[:, 0].dropna().astype(str).tolist())  # 첫 번째 컬럼 값 추출

            # 테이블 위젯 초기화
            self.table_widget.setRowCount(len(self.url_list))
            self.table_widget.setColumnCount(1)  # URL만 표시
            self.table_widget.setHorizontalHeaderLabels(["URL"])

            # 데이터 로드
            for row_idx, url in enumerate(self.url_list):
                # 수정해서 쓰려면 이렇게
                # self.table_widget.setItem(row_idx, 0, QTableWidgetItem(url))

                # ReadOnly로
                item = QTableWidgetItem(url)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 셀을 읽기 전용으로 설정
                self.table_widget.setItem(row_idx, 0, item)


            # 상태 업데이트
            self.drag_drop_label.setText(f"총 {len(file_paths)}개의 파일이 성공적으로 로드되었습니다.")
            self.drag_drop_label.setStyleSheet("background-color: lightgreen;")

        except Exception as e:
            self.drag_drop_label.setText(f"파일 로드 중 오류 발생: {str(e)}")


    # 중앙에 화면 배치
    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)


    # 확인버튼
    def on_confirm(self):
        self.updateList.emit(self.url_list)
        self.accept()  # 팝업 닫기`