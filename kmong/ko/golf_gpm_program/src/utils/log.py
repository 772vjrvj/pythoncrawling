import logging
import sys
import os
import json
from datetime import datetime

# 로그 디렉토리 생성
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

today_str = datetime.now().strftime('%Y-%m-%d')
log_file_path = os.path.join(LOG_DIR, f"{today_str}.log")

# 개발 모드 여부 확인
IS_DEV = os.getenv("ENV", "dev") == "dev"

# 로그 포맷 정의
log_format = '[%(asctime)s.%(msecs)03d] %(filename)s:%(lineno)d ▶ %(message)s'
formatter = logging.Formatter(log_format, datefmt='%Y.%m.%d %H:%M:%S')


# 콘솔 핸들러: flush 보장
class ImmediateFlushHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


# 로거 생성
logger = logging.getLogger("mylogger")
logger.setLevel(logging.INFO)
logger.propagate = False  # 다른 핸들러로 전달 방지

# 중복 핸들러 방지
if not logger.handlers:
    if IS_DEV:
        stream_handler = ImmediateFlushHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


# 로그 함수
def log(msg: str):
    logger.info(msg, stacklevel=2)


def log_json(obj: dict):
    logger.info(json.dumps(obj, ensure_ascii=False, indent=2), stacklevel=2)
