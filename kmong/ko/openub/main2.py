import pytesseract
from PIL import Image
import re

# Tesseract 설치 경로 지정
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 이미지 파일 열기
img = Image.open("image2.png")

# 이미지에서 텍스트 추출
raw_text = pytesseract.image_to_string(img, lang='kor')

# 줄바꿈을 기준으로 문자열을 나누어 배열에 담기
text_lines = raw_text.splitlines()

# 필터링 조건에 맞는 요소만 남기기
filtered_lines = [
    line for line in text_lines
    if re.search(r'\d', line) or re.search(r'[억만~]', line)
]

# 배열을 역순으로 정렬
filtered_lines.reverse()

# 배열을 하나의 문자열로 합친 후 공백 제거
result = ''.join(filtered_lines).replace(" ", "")

# '워' 제거
result = re.sub(r'[워위원]', '', result)

# 결과 출력
print("최종 문자열:", result)




# https://github.com/UB-Mannheim/tesseract/wiki 여기서
# tesseract-ocr-w64-setup-5.4.0.20240606.exe (64비트) 다운로드

# https://github.com/tesseract-ocr/tessdata 여기서 kor.traineddata 다운
# D:\program\Tesseract-OCR\tessdata\ 폴더 안에 kor.traineddata 파일이 있어야 합니다.