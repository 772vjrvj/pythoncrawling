import os
import sys
import logging
from mitmproxy import ctx

_pando_logger = None

def get_executable_dir():
    """실행파일 또는 스크립트 기준 경로 반환"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

def init_pando_logger():
    global _pando_logger

    base_dir = get_executable_dir()
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    _pando_logger = logging.getLogger("pando")
    _pando_logger.setLevel(logging.INFO)

    handler = logging.FileHandler(os.path.join(logs_dir, "pando.log"), encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    _pando_logger.addHandler(handler)

def log_info(message: str):
    ctx.log.info(message)
    if "[판도]" in message and _pando_logger:
        _pando_logger.info(message)

def log_error(message: str):
    ctx.log.error(message)
    if "[판도]" in message and _pando_logger:
        _pando_logger.error(message)
