import pandas as pd
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QTableWidgetItem, QDesktopWidget, QDialog, QTableWidget, QHeaderView, QScrollArea
from src.ui.excel_drag_drop_label import ExcelDragDropLabel


class AllRegisterPopup(QDialog):

    updateList = pyqtSignal(list)  # 파일 경로를 전달하는 시그널

    # 초기화
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 객체 저장
        self.setWindowTitle("엑셀 파일 드래그 앤 드롭")
        self.setGeometry(200, 200, 800, 600)  # 팝업 창 크기 설정
        self.setStyleSheet("background-color: white;")
        self.id_list = []
        self.layout = QVBoxLayout(self)
        self.drag_drop_label = ExcelDragDropLabel()
        self.drag_drop_label.fileDropped.connect(self.load_excel)  # 시그널 연결
        self.layout.addWidget(self.drag_drop_label)
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(1)  # 컬럼 수를 2개로 설정
        self.table_widget.setHorizontalHeaderLabels(["ID"])  # 컬럼 헤더 이름 설정
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.table_widget)
        scroll_area.setWidgetResizable(True)
        self.layout.addWidget(scroll_area)
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
        self.center_window()

    # load_excel 함수
    def load_excel(self, file_paths):
        try:
            combined_data = []
            for file in file_paths:
                if file.endswith('.csv'):
                    df = pd.read_csv(file)  # CSV 파일 읽기
                else:
                    df = pd.read_excel(file)  # 엑셀 파일 읽기
                combined_data.append(df)
            combined_df = pd.concat(combined_data, ignore_index=True)
            self.id_list.clear()

            # combined_df.iloc[:, 0]: 데이터프레임의 첫 번째 컬럼만 선택.
            # .dropna(): NaN 값을 제거.
            # .astype(str).tolist(): 데이터를 문자열로 변환하고 Python 리스트로 변환.
            id_list = combined_df.iloc[:, 0].dropna().astype(str).tolist()

            self.id_list = id_list  # 리스트로 저장

            # 테이블 위젯 초기화
            self.table_widget.setRowCount(len(self.id_list))
            self.table_widget.setColumnCount(1)  # ID, PASSWORD 컬럼 설정
            self.table_widget.setHorizontalHeaderLabels(["ID"])

            # 데이터 로드
            for row_idx, id_value in enumerate(self.id_list):  # 튜플 언패킹 제거
                id_item = QTableWidgetItem(id_value)
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)  # 읽기 전용 설정
                self.table_widget.setItem(row_idx, 0, id_item)


            # 상태 업데이트
            self.drag_drop_label.setText(f"총 {len(file_paths)}개의 행이 성공적으로 로드되었습니다.")
            self.drag_drop_label.setStyleSheet("background-color: lightgreen;")

        except Exception as e:
            self.drag_drop_label.setText(f"파일 로드 중 오류 발생: {str(e)}")

    # 중앙에 화면 배치
    def center_window(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()  # 현재 창 크기
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    # 확인버튼
    def on_confirm(self):
        self.updateList.emit(self.id_list)
        self.accept()