class DomState:
    _data_list = []

    @classmethod
    def add(cls, data: dict):
        for item in cls._data_list:
            if item == data:
                return
        cls._data_list.append(data)

    @classmethod
    def get_all(cls) -> list:
        return cls._data_list

    @classmethod
    def clear(cls):
        cls._data_list = []

    @classmethod
    def has(cls, key: str) -> bool:
        return any(key in item for item in cls._data_list)

    @classmethod
    def get_last(cls) -> dict:
        return cls._data_list[-1] if cls._data_list else {}

    @classmethod
    def update(cls, index: int, data: dict):
        if 0 <= index < len(cls._data_list):
            cls._data_list[index] = data
