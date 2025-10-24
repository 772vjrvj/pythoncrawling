# src/server/proxy_server.py
import sys
import os
import io
import json
from urllib.parse import parse_qs
from mitmproxy import http

# === 신규: 로거 연동 ===
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.utils.logger import init_pando_logger, log_info, log_error  # noqa: E402

# 전역 검색어 저장용 (최근 queryText)
latest_query_text = None


# kipris 사용중
class ProxyLogger:
    def __init__(self):
        # === 신규: 한글 깨짐 방지(배포/개발 공통) ===
        try:
            # Python 3.7+ 전용
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            # 하위 호환 (detach → 래핑)
            try:
                sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8", errors="replace")
                sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8", errors="replace")
            except Exception:
                pass

        # === 신규: 로거 초기화 & 부팅 로그 ===
        try:
            init_pando_logger()
        except Exception as e:
            # 로거 초기화 자체가 실패해도 프록시는 계속 올라가야 함
            print("[proxy_server] logger init failed:", str(e))

        log_info("🚀 [proxy_server] 프록시 서버 로딩 완료 (한글 출력 테스트)")
        log_info("✅ [proxy_server] 이 줄이 찍히면 최신 로깅 통합 버전입니다.")

    def request(self, flow: http.HTTPFlow):
        """
        kipris 검색 요청에서 payload의 queryText 파라미터를 추출
        """
        global latest_query_text

        url = flow.request.pretty_url
        host = flow.request.pretty_host
        method = flow.request.method.upper()
        content_type = flow.request.headers.get("content-type", "")

        log_info(f"[request] : {method} {url}")
        log_info(f"[request] flow.request.headers : {flow.request.headers}")

        # KIPRIS 검색 요청 필터
        if "kipris.or.kr" in host and "kpat/resulta.do" in url:
            try:
                raw_text = flow.request.get_text() or ""
            except Exception as e:
                log_error(f"[request] : 본문 디코딩 실패: {str(e)}")
                raw_text = ""

            # 폼 전송일 가능성이 높으므로 parse_qs 사용
            try:
                parsed = parse_qs(raw_text)
                query_text = parsed.get("queryText", [""])[0]
                if query_text:
                    latest_query_text = query_text
                    log_info(f"[proxy_server] [request] queryText 추출: {query_text}")
                else:
                    log_info("[proxy_server] [request] queryText 미존재")
            except Exception as e:
                log_error(f"[proxy_server] [request] : queryText 파싱 실패: {str(e)}")
                # 원문 일부 로그
                if raw_text:
                    log_info(f"[proxy_server] [request] : Body (Raw, 0..300)\n{raw_text[:300]}")

    def response(self, flow: http.HTTPFlow):
        """
        kipris 검색 응답(JSON)을 파싱하여 resultList를 data.json에 누적 저장
        """
        url = flow.request.pretty_url
        host = flow.request.pretty_host
        method = flow.request.method.upper()
        status = flow.response.status_code

        log_info(f"[response] : {method} : {url} → {status}")
        # 원문 일부 로그 (가독성 위해 800자 제한)
        data = flow.response.json()
        log_info(f"[response] : data={data}")

        # 본문 없음
        if status == 204 or not flow.response.content:
            log_info("[response] : 본문 없음 또는 204 → 스킵")
            return

        # KIPRIS 검색 응답 필터
        if not ("kipris.or.kr" in host and "kpat/resulta.do" in url):
            return

        # === 신규: JSON 여부 판별(CT 또는 선두 바이트) ===
        try:
            content_type = (flow.response.headers.get("content-type", "") or "").lower()
        except Exception:
            content_type = ""

        body_bytes = flow.response.content or b""
        body_head = body_bytes.strip()[:1]
        is_json = ("application/json" in content_type) or (body_head in (b"{", b"["))

        if not is_json:
            log_info(f"[response] : 비JSON 응답 → Content-Type={content_type or '-'}, size={len(body_bytes)} bytes")
            return

        # === JSON 파싱 시도 ===
        data = None
        try:
            # mitmproxy의 json 파서 (CT/인코딩 고려)
            data = flow.response.json()
            log_info(f"[response] : data={data}")
        except Exception:
            # 실패 시 수동 디코딩 후 파싱 재시도
            try:
                text = body_bytes.decode("utf-8", errors="replace")
                data = json.loads(text)
            except Exception as e:
                log_error(f"[response] : JSON 파싱 실패: {str(e)}")
                try:
                    # 원문 일부 로그 (가독성 위해 800자 제한)
                    raw_text = body_bytes.decode("utf-8", errors="replace")
                    log_info(f"[response] : 원본 응답 (일부)\n{raw_text}")
                except Exception as de:
                    log_error(f"[response] : 디코딩도 실패: {str(de)}")
                return

        # === 데이터 검증 및 처리 ===
        try:
            result_list = data.get("resultList", [])
            if not isinstance(result_list, list) or not result_list:
                log_info("[proxy_server] [response] resultList가 비어 있거나 형식이 올바르지 않습니다.")
                return

            log_info(f"[proxy_server] [response] 최종 응답 파싱: {len(result_list)}건")

            # 기존 data.json 읽기
            file_path = "data_list.json"  # 필요 시 절대경로로 교체 가능
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                except Exception as e:
                    log_error(f"[proxy_server] [response] : data.json 로드 실패(덮어쓰기 예정): {str(e)}")
                    existing = {}
            else:
                existing = {}

            # 여러 건을 AN_인덱스 키로 저장 (중복 방지/추적 용이)
            saved = 0
            for i, result in enumerate(result_list, start=1):
                try:
                    an = result.get("AN") or f"NO_AN_{i}"
                    key = f"{an}_{i}"
                    existing[key] = result
                    saved += 1
                except Exception as e:
                    log_error(f"[proxy_server] [response] : 항목 저장 준비 실패: {str(e)}")

            # 파일로 저장
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(existing, f, indent=2, ensure_ascii=False)
                log_info(f"[proxy_server] [response] data.json 저장 완료 ({saved}건 반영) → {os.path.abspath(file_path)}")
            except Exception as e:
                log_error(f"[proxy_server] [response] : data.json 저장 실패: {str(e)}")

        except Exception as e:
            log_error(f"[proxy_server] [response] : 처리 단계 실패: {str(e)}")


# mitmproxy가 인식할 수 있게 addons 등록
addons = [ProxyLogger()]
