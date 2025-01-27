import pandas as pd

def update_filtered_content(filter_file, update_file):
    # 엑셀 파일 읽기
    filter_df = pd.read_excel(filter_file, engine="openpyxl")  # 재외동포.xlsx
    update_df = pd.read_excel(update_file, engine="openpyxl")  # 업데이트_재외동포_필터.xlsx

    # 순번을 기준으로 매핑하여 "콘텐츠 내용" 업데이트
    content_mapping = update_df.set_index("순번")["콘텐츠 내용"].to_dict()  # 순번 -> 콘텐츠 내용 매핑

    # 기존 "콘텐츠 내용"이 비어있는 경우에만 업데이트
    filter_df["콘텐츠 내용"] = filter_df.apply(
        lambda row: content_mapping.get(row["순번"], row["콘텐츠 내용"]) if pd.isna(row["콘텐츠 내용"]) else row["콘텐츠 내용"],
        axis=1
    )

    # 업데이트된 데이터 저장
    filter_df.to_excel(filter_file, index=False, engine="openpyxl")
    print(f"파일이 성공적으로 업데이트되었습니다: {filter_file}")

# 파일 경로 설정
filter_file = "재외동포.xlsx"
update_file = "업데이트_재외동포_필터.xlsx"

# 함수 실행
update_filtered_content(filter_file, update_file)
