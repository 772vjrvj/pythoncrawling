import os
import re
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# 프로그램 실행 경로에서 파일 읽기
file_path = os.path.join(os.getcwd(), "송창록.html")
with open(file_path, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# ul class="list_article #post_list list_post1" 찾기
ul_element = soup.find("ul", class_="list_article #post_list list_post1")
if not ul_element:
    raise ValueError("목록을 찾을 수 없습니다.")

# li class="animation_up" 들을 가져오기
li_elements = ul_element.find_all("li", class_="animation_up", recursive=False)

# 객체 리스트 생성
objects = []
base_url = "https://brunch.co.kr"

for li in li_elements:
    obj = {}
    # a 태그의 href 추출
    a_tag = li.find("a")
    if a_tag and "href" in a_tag.attrs:
        href = a_tag["href"]
        obj["URL"] = base_url + href
        # href의 맨 뒤 번호 추출
        match = re.search(r"/(\d+)$", href)
        if match:
            obj["번호"] = match.group(1)
    else:
        continue  # href가 없는 경우 스킵

    # a 태그 안의 class="tit_subject"의 text 추출
    title_tag = a_tag.find("strong", class_="tit_subject")
    obj["제목"] = title_tag.text.strip() if title_tag else ""

    # a 태그 안의 class="publish_time"의 text 추출 및 날짜 변환
    time_tag = a_tag.find("span", class_="publish_time")
    if time_tag:
        raw_date = time_tag.text.strip()
        # 날짜 변환: May 08. 2023 -> yyyy.mm.dd
        try:
            parsed_date = datetime.strptime(raw_date, "%b %d. %Y")
            obj["날짜"] = parsed_date.strftime("%Y.%m.%d")
        except ValueError:
            obj["날짜"] = raw_date  # 변환 실패 시 원본 유지
    else:
        obj["날짜"] = ""

    objects.append(obj)

# 객체 리스트를 DataFrame으로 변환
df = pd.DataFrame(objects)

# 엑셀로 저장
output_path = os.path.join(os.getcwd(), "송창록 목록.xlsx")
df.to_excel(output_path, index=False)

print(f"엑셀 파일이 생성되었습니다: {output_path}")
