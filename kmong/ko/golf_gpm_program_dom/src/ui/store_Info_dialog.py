from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton


class StoreInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("매장 정보 등록")
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setFixedSize(320, 180)
        self.setStyleSheet("background-color: #ffffff;")

        self.settings = QSettings("MyCompany", "PandoGL")

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(20, 20, 20, 20)

        # 제목
        title = QLabel("매장 정보")
        title.setStyleSheet("font-weight: bold; font-size: 15px; color: #222222; padding: 6px;")
        layout.addWidget(title)

        # 매장 ID 라벨 + 입력창
        store_row = QHBoxLayout()
        store_label = QLabel("매장 ID")
        store_label.setFixedWidth(50)
        store_label.setStyleSheet("font-size: 13px; color: #444444;")
        self.store_input = QLineEdit()
        self.store_input.setPlaceholderText("")
        self.store_input.setStyleSheet("""
            font-size: 13px; padding: 6px;
            border: 1px solid #cccccc; border-radius: 4px;
        """)
        store_row.addWidget(store_label)
        store_row.addWidget(self.store_input)
        layout.addLayout(store_row)

        self.store_error = QLabel("")
        self.store_error.setStyleSheet("color: red; font-size: 11px; padding-left: 52px;")
        layout.addWidget(self.store_error)

        # 버튼 레이아웃
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 10, 0, 0)

        cancel_btn = QPushButton("취소")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(28)
        cancel_btn.setStyleSheet("""
            background-color: #aaaaaa;
            color: white;
            border-radius: 5px;
            font-size: 13px;
            padding: 5px 20px;
        """)
        cancel_btn.clicked.connect(self.reject)

        register_btn = QPushButton("등록")
        register_btn.setCursor(Qt.PointingHandCursor)
        register_btn.setFixedHeight(28)
        register_btn.setStyleSheet("""
            background-color: #4682B4;
            color: white;
            border-radius: 5px;
            font-size: 13px;
            padding: 5px 20px;
        """)
        register_btn.clicked.connect(self.validate_and_accept)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(register_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # 저장된 값 불러오기
        self.store_input.setText(self.settings.value("store/id", ""))

    def validate_and_accept(self):
        store_text = self.store_input.text().strip()
        if not store_text:
            self.store_error.setText("필수값 입니다.")
            return
        else:
            self.store_error.setText("")

        # 저장
        self.settings.setValue("store/id", store_text)
        self.accept()
