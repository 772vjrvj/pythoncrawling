from PyQt5.QtCore import QRect
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (QHeaderView, QStyle, QStyleOptionButton)


# 체크박스 헤더 세팅
class HeaderWithCheckbox(QHeaderView):
    def __init__(self, orientation, parent=None, main_window=None):
        super().__init__(orientation, parent)
        self.main_window = main_window
        self.setSectionsClickable(True)  # 헤더 클릭 가능 설정
        self._is_checked = False

    def paintSection(self, painter, rect, logicalIndex):
        """헤더에 체크박스를 그림"""
        super().paintSection(painter, rect, logicalIndex)

        if logicalIndex == 0:  # 첫 번째 열에만 체크박스 표시
            option = QStyleOptionButton()
            checkbox_size = 20
            center_x = rect.x() + (rect.width() - checkbox_size) // 2
            center_y = rect.y() + (rect.height() - checkbox_size) // 2
            option.rect = QRect(center_x, center_y, checkbox_size, checkbox_size)
            option.state = QStyle.State_Enabled | (QStyle.State_On if self._is_checked else QStyle.State_Off)
            self.style().drawControl(QStyle.CE_CheckBox, option, painter)

    def mousePressEvent(self, event: QMouseEvent):
        """헤더 체크박스 클릭 동작"""
        if self.logicalIndexAt(event.pos()) == 0:  # 첫 번째 열 클릭
            self._is_checked = not self._is_checked
            self.updateSection(0)  # 헤더 다시 그림
            if self.main_window:
                self.main_window.toggle_all_checkboxes(self._is_checked)  # 테이블 전체 체크박스 상태 변경
        else:
            super().mousePressEvent(event)
