from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton


class LoginInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("로그인 정보 등록")
        self.setFixedSize(320, 220)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setStyleSheet("background-color: #ffffff;")

        self.settings = QSettings("MyCompany", "PandoGL")

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(20, 20, 20, 20)

        # 제목
        title = QLabel("로그인 정보")
        title.setStyleSheet("font-weight: bold; font-size: 15px; color: #222222; padding: 6px;")
        layout.addWidget(title)

        # 아이디 라벨 + 입력창 (수평 정렬)
        id_row = QHBoxLayout()
        id_label = QLabel("아이디")
        id_label.setFixedWidth(50)
        id_label.setStyleSheet("font-size: 13px; color: #444444;")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("")
        self.id_input.setStyleSheet("""
            font-size: 13px; padding: 6px;
            border: 1px solid #cccccc; border-radius: 4px;
        """)
        id_row.addWidget(id_label)
        id_row.addWidget(self.id_input)
        layout.addLayout(id_row)

        self.id_error = QLabel("")
        self.id_error.setStyleSheet("color: red; font-size: 11px; padding-left: 52px;")
        layout.addWidget(self.id_error)

        # 비밀번호 라벨 + 입력창 (수평 정렬)
        pw_row = QHBoxLayout()
        pw_label = QLabel("비밀번호:")
        pw_label.setFixedWidth(50)
        pw_label.setStyleSheet("font-size: 13px; color: #444444;")
        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("")
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setStyleSheet("""
            font-size: 13px; padding: 6px;
            border: 1px solid #cccccc; border-radius: 4px;
        """)
        pw_row.addWidget(pw_label)
        pw_row.addWidget(self.pw_input)
        layout.addLayout(pw_row)

        self.pw_error = QLabel("")
        self.pw_error.setStyleSheet("color: red; font-size: 11px; padding-left: 52px;")
        layout.addWidget(self.pw_error)

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
        self.id_input.setText(self.settings.value("login/id", ""))
        self.pw_input.setText(self.settings.value("login/password", ""))

    def validate_and_accept(self):
        id_text = self.id_input.text().strip()
        pw_text = self.pw_input.text().strip()
        has_error = False

        if not id_text:
            self.id_error.setText("필수값 입니다.")
            has_error = True
        else:
            self.id_error.setText("")

        if not pw_text:
            self.pw_error.setText("필수값 입니다.")
            has_error = True
        else:
            self.pw_error.setText("")

        if has_error:
            return

        # 저장
        self.settings.setValue("login/id", id_text)
        self.settings.setValue("login/password", pw_text)

        self.accept()
