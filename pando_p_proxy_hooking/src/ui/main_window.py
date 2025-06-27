#src/main_window.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QSizePolicy, QFrame, QSpacerItem, QDialog
)
from PyQt5.QtCore import Qt
from src.ui.store_dialog import StoreDialog
from src.utils.file_storage import load_data, save_data
import os
import subprocess


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PandoP")
        self.setMinimumSize(600, 200)
        self.setStyleSheet("""
            QWidget {
                background-color: #fff;
                font-family: Arial;
                font-size: 13px;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                padding: 6px 16px;
                border-radius: 4px;
                background-color: #4682B4;
                color: white;
                font-size: 13px;
            }
            QFrame#infoBox {
                border: 1px solid #ccc;
                padding: 20px;
                margin: 10px 20px;
                border-radius: 4px;
                background-color: #fafafa;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(10)

        title = QLabel("PandoP")
        title.setStyleSheet("font-size: 20px; margin: 10px 20px 0 20px;")
        layout.addWidget(title, alignment=Qt.AlignLeft)

        info_box = QFrame()
        info_box.setObjectName("infoBox")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(12)

        label_section = QLabel("매장 정보")
        label_section.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(label_section)

        row1 = QHBoxLayout()
        label1 = QLabel("● 매장명 :")
        self.store_name_value = QLabel("-")
        row1.addWidget(label1)
        row1.addSpacing(10)
        row1.addWidget(self.store_name_value)
        row1.addStretch()

        row2 = QHBoxLayout()
        label2 = QLabel("● 지점 :")
        self.branch_value = QLabel("-")
        row2.addWidget(label2)
        row2.addSpacing(10)
        row2.addWidget(self.branch_value)
        row2.addStretch()

        info_layout.addLayout(row1)
        info_layout.addLayout(row2)
        info_box.setLayout(info_layout)
        layout.addWidget(info_box)

        button_box = QHBoxLayout()
        self.store_button = QPushButton("등록")
        self.start_button = QPushButton("시작")

        self.store_button.setFixedWidth(130)
        self.start_button.setFixedWidth(130)

        button_box.addStretch()
        button_box.addWidget(self.store_button)
        button_box.addSpacing(20)
        button_box.addWidget(self.start_button)
        button_box.addStretch()

        layout.addLayout(button_box)
        layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(layout)
        self.setWindowFlag(Qt.Window)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)

        self.current_store_id = None
        self.load_store_id()

        self.store_button.clicked.connect(self.open_store_dialog)
        self.start_button.clicked.connect(self.start_action)

    def load_store_id(self):
        data = load_data()
        store_id = data.get('store_id', None)
        if store_id:
            self.current_store_id = store_id
        # 모달 기본값 업데이트는 open_store_dialog에서 처리

    def save_store_id(self, store_id):
        self.current_store_id = store_id
        data = load_data()
        data['store_id'] = store_id
        save_data(data)

    def open_store_dialog(self):
        dialog = StoreDialog(current_store_id=self.current_store_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            store_id = dialog.get_data()
            if store_id is not None:
                self.save_store_id(store_id)


    def start_action(self):
        if not self.current_store_id:
            # 여기서 경고 메시지 팝업 등 처리 가능
            return
        # 1) 프록시 서버 실행
        self.run_proxy()

    
    def run_proxy(self):
        # __file__ = src/ui/main_window.py
        # 프로젝트 루트 = src의 상위 폴더
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        bat_path = os.path.join(project_root, "bat", "run_mitmproxy.bat")
        bat_path = os.path.abspath(bat_path) # C:\Users\username\project\bat\run_mitmproxy.bat 절대 경로 변환
    
        print("[📡] 프록시 서버를 실행합니다...")
        subprocess.Popen(bat_path, shell=True)