from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QHBoxLayout, QSizePolicy, QCheckBox, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal

from src.ui.style.style import create_common_button
from src.utils.config import NAVER_LOC_ALL


class RegionSetPop(QDialog):
    log_signal = pyqtSignal(str)
    confirm_signal = pyqtSignal(list)

    def __init__(self, selected_regions=None, parent=None):
        super().__init__(parent)
        self.confirm_btn = None
        self.cancel_btn = None
        self.parent = parent
        self.setWindowTitle("지역 선택")
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: white;")

        self.selected_regions = selected_regions or []

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(self.tree_style())
        self.tree.setCursor(Qt.PointingHandCursor)  # ✅ 손가락 커서 적용
        self.tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._is_select_all_action = False

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        info_label = QLabel("지역을 선택하세요")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px;")
        layout.addWidget(info_label)

        self.select_all_checkbox = QCheckBox("전체 선택")
        self.select_all_checkbox.setCursor(Qt.PointingHandCursor)  # ✅ 손가락 커서
        self.select_all_checkbox.setStyleSheet(self.checkbox_style())
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)
        layout.addWidget(self.select_all_checkbox)

        layout.addWidget(self.tree)
        self.populate_tree()
        self.tree.itemChanged.connect(self.on_item_changed)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 15, 0, 0)

        self.cancel_btn = create_common_button("취소", self.reject, "#cccccc", 140)
        self.confirm_btn = create_common_button("확인", self.confirm_selection, "black", 140)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.confirm_btn)
        layout.addLayout(btn_layout)

    def populate_tree(self):
        self.tree.blockSignals(True)
        self.tree.clear()

        region_dict = {}
        selected_set = set((r["시도"], r["시군구"], r["읍면동"]) for r in self.selected_regions)

        for item in NAVER_LOC_ALL:
            sido, sigungu, eupmyeondong = item["시도"], item["시군구"], item["읍면동"]

            if sido not in region_dict:
                sido_item = QTreeWidgetItem([sido])
                sido_item.setFlags(sido_item.flags() | Qt.ItemIsUserCheckable)
                sido_item.setCheckState(0, Qt.Unchecked)
                sido_item.setData(0, Qt.UserRole, "sido")
                self.tree.addTopLevelItem(sido_item)
                region_dict[sido] = {"item": sido_item, "children": {}}

            if sigungu not in region_dict[sido]["children"]:
                sigungu_item = QTreeWidgetItem([sigungu])
                sigungu_item.setFlags(sigungu_item.flags() | Qt.ItemIsUserCheckable)
                sigungu_item.setCheckState(0, Qt.Unchecked)
                sigungu_item.setData(0, Qt.UserRole, "sigungu")
                region_dict[sido]["children"][sigungu] = {"item": sigungu_item}
                region_dict[sido]["item"].addChild(sigungu_item)

            dong_item = QTreeWidgetItem([eupmyeondong])
            dong_item.setFlags(dong_item.flags() | Qt.ItemIsUserCheckable)
            dong_item.setData(0, Qt.UserRole, "eupmyeondong")
            dong_item.setCheckState(0, Qt.Checked if (sido, sigungu, eupmyeondong) in selected_set else Qt.Unchecked)
            region_dict[sido]["children"][sigungu]["item"].addChild(dong_item)

        self.tree.blockSignals(False)
        self.update_all_check_states()

        # ✅ 전체 선택 체크박스를 기본적으로 해제 상태로 설정
        self.select_all_checkbox.setCheckState(Qt.Unchecked)

    def on_item_changed(self, item, column):
        if self.tree.signalsBlocked():
            return

        self.tree.blockSignals(True)
        state = item.checkState(0)
        self.set_check_state_recursive(item, state)
        self.update_parent_check_state(item)
        self.tree.blockSignals(False)

        self.update_all_checkbox_state()

    def update_parent_check_state(self, item):
        parent = item.parent()
        while parent:
            checked = sum(parent.child(i).checkState(0) == Qt.Checked for i in range(parent.childCount()))
            if checked == parent.childCount():
                parent.setCheckState(0, Qt.Checked)
            elif checked == 0:
                parent.setCheckState(0, Qt.Unchecked)
            else:
                parent.setCheckState(0, Qt.PartiallyChecked)
            item = parent
            parent = item.parent()

    def on_select_all_changed(self, state):
        if state == Qt.PartiallyChecked:
            state = Qt.Checked

        self._is_select_all_action = True
        self.tree.blockSignals(True)

        for i in range(self.tree.topLevelItemCount()):
            sido_item = self.tree.topLevelItem(i)
            sido_item.setCheckState(0, state)
            for j in range(sido_item.childCount()):
                sigungu_item = sido_item.child(j)
                sigungu_item.setCheckState(0, state)
                for k in range(sigungu_item.childCount()):
                    sigungu_item.child(k).setCheckState(0, state)

        self.tree.blockSignals(False)
        self._is_select_all_action = False

        self.select_all_checkbox.blockSignals(True)
        self.select_all_checkbox.setCheckState(state)
        self.select_all_checkbox.blockSignals(False)

    def update_all_check_states(self):
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            self.update_check_state_recursive(self.tree.topLevelItem(i))
        self.tree.blockSignals(False)
        self.update_all_checkbox_state()

    def update_check_state_recursive(self, item):
        for i in range(item.childCount()):
            self.update_check_state_recursive(item.child(i))
        checked = sum(item.child(i).checkState(0) == Qt.Checked for i in range(item.childCount()))
        if checked == item.childCount():
            item.setCheckState(0, Qt.Checked)
        elif checked == 0:
            item.setCheckState(0, Qt.Unchecked)
        else:
            item.setCheckState(0, Qt.PartiallyChecked)

    def update_all_checkbox_state(self):
        total = self.tree.topLevelItemCount()
        checked = sum(
            self.tree.topLevelItem(i).checkState(0) == Qt.Checked
            for i in range(total)
        )

        self.select_all_checkbox.blockSignals(True)
        if checked == total:
            self.select_all_checkbox.setCheckState(Qt.Checked)
        elif checked == 0:
            self.select_all_checkbox.setCheckState(Qt.Unchecked)
        else:
            self.select_all_checkbox.setCheckState(Qt.PartiallyChecked)
        self.select_all_checkbox.blockSignals(False)

    def set_check_state_recursive(self, item, state):
        item.setCheckState(0, state)
        for i in range(item.childCount()):
            self.set_check_state_recursive(item.child(i), state)

    def confirm_selection(self):
        selected = []
        for i in range(self.tree.topLevelItemCount()):
            sido_item = self.tree.topLevelItem(i)
            for j in range(sido_item.childCount()):
                sigungu_item = sido_item.child(j)
                for k in range(sigungu_item.childCount()):
                    dong_item = sigungu_item.child(k)
                    if dong_item.checkState(0) == Qt.Checked:
                        selected.append({
                            "시도": sido_item.text(0),
                            "시군구": sigungu_item.text(0),
                            "읍면동": dong_item.text(0)
                        })
        self.log_signal.emit(f"선택된 지역 {len(selected)}개")
        self.confirm_signal.emit(selected)
        self.accept()

    def tree_style(self):
        return """
            QTreeView {
                font-size: 14px;
                padding: 4px 12px;
                selection-color: black;  /* ✅ 선택된 텍스트 색상 */
            }
            QTreeView::item {
                padding: 8px 0px;
            }
            QTreeView::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #888888;
                background-color: white;
                margin-right: 12px;
            }
            QTreeView::indicator:checked {
                background-color: black;
            }
        """

    def checkbox_style(self):
        return """
            QCheckBox {
                font-size: 14px;
                color: #333;
                padding: 8px 12px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #888888;
                background-color: white;
                margin-right: 10px;
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
