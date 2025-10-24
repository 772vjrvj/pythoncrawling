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

# 전역 검색어 저장용 (이전 호환용)
latest_query_text = None


class ProxyLogger:
    def __init__(self):
        # === 신규: 한글 깨짐 방지(배포/개발 공통) ===
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            try:
                sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8", errors="replace")
                sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8", errors="replace")
            except Exception:
                pass

        # === 신규: 로거 초기화 & 부팅 로그 ===
        try:
            init_pando_logger()
        except Exception as e:
            print("[proxy_server] logger init failed:", str(e))

        log_info("🚀 [proxy_server] 프록시 서버 로딩 완료 (한글 출력 테스트)")
        log_info("✅ [proxy_server] 이 줄이 찍히면 최신 로깅 통합 버전입니다.")

    def request(self, flow: http.HTTPFlow):
        """
        단순화:
        - 대상: https://www.kipris.or.kr/kpat/dynaPath
        - 로그: URL, 메서드(POST 여부), 헤더, POST 페이로드(가능 시 파싱+원문 일부)
        """
        try:
            url = flow.request.pretty_url
            host = flow.request.pretty_host or ""
            method = flow.request.method.upper()
        except Exception as e:
            log_error(f"[request] : 요청 정보 취득 실패: {str(e)}")
            return

        if "kipris.or.kr" in host and "/kpat/dynaPath" in url:
            # === 신규: URL + 메서드 ===
            log_info(f"[request] : dynaPath 요청 → {method} {url}")

            # === 신규: 헤더 덤프 ===
            try:
                # mitmproxy Headers 객체를 dict 유사 형태로 보기 쉽게 변환
                headers_dump = {k: v for k, v in flow.request.headers.items()}
                log_info(f"[request] headers: {headers_dump}")
            except Exception as e:
                log_error(f"[request] : 헤더 덤프 실패: {str(e)}")

            # === 신규: POST 페이로드 (가능 시) ===
            if method == "POST":
                content_type = (flow.request.headers.get("content-type", "") or "").lower()
                try:
                    raw_text = flow.request.get_text() or ""
                except Exception as e:
                    log_error(f"[request] : POST 본문 디코딩 실패: {str(e)}")
                    raw_text = ""

                # x-www-form-urlencoded면 파싱, 그 외에는 원문 일부
                if "application/x-www-form-urlencoded" in content_type:
                    try:
                        parsed = parse_qs(raw_text)
                        # 값이 ['a'] 형태라 첫 값만 보기 좋게 변환
                        parsed_simple = {k: (v[0] if isinstance(v, list) and v else v) for k, v in parsed.items()}
                        log_info(f"[request] POST form: {parsed_simple}")
                    except Exception as e:
                        log_error(f"[request] : POST form 파싱 실패: {str(e)}")
                        if raw_text:
                            log_info(f"[request] POST raw(0..800): {raw_text[:800]}")
                else:
                    if raw_text:
                        log_info(f"[request] POST raw(0..800): {raw_text[:800]}")

        # 그 외 요청은 무시 (심플 처리)
        return

    def response(self, flow: http.HTTPFlow):
        """
        단순화:
        - 대상: https://www.kipris.or.kr/kpat/dynaPath
        - JSON 응답만 처리하여 data_list.json에 누적 저장
          키 형식: {연속번호}_{applno}  (처음이면 0_...부터 시작)
        """
        try:
            url = flow.request.pretty_url
            host = flow.request.pretty_host or ""
            status = getattr(flow.response, "status_code", None)
        except Exception as e:
            log_error(f"[response] : 응답/요청 정보 취득 실패: {str(e)}")
            return

        if not ("kipris.or.kr" in host and "/kpat/dynaPath" in url):
            return

        log_info(f"[response] : dynaPath 응답 탐지 → {url} (status={status})")

        # === JSON 여부 확인 ===
        try:
            content_type = (flow.response.headers.get("content-type", "") or "").lower()
        except Exception:
            content_type = ""
        body_bytes = flow.response.content or b""
        body_head = body_bytes.strip()[:1] if body_bytes else b""
        is_json = ("application/json" in content_type) or (body_head in (b"{", b"["))

        if not is_json:
            log_info(f"[response] : dynaPath 응답 (비JSON) → Content-Type={content_type or '-'}, size={len(body_bytes)} bytes")
            return

        # === JSON 파싱 ===
        data = None
        try:
            data = flow.response.json()
        except Exception:
            try:
                text = body_bytes.decode("utf-8", errors="replace")
                data = json.loads(text)
            except Exception as e:
                log_error(f"[response] : dynaPath JSON 파싱 실패: {str(e)}")
                try:
                    raw_text = body_bytes.decode("utf-8", errors="replace")
                    log_info(f"[response] : 원본 응답 (일부)\n{raw_text[:800]}")
                except Exception as de:
                    log_error(f"[response] : 원본 디코딩도 실패: {str(de)}")
                return

        # === 신규: 저장 대상 레코드 배열 만들기 ===
        # 1) resultList가 있으면 그걸로, 2) 리스트면 그대로, 3) 단일 dict면 리스트로 래핑
        if isinstance(data, dict) and isinstance(data.get("resultList"), list):
            records = data.get("resultList")
        elif isinstance(data, list):
            records = data
        else:
            records = [data]

        if not records:
            log_info("[response] : dynaPath JSON 내 저장할 레코드 없음 → 스킵")
            return

        # === 신규: 기존 파일 로드 ===
        file_path = "data_list.json"
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if not isinstance(existing, dict):
                    log_error("[response] : data_list.json이 dict 형식이 아님 → 새로 생성")
                    existing = {}
            except Exception as e:
                log_error(f"[response] : data_list.json 로드 실패(새로 생성): {str(e)}")
                existing = {}
        else:
            existing = {}

        # === 신규: 시작 인덱스 계산 (기존 키 수 기준) ===
        # 키 형식이 "{n}_{applno}"이므로, 단순히 현재 엔트리 수로 다음 인덱스 시작
        start_idx = len(existing)

        # === 신규: 저장 루프 ===
        saved = 0
        idx = start_idx
        for rec in records:
            if not isinstance(rec, dict):
                # dict가 아닌 항목은 스킵
                continue
            applno = rec.get("applno")
            if applno is None:
                # applno가 없으면 대체 키
                key = f"{idx}_NO_APPLNO"
            else:
                key = f"{idx}_{applno}"

            # 덮어쓰기 허용(동일 key 재생성 가능성 낮음) — 필요 시 존재 검사하여 idx++로 회피 가능
            existing[key] = rec
            saved += 1
            idx += 1

        # === 신규: 파일 저장 ===
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
            log_info(f"[response] : data_list.json 저장 완료 ({saved}건 반영, 총 {len(existing)}건) → {os.path.abspath(file_path)}")
        except Exception as e:
            log_error(f"[response] : data_list.json 저장 실패: {str(e)}")


# mitmproxy가 인식할 수 있게 addons 등록
addons = [ProxyLogger()]
