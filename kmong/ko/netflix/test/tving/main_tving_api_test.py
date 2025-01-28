import json
import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import psutil
import os
# 쿠팡 api 호출 테스트

episode_seq = ""
baseUrl = "https://www.tving.com"
driver = None
cookies = None

def get_cookies_from_browser(url):
    driver.get(url)
    cookies = driver.get_cookies()

    if not cookies:  # 쿠키가 없는 경우
        return None

    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    return cookie_dict



def login():
    try:
        # 필요한 쿠키 키 목록
        required_cookies = [
            "authToken",
            "accessToken",
            "refreshToken",
        ]

        cookies = get_cookies_from_browser(baseUrl)

        if all(key in cookies for key in required_cookies):
            cookies = cookies
            print("회원 확인.")

        if cookies is None:
            print("로그인 후 프로그램을 다시 실행하세요.")
            return False
        else:
            cookies = cookies
            print("★ 쿠키 확인 성공.")
            print("※※※※ ★회원과 ★쿠키가 모두 성공해야 정상적인 크롤링이 진행됩니다.")
            return True

    except Exception as e:
        print(f"넷플릭스 로그인 중 에러 발생 : {e}")
        return False


def close_chrome_processes(self):
    """모든 Chrome 프로세스를 종료합니다."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'chrome' in proc.info['name'].lower():
                proc.kill()  # Chrome 프로세스를 종료
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def setup_driver():
    try:
        close_chrome_processes()

        chrome_options = Options()
        user_data_dir = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data"
        profile = "Default"

        chrome_options.add_argument(f"user-data-dir={user_data_dir}")
        chrome_options.add_argument(f"profile-directory={profile}")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--start-maximized")
        # chrome_options.add_argument("--headless")  # Headless 모드 추가

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        download_dir = os.path.abspath("downloads")
        os.makedirs(download_dir, exist_ok=True)

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

def _url_change(url):
    global episode_seq

    if "/clip/player/" in url:
        return url.replace("/clip/player/", "/contents/")

    elif "/live/player/" in url:
        updated_url = url.replace("/live/player/", "/player/")
        return updated_url
    elif "/vod/player/" in url:
        updated_url = url.replace("/vod/player/", "/contents/")
        return updated_url
    elif "/program.tving.com/tvn/" in url:
        tvn_path = url.split("/tvn/")[1].split("/")
        new_url = f"https://tvn.cjenm.com/ko/{tvn_path[0]}"
        episode_seq = tvn_path[1]
        return new_url
    return url  # 조건에 맞지 않으면 원래 URL 반환


def _data_set_json_info(json_data, result):
    # JSON 내 필요한 데이터 접근
    pageProps = json_data.get("props", {}).get("pageProps", {})

    content = pageProps.get("streamData", {}).get("body", {}).get("content", {})

    content_info         = pageProps.get("contentInfo", {})
    content_info_message = content_info.get("message", {})
    content_info_content = content_info.get("content", {})

    if content_info_message:
        print('content_info_message')
        result['success']           = "O"
        result['message']           = content_info_message
        result['error']             = "X"
    elif content_info_content:
        print('content_info_content')
        result['title']             = content_info_content.get("title", "")
        result['episode_synopsis']  = content_info_content.get("episode_synopsis", "")
        result['episode_title']     = content_info_content.get("episode_title", "")
        result['episode_seq']       = str(content_info_content.get("frequency", ""))
        result['episode_season']    = content_info_content.get("episode_sort", "")
        result['year']              = str(content_info_content.get("product_year", ""))
        result['season']            = content_info_content.get("season_no", "")
        result['rating']            = ""
        result['genre']             = content_info_content.get("genre_name", "")
        result['summary']           = content_info_content.get("synopsis", "")
        result['cast']              = ", ".join(content_info_content.get("actor", []))
        result['director']          = ", ".join(content_info_content.get("director", []))
        result['success']           = "O"
        result['message']           = "성공"
        result['error']             = "X"
    elif content_info:
        print('content_info_content')
        result['title']             = content_info.get("title", "")
        result['episode_synopsis']  = content_info.get("episode_synopsis", "")
        result['episode_title']     = content_info.get("episode_title", "")
        result['episode_seq']       = str(content_info.get("frequency", ""))
        result['episode_season']    = content_info.get("episode_sort", "")
        result['year']              = str(content_info.get("product_year", ""))
        result['season']            = content_info.get("season_no", "")
        result['rating']            = ""
        result['genre']             = content_info.get("genre_name", "")
        result['summary']           = content_info.get("synopsis", "")
        result['cast']              = ", ".join(content_info.get("actor", []))
        result['director']          = ", ".join(content_info.get("director", []))
        result['success']           = "O"
        result['message']           = "성공"
        result['error']             = "X"
    elif content:
        print('content')
        content_schedule = content.get("info", {}).get("schedule", {})
        program = content_schedule.get("program", {})
        episode = content_schedule.get("episode", {})

        result['title']             = content.get("program_name", {})
        result['episode_title']     = content.get("episode_name", {})
        result['episode_seq']       = content.get("frequency", "")

        result['summary']           = program.get("synopsis", {}).get("ko", "")
        result['cast']              = ", ".join(program.get("actor", []))
        result['director']          = ", ".join(program.get("director", []))
        result['episode_season']    = program.get("season_pgm_no", "")
        result['season']            = program.get("season_pgm_no", "")
        result['year']              = program.get("product_year", "")
        result['rating']            = '19+' if program.get("adult_yn", "") == "Y" else 'All'''

        result['episode_synopsis']  = episode.get("synopsis", {}).get("ko", "")
        category1_name = episode.get("category1_name", {}).get("ko", "")
        category2_name = episode.get("category2_name", {}).get("ko", "")
        if category1_name and category2_name:
            category = f"{category1_name}, {category2_name}"
        else:
            category = category1_name
        result['genre'] = category

        result['success'] = "O"
        result['message'] = "성공"
        result['error']   = "X"

def _api_tving_contents(new_url, result):
    result['url'] = new_url
    headers = {
        "authority": "www.tving.com",
        "method": "GET",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "cookie": (
            "webOauthCancelUrl=https%3A%2F%2Fwww.tving.com%2Faccount%2F%2Flogin; "
            "cs=screenCode%3DCSSD0100%3BnetworkCode%3DCSND0900%3BosCode%3DCSOD0900%3BteleCode%3DCSCD0900; "
            "TVING_SESSION=afc67f33-c913-4225-9020-3ffe19da05e8; _cfuvid=nkwQNP.aythrBXE7VVlYOTG5pKRAm6tO4zSwzhnsKs4-1737986215917-0.0.1.1-604800000; "
            "TVING_AUTO_EXPIRE_TIME=FHi0wXJTfQXQ30DOaVSmxA%3D%3D; accessToken=6e8b4f70c5f1e23f76c6781899ab08497778bab10c9b4a88af0e249f454a28bdb6eb69fd7e9e4f5f836e22ba35402e58; "
            "refreshToken=6d444268c9792185b96c7a15854c270ea4173dfafac1bc11fc5484f032f7f6798eb7757870ca4ad29c995df7e3714bc0; _tving_token=596DarMcZ%2FQ7XUFDf7k3JQ%3D%3D; "
            "_snsToken=596DarMcZ%2FQ7XUFDf7k3JQ%3D%3D; _login_onetime_www_hellovision=Y; LEGAL_CONFIRM_YN=N; TLPUDB35Qhn7=20250114004059; "
            "GA360_USERTYPE_JSON=%7B%22dm019_paycnt%22%3A%22%22%2C%22dm016_TL_FYMD%22%3A%22%22%2C%22dm018_LP_FYMD%22%3A%22%22%2C%22dm022_MP_CYMD%22%3A%22%22%2C%22dm051_CYMD%22%3A%22%22%2C%22dm017_TL_CYMD%22%3A%22%22%2C%22dm020_LP_CYMD%22%3A%22%22%2C%22dm001_userToken%22%3A%22596DarMcZ%2FQ7XUFDf7k3JQ%3D%3D%22%2C%22dm009_usertype%22%3A%22N%22%2C%22dm050_FYMD%22%3A%22%22%2C%22dm021_MP_FYMD%22%3A%22%22%2C%22dm013_resIsPaid%22%3A%22F%22%7D; "
            "llsct=XC8DvIP1jqZbEmhS4bcVCw%3D%3D; LAST_LOGIN_TYPE=94; authToken=G8foNsmSjC%2FQnmXfhZ3Q8EM22i2hLYpK63jW3hqqAnE%3D; _tutB3583=596DarMcZ%2FQ7XUFDf7k3JQ%3D%3D; tving_logger=-1; "
            "TP2wgas1K9Q8F7B359108383=Y; TPLYFLt9NxVcJjQhn7Ee0069=N; MASTER_PROFILE_LOCK_YN=N; TVING_LOGIN_JOIN_LOGGER_RTURL=""; _fwb=6098QhAYgFYeUmYhh3xdqP.1737986218133; _gcl_au=1.1.1680889509.1737986218; _fbp=fb.1.1737986220425.732809408289355251; "
            "CloudFront-Key-Pair-Id=APKAIXCIJCFRGOUEZDWA; sendbirdSession_299318132=%7B%22token%22%3A%22eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1IjoxNzk1MzE1MDYsInYiOjEsImUiOjE3Mzk3MTQyMjB9.ChpNO9dSF8gpdUykYaayvlnngqJshzTnu5L71qiGCzk%22%2C%22expires%22%3A%222025-02-16T13%3A57%3A00.000Z%22%2C%22refreshBy%22%3A%222025-02-09T13%3A57%3A00.000Z%22%7D; "
            "_aproxy_aid=FH83Y2Zp2TTxnG3i; _tt_enable_cookie=1; _ttp=gHUC07EQd5XSFA9QblLKp69DUjW.tt.1; _ga=GA1.1.625943814.1737986353; _aproxy_pref={%22WEB_NPU_LIVE%22:{}%2C%22WEB_NPU_TVINGTV%22:{}}; "
            "_ga_7ERF1X30YC=GS1.1.1737991113.2.0.1737991113.0.0.0; ab.storage.deviceId.0ba2d3e8-c535-437c-84c2-f5f44a3691a7=%7B%22g%22%3A%2240e6b897-242c-f7d0-146e-cee1727d2884%22%2C%22c%22%3A1737986218410%2C%22l%22%3A1737993346619%7D; "
            "ab.storage.userId.0ba2d3e8-c535-437c-84c2-f5f44a3691a7=%7B%22g%22%3A%22596DarMcZ%2FQ7XUFDf7k3JQ%3D%3D%22%2C%22c%22%3A1737986218402%2C%22l%22%3A1737993346620%7D; CloudFront-Policy=eyJTdGF0ZW1lbnQiOiBbeyJSZXNvdXJjZSI6Iio6Ly90dm4tbWNkbi50dmluZy5jb20vdHZuL2xpdmUxMDAwLnNtaWwqIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzM4MDc5NzQ3fSwiSXBBZGRyZXNzIjp7IkFXUzpTb3VyY2VJcCI6IjAuMC4wLjAvMCJ9fX1dfQ__; "
            "CloudFront-Signature=RkkunHYh9If0xH7Kg6njVPHHPpoksucx88Qrx2iaefhwNpGg9f3jO4w-y~F2bR3BTY9upr3F3O85ONHpvfRABT5oBop9tYE4lY6Z9-W4Yi7K06mt6~hWpXuDv27A5eRRmB-B5AhY-42KBrHAUtCwu0NtGtRRLR0BXq1m7z5GJ7GJv8ksz0sIFlRurmOsHOX~ElQ6YgTLuZzNIxWZIff9qD6KV7bmZphoIYABLr0HtEleWanx030EteX4-D0DasUvC~Z~nUWRRQaNpyyywwKLXQyq~wxOjFBc~t39E3wKfLn60oUTDowxUQuDH00fveA3LUmCRnqf74qsBFHSVfUPNQ__; "
            "AWSALBTG=cMUk+USTZod6DwMJ7Q/fCuFQigvjqz/FuUrshuzlNswjnyZ4dpJBt3PaGCGdr95AhYfOKWTF/uX2I6bGp20W2XDGp++fjD/R1oBX07ee3Q60l5GHMMz+gIs+BYr7s/DpNGT54WWz7ZMcx8T7AchplkwQeiGtcwxxftjzAoP/QDLI; AWSALBTGCORS=cMUk+USTZod6DwMJ7Q/fCuFQigvjqz/FuUrshuzlNswjnyZ4dpJBt3PaGCGdr95AhYfOKWTF/uX2I6bGp20W2XDGp++fjD/R1oBX07ee3Q60l5GHMMz+gIs+BYr7s/DpNGT54WWz7ZMcx8T7AchplkwQeiGtcwxxftjzAoP/QDLI; "
            "amp_c2b312=yaS8GlyyURDCN685vrw6qN.NTk2RGFyTWNaL1E3WFVGRGY3azNKUT09..1iik5fk0a.1iik7kc4a.2e.21.4f; wcs_bt=s_1b6ae80a204f:1737993367; ab.storage.sessionId.0ba2d3e8-c535-437c-84c2-f5f44a3691a7=%7B%22g%22%3A%2249644894-78d2-cd1c-0233-2667dc64a14d%22%2C%22e%22%3A1737995168985%2C%22c%22%3A1737993346618%2C%22l%22%3A1737993368985%7D"
        ),
        "priority": "u=0, i",
        "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }

    try:
        # HTML 요청
        response = requests.get(new_url, headers=headers)
        response.raise_for_status()  # HTTP 에러 확인

        # BeautifulSoup로 HTML 파싱
        soup = BeautifulSoup(response.text, "html.parser")

        # <script> 태그에서 JSON 데이터 추출

        script_tags = soup.find_all("script", type="application/json")
        script_tag = None
        for tag in script_tags:
            if tag.get("id") == "__NEXT_DATA__":
                script_tag = tag
                break

        if not script_tag or not script_tag.string:
            result['message'] = "JSON script tag not found"

        # JSON 파싱
        json_data = json.loads(script_tag.string)

        _data_set_json_info(json_data, result)

    except requests.exceptions.RequestException as e:
        result['message'] = str(e)
    except json.JSONDecodeError:
        result['message'] = "Failed to parse JSON"
    except Exception as e:
        result['message'] = str(e)


def _api_tving_cjenm(new_url, result):

    headers = {
        "authority": "www.tving.com",
        "method": "GET",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "cookie": (
            "webOauthCancelUrl=https%3A%2F%2Fwww.tving.com%2Faccount%2F%2Flogin; "
            "cs=screenCode%3DCSSD0100%3BnetworkCode%3DCSND0900%3BosCode%3DCSOD0900%3BteleCode%3DCSCD0900; "
            "TVING_SESSION=afc67f33-c913-4225-9020-3ffe19da05e8; _cfuvid=nkwQNP.aythrBXE7VVlYOTG5pKRAm6tO4zSwzhnsKs4-1737986215917-0.0.1.1-604800000; "
            "TVING_AUTO_EXPIRE_TIME=FHi0wXJTfQXQ30DOaVSmxA%3D%3D; accessToken=6e8b4f70c5f1e23f76c6781899ab08497778bab10c9b4a88af0e249f454a28bdb6eb69fd7e9e4f5f836e22ba35402e58; "
            "refreshToken=6d444268c9792185b96c7a15854c270ea4173dfafac1bc11fc5484f032f7f6798eb7757870ca4ad29c995df7e3714bc0; _tving_token=596DarMcZ%2FQ7XUFDf7k3JQ%3D%3D; "
            "_snsToken=596DarMcZ%2FQ7XUFDf7k3JQ%3D%3D; _login_onetime_www_hellovision=Y; LEGAL_CONFIRM_YN=N; TLPUDB35Qhn7=20250114004059; "
            "GA360_USERTYPE_JSON=%7B%22dm019_paycnt%22%3A%22%22%2C%22dm016_TL_FYMD%22%3A%22%22%2C%22dm018_LP_FYMD%22%3A%22%22%2C%22dm022_MP_CYMD%22%3A%22%22%2C%22dm051_CYMD%22%3A%22%22%2C%22dm017_TL_CYMD%22%3A%22%22%2C%22dm020_LP_CYMD%22%3A%22%22%2C%22dm001_userToken%22%3A%22596DarMcZ%2FQ7XUFDf7k3JQ%3D%3D%22%2C%22dm009_usertype%22%3A%22N%22%2C%22dm050_FYMD%22%3A%22%22%2C%22dm021_MP_FYMD%22%3A%22%22%2C%22dm013_resIsPaid%22%3A%22F%22%7D; "
            "llsct=XC8DvIP1jqZbEmhS4bcVCw%3D%3D; LAST_LOGIN_TYPE=94; authToken=G8foNsmSjC%2FQnmXfhZ3Q8EM22i2hLYpK63jW3hqqAnE%3D; _tutB3583=596DarMcZ%2FQ7XUFDf7k3JQ%3D%3D; tving_logger=-1; "
            "TP2wgas1K9Q8F7B359108383=Y; TPLYFLt9NxVcJjQhn7Ee0069=N; MASTER_PROFILE_LOCK_YN=N; TVING_LOGIN_JOIN_LOGGER_RTURL=""; _fwb=6098QhAYgFYeUmYhh3xdqP.1737986218133; _gcl_au=1.1.1680889509.1737986218; _fbp=fb.1.1737986220425.732809408289355251; "
            "CloudFront-Key-Pair-Id=APKAIXCIJCFRGOUEZDWA; sendbirdSession_299318132=%7B%22token%22%3A%22eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1IjoxNzk1MzE1MDYsInYiOjEsImUiOjE3Mzk3MTQyMjB9.ChpNO9dSF8gpdUykYaayvlnngqJshzTnu5L71qiGCzk%22%2C%22expires%22%3A%222025-02-16T13%3A57%3A00.000Z%22%2C%22refreshBy%22%3A%222025-02-09T13%3A57%3A00.000Z%22%7D; "
            "_aproxy_aid=FH83Y2Zp2TTxnG3i; _tt_enable_cookie=1; _ttp=gHUC07EQd5XSFA9QblLKp69DUjW.tt.1; _ga=GA1.1.625943814.1737986353; _aproxy_pref={%22WEB_NPU_LIVE%22:{}%2C%22WEB_NPU_TVINGTV%22:{}}; "
            "_ga_7ERF1X30YC=GS1.1.1737991113.2.0.1737991113.0.0.0; ab.storage.deviceId.0ba2d3e8-c535-437c-84c2-f5f44a3691a7=%7B%22g%22%3A%2240e6b897-242c-f7d0-146e-cee1727d2884%22%2C%22c%22%3A1737986218410%2C%22l%22%3A1737993346619%7D; "
            "ab.storage.userId.0ba2d3e8-c535-437c-84c2-f5f44a3691a7=%7B%22g%22%3A%22596DarMcZ%2FQ7XUFDf7k3JQ%3D%3D%22%2C%22c%22%3A1737986218402%2C%22l%22%3A1737993346620%7D; CloudFront-Policy=eyJTdGF0ZW1lbnQiOiBbeyJSZXNvdXJjZSI6Iio6Ly90dm4tbWNkbi50dmluZy5jb20vdHZuL2xpdmUxMDAwLnNtaWwqIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzM4MDc5NzQ3fSwiSXBBZGRyZXNzIjp7IkFXUzpTb3VyY2VJcCI6IjAuMC4wLjAvMCJ9fX1dfQ__; "
            "CloudFront-Signature=RkkunHYh9If0xH7Kg6njVPHHPpoksucx88Qrx2iaefhwNpGg9f3jO4w-y~F2bR3BTY9upr3F3O85ONHpvfRABT5oBop9tYE4lY6Z9-W4Yi7K06mt6~hWpXuDv27A5eRRmB-B5AhY-42KBrHAUtCwu0NtGtRRLR0BXq1m7z5GJ7GJv8ksz0sIFlRurmOsHOX~ElQ6YgTLuZzNIxWZIff9qD6KV7bmZphoIYABLr0HtEleWanx030EteX4-D0DasUvC~Z~nUWRRQaNpyyywwKLXQyq~wxOjFBc~t39E3wKfLn60oUTDowxUQuDH00fveA3LUmCRnqf74qsBFHSVfUPNQ__; "
            "AWSALBTG=cMUk+USTZod6DwMJ7Q/fCuFQigvjqz/FuUrshuzlNswjnyZ4dpJBt3PaGCGdr95AhYfOKWTF/uX2I6bGp20W2XDGp++fjD/R1oBX07ee3Q60l5GHMMz+gIs+BYr7s/DpNGT54WWz7ZMcx8T7AchplkwQeiGtcwxxftjzAoP/QDLI; AWSALBTGCORS=cMUk+USTZod6DwMJ7Q/fCuFQigvjqz/FuUrshuzlNswjnyZ4dpJBt3PaGCGdr95AhYfOKWTF/uX2I6bGp20W2XDGp++fjD/R1oBX07ee3Q60l5GHMMz+gIs+BYr7s/DpNGT54WWz7ZMcx8T7AchplkwQeiGtcwxxftjzAoP/QDLI; "
            "amp_c2b312=yaS8GlyyURDCN685vrw6qN.NTk2RGFyTWNaL1E3WFVGRGY3azNKUT09..1iik5fk0a.1iik7kc4a.2e.21.4f; wcs_bt=s_1b6ae80a204f:1737993367; ab.storage.sessionId.0ba2d3e8-c535-437c-84c2-f5f44a3691a7=%7B%22g%22%3A%2249644894-78d2-cd1c-0233-2667dc64a14d%22%2C%22e%22%3A1737995168985%2C%22c%22%3A1737993346618%2C%22l%22%3A1737993368985%7D"
        ),
        "priority": "u=0, i",
        "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }


    try:
        # HTML 요청
        response = requests.get(new_url, headers=headers)
        response.raise_for_status()  # HTTP 에러 확인

        # BeautifulSoup로 HTML 파싱
        soup = BeautifulSoup(response.text, "html.parser")
        title_text = soup.title.string if soup.title else ""

        # <script> 태그에서 JSON 데이터 추출

        # 결과 매핑
        result['url'] = new_url
        result['title'] = title_text
        result['episode_synopsis'] = ""
        result['episode_title'] = ""
        result['episode_seq'] = episode_seq
        result['episode_season'] = ""
        result['year'] = ""
        result['season'] = ""
        result['rating'] = ""
        result['genre'] = ""
        result['summary'] = ""
        result['cast'] = ""
        result['director'] = ""
        result['success'] = "O"  # Assuming successful mapping
        result['message'] = "successful"
        result['error'] = "X"

    except requests.exceptions.RequestException as e:
        result['message'] = str(e)
    except json.JSONDecodeError:
        result['message'] = "Failed to parse JSON"
    except Exception as e:
        result['message'] = str(e)


def _fetch_place_info(url, result):

    # CASE1
    if "/player/" in url:
        contents_id = ''
        # 첫 번째 '/player/' 이후의 값을 가져옴
        match = re.search(r'/player/(.+)', url)
        if match:
            contents_id = match.group(1)  # '/player/' 뒤의 값 반환

        if '/' in contents_id:
            # '/'로 나누고 첫 번째 부분 가져오기
            contents_id = contents_id.split('/')[0]
            # '.#' 제거
            contents_id = contents_id.replace('.', '').replace('#', '')


        new_url = f"https://www.tving.com/player/{contents_id}"
        print(f'player new_url : {new_url}')
        _api_tving_contents(new_url, result)

    # CASE2
    elif "/program/" in url:
        contents_id = ''
        # 첫 번째 '/program/' 이후의 값을 가져옴
        match = re.search(r'/program/(.+)', url)
        if match:
            contents_id = match.group(1)  # '/player/' 뒤의 값 반환

        if '/' in contents_id:
            # '/'로 나누고 첫 번째 부분 가져오기
            contents_id = contents_id.split('/')[0]
            # '.#' 제거
            contents_id = contents_id.replace('.', '').replace('#', '')


        new_url = f"http://www.tving.com/contents/{contents_id}"
        print(f'program new_url : {new_url}')
        _api_tving_contents(new_url, result)


    # http://www.tving.com/vod/player
    # https://www.tving.com/contents
    # elif "tvn.cjenm.com/ko/" in new_url:
    #     _api_tving_cjenm(new_url, result)



def _set_https(url):
    if url.startswith("http://"):
        return url.replace("http://", "https://", 1)
    return url


if __name__ == "__main__":
    episode_seq = ""
    # url = "http://www.tving.com/live/player/C00551"
    # url = "http://www.tving.com/vod/player/E000462640"
    # url = "http://program.tving.com/tvn/dokebi/11/Contents/Html"
    url = "http://program.tving.com/zhtv/actionking"


    # player
    # url = "http://www.tving.com/vod/player/E000243732"
    # url = "http://www.tving.com/vod/player/S006915776#/clip/player/S006906386"
    # url = "http://www.tving.com/vod/player/E000851938#./E000857626"
    # url = "http://www.tving.com/vod/player/S006672782#./E000744409"
    # url = "http://www.tving.com/live/player/C00551#./C00551"

    url = "http://www.tving.com/vod/program/P000169779"
    # url = "http://www.tving.com/vod/program/P08214"

    # https 로 수정
    url = _set_https(url)

    result = {
        "origin_url": url,
        "url": "",
        "title": "",
        "episode_synopsis": "",
        "episode_title": "",
        "episode_seq": "",
        "episode_season": "",
        "year": "",
        "season": "",
        "rating": "",
        "genre": "",
        "summary": "",
        "cast": "",
        "director": "",
        "success": "X",
        "message": "",
        "error": "X"
    }

    _fetch_place_info(url, result)

    print(json.dumps(result, ensure_ascii=False, indent=4))