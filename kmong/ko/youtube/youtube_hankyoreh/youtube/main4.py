import pyautogui
import webbrowser
import time

# Step 1: 브라우저 열기 및 URL로 이동
# url = "https://www.youtube.com/watch?v=6jdWM6nXbAI&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=295" # 3

# url = "https://www.youtube.com/watch?v=98fhrs2NB8w&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=277" # 5

# url = "https://www.youtube.com/watch?v=MxgluFEWJTc&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=275" # 7

# url = "https://www.youtube.com/watch?v=eZPj_DFogaQ&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=269" #9

# url = "https://www.youtube.com/watch?v=122f2QG1Pq8&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=266" #11

# url = "https://www.youtube.com/watch?v=x77xCjWaSW4&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=264" #13

# url = "https://www.youtube.com/watch?v=jdxinl7h590&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=262" #15

url = "https://www.youtube.com/watch?v=Jx7WFznh2eU&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=260" #17

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
