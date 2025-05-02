from mitmproxy import http
from urllib.parse import unquote

def request(flow: http.HTTPFlow):
    if '/rest/ui/booking/' in flow.request.url:
        print("\n[📡 요청 감지]")
        print(f"▶ URL: {flow.request.url}")
        print(f"▶ Method: {flow.request.method}")

        # 요청 Body URL 디코딩
        body = flow.request.get_text()
        decoded_body = unquote(body)

        print(f"▶ Body: {decoded_body}")

def response(flow: http.HTTPFlow):
    if '/rest/ui/booking/' in flow.request.url:
        print("\n[📦 응답 감지]")
        print(f"▶ URL: {flow.request.url}")
        print(f"▶ 상태 코드: {flow.response.status_code}")

        # 응답 Body URL 디코딩
        body = flow.response.get_text()
        decoded_body = unquote(body)

        print(f"▶ Body: {decoded_body[:500]}")
