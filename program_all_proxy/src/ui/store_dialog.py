# src/ui/store_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt

class StoreDialog(QDialog):
    def __init__(self, current_store_id=""):
        super().__init__()
        self.save_btn = None
        self.cancel_btn = None
        self.store_id = None  # 저장될 매장 ID
        self.current_store_id = current_store_id  # 현재 설정된 매장 ID
        self.store_id_input = None  # QLineEdit 인스턴스
        self.error_label = None  # 에러 메시지 출력용 QLabel
        self.ui_set()  # UI 초기화

    def ui_set(self):
        self.setWindowTitle("매장 정보 등록")  # 다이얼로그 제목
        self.setMinimumSize(400, 200)  # 최소 크기 지정

        # 전체 위젯 스타일 지정
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;  /* 전체 배경 흰색 */
            }
            QLabel {
                font-size: 13px;
                color: #444;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
            QPushButton {
                padding: 6px 16px;
                border-radius: 4px;
                background-color: #4682B4;
                color: white;
                font-size: 13px;
            }
            QLabel#errorLabel {
                color: red;
                font-size: 11px;
                margin-top: 4px;
            }
        """)

        layout = QVBoxLayout()  # 다이얼로그 전체 수직 레이아웃

        form_group = QVBoxLayout()  # 입력 필드 그룹 수직 레이아웃

        label = QLabel("인증 key")  # 매장 ID 라벨
        label.setStyleSheet("font-weight: bold;")
        self.store_id_input = QLineEdit()  # 매장 ID 입력창
        self.store_id_input.setText(self.current_store_id)  # 기본값 설정

        self.error_label = QLabel("")  # 에러 메시지 표시용
        self.error_label.setObjectName("errorLabel")  # CSS 선택자용 ID 설정

        # 입력 폼 레이아웃 구성
        form_group.addWidget(label)
        form_group.addWidget(self.store_id_input)
        form_group.addWidget(self.error_label)

        layout.addLayout(form_group)  # 메인 레이아웃에 폼 추가

        button_layout = QHBoxLayout()  # 버튼 수평 레이아웃
        self.cancel_btn = QPushButton("취소")  # 취소 버튼
        self.cancel_btn.clicked.connect(self.reject)  # 취소 시 다이얼로그 닫기
        self.cancel_btn.setFixedWidth(130)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)

        self.save_btn = QPushButton("등록")  # 등록 버튼
        self.save_btn.clicked.connect(self.on_save_clicked)  # 등록 시 저장 처리
        self.save_btn.setFixedWidth(130)
        self.save_btn.setCursor(Qt.PointingHandCursor)

        button_layout.addStretch()  # 좌측 여백 확보
        button_layout.addWidget(self.cancel_btn)
        button_layout.addSpacing(20)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()  # 우측 여백 확보

        layout.addLayout(button_layout)  # 버튼 레이아웃을 메인 레이아웃에 추가
        self.setLayout(layout)  # 최종 레이아웃 설정
        self.setWindowFlag(Qt.Window)  # 창으로 표시
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)  # 최소/최대 버튼 허용


    def on_save_clicked(self):
        store_id = self.store_id_input.text().strip()  # 입력된 매장 ID
        if not store_id:
            self.error_label.setText("필수값 입니다.")  # 유효성 검사
        else:
            self.store_id = store_id  # 내부 변수에 저장
            self.accept()  # QDialog.Accepted 반환하며 닫힘

    def get_data(self):
        return self.store_id  # 저장된 매장 ID 반환
