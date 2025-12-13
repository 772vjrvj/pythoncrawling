# peachhill.py
import os
import re
import time
import shutil
import tempfile
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


EXCEL_PATH = Path(__file__).parent / "data+수집.xlsx"
SHEET_NAME = 0

CHROME_USER_DATA_DIR = os.path.expandvars(r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\User Data")
CHROME_PROFILE_DIR = "Default"

TARGET_COLS = [
    "앱 이름", "앱 ID",
    "카테고리", "가격", "인기국가/지역", "광고집행여부",
    "현재버전", "최종업데이트", "퍼블리셔국가", "국가출시일", "글로벌출시일", "언어",
    "인앱구매아이템명", "인앱구매기간", "인앱구매가격",
    "요약", "설명"
]

def ensure_columns(df: pd.DataFrame, cols):
    for c in cols:
        if c not in df.columns:
            df[c] = ""

def extract_digits(s: str) -> str:
    return "".join(re.findall(r"\d+", s or ""))

def get_text_safe(driver, by, value, index_1_based=None, timeout=8, warn=True):
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    try:
        if index_1_based is None:
            el = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
            return el.text.strip()
        else:
            WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((by, value)))
            els = driver.find_elements(by, value)
            if len(els) >= index_1_based:
                return els[index_1_based - 1].text.strip()
            return ""
    except (TimeoutException, NoSuchElementException, WebDriverException) as e:
        if warn:
            print(f"[WARN] get_text_safe: (idx={index_1_based}) {type(e).__name__}")
        return ""

def click_safe(driver, by, value, timeout=10):
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        driver.execute_script("arguments[0].click();", el)
        return True
    except Exception as e:
        print(f"[WARN] click_safe: {value} -> {e}")
        return False

def _base_options():
    import random
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--no-first-run")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--lang=ko-KR")
    opts.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(f"--remote-debugging-port={random.randint(9222, 9555)}")
    return opts

def _try_boot(options, test_url="chrome://version", timeout=20):
    from selenium.common.exceptions import TimeoutException
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(120)
        driver.get(test_url)
        WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.TAG_NAME, "body")))
        return True, driver
    except TimeoutException:
        return True, driver
    except Exception as e:
        print(f"[BOOT FAIL] {e}")
        return False, None

def setup_driver():
    print("[STEP] 기본 옵션 부팅")
    opts = _base_options()
    ok, driver = _try_boot(opts)
    if ok:
        print("[OK] 기본 옵션 성공(프로필 미사용)")
        return driver

    print("[STEP] 사용자 프로필 부팅")
    opts = _base_options()
    if os.path.isdir(CHROME_USER_DATA_DIR):
        opts.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
        if CHROME_PROFILE_DIR:
            opts.add_argument(f"--profile-directory={CHROME_PROFILE_DIR}")
    ok, driver = _try_boot(opts)
    if ok:
        print("[OK] 사용자 프로필 성공")
        return driver

    print("[STEP] 임시 프로필 폴백")
    temp_profile = tempfile.mkdtemp(prefix="chrome-profile-")
    opts = _base_options()
    opts.add_argument(f"--user-data-dir={temp_profile}")
    ok, driver = _try_boot(opts)
    if ok:
        print(f"[OK] 임시 프로필 성공: {temp_profile}")
        driver._temp_profile_path = temp_profile
        return driver

    raise RuntimeError("Chrome 실행 실패: 크롬/드라이버 버전, 권한, 보안도구를 확인하세요.")


# ─────────────────────────────────────────────────────────────
# 동적 라벨 매핑 파서들
# ─────────────────────────────────────────────────────────────
def parse_stat_cards(driver) -> dict:
    """
    카테고리 / 가격 / 인기국가/지역 / 광고집행여부
    h4 라벨을 정규화(공백/콜론 제거)하여 매핑, 값은 body1 모음 → 없으면 컨테이너 텍스트.
    """
    import re
    key_map = {
        "카테고리": "카테고리",
        "가격": "가격",
        "인기국가/지역": "인기국가/지역",     # '인기 국가/지역'도 정규화 후 일치
        "광고집행여부": "광고집행여부",       # '광고 집행 여부'도 정규화 후 일치
    }
    result = {v: "" for v in key_map.values()}

    card_xpath = "//div[contains(@class,'BaseStatistic-module__statistic')]"
    cards = driver.find_elements(By.XPATH, card_xpath)
    for card in cards:
        try:
            label_raw = card.find_element(
                By.XPATH, ".//h4[contains(@class,'MuiTypography-h4')]"
            ).text.strip()
            # 공백/콜론 제거하여 정규화
            label_norm = re.sub(r"[\s:]+", "", label_raw)

            key = key_map.get(label_norm)
            if not key:
                continue

            values_container = card.find_element(
                By.XPATH, ".//div[contains(@class,'BaseStatistic-module__values')]"
            )
            # 우선 body1 스팬 모으기
            spans = values_container.find_elements(
                By.XPATH, ".//*[contains(@class,'MuiTypography-body1')]"
            )
            texts = [s.text.strip() for s in spans if s.text.strip()]
            if texts:
                value = ", ".join(texts)
            else:
                # 가격처럼 컨테이너에 바로 텍스트가 있는 경우
                value = values_container.text.strip()

            # 구분자 콤마 사이 공백 정리
            value = re.sub(r"\s*,\s*", ", ", value)
            result[key] = value
        except Exception:
            continue
    return result


def parse_release_details(driver) -> dict:
    """
    현재버전, 최종업데이트, 퍼블리셔국가, 국가출시일, 글로벌출시일, 언어
    ul > li 들에서 h4 라벨과 p 값을 매핑
    """
    map_keys = {
        "현재 버전": "현재버전",
        "현재 버전:": "현재버전",
        "현재버전": "현재버전",
        "최종 업데이트": "최종업데이트",
        "최종 업데이트:": "최종업데이트",
        "최종업데이트": "최종업데이트",
        "퍼블리셔 국가": "퍼블리셔국가",
        "퍼블리셔 국가:": "퍼블리셔국가",
        "퍼블리셔국가": "퍼블리셔국가",
        "국가 출시일": "국가출시일",
        "국가 출시일:": "국가출시일",
        "국가출시일": "국가출시일",
        "글로벌 출시일": "글로벌출시일",
        "글로벌 출시일:": "글로벌출시일",
        "글로벌출시일": "글로벌출시일",
        "언어": "언어",
        "언어:": "언어",
    }
    out = {v: "" for v in set(map_keys.values())}

    li_xpath = "//li[contains(@class,'AppOverviewSubappAboutReleaseDetails-module__listItem')]"
    items = driver.find_elements(By.XPATH, li_xpath)
    for li in items:
        try:
            h4 = li.find_element(By.XPATH, ".//h4[contains(@class,'MuiTypography-h4')]").text.strip()
            key = map_keys.get(h4, map_keys.get(h4.replace(" ", ""), None))
            if not key:
                continue
            p = li.find_element(
                By.XPATH,
                ".//p[contains(@class,'AppOverviewSubappAboutReleaseDetails-module__value')]"
            ).text.strip()
            out[key] = p
        except Exception:
            continue
    return out


# ─────────────────────────────────────────────────────────────
# 스크래핑 본체
# ─────────────────────────────────────────────────────────────
def scrape_sensortower(driver, url: str) -> dict:
    out = {k: "" for k in TARGET_COLS}
    driver.get(url)

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class,'AppOverviewSubappDetailsHeader-module')]")
            )
        )
    except Exception:
        print("[WARN] 헤더 대기 실패 (로그인/권한 필요 가능)")

    # 앱 이름
    out["앱 이름"] = get_text_safe(
        driver, By.XPATH,
        "//h2[contains(@class,'AppOverviewSubappDetailsHeader-module__appName')]"
    )

    # 앱 ID (2번째 body1에서 숫자만)
    app_id_raw = get_text_safe(
        driver, By.XPATH,
        "//p[contains(@class,'css-1poubqx')]", index_1_based=2
    )
    out["앱 ID"] = extract_digits(app_id_raw)

    # ── [수정] 통계 카드 라벨 매핑 ──
    stats = parse_stat_cards(driver)
    out.update(stats)

    # ── [수정] 릴리즈 상세 라벨 매핑 ──
    release = parse_release_details(driver)
    out.update(release)

    # 인앱구매 (첫 행)
    out["인앱구매아이템명"] = get_text_safe(
        driver, By.XPATH,
        "(//th[contains(@class,'AppOverviewSubappAboutTopInAppPurchases-module__tableCell') and contains(@class,'css-16vheyy')]"
        " | //td[contains(@class,'AppOverviewSubappAboutTopInAppPurchases-module__tableCell') and contains(@class,'css-16vheyy')])[1]",
        warn=False
    )
    out["인앱구매기간"] = get_text_safe(
        driver, By.XPATH,
        "//td[contains(@class,'AppOverviewSubappAboutTopInAppPurchases-module__tableCell') and contains(@class,'css-awwn6t')]",
        index_1_based=1, warn=False
    )

    # 인앱구매가격
    price = get_text_safe(
        driver, By.XPATH,
        "//td[contains(@class,'AppOverviewSubappAboutTopInAppPurchases-module__tableCell') and contains(@class,'css-102s19')]",
        index_1_based=1, warn=False
    )

    if not price:
        msg_text = get_text_safe(
            driver, By.XPATH,
            "//div[contains(@class,'AppOverviewSubappAboutTopInAppPurchases-module__message')]",
            warn=False
        )
        if msg_text:
            # "$2.99 - $59.99 per item" → "$2.99 - $59.99"
            m = re.search(r"\$\d[\d.,]*(?:\s*-\s*\$\d[\d.,]*)?", msg_text)
            if m:
                price = m.group(0).strip()

    out["인앱구매가격"] = price

    # 요약 (안정 셀렉터 + 재시도)
    summary_xpath = ("//div[contains(@class,'MuiStack-root') and "
                     "contains(@class,'AppOverviewSubappAboutAppSummary-module__textContainer') and "
                     "contains(@class,'css-hmrm3s')]")
    out["요약"] = get_text_safe(driver, By.XPATH, summary_xpath, timeout=20, warn=False)
    if not out["요약"]:
        time.sleep(1.0)
        driver.execute_script("window.scrollBy(0, 400)")
        out["요약"] = get_text_safe(driver, By.XPATH, summary_xpath, timeout=10, warn=False)

    # 설명 (버튼 클릭 후 Stack 2번째)
    clicked = click_safe(
        driver, By.XPATH,
        "//button[contains(@class,'BaseButton-module__tertiary') and contains(@class,'css-j16pl4')]"
    )
    if clicked:
        time.sleep(1.2)
        desc_block = get_text_safe(
            driver, By.XPATH,
            "//div[contains(@class,'MuiStack-root') and contains(@class,'css-hmrm3s')]",
            index_1_based=2
        )
        # "설명:" 뒤만 추출
        part = re.split(r"(?:^|\n)\s*설명:\s*", desc_block, maxsplit=1)
        desc_only = part[-1].strip() if len(part) > 1 else desc_block.strip()
        out["설명"] = desc_only.replace("접기", "").strip()

    return out


def main():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"엑셀 없음: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
    if "SensorTower_link" not in df.columns:
        raise ValueError("'SensorTower_link' 컬럼이 없습니다.")
    ensure_columns(df, TARGET_COLS)

    # ✅ 문자열 컬럼 강제 (FutureWarning 방지)
    for col in TARGET_COLS:
        if col in df.columns and df[col].dtype != "object":
            df[col] = df[col].astype("object")

    driver = setup_driver()
    try:
        for i, row in df.iterrows():
            url = str(row.get("SensorTower_link", "")).strip()
            if not url.startswith("http"):
                print(f"[SKIP] ({i}) 잘못된 URL: {url}")
                continue

            print(f"\n[GO] ({i}) {url}")
            try:
                data = scrape_sensortower(driver, url)
                for k, v in data.items():
                    df.at[i, k] = v
                df.to_excel(EXCEL_PATH, index=False)
                print(f"[OK] ({i}) 저장 완료")
            except Exception as e:
                print(f"[ERR] ({i}) 실패: {e}")
                continue
    finally:
        try:
            temp_profile = getattr(driver, "_temp_profile_path", None)
            driver.quit()
            if temp_profile and os.path.isdir(temp_profile):
                shutil.rmtree(temp_profile, ignore_errors=True)
        except Exception:
            pass

    print(f"\n✅ 완료 → {EXCEL_PATH}")

if __name__ == "__main__":
    main()
