import sqlite3
from src.db.database import Database
from src.model.oldnavy.category_list_model import CategoryListModel
from typing import Optional

class CategoryListDAO:
    def __init__(self, db: Database):
        self.db = db

    def _map_to_model(self, model_class, rows):
        """ 공통 데이터 매핑 함수 """
        return [model_class(**dict(zip(model_class.COLUMNS, row))) for row in rows]

    def find_active_categories(self):
        """ OLDNAVY_CATEGORY_LIST 테이블에서 DELETED_YN = 'N' 인 항목 조회 """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            query = '''
                SELECT NO, PNO, CID, CATEGORY, INPUT_START_PAGE, INPUT_END_PAGE,
                       REAL_START_PAGE, REAL_END_PAGE, TOTAL_PAGE_CNT, TOTAL_PRODUCT_CNT,
                       NOW_PAGE_NO, NOW_PRODUCT_NO, COMPLETED_YN, UPDATE_DATE, REG_DATE, DELETED_YN
                FROM OLDNAVY_CATEGORY_LIST
                WHERE DELETED_YN = 'N'
            '''
            cursor.execute(query)
            rows = cursor.fetchall()

            # 공통 매핑 함수 사용 (컬럼 리스트 제거)
            return self._map_to_model(CategoryListModel, rows)

        except sqlite3.Error as e:
            print(f"[ERROR] Database query failed: {e}")
            return []

        finally:
            conn.close()  # 예외 발생 여부와 관계없이 반드시 DB 연결 닫기


    def insert_category(self, category: CategoryListModel) -> Optional[CategoryListModel]:
        """ OLDNAVY_CATEGORY_LIST 테이블에 새로운 카테고리 삽입 후, 삽입된 객체 반환 """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            query = '''
                INSERT INTO OLDNAVY_CATEGORY_LIST (
                    PNO, CID, CATEGORY, INPUT_START_PAGE, INPUT_END_PAGE,
                    REAL_START_PAGE, REAL_END_PAGE, TOTAL_PAGE_CNT, TOTAL_PRODUCT_CNT,
                    NOW_PAGE_NO, NOW_PRODUCT_NO, COMPLETED_YN, UPDATE_DATE, REG_DATE, DELETED_YN
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            values = (
                category.pno, category.cid, category.category,
                category.input_start_page, category.input_end_page,
                category.real_start_page, category.real_end_page,
                category.total_page_cnt, category.total_product_cnt,
                category.now_page_no, category.now_product_no,
                category.completed_yn, category.update_date,
                category.reg_date, category.deleted_yn
            )

            cursor.execute(query, values)
            conn.commit()
            inserted_id = cursor.lastrowid  # 삽입된 행의 ID 가져오기

            # 삽입된 데이터를 포함한 새로운 CategoryListModel 반환
            return CategoryListModel(
                no=inserted_id,
                pno=category.pno,
                cid=category.cid,
                category=category.category,
                input_start_page=category.input_start_page,
                input_end_page=category.input_end_page,
                real_start_page=category.real_start_page,
                real_end_page=category.real_end_page,
                total_page_cnt=category.total_page_cnt,
                total_product_cnt=category.total_product_cnt,
                now_page_no=category.now_page_no,
                now_product_no=category.now_product_no,
                completed_yn=category.completed_yn,
                update_date=category.update_date,
                reg_date=category.reg_date,
                deleted_yn=category.deleted_yn
            )

        except sqlite3.Error as e:
            print(f"[ERROR] Insert failed: {e}")
            conn.rollback()
            return None

        finally:
            conn.close()
