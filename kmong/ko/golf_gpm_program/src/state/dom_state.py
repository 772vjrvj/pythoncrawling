# src/state/dom_state.py

class DomState:
    _latest_data = {}

    @classmethod
    def set(cls, data: dict):
        cls._latest_data = data

    @classmethod
    def get(cls) -> dict:
        return cls._latest_data

    @classmethod
    def clear(cls):
        cls._latest_data = {}

    @classmethod
    def has(cls, key: str) -> bool:
        return key in cls._latest_data
