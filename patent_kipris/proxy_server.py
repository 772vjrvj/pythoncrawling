import sys
import os
import io
import json
from datetime import datetime
from urllib.parse import parse_qs
from mitmproxy import http
from mitmproxy import ctx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 전역 검색어 저장용
latest_query_text = None


class ProxyLogger:
    def __init__(self):
        global latest_query_text
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except AttributeError:
            sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace')

        ctx.log.info("🚀 프록시 서버 로딩 완료")

    def request(self, flow: http.HTTPFlow):
        global latest_query_text

        if "kipris.or.kr" in flow.request.pretty_host and "kpat/resulta.do" in flow.request.pretty_url:
            payload = flow.request.get_text()
            parsed = parse_qs(payload)
            query_text = parsed.get("queryText", [""])[0]
            if query_text:
                latest_query_text = query_text
                ctx.log.info(f"📨 요청 Payload에서 추출된 queryText: {query_text}")

    def response(self, flow: http.HTTPFlow):
        global latest_query_text

        if "kipris.or.kr" in flow.request.pretty_host and "kpat/resulta.do" in flow.request.pretty_url:
            try:
                data = json.loads(flow.response.get_text())
                result = data.get("resultList", [])[0] if data.get("resultList") else {}
                ctx.log.info("📄 최종 응답 전문 (첫 건):")
                ctx.log.info(json.dumps(result, indent=2, ensure_ascii=False))

                if latest_query_text:
                    file_path = "test.json"
                    if os.path.exists(file_path):
                        with open(file_path, "r", encoding="utf-8") as f:
                            existing = json.load(f)
                    else:
                        existing = {}

                    existing[latest_query_text] = result

                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(existing, f, indent=2, ensure_ascii=False)

                    ctx.log.info(f"✅ test.json 파일에 '{latest_query_text}' 항목 저장 완료")

            except Exception as e:
                ctx.log.warn(f"⚠️ 응답 처리 실패: {str(e)}")


addons = [ProxyLogger()]
