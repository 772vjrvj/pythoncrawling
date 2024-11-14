import pandas as pd
import re

# 엑셀 파일 읽기 (예: input.xlsx)
df = pd.read_excel('스터디코리안 학생소식.xlsx')

# "콘텐츠 대상지역" 컬럼에서 ] 뒤의 텍스트를 제거하는 함수 정의
def remove_text_after_bracket(text):
    # NaN 값을 빈 문자열로 처리
    if pd.isna(text):
        return ""

    # "]"가 포함된 경우만 ] 뒤의 텍스트 제거
    if ']' in text:
        return re.sub(r'\].*', ']', text)
    else:
        return text  # "]"가 없는 경우는 그대로 반환

# "콘텐츠 대상지역" 컬럼에 함수 적용
df['콘텐츠 대상지역'] = df['콘텐츠 대상지역'].apply(remove_text_after_bracket)

# 결과를 새로운 엑셀 파일로 저장 (예: output.xlsx)
df.to_excel('output.xlsx', index=False)
