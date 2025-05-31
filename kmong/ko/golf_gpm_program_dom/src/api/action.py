from src.utils.log import log, log_json
from src.utils.config import EXTERNAL_API_BASE_URL
from src.state.dom_state import DomState
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

        # 임시로 register도 patch 사용 (2025-05-26 이슈)
        method = {"register": requests.patch, "edit": requests.patch, "delete": requests.delete}.get(action)

        log(f"[{action}] : {url}")
        if method:
            response = method(url, headers=headers, json=payload)

            dom_list = DomState.get_all()
            matched_index = None

            for i in range(len(dom_list) - 1, -1, -1):
                dom = dom_list[i]
                if dom.get("name") == payload.get("name") and dom.get("phone") == payload.get("phone"):
                    matched_index = i
                    break

            if response.status_code in (200, 201):
                log(f"[{action}] : 판도 서버 전송 성공")
                if matched_index is not None:
                    updated = {**dom_list[matched_index], "succYn": "Y"}
                    DomState.update(matched_index, updated)
                    log(f"[{action}] : DomState 업데이트 완료 → succYn=Y {updated}")
            else:
                log(f"[{action}] : 판도 서버 전송 실패 -> {response.status_code}")
                try:
                    log(f"[{action}] : 실패 내용 ↓")
                    log_json(response.json())
                except Exception as e:
                    log(f"[{action}] : Exception 응답 본문 -> {response.text}")
                    log(f"[{action}] : Exception e -> {e}")

                if matched_index is not None:
                    updated = {**dom_list[matched_index], "succYn": "N"}
                    DomState.update(matched_index, updated)
                    log(f"[{action}] : DomState 업데이트 완료 → succYn=N {updated}")
        else:
            log(f"[{action}] : 지원되지 않는 action")

    except Exception as e:
        log(f"[{action}] : API 호출 중 예외 발생 -> {e}")
