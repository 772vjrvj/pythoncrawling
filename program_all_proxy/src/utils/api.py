# src/utils/api.py

import requests
import os
from src.utils.logger import ui_log

BASE_URL = 'http://vjrvj.cafe24.com'  # 개발환경

MITM_CERT_PATH = os.path.join(os.path.expanduser("~"), ".mitmproxy", "mitmproxy-ca-cert.pem")


def fetch_token_from_api_main(store_id: str) -> str:
    url = f"{BASE_URL}/auth/token/stores/{store_id}"
    ui_log(f" 🔑 토큰 요청: {url}")
    try:
        res = requests.get(url, timeout=5, verify=MITM_CERT_PATH)
        res.raise_for_status()

        token = res.text.strip()

        if not token or len(token) < 20:
            ui_log(f" 예외: 예상치 못한 응답 내용: {token}")
            return None

        ui_log(f"토큰 발급 성공 : {token}")
        return token

    except requests.RequestException as err:
        ui_log(f"[에러] ❌ 토큰 요청 실패: {err}")
    return None


def fetch_store_info_main(token: str, store_id: str):
    url = f"{BASE_URL}/stores/{store_id}"
    headers = {'Authorization': f'Bearer {token}'}
    ui_log(f" 🏬 유저 정보 요청: {url}")

    try:
        res = requests.get(url, headers=headers, timeout=3, verify=MITM_CERT_PATH)
        res.raise_for_status()
        info = res.json()
        ui_log(f" 유저명: {info.get('storeName', '-')}")
        return info
    except requests.RequestException as err:
        if hasattr(err, 'response') and err.response is not None:
            ui_log(f" ❌ 유저 정보 요청 실패: {err} → {err.response.text}")
        else:
            ui_log(f" ❌ 유저 정보 요청 실패: {err}")
        return None


def fetch_token_from_api(store_id: str) -> str:
    """
    네트워크 호출 없이 항상 더미 토큰을 반환합니다.
    실제 토큰 서버가 준비되면 원래 구현으로 복원하세요.
    """
    dummy_token = "dummy-token-00000000000000000000"  # length > 20
    ui_log(f"🔑 (더미) 토큰 발급: store_id={store_id} -> {dummy_token}")
    return dummy_token


def fetch_store_info(token: str, store_id: str):
    """
    네트워크 호출 없이 항상 더미 스토어 정보를 반환합니다.
    실제 API 사용 시에는 주석 처리된 원본 코드를 복원하세요.
    """
    dummy_info = {
        "name": store_id,
        "branch": f"테스트매장-{store_id}"
    }
    ui_log(f"🏬 (더미) 유저 정보 반환: store_id={store_id} token={token} -> name={dummy_info['name']}")
    return dummy_info
