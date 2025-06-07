import os
import time
import pyautogui
import pyperclip
import urllib.parse
from bs4 import BeautifulSoup
import re
import pandas as pd

import os
import subprocess
from src.utils.time_utils import get_current_yyyymmddhhmmss
import random
# ✅ 전역 변수 선언
current_url = ""
keyword = ""
page = 1
last_page = 2
result_list = []
result_list_index = 0
folder_path = ""
columns = ["상품명", "상호명","사업장소재지", "연락처", "URL", "키워드"]
excel_name = "쿠팡"
urls_list= []

def extract_last_page(soup):
    global last_page

    # ✅ class 속성이 'Pagination_pagination__'로 시작하는 요소 찾기
    pagination = soup.find('div', class_=re.compile(r'^Pagination_pagination__'))
    if not pagination:
        print("❌ 페이지네이션 영역을 찾을 수 없습니다.")
        return last_page

    page_numbers = []
    for a_tag in pagination.find_all('a', attrs={'data-page': True}):
        title = a_tag.get('title', '')
        if title not in ['이전', '다음']:
            try:
                page_num = int(a_tag['data-page'])
                page_numbers.append(page_num)
            except ValueError:
                continue

    if page_numbers:
        last_page = max(page_numbers)
        print(f"✅ 마지막 페이지 번호 추출됨: {last_page}")
    else:
        print("❌ 유효한 페이지 번호를 찾지 못했습니다.")
    return last_page


def extract_product_urls(soup):
    base_url = "https://www.coupang.com"

    ul = soup.find('ul', id='product-list')
    if not ul:
        print("❌ 'product-list' UL 태그를 찾을 수 없습니다.")
        return []

    urls = set()

    for li in ul.find_all('li', attrs={"data-sentry-component": "ProductItem"}):
        a_tag = li.find('a', href=True)
        if a_tag:
            href = a_tag['href']
            if not href.startswith("http"):
                href = base_url + href
            urls.add(href)

    url_list = sorted(list(urls))

    print(f"\n✅ 총 {len(url_list)}개 상품 URL 추출됨:\n")
    return url_list

def crawl_once():
    global current_url, keyword, page, last_page, folder_path, result_list_index, urls_list

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # 페이지 로딩 및 HTML 저장
    pyautogui.moveTo(10, 10)
    pyautogui.click()
    time.sleep(0.5)

    pyautogui.hotkey('ctrl', 'l')
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.3)

    # URL 가져오기
    current_url = pyperclip.paste()
    print(f"📋 현재 URL: {current_url}")

    pyautogui.moveTo(300, 400)
    pyautogui.click()
    time.sleep(0.3)

    for _ in range(11):
        pyautogui.scroll(-1000)
        time.sleep(0.3)

    pyautogui.hotkey('ctrl', 'u')
    time.sleep(5)

    pyautogui.hotkey('ctrl', 'a')
    time.sleep(2)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(2)

    html_source = pyperclip.paste()
    print("HTML 길이:", len(html_source))
    print("시작부분:", html_source[:200])

    parsed = urllib.parse.urlparse(current_url)
    query = urllib.parse.parse_qs(parsed.query)
    keyword_encoded = query.get("q", [""])[0]
    page_str = query.get("page", ["1"])[0]

    keyword = urllib.parse.unquote(keyword_encoded)
    page = int(page_str)

    filename = f"쿠팡_{keyword}_{page}.html"
    save_path = os.path.join(folder_path, filename)

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(html_source)

    pyautogui.hotkey('ctrl', 'w')
    time.sleep(0.5)



    print(f"💾 저장 완료: {save_path}")

    with open(save_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    last_page = extract_last_page(soup)
    urls = extract_product_urls(soup)

    if urls_list and urls_list[-1] == urls:
        return False
    else:
        urls_list.append(urls)

    if os.path.exists(save_path):
        os.remove(save_path)
        print(f"🗑️ HTML 파일 삭제됨: {save_path}")

    for i, url in enumerate(urls, start=1):
        if i == 2:
            break
        result_list_index += 1
        data_detail(i, url)

    return True


def data_detail(i, url):
    global result_list, keyword, page, folder_path, excel_name
    print(f'i : {i}, url : {url}')
    # ✅ 브라우저에 URL 입력 후 이동
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(0.3)
    pyperclip.copy(url)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.3)
    pyautogui.press('enter')
    time.sleep(3)

    # ✅ 1단계: 아래 방향키로 30번 빠르게 스크롤
    for _ in range(20):
        pyautogui.press('pagedown')
        time.sleep(0.3)  # 살짝 빠르게, 자연스러운 스크롤

    # ✅ 2단계: 마지막에 스크롤 끝까지 내리기
    for _ in range(3):
        pyautogui.press('end')
        time.sleep(0.3)  # 로딩 대기 시간

    # ✅ HTML 복사
    pyautogui.hotkey('ctrl', 'u')
    time.sleep(random.uniform(4.5, 5.5))
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(random.uniform(1, 2))
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(random.uniform(2, 3))

    x = random.randint(100, 500)
    y = random.randint(100, 500)
    pyautogui.moveTo(x, y, duration=0.5)

    pyautogui.hotkey('ctrl', 'w')
    time.sleep(random.uniform(0.5, 1))

    html_source = pyperclip.paste()
    print("HTML 길이:", len(html_source))
    print("시작부분:", html_source[:200])

    # ✅ 파일 저장
    filename = f"쿠팡_{keyword}_{page}_{i}.html"
    save_path = os.path.join(folder_path, filename)

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(html_source)

    # ✅ 판매자 정보 추출
    soup = BeautifulSoup(html_source, 'html.parser')

    seller_info = {
        "상품명": "",
        "상호명": "",
        "사업장소재지": "",
        "연락처": "",
        "URL": url,
        "키워드": keyword
    }

    # ✅ 상품명 추출
    title_tag = soup.find("h1", attrs={"data-sentry-component": "ProductTitle"})
    if title_tag:
        seller_info["상품명"] = title_tag.get_text(strip=True)
    else:
        print("❌ 상품명을 찾을 수 없습니다.")

    # ✅ 판매자 정보 테이블 추출
    container = soup.find("div", class_="product-item__table product-seller")
    if container:
        table = container.find("table", class_=re.compile(r"prod-delivery-return-policy-table"))
        if table:
            rows = table.find_all("tr")
            for row in rows:
                ths = row.find_all("th")
                tds = row.find_all("td")

                for i in range(min(len(ths), len(tds))):
                    label = ths[i].get_text(strip=True)
                    value = tds[i].get_text(strip=True)

                    if "상호" in label:
                        seller_info["상호명"] = value
                    elif "소재지" in label:
                        seller_info["사업장소재지"] = value
                    elif "연락처" in label:
                        seller_info["연락처"] = value

    print(f'{get_current_yyyymmddhhmmss()} 연락처 : {seller_info["연락처"]}')
    print(f'{get_current_yyyymmddhhmmss()} 상품명 : {seller_info["상품명"]}')
    print(f'{get_current_yyyymmddhhmmss()} 상호명 : {seller_info["상호명"]}')
    print(f'{get_current_yyyymmddhhmmss()} 사업장소재지 : {seller_info["사업장소재지"]}')



    # ✅ 중복 체크 후 추가
    result_list.append(seller_info)

    if os.path.exists(save_path):
        os.remove(save_path)
        print(f"🗑️ HTML 파일 삭제됨: {save_path}")

    if result_list_index % 5 == 0:
        df = pd.DataFrame(result_list, columns=columns)
        if not os.path.exists(excel_name):
            df.to_csv(excel_name, mode='a', header=True, index=False, encoding="utf-8-sig")
        else:
            df.to_csv(excel_name, mode='a', header=False, index=False, encoding="utf-8-sig")
        result_list.clear()

    time.sleep(random.uniform(5, 7))



def main():
    global page, current_url, last_page, folder_path, excel_name
    folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "html")
    excel_name = f"쿠팡_{get_current_yyyymmddhhmmss()}.csv"


    print("▶ 사용자에게 쿠팡 브라우저 로그인 후 확인 대기...")
    input("✅ 쿠팡 로그인 후 화면 최대화 + 검색 완료 → Enter 키를 눌러주세요...")

    try:
        # ✅ 첫 페이지 크롤링
        print(f"▶ 페이지 {page} 진행 ============================================")
        crawl_once()

        # ✅ 다음 페이지부터 자동 반복
        while True:
            page += 1

            if page > last_page:
                print(f"✅page : {page}")
                print(f"✅last_page : {last_page}")

            # ✅ current_url의 page 값 수정
            parsed = urllib.parse.urlparse(current_url)
            query = urllib.parse.parse_qs(parsed.query)
            query['page'] = [str(page)]

            new_query = urllib.parse.urlencode(query, doseq=True)
            current_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
            print(f"\n🔁 다음 페이지 URL: {current_url}")

            if page % 3 == 0:
                # 크롬 강제 종료
                os.system("taskkill /f /im chrome.exe")
                time.sleep(random.uniform(1200, 1320))  # 종료 대기

                # 크롬 실행 (사용자 프로필 유지)
                chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

                subprocess.Popen([chrome_path, current_url])
                time.sleep(2)  # 쿠팡 로딩 대기

            # ✅ 브라우저 자동 이동
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.3)
            pyperclip.copy(current_url)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.3)
            pyautogui.press('enter')
            time.sleep(3)  # 페이지 로딩 대기

            print(f"▶ 페이지 {page} 진행")
            rs = crawl_once()
            if not rs:
                break

        if result_list:
            df = pd.DataFrame(result_list, columns=columns)
            df.to_csv(excel_name, mode='a', header=False, index=False, encoding="utf-8-sig")
            result_list.clear()

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
