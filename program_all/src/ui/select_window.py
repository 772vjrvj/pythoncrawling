from functools import partial

from PyQt5.QtCore import Qt                     # 정렬, 스크롤바 정책 등 Qt 상수
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor   # 아이콘/픽스맵/도형 그리기
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QScrollArea, QSizePolicy,
    QStyle, QFrame, QDesktopWidget, QLineEdit, QWidget as QW
)

from src.core.global_state import GlobalState                # 전역 상태 저장/조회
from src.ui.style.style import create_common_button, main_style  # 공통 버튼/입력창 스타일
from src.vo.site import Site                                 # 사이트 정보 VO(레이블/키/컬러 등)


class SelectWindow(QWidget):
    """
    사이트 선택 창.
    - 상단 검색 입력창(Enter로 검색 실행)
    - 검색창 아래 얇은 구분선
    - 스크롤 가능한 사이트 버튼 목록(가로 300px 고정, 중앙 정렬)
    - 창 최소 크기: 화면 높이의 1/2, 너비 500px (이하로는 축소 불가)

     SelectWindow (QWidget)
     └─ layout : QVBoxLayout
     ├─ search_edit : QLineEdit
     ├─ sep : QFrame (구분선)
     └─ scroll_area : QScrollArea
     └─ viewport (내부 위젯, QScrollArea가 자동 생성)
     └─ scroll_host : QWidget            # setWidget()으로 붙인 컨테이너
     └─ scroll_layout : QVBoxLayout   # 버튼들이 여기에 쌓임
     ├─ create_common_button(...) × N
     └─ spacer (Expanding)
    """

    def __init__(self, app_manager, site_list):
        """
        :param app_manager: 화면 전환/라우팅을 담당하는 AppManager 인스턴스
        :param site_list:   초기 전체 사이트 목록(list[Site])
        """
        super().__init__()
        self.app_manager = app_manager                 # (의존성) 상위에서 전달받는 앱 매니저
        self.sites = list(site_list)                   # (데이터) 전체 사이트 원본 목록
        self.filtered_sites = list(site_list)          # (상태) 현재 필터링된 목록(초기엔 전체)

        # 창 크기 관련 고정값(최소값) — _init_window_metrics()에서 채워짐
        self.fixed_w = None                            # (상태) 창 최소 너비
        self.fixed_h = None                            # (상태) 창 최소 높이

        # UI 위젯 핸들(초기화 후 _build_ui에서 실제 인스턴스 할당)
        self.search_edit = None                        # (위젯) 검색어 입력창(QLineEdit)
        self.search_btn = None                         # (사용 안 함) 버튼 제거했지만 멤버 유지
        self.scroll_area = None                        # (위젯) 스크롤 컨테이너(QScrollArea)
        self.scroll_host = None                        # (위젯) 스크롤 내부 호스트 위젯(열 컨테이너)
        self.scroll_layout = None                      # (레이아웃) 버튼을 쌓는 수직 레이아웃

        self._init_window_metrics()                    # 화면 크기 기반 최소 크기 산출
        self._build_ui()                               # UI 구성
        self.center_window()                           # 화면 중앙 배치

    # ─────────────────────────────────────────
    # 레이아웃/창 크기 초기화
    # ─────────────────────────────────────────
    def _init_window_metrics(self):
        """
        화면(모니터)의 전체 지오메트리를 참조해
        - 창 최소 높이: 화면 높이의 1/2
        - 창 최소 너비: 500
        를 계산해 둔다.
        """
        # screen_geo = QDesktopWidget().screenGeometry()  # 전체 화면 지오메트리
        # self.fixed_h = int(screen_geo.height() * 0.5)   # 최소 높이(화면의 절반)
        self.fixed_h = 600
        self.fixed_w = 500                               # 최소 너비(500px 고정)

    # ─────────────────────────────────────────
    # UI 빌드
    # ─────────────────────────────────────────
    def _build_ui(self):
        """검색창/구분선/스크롤 리스트까지 메인 UI를 구성한다."""
        # 1) 윈도우 아이콘(회색 사각형 32x32) 그리기
        icon_pixmap = QPixmap(32, 32)            # 32x32 픽스맵 생성
        icon_pixmap.fill(Qt.transparent)         # 배경 투명
        p = QPainter(icon_pixmap)                # 페인터 시작
        p.setBrush(QColor("#e0e0e0"))            # 브러시(채우기색): 연한 회색
        p.setPen(QColor("#e0e0e0"))              # 펜(테두리색): 연한 회색
        p.drawRect(0, 0, 32, 32)                 # 사각형 그리기
        p.end()                                  # 페인터 종료
        self.setWindowIcon(QIcon(icon_pixmap))   # 창 아이콘 설정

        # 2) 창 타이틀/크기/배경
        self.setWindowTitle("사이트")            # 창 제목
        self.resize(self.fixed_w, self.fixed_h)  # 초기 크기(최소값과 동일하게 시작)
        self.setMinimumHeight(self.fixed_h)      # 최소 높이 제한(아래로 축소 불가)
        self.setMinimumWidth(self.fixed_w)       # 최소 너비 제한(아래로 축소 불가)
        self.setStyleSheet("background-color: #ffffff;")  # 배경 흰색

        # 3) 메인 수직 레이아웃 구성
        layout = QVBoxLayout(self)                               # 루트 레이아웃
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)       # 상단 정렬 + 가로 중앙 # 레이아웃 “자기자신”의 정렬
        # AlignTop 창(부모)에 세로로 여유 공간이 생기면, 내용을 위쪽에 붙여 놓습니다. (아래쪽이 비게 됨)
        # AlignHCenter 가로 여유 공간이 생기면, 내용을 가로 중앙에 둡니다.
        layout.setContentsMargins(20, 20, 20, 20)                # 바깥 마진
        layout.setSpacing(16)                                    # 위젯 간 간격
        # 검색창 ↔ 구분선 ↔ 스크롤영역 사이 세로 간격이 16px

        # 4) 검색 입력창(엔터로 검색 실행)
        self.search_edit = QLineEdit(self)                       # 검색어 입력창
        self.search_edit.setPlaceholderText("검색어를 입력후 엔터를 치세요.")  # 플레이스홀더
        self.search_edit.setClearButtonEnabled(True)             # 클리어 버튼 표시 (x)
        self.search_edit.setFixedHeight(40)                      # 높이 고정
        self.search_edit.setFixedWidth(300)                      # 너비 고정(열 너비와 동일)
        self.search_edit.setStyleSheet(main_style("#888888"))    # 테두리/서체 스타일
        self.search_edit.returnPressed.connect(self._run_search) # Enter 입력 시 검색 실행
        layout.addWidget(self.search_edit, alignment=Qt.AlignHCenter)  # 중앙 배치

        # 5) 검색창 아래 구분선(가로 300px, 두께 1px, 중간 정렬)
        sep = QFrame(self)                                       # 수평선 프레임
        sep.setFrameShape(QFrame.HLine)                          # 가로선 모양
        sep.setFrameShadow(QFrame.Plain)                         # 평면 그림자(단색)
        sep.setFixedSize(300, 1)                                 # 너비 300, 높이 1
        sep.setStyleSheet("background-color: #888888;")          # 라인 색상(연한 회색)
        sep.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 사이즈 정책(고정/고정)
        layout.addWidget(sep, alignment=Qt.AlignHCenter)         # 중앙 배치

        # 6) 스크롤 가능한 사이트 버튼 리스트
        self.scroll_area = QScrollArea(self)                     # 스크롤 컨테이너
        self.scroll_area.setWidgetResizable(True)                # 내부 위젯 크기 자동 조절
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 가로 스크롤 숨김
        self.scroll_area.setFrameShape(QFrame.NoFrame)           # 외곽 프레임 제거
        self.scroll_area.setAlignment(Qt.AlignTop | Qt.AlignHCenter)          # 내부 중앙 정렬

        self.scroll_host = QW()                                  # 스크롤 내부 실제 컨테이너
        self.scroll_host.setFixedWidth(300)                      # 열 너비 300 고정(버튼과 동일)
        self.scroll_host.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred) # Fixed 가로로 절대 늘어나지 않음. Preferred 늘거나 줄 수 있음

        self.scroll_layout = QVBoxLayout(self.scroll_host)       # 버튼을 쌓을 수직 레이아웃
        self.scroll_layout.setAlignment(Qt.AlignTop)             # 위에서부터 쌓기
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)        # 내부 마진 없음
        self.scroll_layout.setSpacing(12)                        # 버튼 간 간격

        self.scroll_area.setWidget(self.scroll_host)             # 호스트를 스크롤에 장착
        layout.addWidget(self.scroll_area, stretch=1)            # 메인 레이아웃에 추가(여백 가중치 1)

        # 7) 스크롤바 등장/제거 시 중앙 보정(좌측 마진을 스크롤바 폭만큼 줌)
        self.scroll_area.verticalScrollBar().rangeChanged.connect(self._on_scroll_range_changed)

        # 8) 초기 렌더링 및 마진 보정
        self._rebuild_buttons()     # 버튼 리스트 최초 생성

    # ─────────────────────────────────────────
    # 스크롤바 범위가 바뀌면(등장/제거) 콘텐츠 열이 창 기준 중앙을 유지하도록 마진 재보정
    # ─────────────────────────────────────────
    def _on_scroll_range_changed(self, minimum: int, maximum: int) -> None:
        """스크롤바 범위가 바뀔 때 중앙 보정"""
        self._adjust_scrollbar_margin()

    # ─────────────────────────────────────────
    # 검색/필터링
    # ─────────────────────────────────────────
    def _run_search(self):
        """
        Enter 입력 시 호출되는 핸들러.
        - 입력값 앞뒤 공백 제거
        - 빈 문자열이면 전체 목록
        - 비어있지 않으면 부분 포함으로 필터링(대소문자 무시)
        """
        q = (self.search_edit.text() or "").strip()  # 현재 검색어
        self._apply_search(q)

    # ─────────────────────────────────────────
    # 검색
    # ─────────────────────────────────────────
    def _apply_search(self, q: str):
        """
        실제 필터링 로직.
        :param q: 검색어(공백/빈 문자열일 수 있음)
        - casefold()로 대/소문자 구분 없이 부분 포함 검색
        - Site.label, Site.key 기준으로 매칭
        """
        q_norm = self._norm_text(q)
        if not q_norm:
            self.filtered_sites = list(self.sites)
        else:
            self.filtered_sites = [
                s for s in self.sites
                if (q_norm in self._norm_text(s.label)) or (q_norm in self._norm_text(getattr(s, "key", "")))
            ]
        self._rebuild_buttons()

    # ─────────────────────────────────────────
    # 검색 문자 처리
    # ─────────────────────────────────────────
    def _norm_text(self, s: str) -> str:
        """None/빈값 안전 처리 + casefold로 대소문자 무시 정규화"""
        return (s or "").casefold()

    # ─────────────────────────────────────────
    # 버튼 리스트 렌더링
    # ─────────────────────────────────────────
    def _rebuild_buttons(self):
        """
        현재 self.filtered_sites를 기준으로 스크롤 영역의 버튼들을 모두 다시 구성한다.
        - 기존 위젯 제거
        - create_common_button(...)으로 버튼 생성
        - 버튼 너비 300 고정(열 너비와 맞춤)
        - 하단 여백용 스페이서 추가
        """
        # 1) 기존 위젯 제거(메모리 누수 방지: 부모 해제)
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()   # ← 검색처럼 자주 갈아끼울 땐 이게 깔끔

        # 2) 필터링된 사이트 목록으로 버튼 재생성
        for site in self.filtered_sites:
            # 공통 스타일 버튼 생성: (라벨, 클릭 핸들러, 색상, 너비)
            btn = create_common_button(
                site.label,
                partial(self.select_site, site),
                site.color,
                300,
                site.enabled
            )
            btn.setFixedWidth(300)                          # 버튼 폭 300 고정
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 사이즈 정책 고정/고정
            self.scroll_layout.addWidget(btn)               # 레이아웃에 추가

        # 3) 하단 빈 공간 채우기용 스페이서(스크롤 최하단에서 여유 공간 확보)
        spacer = QW()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_layout.addWidget(spacer)

        # 4) 보정 재적용(스크롤바 등장/제거 상황 반영)
        self._adjust_scrollbar_margin()

    # ─────────────────────────────────────────
    # 스크롤 뷰포트 마진 보정
    # ─────────────────────────────────────────
    def _adjust_scrollbar_margin(self):
        """
        세로 스크롤바가 보일 때,
        - 스크롤바 폭(PM_ScrollBarExtent)만큼 왼쪽 마진을 주어
        - '창 기준'으로 열(300px)이 정확히 중앙에 오도록 보정한다.
        (오른쪽이 아니라 왼쪽에 마진을 주는 이유: 스크롤바가 오른쪽을 차지하기 때문)
        """
        extent = self.scroll_area.style().pixelMetric(QStyle.PM_ScrollBarExtent)  # 스크롤바 폭(px)
        has_scroll = self.scroll_area.verticalScrollBar().maximum() > 0           # 스크롤 필요 여부
        self.scroll_area.setViewportMargins(extent if has_scroll else 0, 0, 0, 0) # 좌측 마진만 조정

    # ─────────────────────────────────────────
    # 창 중앙 배치
    # ─────────────────────────────────────────
    def center_window(self):
        """
        현재 창을 화면 중앙으로 이동.
        (QDesktopWidget 사용: PyQt5 기본)
        """
        screen = QDesktopWidget().screenGeometry()  # 전체 화면 영역
        size = self.geometry()                      # 현재 창 크기
        self.move((screen.width() - size.width()) // 2,
                  (screen.height() - size.height()) // 2)

    # ─────────────────────────────────────────
    # 메시지 유틸
    # ─────────────────────────────────────────
    def show_message(self, title, message):
        """간단 정보 메시지 박스 표시"""
        QMessageBox.information(self, title, message)

    # ─────────────────────────────────────────
    # 사이트 선택(메인 화면 진입)
    # ─────────────────────────────────────────
    def select_site(self, site: Site):
        """
        사이트 버튼 클릭 시 호출.
        - 비활성 사이트면 경고 후 중단
        - 전역 상태(GlobalState)에 선택 정보를 기록
        - 현재 창을 닫고 메인 화면으로 전환
        """
        if not site.is_enabled():  # 접속 불가/준비 중 사이트
            self.show_message("접속실패", f"{site.label}은(는) 준비 중입니다.")
            return

        state = GlobalState()                          # 전역 상태 싱글톤
        state.set(GlobalState.NAME, site.label)        # 사이트 표시명
        state.set(GlobalState.SITE, site.key)          # 내부 키
        state.set(GlobalState.COLOR, site.color)       # 테마 색상
        state.set(GlobalState.USER, site.user)         # 사용자 정보(사이트별)
        state.set(GlobalState.SETTING, site.setting)   # 설정 정보
        state.set(GlobalState.COLUMNS, site.columns)   # 컬럼/필드 구성
        state.set(GlobalState.REGION, site.region)     # 리전/지역 등
        state.set(GlobalState.POPUP, site.popup)     # 리전/지역 등

        self.close()                                   # 현재 선택창 닫기
        self.app_manager.go_to_main()                  # 메인 화면으로 전환
