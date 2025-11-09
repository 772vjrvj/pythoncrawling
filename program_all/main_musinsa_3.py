# -*- coding: utf-8 -*-
"""
musinsa_goods_detail.csv 에서 email 중복 제거 후 저장
- 컬럼: goodsNo, email
- 빈값 제외, 중복 제거
- unique_emails.csv 로 출력
"""
import pandas as pd

SRC_PATH = "musinsa_goods_detail.csv"
OUT_PATH = "unique_emails.csv"

def main():
    try:
        df = pd.read_csv(SRC_PATH, dtype=str)  # 모든 컬럼 문자열로 읽기
    except Exception as e:
        print(f"[ERROR] CSV 읽기 실패: {e}")
        return

    if "email" not in df.columns:
        print("[ERROR] 'email' 컬럼이 없습니다.")
        return

    # email 정제
    df["email"] = df["email"].astype(str).str.strip()
    df = df[df["email"].notna() & (df["email"] != "")]

    # 중복 제거
    unique_emails = df["email"].drop_duplicates().reset_index(drop=True)

    # 새 CSV 저장
    unique_emails.to_csv(OUT_PATH, index=False, header=["email"], encoding="utf-8-sig")
    print(f"[OK] 고유 이메일 {len(unique_emails)}개 저장 완료 → {OUT_PATH}")

if __name__ == "__main__":
    main()
