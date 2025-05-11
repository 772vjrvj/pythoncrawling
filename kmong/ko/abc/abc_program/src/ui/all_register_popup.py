import pandas as pd
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QTableWidgetItem, QDesktopWidget, QDialog, QTableWidget, QHeaderView, QScrollArea
from src.ui.excel_drag_drop_label import ExcelDragDropLabel

class AllRegisterPopup(QDialog):
    updateList = pyqtSignal(list)      # URL 리스트 시그널
    updateUser = pyqtSignal(dict)      # 사용자 ID/PW 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("엑셀 파일 드래그 앤 드롭")
        self.setGeometry(200, 200, 800, 600)
        self.setStyleSheet("background-color: white;")
        self.url_list = []
        self.user = {}

        self.layout = QVBoxLayout(self)
        self.drag_drop_label = ExcelDragDropLabel()
        self.drag_drop_label.fileDropped.connect(self.load_excel)
        self.layout.addWidget(self.drag_drop_label)

        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(1)
        self.table_widget.setHorizontalHeaderLabels(["URL"])
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.table_widget)
        scroll_area.setWidgetResizable(True)
        self.layout.addWidget(scroll_area)

        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("확인", self)
        self.confirm_button.setStyleSheet("""
            background-color: black;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            padding: 10px;
        """)
        self.confirm_button.setFixedHeight(40)
        self.confirm_button.setFixedWidth(140)
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.clicked.connect(self.on_confirm)
        button_layout.addWidget(self.confirm_button)
        button_layout.setAlignment(Qt.AlignCenter)
        self.layout.addLayout(button_layout)

        self.center_window()

    def load_excel(self, file_paths):
        try:
            combined_data = []
            self.user = {}

            for file in file_paths:
                if file.endswith('.csv'):
                    df = pd.read_csv(file)
                    combined_data.append(df)
                else:
                    excel_file = pd.ExcelFile(file)

                    # 시트1 (URL 리스트)
                    df1 = excel_file.parse(sheet_name=0)
                    combined_data.append(df1)

                    # 시트2 (ID/PW)
                    if len(excel_file.sheet_names) >= 2:
                        df2 = excel_file.parse(sheet_name=1)
                        if not df2.empty and "ID" in df2.columns and "PW" in df2.columns:
                            self.user = {
                                "id": str(df2.iloc[0]["ID"]),
                                "pw": str(df2.iloc[0]["PW"])
                            }

            self.url_list.clear()
            self.url_list.extend(combined_data[0].iloc[:, 0].dropna().astype(str).tolist())

            self.table_widget.setRowCount(len(self.url_list))
            self.table_widget.setColumnCount(1)
            self.table_widget.setHorizontalHeaderLabels(["URL"])

            for row_idx, url in enumerate(self.url_list):
                item = QTableWidgetItem(url)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table_widget.setItem(row_idx, 0, item)

            self.drag_drop_label.setText(f"총 {len(file_paths)}개의 파일이 성공적으로 로드되었습니다.")
            self.drag_drop_label.setStyleSheet("background-color: lightgreen;")

        except Exception as e:
            self.drag_drop_label.setText(f"파일 로드 중 오류 발생: {str(e)}")

    def center_window(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def on_confirm(self):
        self.updateList.emit(self.url_list)
        if self.user:
            self.updateUser.emit(self.user)
        self.accept()
