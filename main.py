import pandas as pd
import numpy as np
import time
import csv
from tqdm import tqdm_notebook
import re
import warnings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import ssl
import random
import os
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import speech_recognition as sr
import requests

# SSL 설정 (인증서 검증 비활성화)
ssl._create_default_https_context = ssl._create_unverified_context

# 경고 무시
warnings.filterwarnings('ignore')

# 논문 제목
some_paper = [
    # 논문 제목 리스트...
]


# 데이터 로드 함수
def load_data(file_path):
    """JSON 파일에서 데이터를 로드하는 함수"""
    return pd.read_json(file_path)


# 첫 네 개의 텍스트를 추출하는 함수
def extract_first_four_texts(data):
    """각 항목에서 첫 네 개의 텍스트를 추출하는 함수"""
    result = {}
    for key, value in data.items():
        texts = [sentence['text'] for sentence in value['x'][:4]]
        result[key] = texts
    return result


# Selenium 웹 드라이버 설정 함수
def setup_driver():
    try:
        chrome_options = Options()

        ##  크롬 브라우저에 chrome://version/ 검색 해서
        ## 프로필 경로      C:\Users\772vj\AppData\Local\Google\Chrome\User Data\Default 에서 Default만 profile에 넣는다.
        user_data_dir = "C:\\Users\\772vj\\AppData\\Local\\Google\\Chrome\\User Data"
        profile = "Default"

        chrome_options.add_argument(f"user-data-dir={user_data_dir}")
        chrome_options.add_argument(f"profile-directory={profile}")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--start-maximized")

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        download_dir = os.path.abspath("downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        chrome_options.add_experimental_option('prefs', {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        script = '''
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' });
        '''
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})

        return driver
    except WebDriverException as e:
        print(f"Error setting up the WebDriver: {e}")
        return None


def search_google(driver, url, texts):
    driver.get(url)
    search_box = driver.find_element(By.NAME, 'q')
    search_box.clear()
    search_box.send_keys(f"{texts}")
    search_box.send_keys(Keys.RETURN)


# 음성 파일을 텍스트로 변환하는 함수
def audio_to_text(audio_url):
    r = sr.Recognizer()
    response = requests.get(audio_url)
    with open("audio.mp3", "wb") as file:
        file.write(response.content)

    with sr.AudioFile("audio.mp3") as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None


# 논문 제목을 검색하는 함수
def search_paper_titles(driver, extracted_texts, url='https://www.google.co.kr/'):
    """추출된 텍스트를 사용하여 구글에서 논문 제목을 검색하는 함수"""
    paper_names = {}
    error_names = {}

    index = 0
    print(f"len {len(extracted_texts.items())}")
    for key, texts in extracted_texts.items():
        paper_names[key] = ""
        error_names[key] = ""

        index = index + 1
        print(f"============= index: {index}, key : {key}")
        search_google(driver, url, texts)

        time.sleep(random.uniform(3, 7))

        # 캡챠 확인
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
            )
            print("reCAPTCHA iframe 존재.")

            # reCAPTCHA iframe 으로 변경
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
            )

            # 클릭 the reCAPTCHA checkbox
            recaptcha_checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "recaptcha-checkbox-border"))
            )

            # 로봇 방지 클릭
            recaptcha_checkbox.click()
            print("로봇 방지 클릭.")
            time.sleep(3)

            # Switch back to the default content
            driver.switch_to.default_content()

            # "reCAPTCHA 보안문자 2분 후 만료" 확인
            try:
                print("오디오 버튼 확인")
                # 새로운 reCAPTCHA 보안문자 iframe으로 전환
                WebDriverWait(driver, 10).until(
                    EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title*='보안문자']"))
                )
                print("오디오 버튼 확인")
                time.sleep(5)

                # 오디오 버튼 클릭
                audio_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "recaptcha-audio-button"))
                )
                audio_button.click()
                print("오디오 버튼 클릭")
                time.sleep(5)

                # 오디오 재생 버튼 클릭
                audio_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.rc-button-audio:not([disabled])"))
                )
                audio_button.click()
                print("오디오 재생 버튼 클릭")

                # 오디오 URL 가져오기
                audio_source = driver.find_element(By.ID, "audio-source")
                audio_url = audio_source.get_attribute("src")

                # 오디오를 텍스트로 변환
                audio_text = audio_to_text(audio_url)

                if (audio_text):
                    # 텍스트 입력
                    audio_response_input = driver.find_element(By.ID, "audio-response")
                    audio_response_input.send_keys(audio_text)

                    # 확인 버튼 클릭
                    verify_button = driver.find_element(By.ID, "recaptcha-verify-button")
                    verify_button.click()
                    time.sleep(3)
            except NoSuchElementException:
                print("보안문자 미확인.")

            # 안전한 검색을 위해 재 검색 시도
            search_google(driver, url, texts)
            print("크롤링 재시도...")

            time.sleep(random.uniform(2, 5))

            paper_names, error_names = paper_name(driver, key, paper_names, error_names)
            if key in error_names:
                pass

        except TimeoutException:
            print("reCAPTCHA iframe 미존재.")
            paper_names, error_names = paper_name(driver, key, paper_names, error_names)

            if key in error_names:
                pass

        # 매번 루프 끝날 때마다 현재까지의 결과를 저장
        save_to_csv(paper_names, 'paper_names.csv')

    return paper_names, error_names


def paper_name(driver, key, paper_names, error_names):
    try:
        paper_name = driver.find_element(By.XPATH, '/html/body/div[4]/div/div[14]/div/div[2]/div[2]/div/div/div[1]/div/div/div/div[1]/div/div/span/a/h3').text
        print("paper_name1:", paper_name)
        paper_names[key] = paper_name
    except:
        try:
            paper_name = driver.find_element(By.XPATH, '/html/body/div[5]/div/div[13]/div/div[2]/div[2]/div/div/div[1]/div/div/div/div[1]/div/div/span/a/h3').text
            print("paper_name2:", paper_name)
            paper_names[key] = paper_name
        except:
            try:
                paper_name = driver.find_element(By.XPATH, '/html/body/div[5]/div/div[14]/div/div[2]/div[2]/div/div/div[1]/div/div/div/div[1]/div/div/span/a/h3').text
                print("paper_name3:", paper_name)
                paper_names[key] = paper_name
            except:
                try:
                    paper_name = driver.find_element(By.XPATH, '/html/body/div[4]/div/div[14]/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div/div/span/a/h3').text
                    print("paper_name4:", paper_name)
                    paper_names[key] = paper_name
                except:
                    error_names[key] = "Not Found"
                    print("error!!")
    time.sleep(0.5)
    return paper_names, error_names


# CSV 파일로 저장하는 함수
def save_to_csv(paper_names, file_path):
    """paper_names 딕셔너리를 CSV 파일로 저장하는 함수"""
    df = pd.DataFrame(list(paper_names.items()), columns=['Key', 'Paper Name'])
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"Data saved to {file_path}")


# 메인 함수
def main():
    """메인 실행 함수"""
    data = load_data('full_raw.json')  # 데이터 로드
    extracted_texts = extract_first_four_texts(data)  # 텍스트 추출

    for key, texts in extracted_texts.items():
        print(f"{texts}")

    driver = setup_driver()  # 웹 드라이버 설정
    paper_names, error_names = search_paper_titles(driver, extracted_texts)  # 논문 제목 검색
    driver.quit()  # 드라이버 종료

    print("Paper Names:", paper_names)
    print("Errors:", error_names)

    # CSV 파일로 저장
    save_to_csv(paper_names, 'paper_names.csv')


# 프로그램 실행
if __name__ == "__main__":
    main()
