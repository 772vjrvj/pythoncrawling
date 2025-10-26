from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QCheckBox, QPushButton,
    QHBoxLayout, QSizePolicy, QWidget, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from src.ui.style.style import create_common_button


class SiteSetPop(QDialog):
    log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.confirm_btn = None
        self.cancel_btn = None
        self.parent = parent
        self.setWindowTitle("사이트 선택")
        self.resize(700, 450)
        self.setMinimumWidth(700)
        self.setStyleSheet("background-color: white;")
        self.checkbox_map = {}
        self.all_checkbox = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title_label = QLabel("사이트 선택")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(title_label)

        # ✅ 전체 선택 체크박스
        self.all_checkbox = QCheckBox("전체 선택")
        self.all_checkbox.setCursor(Qt.PointingHandCursor)
        self.all_checkbox.setStyleSheet(self.checkbox_style())
        self.all_checkbox.stateChanged.connect(self.handle_all_checkbox_click)

        # ✅ 초기 상태 설정
        total = len(self.parent.sites)
        checked_count = sum(1 for col in self.parent.sites if col.get("checked", True))
        if checked_count == total:
            self.all_checkbox.setCheckState(Qt.Checked)
        elif checked_count == 0:
            self.all_checkbox.setCheckState(Qt.Unchecked)
        else:
            self.all_checkbox.setCheckState(Qt.PartiallyChecked)

        layout.addWidget(self.all_checkbox)

        # ✅ 사이트 체크박스들을 그리드로 나열
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        col_per_row = 5
        for idx, col in enumerate(self.parent.sites):
            checkbox = QCheckBox(col["value"])
            checkbox.setChecked(col.get("checked", True))
            checkbox.setCursor(Qt.PointingHandCursor)
            checkbox.setStyleSheet(self.checkbox_style())
            checkbox.stateChanged.connect(self.update_all_checkbox_state)
            self.checkbox_map[col["code"]] = checkbox

            row = idx // col_per_row
            col_in_row = idx % col_per_row
            grid_layout.addWidget(checkbox, row, col_in_row)

        layout.addWidget(grid_widget)

        # ✅ 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 15, 0, 0)

        self.cancel_btn = create_common_button("취소", self.reject, "#cccccc", 140)

        self.confirm_btn = create_common_button("확인", self.confirm_selection, "black", 140)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.confirm_btn)
        layout.addLayout(btn_layout)

    def handle_all_checkbox_click(self):
        all_checked = all(cb.isChecked() for cb in self.checkbox_map.values())

        # ✅ 전체 해제 또는 전체 선택
        for checkbox in self.checkbox_map.values():
            checkbox.blockSignals(True)
            checkbox.setChecked(not all_checked)
            checkbox.blockSignals(False)

        self.update_all_checkbox_state()

    def update_all_checkbox_state(self):
        total = len(self.checkbox_map)
        checked_count = sum(1 for cb in self.checkbox_map.values() if cb.isChecked())

        self.all_checkbox.blockSignals(True)
        if checked_count == total:
            self.all_checkbox.setCheckState(Qt.Checked)
        elif checked_count == 0:
            self.all_checkbox.setCheckState(Qt.Unchecked)
        else:
            self.all_checkbox.setCheckState(Qt.PartiallyChecked)
        self.all_checkbox.blockSignals(False)

    def confirm_selection(self):
        # ✅ checked 상태를 사이트 객체에 반영
        for col in self.parent.sites:
            checkbox = self.checkbox_map.get(col["code"])
            if checkbox:
                col["checked"] = checkbox.isChecked()
        self.accept()

    def checkbox_style(self):
        return """
            QCheckBox {
                font-size: 14px;
                color: #333;
                padding: 4px 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #888888;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: black;
            }
        """

    def button_style(self, bg_color, font_color):
        return f"""
            background-color: {bg_color};
            color: {font_color};
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """

    def showEvent(self, event):
        super().showEvent(event)
        self.update_all_checkbox_state()
