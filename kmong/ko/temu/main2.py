import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import requests
import time
import random


mainUrl = "https://www.temu.com"

def fetch_detail_page_selenium(driver, detail_url):
    target_tag = ""
    retries = 5  # 최대 재시도 횟수

    for attempt in range(retries):
        try:
            # URL 접근
            driver.get(detail_url)

            time.sleep(2)
            # 페이지 로딩 대기 (최대 15초)
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "_151rnt-L"))
            )

            # 지정된 클래스 이름을 가진 태그 찾기
            target_tag = driver.find_element(By.CLASS_NAME, "_151rnt-L")

            if target_tag:
                print(target_tag.get_attribute('outerHTML'))  # 태그 자체를 출력
                return target_tag.get_attribute('outerHTML')
            else:
                print("지정된 클래스 이름을 가진 태그를 찾을 수 없습니다.")

        except (NoSuchElementException, TimeoutException):
            print(f"태그를 찾을 수 없거나 페이지 로딩에 실패했습니다: {detail_url}")

        # 재시도 전에 5초 대기 후 새로고침
        print("재시도 중... 1초 대기 후 새로고침합니다.")
        time.sleep(1)
        driver.refresh()

    print("지정된 태그를 가져오지 못했습니다. 최대 재시도 횟수에 도달했습니다.")
    return target_tag

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

def fetch_data():

    # 조회할 url
    url = "https://www.temu.com/api/poppy/v1/search?scene=search"

    # payload 설정
    payload = {
        "scene": "search",
        "pageSn": 10009,
        "offset": 6,
        "listId": "69426b1cc6dd4a499b2c56b3ce0e2389",
        "pageSize": 120,
        "query": "여성 목걸이",
        "filterItems": "",
        "searchMethod": "user",
        "disableCorrect": False
    }

    # 헤더 설정
    headers = {
        "authority": "www.temu.com",
        "method": "POST",
        "path": "/api/poppy/v1/search?scene=search",
        "scheme": "https",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-length": "192",
        "content-type": "application/json;charset=UTF-8",
        "cookie": "region=185; language=ko; currency=KRW; api_uid=Cm3EUma9xmqCxABHZ/glAg==; timezone=Asia%2FSeoul; webp=1; _nano_fp=XpmxXqmaXqgqn0djXC_pbKCoyOQjaLLqMy7XEpdy; _bee=4UoHmiJ1ctuzf2HydeOj5mhi7nHuDdOG; njrpl=4UoHmiJ1ctuzf2HydeOj5mhi7nHuDdOG; dilx=kLHZkv~x0z0Sh3yVGx54s; hfsc=L3yIeos26Tvx1ZLOeA==; _device_tag=CgI2WRIIWG9MU3RkbnkaMNrEOLr5zU44g5yZCOsCKkbF+KJZ3v8lnQCEfAd+uaOFk64ZYogVSw6JgFF0lRzKnjAC; _ttc=3.rEA8aZtsXcfk.1755249152; verifyAuthToken=NyVEcJlD_A5tAl73W53oSQ0a5ab6c17aefc8b62; _hal_tag=AJ22fGD7I1uVcuAItzda4La/YT7aYAaT1mX4wv5rV53nsDzrnWDCqMFs2HIZKh1gtUZNKUE/gEQ8k4jo9w==; AccessToken=VUIWI7G7P5CIF67AGJWRXI6EM3UFQV56GQXDO4C7VKVCZFJRA4VQ0110b9bacd10; user_uin=BBJAOAX67CURFFZLMHFPSNYSFHX5T2YDPGQBQQUZ; isLogin=1723863017139; __cf_bm=1a4t7JqZBf0SipQaSX3oFhvFCcNCjCg737IHMAAawLo-1723865651-1.0.1.1-.CIlGYVLjFhdYfTv._48qLA3usjEYcOXD_TX.UJPXGYbB6wJEMmbDNOssfzCSIoAScwCbgsYzZswnwvs.6o4tQ",  # 실제 쿠키 값으로 대체
        "origin": "https://www.temu.com",
        "referer": "https://www.temu.com/search_result.html",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }

    # POST 요청 보내기
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    # 응답 데이터 확인
    if response.status_code == 200:
        data = response.json()
        print("data:", data)
        return data
    else:
        print("데이터를 불러오는데 실패했습니다. 상태 코드:", response.status_code)
        return None, None


def parse_data(data):
    # 결과에서 필요한 정보 추출
    goods_list = data['result']['data']['goods_list']

    # 추출한 데이터를 저장할 리스트 초기화
    extracted_data = []

    for item in goods_list:
        image_url = item['image']['url'] if 'image' in item else ''
        detail_url = mainUrl + "/" + item['link_url'] if 'link_url' in item else ''
        title = item['title'] if 'title' in item else ''
        price = item['price_info']['price_str'] if 'price_info' in item and 'price_str' in item['price_info'] else ''
        rating = item['comment']['goods_score'] if 'comment' in item and 'goods_score' in item['comment'] else ''

        data = {
            "메인 이미지": image_url,
            "상세 Url": detail_url,
            "이름": title,
            "가격": price,
            "평점": rating
        }

        extracted_data.append(data)

    return extracted_data


def save_to_excel(data, filename="temu_necklaces_with_details.xlsx"):
    # DataFrame으로 변환
    df = pd.DataFrame(data)

    # 엑셀 파일로 저장
    df.to_excel(filename, index=False)
    print(f"데이터가 엑셀 파일로 저장되었습니다: {filename}")


def main():

    driver = setup_driver()
    if not driver:
        return

    # data = fetch_data()
    # if data:
    if True:
        # parsed_data = parse_data(data)
        parsed_data = ["https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099562614761&_oak_mp_inf=EOn%2Fna%2Bm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCYh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F5f479f92-3802-4197-8a99-c829dfaa25c2.jpg&spec_gallery_id=2123514842&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NjMy",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099586351891&_oak_mp_inf=EJPmxrqm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCYh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F28b897c9-ed45-44b9-ba9d-f7eb5998bae7.jpg&spec_gallery_id=2163263720&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjQyOA",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099603845448&_oak_mp_inf=EMjC8sKm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCZh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F28458db1-37d8-41b5-8e6c-61ebb17545be.jpg&spec_gallery_id=2223857580&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjYwOQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099567941841&_oak_mp_inf=ENGR47Gm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCZh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F6848d266-5656-4fe4-936b-bd618734edff.jpg&spec_gallery_id=2128662453&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTc2OA",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099584111079&_oak_mp_inf=EOeDvrmm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCZh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F5e6ed0ea-0e14-4faf-8898-14000e34cea0.jpg&spec_gallery_id=2158453143&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NjAy",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099547555931&_oak_mp_inf=ENvwhqim1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCZh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F08c1c84a-0456-4713-9d9d-65b087c1d3f0.jpg&spec_gallery_id=2093081911&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTA4NTQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099628673230&_oak_mp_inf=EM7x3c6m1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCZh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F4035d654-2f54-4ca7-b62b-2a581bd8b5f2.jpg&spec_gallery_id=2318325388&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NjAxMg",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099607628264&_oak_mp_inf=EOiz2cSm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCZh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fe62376e8-b24f-4bb8-a74b-184e84cb98a4.jpg&spec_gallery_id=2255326550&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NDQ4OQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099522456088&_oak_mp_inf=EJj0ipym1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCZh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2F2b877e809664f044ee5b336d789b1dca.jpg&spec_gallery_id=2021002149&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTIyMQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099553222340&_oak_mp_inf=EMTd4Kqm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCZh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fba8f3a9a-6a8a-4412-8bf1-6b2db009fc85.jpg&spec_gallery_id=2143850320&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=Mzc2Mw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099549468251&_oak_mp_inf=ENvM%2B6im1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCZh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fc2936626-1481-4b3b-96a2-fddddb3f48ab.jpg&spec_gallery_id=2095717490&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTAzMw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099597376233&_oak_mp_inf=EOnV57%2Bm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCZh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F898148e9-7e2e-4be6-b124-abc3da7321d5.jpg&spec_gallery_id=2214592224&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=ODcyNw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099582016638&_oak_mp_inf=EP6Yvrim1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCZh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fd89c7cf4-16b9-4782-99e0-f39ef7ce0c0e.jpg&spec_gallery_id=2237107846&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTYxMDM",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099582252299&_oak_mp_inf=EIvKzLim1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCZh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F71e838d1-4a7c-454b-a2c5-83429b5830bb.jpg&spec_gallery_id=2171516986&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTQwMg",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099514519335&_oak_mp_inf=EKe%2Bppim1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCah6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Ffc49dbd2-2a4d-4bc4-be09-f4de86ef445f.jpg&spec_gallery_id=21805161&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjIwNTQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099513127538&_oak_mp_inf=EPLE0Zem1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCah6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Fopen%2F2022-11-30%2F1669831409634-6e57fd8184f74ab180412cfe26224916-goods.jpeg&spec_gallery_id=10282015&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=Nzk3",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099546291153&_oak_mp_inf=ENHXuaem1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCah6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F3ffa4662-311b-413c-81c4-6381cd73fa37.jpg&spec_gallery_id=2090232209&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjU4MA",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099606946867&_oak_mp_inf=ELPor8Sm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCah6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fbc2c3ba3-bfd8-40ad-985e-dd3753f5b5c6.jpg&spec_gallery_id=2236732066&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTMwNA",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099520500302&_oak_mp_inf=EM7Ek5um1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCah6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2F285b6edb5f4a392e56c4aaa3628216fb.jpg&spec_gallery_id=2025461725&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjEwNA",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099553207995&_oak_mp_inf=ELvt36qm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCah6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F930b83db-f9a8-4302-8059-5a8c4f29078d.jpg&spec_gallery_id=2148714598&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=Mzc2Mw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099520910887&_oak_mp_inf=EKfMrJum1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCah6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2Ff42c4ac6abcd0be1c57bd9149546040f.jpg&spec_gallery_id=2047069650&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTY1OQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099554661685&_oak_mp_inf=ELXKuKum1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCah6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F7133ca1d-b102-45d7-99f1-7bd5cc119627.jpg&spec_gallery_id=2101386606&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NDE3",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099602183164&_oak_mp_inf=EPyHjcKm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCah6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F9ef20ece-8e51-4735-8df2-10e84823a0d5.jpg&spec_gallery_id=2227156628&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=Njcy",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099619649941&_oak_mp_inf=EJWTt8qm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCah6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Fopen%2F2024-07-23%2F1721718135497-0bf0b22d1fa44153bacf3316242edabc-goods.jpeg&spec_gallery_id=2267837251&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTk5Nw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099530055955&_oak_mp_inf=EJPi2p%2Bm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCah6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2F26c9996a7917c88bfb3f8059dd126ca4.jpg&spec_gallery_id=2044681975&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=ODY4",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099532913611&_oak_mp_inf=EMuXiaGm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2F91676eeefb90f09cab410f10c3d54694.jpg&spec_gallery_id=2105927455&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NDk0",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099551844087&_oak_mp_inf=EPfNjKqm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fba93655c-2f26-4c93-af98-677728a252cd.jpg&spec_gallery_id=2105313087&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjE5MDI",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099536013514&_oak_mp_inf=EMqxxqKm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2Fafa0183e4f027b7a0ba82a08e897ee7e.jpg&spec_gallery_id=2065341472&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NzQ5",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099530341562&_oak_mp_inf=ELqZ7J%2Bm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2Fc70cbfa11732871423e86cdd47c937c6.jpg&spec_gallery_id=2045298655&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjE3Nw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099543745180&_oak_mp_inf=EJylnqam1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F7c87da52-ac5e-449c-b532-5d8739faaa31.jpg&spec_gallery_id=2083478574&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTI1ODc",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099588873134&_oak_mp_inf=EK7X4Lum1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F7479dd58-7403-493e-b726-bc9851eea12c.jpg&spec_gallery_id=2188875965&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTY1OQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099586005138&_oak_mp_inf=EJLRsbqm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F8efd4c10-7fbe-49bb-8a36-b1af7f835ad8.jpg&spec_gallery_id=2255487548&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=ODYw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099577291038&_oak_mp_inf=EJ7inbam1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F6acafd35-8163-48c7-bb1f-79433cca46cc.jpg&spec_gallery_id=2171310516&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTIzMw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099537098957&_oak_mp_inf=EM3RiKOm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2Faae139625a0268765ded59d4656f62fd.jpg&spec_gallery_id=2066845864&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTY4NDA",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099587079685&_oak_mp_inf=EIWc87qm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Ffd820135-ddbf-45d9-990e-60ff68f099a3.jpg&spec_gallery_id=2184024459&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTI0NjI",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099582230120&_oak_mp_inf=EOicy7im1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F11be46b0-35c0-4941-ac39-ef8bd847c591.jpg&spec_gallery_id=2171071946&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTIzNg",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099511944888&_oak_mp_inf=ELitiZem1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2F1d14c6c0a3a%2F84539eec-7f23-4207-88ae-42e254fc7233_800x800.jpeg&spec_gallery_id=3105551&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTMyMg",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099546857367&_oak_mp_inf=EJef3Kem1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F0e5d8b1f-2e75-432b-938f-acd9d4f7885a.jpg&spec_gallery_id=2103871279&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NjM3",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099581999568&_oak_mp_inf=ENCTvbim1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCbh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fd27c9047-9273-4088-9a18-ece5f7797968.jpg&spec_gallery_id=2158836721&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTAxMDQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099519596916&_oak_mp_inf=EPSy3Jqm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2Ffd4645b2fd0a79c071b20e40afad8015.jpg&spec_gallery_id=2011432457&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjY1Nw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099535891673&_oak_mp_inf=ENn5vqKm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2F4648203175c7fa15454c44fce0e674a7.jpg&spec_gallery_id=2062975853&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MzE0",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099584886387&_oak_mp_inf=EPOs7bmm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F59180a84-a012-45e6-a177-42a25398910d.jpg&spec_gallery_id=2223552681&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NzgzMA",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099607053967&_oak_mp_inf=EI%2BttsSm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fb3346126-68b3-436b-8e83-f6c908fff2bd.jpg&spec_gallery_id=2235219253&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTU3OQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099608362379&_oak_mp_inf=EIubhsWm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Ff6c9541b-bcf3-4712-8f9c-35b082dcc7d2.jpg&spec_gallery_id=2232402334&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MzkyNQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099603844100&_oak_mp_inf=EIS48sKm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fe685f6be-2c89-4de7-b3de-1a5a7a90a0a4.jpg&spec_gallery_id=2270376286&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjA2Mg",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099545649761&_oak_mp_inf=EOHEkqem1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Faeb21407-6122-488e-85fc-1aa907b39172.jpg&spec_gallery_id=2094296267&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NDI1Nw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099569628640&_oak_mp_inf=EOCLyrKm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Faca4bbae-ef0b-4f20-a13c-c386b73558e0.jpg&spec_gallery_id=2260441550&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTAwOA",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099572426481&_oak_mp_inf=EPHt9LOm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F4298adc5-21c4-43bc-9bf6-3526d70d3567.jpg&spec_gallery_id=2132869104&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjQxNw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099623392151&_oak_mp_inf=EJfHm8ym1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F1276c30d-cf9a-423a-883c-57986c97b2ca.jpg&spec_gallery_id=2322347333&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjE5MA",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099544668980&_oak_mp_inf=ELTW1qam1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F32624484-7646-4e02-8dcd-1367c41b0799.jpg&spec_gallery_id=2082666633&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTM5NTk",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099550593298&_oak_mp_inf=EJKiwKmm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fc58d2788-c3a9-4548-8ca0-86bc72e1ed90.jpg&spec_gallery_id=2099053815&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MzI4",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099559614786&_oak_mp_inf=EMLy5q2m1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F6f65b789-30cf-4cda-848c-00830cde6902.jpg&spec_gallery_id=2124440339&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTE4NzE",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099565369913&_oak_mp_inf=ELmUxrCm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F2fd10194-22bf-4c8d-98dd-da36006083ef.jpg&spec_gallery_id=2122278322&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTAzNQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099546159896&_oak_mp_inf=EJjWsaem1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCch6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F9386ef48-0c28-4174-b9c0-ba2157e53fa2.jpg&spec_gallery_id=2104670027&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTE2MzE",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099593261282&_oak_mp_inf=EOLB7L2m1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F90bf8076-cf49-46e0-8d65-e9f554d07a5a.jpg&spec_gallery_id=2183340862&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NzY2",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099607454810&_oak_mp_inf=ENrozsSm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F9248a458-ede3-4148-9ad1-ead178112091.jpg&spec_gallery_id=2228094788&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTYyNw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099612963072&_oak_mp_inf=EICCn8em1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F897e4b76-415c-4b0f-9001-74702f307d03.jpg&spec_gallery_id=2247775281&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=Mjk4Nw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099592085169&_oak_mp_inf=ELHdpL2m1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F9093ce47-e76f-46c7-9b47-31b8c7a12fb8.jpg&spec_gallery_id=2196835802&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=OTExOQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099546178050&_oak_mp_inf=EILksqem1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F99e6c3e9-b176-4544-aa4a-b995bab7cd60.jpg&spec_gallery_id=2091096379&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=ODAxNA",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099573538527&_oak_mp_inf=EN%2FduLSm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F4b359e24-924e-4362-828b-a0c18a053288.jpg&spec_gallery_id=2138158182&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTM5NTk",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099581131902&_oak_mp_inf=EP6YiLim1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Ff14ceaf9-20f7-4b32-b99e-eff679736ebd.jpg&spec_gallery_id=2153490512&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NDgx",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099575211235&_oak_mp_inf=EOPpnrWm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fed2ef6d2-ff40-4034-88d3-0a045813abef.jpg&spec_gallery_id=2325624503&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NzM4",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099523585620&_oak_mp_inf=ENTsz5ym1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2F2349587ede137f98a00353f99a0ee759.jpg&spec_gallery_id=2030540168&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjI2Ng",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099576980060&_oak_mp_inf=ENzkiram1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F09df7e79-e0d4-4767-a594-e4566b6d8e77.jpg&spec_gallery_id=2166206004&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=OTkxMg",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099584169299&_oak_mp_inf=ENPKwbmm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F9e75c935-9f43-4cd4-948f-d8461a5d63bb.jpg&spec_gallery_id=2220508075&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MzM4NQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099565157069&_oak_mp_inf=EM2VubCm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F32916f26-52a7-47ab-8f3b-16dd7dc71beb.jpg&spec_gallery_id=2124032140&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NjE3",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099557089499&_oak_mp_inf=ENvhzKym1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F7ad635ac-1647-45e1-879a-45f42bff3df0.jpg&spec_gallery_id=2113835059&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTU5ODk",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099520653805&_oak_mp_inf=EO3znJum1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2Fadfc72c9fd91dd5d7ea1f4bbee2c5300.jpg&spec_gallery_id=2017343201&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjI2Ng",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099549372068&_oak_mp_inf=EKTd9aim1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCdh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2F30588ea1efa07cf1cb26034d1eef6d0f.jpg&spec_gallery_id=2095956977&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=OTQ0",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099518385461&_oak_mp_inf=ELW6kpqm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCeh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2F1d5858fa808dee3ad7ca6c1c5ee45b4f.jpg&spec_gallery_id=2042094009&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=ODEx",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099550232825&_oak_mp_inf=EPmhqqmm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCeh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F639044c3-693a-40d7-be29-cf33ef5f4b95.jpg&spec_gallery_id=2098962998&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NDc2Nw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099521834454&_oak_mp_inf=ENb75Jum1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCeh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2Fbd2c46ce57ce538267d447ee1dedd941.jpg&spec_gallery_id=2021427533&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjI2Ng",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099622600932&_oak_mp_inf=EOSh68um1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCeh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F619f13d9-fa04-4583-ae69-43a7c412e349.jpg&spec_gallery_id=2288494872&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MjU1Ng",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099538135318&_oak_mp_inf=EJbyx6Om1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCeh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2F6c1309c54af328d037313de972274f28.jpg&spec_gallery_id=2080642159&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=Nzc1",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099528881888&_oak_mp_inf=EOCNk5%2Bm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCeh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fd049826c-b862-4d10-9245-f09f668cc70c.jpg&spec_gallery_id=2038366395&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTA1OTc",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099547359986&_oak_mp_inf=EPL1%2Bqem1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCeh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F234a6082-16d9-42de-9f88-b4eafc086794.jpg&spec_gallery_id=2092528220&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTM1NzA",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099597850406&_oak_mp_inf=EKbOhMCm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCeh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2Fe0582730-b26a-4554-8954-783acb03a90f.jpg&spec_gallery_id=2227907039&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTA2MQ",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099529282231&_oak_mp_inf=ELfFq5%2Bm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCeh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2FFancyalgo%2FVirtualModelMatting%2Fb5d6206819c9c39e6094f03fbcb25a37.jpg&spec_gallery_id=2043064309&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=MTcwMw",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099540453949&_oak_mp_inf=EL201aSm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCeh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F4645e7a1-81cb-4e22-9196-2049c20e4a97.jpg&spec_gallery_id=2071292995&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=NDkzNA",
                       "https://www.temu.com/goods.html?_bg_fs=1&goods_id=601099551922110&_oak_mp_inf=EL6vkaqm1ogBGiA2OTQyNmIxY2M2ZGQ0YTQ5OWIyYzU2YjNjZTBlMjM4OSCeh6XzlTI%3D&top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F4392276d-5ad7-48fb-8b4e-ee12b8d622bf.jpg&spec_gallery_id=2107282054&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=OTcxMQ"]


        # 각 상세 URL에 접속하여 추가 데이터를 가져옴
        for index, item in enumerate(parsed_data):
            if index == 4:
                break
            detail_description = fetch_detail_page_selenium(driver, item)
            print(f"detail_description : {detail_description}")
            time.sleep(random.uniform(3,5))
            # detail_description = fetch_detail_page_selenium(driver, item['상세 Url'])
            # item['상세 설명'] = detail_description
            # time.sleep(random.uniform(2,4))

        save_to_excel(parsed_data)

    driver.quit()



# 프로그램 실행
if __name__ == "__main__":
    main()
