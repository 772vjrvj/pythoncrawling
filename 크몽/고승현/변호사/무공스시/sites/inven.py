import requests
import os
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from util.common import extract_and_format, capture_full_page_screenshot, make_dir, excel_max_cut


# 페이지에서 링크 추출
def extract_links_inven(driver, keyword, page):
    try:
        url = f'https://www.inven.co.kr/search/webzine/article/{keyword}/{page}'
        print(f"Fetching URL: {url}")
        headers = {
            'authority': 'www.inven.co.kr',
            'method': 'GET',
            'scheme': 'https',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'cookie': 'OAX=2pOE7Gc48vgADVAa; _fwb=139MSl6E6DfQ2lfW1GBv8KU.1731785466460; a1_gid=2pOE7GcG/NMAC9Ch; a1_sgid=2pOE7GcG/NMAC9Ch1731785466907; _ga=GA1.1.2050071318.1731785467; _clck=1k33mp8%7C2%7Cfqx%7C0%7C1781; inven_link=stream; VISIT_SITE=webzine%7Cgirlsfrontline; invenrchk=%7B%225078%7C290350%22%3A%7B%22d%22%3A%222024-11-17%2004%3A33%3A22%22%2C%22s%22%3Anull%7D%2C%222097%7C2027852%22%3A%7B%22d%22%3A%222024-11-17%2004%3A53%3A46%22%2C%22s%22%3Anull%7D%7D; topskyCnt=36; _ga_K8NJQS78X7=GS1.1.1731785467.1.1.1731788734.0.0.0; _ga_P0BBTC1DR3=GS1.1.1731785466.1.1.1731788734.59.0.0; wcs_bt=105811aa1e895d:1731788734; _clsk=1ha1idj%7C1731788734991%7C33%7C0%7Cx.clarity.ms%2Fcollect; cto_bundle=5g4suV9iemRkZFpEVTcwQnlCbWczJTJGSWNNS3pMa0V6eXVuTjM2UWdhTlJONHpZMkMxdEtQTm84Y29ocUIwMkFMWDJLdk9yZ2ZBMGdwbGQ5UFN3JTJCdmo5emlDdkFkdFVsTFJWRVhCb210MkppJTJCVGdEOFhqUnN1N1RuaG5xZnJXbFFKUTJZSGx1cXJXVXBuUjNDNFRuako5JTJGYXZpaEZkNlBDdldwZVVKZVB2OVBZRGhldTl0MGNycmpQNVpBRVBBcnRKZDhBaWVWZ1NlU2VkT29WZkZJenhvMWxKWWclM0QlM0Q',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        search_result_list = soup.find('ul', class_='news_list')
        if not search_result_list:
            print(f"No search results found on page {page}")
            return []

        # li 태그 내 a 태그의 href 값 추출
        links = []
        li_elements = search_result_list.find_all('li')
        for li in li_elements:
            h1_tag = li.find('h1')
            if h1_tag:
                a_tag = h1_tag.find('a')
                if a_tag:
                    href = a_tag.get('href')
                    links.append(href)

        return links

    except Exception as e:
        print(f"Error processing page {page}: {e}")
        return []


# 내용 추출
def extract_contents_inven(driver, site, keyword, link, forbidden_keywords):
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
            page_data["제목"] = driver.find_element(By.CLASS_NAME, "articleTitle").text
        except NoSuchElementException:
            page_data["제목"] = ""

        # 내용 추출
        try:
            content = driver.find_element(By.ID, "powerbbsContent").text
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

        article_info = ""
        # 내용 추출
        try:
            article_info = driver.find_element(By.CLASS_NAME, "articleInfo")
        except NoSuchElementException:
            page_data["아이디"] = ""
            page_data["작성일"] = ""

        # 제목 추출
        try:
            page_data["아이디"] = article_info.find_element(By.CLASS_NAME, "articleWriter").text
        except NoSuchElementException:
            page_data["아이디"] = ""

        # 제목 추출
        try:
            page_data["작성일"] = article_info.find_element(By.CLASS_NAME, "articleDate").text
        except NoSuchElementException:
            page_data["작성일"] = ""

        # 스크린샷 저장
        date, tm = page_data["작성일"].split()  # 날짜와 시간을 분리
        hour, minute = tm.split(":")  # 시간을 ":"로 분리
        formatted_timestamp = f"{date} {hour}시{minute}분"

        screenshot_path = os.path.join(f'{site}_image_list', f'{formatted_timestamp}({page_data["글번호"]})')
        full_screenshot_path = capture_full_page_screenshot(driver, screenshot_path)
        page_data["스크린샷"] = full_screenshot_path


        try:
            # 두 번째 class="commentList1"을 찾기
            comment_lists = driver.find_elements(By.CLASS_NAME, "commentList1")

            if len(comment_lists) < 2:
                print("두 번째 commentList1이 없습니다.")

                page_data.update({
                    "리플 번호": "",
                    "리플 아이디": "",
                    "리플 내용": "",
                    "리플 날짜": ""
                })
                print(f"obj : {page_data}")
                comments.append(page_data)

                return comments

            # 두 번째 commentList1에서 ul -> li를 찾아서 댓글 추출
            second_comment_list = comment_lists[1]

            comment_items = []

            # ul 태그가 존재하는지 확인
            ul_elements = second_comment_list.find_elements(By.TAG_NAME, "ul")
            if len(ul_elements) > 0:
                # ul이 존재하면 그 안에서 li 태그 찾기
                li_elements = ul_elements[0].find_elements(By.TAG_NAME, "li")
                if len(li_elements) > 0:
                    comment_items = li_elements


            if not comment_items:  # 댓글이 없을 경우
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
                for idx, item in enumerate(comment_items, start=1):
                    comment_data = {"리플 번호": idx}

                    try:
                        # 리플 아이디 추출
                        comment_data["리플 아이디"] = item.find_element(By.CLASS_NAME, "nickname").text
                    except NoSuchElementException:
                        comment_data["리플 아이디"] = ""

                    try:
                        # 리플 내용 추출
                        comment_data["리플 내용"] = item.find_element(By.CLASS_NAME, "content.cmtContentOne").text
                    except NoSuchElementException:
                        comment_data["리플 내용"] = ""

                    try:
                        # 리플 날짜 추출
                        comment_data["리플 날짜"] = item.find_element(By.CLASS_NAME, "date").text
                    except NoSuchElementException:
                        comment_data["리플 날짜"] = ""

                    # 공통 데이터 병합
                    obj = {**page_data, **comment_data}
                    print(f"obj : {obj}")
                    comments.append(obj)
                return comments

        except NoSuchElementException as e:
            print(f"Error extracting comments: {e}")
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

