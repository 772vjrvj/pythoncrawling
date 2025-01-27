from utils.sql_util import load_query  # SQL 쿼리 로딩 함수 임포트
from utils.date import get_date  # 날짜 유틸리티 함수 임포트
from sqlalchemy import text
import logging

def select_existing_data(session, src):
    """SELECT 쿼리: 특정 소스와 날짜에 맞는 데이터를 조회"""
    try:
        # 오늘 날짜와 어제 날짜 각각 구하기
        today_str = get_date(0)  # 오늘
        yesterday_str = get_date(-1)  # 어제

        # 쿼리 파일 읽기 (config에서 경로 관리)
        select_query = load_query('select_reg_yml')  # 쿼리 파일을 'select_reg_yml'로 읽어옴
        if not select_query:
            return []

        # 쿼리 실행 (OR 조건 사용)
        result = session.execute(
            text(select_query),
            {
                'src': src,
                'reg_ymd_today': '20241219',  # 첫 번째 날짜
                'reg_ymd_yesterday': '20241220'  # 두 번째 날짜
            }
        ).fetchall()

        return result
    except Exception as e:
        logging.error(f"데이터 조회 실패: {e}")
        return []


def insert_all_data_to_db(session, data_list):
    """INSERT ALL: 여러 개의 데이터를 한 번에 삽입"""
    try:
        # 쿼리 파일 읽기 (config에서 경로 관리)
        insert_query = load_query()  # config에서 경로를 가져옴
        if not insert_query:
            return

        # 여러 개의 데이터 삽입
        for data in data_list:
            session.execute(
                text(insert_query),
                {
                    'DMNFR_TREND_NO': data['DMNFR_TREND_NO'],
                    'STTS_CHG_CD': data['STTS_CHG_CD'],
                    'TTL': data['TTL'],
                    'SRC': data['SRC'],
                    'REG_YMD': data['REG_YMD'],
                    'URL': data['URL']
                }
            )

        session.commit()
        logging.info(f"{len(data_list)}개의 데이터 삽입 완료")
    except Exception as e:
        session.rollback()
        logging.error(f"데이터 삽입 실패: {e}")
