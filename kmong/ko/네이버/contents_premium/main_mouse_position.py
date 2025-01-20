from pynput import mouse

def on_click(x, y, button, pressed):
    if pressed:
        print(f"Mouse clicked at ({x}, {y})")

# 마우스 리스너 설정
with mouse.Listener(on_click=on_click) as listener:
    listener.join()

# 클릭시 현재 마우스 위치

# 드래그 프리 시작
# Mouse clicked at (1012, 83)

# 제한풀기
# Mouse clicked at (599, 251)

# 드래그 프리 시작
# Mouse clicked at (1012, 83)

# 클릭
# Mouse clicked at (79, 186)

# 컨트롤 + A 전체선택 -> 복사

