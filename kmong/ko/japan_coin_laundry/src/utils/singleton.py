class GlobalState:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._data = {}
            cls._instance._initialized = False  # 초기화 여부를 추적
        return cls._instance

    def initialize(self):
        if not self._initialized:
            self._data = {
                "cookies": "",
                "site": "",
                "color": "",
            }
            self._initialized = True
        else:
            pass

    def set(self, key, value):
        self._data[key] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

    def remove(self, key):
        if key in self._data:
            del self._data[key]

    def clear(self):
        self._data.clear()