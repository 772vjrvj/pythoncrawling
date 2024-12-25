from config import QUERY_PATHS  # config에서 QUERY_PATHS 가져오기

# 예시로, 쿼리 파일을 로드하는 함수
def load_query(file_name):
    """쿼리 파일을 읽어 반환"""
    try:
        # 상대 경로에서 파일 경로 가져오기
        query_path = QUERY_PATHS.get(file_name)

        if not query_path:
            raise ValueError(f"{file_name} 경로를 찾을 수 없습니다.")

        # 쿼리 파일을 읽기
        with open(query_path, 'r', encoding='utf-8') as file:
            return file.read()

    except Exception as e:
        raise ValueError(f"쿼리 파일 로딩 실패: {e}")
