# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

# =========================
# 1) 파일 경로
# =========================
BASE_DIR = Path(__file__).resolve().parent
IN_CSV  = BASE_DIR / "thairath_renamed_seq_clean.csv"
OUT_CSV = BASE_DIR / "thairath_clip_score_summary.csv"

# =========================
# 2) CSV 로드
# =========================
df = pd.read_csv(IN_CSV)

total_count = len(df)

if total_count == 0:
    raise ValueError("CSV에 데이터가 없습니다.")

# =========================
# 3) 조건 정의
# =========================
conditions = [
    {
        "label": "force",
        "column": "force_clip_score",
        "condition": ">= 0.23",
        "mask": df["force_clip_score"] >= 0.23
    },
    {
        "label": "checkpoint",
        "column": "checkpoint_clip_score",
        "condition": ">= 0.23",
        "mask": df["checkpoint_clip_score"] >= 0.23
    },
    {
        "label": "red25",
        "column": "red25_clip_score",
        "condition": "== 1",
        "mask": df["red25_clip_score"] == 1
    },
    {
        "label": "smoke",
        "column": "smoke_clip_score",
        "condition": ">= 0.23",
        "mask": df["smoke_clip_score"] >= 0.23
    },
    {
        "label": "guns",
        "column": "guns_clip_score",
        "condition": ">= 0.23",
        "mask": df["guns_clip_score"] >= 0.23
    }
]

# =========================
# 4) 통계 계산
# =========================
rows = []

for c in conditions:
    cnt = int(c["mask"].sum())
    pct = round(cnt / total_count * 100, 2)

    rows.append({
        "label": c["label"],
        "condition": c["condition"],
        "count": cnt,
        "percent": pct
    })

summary_df = pd.DataFrame(rows)

# =========================
# 5) CSV 저장
# =========================
summary_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

print("완료!")
print(summary_df)
print(f"\n총 이미지 수: {total_count}")
print(f"저장 파일: {OUT_CSV}")
