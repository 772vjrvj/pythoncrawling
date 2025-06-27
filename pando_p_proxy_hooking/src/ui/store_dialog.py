#src/store_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt

class StoreDialog(QDialog):
    def __init__(self, current_store_id="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("매장 정보 등록")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
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

        layout = QVBoxLayout()

        form_group = QVBoxLayout()

        label = QLabel("매장 ID")
        self.store_id_input = QLineEdit()
        self.store_id_input.setText(current_store_id)  # 기본값 세팅

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")

        form_group.addWidget(label)
        form_group.addWidget(self.store_id_input)
        form_group.addWidget(self.error_label)

        layout.addLayout(form_group)

        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("취소")
        save_btn = QPushButton("등록")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.on_save_clicked)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def on_save_clicked(self):
        store_id = self.store_id_input.text().strip()
        if not store_id:
            self.error_label.setText("필수값 입니다.")
        else:
            self.error_label.setText("")
            self.accept()

    def get_data(self):
        return self.store_id_input.text().strip()
