from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QCheckBox, QHBoxLayout,
    QSizePolicy, QWidget, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from src.ui.style.style import create_common_button


class DetailSetPop(QDialog):
    log_signal = pyqtSignal(str)

    def __init__(self, parent=None, title="상세세팅"):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(title)
        self.resize(700, 520)
        self.setStyleSheet("background-color: white;")

        self.checkbox_map = {}
        self.all_checkbox = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title_label = QLabel(self.windowTitle())
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(title_label)

        self.all_checkbox = QCheckBox("전체 선택")
        self.all_checkbox.setCursor(Qt.PointingHandCursor)
        self.all_checkbox.setStyleSheet(self.checkbox_style())
        self.all_checkbox.stateChanged.connect(self.handle_all_checkbox_click)
        layout.addWidget(self.all_checkbox)

        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        rows = getattr(self.parent, "setting_detail", None) or []

        # === 신규 === 부모/자식 분리 파싱
        sections = [r for r in rows if r.get("row_type") == "section"]
        items = [r for r in rows if r.get("row_type") != "section"]  # 호환: 기존 row는 item으로 취급

        # === 신규 === 기존 구조 호환: row_type이 없다면 type을 parent_id로 간주
        for it in items:
            if "parent_id" not in it and it.get("type"):
                it["parent_id"] = it.get("type")

        # === 신규 === 섹션이 아예 없으면(기존 데이터) type 기준으로 섹션 자동 생성
        if not sections:
            seen = []
            for it in items:
                pid = it.get("parent_id") or "default"
                if pid in seen:
                    continue
                seen.append(pid)
                sections.append({"id": pid, "title": pid, "col_per_row": 5})

        cur_row = 0
        for sec in sections:
            sec_id = sec.get("id")
            sec_title = sec.get("title") or str(sec_id)
            col_per_row = int(sec.get("col_per_row") or 5)

            grid_layout.addWidget(self._make_section_label(sec_title), cur_row, 0, 1, col_per_row)
            cur_row += 1

            sec_items = [x for x in items if x.get("parent_id") == sec_id]
            self._add_checkboxes(grid_layout, sec_items, start_row=cur_row, col_per_row=col_per_row, sec_id=sec_id)

            # 섹션이 차지한 행 수만큼 증가
            cur_row += (len(sec_items) + col_per_row - 1) // col_per_row
            cur_row += 1  # 섹션 간 여백

        layout.addWidget(grid_widget)

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

    def _add_checkboxes(self, grid_layout, rows, start_row, col_per_row=5, sec_id=None):
        for idx, row in enumerate(rows):
            cb = QCheckBox(row.get("value") or "")
            cb.setChecked(bool(row.get("checked", True)))
            cb.setCursor(Qt.PointingHandCursor)
            cb.setStyleSheet(self.checkbox_style())
            cb.stateChanged.connect(self.update_all_checkbox_state)

            key = (sec_id or row.get("parent_id"), row.get("code"))
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
        rows = getattr(self.parent, "setting_detail", None) or []
        for row in rows:
            if row.get("row_type") == "section":
                continue

            # 호환: parent_id 없고 type 있으면 type을 parent_id로 봄
            pid = row.get("parent_id") or row.get("type")
            key = (pid, row.get("code"))
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
