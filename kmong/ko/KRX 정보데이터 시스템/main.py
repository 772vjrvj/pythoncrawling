import requests
import pandas as pd
import time
import random
from datetime import datetime, timedelta

def get_json_data(trdDd):
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    payload = {
        'bld': 'dbms/MDC/STAT/standard/MDCSTAT03501',
        'locale': 'ko_KR',
        'searchType': '1',
        'mktId': 'ALL',
        'trdDd': trdDd,
        'tboxisuCd_finder_stkisu0_0': '005930/삼성전자',
        'isuCd': 'KR7005930003',
        'isuCd2': 'KR7005930003',
        'codeNmisuCd_finder_stkisu0_0': '삼성전자',
        'param1isuCd_finder_stkisu0_0': 'ALL',
        'strtDd': '20240705',
        'endDd': '20240712',
        'csvxls_isNo': 'false'
    }

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Content-Length': '350',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': '__smVisitorID=sah-sXbnhsL; JSESSIONID=5uBoPj40hI3aD4FP1FYdD0vS7lCI23vGqL6laIZpqjZuPe0Qz7QKiKyQXOQAhqmC.bWRjX2RvbWFpbi9tZGNvd2FwMS1tZGNhcHAxMQ==',
        'Host': 'data.krx.co.kr',
        'Origin': 'http://data.krx.co.kr',
        'Referer': 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020502',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    response = requests.post(url, data=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def map_data(data_list, trdDd):
    # 모든 종목의 TDD_CLSPRC 값을 확인하여 휴장 여부 판단
    all_empty = all(data['TDD_CLSPRC'] == '-' for data in data_list)
    if all_empty:
        return []  # 모든 종목의 종가가 없으면 빈 리스트 반환

    mapped_list = []
    for data in data_list:
        if data['TDD_CLSPRC'] == '-':
            continue
        mapped_data = {
            '종목코드': data['ISU_SRT_CD'],
            '종목명': data['ISU_ABBRV'],
            '종가': data['TDD_CLSPRC'],
            '대비': data['CMPPREVDD_PRC'],
            '등락률': data['FLUC_RT'],
            'EPS': data['EPS'],
            'PER': data['PER'],
            '선행 EPS': data['FWD_EPS'],
            '선행 PER': data['FWD_PER'],
            'BPS': data['BPS'],
            'PBR': data['PBR'],
            '주당배당금': data['DPS'],
            '배당수익률': data['DVD_YLD'],
            '날짜': trdDd
        }
        mapped_list.append(mapped_data)
    return mapped_list


def save_to_excel(mapped_list, filename='output.xlsx'):
    df = pd.DataFrame(mapped_list)
    df.to_excel(filename, index=False)

def main():
    # start_date = datetime(2004, 1, 1)
    # end_date = datetime(2024, 6, 30)
    start_date = datetime(2024, 6, 26)
    end_date = datetime(2024, 6, 30)
    delta = timedelta(days=1)

    all_data = []

    current_date = start_date
    while current_date <= end_date:
        trdDd = current_date.strftime('%Y%m%d')
        try:
            json_response = get_json_data(trdDd)
            if 'output' in json_response:
                mapped_list = map_data(json_response['output'], trdDd)
                if mapped_list:  # If the mapped_list is not empty
                    all_data.extend(mapped_list)
                else:
                    print(f"No valid data for {trdDd}, skipping")
            else:
                print(f"No output data for {trdDd}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred for {trdDd}: {e}")

        time.sleep(random.uniform(2, 5))
        current_date += delta

    file_count = 0
    for i in range(0, len(all_data), 850000):
        chunk = all_data[i:i + 850000]
        filename = f'output_{file_count}.xlsx'
        save_to_excel(chunk, filename)
        file_count += 1
        print(f"Data successfully saved to {filename}")

if __name__ == "__main__":
    main()
