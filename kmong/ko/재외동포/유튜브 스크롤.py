import pyautogui
import webbrowser
import time


# url = "https://www.youtube.com/@OKAKOREA/videos" #45
# url = "https://www.youtube.com/@OKc-center/videos" #607
# url = "https://www.youtube.com/@studykoreanvod/videos" #500
url = "https://www.youtube.com/@YTNKOREAN/videos" #4000

webbrowser.open(url)

# Step 2: 브라우저가 로드되는 동안 대기 (인터넷 속도에 따라 조정 가능)
time.sleep(5)  # 페이지 로드 기다림

# Step 3: 스크롤을 계속 내리는 함수 정의
def scroll_down_forever():
    while True:
        # pyautogui.scroll()에서 음수 값은 아래로 스크롤, 양수는 위로 스크롤
        pyautogui.scroll(-500)  # 스크롤 속도를 조절할 수 있음
        time.sleep(1)  # 스크롤 간 대기 시간

# Step 4: 스크롤 내리기
scroll_down_forever()
