# -*- coding: utf-8 -*-
import re
import pandas as pd
from pathlib import Path

# =========================================================
# 0) 설정
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
IN_CSV   = BASE_DIR / "thairath_renamed_seq_clean.csv"
OUT_CSV  = BASE_DIR / "thairath_keyword_stats_7words.csv"

# 우리가 확정한 7개 키워드
KEYWORDS = [
    ("โจรใต้",       "남부 분리주의 무장 세력/남부 반군"),
    ("มุสลิม",        "무슬림/이슬람교도"),
    ("ความมั่นคง",    "국가 안보/치안/보안"),
    ("พื้นที่สีแดง",  "레드존/위험 지역/분쟁 지역"),
    ("ยิง",           "사격/총격"),
    ("ระเบิด",        "폭발/폭탄 사건"),
    ("ปะทะ",          "충돌/교전/무력 충돌"),
]

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
# 2) (가능하면) 태국어 토크나이저 사용 → 단어 기준 정규화
#    없으면 문자 기준 정규화
# =========================================================
def try_get_word_tokenize():
    try:
        from pythainlp.tokenize import word_tokenize  # type: ignore
        return word_tokenize
    except Exception:
        return None

WORD_TOKENIZE = try_get_word_tokenize()

def normalize_denominator(text: str):
    """
    norm_value 계산용 분모:
    - pythainlp 있으면 단어 수(word count)
    - 없으면 문자 수(char count)로 대체
    """
    if WORD_TOKENIZE is not None:
        tokens = WORD_TOKENIZE(text, keep_whitespace=False)
        wc = len([t for t in tokens if t and not t.isspace()])
        return max(wc, 1), "per_1000_words"
    # 태국어 띄어쓰기 한계 때문에 fallback은 문자 기준이 더 안정적
    cc = len(text)
    return max(cc, 1), "per_10000_chars"

# =========================================================
# 3) 키워드 카운트
#    - phrase(พื้นที่สีแดง, ความมั่นคง 등)는 substring count가 실용적
#    - 단어(ยิง 등)도 태국어 특성상 substring 기반이 무난함
# =========================================================
def count_occurrences(text: str, kw: str) -> int:
    # 겹침(overlap) 거의 문제 안 되는 키워드들이라 단순 count 사용
    return text.count(kw)

# =========================================================
# 4) 실행
# =========================================================
df = pd.read_csv(IN_CSV)

df["__text__"] = df.apply(pick_text, axis=1)
df = df[df["__text__"].astype(str).str.len() > 0].reset_index(drop=True)

total_docs = len(df)
if total_docs == 0:
    raise ValueError("분석할 텍스트가 없습니다. (articleBody/title 둘 다 비어있는 row만 존재)")

# 문서별 분모(단어수 또는 문자수)
denoms = []
basis = None
for t in df["__text__"].astype(str).tolist():
    d, b = normalize_denominator(t)
    denoms.append(d)
    basis = b  # 모두 동일 basis로 나옴
df["__denom__"] = denoms

results = []

for kw_th, kw_ko in KEYWORDS:
    # 문서별 등장 횟수
    occ = df["__text__"].astype(str).apply(lambda x: count_occurrences(x, kw_th))
    # 기사 단위 포함(1회 이상이면 해당 기사에 포함)
    doc_mask = occ > 0

    doc_count = int(doc_mask.sum())
    doc_percent = round(doc_count / total_docs * 100, 2)

    total_occ = int(occ.sum())

    # 정규화 강도
    denom_sum = int(df["__denom__"].sum())
    if basis == "per_1000_words":
        norm_value = round((total_occ / denom_sum) * 1000, 4)  # 1000단어당 등장
    else:
        norm_value = round((total_occ / denom_sum) * 10000, 4)  # 10000문자당 등장

    results.append({
        "keyword_th": kw_th,
        "keyword_ko": kw_ko,
        "doc_count": doc_count,
        "doc_percent": doc_percent,
        "total_occurrences": total_occ,
        "norm_value": norm_value,
        "norm_basis": basis,
        "total_docs_analyzed": total_docs,
    })

out_df = pd.DataFrame(results)
out_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

print("완료!")
print(f"- 분석 문서 수: {total_docs}")
print(f"- 결과 파일: {OUT_CSV}")
print(out_df)
