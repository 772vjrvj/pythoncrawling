import sqlite3

class Database:
    def __init__(self, db_path="data.db"):
        self.db_path = db_path

    def connect(self):
        """ 데이터베이스 연결 """
        return sqlite3.connect(self.db_path)
