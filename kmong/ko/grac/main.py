import requests
import pandas as pd
from bs4 import BeautifulSoup
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 요청 URL 및 헤더
BASE_URL = "https://www.grac.or.kr/Statistics/GameStatistics.aspx?gameTitle="
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "connection": "keep-alive",
    "host": "www.grac.or.kr",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
}

# 등급 이미지 파일명 매핑
RATING_MAP = {
    "rating_15.gif": "15세이용가",
    "rating_12.gif": "12세이용가",
    "rating_all.gif": "전체이용가"
}

# 컬럼명 설정
TABLE_COLUMNS = [
    "게임물명", "신청자", "분류일자", "등급", "분류번호", "취소", "결정일(관보게재일)",
    "설명서", "기관", "결정내용", "등급이력", "해외등급"
]

OUTPUT_FILE = "게임등급_결과.csv"


def read_excel_data(excel_file):
    """엑셀 파일을 읽고 컬럼명과 제목을 리스트로 변환"""
    df = pd.read_excel(excel_file)

    columns = [
        "어드밴스마메", "마메", "아토미스웨이브", "FB네오", "MSX2", "PC엔진",
        "닌텐도64", "닌텐도DS", "닌텐도엔터테이먼트시스템", "닌텐도게임보이어드밴스",
        "슈퍼닌텐도엔터테이먼트시스템", "드림캐스트", "세가마스터시스템", "세가메가드라이브",
        "세가나오미", "네오지오", "플레이스테이션", "PSP"
    ]

    game_entries = []
    for col in columns:
        if col in df:
            titles = df[col].dropna().astype(str).tolist()
            for title in titles:
                game_entries.append({"컬럼명": col, "제목": title.replace(" ", "")})  # 공백 제거
    return game_entries


def fetch_game_data(entry):
    """각 게임별 등급 데이터를 가져오는 함수"""
    title = entry["제목"]
    column_name = entry["컬럼명"]
    print(f"Processing: {title} ({column_name})")

    url = BASE_URL + title

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # HTTP 에러 확인
    except requests.exceptions.RequestException as e:
        print(f"요청 오류 발생: {e} (게임: {title})")
        return None  # 요청 실패 시 None 반환

    soup = BeautifulSoup(response.text, "html.parser")

    # 새로운 테이블 찾기
    table = soup.find("table", class_="board list fixed mt10 statistics")
    if not table:
        print(f"No data found for {title}")
        return None

    tbody = table.find("tbody")
    rows = tbody.find_all("tr") if tbody else []

    for row in rows:
        columns_data = row.find_all("td")
        row_data = {"컬럼명": column_name, "원래제목": title}  # 원래 제목 추가

        rating_found = False
        cancel_status = ""

        for idx, col in enumerate(columns_data):
            if idx == 3 and not rating_found:
                img_tag = col.find("img")
                if img_tag and "src" in img_tag.attrs:
                    img_src = img_tag["src"]
                    img_filename = os.path.basename(img_src)

                    if img_filename in RATING_MAP:
                        row_data[TABLE_COLUMNS[idx]] = RATING_MAP[img_filename]
                        rating_found = True
                    else:
                        continue  # 등급이 없는 경우 다음 행 검사

                if not rating_found:
                    continue  # 다음 행으로 이동

            else:
                row_data[TABLE_COLUMNS[idx]] = col.get_text(strip=True)

            if idx == 5:
                cancel_status = row_data[TABLE_COLUMNS[idx]]

        if cancel_status == "취소확정":
            return None  # 취소확정이면 데이터 반환 안 함

        if rating_found:
            return row_data  # 가장 먼저 찾은 행만 반환

    return None


def save_to_csv(data):
    """데이터를 CSV 파일에 저장"""
    if data:
        pd.DataFrame(data).to_csv(OUTPUT_FILE, mode="a", index=False, header=not os.path.exists(OUTPUT_FILE), encoding="utf-8-sig")


def process_games(game_entries, batch_size=10):
    """멀티스레드를 이용하여 데이터를 가져오고 CSV에 저장"""
    game_data = []
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        for i in range(0, len(game_entries), batch_size):
            print(f'순번 : {i}')
            batch = game_entries[i:i + batch_size]
            futures = {executor.submit(fetch_game_data, entry): entry for entry in batch}

            for future in as_completed(futures):
                result = future.result()
                if result:
                    game_data.append(result)

            # 50개씩 CSV에 저장 후 리스트 초기화
            if len(game_data) >= 50:
                save_to_csv(game_data)
                game_data = []

            time.sleep(1)  # 배치 실행 후 1초 대기 (서버 부하 방지)

    # 마지막 남은 데이터 저장
    save_to_csv(game_data)


def main():
    """메인 함수"""
    excel_file = "레볼루션2게임리스트-2.xlsx"
    game_entries = read_excel_data(excel_file)

    print(f"총 {len(game_entries)}개의 게임을 검색합니다.")
    process_games(game_entries, batch_size=10)

    print(f"데이터 저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
