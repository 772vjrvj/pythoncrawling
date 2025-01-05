from bs4 import BeautifulSoup

# HTML 파일을 읽어들이기
with open("kim1.html", "r", encoding="utf-8") as file:
    html_content = file.read()

# BeautifulSoup 객체 생성
soup = BeautifulSoup(html_content, "html.parser")

# 특정 태그 안의 텍스트를 모두 추출하여 배열에 담기
texts = []
for span in soup.find_all("span", class_="yt-core-attributed-string yt-core-attributed-string--white-space-pre-wrap"):
    print(f' text : {span.get_text()}')

    texts.append(span.get_text())

# 결과 출력
print(texts)
