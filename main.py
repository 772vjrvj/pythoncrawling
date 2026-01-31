import os
import sys
import json
import time
import urllib.parse
import logging
import traceback
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from datetime import datetime


# =========================================================
# 시간 / 로깅
# =========================================================
def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def setup_logging():
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger("naver_cookie")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    fh = logging.FileHandler("logs/app.log", encoding="utf-8")
    fh.setFormatter(fmt)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(sh)

    return logger


def install_global_excepthook(logger):
    def _hook(exc_type, exc, tb):
        logger.error(
            "UNHANDLED EXCEPTION\n%s",
            "".join(traceback.format_exception(exc_type, exc, tb))
        )
    sys.excepthook = _hook


log = setup_logging()
install_global_excepthook(log)


# =========================================================
# 전역 변수
# =========================================================
global_naver_keyword_cookies = None
driver = None
bearer_token = ""
refresh_token = ""
name = "keyword"
URL = "https://주식회사비전.com/open/update-cookie"


# =========================================================
# 드라이버 설정
# =========================================================
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless")

    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    drv = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    drv.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'}
    )

    drv.set_window_position(0, 0)
    drv.set_window_size(500, 800)

    return drv


# =========================================================
# 쿠키 서버 전송
# =========================================================
def updatePlaceCookie(name, cookies_dict, refresh_token, bearer_token):
    if not cookies_dict:
        log.warning("쿠키가 없습니다.")
        return

    required_keys = {"NNB", "NID_AUT", "NID_SES"}
    filtered = {k: v for k, v in cookies_dict.items() if k in required_keys}

    cookie_string = "; ".join(
        f"{k}={urllib.parse.quote(str(v))}" for k, v in filtered.items()
    )

    data = {
        "name": name,
        "cookie": cookie_string,
        "refreshToken": refresh_token,
        "bearerToken": bearer_token
    }

    try:
        resp = requests.post(URL, json=data, timeout=15)
        if not resp.ok:
            log.error("HTTP %s | %s", resp.status_code, resp.text)
            resp.raise_for_status()

        log.info("서버 응답: %s", resp.text)

    except Exception as e:
        log.error("쿠키 업데이트 실패: %s", e)


# =========================================================
# 새로고침 & 쿠키 갱신
# =========================================================
def reload():
    global driver, global_naver_keyword_cookies, bearer_token, refresh_token

    if driver is None:
        log.warning("driver가 없습니다.")
        return

    try:
        log.info("reload start")

        driver.refresh()
        time.sleep(3)

        tokens_json = driver.execute_script(
            "return window.localStorage.getItem('tokens');"
        )

        global_naver_keyword_cookies = {
            c["name"]: c["value"] for c in driver.get_cookies()
        }

        if not tokens_json:
            log.warning("tokens 값이 없습니다.")
            return

        tokens = json.loads(tokens_json)
        keys = list(tokens.keys())

        if len(keys) < 2:
            log.error("tokens key 부족: %s", keys)
            return

        account_data = tokens[keys[1]]

        bearer = account_data.get("bearer")
        refresh = account_data.get("refreshToken")

        if not bearer or not refresh:
            log.error("bearer/refreshToken 없음: %s", account_data)
            return

        bearer_token = f"Bearer {bearer}"
        refresh_token = refresh

        updatePlaceCookie(
            name,
            global_naver_keyword_cookies,
            refresh_token,
            bearer_token
        )

        log.info("reload done")

    except Exception as e:
        log.error("reload ERROR: %s", e)
        log.error(traceback.format_exc())


# =========================================================
# 네이버 로그인
# =========================================================
def naver_login():
    global driver, bearer_token, refresh_token, global_naver_keyword_cookies

    try:
        driver = setup_driver()
        driver.get("https://nid.naver.com/nidlogin.login")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "id"))
        )

        log.info("네이버 로그인 페이지 로드")

        start = time.time()
        while True:
            time.sleep(1)

            if time.time() - start > 300:
                log.error("로그인 타임아웃")
                return

            cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
            if "NID_AUT" in cookies and "NID_SES" in cookies:
                break

        log.info("로그인 완료 감지")

        print("\n===================================================")
        print("👉 키워드 플래너 페이지 이동 후 작업 완료")
        print("👉 끝났으면 엔터")
        print("===================================================\n")
        input()

        target = "https://manage.searchad.naver.com/customers/3775719/tool/keyword-planner"
        driver.get(target)
        time.sleep(3)

        if driver.current_url != target:
            raise RuntimeError("잘못된 페이지 접근")

        tokens_json = driver.execute_script(
            "return window.localStorage.getItem('tokens');"
        )

        global_naver_keyword_cookies = {
            c["name"]: c["value"] for c in driver.get_cookies()
        }

        tokens = json.loads(tokens_json)
        keys = list(tokens.keys())

        if len(keys) < 2:
            log.error("tokens key 부족: %s", keys)
            return

        account_data = tokens[keys[1]]

        bearer_token = f"Bearer {account_data.get('bearer')}"
        refresh_token = account_data.get("refreshToken")

        updatePlaceCookie(
            name,
            global_naver_keyword_cookies,
            refresh_token,
            bearer_token
        )

        log.info("초기 쿠키 전송 완료")

    except Exception as e:
        log.error("login ERROR: %s", e)
        log.error(traceback.format_exc())


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    log.info("프로그램 시작")

    naver_login()

    while True:
        try:
            log.info("주기적 쿠키 갱신 실행")
            reload()
            time.sleep(60 * 2)  # 10분
        except Exception as e:
            log.error("main loop ERROR: %s", e)
            log.error(traceback.format_exc())
            time.sleep(30)
