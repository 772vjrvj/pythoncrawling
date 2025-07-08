# src/server/proxy_server.py
import sys
import os
import re
import io
import json
from urllib.parse import parse_qs
from mitmproxy import http

# 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.router.hook_router import save_request, match_and_dispatch
from src.utils.logger import init_pando_logger, log_info, log_error  # ✅ 로거 가져오기

TARGETS_REQUEST = {
    "register": re.compile(r"/rest/ui/booking/register(\?timestamp=|$)"),
    "edit": re.compile(r"/rest/ui/booking/\d+/edit(\?timestamp=|$)"),
    "edit_move": re.compile(r"/rest/ui/booking/\d+/ajax-edit(\?timestamp=|$)"),
    "delete": re.compile(r"/rest/ui/booking/\d+/delete(\?timestamp=|$)"),
    "delete_mobile": re.compile(r"/rest/ui/polling/booking/\d+\?(?=.*\btimestamp=)(?=.*\bbookingStartDt=)(?=.*\bdata=)(?=.*\bbookingNumber=)"),
}
TARGETS_RESPONSE = TARGETS_REQUEST

class ProxyLogger:
    def __init__(self):
        # 한글 깨짐 방지
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace')

        # 로그 디렉토리 초기화
        init_pando_logger()
        log_info("[판도] 프록시 서버 시작")

        log_info("[판도] 프록시 서버 로딩 완료 (한글 출력 테스트)")
        log_info("[판도] 이 줄이 찍히면 최신 코드입니다!")

    def request(self, flow: http.HTTPFlow):
        url = flow.request.url
        method = flow.request.method
        content_type = flow.request.headers.get("content-type", "")

        log_info(f"[판도] [request] : {method} {url}")

        try:
            raw_text = flow.request.raw_content.decode('utf-8', errors='replace')
        except Exception as e:
            log_error(f"[판도] [request] : 본문 디코딩 실패: {e}")
            raw_text = "<디코딩 실패>"

        for action, pattern in TARGETS_REQUEST.items():
            if pattern.search(url):
                if method in ("POST", "PUT"):
                    log_info("[판도] [request] : URL 매칭됨")
                    parsed_data = None
                    try:
                        if "application/json" in content_type:
                            parsed_data = json.loads(raw_text)
                        elif "application/x-www-form-urlencoded" in content_type or "text/plain" in content_type:
                            parsed_qs = parse_qs(raw_text)
                            parsed_data = {k: v[0] if len(v) == 1 else v for k, v in parsed_qs.items()}
                        else:
                            log_info(f"⚠️ Unknown content type: {content_type}")
                    except Exception as e:
                        log_error(f"[판도] [request] : 바디 파싱 실패: {e}")
                        log_info(f"[판도] [request] : Body (Raw): {raw_text[:500]}")

                    if parsed_data is not None:
                        save_request(action, url, parsed_data)
                        log_info(f"[판도] [request] : [{method}] {url}")
                        log_info("[판도] [request] : 파싱 결과\n" + json.dumps(parsed_data, ensure_ascii=False, indent=2))
                        log_info(f"[판도] [request] : [{action}] 요청 감지됨")
                break

    def response(self, flow: http.HTTPFlow):
        url = flow.request.url
        status = flow.response.status_code

        log_info(f"[판도] [response] : {flow.request.method} {url} → {status}")

        if status == 204:
            log_info("[판도] [response] : [204] 응답 무시됨: 본문 없음")
            return

        if not flow.response.content:
            log_info("[판도] [response] : 본문이 비어 있음 → 스킵")
            return

        try:
            response_json = flow.response.json()
        except Exception as e:
            if "Could not load body" in str(e):
                log_info(f"[판도] [response] : 응답 본문 없음 (무시됨): {url}")
                return
            else:
                log_error(f"[판도] [response] : 실패: {e}")
                return

        for action, pattern in TARGETS_RESPONSE.items():
            if pattern.search(url):
                log_info("[판도] [response] : URL 매칭됨")
                if action == "delete_mobile":
                    destroy = response_json.get("entity", {}).get("destroy")
                    if not (isinstance(destroy, list) and len(destroy) > 0):
                        return

                response_code = response_json.get("code")
                if response_code == "FAIL":
                    log_info(f"[판도] [response] : 처리 중단 응답 code가 FAIL → {url}")
                    return

                log_info(f"[판도] [response] : [{action}] 수신됨")
                log_info("[판도] [response] : JSON\n" + json.dumps(response_json, ensure_ascii=False, indent=2))

                match_and_dispatch(action, url, response_json)
                break

# mitmproxy가 인식할 수 있게 addons 등록
addons = [ProxyLogger()]
