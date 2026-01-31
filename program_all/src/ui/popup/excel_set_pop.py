import pandas as pd
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QTableWidgetItem, QDesktopWidget,
    QDialog, QTableWidget, QHeaderView, QAbstractItemView
)
from pathlib import Path

from src.ui.popup.excel_drag_drop_label import ExcelDragDropLabel


class ExcelSetPop(QDialog):
    updateList = pyqtSignal(object)
    updateUser = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("엑셀 파일 드래그 앤 드롭")
        self.setGeometry(200, 200, 800, 600)
        self.setStyleSheet("background-color: white;")

        self.data_list = []
        self.user = {}

        self.layout = QVBoxLayout(self)

        self.drag_drop_label = ExcelDragDropLabel()
        self.drag_drop_label.fileDropped.connect(self.load_excel)
        self.layout.addWidget(self.drag_drop_label)

        self.table_widget = QTableWidget(self)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setAlternatingRowColors(True)
        self.layout.addWidget(self.table_widget)

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
            dfs = []
            self.user = {}

            for file in file_paths:
                base = Path(file).stem

                if file.lower().endswith(".csv"):
                    df = pd.read_csv(file, dtype=str).fillna("")
                    df["file"] = base

                    # === 신규 === 원본 파일 경로/행번호 저장(원본 반영용)
                    df["__excel_path"] = file
                    df["__sheet_idx"] = 0
                    df["__row_idx"] = df.index + 2  # 1행 헤더 가정

                    dfs.append(df)

                else:
                    excel_file = pd.ExcelFile(file)

                    # 시트1: 데이터
                    df1 = excel_file.parse(sheet_name=0, dtype=str).fillna("")
                    df1["file"] = base

                    # === 신규 === 원본 파일 경로/행번호 저장(원본 반영용)
                    df1["__excel_path"] = file
                    df1["__sheet_idx"] = 0
                    df1["__row_idx"] = df1.index + 2  # 1행 헤더 가정

                    dfs.append(df1)

                    # 시트2: 사용자(ID/PW) (기존 유지)
                    if len(excel_file.sheet_names) >= 2:
                        df2 = excel_file.parse(sheet_name=1, dtype=str).fillna("")
                        if not df2.empty and "ID" in df2.columns and "PW" in df2.columns:
                            self.user = {"id": df2.iloc[0]["ID"], "pw": df2.iloc[0]["PW"]}

            if not dfs:
                raise ValueError("로드할 수 있는 파일이 없습니다.")

            combined_df = pd.concat(dfs, ignore_index=True, sort=False).fillna("")
            combined_df = combined_df.astype(str)

            headers = [str(c) for c in combined_df.columns]
            rows = combined_df.values.tolist()

            self.table_widget.setUpdatesEnabled(False)
            self.table_widget.clear()
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)

            self.table_widget.setColumnCount(len(headers))
            self.table_widget.setHorizontalHeaderLabels(headers)
            self.table_widget.setRowCount(len(rows))

            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.table_widget.setItem(r, c, QTableWidgetItem(val))

            header = self.table_widget.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Interactive)
            header.setStretchLastSection(True)

            self.table_widget.setUpdatesEnabled(True)

            self.drag_drop_label.setText(
                f"총 {len(file_paths)}개 파일, {len(rows)}행 {len(headers)}열 로드 완료"
            )
            self.drag_drop_label.setStyleSheet("background-color: lightgreen;")

            self.data_list = combined_df.to_dict(orient="records")

        except Exception as e:
            self.table_widget.setUpdatesEnabled(True)
            self.drag_drop_label.setText(f"파일 로드 중 오류 발생: {str(e)}")

    def center_window(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def on_confirm(self):
        self.updateList.emit(self.data_list)
        if self.user:
            self.updateUser.emit(self.user)
        self.accept()
