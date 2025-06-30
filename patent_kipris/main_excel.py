import pandas as pd
import json

def extract_info(data):
    # 피인용 횟수 숫자로 변환
    cited_count = data.get("BCTC", "")
    cited_count = int(cited_count) if cited_count.isdigit() else ""

    # IPC 파싱
    ipc_raw = data.get("IPC", "")
    ipc_list = [code.strip() for code in ipc_raw.split("|") if code.strip()]
    ipc_str = ", ".join(ipc_list)

    return {
        "법적상태 (등록/소멸-등록료불납/존속기간만료)": data.get("LSTO", ""),
        "심사청구항수": data.get("BIC", ""),
        "피인용 횟수": cited_count,
        "최종 권리자": data.get("AP", ""),
        "IPC코드": ipc_str
    }

def main():
    # 1. 엑셀 로드 및 등록번호 정규화
    df = pd.read_excel("data.xlsx", dtype={"등록번호": str})
    df["등록번호"] = df["등록번호"].apply(lambda x: str(x).zfill(7))

    # 2. JSON 데이터 로드
    with open("data.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)

    result_rows = []

    # 3. 각 등록번호에 대해 매칭 데이터 추출
    for idx, row in df.iterrows():
        reg_no = row["등록번호"]
        found = False

        for key, data in json_data.items():
            if reg_no in key and reg_no in data.get("GN", ""):
                info = extract_info(data)
                new_row = row.to_dict()
                new_row.update(info)
                result_rows.append(new_row)
                found = True
                break

        if not found:
            print(f"⚠️ 매칭 실패: {reg_no}")

    # 4. 결과 병합 및 저장
    result_df = pd.DataFrame(result_rows)
    columns = [
        "기업코드", "등록번호", "출원년도", "잔존기간", "권리만료일",
        "법적상태 (등록/소멸-등록료불납/존속기간만료)", "심사청구항수", "피인용 횟수", "최종 권리자", "IPC코드"
    ]
    result_df = result_df[columns]
    result_df.to_excel("kipris_결과_병합.xlsx", index=False)
    print("✅ 엑셀 저장 완료: kipris_결과_병합.xlsx")

if __name__ == "__main__":
    main()
