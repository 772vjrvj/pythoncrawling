from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,750")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(2)  # 페이지가 로드되는 시간을 기다림
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def get_comments(driver):
    comments = set()  # 중복을 피하기 위해 set 사용
    comment_elements = driver.find_elements(By.CSS_SELECTOR, 'yt-formatted-string.yt-core-attributed-string--white-space-pre-wrap')
    for comment_element in comment_elements:
        comments.add(comment_element.text.strip())
    return comments

def main():
    driver = setup_driver()

    urls = [
        # "https://www.youtube.com/watch?v=8BNhOIz1xX0&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=331",
        "https://www.youtube.com/watch?v=WgFi_lXmofs&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=327",
        # "https://www.youtube.com/watch?v=6jdWM6nXbAI&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=295",
        # "https://www.youtube.com/watch?v=LacjDxxRD1s&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=289",
        # "https://www.youtube.com/watch?v=98fhrs2NB8w&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=277",
        # "https://www.youtube.com/watch?v=8RrkbAd9Q5k&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=276",
        # "https://www.youtube.com/watch?v=MxgluFEWJTc&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=275",
        # "https://www.youtube.com/watch?v=zv3jcz5A7ws&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=272",
        # "https://www.youtube.com/watch?v=eZPj_DFogaQ&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=269",
        # "https://www.youtube.com/watch?v=huvSC_fpYw8&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=267",
        # "https://www.youtube.com/watch?v=122f2QG1Pq8&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=266",
        # "https://www.youtube.com/watch?v=n2qRO09lxb8&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=265",
        # "https://www.youtube.com/watch?v=x77xCjWaSW4&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=264",
        # "https://www.youtube.com/watch?v=A5WyB_JrL_o&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=263",
        # "https://www.youtube.com/watch?v=jdxinl7h590&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=262",
        # "https://www.youtube.com/watch?v=Tc4bF0rG-9Q&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=261",
        # "https://www.youtube.com/watch?v=Jx7WFznh2eU&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=260",
        # "https://www.youtube.com/watch?v=X2BV3Hnp9xA&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=256",
        # "https://www.youtube.com/watch?v=PVS9gBxwWMo&list=PLpDZdhM6kelSlKqvKUwMGwbZj1OynPDMR&index=254",
    ]
    driver.get(urls[0])
    time.sleep(5)
    all_comments = set()  # 모든 댓글을 저장할 set
    scroll_to_bottom(driver)
    #
    # for url in urls:
    #     print(f"Processing URL: {url}")
    #     driver.get(url)
    #     prev_comments_count = 0  # 새롭게 추가된 댓글 수 확인용
    #
    #     while True:
    #         scroll_to_bottom(driver)
    #         new_comments = get_comments(driver)
    #
    #         if len(new_comments) == prev_comments_count:  # 새로 추가된 댓글이 없을 경우 종료
    #             print(f"URL {url}: 더 이상 새로운 댓글이 없습니다. 다음 URL로 이동합니다.")
    #             break
    #
    #         all_comments.update(new_comments)
    #         prev_comments_count = len(new_comments)
    #         print(f"새로운 댓글을 발견했습니다. 현재 총 {len(all_comments)}개의 댓글이 있습니다.")
    #
    # # 모든 URL에서 크롤링된 댓글 출력
    # for idx, comment in enumerate(all_comments, start=1):
    #     print(f"{idx}: {comment}")
    time.sleep(100000)
    driver.quit()

if __name__ == "__main__":
    main()
