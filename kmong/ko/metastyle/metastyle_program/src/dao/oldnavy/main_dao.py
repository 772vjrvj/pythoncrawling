import sqlite3
from src.db.database import Database
from src.model.oldnavy.main_model import MainModel
from typing import Optional

class MainDAO:
    def __init__(self, db: Database):
        self.db = db

    def _map_to_model(self, model_class, rows):
        """ 공통 데이터 매핑 함수 """
        return [model_class(**dict(zip(model_class.COLUMNS, row))) for row in rows]

    def find_active_main_entries(self):
        """ MAIN 테이블에서 DELETED_YN = 'N' 인 항목 조회 """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            query = '''
                SELECT NO, NOW_CATEGORY, NOW_PAGE_NO, NOW_PRODUCT_NO,
                       TOTAL_PAGE_CNT, TOTAL_PRODUCT_CNT, COMPLETED_YN,
                       UPDATE_DATE, REG_DATE, DELETED_YN
                FROM MAIN
                WHERE DELETED_YN = 'N'
            '''
            cursor.execute(query)
            rows = cursor.fetchall()

            # 공통 매핑 함수 사용
            return self._map_to_model(MainModel, rows)

        except sqlite3.Error as e:
            print(f"[ERROR] Database query failed: {e}")
            return []

        finally:
            conn.close()  # 예외 발생 여부와 관계없이 반드시 DB 연결 닫기


    def find_latest_main_entry(self):
        """ MAIN 테이블에서 DELETED_YN = 'N' 이면서 REG_DATE가 가장 최신인 데이터 1개 조회 """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            query = '''
                SELECT NO, NOW_CATEGORY, NOW_PAGE_NO, NOW_PRODUCT_NO,
                       TOTAL_PAGE_CNT, TOTAL_PRODUCT_CNT, COMPLETED_YN,
                       UPDATE_DATE, REG_DATE, DELETED_YN
                FROM MAIN
                WHERE DELETED_YN = 'N'
                ORDER BY REG_DATE DESC
                LIMIT 1
            '''
            cursor.execute(query)
            row = cursor.fetchone()  # 최신 1개만 가져옴

            # 공통 매핑 함수 사용
            return self._map_to_model(MainModel, [row])[0] if row else None

        except sqlite3.Error as e:
            print(f"[ERROR] Database query failed: {e}")
            return None

        finally:
            conn.close()  # 예외 발생 여부와 관계없이 반드시 DB 연결 닫기




    def insert_main_entry(self, main_model: MainModel) -> Optional[MainModel]:
        """ MAIN 테이블에 새 데이터 삽입 후 삽입된 객체를 반환 """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            query = '''
                INSERT INTO MAIN (NOW_CATEGORY, NOW_PAGE_NO, NOW_PRODUCT_NO,
                                  TOTAL_PAGE_CNT, TOTAL_PRODUCT_CNT, COMPLETED_YN,
                                  UPDATE_DATE, REG_DATE, DELETED_YN)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, (
                main_model.now_category, main_model.now_page_no, main_model.now_product_no,
                main_model.total_page_cnt, main_model.total_product_cnt, main_model.completed_yn,
                main_model.update_date, main_model.reg_date, main_model.deleted_yn
            ))

            conn.commit()
            inserted_id = cursor.lastrowid  # 삽입된 행의 ID 가져오기

            # 새롭게 생성된 객체를 반환
            return MainModel(
                no=inserted_id,  # 자동 증가된 ID
                now_category=main_model.now_category,
                now_page_no=main_model.now_page_no,
                now_product_no=main_model.now_product_no,
                total_page_cnt=main_model.total_page_cnt,
                total_product_cnt=main_model.total_product_cnt,
                completed_yn=main_model.completed_yn,
                update_date=main_model.update_date,
                reg_date=main_model.reg_date,
                deleted_yn=main_model.deleted_yn
            )

        except sqlite3.Error as e:
            print(f"[ERROR] Failed to insert data: {e}")
            conn.rollback()
            return None

        finally:
            conn.close()  # 예외 발생 여부와 관계없이 반드시 DB 연결 닫기



