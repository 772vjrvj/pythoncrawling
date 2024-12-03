import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone

def ydata_description(symbol):
    # 요청 URL, symbol에 따라 다르게 설정
    url = f"https://finance.yahoo.com/quote/{symbol}/profile/"

    # 요청 헤더
    headers = {
        "authority": "finance.yahoo.com",
        "method": "GET",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://finance.yahoo.com/",
        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    # 요청 보내기
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # 특정 data-url을 가진 <script> 태그 찾기
        script_tags = soup.find_all('script', {'type': 'application/json'})
        target_script = None
        for script in script_tags:
            if 'data-url' in script.attrs and 'quoteSummary' in script['data-url']:
                target_script = script
                break

        if target_script:
            try:
                # 첫 번째 파싱: 문자열로 된 JSON 데이터 파싱
                data_url_json = json.loads(target_script.string)

                # 두 번째 파싱: body 필드에 포함된 JSON 문자열을 다시 파싱
                body_json = json.loads(data_url_json['body'])

                # longBusinessSummary 추출
                long_business_summary = body_json['quoteSummary']['result'][0]['assetProfile']['longBusinessSummary']
                return long_business_summary
            except (KeyError, IndexError, json.JSONDecodeError):
                return "longBusinessSummary 정보를 찾을 수 없습니다."
        else:
            return "해당하는 스크립트를 찾을 수 없습니다."
    else:
        return f"요청 실패: 상태 코드 {response.status_code}"

def ydata_industry(symbol):
    # 요청 URL, symbol에 따라 다르게 설정
    url = f"https://finance.yahoo.com/quote/{symbol}/"

    # 요청 헤더 (쿠키 정보 제외)
    headers = {
        "authority": "finance.yahoo.com",
        "method": "GET",
        "path": f"/quote/{symbol}/",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    # 요청 보내기
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # class 이름 titleInfo yf-6e9c7m을 포함한 <span> 태그 찾기
        title_info = soup.find('span', class_='titleInfo yf-6e9c7m')

        if title_info:
            # 텍스트 가져오기 및 /로 분할하여 각 항목의 양쪽 공백 제거
            industries = [item.strip() for item in title_info.get_text().split('/')]
            return industries[0]
        else:
            return "industry 정보를 찾을 수 없습니다."
    else:
        return f"요청 실패: 상태 코드 {response.status_code}"

def ydata_sector(symbol):
    # 요청 URL, symbol에 따라 다르게 설정
    url = f"https://finance.yahoo.com/quote/{symbol}/"

    # 요청 헤더 (쿠키 정보 제외)
    headers = {
        "authority": "finance.yahoo.com",
        "method": "GET",
        "path": f"/quote/{symbol}/",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    # 요청 보내기
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # class 이름 titleInfo yf-6e9c7m을 포함한 <span> 태그 찾기
        title_info = soup.find('span', class_='titleInfo yf-6e9c7m')

        if title_info:
            # 텍스트 가져오기 및 /로 분할하여 각 항목의 양쪽 공백 제거
            industries = [item.strip() for item in title_info.get_text().split('/')]
            return industries[1]
        else:
            return "sector 정보를 찾을 수 없습니다."
    else:
        return f"요청 실패: 상태 코드 {response.status_code}"

def ydata_history(symbol, end_date_str):
    # 시작 타임스탬프는 2024-01-01
    period1 = 1704067200  # 2024-01-01 00:00:00

    # 문자열로 된 날짜를 datetime 객체로 변환하고 타임스탬프로 변환
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    # 23시 59분 59초로 설정
    end_date_with_time = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
    period2 = int(end_date_with_time.timestamp())  # end_date를 타임스탬프로 변환

    # 요청 URL 구성
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/AAPL?events=capitalGain%7Cdiv%7Csplit&formatted=true&includeAdjustedClose=true&interval=1d&period1={period1}&period2={period2}&symbol=AAPL&userYfid=true&lang=en-US%C2%AEion=US"

    # 요청 헤더 (쿠키 제외)
    headers = {
        "authority": "finance.yahoo.com",
        "method": "GET",
        "path": f"/quote/{symbol}/history/?period1={period1}&period2={period2}",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    # 요청 보내기
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            # JSON 데이터 파싱
            data = json.loads(response.text)

            # chart 데이터 추출
            chart_data = data['chart']['result'][0]
            timestamps = chart_data['timestamp']
            quotes = chart_data['indicators']['quote'][0]

            # 필요한 데이터 추출
            open_prices = quotes['open']
            high_prices = quotes['high']
            low_prices = quotes['low']
            close_prices = quotes['close']
            volumes = quotes['volume']

            # 결과를 저장할 리스트
            result = []

            for i in range(len(timestamps)):
                # timestamp를 날짜로 변환 (UTC 타임존 사용)
                date = datetime.fromtimestamp(timestamps[i], timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

                # 각 값들을 소수점 3자리로 반올림 및 3자리마다 콤마 추가, 데이터가 없으면 공백으로 처리
                open_price = f"{round(open_prices[i], 3):,}" if open_prices[i] is not None else ''
                high_price = f"{round(high_prices[i], 3):,}" if high_prices[i] is not None else ''
                low_price = f"{round(low_prices[i], 3):,}" if low_prices[i] is not None else ''
                close_price = f"{round(close_prices[i], 3):,}" if close_prices[i] is not None else ''
                volume = f"{volumes[i]:,}" if volumes[i] is not None else ''

                # 객체 생성 및 리스트에 추가
                result.append({
                    'date': date,
                    'Open': open_price,
                    'High': high_price,
                    'Low': low_price,
                    'Close': close_price,
                    'Volume': volume
                })

            return result

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            return f"데이터를 처리하는 중 오류 발생: {e}"
    else:
        return f"요청 실패: 상태 코드 {response.status_code}"

def main():
    symbol = "AAPL"  # 사용할 심볼
    description = ydata_description(symbol)
    industry = ydata_industry(symbol)
    sector = ydata_sector(symbol)
    end_date_str = "2024-10-12"  # 종료 날짜
    result_data = ydata_history(symbol, end_date_str)

    print(f"{symbol} description:\n{description}\n")
    print(f"{symbol} industry:\n{industry}\n")
    print(f"{symbol} sector:\n{sector}\n")
    print(f"{symbol} result_data:\n{result_data}\n")

if __name__ == "__main__":
    main()
