import os
from bs4 import BeautifulSoup
import pandas as pd

# 프로그램 실행 경로의 '비플랜.html' 파일 읽기
file_path = os.path.join(os.getcwd(), '비플랜.html')

if not os.path.exists(file_path):
    raise FileNotFoundError(f"'{file_path}' 파일이 존재하지 않습니다.")

with open(file_path, 'r', encoding='utf-8') as file:
    soup = BeautifulSoup(file, 'html.parser')

# class="content_item_inner" 찾기
content_items = soup.find_all(class_='content_item_inner')

# 결과를 담을 배열
result = []

# 각 content_item_inner 처리
for item in content_items:
    obj = {}

    # class="content_text" 안의 a 태그 텍스트 추출
    content_text = item.find(class_='content_text')
    if content_text:
        a_tags = content_text.find_all('a')
        obj['카테고리'] = a_tags[0].get_text(strip=True) if len(a_tags) > 0 else None
        obj['url'] = f"https://contents.premium.naver.com{a_tags[1]['href']}" if a_tags[1] else None

        # strong 태그 텍스트 추출
        strong_tag = content_text.find('strong', class_='content_title')
        obj['제목'] = strong_tag.get_text(strip=True) if strong_tag else None

    # class="content_info" 아래의 두 번째 class="content_info_text" 텍스트 추출
    content_info = item.find(class_='content_info')
    if content_info:
        info_texts = content_info.find_all(class_='content_info_text')
        obj['날짜'] = info_texts[1].get_text(strip=True) if len(info_texts) > 1 else None

    print(obj)
    # 결과 배열에 추가
    result.append(obj)

# 데이터프레임으로 변환 및 엑셀 저장
df = pd.DataFrame(result)
output_file = os.path.join(os.getcwd(), 'result.xlsx')
df.to_excel(output_file, index=False)

print(f"엑셀 파일이 성공적으로 저장되었습니다: {output_file}")
