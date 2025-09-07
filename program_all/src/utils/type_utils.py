# -*- coding: utf-8 -*-

__all__ = ["_as_dict", "_as_list", "_s", "ensure_list_attr"]

def _as_dict(x):
    return x if isinstance(x, dict) else {}

def _as_list(x):
    return x if isinstance(x, list) else []

def _s(v):
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (int, float)):
        return str(v)            # ← 숫자는 문자열로 변환
    return ""                    # 그 외(dict/list 등)는 빈값으로

def ensure_list_attr(obj, attr):
    v = getattr(obj, attr, None)
    if isinstance(v, list):
        return v
    setattr(obj, attr, [])
    return getattr(obj, attr)
