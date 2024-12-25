import os
import configparser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.logger import logger  # 로깅 유틸 불러오기

def connect_to_db():
    """DB 연결 함수 (INI 파일에서 정보 읽어오기)"""

    # INI 파일 경로
    config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'db_config.ini')

    # INI 파일 존재 여부 확인
    if not os.path.exists(config_file):
        logger.error(f"INI 파일이 존재하지 않습니다: {config_file}")
        return None

    # configparser로 INI 파일 읽기
    config = configparser.ConfigParser()
    config.read(config_file)

    # INI 파일에서 DB 연결 정보 가져오기
    try:
        host = config.get('database', 'host')
        port = config.get('database', 'port')
        dbname = config.get('database', 'dbname')
        username = config.get('database', 'username')
        password = config.get('database', 'password')
    except configparser.NoSectionError as e:
        logger.error(f"INI 파일에 'database' 섹션이 없습니다: {e}")
        return None
    except configparser.NoOptionError as e:
        logger.error(f"INI 파일에 필요한 옵션이 없습니다: {e}")
        return None

    # DB 연결 문자열 생성
    db_url = f'oracle+cx_oracle://{username}:{password}@{host}:{port}/?service_name={dbname}'

    try:
        # SQLAlchemy 연결 설정
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        logger.info("DB 연결 성공")
        return session
    except Exception as e:
        logger.error(f"DB 연결 실패: {e}")
        return None
