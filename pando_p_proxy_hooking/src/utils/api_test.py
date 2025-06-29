import requests
import json
from mitmproxy import ctx

BASE_URL = 'https://api.dev.24golf.co.kr'  # 개발환경
# BASE_URL = 'https://api.24golf.co.kr'  # 운영환경

def build_url(store_id: str, param_type: str = None) -> str:
    if not store_id:
        raise ValueError("storeId is not set")

    path = 'crawl'
    if param_type == 'm':
        path = 'crawl/fields'
    elif param_type == 'g':
        path = 'crawl/group'

    return f"{BASE_URL}/stores/{store_id}/reservation/{path}"

def handle_response(response: requests.Response, method_name: str):
    try:
        response.raise_for_status()
        msg = f"{method_name} 판도서버 {response.status_code} : 성공"
        ctx.log.info(msg)

        # ✅ 응답 본문이 비어 있으면 None 반환
        if not response.content or response.text.strip() == "":
            ctx.log.info(f"{method_name} 응답 본문 없음 (빈 응답)")
            return None

        return response.json()

    except requests.HTTPError as err:
        error_msg = f"{method_name} 응답 오류 ({response.status_code}): {response.text}"
        ctx.log.error(error_msg)
        raise
    except Exception as err:
        error_msg = f"{method_name} 실행 오류: {str(err)}"
        ctx.log.error(error_msg)
        raise

def post(token: str, store_id: str, data: dict, param_type: str = None):
    url = build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    ctx.log.info(f"[POST] {url}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
    try:
        res = requests.post(url, json=data, headers=headers, proxies={"http": None, "https": None})
        return handle_response(res, 'POST')
    except Exception as e:
        ctx.log.error(f"❌ POST 요청 중 예외 발생: {e}")
        return None

def put(token: str, store_id: str, data: dict, param_type: str = None):
    url = build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    ctx.log.info(f"[PUT] {url}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
    try:
        res = requests.put(url, json=data, headers=headers, proxies={"http": None, "https": None})
        return handle_response(res, 'PUT')
    except Exception as e:
        ctx.log.error(f"❌ PUT 요청 중 예외 발생: {e}")
        return None

def patch(token: str, store_id: str, data: dict, param_type: str = None):
    url = build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    ctx.log.info(f"[PATCH] {url}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
    try:
        res = requests.patch(url, json=data, headers=headers, proxies={"http": None, "https": None})
        return handle_response(res, 'PATCH')
    except Exception as e:
        ctx.log.error(f"❌ PATCH 요청 중 예외 발생: {e}")
        return None

def delete(token: str, store_id: str, data: dict = None, param_type: str = None):
    url = build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    ctx.log.info(f"[DELETE] {url}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
    try:
        res = requests.delete(url, json=data, headers=headers, proxies={"http": None, "https": None})
        return handle_response(res, 'DELETE')
    except Exception as e:
        ctx.log.error(f"❌ DELETE 요청 중 예외 발생: {e}")
        return None

def fetch_token_from_api(store_id: str):
    url = f"{BASE_URL}/auth/token/stores/{store_id}/role/singleCrawler"
    ctx.log.info(f"🔑 토큰 요청: {url}")
    try:
        res = requests.get(url, timeout=3, proxies={"http": None, "https": None})
        res.raise_for_status()
        data = res.json()
        token = data.get('token', data)
        ctx.log.info("✅ 토큰 발급 성공")
        return token
    except requests.RequestException as err:
        msg = f"❌ 토큰 요청 실패: {err}"
        ctx.log.error(msg)
    ctx.log.warn("⚠️ fallback 토큰 반환")
    return None

def fetch_store_info(token: str, store_id: str):
    url = f"{BASE_URL}/stores/{store_id}"
    headers = {'Authorization': f'Bearer {token}'}
    ctx.log.info(f"🏬 매장 정보 요청: {url}")
    try:
        res = requests.get(url, headers=headers, proxies={"http": None, "https": None})
        res.raise_for_status()
        return res.json()
    except requests.RequestException as err:
        msg = f"❌ 매장 정보 요청 실패: {err}"
        ctx.log.error(msg)
        return None
