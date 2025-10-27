from mitmproxy import http
import requests

def response(flow: http.HTTPFlow):
    if "gpm.golfzonpark.com" in flow.request.pretty_url:
        try:
            data = {
                "url": flow.request.pretty_url,
                "method": flow.request.method,
                "request_headers": dict(flow.request.headers),
                "request_body": flow.request.get_text(),
            }

            # 응답이 존재할 경우에만 포함
            if flow.response:
                data["response_code"] = flow.response.status_code
                data["response_body"] = flow.response.get_text()

            print(f"[📦 감지됨] {data['method']} - {data['url']}")

            # 판도 서버 전송
            # requests.post("https://YOUR_PANDO_API_URL", json=data)

        except Exception as e:
            print("[❌ 전송 실패]", e)
