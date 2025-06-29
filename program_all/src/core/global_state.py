class GlobalState:
    # 전역에서 사용하는 고정된 키 상수들 (문자열 오타 방지용)
    NAME = "name"
    SITE = "site"
    COLOR = "color"
    COOKIES = "cookies"
    USER = "user"
    SETTING = "setting"
    COLUMNS = "columns"
    REGION = "region"

    # 싱글톤 인스턴스를 저장할 변수
    _instance = None

    # 1. MyClass.__new__() → 객체 생성
    # 2. MyClass.__init__() → 생성된 객체를 초기화
    def __new__(cls, *args, **kwargs):
        # 이 클래스는 싱글톤이므로 인스턴스가 없을 때만 새로 생성
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._data = {}           # 데이터를 저장할 딕셔너리
            cls._instance._initialized = False # 초기화 여부
        return cls._instance

    def __init__(self):
        # 초기화된 적이 없다면 기본 속성 생성
        if not hasattr(self, '_data'):
            self._data = None
        if not hasattr(self, '_initialized'):
            self._initialized = None

    def initialize(self):
        # 초기화되지 않은 경우, 기본값으로 상태 딕셔너리를 설정
        if not self._initialized:
            self._data = {
                self.COOKIES: "",  # 쿠키 정보
                self.NAME: "",     # 사용자 이름
                self.SITE: "",     # 사이트 코드
                self.COLOR: "",    # UI 색상
                self.USER: "",     # 로그인 사용자 정보
                self.SETTING: "",     # 로그인 사용자 정보
                self.COLUMNS: "",     # 로그인 사용자 정보
                self.REGION: "",     # 로그인 사용자 정보
            }
            self._initialized = True  # 초기화 완료 표시

    def set(self, key, value):
        """상태 값을 저장합니다."""
        self._data[key] = value

    def get(self, key, default=None):
        """상태 값을 가져옵니다. 값이 없으면 default 반환"""
        return self._data.get(key, default)

    def remove(self, key):
        """특정 키의 상태를 삭제합니다."""
        if key in self._data:
            del self._data[key]

    def clear(self):
        """전체 상태 데이터를 초기화합니다."""
        self._data.clear()
