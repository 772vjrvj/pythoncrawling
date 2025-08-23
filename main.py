import requests

API_URL = "http://localhost:8088/nhbank"
API_KEY = "changeme-please"

headers = {"X-API-Key": API_KEY}
#1755877318
#1755877483
#1755877693
ts = 1755877318  # 찾고 싶은 date 값 (unix timestamp, 초)

resp = requests.get(f"{API_URL}/transactions/by-timestamp",
                    params={"ts": ts}, headers=headers)

print(resp.status_code)
print(resp.json())
