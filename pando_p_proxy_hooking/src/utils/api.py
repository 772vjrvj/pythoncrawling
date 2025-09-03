# src/utils/api.py

import requests
import os
from src.utils.logger import ui_log

# BASE_URL = 'https://api.dev.24golf.co.kr'  # 개발환경
BASE_URL = 'https://api.24golf.co.kr'    # 운영환경

MITM_CERT_PATH = os.path.join(os.path.expanduser("~"), ".mitmproxy", "mitmproxy-ca-cert.pem")


def fetch_token_from_api(store_id: str) -> str:
    url = f"{BASE_URL}/auth/token/stores/{store_id}/role/singleCrawler"
    ui_log(f"[판도] 🔑 토큰 요청: {url}")
    try:
        res = requests.get(url, timeout=5, verify=MITM_CERT_PATH)
        res.raise_for_status()

        token = res.text.strip()

        if not token or len(token) < 20:
            ui_log(f"[판도] 예외: 예상치 못한 응답 내용: {token}")
            return None

        ui_log(f"[판도] ✅ 토큰 발급 성공 : {token}")
        return token

    except requests.RequestException as err:
        ui_log(f"[판도] ❌ 토큰 요청 실패: {err}")
    ui_log("[판도] ⚠️ fallback 토큰 반환")
    return None


def fetch_store_info(token: str, store_id: str):
    url = f"{BASE_URL}/stores/{store_id}"
    headers = {'Authorization': f'Bearer {token}'}
    ui_log(f"[판도] 🏬 매장 정보 요청: {url}")
    try:
        res = requests.get(url, headers=headers, timeout=3, verify=MITM_CERT_PATH)
        res.raise_for_status()
        info = res.json()
        ui_log(f"[판도] 매장명: {info.get('storeName', '-')}")
        return info
    except requests.RequestException as err:
        if hasattr(err, 'response') and err.response is not None:
            ui_log(f"[판도] ❌ 매장 정보 요청 실패: {err} → {err.response.text}")
        else:
            ui_log(f"[판도] ❌ 매장 정보 요청 실패: {err}")
        return None
