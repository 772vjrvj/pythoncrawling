from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QCheckBox, QPushButton,
    QHBoxLayout, QSizePolicy, QWidget, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from src.ui.style.style import create_common_button


class DetailSetPop(QDialog):
    log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.confirm_btn = None
        self.cancel_btn = None
        self.parent = parent
        self.setWindowTitle("상세세팅")
        self.resize(700, 520)
        # self.resize(1200, 450)
        # self.setMinimumWidth(700)
        self.setStyleSheet("background-color: white;")
        self.checkbox_map = {}
        self.all_checkbox = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title_label = QLabel("상세세팅 (매물유형 / 거래유형)")
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
        layout.addWidget(self.all_checkbox)

        # ✅ 초기 상태 설정
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        rows = getattr(self.parent, "setting_detail", None) or []
        # 2그룹으로 나눠서 UI 배치
        rlet_rows = [x for x in rows if x.get("type") == "rlet_types"]
        trad_rows = [x for x in rows if x.get("type") == "trade_types"]

        # --- 매물유형 ---
        grid_layout.addWidget(self._make_section_label("매물유형"), 0, 0, 1, 5)
        self._add_checkboxes(grid_layout, rlet_rows, start_row=1, col_per_row=5)

        # --- 거래유형 ---
        base_row = 1 + ((len(rlet_rows) + 4) // 5) + 1
        grid_layout.addWidget(self._make_section_label("거래유형"), base_row, 0, 1, 5)
        self._add_checkboxes(grid_layout, trad_rows, start_row=base_row + 1, col_per_row=5)

        layout.addWidget(grid_widget)

        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 15, 0, 0)
        cancel_btn = create_common_button("취소", self.reject, "#cccccc", 140)
        confirm_btn = create_common_button("확인", self.confirm_selection, "black", 140)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)

        self.update_all_checkbox_state()

    def _make_section_label(self, text):
        lb = QLabel(text)
        lb.setStyleSheet("font-size: 15px; font-weight: bold; margin-top: 6px;")
        return lb

    def _add_checkboxes(self, grid_layout, rows, start_row, col_per_row=5):
        for idx, row in enumerate(rows):
            cb = QCheckBox(row.get("value") or "")
            cb.setChecked(bool(row.get("checked", True)))
            cb.setCursor(Qt.PointingHandCursor)
            cb.setStyleSheet(self.checkbox_style())
            cb.stateChanged.connect(self.update_all_checkbox_state)

            key = (row.get("type"), row.get("code"))
            self.checkbox_map[key] = cb

            r = start_row + (idx // col_per_row)
            c = idx % col_per_row
            grid_layout.addWidget(cb, r, c)

    def handle_all_checkbox_click(self):
        all_checked = all(cb.isChecked() for cb in self.checkbox_map.values())
        for cb in self.checkbox_map.values():
            cb.blockSignals(True)
            cb.setChecked(not all_checked)
            cb.blockSignals(False)
        self.update_all_checkbox_state()

    def update_all_checkbox_state(self):
        total = len(self.checkbox_map)
        checked_count = sum(1 for cb in self.checkbox_map.values() if cb.isChecked())

        self.all_checkbox.blockSignals(True)
        if total == 0 or checked_count == 0:
            self.all_checkbox.setCheckState(Qt.Unchecked)
        elif checked_count == total:
            self.all_checkbox.setCheckState(Qt.Checked)
        else:
            self.all_checkbox.setCheckState(Qt.PartiallyChecked)
        self.all_checkbox.blockSignals(False)

    def confirm_selection(self):
        # parent.setting_detail에 checked 반영
        rows = getattr(self.parent, "setting_detail", None) or []
        for row in rows:
            t = row.get("type")
            if t not in ("rlet_types", "trade_types"):
                continue
            key = (t, row.get("code"))
            cb = self.checkbox_map.get(key)
            if cb:
                row["checked"] = cb.isChecked()
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

    def showEvent(self, event):
        super().showEvent(event)
        self.update_all_checkbox_state()
