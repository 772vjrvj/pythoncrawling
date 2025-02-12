import requests

# 이미지 URL
# url = "https://www.mytheresa.com/media/1094/1238/100/e6/P00965150.jpg"
# url = "https://www.mytheresa.com/media/1094/1238/100/e6/P00965150_b1.jpg"
url = "https://www.mytheresa.com/media/1094/1238/100/e6/P00965150_b2.jpg"
# 이미지를 다운로드하여 파일로 저장
response = requests.get(url)

# 이미지가 성공적으로 다운로드된 경우
if response.status_code == 200:
    with open("P00965150_b2.jpg", "wb") as file:
        file.write(response.content)
    print("이미지가 성공적으로 다운로드되었습니다.")
else:
    print("이미지 다운로드 실패")
