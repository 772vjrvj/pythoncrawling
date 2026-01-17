import pandas as pd
from pathlib import Path

def remove_duplicate_by_contact(
        input_filename: str,
        output_filename: str,
        contact_col: str = "연락처"
):
    # 현재 경로
    base_dir = Path.cwd()

    input_path = base_dir / input_filename
    output_path = base_dir / output_filename

    if not input_path.exists():
        raise FileNotFoundError(f"엑셀 파일이 없습니다: {input_path}")

    # 엑셀 읽기
    df = pd.read_excel(input_path)

    if contact_col not in df.columns:
        raise ValueError(f"'{contact_col}' 컬럼이 존재하지 않습니다")

    # === 핵심 ===
    # 연락처 기준 중복 제거 (첫 번째 row 유지)
    dedup_df = df.drop_duplicates(
        subset=[contact_col],
        keep="first"
    )

    # 엑셀로 저장
    dedup_df.to_excel(output_path, index=False)

    print(f"처리 완료")
    print(f"- 원본 행 수: {len(df)}")
    print(f"- 중복 제거 후 행 수: {len(dedup_df)}")
    print(f"- 저장 경로: {output_path}")


if __name__ == "__main__":
    remove_duplicate_by_contact(
        input_filename="hohoyoga_seoul__20260114011544.xlsx",
        output_filename="output_dedup.xlsx"
    )
