import logging
from db.dmnfr_trend.dmnfr_trend_operations import select_existing_data  # select_existing_data 함수 임포트
from db.db_connection import connect_to_db  # DB 연결 함수 import
from sqlalchemy import text
from utils.logger import logger  # 로깅 유틸 불러오기
from utils.date import get_date  # 날짜 관련 유틸리티 함수 import
from utils.sql_util import load_query  # 쿼리 로드 함수 import

def main():
    # DB 연결 시도
    session = connect_to_db()  # DB 연결 함수 호출
    if not session:
        print("DB 연결 실패")
        return

    # '미국 USDA 보도자료'로 조회할 데이터 소스 설정
    src = '미국 USDA 보도자료'

    # select_existing_data 함수 호출하여 데이터 조회
    result = select_existing_data(session, src)

    # 조회된 데이터 출력
    if result:
        print(f"조회된 데이터: {result}")
    else:
        print("데이터를 조회할 수 없습니다.")

    # DB 세션 종료
    session.close()
    print("DB 연결 종료")

if __name__ == '__main__':
    main()
