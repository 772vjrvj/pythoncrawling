import requests
import time
import re

# 요청 헤더 설정
headers = {
    "authority": "api.kream.co.kr",
    "method": "GET",
    "scheme": "https",
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "origin": "https://kream.co.kr",
    "referer": "https://kream.co.kr/my/selling?tab=finished",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "authorization": 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6dHJ1ZSwiaWF0IjoxNzQwNDA3MTYyLCJqdGkiOiJkYThlNWU3ZS1lOTJjLTQ4ZDQtODY3My1mODUwOGU2ZGU3MzAiLCJ0eXBlIjoiYWNjZXNzIiwiaWRlbnRpdHkiOjYyNDA2NzUsIm5iZiI6MTc0MDQwNzE2MiwiY3NyZiI6ImQ1Y2Q0YjNjLWNkZTItNDFkNy1hNDNlLWI3NjFjYjBmZDdjZCIsImV4cCI6MTc0MDQxNDM2MiwidWMiOnsic2FmZSI6dHJ1ZX0sInVkIjoiLmVKeEZqa3RMdzBBVWhmX0taVll0ZENienpNMWpKUzRVYXQwWTZESk1NcmM2TkcxQ0dxMFBfTzhtS01qWmZlY2N6dmxpWVdJRjAxSTdMalhYdGxLMjBHa2h0VURVdWN2WWhnVjZpeTNWMDhkQWNfUkt6VC1MNFplVWlHZ2IxMXFPVGhLM2hNaWJfT0I1RnRBb2JVMnVVTTYxa1U3OVJMVVBZVnhXVlNhVVJhR01GdHFrc185Nm9iSDJ6M1JlVHUzNno5aDFQbkZDd21vZno2R19YdUN4QWlXRkxHRUdxUzNoUGJWcnVCbUdqdmJVYk9PVU9JUENwTERhM2xlN2h3MTA4VWh3Ui0yeFg4UHR5OWlmS0ZIR0NMa0ludnpCal9HdndyNV9BTmFqU3BnLlNtMjFfNEl0am5Jc0kwNDBEaEVMMnhBb1lQayJ9.MGHRDNsh0b-U7_Lh23tnYPUWT8TzuvITBKOf-Sljp7c',
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "x-kream-api-version": "41",
    "x-kream-client-datetime": "20250223183955+0900",
    "x-kream-device-id": "web;fcb9350d-91d8-4a78-945d-e941984c6386",
    "x-kream-web-build-version": "6.7.4",
    "x-kream-web-request-secret": "kream-djscjsghdkd"
}

# URL 패턴 정규표현식 (숫자만 추출)
url_pattern = re.compile(r"https://kream\.co\.kr/my/selling/(\d+)")
extracted_ids = []

def fetch_data(cursor):
    # status=expired
    # status=canceled
    tab="finished"
    status="canceled"
    request_key="a513410c-91b9-484c-8275-97e99a9eb2d2"


    url = f"https://api.kream.co.kr/api/o/asks/?cursor={cursor}&tab={tab}&status={status}&request_key={request_key}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            for item in data["items"]:
                if item.get("actions", []):
                    for action in item.get("actions", []):
                        if "value" in action and "https://kream.co.kr/my/selling/" in action["value"]:
                            match = url_pattern.search(action["value"])
                            if match:
                                print(match.group(1))
                                extracted_ids.append(match.group(1))  # 숫자 부분만 저장
            print(f"Cursor {cursor}: {extracted_ids}")
    else:
        print(f"Cursor {cursor}: 요청 실패 (HTTP {response.status_code})")

def main():
    for cursor in range(1, 30):  # 1부터 52까지 반복
        fetch_data(cursor)
        time.sleep(1)  # 1초 대기
    print(extracted_ids)

if __name__ == "__main__":
    main()
