# src/utils/logger.py
import sys
import os
import io
import logging
from datetime import datetime

def get_logger(name="proxy_logger"):
    # 로거 객체 생성 (이름은 기본적으로 "proxy_logger")
    logger = logging.getLogger(name)

    # 기존에 이미 핸들러가 등록되어 있으면 모두 제거 (중복 방지)
    if logger.hasHandlers():
        logger.handlers.clear()

    # 로그 레벨 설정 (INFO 이상만 출력)
    logger.setLevel(logging.INFO)

    # 콘솔 출력용 핸들러 설정 (stdout에 UTF-8로 출력되도록 함)
    utf8_stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace',
        line_buffering=True
    )
    console_handler = logging.StreamHandler(utf8_stdout)
    console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(console_handler)

    # 날짜별 로그 파일 저장 위치 설정
    # logger.py 위치 → src/utils → 두 단계 위로 이동 → logs 디렉토리 생성
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
    os.makedirs(log_dir, exist_ok=True)  # 디렉토리가 없으면 생성

    # 오늘 날짜 (예: 2025-06-29)
    today = datetime.now().strftime("%Y-%m-%d")

    # 로그 파일 경로: logs/proxy_2025-06-29.log
    log_path = os.path.join(log_dir, f"proxy_{today}.log")

    # 파일 핸들러 설정 (UTF-8 인코딩으로 로그 저장)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(file_handler)

    # 📌 root logger의 기존 핸들러 제거 후 proxy_logger 핸들러 복사
    logging.root.handlers.clear()
    for h in logger.handlers:
        logging.root.addHandler(h)

    # 디버깅용: 현재 설정된 로그 경로와 핸들러 출력 (print → logger.info 로 변경)
    logger.info(f"[로그 경로]: {log_path}")
    for h in logger.handlers:
        logger.info(f"[등록됨] {type(h).__name__} → {getattr(h, 'baseFilename', '콘솔')}")

    return logger

# 편하게 사용할 수 있도록 출력 함수 래핑
def info_log(*args, logger=None):
    # 전달된 logger가 없으면 get_logger()로 불러와서 info 로그 출력
    (logger or get_logger()).info(" ".join(map(str, args)))

def error_log(*args, logger=None):
    # 전달된 logger가 없으면 get_logger()로 불러와서 error 로그 출력
    (logger or get_logger()).error(" ".join(map(str, args)))
