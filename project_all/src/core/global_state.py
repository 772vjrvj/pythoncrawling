class GlobalState:
    # 상수 정의
    NAME = "name"
    SITE = "site"
    COLOR = "color"
    COOKIES = "cookies"
    USER = "user"

    _instance = None

    def __init__(self):
        if not hasattr(self, '_data'):
            self._data = None
        if not hasattr(self, '_initialized'):
            self._initialized = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._data = {}
            cls._instance._initialized = False
        return cls._instance

    def initialize(self):
        if not self._initialized:
            self._data = {
                self.COOKIES: "",
                self.NAME: "",
                self.SITE: "",
                self.COLOR: "",
                self.USER: "",
            }
            self._initialized = True

    def set(self, key, value):
        self._data[key] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

    def remove(self, key):
        if key in self._data:
            del self._data[key]

    def clear(self):
        self._data.clear()
