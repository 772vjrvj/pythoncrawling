from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import QLabel


class ExcelDragDropLabel(QLabel):
    fileDropped = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setText("엑셀 파일을 여기에 드래그하세요.")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 2px dashed #aaaaaa; padding: 10px; font-size: 14px;")
        self.setFixedHeight(100)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        files = [url.toLocalFile() for url in event.mimeData().urls()]
        valid_files = [f for f in files if f.lower().endswith((".xlsx", ".xlsm", ".csv"))]
        if valid_files:
            self.fileDropped.emit(valid_files)
        else:
            self.setText("지원하지 않는 파일 형식입니다. 엑셀 파일을 드래그하세요.")

        event.acceptProposedAction()
