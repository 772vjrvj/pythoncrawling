# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

# =========================================================
# 0) 설정
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
IN_CSV   = BASE_DIR / "thairath_renamed_seq_clean.csv"
OUT_CSV  = BASE_DIR / "thairath_muslim_200404_200503_stats.csv"

# 분석 기간 (UTC 기준으로 처리)
START = "2004-04-01"
END_EXCL = "2005-04-01"   # 2005-03-31까지 포함하려면 end는 2005-04-01 미만으로

KEYWORD = "มุสลิม"

# =========================================================
# 1) 텍스트 선택 규칙: articleBody 우선, 없으면 title
# =========================================================
def pick_text(row) -> str:
    body = row.get("articleBody", "")
    if pd.notna(body):
        body = str(body).strip()
        if body:
            return body

    title = row.get("title", "")
    if pd.notna(title):
        title = str(title).strip()
        if title:
            return title

    return ""

# =========================================================
# 2) 실행
# =========================================================
df = pd.read_csv(IN_CSV)

# publishTime 파싱 (Z/UTC 포함 ISO 문자열 대응)
# errors='coerce'로 이상값은 NaT 처리
df["__dt__"] = pd.to_datetime(df.get("publishTime"), errors="coerce", utc=True)

# 기간 필터 (2004-04-01 <= dt < 2005-04-01)
start_dt = pd.Timestamp(START, tz="UTC")
end_dt   = pd.Timestamp(END_EXCL, tz="UTC")
df = df[(df["__dt__"] >= start_dt) & (df["__dt__"] < end_dt)].copy()

# 텍스트 만들기
df["__text__"] = df.apply(pick_text, axis=1)
df["__text__"] = df["__text__"].astype(str)

# 빈 텍스트 제거(선택)
df = df[df["__text__"].str.strip().str.len() > 0].reset_index(drop=True)

total_docs = len(df)
if total_docs == 0:
    raise ValueError("해당 기간(2004-04~2005-03)에 분석할 텍스트가 없습니다.")

# 키워드 포함 여부(단순 substring)
df["has_keyword"] = df["__text__"].str.contains(KEYWORD, regex=False)

doc_count = int(df["has_keyword"].sum())
doc_percent = round((doc_count / total_docs) * 100, 4)

out = pd.DataFrame([{
    "period_start": START,
    "period_end_inclusive": "2005-03-31",
    "keyword_th": KEYWORD,
    "total_docs_in_period": total_docs,
    "doc_count": doc_count,
    "doc_percent": doc_percent,
}])

out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

print("완료!")
print(f"- 기간: {START} ~ 2005-03-31")
print(f"- 전체 기사 수: {total_docs}")
print(f"- '{KEYWORD}' 포함 기사 수: {doc_count}")
print(f"- 비율(%): {doc_percent}")
print(f"- 결과 파일: {OUT_CSV}")

# (옵션) 포함 기사만 별도 저장하고 싶으면 주석 해제
# HIT_CSV = BASE_DIR / "thairath_muslim_200404_200503_hits.csv"
# df[df["has_keyword"]].to_csv(HIT_CSV, index=False, encoding="utf-8-sig")
# print(f"- 포함 기사 목록: {HIT_CSV}")
