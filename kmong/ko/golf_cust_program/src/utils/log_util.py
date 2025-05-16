import logging
import sys

# ▶ 전역 로거 인스턴스 생성
logger = logging.getLogger("mylogger")  # 원하는 이름 지정
logger.setLevel(logging.INFO)

# ▶ 핸들러가 중복으로 추가되지 않도록 방지
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s ▶ %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# ▶ log 함수
def log(msg: str):
    logger.info(msg)
