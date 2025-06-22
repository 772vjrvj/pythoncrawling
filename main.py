from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import requests

LOGIN_URL = 'https://st.apro.sooplive.co.kr/member/login'
VOD_URL = 'https://st.apro.sooplive.co.kr/lee28261/vod/player/0/192781'


def setup_driver():
    options = Options()
    options.add_argument('--start-maximized')
    # options.add_argument('--headless')  # 필요시 헤드리스
    driver = webdriver.Chrome(options=options)
    return driver


def get_logged_in_cookies_and_video_src(driver):
    print("🔐 로그인 페이지로 이동 중...")
    driver.get(LOGIN_URL)
    print("👉 브라우저에서 직접 로그인 후, 엔터를 눌러주세요.")
    input("✅ 로그인 완료 후 엔터를 누르세요...")

    print("📺 VOD 페이지로 이동 중...")
    driver.get(VOD_URL)
    time.sleep(3)

    # video src 추출
    try:
        video_tag = driver.find_element(By.TAG_NAME, 'video')
        video_url = video_tag.get_attribute('src')
        print(f"🎬 추출된 video URL: {video_url}")
    except:
        print("❌ video 태그 찾기 실패")
        return None, None

    # 쿠키 추출
    cookies = driver.get_cookies()
    return cookies, video_url


def convert_cookies_to_dict(cookies):
    return {cookie['name']: cookie['value'] for cookie in cookies}


def download_video(video_url, cookies, filename='vod_download.mp4'):
    print("⬇ 동영상 다운로드 시작...")
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': VOD_URL
    }

    cookie_dict = convert_cookies_to_dict(cookies)

    with requests.get(video_url, headers=headers, cookies=cookie_dict, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    print(f"✅ 다운로드 완료: {filename}")


def main():
    driver = setup_driver()
    try:
        cookies, video_url = get_logged_in_cookies_and_video_src(driver)
        if video_url and cookies:
            download_video(video_url, cookies)
        else:
            print("❌ 다운로드 실패: 쿠키 또는 video URL 없음")
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
