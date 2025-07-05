import logging
import os
import sys
import time

try:
    from mitmproxy import ctx
    MITM_AVAILABLE = True
except ImportError:
    ctx = None
    MITM_AVAILABLE = False

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

    # 💡 오래된 로그 자동 삭제 (pando / proxy)
    clean_old_logs(logs_dir, prefix="pando", days=7)
    clean_old_logs(logs_dir, prefix="proxy_server", days=3)

    _pando_logger = logging.getLogger("pando")
    _pando_logger.setLevel(logging.INFO)

    log_path = os.path.join(logs_dir, "pando.log")
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    _pando_logger.addHandler(handler)

# ✅ 오래된 로그 정리 함수
def clean_old_logs(log_dir, prefix, days=7):
    now = time.time()
    cutoff = now - (days * 86400)

    for fname in os.listdir(log_dir):
        if fname.startswith(prefix) and fname.endswith(".log"):
            path = os.path.join(log_dir, fname)
            if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                os.remove(path)
                print(f"🧹 로그 삭제: {fname}")

# ✅ UI 전용 로그
def ui_log(message: str):
    print(message)
    if "[판도]" in message and _pando_logger:
        _pando_logger.info(message)

# ✅ 프록시 전용 로그
def log_info(message: str):
    if MITM_AVAILABLE and ctx:
        ctx.log.info(message)
    if "[판도]" in message and _pando_logger:
        _pando_logger.info(message)

def log_warn(message: str):
    if MITM_AVAILABLE and ctx:
        ctx.log.warn(message)
    if "[판도]" in message and _pando_logger:
        _pando_logger.warning(message)

def log_error(message: str):
    if MITM_AVAILABLE and ctx:
        ctx.log.error(message)
    if "[판도]" in message and _pando_logger:
        _pando_logger.error(message)
