from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QComboBox, QCheckBox
)

from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon
from PyQt5.QtCore import Qt, pyqtSignal

from src.ui.style.style import create_common_button


class ParamSetPop(QDialog):

    log_signal = pyqtSignal(str)  # 🔧 여기에 시그널 정의 필요

    def __init__(self, parent=None):
        super().__init__(parent)
        self.confirm_button = None
        self.cancel_button = None
        self.cancel_button = None
        self.parent = parent
        self.input_fields = {}

        self.set_layout()

    def set_layout(self):
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
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        popup_layout.addWidget(title_label)

        for item in self.parent.setting:
            item_type = item.get("type", "input")

            # ✅ 개별 항목 레이아웃 (간격 포함용)
            item_layout = QVBoxLayout()
            item_layout.setContentsMargins(0, 12, 0, 0)  # 위쪽 마진만 주기
            item_layout.setSpacing(5)

            # 라벨
            label = QLabel(item["name"])
            label.setStyleSheet("font-weight: bold; font-size: 13px;")
            item_layout.addWidget(label)

            if item_type == "input":
                line_edit = QLineEdit(self)
                line_edit.setText(str(item.get("value", "")))
                line_edit.setFixedHeight(40)
                line_edit.setStyleSheet("""
                    border-radius: 10%;
                    border: 2px solid #888888;
                    padding: 10px;
                    font-size: 14px;
                    color: #333333;
                """)
                self.input_fields[item["code"]] = line_edit
                item_layout.addWidget(line_edit)

            elif item_type == "select":
                combo = QComboBox(self)
                combo.setFixedHeight(40)
                combo.setStyleSheet("""
                    QComboBox {
                        border-radius: 10%;
                        border: 2px solid #888888;
                        padding: 10px;
                        font-size: 14px;
                        color: #333333;
                    }
                    QComboBox::drop-down { border: none; }
                """)
                options = [
                    {"key": "▼ 선택 ▼", "value": ""}
                ]
                for opt in options:
                    combo.addItem(opt["key"], opt["value"])
                combo.setCurrentIndex(0)
                self.input_fields[item["code"]] = combo
                item_layout.addWidget(combo)

            elif item_type == "button":
                line_edit = QLineEdit(self)
                line_edit.setText(str(item.get("value", "")))
                line_edit.setFixedHeight(40)
                line_edit.setStyleSheet("""
                    border-radius: 10%;
                    border: 2px solid #888888;
                    padding: 10px;
                    font-size: 14px;
                    color: #333333;
                """)

                self.input_fields[item["code"]] = line_edit
                item_layout.addWidget(line_edit)

                btn = QPushButton("조회", self)
                btn.setFixedHeight(40)
                btn.setStyleSheet("""
                    background-color: black;
                    color: white;
                    border-radius: 10%;
                    font-size: 14px;
                """)
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(lambda _, c=item["code"]: self.on_button_clicked(c))  # ✅ 여기 중요

                item_layout.addWidget(btn)

            elif item_type == "check":
                checkbox = QCheckBox(self)
                checkbox.setChecked(bool(item.get("value")))  # True/False 초기값
                checkbox.setStyleSheet("""
                    QCheckBox {
                        font-size: 14px;
                        color: #333333;
                        padding: 5px;
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
                        image: url(:/icons/check-white.png);  /* ✔ 아이콘 넣을 수도 있음 */
                    }
                """)
                checkbox.setCursor(Qt.PointingHandCursor)

                self.input_fields[item["code"]] = checkbox
                item_layout.addWidget(checkbox)


            # ✅ 최종적으로 popup_layout에 묶은 item_layout 추가
            popup_layout.addLayout(item_layout)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        self.cancel_button = create_common_button("취소", self.reject, "#cccccc", 140)

        self.confirm_button = create_common_button("확인", self.on_confirm, "black", 140)


        button_layout.setContentsMargins(0, 15, 0, 0)  # top에만 20px
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.confirm_button)
        popup_layout.addLayout(button_layout)

        self.center_window()


    def on_button_clicked(self, code):
        # 1. 입력값 가져오기
        input_widget = self.input_fields.get(code)
        if not input_widget:
            self.log_signal.emit(f"[{code}] 입력 필드를 찾을 수 없습니다.")
            return

        value = input_widget.text()

        # 2. 워커 클래스의 get_list 함수 실행
        if not self.parent.on_demand_worker:
            self.log_signal.emit(f"[{self.site}]에 해당하는 워커 클래스가 없습니다.")
            return

        try:
            result_list = self.parent.on_demand_worker.get_list(value)  # 👈 value를 인자로 넘김
            self.log_signal.emit(f"[{code}] 결과 수신 완료: {result_list}")

            # 3. 결과를 select(QComboBox)에 반영할 대상 코드 추정 (예: "{code}_select")
            select_code = f"{code}_select"
            select_widget = self.input_fields.get(select_code)

            if isinstance(select_widget, QComboBox):
                select_widget.clear()
                select_widget.addItem("▼ 선택 ▼", "")

                for item in result_list:
                    name = item.get("key", "")
                    val = item.get("value", "")
                    select_widget.addItem(name, val)

                select_widget.setCurrentIndex(0)
            else:
                self.log_signal.emit(f"[{select_code}] select 위젯이 없습니다.")
        except Exception as e:
            self.log_signal.emit(f"[{code}] 실행 중 오류: {e}")


    def on_confirm(self):
        for item in self.parent.setting:
            code = item["code"]
            widget = self.input_fields.get(code)

            if widget is None:
                continue

            # QLineEdit
            if isinstance(widget, QLineEdit):
                text = widget.text()
                try:
                    item["value"] = int(text)
                except ValueError:
                    item["value"] = text
            # QComboBox
            elif isinstance(widget, QComboBox):
                value = widget.currentData()  # 실제 값 (value)
                item["value"] = value

            # ✅ QCheckBox 처리 추가
            elif isinstance(widget, QCheckBox):
                item["value"] = widget.isChecked()


        self.log_signal.emit(f'setting : {self.parent.setting}')
        self.accept()


    def center_window(self):
        frame_geometry = self.frameGeometry()
        center_point = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
