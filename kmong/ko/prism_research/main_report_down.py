import os
import requests
import pandas as pd
import re

# 설정 값
EXCEL_FILENAME = "prism_data_report.xlsx"
SHEET_NAME = "전체"
SAVE_DIR = "prism_data_report_전체"

# 요청 URL
DOWNLOAD_URL = "https://www.prism.go.kr/homepage/entire/homepageTotalSearchDownload.do"

# 요청 헤더 (쿠키 제거)
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "connection": "keep-alive",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://www.prism.go.kr",
    "referer": "https://www.prism.go.kr/homepage/researchsrch/totalSearchProgress2.do",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
}

# 폴더 생성
os.makedirs(SAVE_DIR, exist_ok=True)

# 파일 ID를 파싱하는 함수
def parse_file_id(file_id):
    """
    파일 ID를 분해하여 필요한 필드 값을 반환
    예외 처리:
      - 001_CPR_001_      -202100001_Y  같은 경우 연구 ID 유지
    """
    match = re.match(r"(\d{3})_(\w{3})_(\d{3})_(.*?)-(\d+)_([A-Z])", file_id)
    if match:
        work_key, file_type, seq_no, research_prefix, research_suffix, pdf_conv_yn = match.groups()
        research_id = f"{research_prefix}-{research_suffix}"
    else:
        match = re.match(r"(\d{3})_(\w{3})_(\d{3})_(.*)", file_id)
        if match:
            work_key, file_type, seq_no, research_id = match.groups()
            pdf_conv_yn = "Y"
        else:
            print(f"❌ 파일 ID 형식 오류 (건너뜀): {file_id}")
            return None

    return {
        "work_key": work_key,
        "file_type": file_type,
        "seq_no": seq_no,
        "research_id": research_id,
        "pdf_conv_yn": pdf_conv_yn
    }

# 파일 저장 함수 (중복 처리)
def get_unique_filename(directory, filename):
    """파일명이 중복되면 (1), (2) 숫자를 붙여서 반환"""
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}({counter}){ext}"
        counter += 1

    return new_filename

# 파일 다운로드 함수
def download_file(file_info, file_name):
    """
    파일 다운로드 요청 및 저장
    """
    payload = {
        "work_key": file_info["work_key"],
        "file_type": file_info["file_type"],
        "seq_no": file_info["seq_no"],
        "research_id": file_info["research_id"],
        "pdf_conv_yn": file_info["pdf_conv_yn"]
    }

    try:
        response = requests.post(DOWNLOAD_URL, headers=HEADERS, data=payload, stream=True)
        response.raise_for_status()

        # 중복 처리된 파일명 생성
        unique_filename = get_unique_filename(SAVE_DIR, file_name)

        # 파일 저장
        file_path = os.path.join(SAVE_DIR, unique_filename)
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ 다운로드 완료: {file_path}")
        return "Y", unique_filename  # 다운로드 성공 시 파일명 반환
    except requests.exceptions.RequestException as e:
        print(f"❌ 다운로드 실패: {file_name} - {e}")
        return "N", ""  # 다운로드 실패 시 빈 문자열 반환

# 엑셀 파일 읽기 및 데이터 처리 (업데이트 포함)
def process_excel():
    try:
        # 엑셀 파일 로드
        df = pd.read_excel(EXCEL_FILENAME, sheet_name=SHEET_NAME, engine="openpyxl")

        # 필요한 컬럼 존재 여부 확인 및 추가
        if "파일아이디" not in df.columns or "파일명" not in df.columns:
            raise ValueError("❌ 필요한 컬럼(파일아이디, 파일명)이 엑셀에 없습니다.")

        if "다운로드" not in df.columns:
            df["다운로드"] = ""  # 다운로드 여부 컬럼 추가

        if "다운로드 파일" not in df.columns:
            df["다운로드 파일"] = ""  # 다운로드된 실제 파일명 컬럼 추가

        # 객체 리스트 변환
        for index, row in df.iterrows():
            print(f'🔄 번호 {index + 1} 처리 중...')

            try:
                file_id = str(row["파일아이디"]).strip()  # 파일아이디
                file_name = str(row["파일명"]).strip()  # 파일명

                # 파일 ID 파싱
                file_info = parse_file_id(file_id)
                if file_info:
                    # 파일 다운로드 실행
                    download_status, saved_filename = download_file(file_info, file_name)

                    # 엑셀 업데이트
                    df.at[index, "다운로드"] = download_status
                    df.at[index, "다운로드 파일"] = saved_filename
                else:
                    df.at[index, "다운로드"] = "N"  # 파일 ID 오류 시 실패 처리

            except Exception as e:
                print(f"❌ 데이터 처리 중 오류 발생 (건너뜀): {e}")
                df.at[index, "다운로드"] = "N"  # 오류 발생 시 실패 처리
                continue  # 다음 행으로 진행

        # 엑셀 파일 업데이트 (기존 데이터 유지)
        with pd.ExcelWriter(EXCEL_FILENAME, engine="openpyxl", mode="w") as writer:
            df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

        print(f"📁 엑셀 파일 업데이트 완료: {EXCEL_FILENAME}")

    except Exception as e:
        print(f"❌ 엑셀 파일 처리 중 오류 발생: {e}")

# 실행
if __name__ == "__main__":
    process_excel()
