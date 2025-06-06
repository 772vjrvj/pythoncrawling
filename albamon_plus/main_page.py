import ssl
import os
import time
import pyautogui
import pyperclip
import urllib.parse
from bs4 import BeautifulSoup

ssl._create_default_https_context = ssl._create_unverified_context

# ✅ 전역 변수 선언
current_url = ""

def extract_product_urls(html_path):
    base_url = "https://www.coupang.com"

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

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
    for url in url_list:
        print(url)

    return url_list

def main():
    global current_url  # ✅ 전역 변수 사용

    print("▶ 사용자에게 쿠팡 브라우저 로그인 후 확인 대기...")
    input("✅ 쿠팡 로그인 후 화면 최대화 + 검색 완료 → Enter 키를 눌러주세요...")

    try:
        time.sleep(1)

        folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "html")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        pyautogui.moveTo(10, 10)
        pyautogui.click()
        time.sleep(0.5)

        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.3)

        # ✅ 현재 URL 전역 변수에 저장
        current_url = pyperclip.paste()
        print(f"📋 복사된 URL: {current_url}")

        pyautogui.moveTo(300, 400)
        pyautogui.click()
        time.sleep(0.3)

        for _ in range(10):
            pyautogui.scroll(-1000)
            time.sleep(0.2)

        pyautogui.hotkey('ctrl', 'u')
        time.sleep(3)

        pyautogui.hotkey('ctrl', 'a')
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(2)

        html_source = pyperclip.paste()

        parsed = urllib.parse.urlparse(current_url)
        query = urllib.parse.parse_qs(parsed.query)
        keyword_encoded = query.get("q", [""])[0]
        page = query.get("page", ["1"])[0]

        keyword = urllib.parse.unquote(keyword_encoded)
        filename = f"쿠팡_{keyword}_{page}.html"
        save_path = os.path.join(folder_path, filename)

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_source)

        pyautogui.hotkey('ctrl', 'w')
        time.sleep(0.5)

        print(f"💾 저장 완료: {save_path}")

        urls = extract_product_urls(save_path)

        if os.path.exists(save_path):
            os.remove(save_path)
            print(f"🗑️ HTML 파일 삭제됨: {save_path}")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
