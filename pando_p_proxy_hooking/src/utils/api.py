# src/utils/api.py
import requests
import os

BASE_URL = 'https://api.dev.24golf.co.kr'  # 개발
# BASE_URL = 'https://api.24golf.co.kr'    # 운영

# 인증서 경로 (.pem 형식이어야 함)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # src/utils → src → project root
MITM_CERT_PATH = os.path.join(BASE_DIR, "cert", "mitmproxy-ca-cert.pem")

def fetch_token_from_api(store_id: str) -> str:
    url = f"{BASE_URL}/auth/token/stores/{store_id}/role/singleCrawler"
    print(f"토큰 요청: {url}")
    try:
        res = requests.get(url, timeout=5, verify=MITM_CERT_PATH)
        res.raise_for_status()

        # 응답 본문이 JSON이 아닌 텍스트 토큰임
        token = res.text.strip()

        if not token or len(token) < 20:
            print(f"예상치 못한 응답: {token}")
            return None

        print(f"토큰 발급 성공 : {token}")
        return token

    except requests.RequestException as err:
        print(f"토큰 요청 실패: {err}")
    print("fallback 토큰 반환")
    return None


def fetch_store_info(token: str, store_id: str):
    url = f"{BASE_URL}/stores/{store_id}"
    headers = {'Authorization': f'Bearer {token}'}
    try:
        res = requests.get(url, headers=headers, timeout=3, verify=MITM_CERT_PATH)
        res.raise_for_status()
        info = res.json()
        print(f"매장명: {info.get('storeName', '-')}")
        return info
    except requests.RequestException as err:
        if hasattr(err, 'response') and err.response is not None:
            print(f"매장 정보 요청 실패: {err} → {err.response.text}")
        else:
            print(f"매장 정보 요청 실패: {err}")
        return None