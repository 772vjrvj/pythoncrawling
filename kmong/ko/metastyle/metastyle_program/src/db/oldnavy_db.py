from src.db.database import Database

class OldNavyDB:
    def __init__(self, db: Database):
        self.db = db

    def create_tables(self):
        """ OldNavy 전용 테이블 생성 """
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            # OLDNAVY_MAIN 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS OLDNAVY_MAIN (
                NO INTEGER PRIMARY KEY AUTOINCREMENT,
                NOW_CATEGORY TEXT NOT NULL,
                NOW_PAGE_NO INTEGER NOT NULL,
                NOW_PRODUCT_NO INTEGER NOT NULL,
                TOTAL_PAGE_CNT INTEGER NOT NULL,
                TOTAL_PRODUCT_CNT INTEGER NOT NULL,
                COMPLETED_YN TEXT NOT NULL,
                UPDATE_DATE TEXT NOT NULL,
                REG_DATE TEXT NOT NULL,
                DELETED_YN TEXT NOT NULL
            )
            ''')

            # OLDNAVY_CATEGORY_LIST 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS OLDNAVY_CATEGORY_LIST (
                NO INTEGER PRIMARY KEY AUTOINCREMENT,
                PNO INTEGER NOT NULL,
                CID TEXT NOT NULL,
                CATEGORY TEXT NOT NULL,
                INPUT_START_PAGE INTEGER NOT NULL,
                INPUT_END_PAGE INTEGER NOT NULL,
                REAL_START_PAGE INTEGER NOT NULL,
                REAL_END_PAGE INTEGER NOT NULL,
                TOTAL_PAGE_CNT INTEGER NOT NULL,
                TOTAL_PRODUCT_CNT INTEGER NOT NULL,
                NOW_PAGE_NO INTEGER NOT NULL,
                NOW_PRODUCT_NO INTEGER NOT NULL,
                COMPLETED_YN TEXT NOT NULL,
                UPDATE_DATE TEXT NOT NULL,
                REG_DATE TEXT NOT NULL,
                DELETED_YN TEXT NOT NULL
            )
            ''')

            # OLDNAVY_PRODUCT_INFO 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS OLDNAVY_PRODUCT_INFO (
                NO INTEGER PRIMARY KEY AUTOINCREMENT,
                PNO INTEGER NOT NULL,
                CID TEXT NOT NULL,
                CATEGORY TEXT NOT NULL,
                PID TEXT NOT NULL,
                PRODUCT TEXT NOT NULL,
                DESCRIPTION TEXT NOT NULL,
                PAGE_NO INTEGER NOT NULL,
                PRODUCT_NO INTEGER NOT NULL,
                IMG_LIST TEXT NOT NULL,
                SUCCESS_YN TEXT NOT NULL,
                MAIN_URL TEXT NOT NULL,
                DETAIL_URL TEXT NOT NULL,
                ERROR_MESSAGE TEXT NOT NULL,
                REG_DATE TEXT NOT NULL,
                DELETED_YN TEXT NOT NULL
            )
            ''')

            conn.commit()
        finally:
            conn.close()
