import pyautogui
import subprocess
import time

# 1. 크롬 브라우저 실행 및 유튜브 접속
def open_chrome_and_go_to_youtube(url):
    # 크롬 브라우저를 실행 (크롬의 경로를 지정)
    chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
    subprocess.Popen([chrome_path, url])
    time.sleep(5)  # 브라우저가 열릴 때까지 대기

# 2. 댓글을 보기 위해 끝까지 스크롤하는 함수
def scroll_to_bottom():
    last_position = pyautogui.position()
    same_position_count = 0

    # 주기적으로 페이지 아래로 스크롤
    while same_position_count < 5:  # 스크롤 위치가 5번 연속으로 같으면 종료
        pyautogui.scroll(-1000)  # 스크롤을 아래로 내림
        time.sleep(1)  # 1초 대기
        current_position = pyautogui.position()

        # 스크롤 위치가 변화가 없으면 종료 카운트 증가
        if current_position == last_position:
            same_position_count += 1
        else:
            same_position_count = 0

        last_position = current_position

# 3. 스크롤이 끝난 후 웹 페이지 저장
def save_page_html():
    # Ctrl+S를 눌러서 '페이지 저장' 창을 엶
    pyautogui.hotkey('ctrl', 's')
    time.sleep(2)  # 저장 대기 (파일명 입력 창 대기)

    # 파일명을 입력하고 엔터를 눌러 저장
    pyautogui.write("222.html")
    pyautogui.press('enter')

if __name__ == "__main__":
    youtube_url = "https://www.youtube.com/watch?v=WgFi_lXmofs&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=327"  # 유튜브 동영상 URL
    open_chrome_and_go_to_youtube(youtube_url)

    # 스크롤 시작 (페이지 로드 이후)
    time.sleep(10)  # 페이지가 완전히 로드될 때까지 대기
    scroll_to_bottom()

    # 페이지 HTML 저장
    save_page_html()
