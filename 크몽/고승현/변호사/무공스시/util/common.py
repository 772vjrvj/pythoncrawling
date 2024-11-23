# 전체 페이지 스크린샷 캡처
import time
import re
from PIL import Image
import os
from urllib.parse import urlparse

def capture_full_page_screenshot(driver, file_path):
    try:
        # 페이지 전체 크기 가져오기
        total_width = driver.execute_script("return document.body.scrollWidth")
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")

        # 스크롤 단계와 캡처된 이미지를 저장할 리스트
        scroll_steps = range(0, total_height, viewport_height)
        screenshot_parts = []

        for step in scroll_steps:
            # 스크롤 위치 이동
            driver.execute_script(f"window.scrollTo(0, {step});")
            time.sleep(0.3)  # 스크롤 대기

            # 현재 뷰포트 캡처
            screenshot_part_path = f"{file_path}_part_{step}.png"
            driver.save_screenshot(screenshot_part_path)
            screenshot_parts.append(screenshot_part_path)

        # 마지막 스크롤에서 남은 높이 처리
        if total_height % viewport_height > 0:
            driver.execute_script(f"window.scrollTo(0, {total_height - viewport_height});")
            time.sleep(0.3)
            screenshot_part_path = f"{file_path}_part_final.png"
            driver.save_screenshot(screenshot_part_path)
            screenshot_parts.append(screenshot_part_path)

        # 이미지 결합
        stitched_image = Image.new("RGB", (total_width, total_height))
        current_height = 0

        for idx, part_path in enumerate(screenshot_parts):
            with Image.open(part_path) as part_image:
                # 현재 캡처된 이미지 크기 가져오기
                part_width, part_height = part_image.size

                # 마지막 스크롤 조정
                if idx == len(screenshot_parts) - 1 and total_height % viewport_height > 0:
                    part_image = part_image.crop((0, part_height - (total_height % viewport_height), part_width, part_height))

                stitched_image.paste(part_image, (0, current_height))
                current_height += part_image.size[1]

            os.remove(part_path)  # 임시 파일 삭제

        # 최종 스크린샷 저장
        final_path = f"{file_path}.png"
        stitched_image.save(final_path)
        print(f"Full page screenshot saved: {final_path}")
        return final_path

    except Exception as e:
        print(f"Error capturing full page screenshot: {e}")
        return None


def make_dir(site):
    # 폴더 경로 생성
    folder_path = f'{site}_image_list'

    # 폴더가 없으면 생성
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"{folder_path} 폴더생성")
    else:
        print(f"{folder_path} 폴더존재")
    

def excel_max_cut(content):
    # 내용 자르기 (Excel 셀 최대 크기 제한 처리)
    max_cell_length = 32767  # Excel 셀의 최대 문자 크기
    if len(content) > max_cell_length:
        print(f"Content too long, trimming to {max_cell_length} characters.")
        return content[:max_cell_length]  # 내용 자르기
    else:
        return content


def extract_and_format(site, url):
    if site == 'fmkorea':
        return url.split("/")[-1]
    elif site == 'ruliweb':
        match = re.search(r'board/(\d+)/read/(\d+)', url)
        if match:
            board_id = match.group(1)
            read_id = match.group(2)
            return f'{board_id}_{read_id}'
        else:
            return ''
    elif site == 'inven':
        return url.split("/")[-1]
    elif site == 'arcalive':
        return url.split("/")[-1]
