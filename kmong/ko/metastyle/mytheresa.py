import requests

# 이미지 URL
url = "https://www.mytheresa.com/media/2310/2612/100/e6/P00965150.jpg"

# 이미지를 다운로드하여 파일로 저장
response = requests.get(url)

# 이미지가 성공적으로 다운로드된 경우
if response.status_code == 200:
    with open("P00965150.jpg", "wb") as file:
        file.write(response.content)
    print("이미지가 성공적으로 다운로드되었습니다.")
else:
    print("이미지 다운로드 실패")
