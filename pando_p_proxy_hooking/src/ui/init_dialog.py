# src/ui/init_dialog.py  (또는 main_window.py 상단에 붙여넣기)
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QMovie, QFont

class InitDialog(QDialog):
    """
    취소 버튼 없는 초기화 다이얼로그.
    - GIF (assets/loader.gif) 있으면 해당 GIF로 애니메이션 표시.
    - GIF 없으면 텍스트로 '로딩' + 점 애니메이션으로 폴백.
    - show() 로 비차단 방식으로 띄우고, 작업 완료 시 close() 로 닫음.
    """

    def __init__(self, parent=None, message="잠시만 기다려주세요.", loader_path=None):
        super().__init__(parent)

        # 윈도우 스타일: 닫기 버튼 등 불필요한 버튼 제거 (타이틀은 유지)
        # (원하면 Qt.FramelessWindowHint 로 테두리 없음으로 바꿀 수 있음)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle("")  # 타이틀 필요 없으면 빈 문자열
        self.setFixedSize(360, 150)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # 메시지 레이블 (중학생도 알아볼 수 있게 한글)
        self.lbl_message = QLabel(message, self)
        self.lbl_message.setWordWrap(True)
        font = QFont()
        font.setPointSize(11)
        self.lbl_message.setFont(font)
        self.lbl_message.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_message)

        # 애니메이션 레이블 (GIF 또는 텍스트 애니메이션)
        self.anim_label = QLabel(self)
        self.anim_label.setFixedHeight(80)
        self.anim_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.anim_label)

        # 시계용 타이머(텍스트 점 애니메이션)
        self._dot_timer = None
        self._dot_state = 0

        # 우선 loader_path 우선, 없으면 부모의 get_resource_path 또는 default 경로 확인
        gif_path = None
        if loader_path and os.path.exists(loader_path):
            gif_path = loader_path
        else:
            # 부모가 제공한 get_resource_path가 있으면 사용 시도
            try:
                if parent is not None and hasattr(parent, "get_resource_path"):
                    candidate = parent.get_resource_path("assets/loader.gif")
                    if os.path.exists(candidate):
                        gif_path = candidate
            except Exception:
                pass

        # GIF 사용 가능하면 QMovie 세팅
        self._movie = None
        if gif_path and os.path.exists(gif_path):
            try:
                self._movie = QMovie(gif_path)
                if self._movie.isValid():
                    self.anim_label.setMovie(self._movie)
                    self._movie.start()
                else:
                    # invalid movie -> fallback to text animation
                    self._movie = None
                    self._start_text_animation()
            except Exception:
                self._movie = None
                self._start_text_animation()
        else:
            # GIF 없을 때 텍스트 점 애니메이션 사용
            self._start_text_animation()

        # 창 가운데 정렬은 부모가 맡도록(부모가 있으면 중앙에 뜸)
        # if parent is not None:
        #     try:
        #         # center over parent
        #         parent_rect = parent.geometry()
        #         self.move(
        #             parent_rect.x() + (parent_rect.width() - self.width()) // 2,
        #             parent_rect.y() + (parent_rect.height() - self.height()) // 2
        #         )
        #     except Exception:
        #         pass

    def _start_text_animation(self):
        """'로딩' + 점 애니메이션 시작"""
        if self._dot_timer is None:
            self._dot_timer = QTimer(self)
            self._dot_timer.setInterval(400)  # 400ms 마다 점 증가
            self._dot_timer.timeout.connect(self._update_dots)
            self._dot_timer.start()
        # initial text
        self._dot_state = 0
        self._update_dots()

    def _stop_text_animation(self):
        if self._dot_timer is not None:
            try:
                self._dot_timer.stop()
            except Exception:
                pass
            self._dot_timer = None

    def _update_dots(self):
        self._dot_state = (self._dot_state + 1) % 4
        dots = "." * self._dot_state
        # 기본 메시지에서 점만 추가해서 애니메이션처럼 보이게 함
        base = self.lbl_message.text().split()[0] if self.lbl_message.text() else "로딩"
        # 그냥 고정 문자열으로도 괜찮음:
        self.anim_label.setText(f"{dots}")

    def closeEvent(self, event):
        # 다이얼로그 닫힐 때 리소스 정리
        try:
            if self._movie is not None:
                try:
                    self._movie.stop()
                except Exception:
                    pass
                self._movie = None
            self._stop_text_animation()
        except Exception:
            pass
        super().closeEvent(event)

    # 외부에서 명시적으로 중지/정리 호출용
    def stop(self):
        try:
            self.close()
        except Exception:
            pass
