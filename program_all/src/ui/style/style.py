from PyQt5.QtWidgets import QPushButton, QLineEdit
from PyQt5.QtCore import Qt

LOG_STYLE = """
    background-color: #f9f9f9; 
    border: 1px solid #ccc; 
    padding: 5px;
"""

HEADER_TEXT_STYLE = """
    font-size: 18px; 
    font-weight: bold; 
    background-color: white; 
    color: black; 
    padding: 10px;
"""


def apply_common_button_style(button: QPushButton, bg_color: str = "#4682B4", width: int = 140):
    button.setStyleSheet(main_style(bg_color))
    button.setFixedHeight(40)
    button.setFixedWidth(width)
    button.setCursor(Qt.PointingHandCursor)


def create_common_button(
        text: str,
        on_click,                         # 반드시 두 번째 인자가 콜백 함수여야 함
        bg_color: str = "#4682B4",
        width: int = 140
) -> QPushButton:
    button = QPushButton(text)
    apply_common_button_style(button, bg_color, width)
    button.clicked.connect(on_click)
    return button

def main_style(color):
    return f"""
        border-radius: 20px;
        border: 2px solid {color};
        padding: 10px;
        font-weight: 490;
        font-size: 15px;
        color: #333333;
    """


def create_line_edit(placeholder: str, pw: bool = False, color: str = "#888888",
                     width: int = 300) -> QLineEdit:
    line_edit = QLineEdit()
    line_edit.setPlaceholderText(placeholder)
    line_edit.setStyleSheet(main_style(color))
    line_edit.setFixedHeight(40)
    line_edit.setFixedWidth(width)
    if pw:
        line_edit.setEchoMode(QLineEdit.Password)
    return line_edit
