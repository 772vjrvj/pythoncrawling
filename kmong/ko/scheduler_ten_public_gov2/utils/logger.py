import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logger(name='root', log_level=logging.INFO):
    """
    기본 로거 설정 함수 (날짜별로 로그 기록)
    :param name: 로거 이름 (기본은 'root')
    :param log_level: 로그 레벨 (기본은 INFO)
    :return: 설정된 로거 객체
    """
    # 로그 형식 설정
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 콘솔 핸들러 설정 (콘솔 출력)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    # 파일 핸들러 설정 (날짜별 로그 파일 기록)
    # 하루마다 로그 파일을 새로 만듭니다.
    # 7일치 로그만 보관하고, 그 이전의 로그 파일은 삭제합니다.
    file_handler = TimedRotatingFileHandler('app.log', when='midnight', interval=1, backupCount=7)
    file_handler.setFormatter(log_formatter)

    # 로거 설정
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# 로거 설정 (애플리케이션 시작 시 한 번만 호출)
logger = setup_logger()