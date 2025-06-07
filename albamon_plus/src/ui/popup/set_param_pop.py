from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon
from PyQt5.QtCore import Qt, pyqtSignal


class SetParamPop(QDialog):

    log_signal = pyqtSignal(str)  # 🔧 여기에 시그널 정의 필요


    def __init__(self, setting):
        super().__init__()
        self.setting = setting  # 참조 유지
        self.input_fields = {}

        self.setWindowTitle("설정")
        self.resize(400, 100)  # 초기 크기 (자동 확장 허용)
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: white;")

        # 회색 정사각형 아이콘 생성
        icon_pixmap = QPixmap(32, 32)
        icon_pixmap.fill(QColor("transparent"))
        painter = QPainter(icon_pixmap)
        painter.setBrush(QColor("#e0e0e0"))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, 32, 32)
        painter.end()
        self.setWindowIcon(QIcon(icon_pixmap))

        # 전체 레이아웃
        popup_layout = QVBoxLayout(self)
        popup_layout.setContentsMargins(10, 10, 10, 10)
        popup_layout.setSpacing(5)

        # 제목
        title_label = QLabel("설정 파라미터 세팅")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            margin: 10px 0;
            padding: 5px 0;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        popup_layout.addWidget(title_label)

        # 설정 항목들
        for item in self.setting:
            label = QLabel(item["name"])
            label.setStyleSheet("font-weight: bold; font-size: 13px;")
            popup_layout.addWidget(label)

            line_edit = QLineEdit(self)
            line_edit.setPlaceholderText(item["code"])
            line_edit.setText(str(item.get("value", "")))
            line_edit.setStyleSheet("""
                border-radius: 10%;
                border: 2px solid #888888;
                padding: 10px;
                font-size: 14px;
                color: #333333;
            """)
            line_edit.setFixedHeight(40)
            self.input_fields[item["code"]] = line_edit
            popup_layout.addWidget(line_edit)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("취소", self)
        self.cancel_button.setStyleSheet("""
            background-color: #cccccc;
            color: black;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.setFixedWidth(140)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self.reject)

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

        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.confirm_button)
        popup_layout.addLayout(button_layout)

        self.center_window()

    def on_confirm(self):
        for item in self.setting:
            code = item["code"]
            line_edit = self.input_fields.get(code)
            if line_edit:
                text = line_edit.text()
                try:
                    item["value"] = int(text)
                except ValueError:
                    item["value"] = text
        self.log_signal.emit(f'setting : {self.setting}')
        self.accept()

    def center_window(self):
        frame_geometry = self.frameGeometry()
        center_point = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
