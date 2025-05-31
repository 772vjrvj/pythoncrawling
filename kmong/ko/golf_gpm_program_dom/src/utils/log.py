import logging
import sys
import os
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from src.utils.gui_log_bridge import log_bridge

# .env 파일 로드
load_dotenv()

# 환경 변수 확인
ENV = os.getenv("ENV", "dev").lower()
IS_DEV = ENV == "dev"

# 로그 디렉토리 생성
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

today_str = datetime.now().strftime('%Y-%m-%d')
log_file_path = os.path.join(LOG_DIR, f"{today_str}.log")

# 로그 포맷
log_format = '[%(asctime)s.%(msecs)03d] %(levelname)s %(filename)s:%(lineno)d ▶ %(message)s'
formatter = logging.Formatter(log_format, datefmt='%Y.%m.%d %H:%M:%S')

# 콘솔 로그 핸들러 (개발 중 디버깅 용도로만 등록 가능)
class ImmediateFlushHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# 로거 설정
logger = logging.getLogger("mylogger")
logger.setLevel(logging.DEBUG if IS_DEV else logging.INFO)
logger.propagate = False
logger.handlers.clear()

# (선택) 콘솔 출력 핸들러
# if IS_DEV:
#     stream_handler = ImmediateFlushHandler(sys.stdout)
#     stream_handler.setFormatter(formatter)
#     logger.addHandler(stream_handler)

# 파일 핸들러 (회전 적용)
file_handler = RotatingFileHandler(
    log_file_path,
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=3
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# GUI 로그 출력 연결
def set_gui_log_callback(callback):
    log_bridge.connect_to(callback)

# 로그 출력 함수 (레벨 + 위치 포함)
def log(msg: str, level: str = "INFO"):
    now = datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f')[:-3]
    frame = sys._getframe(1)
    filename = os.path.basename(frame.f_code.co_filename)
    lineno = frame.f_lineno
    context = f"{filename}:{lineno}"
    full_msg = f"{context} ▶ {msg}"

    # 파일 로그 기록
    if level == "DEBUG":
        logger.debug(full_msg)
    elif level == "WARNING":
        logger.warning(full_msg)
    elif level == "ERROR":
        logger.error(full_msg)
    else:
        logger.info(full_msg)

    # GUI 출력
    try:
        log_bridge.write(f"[{now}] {level} {context} ▶ {msg}")
    except Exception:
        pass

def log_json(obj: dict, level: str = "INFO"):
    now = datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f')[:-3]
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    frame = sys._getframe(1)
    filename = os.path.basename(frame.f_code.co_filename)
    lineno = frame.f_lineno
    context = f"{filename}:{lineno}"
    full_msg = f"{context} ▶ {text}"

    if level == "DEBUG":
        logger.debug(full_msg)
    elif level == "WARNING":
        logger.warning(full_msg)
    elif level == "ERROR":
        logger.error(full_msg)
    else:
        logger.info(full_msg)

    try:
        log_bridge.write(f"[{now}] {level} {context} ▶ {text}")
    except Exception:
        pass

# 초기화 로그 출력
log(f"로거 초기화 완료 - ENV: {ENV}, IS_DEV: {IS_DEV}")
