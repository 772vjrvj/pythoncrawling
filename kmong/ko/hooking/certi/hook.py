from mitmproxy import http
from urllib.parse import unquote

def request(flow: http.HTTPFlow):
    if '/rest/ui/booking/' in flow.request.url:
        print("\n[📡 요청 감지]")
        print(f"▶ URL: {flow.request.url}")
        print(f"▶ Method: {flow.request.method}")
        print("▶ Body:", unquote(flow.request.get_text()))

def response(flow: http.HTTPFlow):
    if '/rest/ui/booking/' in flow.request.url:
        print("\n[📦 응답 감지]")
        print(f"▶ URL: {flow.request.url}")
        print(f"▶ 상태 코드: {flow.response.status_code}")
        print("▶ Body:", unquote(flow.response.get_text())[:500])
