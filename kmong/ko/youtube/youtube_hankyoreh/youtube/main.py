import os
import pandas as pd
from bs4 import BeautifulSoup

# 폴더 경로 및 HTML 파일 범위 설정
folder_path = os.path.join(os.getcwd(), "youtube_sen")  # 현재 경로 내 youtube_sen 폴더
file_range = range(2, 20)  # 2.html부터 19.html까지

# 결과를 담을 리스트 초기화
data = []


urls = ["https://www.youtube.com/watch?v=WgFi_lXmofs&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=327",
        "https://www.youtube.com/watch?v=6jdWM6nXbAI&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=295",
        "https://www.youtube.com/watch?v=LacjDxxRD1s&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=289",
        "https://www.youtube.com/watch?v=98fhrs2NB8w&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=277",
        "https://www.youtube.com/watch?v=8RrkbAd9Q5k&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=276",
        "https://www.youtube.com/watch?v=MxgluFEWJTc&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=275",
        "https://www.youtube.com/watch?v=zv3jcz5A7ws&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=272",
        "https://www.youtube.com/watch?v=eZPj_DFogaQ&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=269",
        "https://www.youtube.com/watch?v=huvSC_fpYw8&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=267",
        "https://www.youtube.com/watch?v=122f2QG1Pq8&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=266",
        "https://www.youtube.com/watch?v=n2qRO09lxb8&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=265",
        "https://www.youtube.com/watch?v=x77xCjWaSW4&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=264",
        "https://www.youtube.com/watch?v=A5WyB_JrL_o&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=263",
        "https://www.youtube.com/watch?v=jdxinl7h590&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=262",
        "https://www.youtube.com/watch?v=Tc4bF0rG-9Q&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=261",
        "https://www.youtube.com/watch?v=Jx7WFznh2eU&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=260",
        "https://www.youtube.com/watch?v=X2BV3Hnp9xA&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=256",
        "https://www.youtube.com/watch?v=PVS9gBxwWMo&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=254"]



# 파일 읽기 및 데이터 추출
for i in file_range:
    print(f'index {i}')
    file_name = f"{i}.html"
    file_path = os.path.join(folder_path, file_name)

    # HTML 파일을 읽어들이기
    with open(file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(html_content, "html.parser")

    # 특정 태그 안의 텍스트를 모두 추출하여 배열에 담기
    for span in soup.find_all("span", class_="yt-core-attributed-string yt-core-attributed-string--white-space-pre-wrap"):
        # 텍스트와 파일 이름을 함께 저장
        data.append({"reply": span.get_text(), "name": urls[i-2]})

# DataFrame 생성
df = pd.DataFrame(data)

# 엑셀 파일로 저장
output_file = os.path.join(os.getcwd(), 'replies_last.xlsx')
df.to_excel(output_file, index=False)

print(f"엑셀 파일로 저장되었습니다: {output_file}")
