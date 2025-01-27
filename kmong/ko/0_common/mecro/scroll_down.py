import pyautogui
import keyboard
import time

def scroll_down_continuously():
    print("스크롤 매크로 시작: 's'를 눌러 중지하세요.")
    try:
        while not keyboard.is_pressed('s'):  # 's' 키를 누르면 종료
            pyautogui.scroll(-100)  # 아래로 스크롤 (음수 값)
            time.sleep(0.1)  # 0.1초 대기 (너무 빠르면 속도 조절)
    except KeyboardInterrupt:
        print("매크로가 중지되었습니다.")

if __name__ == "__main__":
    print("매크로를 시작하려면 'r'을 누르세요.")
    keyboard.wait('r')  # 'r' 키를 누르면 매크로 시작
    scroll_down_continuously()
    print("스크롤 매크로 종료.")