from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from src.utils.config import NAVER_LOC_ALL


class RegionSetPop(QDialog):
    log_signal = pyqtSignal(str)
    confirm_signal = pyqtSignal(list)  # 선택된 지역 반환용

    def __init__(self, selected_regions=None, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("지역 선택")
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: white;")

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(self.tree_style())
        self.tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 선택된 지역 리스트
        self.selected_regions = selected_regions or []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        layout.addWidget(self.tree)
        self.populate_tree()

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 15, 0, 0)

        cancel_btn = QPushButton("취소")
        cancel_btn.setFixedSize(140, 40)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(self.button_style("#cccccc", "black"))
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("확인")
        confirm_btn.setFixedSize(140, 40)
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.setStyleSheet(self.button_style("black", "white"))
        confirm_btn.clicked.connect(self.confirm_selection)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)

    def populate_tree(self):
        """시도 > 시군구 > 읍면동 트리 구성 및 체크 상태 반영"""
        region_map = {}
        selected_set = set(
            (r["시도"], r["시군구"], r["읍면동"]) for r in self.selected_regions
        )
        has_user_selection = bool(selected_set)

        for item in NAVER_LOC_ALL:
            sido, sigungu, eupmyeondong = item["시도"], item["시군구"], item["읍면동"]

            if sido not in region_map:
                sido_item = QTreeWidgetItem([sido])
                self.tree.addTopLevelItem(sido_item)
                sido_item.setExpanded(False)
                region_map[sido] = {}

            if sigungu not in region_map[sido]:
                sigungu_item = QTreeWidgetItem([sigungu])
                region_map[sido][sigungu] = sigungu_item
                sido_item.addChild(sigungu_item)

            # 읍면동 항목
            dong_item = QTreeWidgetItem([eupmyeondong])
            dong_item.setFlags(dong_item.flags() | Qt.ItemIsUserCheckable)

            if has_user_selection:
                # 사용자 선택이 있으면 해당 항목만 체크
                state = Qt.Checked if (sido, sigungu, eupmyeondong) in selected_set else Qt.Unchecked
            else:
                # 선택이 없으면 전체 체크
                state = Qt.Checked

            dong_item.setCheckState(0, state)
            region_map[sido][sigungu].addChild(dong_item)

    def confirm_selection(self):
        """체크된 읍면동만 추출하여 배열 반환"""
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
            }
            QTreeView::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #888888;
                background-color: white;
            }
            QTreeView::indicator:checked {
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
