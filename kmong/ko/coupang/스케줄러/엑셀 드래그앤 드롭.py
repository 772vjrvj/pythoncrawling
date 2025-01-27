import sys
import pandas as pd  # pandas를 사용하여 엑셀 파일 처리
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

class ExcelDragDropLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)  # 드래그 앤 드롭 허용
        self.setText("엑셀 파일을 여기에 드래그하세요.")
        self.setAlignment(Qt.AlignCenter)  # 텍스트 가운데 정렬
        self.setStyleSheet("border: 2px dashed #aaaaaa; padding: 10px;")  # 스타일 추가
        self.setWordWrap(True)  # 텍스트 줄바꿈

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():  # 파일 드래그 확인
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            for file in files:
                if file.endswith(('.xlsx', '.xlsm')):  # 엑셀 파일만 처리
                    self.setText(f"Processing file: {file}")
                    self.read_excel(file)
                else:
                    self.setText(f"Unsupported file type: {file}")
            event.acceptProposedAction()

    def read_excel(self, file_path):
        try:
            # pandas로 엑셀 파일 읽기
            df = pd.read_excel(file_path)
            rows = df.values.tolist()  # 데이터프레임을 리스트로 변환

            # 텍스트에 결과 출력 (모든 행 표시)
            self.setText(f"Rows from {file_path}:\n" +
                         "\n".join(str(row) for row in rows))

            print(df)  # 전체 데이터프레임을 콘솔에 출력

        except Exception as e:
            self.setText(f"Error reading file: {file_path}\n{str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel Drag and Drop Example")
        self.resize(800, 600)  # 기본 창 크기 설정

        layout = QVBoxLayout()

        # 드래그 앤 드롭 가능한 QLabel 생성
        self.label = ExcelDragDropLabel()

        # QLabel을 QScrollArea에 추가
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.label)
        scroll_area.setWidgetResizable(True)  # 위젯 크기 자동 조정
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # 세로 스크롤 항상 표시
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 가로 스크롤 필요 시 표시

        layout.addWidget(scroll_area)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
