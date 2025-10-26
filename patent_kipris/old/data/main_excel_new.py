import pandas as pd
import json

def extract_info(data):
    """JSON 객체에서 필요한 필드 추출 및 변환"""
    cited_count = data.get("BCTC", "")
    cited_count = int(cited_count) if cited_count.isdigit() else ""

    ipc_raw = data.get("IPC", "")
    ipc_list = [code.strip() for code in ipc_raw.split("|") if code.strip()]
    ipc_str = ", ".join(ipc_list)

    ad_raw = data.get("AD", "")
    ad_formatted = ad_raw.replace("-", ".") if ad_raw else ""

    return {
        "법적상태 (등록/소멸-등록료불납/존속기간만료)": data.get("LSTO", ""),
        "심사청구항수": data.get("BIC", ""),
        "피인용 횟수": cited_count,
        "최종 권리자": data.get("AP", ""),
        "출원번호(일자)": f"{data.get('AN', '')} ({ad_formatted})" if data.get("AN") else "",
        "등록번호": data.get("GN", ""),
        "IPC코드": ipc_str
    }

def empty_info():
    """빈 데이터 구조 반환"""
    return {
        "법적상태 (등록/소멸-등록료불납/존속기간만료)": "",
        "심사청구항수": "",
        "피인용 횟수": "",
        "최종 권리자": "",
        "출원번호(일자)": "",
        "등록번호": "",
        "IPC코드": ""
    }

def main():
    # 1. 엑셀 로드
    df = pd.read_excel("data_new.xlsx", dtype=str).fillna("")

    # 2. JSON 로드
    with open("data.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)

    result_rows = []

    for _, row in df.iterrows():
        no = row["NO"].strip()
        ap = row["AP"].strip()
        ipc = row["IPC"].strip()

        matched = False
        for key, data in json_data.items():
            if no in key and ap in data.get("AP", "") and ipc in data.get("IPC", ""):
                info = extract_info(data)
                new_row = row.to_dict()
                new_row.update(info)
                result_rows.append(new_row)
                matched = True
                break

        if not matched:
            print(f"⚠️ 매칭 실패: {no}")
            new_row = row.to_dict()
            new_row.update(empty_info())
            result_rows.append(new_row)

    # 3. 결과 저장
    result_df = pd.DataFrame(result_rows)

    columns = [
        "NO", "AP", "IPC",
        "법적상태 (등록/소멸-등록료불납/존속기간만료)",
        "심사청구항수", "피인용 횟수",
        "최종 권리자", "출원번호(일자)", "등록번호", "IPC코드"
    ]
    result_df = result_df[[col for col in columns if col in result_df.columns]]
    result_df.to_excel("kipris_결과_병합.xlsx", index=False)

    print("✅ 엑셀 저장 완료: kipris_결과_병합.xlsx")

if __name__ == "__main__":
    main()
