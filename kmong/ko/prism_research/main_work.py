import requests
import pandas as pd
import time
import re
import os
from openpyxl import load_workbook

# 요청에 필요한 헤더 설정 (쿠키 제거)
HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "connection": "keep-alive",
    "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    "origin": "https://www.prism.go.kr",
    "referer": "https://www.prism.go.kr/homepage/researchsrch/totalSearchProgress2.do",
    "cookie": "JSESSIONID=I2Z5UnPOFk5bvsExwatHc3bo.prism_40; VISITDAY_INNER=20250302; WHATAP=z2dibc5kr7t9bf; clientid=020027119457",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}

# 요청 URL
URL = "https://www.prism.go.kr/homepage/entire/homepageTotalSearchProgressAsync.do"

# 페이지별 데이터 요청 함수 (최대 3회 재시도)
def fetch_data(page_no, max_retries=3):
    payload = {
        "detailSearch": "N",
        "page_no": page_no,
        "menuNo": "I0000002",
        "target": "ASSIGN",
        "sim_yn": "N",
        "query": "푸드플랜",
        "from": "",
        "to": "",
        "organ_id": "",
        "brm_biz_id": "",
        "or_query": "",
        "and_query": "",
        "not_query": "",
        "stnc_query": "",
        "research_outln": "",
        "research_keyword": "",
        "research_contents": "",
        "research_smry": "",
        "inner_query": ""
    }

    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.post(URL, headers=HEADERS, data=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            retry_count += 1
            print(f"페이지 {page_no} 요청 중 오류 발생 (재시도 {retry_count}/{max_retries}): {e}")
            time.sleep(1)

    print(f"페이지 {page_no} 요청 실패. 최대 재시도 횟수 초과.")
    return None

# HTML 태그 제거 및 줄바꿈 처리 함수
def clean_text(text):
    if not isinstance(text, str):
        return text
    text = text.replace("<br>", "\n")
    text = re.sub(r'<.*?>', '', text)
    return text.strip()

# 50개씩 데이터를 한 파일에 추가 저장하는 함수
def save_to_excel(data, filename="prism_data_work.xlsx"):
    df = pd.DataFrame(data)

    # 필요한 컬럼만 선택
    columns = ["no", "page_no", "brm_biz_nm", "research_nm", "research_id", "research_stat", "organ_nm", "research_outln", "research_contents", "research_smry", "research_keyword", "search_keyword", "type"]
    df = df[columns]

    # 컬럼명 변경 (한글로 변경)
    df.columns = ["No", "페이지번호", "사업명", "연구명", "연구아이디", "연구상태", "기관명", "연구개요", "연구내용", "연구요약", "연구 키워드", "검색어", "유형"]

    # 모든 텍스트 컬럼에 대해 HTML 태그 제거 및 줄바꿈 적용
    for col in ["사업명", "연구명", "연구상태", "기관명", "연구개요", "연구내용", "연구요약", "연구 키워드"]:
        df[col] = df[col].apply(clean_text)

    # 파일이 이미 존재하는 경우 추가 (append)
    if os.path.exists(filename):
        with pd.ExcelWriter(filename, mode="a", engine="openpyxl", if_sheet_exists="overlay") as writer:
            df.to_excel(writer, index=False, header=False, startrow=writer.sheets["Sheet1"].max_row)
    else:
        # 파일이 없으면 헤더 포함해서 새로 생성
        df.to_excel(filename, index=False, engine="openpyxl")

    print(f"{len(df)}개의 데이터가 {filename} 파일에 추가되었습니다.")

# 모든 페이지 데이터를 수집하는 함수 (50개 단위 저장)
def collect_all_data(batch_size=50):
    all_results = []
    for page_no in range(1, 12):
        print(f"페이지 {page_no} 데이터 수집 중...")
        data = fetch_data(page_no)
        if data and "assign" in data and "resultList" in data["assign"]:
            result_list = data["assign"]["resultList"]
            for idx, item in enumerate(result_list, start=1):
                item["no"] = (page_no - 1) * 10 + idx
                item["page_no"] = page_no
                item["search_keyword"] = "푸드플랜"
                item["type"] = "과제정보"
                all_results.append(item)

        # 50개 이상이면 바로 저장 후 리스트 초기화
        if len(all_results) >= batch_size:
            save_to_excel(all_results)
            all_results = []  # 저장 후 리스트 초기화

        time.sleep(0.5)  # 서버 부하 방지를 위해 대기

    # 마지막 남은 데이터 저장
    if all_results:
        save_to_excel(all_results)

# 메인 함수
def main():
    print("데이터 수집 시작...")
    collect_all_data()
    print("데이터 수집 완료.")

# 실행
if __name__ == "__main__":
    main()
