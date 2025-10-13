# src/utils/api_proxy.py
import requests
import json
from mitmproxy import ctx
from src.utils.logger import log_info, log_error, log_warn  # ✅ 공통 로그 함수 사용

BASE_URL = 'https://api.dev.24golf.co.kr'  # 개발환경
# BASE_URL = 'https://api.24golf.co.kr'      # 운영환경
LOCAL_URL = 'http://localhost:32123'       # 운영환경


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
        log_info(msg)

        if not response.content or response.text.strip() == "":
            log_info(f"{method_name} 응답 본문 없음 (빈 응답)")
            return None

        return response.json()

    except requests.HTTPError as err:
        error_msg = f"{method_name} 응답 오류 ({response.status_code}): {response.text}"
        log_error(error_msg)
        raise
    except Exception as err:
        error_msg = f"{method_name} 실행 오류: {str(err)}"
        log_error(error_msg)
        raise


def post(token: str, store_id: str, data: dict, param_type: str = None):
    url = build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    log_info(f"[POST] header : {headers}")
    log_info(f"[POST] {url}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
    try:
        res = requests.post(url, json=data, headers=headers, proxies={"http": None, "https": None})
        return handle_response(res, 'POST')
    except Exception as e:
        log_error(f"POST 요청 중 예외 발생: {e}")
        return None


def put(token: str, store_id: str, data: dict, param_type: str = None):
    url = build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    log_info(f"[PUT] header : {headers}")
    log_info(f"[PUT] {url}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
    try:
        res = requests.put(url, json=data, headers=headers, proxies={"http": None, "https": None})
        return handle_response(res, 'PUT')
    except Exception as e:
        log_error(f"PUT 요청 중 예외 발생: {e}")
        return None


def patch(token: str, store_id: str, data: dict, param_type: str = None):
    url = build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    log_info(f"[PATCH] header : {headers}")
    log_info(f"[PATCH] {url}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
    try:
        res = requests.patch(url, json=data, headers=headers, proxies={"http": None, "https": None})
        return handle_response(res, 'PATCH')
    except Exception as e:
        log_error(f"PATCH 요청 중 예외 발생: {e}")
        return None


def local_web_req(token: str, store_id: str, data: dict, param_type: str = None):
    url = local_web_build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    log_info(f"[GET] header : {headers}")
    log_info(f"[GET] {url}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
    try:
        res = requests.get(url, params=data, headers=headers, proxies={"http": None, "https": None})
        return handle_response(res, 'GET')
    except Exception as e:
        log_error(f"PATCH 요청 중 예외 발생: {e}")
        return None


def delete(token: str, store_id: str, data: dict = None, param_type: str = None):
    url = build_url(store_id, param_type)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    log_info(f"[DELETE] header : {headers}")
    log_info(f"[DELETE] {url}\n{json.dumps(data, ensure_ascii=False, indent=2)}")
    try:
        res = requests.delete(url, json=data, headers=headers, proxies={"http": None, "https": None})
        return handle_response(res, 'DELETE')
    except Exception as e:
        log_error(f"DELETE 요청 중 예외 발생: {e}")
        return None


def fetch_token_from_api(store_id: str):
    url = f"{BASE_URL}/auth/token/stores/{store_id}/role/singleCrawler"
    log_info(f"토큰 요청: {url}")
    try:
        res = requests.get(url, timeout=3, proxies={"http": None, "https": None})
        res.raise_for_status()
        data = res.json()
        token = data.get('token', data)
        log_info("토큰 발급 성공")
        return token
    except requests.RequestException as err:
        msg = f"토큰 요청 실패: {err}"
        log_error(msg)
    log_warn("fallback 토큰 반환")
    return None


def fetch_store_info(token: str, store_id: str):
    url = f"{BASE_URL}/stores/{store_id}"
    headers = {'Authorization': f'Bearer {token}'}
    log_info(f"매장 정보 요청: {url}")
    try:
        res = requests.get(url, headers=headers, proxies={"http": None, "https": None})
        res.raise_for_status()
        return res.json()
    except requests.RequestException as err:
        msg = f"매장 정보 요청 실패: {err}"
        log_error(msg)
        return None


def local_web_build_url(store_id: str, param_type: str = None) -> str:
    if not store_id:
        raise ValueError("storeId is not set")

    return f"{LOCAL_URL}/reseration"
