import requests
import pandas as pd
from datetime import datetime, timedelta

# 월별 데이터를 요청하는 함수
def fetch_monthly_data(date_str):
    url = "http://3.36.226.118:8081/api/shop/selectManageMstMonthlyTotal"

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
        "x-auth-token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJVU1IwMDAwMDAwMDEiLCJyb2xlcyI6WyJST0xFX0FETUlOIl0sImlhdCI6MTcyNDc3MTIwNiwiZXhwIjoxNzI3MzYzMjA2fQ.rekxRSL6A3q5j70rgbCPGAt_u8TkmLlIgnjt-HVk1Aw"
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get('data', {})
    else:
        print(f"Error fetching monthly data for {date_str}: {response.status_code}")
        return None

# 월별 데이터를 처리하고 업장명을 추가하여 하나로 합치는 함수
def process_monthly_data(start_date_str, end_date_str):
    # 날짜를 datetime 형식으로 변환
    start_date = datetime.strptime(start_date_str, "%Y-%m")
    end_date = datetime.strptime(end_date_str, "%Y-%m")

    all_data = []

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m")
        print(f"Fetching data for {date_str}")

        # fetch_monthly_data 함수 호출
        data = fetch_monthly_data(date_str)

        if not data:
            print(f"No data for {date_str}")
        else:
            header = data.get('header', [])
            list_of_shops = data.get('list', [])

            for idx, shop_data in enumerate(list_of_shops):
                shop_name = header[idx] if idx < len(header) else f"Shop_{idx + 1}"
                for day_data in shop_data:
                    if day_data['DT'] is not None:  # 유효한 데이터만 처리
                        day_data['SHOP_NAME'] = shop_name
                        day_data['DATE'] = date_str  # 날짜 컬럼 추가
                        print(f"day_data : {day_data}")
                        all_data.append(day_data)

        # 다음 달로 이동
        current_date += timedelta(days=31)
        current_date = current_date.replace(day=1)  # 달의 첫째 날로 이동

    return pd.DataFrame(all_data)



# 수집한 데이터를 엑셀로 저장
def save_to_excel(data, file_name="monthly_data.xlsx"):
    df = pd.DataFrame(data)
    if not df.empty:
        df.to_excel(file_name, index=False)
        print(f"Data saved to {file_name}")
    else:
        print("No data to save.")

if __name__ == "__main__":
    # 시작일과 종료일 설정 (예: 2022년 4월부터 2024년 8월까지)
    start_date = "2022-04"
    end_date = "2024-08"

    # 데이터를 처리하여 하나로 합치기
    combined_data = process_monthly_data(start_date, end_date)

    # 데이터 엑셀 파일로 저장
    save_to_excel(combined_data, file_name="monthly_data.xlsx")
