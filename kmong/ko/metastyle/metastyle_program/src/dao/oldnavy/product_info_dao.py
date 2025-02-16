import sqlite3
from src.db.database import Database
from src.model.oldnavy.product_info_model import ProductInfoModel

class ProductInfoDAO:
    def __init__(self, db: Database):
        self.db = db

    def _map_to_model(self, model_class, rows):
        """ 공통 데이터 매핑 함수 """
        return [model_class(**dict(zip(model_class.COLUMNS, row))) for row in rows]

    def find_successful_products(self):
        """ PRODUCT_INFO 테이블에서 SUCCESS_YN = 'Y' 인 항목 조회 """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            query = '''
                SELECT NO, PNO, CID, CATEGORY, PID, PRODUCT, DESCRIPTION, PAGE_NO,
                       PRODUCT_NO, IMG_LIST, SUCCESS_YN, MAIN_URL, DETAIL_URL,
                       ERROR_MESSAGE, REG_DATE, DELETED_YN
                FROM PRODUCT_INFO
                WHERE SUCCESS_YN = 'Y'
            '''
            cursor.execute(query)
            rows = cursor.fetchall()

            # 공통 매핑 함수 사용
            return self._map_to_model(ProductInfoModel, rows)

        except sqlite3.Error as e:
            print(f"[ERROR] Database query failed: {e}")
            return []

        finally:
            conn.close()  # 예외 발생 여부와 관계없이 반드시 DB 연결 닫기


    def insert_all(self, products: list[ProductInfoModel]) -> list[ProductInfoModel]:
        """ PRODUCT_INFO 테이블에 여러 개의 데이터를 한 번의 SQL 실행으로 삽입하고, 삽입된 객체 리스트 반환 """
        if not products:
            return []

        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            query = '''
                INSERT INTO PRODUCT_INFO (
                    PNO, CID, CATEGORY, PID, PRODUCT, DESCRIPTION, PAGE_NO,
                    PRODUCT_NO, IMG_LIST, SUCCESS_YN, MAIN_URL, DETAIL_URL,
                    ERROR_MESSAGE, REG_DATE, DELETED_YN
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''

            # 여러 개의 데이터를 리스트 형식으로 변환
            values = [
                (
                    product.pno, product.cid, product.category,
                    product.pid, product.product, product.description,
                    product.page_no, product.product_no, product.img_list,
                    product.success_yn, product.main_url, product.detail_url,
                    product.error_message, product.reg_date, product.deleted_yn
                )
                for product in products
            ]

            # executemany를 사용하여 한 번에 삽입
            cursor.executemany(query, values)
            conn.commit()

            # lastrowid가 여러 개의 행 삽입 시 첫 번째 ID만 반환하는 경우가 있음
            inserted_ids = range(cursor.lastrowid, cursor.lastrowid + len(products))

            # 삽입된 데이터를 새로운 ProductInfoModel 객체로 변환하여 리스트에 저장
            inserted_products = [
                ProductInfoModel(
                    no=inserted_id,
                    pno=product.pno,
                    cid=product.cid,
                    category=product.category,
                    pid=product.pid,
                    product=product.product,
                    description=product.description,
                    page_no=product.page_no,
                    product_no=product.product_no,
                    img_list=product.img_list,
                    success_yn=product.success_yn,
                    main_url=product.main_url,
                    detail_url=product.detail_url,
                    error_message=product.error_message,
                    reg_date=product.reg_date,
                    deleted_yn=product.deleted_yn
                )
                for inserted_id, product in zip(inserted_ids, products)
            ]

            return inserted_products  # 삽입된 데이터 리스트 반환

        except sqlite3.Error as e:
            print(f"[ERROR] Bulk insert failed: {e}")
            conn.rollback()
            return []

        finally:
            conn.close()

