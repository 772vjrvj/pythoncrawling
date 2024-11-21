import requests
from bs4 import BeautifulSoup
import time
import random
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from openpyxl import load_workbook
from PIL import Image
import re


# 요청 헤더 설정

# 페이지에서 링크 추출
def extract_links_from_page(query, page):
    try:
        url = f"https://bbs.ruliweb.com/search?q={query}&op=&page={page}#board_search&gsc.tab=0&gsc.q={query}&gsc.page=1"
        print(f"Fetching URL: {url}")
        headers = {
            "authority": "bbs.ruliweb.com",
            "method": "GET",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "cookie": "ruli_board_font=; _ga=GA1.1.879995571.1731767001; __igaw__adid=NzAwPWRiOTkxOWY1ZTkyNTRiYzRmMmNmYmIzNGVhNjM3YTRhOzAwMD0wNjJiOTc4NC04OTMxLTExZWYtOTM3Ny0wMjQyYWMxMTAwMDI=; dable_uid=81234842.1725213932429; __dbl_v=1; session_key=3AmOQmAiIIQBsmm6; ad4989ad4989=1; _pubcid=ed3d4e1a-f369-4551-a6b5-190fcc7bba2d; _pubcid_cst=zix7LPQsHA%3D%3D; panoramaId_expiry=1732374265083; _cc_id=fc8c9804394c04519f4f0ea0a620cc34; panoramaId=3dcdfedecd3cdc6bf59d0e2bd03616d539385c1dede6a341753a5d252be3ae13; __gsas=ID=51e797045032c6fa:T=1731769477:RT=1731769477:S=ALNI_MYZ59MUOI5OQ4P1RvqVIcFAvsL9pQ; pbjs-unifiedid=%7B%22TDID%22%3A%22af80919c-ef84-4080-8e16-ce1f830c7fc1%22%2C%22TDID_LOOKUP%22%3A%22TRUE%22%2C%22TDID_CREATED_AT%22%3A%222024-10-16T15%3A04%3A40%22%7D; pbjs-unifiedid_cst=zix7LPQsHA%3D%3D; adfit_sdk_id=3158cb60-701b-4edb-92de-eded4235a340; ra_l=3600250; login_redirect_url=https%3A%2F%2Fbbs.ruliweb.com%2Fsearch%3Fq%3D%25EB%25A7%2588%25EA%25B3%25B5%25EC%258A%25A4%25EC%258B%259C%26op%3D%26page%3D1; cfa5=60; __gads=ID=17e51649880101e1:T=1731767001:RT=1731776455:S=ALNI_MbU62cFyl7oV3BAG-vbwIftunYotQ; __gpi=UID=00000f968f0d02e3:T=1731767001:RT=1731776455:S=ALNI_MYyFpCkneX3yk7V-HkempGapQIyRw; __eoi=ID=726e175340070e65:T=1731767001:RT=1731776455:S=AA-AfjaEb4mwbsRplKRWYie5FOA5; push_id=201565; _ga_1MX4XJ9Y2Q=GS1.1.1731776456.4.1.1731776749.58.0.0; cto_bidid=ue3vEF9RVCUyRkdmVUJyM1duS3B0aWhrMjRhQUowSndEd1dJam5LJTJCc2N3RVJRUUZ6UHI4NkFxd3BTZ2R2bEwyd2VrZGs4ZVdtTSUyRkM2bDdHSWtqdTNiJTJCcmE1dEo5bVVvczRMMm80dDFGdGhvVjhOYVprJTNE; cto_bundle=AD3JGV9BT3BYZUQ4YzRwSGxoUmxqWCUyRjdPV0hJMURDMHRKZyUyQjJ0T2RodklGc0dSdGtBUEhmTCUyQk5BQzdieWpLQ2tNRzh2U05XUktsVk5ITTdWMHRBWEZJNDA1bVhSY2VhZ3AwMDI0RVdGRHlxR1olMkZzc3dmT1Q4ZlM1M01EeVhEb1RLJTJCTm9NRHJDM1lzbWxESDJLeiUyRnlzdTFyJTJCQmZOQVdDM3I0T0ZXTFBwT1FoVWppb0pjd1BQdUlGQjdlTFpzbzNRb05odDYxWFZSekQlMkZIbVBMUHhRbzVZNGtXdyUzRCUzRA",
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # id="board_search" 안의 ul.search_result_list 찾기
        search_result_list = soup.find("div", {"id": "board_search"}).find("ul", {"class": "search_result_list"})
        if not search_result_list:
            print(f"No search results found on page {page}")
            return []

        # li 태그 내 a 태그의 href 값 추출
        links = []
        for item in search_result_list.find_all("li", {"class": "search_result_item"}):
            link_element = item.find("a", {"class": "title text_over"})
            if link_element and link_element.get("href"):
                links.append(link_element["href"])

        return links

    except Exception as e:
        print(f"Error processing page {page}: {e}")
        return []

# 메인 크롤링 함수
def get_links(query, start_page=1):
    all_links = set()  # 중복 제거를 위해 set 사용
    page = start_page

    while True:
        print(f"page : {page}...")
        links = extract_links_from_page(query, page)
        print(f'links len : {len(links)}')
        if not links:  # 더 이상 결과가 없으면 중단
            print(f"No more results on page {page}. Stopping.")
            break

        # 새로 가져온 링크를 set에 추가
        all_links.update(links)
        page += 1
        time.sleep(random.uniform(2, 3))

    # 최종 결과를 list로 변환
    all_links = list(all_links)

    print("Crawling complete.")
    print(f'all_links : {all_links}')
    print(f'all_links len : {len(all_links)}')
    return all_links


# 스크린샷 폴더 설정
IMAGE_FOLDER = "ruriweb_image_list"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# 드라이버 세팅
def setup_driver():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--headless")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
            '''
        })
        driver.maximize_window()

        return driver
    except Exception as e:
        print(f"Error setting up the WebDriver: {e}")
        return None


# 전체 페이지 스크린샷 캡처
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
        final_path = f"{file_path}_full.png"
        stitched_image.save(final_path)
        print(f"Full page screenshot saved: {final_path}")
        return final_path

    except Exception as e:
        print(f"Error capturing full page screenshot: {e}")
        return None

def extract_and_format(url):
    # 정규 표현식을 사용해 숫자 부분 추출
    match = re.search(r'board/(\d+)/read/(\d+)', url)
    if match:
        board_id = match.group(1)
        read_id = match.group(2)
        return f"{board_id}_{read_id}"
    else:
        return None


# 페이지 데이터 추출 함수
def extract_page_data(driver, url, keyword):
    try:
        driver.get(url)
        time.sleep(3)

        # 댓글 데이터 추출
        comments = []

        # 공통 데이터 추출
        page_data = {
            "사이트": "루리웹",
            "글번호": extract_and_format(url),
            "제목": "",
            "내용": "",
            "아이디": "",
            "작성일": "",
            "키워드": keyword,
            "url": url,
            "스크린샷": "",
        }

        # 제목, 내용, 사용자 정보 추출
        try:
            page_data["제목"] = driver.find_element(By.CLASS_NAME, "subject_inner_text").text
            page_data["내용"] = driver.find_element(By.TAG_NAME, "article").text

            # 키워드가 "신지수"인 경우 금지된 키워드 필터링
            forbidden_keywords = ["병신지수", "혁신지수", "여신지수"]
            if keyword == "신지수":
                found_keywords = [forbidden for forbidden in forbidden_keywords
                                  if forbidden in page_data["제목"] or forbidden in page_data["내용"]]
                if found_keywords:
                    print(f"found_keywords : {found_keywords}")
                    return []  # 금지된 키워드가 포함되어 있으면 빈 리스트 반환

            # 내용 자르기 (Excel 셀 최대 크기 제한 처리)
            max_cell_length = 32767  # Excel 셀의 최대 문자 크기
            if len(page_data["내용"]) > max_cell_length:
                print(f"Content too long, trimming to {max_cell_length} characters.")
                page_data["내용"] = page_data["내용"][:max_cell_length]  # 내용 자르기

            user_info = driver.find_element(By.CLASS_NAME, "user_info_wrapper")
            page_data["아이디"] = user_info.find_element(By.CLASS_NAME, "nick").text
            page_data["작성일"] = user_info.find_element(By.CLASS_NAME, "regdate").text
        except NoSuchElementException as e:
            print(f"Error extracting main data: {e}")
            page_data.update({
                "리플 번호": "",
                "리플 아이디": "",
                "리플 내용": "",
                "리플 날짜": ""
            })
            print(f"obj : {page_data}")
            comments.append(page_data)
            return comments

        # 스크린샷 저장

        formatted_timestamp = page_data["작성일"].replace(":", "시", 1).replace(":", "분", 1) + "초"
        screenshot_path = os.path.join(IMAGE_FOLDER, f'{formatted_timestamp}({page_data["글번호"]}).png')
        full_screenshot_path = capture_full_page_screenshot(driver, screenshot_path)
        page_data["스크린샷"] = full_screenshot_path

        try:
            comment_rows = driver.find_elements(By.CSS_SELECTOR, ".comment_table tbody tr")
            if not comment_rows:  # 댓글이 없을 경우
                # 리플 데이터가 없으면 빈 값으로 하나의 배열을 리턴
                page_data.update({
                    "리플 번호": "",
                    "리플 아이디": "",
                    "리플 내용": "",
                    "리플 날짜": ""
                })
                comments.append(page_data)
                print(f"obj : {page_data}")
                return comments
            else:
                for idx, row in enumerate(comment_rows, start=1):
                    comment_data = {"리플 번호": idx}

                    try:
                        comment_data["리플 아이디"] = row.find_element(By.CLASS_NAME, "nick_link").text
                    except NoSuchElementException:
                        comment_data["리플 아이디"] = ""

                    try:
                        comment_data["리플 내용"] = row.find_element(By.CLASS_NAME, "text").text
                    except NoSuchElementException:
                        comment_data["리플 내용"] = ""

                    try:
                        comment_data["리플 날짜"] = row.find_element(By.CLASS_NAME, "time").text
                    except NoSuchElementException:
                        comment_data["리플 날짜"] = ""

                    obj = {**page_data, **comment_data}
                    print(f"obj : {obj}")
                    # 공통 데이터 병합
                    comments.append(obj)
                return comments
        except NoSuchElementException as e:
            print(f"Error extracting main data: {e}")
            page_data.update({
                "리플 번호": "",
                "리플 아이디": "",
                "리플 내용": "",
                "리플 날짜": ""
            })
            print(f"obj : {page_data}")
            comments.append(page_data)
            return comments

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return []


def save_or_append_to_excel(data, filename="ruliweb_results.xlsx"):
    df = pd.DataFrame(data)

    try:
        # 기존 파일이 있을 경우 데이터를 추가
        with pd.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            workbook = load_workbook(filename)
            sheet_name = workbook.sheetnames[0]  # 첫 번째 시트 이름 가져오기
            # 기존 데이터의 마지막 행 번호 계산
            if writer.sheets.get(sheet_name):
                startrow = writer.sheets[sheet_name].max_row
            else:
                startrow = 0
            # 데이터 추가
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=startrow)
            print(f"Data successfully appended to {filename}")
    except FileNotFoundError:
        # 파일이 없을 경우 새 파일 생성
        df.to_excel(filename, index=False)
        print(f"New file created: {filename}")

# 실행
if __name__ == "__main__":
    keywords = [
        "마공스시",
        "읍읍스시",
        "마공읍읍",
        "ㅁㄱㅅㅅ",
        "ㅁㄱ스시",
        "신지수",
        # "ㅅㅈㅅ",
        "보일러집 아들",
        "대열보일러",
        "project02",
        "버블트리"
    ]

    # 병신지수 혁신지수 여신지수

    driver = setup_driver()

    all_result_links = set()  # 중복 제거를 위해 set 사용

    if not driver:
        print("Driver setup failed!")
        exit()

    try:
        for index, keyword in enumerate(keywords, start=1):
            print(f"index: {index}/{len(keywords)}, keyword: {keyword}")
            result_links = get_links(keyword)

            if not result_links:
                continue

            # result_links에서 all_result_links와 중복된 것 제거
            unique_links = [link for link in result_links if link not in all_result_links]
            print(f"unique_links len : {len(unique_links)}")
            # all_result_links에 고유 링크 추가
            all_result_links.update(unique_links)

            results = []
            for idx, link in enumerate(unique_links, start=1):  # 중복 제거된 unique_links 사용
                print(f'keyword: {keyword} ({index}/{len(keywords)}), links: ({idx}/{len(unique_links)})')
                data = extract_page_data(driver, link, keyword)
                if data:
                    results.extend(data)

            # 엑셀 저장 또는 추가
            print(f'results len : {len(results)}')
            if results:
                save_or_append_to_excel(results)

    finally:
        driver.quit()