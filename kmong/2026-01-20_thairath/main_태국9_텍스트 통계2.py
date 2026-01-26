# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

# =========================================================
# 0) 설정
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
IN_CSV   = BASE_DIR / "thairath_renamed_seq_clean.csv"
OUT_CSV  = BASE_DIR / "thairath_keyword_stats_7words.csv"

# =========================================================
# 1) 7개 대표 단어(Anchor) + 보조 단어(lexicon)
#   - 표에는 anchor_th(대표 단어)만 보여주고,
#   - 집계(doc_count/doc_percent)는 anchor + 보조 단어 전체로 계산
# =========================================================
# === 텍스트 카테고리(대표 키워드 + 보조어휘군) ===
# - anchor_th: 대표(표에 표시되는) 태국어 키워드
# - core_terms/ext_terms: 대표 의미를 보강하는 동의/완곡/서술 표현
# - 괄호/주석: 한국어 의미(대략 번역) ※ 문맥 따라 뉘앙스 달라질 수 있음

ANCHOR_LEXICONS = [
    {
        "anchor_th": "โจรใต้",  # 남부 반군/남부 분리주의 무장세력(관행적 지칭)
        "anchor_ko": "남부 분리주의 무장 세력/남부 반군",
        "core_terms": [
            "ผู้ก่อเหตุ",           # 가해자/사건을 일으킨 자
            "คนร้าย",              # 범인/용의자(범죄자)
            "กลุ่มก่อความไม่สงบ",   # 소요/불안을 조성하는 집단(소요 세력)
            "กลุ่มติดอาวุธ",        # 무장 집단
            "ผู้ต้องสงสัย",         # 용의자
            "กลุ่มผู้ก่อการ",       # 가해 집단/행위자 집단
            "แนวร่วม",             # 연계 세력/협력 세력(연대)
        ],
        "ext_terms": [
            "ขบวนการแบ่งแยกดินแดน", # 분리주의 운동/분리 독립 세력
            "กลุ่มหัวรุนแรง",       # 극단주의 집단
            "ผู้ก่อความไม่สงบ",     # 소요/불안을 조성하는 자(불온세력)
            "มือปืน",               # 총격범/총잡이(무장 공격자)
            "กลุ่มผู้ไม่หวังดี",     # 악의적 세력/불순분자(좋지 않은 의도의 집단)
            "ลอบโจมตี",             # 기습 공격/매복 공격
            "ก่อการร้าย",           # 테러(행위) / 테러를 저지르다
        ],
    },
    {
        "anchor_th": "มุสลิม",  # 무슬림
        "anchor_ko": "무슬림/이슬람교도",
        "core_terms": [
            "อิสลาม",            # 이슬람
            "ชาวมุสลิม",          # 무슬림 사람들/무슬림 공동체
            "ศาสนาอิสลาม",       # 이슬람교(종교)
            "ชุมชนมุสลิม",        # 무슬림 공동체/지역 공동체
            "ศาสนิกชนมุสลิม",     # 무슬림 신자
            "มุสลิมในพื้นที่",     # 해당 지역의 무슬림(지역 내 무슬림)
        ],
        "ext_terms": [
            "อิสลามิก",           # 이슬람의/이슬람식(형용 표현)
            "ผู้นำศาสนา",         # 종교 지도자
            "โต๊ะอิหม่าม",         # 이맘(호칭/지역 관행 표현)
            "อิหม่าม",            # 이맘(이슬람 성직자/지도자)
            "มัสยิด",             # 모스크(이슬람 사원)
            "ศาสนสถาน",           # 종교 시설/성소
        ],
    },
    {
        "anchor_th": "ความมั่นคง",  # (국가)안보/치안/보안
        "anchor_ko": "국가 안보/치안/보안",
        "core_terms": [
            "ความปลอดภัย",        # 안전
            "ความสงบ",            # 평온/질서/평화(치안 안정)
            "สถานการณ์ความไม่สงบ", # 불안/소요 상황
            "ปัญหาความมั่นคง",     # 안보 문제
            "มาตรการความมั่นคง",   # 안보 조치
            "ด้านความมั่นคง",      # 안보 측면/안보 분야
            "รักษาความปลอดภัย",    # 안전/치안 유지(보안 유지)
            "ความมั่นคงในพื้นที่",  # 지역 안보/해당 지역의 치안
        ],
        "ext_terms": [
            "เข้มงวด",            # 엄격(강화/강도 높임)
            "เฝ้าระวัง",           # 감시/경계(모니터링)
            "ตรวจเข้ม",            # 집중 단속/강도 높은 검문·점검
            "ยกระดับมาตรการ",      # 조치 수준을 격상하다
            "ปิดล้อมตรวจค้น",       # 포위 수색/봉쇄 수색
            "ลาดตระเวน",           # 순찰
            "ตั้งด่าน",            # 검문소/검문 초소 설치
            "คุมเข้ม",            # 강하게 통제/관리 강화
            "ป้องกันเหตุ",          # 사건 예방(사고/사건 방지)
            "ดูแลความสงบ",         # 질서/치안 유지 관리
        ],
    },
    {
        "anchor_th": "พื้นที่สีแดง",  # 레드존/위험 지역(분쟁/소요 관련)
        "anchor_ko": "레드존/위험 지역/분쟁 지역",
        "core_terms": [
            "เขตสีแดง",            # 레드존(구역)
            "เขตแดง",              # 레드존(축약)
            "พื้นที่แดง",           # 레드 지역
            "พื้นที่เสี่ยง",         # 위험 지역
            "พื้นที่เสี่ยงภัย",       # 위험(재난/사고) 지역
            "พื้นที่อันตราย",         # 위험 지역/위험한 구역
        ],
        "ext_terms": [
            "พื้นที่เปราะบาง",        # 취약 지역(불안정/취약)
            "พื้นที่ความไม่สงบ",       # 소요/불안 지역
            "เขตอันตราย",            # 위험 구역
            "พื้นที่เสี่ยงต่อเหตุรุนแรง", # 폭력 사건 위험 지역
            "เขตเสี่ยง",             # 위험 구역(축약)
        ],
    },
    {
        "anchor_th": "ยิง",  # 사격/총격(쏘다)
        "anchor_ko": "사격/총격",
        "core_terms": [
            "ถูกยิง",              # 피격되다/총에 맞다
            "ยิงถล่ม",             # 난사/집중사격하다
            "ยิงปะทะ",             # 교전(총격전)하다
            "ยิงใส่",              # ~을 향해 쏘다/발포하다
            "ยิงเสียชีวิต",         # 총격으로 사망
            "ยิงบาดเจ็บ",           # 총격으로 부상
            "กระหน่ำยิง",           # 연발/집중 사격하다(퍼붓다)
        ],
        "ext_terms": [
            "คนร้ายยิง",            # 범인이 쏘다/총격
            "เปิดฉากยิง",           # 발포를 시작하다(총격 개시)
            "กราดยิง",             # 난사하다(무차별 총격)
            "ยิงใกล้",              # 근거리 사격(가까이서 쏘다)
            "ยิงจาก",              # ~로부터/에서 발포(출처 표현)
            "เหตุยิง",             # 총격 사건
            "ยิงแล้วหลบหนี",         # 쏘고 도주하다
            "ยิงต่อเนื่อง",          # 연속 사격/지속 총격
        ],
    },
    {
        "anchor_th": "ระเบิด",  # 폭발/폭탄
        "anchor_ko": "폭발/폭탄 사건",
        "core_terms": [
            "วัตถุระเบิด",           # 폭발물
            "ลอบวางระเบิด",          # (몰래) 폭탄 설치/사제폭탄 매설
            "ระเบิดแสวงเครื่อง",     # 사제폭탄/IED
            "บึ้ม",                 # ‘쾅’ 폭발(구어)
            "แรงระเบิด",            # 폭발력
            "เสียงระเบิด",           # 폭발음
            "ระเบิดขึ้น",            # 폭발하다
            "จุดระเบิด",             # 폭발 지점/점화·폭발시키다(문맥)
        ],
        "ext_terms": [
            "คาร์บอมบ์",            # 차량 폭탄(카 밤)
            "รถบอมบ์",              # 차량 폭탄
            "ระเบิดถล่ม",            # 폭발 공격/폭탄 세례(강한 표현)
            "เหตุระเบิด",            # 폭발 사건
            "เก็บกู้วัตถุระเบิด",     # 폭발물 처리/제거(해체)
            "หน่วยเก็บกู้",           # 수거/제거(해체) 부대
            "อีโอดี",               # EOD(태국어 음역)
            "EOD",                 # EOD
            "ระเบิดเพลิง",           # 소이탄/화염 폭발물(문맥)
            "สะเก็ดระเบิด",          # 파편(폭발 파편)
        ],
    },
    {
        "anchor_th": "ปะทะ",  # 충돌/교전
        "anchor_ko": "충돌/교전/무력 충돌",
        "core_terms": [
            "ปะทะกัน",              # 서로 충돌/교전하다
            "ยิงปะทะ",              # 총격 교전
            "เหตุปะทะ",             # 교전/충돌 사건
            "การปะทะ",              # 충돌/교전(명사형)
            "ปะทะเดือด",            # 격렬한 충돌/교전
            "ปะทะหนัก",             # 격한/큰 충돌
            "ปะทะดุเดือด",           # 매우 격렬한 교전
        ],
        "ext_terms": [
            "เปิดฉากปะทะ",           # 교전을 시작하다
            "เกิดการปะทะ",           # 충돌이 발생하다
            "ปะทะกันอย่างหนัก",       # 격렬하게 충돌하다
            "ปะทะกับเจ้าหน้าที่",      # 당국/요원과 교전
            "ปะทะกับทหาร",           # 군과 교전
            "ปะทะกับตำรวจ",          # 경찰과 교전
            "ปะทะในพื้นที่",          # 지역에서 교전/충돌
            "ปะทะนาน",              # 장시간 교전(뉘앙스)
            "ปะทะต่อเนื่อง",          # 지속적 교전
        ],
    },
]


# =========================================================
# 2) 텍스트 선택 규칙: articleBody 우선, 없으면 title
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
# 3) (가능하면) 태국어 토크나이저 사용 → 단어 기준 정규화
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
    cc = len(text)
    return max(cc, 1), "per_10000_chars"

# =========================================================
# 4) lexicon 카운트 (substring 기반)
# =========================================================
def uniq_terms(anchor: str, core_terms, ext_terms):
    items = []
    if anchor and anchor.strip():
        items.append(anchor.strip())
    items += [str(x).strip() for x in (core_terms or []) if str(x).strip()]
    items += [str(x).strip() for x in (ext_terms or []) if str(x).strip()]

    seen = set()
    out = []
    for t in items:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out

def count_occurrences(text: str, terms) -> int:
    total = 0
    for t in terms:
        total += text.count(t)
    return total

# =========================================================
# 5) 실행
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
    basis = b
df["__denom__"] = denoms
denom_sum = int(df["__denom__"].sum())

results = []

for it in ANCHOR_LEXICONS:
    anchor_th = it["anchor_th"]
    anchor_ko = it["anchor_ko"]
    terms = uniq_terms(anchor_th, it.get("core_terms"), it.get("ext_terms"))

    occ = df["__text__"].astype(str).apply(lambda x: count_occurrences(x, terms))
    doc_mask = occ > 0

    doc_count = int(doc_mask.sum())
    doc_percent = round(doc_count / total_docs * 100, 2)

    total_occ = int(occ.sum())

    if basis == "per_1000_words":
        norm_value = round((total_occ / denom_sum) * 1000, 4)
    else:
        norm_value = round((total_occ / denom_sum) * 10000, 4)

    results.append({
        # ✅ 네가 원하는 최종 표 컬럼(대표 단어 형태 유지)
        "keyword_th": anchor_th,
        "keyword_ko": anchor_ko,
        "doc_count": doc_count,
        "doc_percent": doc_percent,

        # 아래는 참고용(원하면 지워도 됨)
        "terms_total_unique": len(terms),
        "total_occurrences": total_occ,
        "norm_value": norm_value,
        "norm_basis": basis,
        "total_docs_analyzed": total_docs,
    })

out_df = pd.DataFrame(results)

# 표 순서 고정(고객이 처음 요청한 7개 순서 유지)
order = ["โจรใต้", "มุสลิม", "ความมั่นคง", "พื้นที่สีแดง", "ยิง", "ระเบิด", "ปะทะ"]
out_df["__order__"] = out_df["keyword_th"].apply(lambda x: order.index(x) if x in order else 999)
out_df = out_df.sort_values("__order__").drop(columns=["__order__"]).reset_index(drop=True)

out_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

print("완료!")
print(f"- 분석 문서 수: {total_docs}")
print(f"- 결과 파일: {OUT_CSV}")
print(out_df.to_string(index=False))
