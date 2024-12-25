import os

# 쿼리 파일 경로 설정 (절대 경로로 지정)
QUERY_PATHS = {
    "insert_all": os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db', 'dmnfr_trend', 'sql', 'insert_all.sql')),
    "insert_one": os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db', 'dmnfr_trend', 'sql', 'insert_one.sql')),
    "select_reg_yml": os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db', 'dmnfr_trend', 'sql', 'select_reg_yml.sql'))
}