from src.utils.log import log, log_json
from src.utils.config import EXTERNAL_API_BASE_URL
import requests

def send_to_external_api_action(token, store_id, action, payload, param_type):
    log(f"[{action}] : type {param_type}")
    log(f"[{action}] : payload ↓")
    log_json(payload)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        if param_type == 'm':
            url = f"{EXTERNAL_API_BASE_URL}/stores/{store_id}/reservation/crawl/fields"
        elif param_type == 'g':
            url = f"{EXTERNAL_API_BASE_URL}/stores/{store_id}/reservation/crawl/group"
        else:
            url = f"{EXTERNAL_API_BASE_URL}/stores/{store_id}/reservation/crawl"

        method = {"register": requests.post, "edit": requests.patch, "delete": requests.delete}.get(action)
        log(f"[{action}] : {url}")
        if method:
            response = method(url, headers=headers, json=payload)

            if response.status_code == 200 or response.status_code == 201:
                log(f"[{action}] : 판도 서버 전송 성공")
            else:
                log(f"[{action}] : 판도 서버 전송 실패 -> {response.status_code}")
                try:
                    log(f"[{action}] : 실패 내용 ↓")
                    log_json(response.json())
                except Exception as e:
                    log(f"[{action}] : Exception 응답 본문 -> {response.text}")
                    log(f"[{action}] : Exception e -> {e}")
        else:
            log(f"[{action}] : 지원되지 않는 action")
    except Exception as e:
        log(f"[{action}] : API 호출 중 예외 발생 -> {e}")

