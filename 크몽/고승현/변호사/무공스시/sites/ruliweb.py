import requests
import os
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from util.common import extract_and_format, capture_full_page_screenshot, make_dir, excel_max_cut


# 페이지에서 링크 추출
def extract_links_ruriweb(driver, keyword, page):
    try:
        url = f"https://bbs.ruliweb.com/search?q={keyword}&op=&page={page}#board_search&gsc.tab=0&gsc.q={keyword}&gsc.page=1"
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


# 내용 추출
def extract_contents_ruriweb(driver, site, keyword, link, forbidden_keywords):
    try:
        # 폴더 경로 생성
        make_dir(site)

        driver.get(link)
        time.sleep(3)

        # 댓글 데이터 추출
        comments = []

        # 공통 데이터 추출
        page_data = {
            "사이트": site,
            "글번호": extract_and_format(site, link),
            "제목": "",
            "내용": "",
            "아이디": "",
            "작성일": "",
            "키워드": keyword,
            "url": link,
            "스크린샷": "",
        }

        # 제목 추출
        try:
            title = driver.find_element(By.CLASS_NAME, "subject_inner_text").text
            page_data["제목"] = title
        except NoSuchElementException:
            page_data["제목"] = ""

        # 내용 추출
        try:
            content = driver.find_element(By.TAG_NAME, "article").text
            page_data["내용"] = excel_max_cut(content)
        except NoSuchElementException:
            page_data["내용"] = ""

        # 키워드가 "신지수"인 경우 금지된 키워드 필터링
        if keyword == "신지수":
            found_keywords = [forbidden for forbidden in forbidden_keywords
                              if forbidden in page_data["제목"] or forbidden in page_data["내용"]]
            if found_keywords:
                print(f"found_keywords : {found_keywords}")
                return []  # 금지된 키워드가 포함되어 있으면 빈 리스트 반환

        try:
            user_info = driver.find_element(By.CLASS_NAME, "user_info_wrapper")
            date = user_info.find_element(By.CLASS_NAME, "regdate").text
            page_data["작성일"] = date
            user_id = user_info.find_element(By.CLASS_NAME, "nick").text
            page_data["아이디"] = user_id
        except NoSuchElementException:
            page_data["작성일"] = ""
            page_data["아이디"] = ""

        # 스크린샷 저장
        formatted_timestamp = page_data["작성일"].replace(":", "시", 1).replace(":", "분", 1) + "초"
        screenshot_path = os.path.join(f'{site}_image_list', f'{formatted_timestamp}({page_data["글번호"]})')
        full_screenshot_path = capture_full_page_screenshot(driver, screenshot_path)
        page_data["스크린샷"] = full_screenshot_path

        # 리플 데이터 추출
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
                # 리플이 있다면 기존 로직대로 처리
                for idx, comment in enumerate(comment_rows, start=1):
                    comment_data = {"리플 번호": idx}

                    try:
                        comment_data["리플 아이디"] = comment.find_element(By.CLASS_NAME, "nick_link").text
                    except NoSuchElementException:
                        comment_data["리플 아이디"] = ""

                    try:
                        comment_data["리플 날짜"] = comment.find_element(By.CLASS_NAME, "time").text
                    except NoSuchElementException:
                        comment_data["리플 날짜"] = ""

                    try:
                        comment_data["리플 내용"] = comment.find_element(By.CLASS_NAME, "text").text
                    except NoSuchElementException:
                        comment_data["리플 내용"] = ""

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
        print(f"Error processing {link}: {e}")
        return []
