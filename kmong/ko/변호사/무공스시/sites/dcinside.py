import os
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from util.common import extract_and_format, capture_full_page_screenshot, make_dir, excel_max_cut
import requests
from bs4 import BeautifulSoup

# 페이지에서 링크 추출
def extract_links_dcinside(driver, keyword, page):
    try:
        url = f"https://search.dcinside.com/post/p/{page}/q/{keyword}"
        print(f"Fetching URL: {url}")
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "connection": "keep-alive",
            "host": "search.dcinside.com",
            "cookie": "__eoi=ID=447bb757f245d257:T=1722534276:RT=1722534276:S=AA-AfjZg-nhXpRRQfM6-QCneCwJY; adfit_sdk_id=b79b5c3f-8ed6-4ed9-8586-09f1f5d0c8f8; ck_l_f=l; _ga_H4ZNE3RQBN=GS1.1.1722534276.1.1.1722534340.0.0.0; PHPSESSID=69ac2c87ab15f9959f90ab6fd4c70bec; __utma=118540316.619499823.1722534276.1722534276.1734170371.2; __utmc=118540316; __utmz=118540316.1734170371.2.2.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); csid=0521ab7b80be21aae472f62c600dd5cc013316cd685384c6c6b735ab420fe0bb38975205ef3f32; _ga_45WM05PS9D=GS1.1.1734170371.1.1.1734170382.0.0.0; _gid=GA1.2.1333048155.1734170383; last_alarm=1734170484; ck_img_view_cnt=4; _ga_M13K6V9PME=GS1.1.1734170499.1.0.1734170501.0.0.0; ci_c=ca90996f3fed7b769b20b96a1da2e889; cto_bundle=ZWrhfl91VGhkdlY1R3U1dmN0S1k1QnR5YTh0NGFNOXlra016RXBoU1JkdnRvRFN6NUhqNVAybW8lMkZiMEs2ZFBqOGMlMkZRU203QmozdWczdVZoJTJCZ20wTXNEUFp3ZFFRcmdObE1JMlFnSXc2dEN2eXd6TlZWV0ZoM21tck81TGdYbkViUFhDVzdTZ0NpbzJhUTVnR1gyJTJGcmlLMlJIMHFxaW5xSXVaV29NOTdZeHhHcURlUkV6b2VNMVpOSE5YOFl5WWNoNzVac1p0YUtYT1pDTUdFSlA3MGVBSEFZOFElM0QlM0Q; _ga_HNDXQK2FQ7=GS1.1.1734170508.1.0.1734170514.0.0.0; _ga_03JSGF9S2P=GS1.1.1734170508.1.0.1734170514.0.0.0; _ga_NWM777QSMB=GS1.1.1734170508.1.0.1734170514.0.0.0; ck_lately_gall=w2%7CdKs%7Cb2g%7C3DA%7C53A; gallRecom=MjAyNC0xMi0xNCAxOTowNzowMS8wZGUxNGJlYzU2MWQ5YjdjNmU0NDI3OTY1YTEyOGE0MGI5M2RlMDdiNWIyZWVhMjc1ZmVmNGQ4NDk0NGNkNDhl; service_code=21ac6d96ad152e8f15a05b7350a2475909d19bcedeba9d4face8115e9bc0fc4e4360a8433691e34a8500aeb9d6dd536d9b25a698a6aeda002dc306f6758ea5282518e46194ee62863e9c628b9b8069800976c3e163593b45d798d0bb47cfd84d9e4ca1dba84b60c431cfc228a7489b9cec2af4251d5043aa4e954d81e51f0971e1d0678c2473e2f5925f0b72779d0937842ee31de59747a0bec24484d74ecce44ff02aeba05db43ac26c5d791e4ed0611924661e4f9d375d0677743716292be4e405975185350c35; __utmb=118540316.11.10.1734170371; _ga_8LH47K4LPZ=GS1.1.1734170474.2.1.1734170825.0.0.0; _ga_NJF9PXZD5K=GS1.1.1734170371.2.1.1734170825.57.0.0; _ga_M2T5NMSZ9V=GS1.1.1734170475.1.1.1734170825.57.0.0; _gat=1; _gat_gtag_UA_5149721_4=1; _ga=GA1.1.619499823.1722534276; _ga_V46B0SHSY7=GS1.1.1734170383.3.1.1734171737.0.0.0",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        search_result_list = soup.find("ul", {"class": "sch_result_list"})
        if not search_result_list:
            print(f"No search results found on page {page}")
            return []

        # li 태그 내 a 태그의 href 값 추출
        links = []
        for item in search_result_list.find_all("li", recursive=False):
            link_element = item.find("a", {"class": "tit_txt"})
            if link_element and link_element.get("href"):
                links.append(link_element["href"])

        return links

    except Exception as e:
        print(f"Error processing page {page}: {e}")
        return []



# 페이지에서 데이터 추출
def extract_contents_dcinside(driver, keyword, site, link, forbidden_keywords):
    try:
        # 폴더 경로 생성
        make_dir(site)

        driver.get(link)
        time.sleep(3)  # 페이지 로딩 대기

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
            "아이디 상태": "고정닉",
        }

        # 제목 추출
        try:
            title_headtext = driver.find_element(By.CSS_SELECTOR, "span.title_headtext").text
            title_subject = driver.find_element(By.CSS_SELECTOR, "span.title_subject").text

            page_data["제목"] = title_headtext + title_subject
        except NoSuchElementException:
            page_data["제목"] = ""

        # 내용 추출
        try:
            content = driver.find_element(By.CSS_SELECTOR, "div.writing_view_box").text
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
            # 부모 요소 찾기
            parent_element = driver.find_element(By.CLASS_NAME, "gallview_head")  # 부모 클래스

            # 부모 안에서 특정 span 요소 찾기
            gall_date_element = parent_element.find_element(By.CSS_SELECTOR, "span.gall_date")

            # 텍스트 추출
            gall_date_text = gall_date_element.text

            page_data["작성일"] = gall_date_text
        except NoSuchElementException:
            page_data["작성일"] = ""

        # 아이디 추출
        try:
            parent_element = driver.find_element(By.CLASS_NAME, "gallview_head")  # 부모 클래스

            # 닉네임 추출
            nickname = parent_element.find_element(By.CSS_SELECTOR, "span.nickname")
            name = nickname.text

            # IP가 있는 경우만 추가
            try:
                ip = parent_element.find_element(By.CSS_SELECTOR, "span.ip")
                page_data["아이디 상태"] = "유동닉"
                name += ip.text
            except NoSuchElementException:
                pass  # IP가 없을 경우 아무 작업도 하지 않음

            page_data["아이디"] = name
        except NoSuchElementException:
            page_data["아이디"] = ""


        date, tm = page_data["작성일"].split(' ')  # 날짜와 시간을 분리
        hour, minute = tm.split(":")  # 시간을 ":"로 분리
        formatted_timestamp = f"{date} {hour}시{minute}분"
        screenshot_path = os.path.join(f'{site}_image_list', f'{formatted_timestamp}({page_data["글번호"]})')
        full_screenshot_path = capture_full_page_screenshot(driver, screenshot_path)
        page_data["스크린샷"] = full_screenshot_path

        # 리플 데이터 추출
        try:
            comment_rows = driver.find_elements(By.CSS_SELECTOR, "ul.cmt_list > li")
            if not comment_rows:  # 리플이 없다면
                # 리플 데이터가 없으면 빈 데이터로 하나의 배열을 리턴
                page_data.update({
                    "리플 번호": "",
                    "리플 아이디": "",
                    "리플 날짜": "",
                    "리플 내용": ""
                })
                comments.append(page_data)
                print(f"obj : {page_data}")
                return comments
            else:
                # 리플이 있다면 기존 로직대로 처리
                for idx, comment in enumerate(comment_rows, start=1):
                    comment_data = {"리플 번호": idx}

                    try:
                        comment_data["리플 아이디"] = comment.find_element(By.CSS_SELECTOR, "span.nickname").text
                    except NoSuchElementException:
                        comment_data["리플 아이디"] = ""

                    # 리플 날짜
                    try:
                        comment_data["리플 날짜"] = comment.find_element(By.CSS_SELECTOR, "span.date_time").text
                    except NoSuchElementException:
                        comment_data["리플 날짜"] = ""

                    # 리플 내용
                    try:
                        # 댓글 내용 전체 추출
                        comment_content = comment.find_element(By.CSS_SELECTOR, "p.usertxt.ub-word")

                        # findParent 안의 내용 추출
                        try:
                            # 댓글 본문에서 findParent 텍스트 제거
                            full_comment_text = comment_content.text.strip()
                        except NoSuchElementException:
                            full_comment_text = comment_content.text.strip()
                        # 댓글 내용 추가
                        comment_data["리플 내용"] = full_comment_text
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

