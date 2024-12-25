from sqlalchemy import Column, Integer, String, CHAR
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DmnfrTrend(Base):
    __tablename__ = 'DMNFR_TREND'
    __table_args__ = {'schema': 'PLATNW'}

    # 컬럼 정의
    DMNFR_TREND_NO = Column(Integer, primary_key=True, nullable=False)
    STTS_CHG_CD = Column(String(4))
    TTL = Column(String(200))
    SRC = Column(String(100))
    REG_YMD = Column(CHAR(8))
    URL = Column(String(2000))

    # 각 컬럼에 대한 설명
    def __repr__(self):
        return f"<DmnfrTrend(DMNFR_TREND_NO={self.DMNFR_TREND_NO}, TTL={self.TTL}, SRC={self.SRC}, REG_YMD={self.REG_YMD}, URL={self.URL})>"

