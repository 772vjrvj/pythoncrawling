import requests
import os
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from util.common import extract_and_format, capture_full_page_screenshot, make_dir, excel_max_cut


def extract_links_arcalive(driver, keyword, page):
    try:
        url = f'https://arca.live/b/breaking?keyword={keyword}&p={page}'
        print(f"Fetching URL: {url}")
        headers = {
            "authority": "arca.live",
            "method": "GET",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "cookie": "_sharedid=e4b3d565-87b3-4f57-8d09-cd9ff8392b93; _sharedid_cst=zix7LPQsHA%3D%3D; _lr_env_src_ats=false; _ga=GA1.1.698925934.1731785623; _au_1d=AU1D-0100-001731785623-UEJCV9QC-QMB9; arca.nick=%E3%85%87%E3%85%87; arca.nick.sig=ETcGz1yS4GbrdOJZZg18BIpnFrg; arca.password=KinjoEgL; arca.password.sig=uy3DCL6W45baJO-eI2UNfLA3UvQ; visited-channel=[{%22name%22:%22%EC%A2%85%ED%95%A9%20%EC%86%8D%EB%B3%B4%22%2C%22slug%22:%22breaking%22}]; campaign.session=s%3ArjAoc2WMdIxHfaRRrDORTLNX9zc0czIz.fkf4Z%2FFMjln%2FLLz1SiZo3m5QqWyQm90jFxACLCUVMaY; _lr_retry_request=true; arca.csrf=-QznQ9id3ajsLFv0AlN_k4jE; arca.csrf.sig=HIvL_2GHENskn7NoSadIsLXrlpM; _ga_EVNC8JD9DJ=GS1.1.1731820998.2.1.1731821128.0.0.0; cto_bundle=V8A0pF9pRXA0c21DeUxuMHR0alF5OUhXd28zWVR0WkJ1UFMxR29rMDNydFNYRVhsTTBCcWZtY2pCNEFwZmc1S0FwODBDU3hqVktjdXVQMVpTR25uVzhqRmxEbFhQTVclMkJLOXV6Q3FMRE8yN0k1T3BRVmdpTHlNRkslMkIyTnRwd0pyYzhjQUtJak00dERLUXNvaWU3UGV6eEhNUHh3JTNEJTNE; cto_bidid=VEn6nl9lJTJGRWc1Wm90QkJobWtJbmYlMkJLd2R0aXJtSEY2TWpjd0FHUEdHTzFvaERtQlR3Mm9CWlBTb1hhQzY4TDczTjIzTjlRdHZQb2pvZVd5OVpFMFVGVzlGa3c1TXJWWVlMVDVxSmh0WU9OSFNSMTAlM0Q",
            "priority": "u=0, i",
            "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            "sec-ch-ua-arch": "x86",
            "sec-ch-ua-bitness": "64",
            "sec-ch-ua-full-version": "130.0.6723.119",
            "sec-ch-ua-full-version-list": '"Chromium";v="130.0.6723.119", "Google Chrome";v="130.0.6723.119", "Not?A_Brand";v="99.0.0.0"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": "",
            "sec-ch-ua-platform": "Windows",
            "sec-ch-ua-platform-version": "10.0.0",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 조건에 맞는 a 태그 찾기
        # 사실 아래 조건만으로도 이미 notice와 notice-service는 제외됨
        a_tags = soup.find_all("a", class_="vrow column")

        links = []
        if a_tags:
            for tag in a_tags:
                # class 속성 가져오기
                classes = tag.get("class", [])

                # 'notice'와 'notice-service'가 포함되지 않은 경우 href 추출
                if "notice" not in classes and "notice-service" not in classes:
                    href = tag.get("href")
                    if href:
                        links.append(f"https://arca.live{href}")

        return links

    except Exception as e:
        print(f"Error processing page {page}: {e}")
        return []


# 페이지 데이터 추출 함수
def extract_contents_arcalive(driver, site, keyword, link, forbidden_keywords):
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

        article_head = ""
        try:
            article_head = driver.find_element(By.CLASS_NAME, "article-head")
        except NoSuchElementException:
            page_data["제목"] = ""
            page_data["작성일"] = ""
            page_data["아이디"] = ""

        # 제목 추출
        try:
            # 제목
            title_row = article_head.find_element(By.CLASS_NAME, "title-row")
            title_div = title_row.find_element(By.CLASS_NAME, "title")

            # span 태그를 제외한 텍스트만 추출
            spans = title_div.find_elements(By.TAG_NAME, "span")

            # span 태그 내부 텍스트는 제외하고 나머지 텍스트 추출
            text = title_div.text.strip()

            # span 태그 텍스트를 제외한 부분을 반환
            for span in spans:
                text = text.replace(span.text, "").strip()

            page_data["제목"] = text
        except NoSuchElementException:
            page_data["제목"] = ""

        info_row = ""
        try:
            # 아이디
            info_row = article_head.find_element(By.CLASS_NAME, "info-row")
        except NoSuchElementException:
            page_data["아이디"] = ""
            page_data["작성일"] = ""

        try:
            # 아이디
            page_data["아이디"] = info_row.find_element(By.CLASS_NAME, "user-info").text
        except NoSuchElementException:
            page_data["아이디"] = ""

        try:
            # 작성일
            date_element = info_row.find_element(By.CLASS_NAME, "date")
            page_data["작성일"] = date_element.find_element(By.TAG_NAME, 'time').text
        except NoSuchElementException:
            page_data["작성일"] = ""

        try:
            # 아이디
            page_data["내용"] = driver.find_element(By.CLASS_NAME, "article-body").text
        except NoSuchElementException:
            page_data["내용"] = ""

        # 키워드가 "신지수"인 경우 금지된 키워드 필터링
        if keyword == "신지수":
            found_keywords = [forbidden for forbidden in forbidden_keywords
                              if forbidden in page_data["제목"] or forbidden in page_data["내용"]]
            if found_keywords:
                print(f"found_keywords : {found_keywords}")
                return []  # 금지된 키워드가 포함되어 있으면 빈 리스트 반환

        # 스크린샷 저장
        formatted_timestamp = page_data["작성일"].replace(":", "시", 1).replace(":", "분", 1) + "초"
        screenshot_path = os.path.join(f'{site}_image_list', f'{formatted_timestamp}({page_data["글번호"]})')
        full_screenshot_path = capture_full_page_screenshot(driver, screenshot_path)
        page_data["스크린샷"] = full_screenshot_path



        try:
            # 두 번째 class="commentList1"을 찾기
            list_area = driver.find_element(By.CLASS_NAME, "list-area")
            comment_item_list = list_area.find_elements(By.CLASS_NAME, "comment-item")

            if not comment_item_list:  # 댓글이 없을 경우
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
                for idx, item in enumerate(comment_item_list, start=1):
                    comment_data = {"리플 번호": idx}

                    try:
                        # 리플 아이디 추출
                        reply_user_info = item.find_element(By.CLASS_NAME, "user-info")
                        comment_data["리플 아이디"] = reply_user_info.find_element(By.TAG_NAME, 'a').text
                    except NoSuchElementException:
                        comment_data["리플 아이디"] = ""

                    try:
                        # 리플 내용 추출
                        comment_data["리플 내용"] = item.find_element(By.CLASS_NAME, "text").text
                    except NoSuchElementException:
                        comment_data["리플 내용"] = ""

                    try:
                        # 리플 날짜 추출
                        comment_data["리플 날짜"] = item.find_element(By.TAG_NAME, 'time').text
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
