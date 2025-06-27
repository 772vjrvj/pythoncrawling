# src/utils/api.py
import requests

# BASE_URL = 'https://api.dev.24golf.co.kr'; //개발환경
BASE_URL = 'https://api.24golf.co.kr'  # 운영환경

def build_url(store_id: str, param_type: str = None) -> str:
    if not store_id:
        raise ValueError("❌ storeId is not set")

    path = 'crawl'
    if param_type == 'm':
        path = 'crawl/fields'
    elif param_type == 'g':
        path = 'crawl/group'

    return f"{BASE_URL}/stores/{store_id}/reservation/{path}"

def handle_response(response: requests.Response, method_name: str):
    try:
        response.raise_for_status()
        print(f"✅ {method_name} 판도서버 {response.status_code} : 성공")
        return response.json()
    except requests.HTTPError as err:
        print(f"❌ {method_name} 응답 오류 ({response.status_code}): {response.text}")
        raise
    except Exception as err:
        print(f"❌ {method_name} 실행 오류: {str(err)}")
        raise

def post(token: str, store_id: str, data: dict, param_type: str = None):
    url = build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    res = requests.post(url, json=data, headers=headers)
    return handle_response(res, 'POST')

def put(token: str, store_id: str, data: dict, param_type: str = None):
    url = build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    res = requests.put(url, json=data, headers=headers)
    return handle_response(res, 'PUT')

def patch(token: str, store_id: str, data: dict, param_type: str = None):
    url = build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    res = requests.patch(url, json=data, headers=headers)
    return handle_response(res, 'PATCH')

def delete(token: str, store_id: str, data: dict = None, param_type: str = None):
    url = build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    res = requests.delete(url, json=data, headers=headers)
    return handle_response(res, 'DELETE')

def fetch_token_from_api(store_id: str):
    url = f"{BASE_URL}/auth/token/stores/{store_id}/role/singleCrawler"
    print(f"🔑 토큰 요청: {url}")
    try:
        res = requests.get(url, timeout=3)
        res.raise_for_status()
        data = res.json()
        token = data.get('token', data)
        print("✅ 토큰 발급 성공")
        return token
    except requests.RequestException as err:
        print(f"❌ 토큰 요청 실패: {err}")
    print("⚠️ fallback 토큰 반환")
    return None

def fetch_store_info(token: str, store_id: str):
    url = f"{BASE_URL}/stores/{store_id}"
    headers = {'Authorization': f'Bearer {token}'}
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as err:
        print(f"❌ 매장 정보 요청 실패: {err}")
        return None
