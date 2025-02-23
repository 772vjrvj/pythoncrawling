import time

import requests
import json
import pandas as pd
from datetime import datetime, timedelta

# 헤더 반환 함수
def get_headers():
    return {
        "authority": "api.kream.co.kr",
        "method": "GET",
        "path": "/api/m/asks/74024436?request_key=458d341e-e092-45d5-a60c-7768069b3516",
        "scheme": "https",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6dHJ1ZSwiaWF0IjoxNzQwMzE1ODY3LCJqdGkiOiI5ZWVlMDRmMS1jODNmLTQyZjUtOWQ0OS1hN2IzNzU0N2ZlMDUiLCJ0eXBlIjoiYWNjZXNzIiwiaWRlbnRpdHkiOjYyMTAwNjgsIm5iZiI6MTc0MDMxNTg2NywiY3NyZiI6ImQxY2NiZWZjLTVjMzUtNDA0MS1iZTgwLTUwZTBmYzkzZGI4YiIsImV4cCI6MTc0MDMyMzA2NywidWMiOnsic2FmZSI6dHJ1ZX0sInVkIjoiLmVKeEZqazFMdzBBWWhQX0t5NTVhNkc3Mk83dkpTVHdvMUhveDBHUFlaTl9xMHJRSmFiUi00SDgzUVVIbTlzd01NMThrVHFRZ2trdER1YVJTVlVJVlhCY3laeXIzMGhxeUlSSGZVb3YxOURIZ0hMMWk4ODlTX0NYbG9XMjhNanhTTDZLak91U09lbTBpUmEtRmQ3cTF5dG01TnVLcG43QU9NWTdMcW5CTTZKd0pKWmxVaV85NndiRU96M2hlVHUzNno5UjFJVE9NdzJxZnpyR19YdUN4QXNFWkwyRUdWcGZ3YnZVYWJvYWh3ejAyMnpSbFJzM1hMYXkyOTlYdVlRTmRPaUxjWVh2czEzRDdNdllueklSU2pDLUNwM0FJWV9xcmtPOGZBdHhLMHcubm1uMHE4T3BiZ2lqdFFJZkl4X1JlV2s1LVZZIn0.P0d85fCrcyT09rv0W_WNGumtEGBBVeA6o-16aSrXjww",
        "origin": "https://kream.co.kr",
        "priority": "u=1, i",
        "referer": "https://kream.co.kr/my/selling/74024436",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "x-kream-api-version": "41",
        "x-kream-client-datetime": "20250223205123+0900",
        "x-kream-device-id": "web;fcb9350d-91d8-4a78-945d-e941984c6386",
        "x-kream-web-build-version": "6.7.4",
        "x-kream-web-request-secret": "kream-djscjsghdkd"
    }




def format_date_kst(date_str):
    try:
        # UTC 기준 시간 변환
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

        # 한국 시간(KST)으로 변환 (UTC+9)
        dt_kst = dt + timedelta(hours=9)

        return dt_kst.strftime("%Y-%m-%d %I:%M:%S %p")
    except Exception:
        return ""


def get_progress_status_list(progress):
    # progress의 title이 '진행 상황'인지 확인
    if progress and progress.get("title") == "진행 상황":
        title_list = []

        for item in progress.get("items", []):
            title_obj = item.get("title", {})  # title 객체 가져오기
            title_text = title_obj.get("text", "")

            # ";tl_0;"이면 lookups에서 값 가져오기
            if title_text == ";tl_0;":
                lookups = title_obj.get("lookups", [])
                if lookups and isinstance(lookups, list) and len(lookups) > 0:
                    title_text = lookups[0].get("text", "")

            # title_text가 비어있지 않으면 리스트에 추가
            if title_text:
                title_list.append(title_text)

        return title_list

    return []  # title이 '진행 상황'이 아니면 빈 리스트 반환


def get_transaction_time(items):
    for section in items:
        for item in section.get("items", []):
            title_obj = item.get("title")  # title 객체 가져오기

            if title_obj and isinstance(title_obj, dict):  # title이 None이 아니고, dict인지 확인
                title_text = title_obj.get("text", "")

                if title_text == "거래 일시":
                    description_obj = item.get("description", {})

                    if isinstance(description_obj, dict):  # description이 dict인지 확인
                        return format_date_kst(description_obj.get("text", ""))

    return ""  # "거래 일시"가 없으면 None 반환


def get_penalty_info(items):
    for section in items:
        for item in section.get("items", []):
            title_obj = item.get("title")  # title 객체 가져오기

            if title_obj and isinstance(title_obj, dict):  # title이 None이 아니고, dict인지 확인
                title_text = title_obj.get("text", "")

                if title_text == "페널티":
                    description_obj = item.get("description", {})

                    if isinstance(description_obj, dict):  # description이 dict인지 확인
                        return description_obj.get("text", "")


    return ""  # "페널티"가 없으면 None 반환



def get_penalty_payment_date(items):
    for section in items:
        for item in section.get("items", []):
            title_obj = item.get("title")  # title 객체 가져오기

            if title_obj and isinstance(title_obj, dict):  # title이 None이 아니고, dict인지 확인
                title_text = title_obj.get("text", "")

                if title_text == "페널티 결제일":
                    description_obj = item.get("description", {})

                    if isinstance(description_obj, dict):  # description이 dict인지 확인
                        return format_date_kst((description_obj.get("text", "")))

    return ""  # "페널티 결제일"이 없으면 None 반환


def get_instant_sale_price(items):
    for section in items:
        for item in section.get("items", []):
            title_obj = item.get("title")  # title 객체 가져오기

            if title_obj and isinstance(title_obj, dict):  # title이 None이 아니고, dict인지 확인
                title_text = title_obj.get("text", "")

                if title_text == "즉시 판매가":
                    description_obj = item.get("description", {})

                    if isinstance(description_obj, dict):  # description이 dict인지 확인
                        lookups = description_obj.get("lookups", [])
                        if lookups and isinstance(lookups, list) and len(lookups) > 0:
                            return lookups[0].get("text", "")  # 첫 번째 lookup의 text 반환

    return ""  # "즉시 판매가"가 없으면 None 반환


def get_tracking_info(data):
    tracking_obj = data.get("tracking", {})  # tracking 객체 가져오기

    if isinstance(tracking_obj, dict):  # dict인지 확인
        return tracking_obj.get("tracking_code")  # 존재하면 반환

    return ""  # tracking_code가 없으면 None 반환

# API 요청 및 데이터 파싱 함수
def fetch_product_data(product_id):
    url = f"https://api.kream.co.kr/api/m/asks/{product_id}?request_key=458d341e-e092-45d5-a60c-7768069b3516"
    headers = get_headers()

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        progress_data = data.get("progress", {})
        progress_list = get_progress_status_list(progress_data)

        transaction_time = get_transaction_time(data.get("items", []))

        penalty_info = get_penalty_info(data.get("items", []))

        penalty_payment_date = get_penalty_payment_date(data.get("items", []))

        instant_sale_price = get_instant_sale_price(data.get("items", []))

        tracking_info = get_tracking_info(data)

        return {
            "주문번호": data.get("oid"),
            "사이즈": data.get("option"),
            "영문명": data.get("product", {}).get("release", {}).get("name"),
            "한글명": data.get("product", {}).get("release", {}).get("translated_name"),
            "모델번호": data.get("product", {}).get("release", {}).get("style_code"),
            "진행 상황": progress_list,
            "즉시 판매가": instant_sale_price,
            "거래 일시": transaction_time,
            "페널티": penalty_info,
            "페널티 결제일": penalty_payment_date,
            "페널티 결제 정보": data.get("payment", {}).get("pg_display_title", {}),
            "발송 정보": tracking_info,
        }
    else:
        print(f"Failed to fetch data for product {product_id}, status code: {response.status_code}")
        return ""

# 엑셀 저장 함수
def save_to_excel(data_list, filename="kream_orders.xlsx"):
    df = pd.DataFrame(data_list)
    df.to_excel(filename, index=False)
    print(f"엑셀 저장 완료: {filename}")

# 메인 함수
def main():
    product_ids = ['72420662', '72134068', '72133735', '72133618', '72066435', '72066413', '72066328', '72065912', '72065751', '72065743', '72065471', '72065336', '72065288', '72065023', '72037186', '72012240', '71841119', '71841034', '71830891', '71757171', '71757129', '71757090', '71753448', '71730474', '71730181', '71730031', '71730003', '71717796', '71447914', '71444943', '71346619', '71344660', '71342952', '71342939', '71342919', '71342911', '71342899', '71342894', '71342888', '71342882', '71342875', '71342861', '71342856', '71342850', '71342845', '71342840', '71342832', '71342826', '71342822', '71342817', '71342810', '71342806', '71342796', '71342790', '71342785', '71342781', '71342730', '71342702', '71342685', '71342656', '71342648', '71342639', '71342613', '71342596', '71342587', '71342581', '71342550', '71342529', '71342512', '71342508', '71342501', '71342492', '71342485', '71322374', '71155896', '71155875', '71155751', '71116059', '71068599', '71046522', '71040910', '71037083', '71037056', '71037009', '71036126', '71036097', '71035711', '71035092', '71035036', '71034679', '71034657', '71034478', '71034453', '71034327', '71034299', '71034162', '71033959', '71033934', '71033915', '71033765', '71033698', '71017882', '70964357', '70963882', '70963538', '70661279', '70660501', '70659627', '70659186', '70658189', '70656983', '70562705', '70562704', '70562703', '70562695', '70562693', '70562691', '70562689', '70509741', '70509608', '70509468', '70459336', '70459316', '70446601', '70446593', '70446591', '70401992', '70401363', '70401299', '70401253', '70337418', '70337417', '70337416', '70337415', '70337410', '70337406', '70337401', '70337398', '70337391', '70337388', '70295397', '70153408', '70153040', '70152968', '69914689', '69829046', '69732949', '69729810', '69542607', '69533885', '68949020', '68897100', '68316791', '68174370', '68122720', '67846154', '66227408', '65338421', '64273854', '61707870', '60902529', '60903668', '49168867', '49167893', '49167859', '49168617', '49168056', '49167394', '49167352']
    print(len(product_ids))
    data_list = []
    for product_id in product_ids:
        product_data = fetch_product_data(product_id)
        print(f'product_data : {product_data}')
        time.sleep(0.5)
        if product_data:
            data_list.append(product_data)

    print(data_list)

    if data_list:
        save_to_excel(data_list)

# 실행
if __name__ == "__main__":
    main()
