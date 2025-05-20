import logging
import sys
import os
import json
from datetime import datetime

LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

today_str = datetime.now().strftime('%Y-%m-%d')
log_file_path = os.path.join(LOG_DIR, f"{today_str}.log")

IS_DEV = os.getenv("ENV", "dev") == "dev"

class ImmediateFlushHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            super().emit(record)
            self.flush()
        except Exception:
            pass  # 콘솔이 없는 상황 고려 (운영 exe 등)

logger = logging.getLogger("mylogger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    log_format = '[%(asctime)s.%(msecs)03d] %(filename)s:%(lineno)d ▶ %(message)s'
    formatter = logging.Formatter(log_format, datefmt='%Y.%m.%d %H:%M:%S')

    if IS_DEV:
        stream_handler = ImmediateFlushHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def log(msg: str):
    logger.info(msg, stacklevel=2)

def log_json(req_json: json):
    logger.info(json.dumps(req_json, ensure_ascii=False, indent=2), stacklevel=2)
