import base64
import json
from datetime import datetime, timedelta

# JWT 토큰
jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpbklkIjoiNzcydmpydmo6bmF2ZXIiLCJyb2xlIjowLCJjbGllbnRJZCI6Im5hdmVyLWNvb2tpZSIsImlzQXBpIjpmYWxzZSwidXNlcklkIjozNTAzNTM3LCJ1c2VyS2V5IjoiMTE1ZTIwOTItNjMyYS00NjEwLWJmODktMmQ2M2ViOTBmNzhmIiwiY2xpZW50Q3VzdG9tZXJJZCI6MzIxNjY2MSwiaXNzdWVUeXBlIjoidXNlciIsIm5iZiI6MTczMjM4MDk3OSwiaWRwIjoidXNlci1leHQtYXV0aCIsImN1c3RvbWVySWQiOjMyMTY2NjEsImV4cCI6MTczMjM4MTYzOSwiaWF0IjoxNzMyMzgxMDM5LCJqdGkiOiI1MjRkMjQwYS1mOGFiLTQzZDAtYjdkYi0wYzVlM2Y3MDdjM2MifQ.-WLb6WkZHjpmX6VUMmUWv8JSpsy5UqsbVglYLkI0FSY"

# JWT Payload 디코딩
def decode_jwt_payload(token):
    payload = token.split(".")[1]
    # Base64 디코딩 (패딩 문제 해결 포함)
    padded_payload = payload + "=" * (-len(payload) % 4)
    decoded_bytes = base64.urlsafe_b64decode(padded_payload)
    decoded_payload = json.loads(decoded_bytes)
    return decoded_payload

# JWT Payload에서 exp 확인
payload = decode_jwt_payload(jwt_token)
if "exp" in payload:
    exp_timestamp = payload["exp"]
    exp_datetime = datetime.utcfromtimestamp(exp_timestamp)  # UTC 시간
    print(f"만료 시간 (UTC): {exp_datetime}")

    # 한국 시간(KST, UTC+9)으로 변환
    kst_datetime = exp_datetime + timedelta(hours=9)
    print(f"만료 시간 (KST): {kst_datetime}")
else:
    print("JWT 토큰에 만료 시간(exp)이 포함되어 있지 않습니다.")