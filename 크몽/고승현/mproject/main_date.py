import requests
import pandas as pd
from datetime import datetime, timedelta

# API 요청을 수행하고 데이터를 수집하는 함수
def fetch_data(date_str):
    url = "http://3.36.226.118:8081/api/shop/selectManageMst"

    payload = {
        "DAY_NIGHT_GUBUN": "",
        "DT": date_str,
        "PARAM": "",
        "USER_SEQ": "",
        "current": 1,
        "layout": "inline",
        "pageSize": 1000,
        "total": 0
    }

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "content-type": "application/json;charset=UTF-8",
        "origin": "http://3.36.226.118:3400",
        "referer": "http://3.36.226.118:3400/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "x-auth-token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJVU1IwMDAwMDAwMDEiLCJyb2xlcyI6WyJST0xFX0FETUlOIl0sImlhdCI6MTcyNDc2ODAyNywiZXhwIjoxNzI3MzYwMDI3fQ.BW6IXYLVQEiULXwQYMICmaAWsoOFH446mMcdCoiKBDA"
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get('data', {}).get('list', [])
    else:
        print(f"Error fetching data for {date_str}: {response.status_code}")
        return []



# 날짜 범위를 설정하여 데이터 수집
def collect_data(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    all_data = []

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"Fetching data for {date_str}")
        daily_data = fetch_data(date_str)
        if daily_data:
            all_data.extend(daily_data)
        current_date += timedelta(days=1)

    return all_data


# 수집한 데이터를 엑셀로 저장
def save_to_excel(data):
    df = pd.DataFrame(data)
    df.to_excel("collected_data.xlsx", index=False)
    print("Data saved to collected_data.xlsx")


if __name__ == "__main__":
    # 시작일과 종료일을 설정
    start_date = "2022-04-01"
    end_date = datetime.now().strftime("%Y-%m-%d")  # 오늘 날짜

    # 데이터 수집
    collected_data = collect_data(start_date, end_date)

    # 데이터 엑셀 파일로 저장
    save_to_excel(collected_data)