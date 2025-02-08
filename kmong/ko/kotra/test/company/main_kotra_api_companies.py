import time

import requests
import csv
import os

def fetch_company_list():
    """
    회사 목록을 계속 요청하여 comList 데이터를 수집하는 함수
    """
    url = "https://buykorea.org/cp/cpy/ajax/selectCpComList.do"
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "content-length": "0",
        "content-type": "application/json",
        "cookie": "ozvid=e2abbd67-24a6-d33f-ea52-a472fcb0d8fc; _pk_id.6,DzGc5mPl.570a=eeb08969fd539d55.1738845101.; JSESSIONID=RMlBjDcM4gdBHhfm_dMUjSuD0B6NFAnMqdGgpr6q.bk-fo-02; dialogSnackbar=Y; bkRcntPrds=3732083%2C3732098%2C3702390%2C3730424%2C3732078%2C3732079; _pk_ses.6,DzGc5mPl.570a=1",
        "host": "buykorea.org",
        "origin": "https://buykorea.org",
        "referer": "https://buykorea.org/cp/cpy/selectCompaniesList.do",
        "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    com_list = []
    srch_skip = 0
    srch_cnt = 10000

    while True:
        params = {
            "sortOrder": 0,
            "srchChar": "",
            "ctgryCd": "",
            "srchStr": "",
            "srchSkip": srch_skip,
            "srchCnt": srch_cnt
        }

        response = requests.post(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"요청 실패: {response.status_code}")
            break

        data = response.json()
        new_com_list = data.get("comList", [])

        if not new_com_list:
            break

        com_list.extend(new_com_list)
        srch_skip += srch_cnt  # 다음 페이지 요청
        print(f'com_list : {len(com_list)}')
        time.sleep(1)

    return com_list

def save_com_list_to_csv(com_list, filename="comList.csv"):
    """
    수집된 comList 데이터를 CSV 파일로 저장하는 함수
    """
    if not com_list:
        print("저장할 데이터가 없습니다.")
        return

    save_path = "comList"
    os.makedirs(save_path, exist_ok=True)  # 폴더 없으면 생성

    file_path = os.path.join(save_path, filename)  # 파일 경로 설정

    keys = com_list[0].keys()
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(com_list)

    print(f"{file_path} 파일로 저장 완료.")
    print(f"총 수집된 기업 수: {len(com_list)}")


if __name__ == "__main__":
    company_data = fetch_company_list()
    save_com_list_to_csv(company_data)
