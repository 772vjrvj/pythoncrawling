from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import (QLabel,
                             QDesktopWidget)


# 엑셀 드래그
class ExcelDragDropLabel(QLabel):

    # 초기화
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)  # 드래그 앤 드롭 허용
        self.setText("엑셀 파일을 여기에 드래그하세요.")
        self.setAlignment(Qt.AlignCenter)  # 텍스트 가운데 정렬
        self.setStyleSheet("border: 2px dashed #aaaaaa; padding: 10px; font-size: 14px;")
        self.setFixedHeight(100)  # 라벨의 높이를 100px로 설정 (기본 높이의 약 2배)

    # 드래그 이벤트
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():  # 파일 드래그 확인
            event.acceptProposedAction()
        else:
            event.ignore()

    # 드랍 이벤트
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            for file in files:
                if file.endswith(('.xlsx', '.xlsm')):  # 엑셀 파일만 처리
                    self.parent().load_excel(file)
                else:
                    self.setText("지원하지 않는 파일 형식입니다. 엑셀 파일을 드래그하세요.")
            event.acceptProposedAction()
