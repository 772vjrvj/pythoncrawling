import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidgetItem,
                             QCheckBox, QDesktopWidget, QDialog, QTableWidget, QSizePolicy, QHeaderView, QScrollArea)

from src.ui.excel_drag_drop_label import ExcelDragDropLabel

url_list = []

# 전체등록
class AllRegisterPopup(QDialog):
    
    # 초기화
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 객체 저장
        self.setWindowTitle("엑셀 파일 드래그 앤 드롭")
        self.setGeometry(200, 200, 800, 600)  # 팝업 창 크기 설정
        self.setStyleSheet("background-color: white;")

        # 팝업 레이아웃
        self.layout = QVBoxLayout(self)

        # 드래그 앤 드롭 라벨 추가
        self.drag_drop_label = ExcelDragDropLabel()
        self.layout.addWidget(self.drag_drop_label)

        # 테이블 뷰 추가 (스크롤 가능)
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(1)  # 컬럼 수를 1개로 설정
        self.table_widget.setHorizontalHeaderLabels(["ID"])  # 컬럼 헤더 이름 설정

        # 헤더의 크기를 창 너비에 맞게 조정
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        # 스크롤 영역 설정
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.table_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

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
        self.drag_drop_label.setParent(self)
        self.center_window()

    # load_excel 함수
    def load_excel(self, file_path):
        global url_list
        try:
            df = pd.read_excel(file_path)

            # 특정 열만 추출 (URL 열)
            if "ID" in df.columns:
                url_list.clear()  # 기존 데이터 초기화
                url_list.extend(df["ID"].dropna().astype(str).tolist())  # 전역 변수 업데이트
            else:
                url_list.clear()
                url_list.extend(df.apply(lambda row: ", ".join(row.dropna().astype(str)), axis=1).tolist())

            # 테이블 위젯 초기화
            self.table_widget.setRowCount(len(url_list))
            self.table_widget.setColumnCount(1)  # URL만 표시
            self.table_widget.setHorizontalHeaderLabels(["플레이스 ID"])

            # 데이터 로드
            for row_idx, url in enumerate(url_list):
                self.table_widget.setItem(row_idx, 0, QTableWidgetItem(url))

            # 상태 업데이트
            self.drag_drop_label.setText(f"파일이 성공적으로 로드되었습니다: {file_path}")
            self.drag_drop_label.setStyleSheet("background-color: lightgreen;")

        except Exception as e:
            self.drag_drop_label.setText(f"파일 로드 중 오류 발생: {file_path}\n{str(e)}")

    # 중앙에 화면 배치
    def center_window(self):
        """화면 중앙에 창을 배치"""
        screen = QDesktopWidget().screenGeometry()  # 화면 크기 가져오기
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    # 확인버튼
    def on_confirm(self):
        global url_list
        self.parent.set_url_list(url_list)
        self.accept()  # 팝업 닫기`