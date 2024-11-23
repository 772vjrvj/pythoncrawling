import os
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from util.common import extract_and_format, capture_full_page_screenshot, make_dir, excel_max_cut

# 페이지에서 링크 추출
def extract_links_fmkorea(driver, keyword, page):
    try:
        base_url = "https://www.fmkorea.com/search.php"
        params = f"?act=IS&is_keyword={keyword}&mid=home&where=document&page={page}"
        url = base_url + params
        driver.get(url)
        time.sleep(3)  # 페이지 로딩 대기

        # 검색 결과 링크 추출
        search_results = driver.find_elements(By.CSS_SELECTOR, "ul.searchResult > li > dl > dt > a")
        if not search_results:
            return []

        # 링크 추출
        links = [link.get_attribute("href").split("/")[-1] for link in search_results]
        return links

    except Exception as e:
        print(f"Error extracting links: {e}")
        return []


# 페이지에서 데이터 추출
def extract_contents_fmkorea(driver, site, keyword, link, forbidden_keywords):
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
        }

        # 제목 추출
        try:
            title = driver.find_element(By.CSS_SELECTOR, "span.np_18px_span").text
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
            page_data["작성일"] = driver.find_element(By.CSS_SELECTOR, "span.date.m_no").text
        except NoSuchElementException:
            page_data["작성일"] = ""

        # 아이디 추출
        try:
            page_data["아이디"] = driver.find_element(By.CSS_SELECTOR, "a[href='#popup_menu_area']").text
        except NoSuchElementException:
            page_data["아이디"] = ""

        # 스크린샷 저장
        formatted_timestamp = page_data["작성일"].replace(":", "시", 1).replace(":", "분", 1) + "초"
        screenshot_path = os.path.join(f'{site}_image_list', f'{formatted_timestamp}({page_data["글번호"]})')
        full_screenshot_path = capture_full_page_screenshot(driver, screenshot_path)
        page_data["스크린샷"] = full_screenshot_path

        # 리플 데이터 추출
        try:
            comment_rows = driver.find_elements(By.CSS_SELECTOR, "ul.fdb_lst_ul > li")
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
                        comment_data["리플 아이디"] = comment.find_element(By.CSS_SELECTOR, "div.meta a").text
                    except NoSuchElementException:
                        comment_data["리플 아이디"] = ""

                    # 리플 날짜
                    try:
                        comment_data["리플 날짜"] = comment.find_element(By.CSS_SELECTOR, "div.meta .date").text
                    except NoSuchElementException:
                        comment_data["리플 날짜"] = ""

                    # 리플 내용
                    try:
                        # 댓글 내용 전체 추출
                        comment_content = comment.find_element(By.CSS_SELECTOR, "div.comment-content .xe_content")

                        # findParent 안의 내용 추출
                        try:
                            find_parent_text = comment_content.find_element(By.CSS_SELECTOR, "a.findParent").text
                            reply_content = f"@{find_parent_text}<-"

                            # 댓글 본문에서 findParent 텍스트 제거
                            full_comment_text = comment_content.text
                            full_comment_text = full_comment_text.replace(find_parent_text, "", 1).strip()
                        except NoSuchElementException:
                            reply_content = ""
                            full_comment_text = comment_content.text.strip()

                        # 댓글 내용 추가
                        reply_content += full_comment_text
                        comment_data["리플 내용"] = reply_content
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

