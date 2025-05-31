import requests
from requests import RequestException
from src.utils.config import EXTERNAL_API_BASE_URL, TEST_TOKEN
from src.utils.log import log

def get_golf_token(store_id):
    url = f"{EXTERNAL_API_BASE_URL}/auth/token/stores/{store_id}/role/singleCrawler"
    log(f"토큰 요청 URL: {url}")
    try:
        response = requests.get(url, timeout=3)

        if response.status_code == 200:
            token = response.text.strip()  # JSON이면 response.json().get("token") 등으로 교체
            log(f"토큰 요청 성공: {token}")
            return token
        else:
            log(f"토큰 요청 실패 - 상태 코드: {response.status_code}")
    except RequestException as e:
        log(f"토큰 요청 중 오류 발생: {e}")

    # 실패 fallback
    log("임시 토큰 사용")
    return TEST_TOKEN