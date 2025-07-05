# src/utils/logger.py
from mitmproxy import ctx
import logging
import os
import sys

_pando_logger = None

def get_executable_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

def init_pando_logger():
    global _pando_logger
    logs_dir = os.path.join(get_executable_dir(), "logs")
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

def log_warn(message: str):
    ctx.log.warn(message)
    if "[판도]" in message and _pando_logger:
        _pando_logger.warning(message)
