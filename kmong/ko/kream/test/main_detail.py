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
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6dHJ1ZSwiaWF0IjoxNzQwNDEwMjYzLCJqdGkiOiI2YmI3YTE3Mi0zMzNkLTQ5ZGMtODZlOS0wZjhlMDRhM2E4ZGUiLCJ0eXBlIjoiYWNjZXNzIiwiaWRlbnRpdHkiOjYyMTAwNjgsIm5iZiI6MTc0MDQxMDI2MywiY3NyZiI6ImM5NTZlNDdjLTIxZDAtNDc4Yy1hN2E0LWQ3YjI2MGVlYzdlNyIsImV4cCI6MTc0MDQxNzQ2MywidWMiOnsic2FmZSI6dHJ1ZX0sInVkIjoiLmVKeEZqazFyZzBBUWh2X0tzS2NFc3V0LU9rWlBvWWNXMHZSU0lVZFozVW16eEVReHR1a0hfZTlWV2lqdjdYbm5tWmt2RmthV015MjE0MUp6YlV2bGNvVzVOV0t0VUdZWlc3RkFiN0doYXZ6b2FScTlVZjNQWXZnbEJTTGEyaldXbzVQRUxTSHllbjN3UEF0b2xMWm1YalpwQTUyN2tTb2Z3akJmVlpsUUZvVXlXbWlUVHYzcmxZYkt2OUJsZm1yWGZjYTI5WWtURWhiN2VBbmQ3UXBQSlNncFpBRVRTRzBCNzZsZHdxYnZXOXBUdlkxajRnd0trOEppLTFEdUhsZlF4aFBCUFRXbmJnbDN4NkU3VTZLTUVYSU9QUHVESC1LZndyNV9BTmUxU3BrLjhmbGhyMTdnV0VjdU5aVk13NFFaNlZKbVp4USJ9.aBOflP-xU2mrFI8MPsrnslW3t5WAC00F2OJTwjVotX4",
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


def get_progress_status_text(progress):
    # progress의 title이 '진행 상황'인지 확인합니다.
    if progress and progress.get("title") == "진행 상황":
        for item in progress.get("items", []):
            description = item.get("description")
            if description and isinstance(description, dict):
                text = description.get("text", "")
                if text:  # text 값이 존재하면 즉시 반환
                    return text
    return ""  # 해당 조건을 만족하는 text가 없으면 빈 문자열 반환


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


def extract_fail_and_success_reason(data):
    fail_reason = ""
    success_reason = ""

    # 최상위 items 배열을 순회합니다.
    for section in data.get("items", []):
        section_title = section.get("title")

        # 불합격/페널티 사유 섹션인 경우
        if section_title == "불합격/페널티 사유":
            items = section.get("items", [])
            if items:
                title_obj = items[0].get("title", {})
                fail_reason = title_obj.get("text", "")

        # 95점 합격 사유 섹션인 경우
        elif section_title == "95점 합격 사유":
            items = section.get("items", [])
            if items:
                title_obj = items[0].get("title", {})
                success_reason = title_obj.get("text", "")

    return fail_reason, success_reason


# API 요청 및 데이터 파싱 함수
def fetch_product_data(product_id):
    request_key = "351ec129-c8d3-480c-a80c-f835488e88eb"
    url = f"https://api.kream.co.kr/api/m/asks/{product_id}?request_key={request_key}"
    headers = get_headers()

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        progress_data = data.get("progress", {})
        progress_text = get_progress_status_text(progress_data)

        transaction_time = get_transaction_time(data.get("items", []))

        penalty_info = get_penalty_info(data.get("items", []))

        penalty_payment_date = get_penalty_payment_date(data.get("items", []))

        instant_sale_price = get_instant_sale_price(data.get("items", []))

        tracking_info = get_tracking_info(data)

        fail_reason, success_reason = extract_fail_and_success_reason(data)

        return {
            "주문번호": data.get("oid"),
            "사이즈": data.get("option"),
            "영문명": data.get("product", {}).get("release", {}).get("name"),
            "한글명": data.get("product", {}).get("release", {}).get("translated_name"),
            "모델번호": data.get("product", {}).get("release", {}).get("style_code"),
            "진행 상황": progress_text,
            "즉시 판매가": instant_sale_price,
            "거래 일시": transaction_time,
            "페널티": penalty_info,
            "페널티 결제일": penalty_payment_date,
            "페널티 결제 정보": data.get("payment", {}).get("pg_display_title", {}),
            "발송 정보": tracking_info,
            "불합격/페널티 사유": fail_reason,
            "95점 합격 사유": success_reason
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
    product_ids = ['83161297', '85057359', '82741666', '82741649', '83216917', '82706851', '81350908', '82460273', '85053400', '81352833', '81595249', '74589865', '81045285', '81350418', '81597835', '81595158', '79199042', '81074753', '81351095', '81597786', '81350485', '79199049', '78283598', '77114561', '75675516', '75675513', '75675499', '74977610', '74957853', '74957758', '74957746', '74957722', '74889290', '74887738', '74887733', '74859668', '74859137', '74858890', '74858806', '74857127', '74815081', '74808626', '74732259', '74732258', '74732257', '74732243', '74732237', '74698681', '74698596', '74667992', '74616454', '74592301', '74586603', '74585285', '74585110', '74584969', '74500493', '74499736', '74499643', '74499287', '74101945', '73801662', '73708887', '73705969', '73336851', '73139203', '73139162', '73124270', '72665949', '72420830', '75685818', '75675487', '75685803', '75685810', '73707798', '74889292', '74887736', '74889296', '72420749', '73911242', '73910718', '73910617', '73910614', '73721498', '73699196', '73162394', '72420837', '72420739', '73459118', '73459106', '73459099', '73459092', '73225359', '73225339', '72421364', '72420815', '72420756', '72420701', '73336394', '73250936', '73225856', '73162497', '73112649', '73112619', '73112612', '73112604', '73073697', '72424340', '72421089', '72420789', '72420684', '72833433', '72420832', '72698216', '72420657', '72420656', '72541306', '72541238', '72491617', '72491576', '72491515', '72486498', '72486063', '72481997', '72480456', '72480131', '72423655', '72420863', '72420857', '72420765', '72420734', '72133874', '72133834', '72066645', '72066195', '72066173', '72037926', '71831237', '71757738', '71757592', '71730279', '71441346', '71342936', '71342716', '71342628', '71342540', '71323265', '71357443', '71342902', '71342709', '71342605', '71342572', '71342561', '71342517', '71322422', '71322145', '71322118', '71322073', '71115883', '71040777', '71034489', '71034153', '71033243', '71033223', '70964300', '70964051', '70446590', '70402000', '69773443', '69009296', '70963090', '70659940', '70446310', '70963798', '70459354', '68773396', '70243327', '67842826', '68069061', '70446307', '69870580', '69604974', '69540312', '69388646', '68949017', '68316898', '69542795', '64755581', '69418784', '69261971', '69261946', '69261431', '69009397', '67842104', '67464429', '65046794', '68631699', '68629002', '68632764', '68703063', '68122804', '66303895', '68476341', '68122751', '64756216', '68568706', '68632169', '68067914', '66227237', '68066702', '68122781', '68507014', '68769420', '68067145', '67343151', '67126362', '67005864', '66789210', '66630120', '66609346', '66600022', '66496946', '66496637', '66495216', '64561089', '63684771', '67479125', '67479055', '67427684', '66628025', '66606849', '66357979', '66227702', '66225514', '63684749', '60983801', '49168714', '67370238', '49168618', '65931501', '64630223', '64258229', '65802543', '64596729', '64259133', '63645899', '63684334', '63644397', '62790837', '61707935', '63214097', '62578106', '62578083', '62569877', '62550458', '62390338', '62389690', '62200077', '62199984', '61707923', '61707903', '61861663', '51001516', '60983784', '60769009', '59615468', '60902261', '60165440', '59615856', '54381722', '60115226', '60410837', '60325986', '60325868', '60165362', '60115477', '59663392', '59114219', '57994842', '57994826', '57895303', '56108119', '54788078', '52088072', '60311840', '60165340', '60125216', '60115840', '60115450', '60115261', '59823352', '59732210', '59664696', '59615732', '59615037', '59614985', '59098514', '57994087', '56108121', '49169009', '60115736', '54147115', '59615736', '57994083', '59191978', '59421020', '59420992', '58280484', '58280654', '56933212', '53304240', '57394109', '57390220', '56933220', '56317396', '55453260', '54381346', '55149376', '55063672', '52524555', '53791348', '52580113', '53270397', '53270240', '52523673', '53258587', '49168315', '51485241', '49167541', '49167520', '47246834', '46697621', '47445717', '46697589', '47246752', '47246737', '47246746', '44516072', '44268457', '44268231', '44514049', '38608700', '37343713', '36830304', '32935425']
    print(len(product_ids))
    data_list = []
    for product_id in product_ids:
        product_data = fetch_product_data(product_id)
        print(f'product_data : {product_data}')
        time.sleep(0.5)
        if product_data:
            data_list.append(product_data)

    print(len(data_list))

    if data_list:
        save_to_excel(data_list)

# 실행
if __name__ == "__main__":
    main()
