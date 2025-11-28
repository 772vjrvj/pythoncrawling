# -*- coding: utf-8 -*-
import pandas as pd

# ========================
# 1) 정규화 함수
# ========================
def normalize(df):
    for col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .fillna("")
            .str.replace("\n", "", regex=False)
            .str.replace("\r", "", regex=False)
            .str.strip()
        )
    return df

# ========================
# 2) 데이터 로드 + 정규화
# ========================
df_main = normalize(pd.read_csv("Sheet1.csv", dtype=str))
df_match = normalize(pd.read_csv("매칭조건.csv", dtype=str))

print("[INFO] Sheet1 =", len(df_main))
print("[INFO] 매칭조건 =", len(df_match))

# ========================
# 3) 매칭조건 중복 제거 (매우 중요!)
# ========================

df_match1 = df_match.drop_duplicates(subset=["출원년도", "출원인", "IPC1"])
df_match2 = df_match.drop_duplicates(subset=["출원년도", "출원인", "IPC2"])

print("[INFO] 매칭조건 IPC1 dedup =", len(df_match1))
print("[INFO] 매칭조건 IPC2 dedup =", len(df_match2))

# ========================
# 4) 조건1 매칭
# ========================
merge1 = pd.merge(
    df_main,
    df_match1[["특허NO", "출원년도", "출원인", "IPC1"]],
    how="left",
    left_on=["출원년도", "출원인", "IPC1"],
    right_on=["출원년도", "출원인", "IPC1"]
)

merge1.rename(columns={"특허NO": "조건1"}, inplace=True)

# ========================
# 5) 조건2 매칭
# ========================
merge2 = pd.merge(
    merge1,
    df_match2[["특허NO", "출원년도", "출원인", "IPC2"]],
    how="left",
    left_on=["출원년도", "출원인", "IPC2"],
    right_on=["출원년도", "출원인", "IPC2"],
    suffixes=("", "_cond2")
)

merge2.rename(columns={"특허NO": "조건2"}, inplace=True)

# 매칭 중복열 제거
df_final = merge2.drop(columns=[c for c in merge2.columns if c.endswith("_cond2")])

# ========================
# 6) 결과 저장
# ========================
df_final.to_csv("output.csv", index=False, encoding="utf-8-sig")
print("[INFO] output.csv 저장 완료")

# ========================
# 7) 행 수 검증
# ========================
print("[INFO] 최종 행수 =", len(df_final))

if len(df_final) != len(df_main):
    print("[ERROR] ❌ 행 수가 증가/감소함 → 매칭키 불일치 또는 CSV 구조 오류")
else:
    print("[INFO] ✅ 행 수 정상 (113,439 유지됨)")
