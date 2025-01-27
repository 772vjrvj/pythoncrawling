from db.dmnfr_trend.dmnfr_trend_models import DmnfrTrend  # 모델 임포트
from utils.date import get_date  # 날짜 유틸리티 함수 임포트
from utils.logger import logger
from sqlalchemy.orm import Session

def select_existing_data(session: Session, src: str):
    """SELECT 쿼리: 특정 소스와 날짜에 맞는 데이터를 조회"""
    try:
        # 오늘 날짜와 어제 날짜 구하기
        today_str = get_date(0)  # 오늘
        yesterday_str = get_date(-1)  # 어제

        # DB 조회 쿼리 (src와 reg_ymd를 조건으로 추가)
        existing_data = session.query(DmnfrTrend).filter(
            DmnfrTrend.SRC == src,
            DmnfrTrend.REG_YMD.in_([today_str, yesterday_str])
        ).all()

        # DTO로 변환 (예시)
        data_list = [
            {'DMNFR_TREND_NO': item.DMNFR_TREND_NO, 'STTS_CHG_CD': item.STTS_CHG_CD, 'SRC': item.SRC, 'REG_YMD': item.REG_YMD, 'TTL': item.TTL, 'URL': item.URL}
            for item in existing_data
        ]

        return data_list
    except Exception as e:
        logger.error(f"데이터 조회 실패: {e}")
        return []


def select_init_data(session: Session, src: str):
    try:
        count = session.query(DmnfrTrend).filter(
            DmnfrTrend.SRC == src
        ).count()

        return count
    except Exception as e:
        logger.error(f"데이터 조회 실패: {e}")
        return []


def insert_all_data_to_db(session: Session, data_list: list):
    """INSERT ALL: 여러 개의 데이터를 한 번에 삽입"""
    try:
        trends = []
        for data in data_list:
            trend = DmnfrTrend(
                DMNFR_TREND_NO=data['DMNFR_TREND_NO'],
                STTS_CHG_CD=data['STTS_CHG_CD'],
                TTL=data['TTL'],
                SRC=data['SRC'],
                REG_YMD=data['REG_YMD'],
                URL=data['URL']
            )
            trends.append(trend)

        session.add_all(trends)
        session.commit()
        logger.info(f"{len(data_list)}개의 데이터 삽입 완료")

        # 삽입된 데이터의 개수 반환
        return len(data_list)
    except Exception as e:
        session.rollback()
        logger.error(f"데이터 삽입 실패: {e}")
        # 실패 시 False 반환
        return False

