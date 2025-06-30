import pandas as pd
import json

# 1. 엑셀 파일 로드
df = pd.read_excel("data.xlsx", dtype={"등록번호": str})

# 2. JSON 파일 로드
with open("test.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)

# 3. JSON 항목 추출 함수
def extract_info(reg_no):
    data = json_data.get(reg_no.zfill(7), {})  # zero-padding 대응

    # 피인용 횟수 숫자로 변환
    cited_count = data.get("BCTC", "")
    cited_count = int(cited_count) if cited_count.isdigit() else ""

    # IPC 파싱
    ipc_raw = data.get("IPC", "")
    ipc_list = [code.strip() for code in ipc_raw.split("|") if code.strip()]
    ipc_str = ", ".join(ipc_list)

    return {
        "법적상태": data.get("LSTO", ""),
        "심사청구항수": data.get("BIC", ""),
        "피인용횟수": cited_count,
        "최종권리자": data.get("AP", ""),
        "IPC코드": ipc_str  # 리스트를 문자열로 변환
    }

# 4. 등록번호 기준 데이터 추출
extra_info_list = df["등록번호"].apply(lambda reg_no: extract_info(reg_no))

# 5. 추가 컬럼 생성 및 병합
extra_df = pd.DataFrame(extra_info_list.tolist())
result_df = pd.concat([df, extra_df], axis=1)

# 6. 엑셀 저장
result_df.to_excel("kipris_결과_병합.xlsx", index=False)
print("✅ 엑셀 저장 완료: kipris_결과_병합.xlsx")
