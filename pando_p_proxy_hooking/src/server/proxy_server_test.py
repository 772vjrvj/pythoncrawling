# src/proxy_server.py
from mitmproxy import http
import asyncio
import json
import re
from urllib.parse import parse_qs

from src.router.hook_router import save_request, match_and_dispatch

TARGETS_REQUEST = {
    "register": re.compile(r"/rest/ui/booking/register(\?timestamp=|$)"),
    "edit": re.compile(r"/rest/ui/booking/\d+/edit(\?timestamp=|$)"),
    "edit_move": re.compile(r"/rest/ui/booking/\d+/ajax-edit(\?timestamp=|$)"),
    "delete": re.compile(r"/rest/ui/booking/\d+/delete(\?timestamp=|$)"),
    "delete_mobile": re.compile(r"/rest/ui/polling/booking/\d+\?(?=.*\btimestamp=)(?=.*\bbookingStartDt=)(?=.*\bdata=)(?=.*\bbookingNumber=)"),
}

TARGETS_RESPONSE = TARGETS_REQUEST

def nodeLog(*args):
    print(*args)

def nodeError(*args):
    print("[ERROR]", *args)

def request(flow: http.HTTPFlow):
    url = flow.request.url
    method = flow.request.method
    content_type = flow.request.headers.get("content-type", "")
    raw_text = flow.request.get_text() or ""

    for action, pattern in TARGETS_REQUEST.items():
        if pattern.search(url):
            if method in ("POST", "PUT"):
                parsed_data = None
                try:
                    if "application/json" in content_type:
                        parsed_data = json.loads(raw_text)
                    elif "application/x-www-form-urlencoded" in content_type or "text/plain" in content_type:
                        parsed_qs = parse_qs(raw_text)
                        parsed_data = {k: v[0] if len(v) == 1 else v for k, v in parsed_qs.items()}
                    else:
                        nodeError(f"Unknown content type: {content_type}")
                except Exception as e:
                    nodeError(f"❌ 요청 바디 파싱 실패: {e}")
                    nodeLog(f"📤 요청 Body (Raw): {raw_text[:500]}")

                if parsed_data is not None:
                    save_request(action, url, parsed_data)
                    nodeLog(f"➡️ [{method}] {url}")
                    nodeLog(f"📤 요청 파싱 결과: {json.dumps(parsed_data, ensure_ascii=False, indent=2)}")
                    nodeLog(f"🔍 [{action}] 요청 감지됨")
            break

def response(flow: http.HTTPFlow):
    url = flow.request.url
    status = flow.response.status_code

    if status in (304, 204):
        nodeLog(f"ℹ️ [{status}] 캐시 응답 무시됨: {url}")
        return

    content_type = flow.response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return

    try:
        response_json = flow.response.json()
    except Exception as e:
        if "Could not load body" in str(e):
            nodeLog(f"⚠️ 응답 본문 없음 (무시됨): {url}")
            return
        else:
            nodeError(f"❌ 응답 파싱 실패: {e}")
            return

    for action, pattern in TARGETS_RESPONSE.items():
        if pattern.search(url):
            # delete_mobile 처리 조건 체크
            if action == "delete_mobile":
                destroy = response_json.get("entity", {}).get("destroy")
                if not (isinstance(destroy, list) and len(destroy) > 0):
                    return
            nodeLog(f"📦 [{action}] 응답 수신됨")
            nodeLog(f"📦 응답 JSON: {json.dumps(response_json, ensure_ascii=False, indent=2)}")

            asyncio.get_event_loop().create_task(match_and_dispatch(action, url, response_json))
            break
