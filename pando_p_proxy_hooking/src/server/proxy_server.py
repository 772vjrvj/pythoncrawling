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
from src.utils.logger import init_pando_logger, log_info, log_error

TARGETS_REQUEST = {
    "register": re.compile(r"/rest/ui/booking/register(\?timestamp=|$)"),
    "edit": re.compile(r"/rest/ui/booking/\d+/edit(\?timestamp=|$)"),
    "edit_move": re.compile(r"/rest/ui/booking/\d+/ajax-edit(\?timestamp=|$)"),
    "delete": re.compile(r"/rest/ui/booking/\d+/delete(\?timestamp=|$)"),
    "delete_mobile": re.compile(r"/rest/ui/polling/booking/\d+\?(?=.*\btimestamp=)(?=.*\bbookingStartDt=)(?=.*\bdata=)(?=.*\bbookingNumber=)"),
    "reseration": re.compile(r"/golfzone/agent/reseration\.json$"),
    "mobile_host": re.compile(r"/rest/ui/reservation/\d+\?(?=.*\btimestamp=)(?=.*\bdata=)")
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
        log_info("[proxy_server] 프록시 서버 시작")

        log_info("[proxy_server] 프록시 서버 로딩 완료 (한글 출력 테스트)")
        log_info("[proxy_server] 이 줄이 찍히면 최신 코드입니다!")

    def request(self, flow: http.HTTPFlow):
        url = flow.request.url
        method = flow.request.method
        content_type = flow.request.headers.get("content-type", "")

        log_info(f"[request] : {method} {url}")

        try:
            raw_text = flow.request.raw_content.decode('utf-8', errors='replace')
        except Exception as e:
            log_error(f"[request] : 본문 디코딩 실패: {e}")
            raw_text = "<디코딩 실패>"

        for action, pattern in TARGETS_REQUEST.items():
            if pattern.search(url):
                if method in ("POST", "PUT"):
                    log_info("[proxy_server] [request] : URL 매칭됨")
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
                        log_error(f"[proxy_server] [request] : 바디 파싱 실패: {e}")
                        log_info(f"[proxy_server] [request] : Body (Raw): {raw_text[:500]}")

                    if parsed_data is not None:
                        save_request(action, url, parsed_data)
                        log_info(f"[proxy_server] [request] : [{method}] {url}")
                        log_info("[proxy_server] [request] : 파싱 결과\n" + json.dumps(parsed_data, ensure_ascii=False, indent=2))
                        log_info(f"[proxy_server] [request] : [{action}] 요청 감지됨")
                break

    def response(self, flow: http.HTTPFlow):
        url = flow.request.url
        status = flow.response.status_code
        method = flow.request.method

        log_info(f"[response] : {method} : {url} → {status}")

        if status == 204:
            log_info("[response] : [204] 응답 무시됨: 본문 없음")
            return

        if not flow.response.content:
            log_info("[response] : 본문이 비어 있음 → 스킵")
            return

        # === 신규 === JSON 여부 판별(CT 또는 선두 바이트)
        content_type = flow.response.headers.get("content-type", "").lower()
        body = flow.response.content or b""
        is_json = ("application/json" in content_type) or (body.strip()[:1] in (b"{", b"["))

        response_json = {}
        # === 수정 === JSON일 때만 파싱 시도
        if is_json:
            try:
                response_json = flow.response.json()
            except Exception as e:
                log_error(f"[response] : JSON 파싱 실패: {e}")
                try:
                    raw_text = body.decode("utf-8", errors="replace")
                    log_info(f"[response] : 원본 응답 (일부):\n{raw_text[:300]}")
                except Exception as de:
                    log_error(f"[response] : 디코딩도 실패: {de}")
        else:
            # === 신규 === 비-JSON(이미지/바이너리/텍스트) 응답은 길이/CT만 기록하고 종료
            log_info(f"[response] : 비JSON 응답 → Content-Type={content_type or '-'}, size={len(body)} bytes")
            return

        for action, pattern in TARGETS_RESPONSE.items():
            if pattern.search(url):
                log_info("[proxy_server] [response] : URL 매칭됨")
                if action == "delete_mobile":
                    destroy = response_json.get("entity", {}).get("destroy")
                    if not (isinstance(destroy, list) and len(destroy) > 0):
                        return

                # ✅ reseration은 code 검사 생략
                if action != "reseration":
                    response_code = response_json.get("code")
                    if response_code == "FAIL":
                        log_info(f"[proxy_server] [response] : 처리 중단 응답 code가 FAIL → {url}")
                        return

                log_info(f"[proxy_server] [response] : [{action}] 수신됨")
                log_info("[proxy_server] [response] : JSON\n" + json.dumps(response_json, ensure_ascii=False, indent=2))

                match_and_dispatch(action, url, response_json)
                break

# mitmproxy가 인식할 수 있게 addons 등록
addons = [ProxyLogger()]
