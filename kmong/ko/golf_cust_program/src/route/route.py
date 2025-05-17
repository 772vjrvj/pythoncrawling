from dataclasses import dataclass
from typing import Callable, Pattern

@dataclass
class Route:
    method: str
    pattern: Pattern
    handler: Callable
    action: str = ""  # 선택적: 필요하면 사용

    def matches(self, method: str, url: str) -> bool:
        return self.method == method and bool(self.pattern.search(url))
