import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import schedule
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from datetime import datetime


# 현재 시간 반환 함수

# 전역 변수
SELECT_URL = "https://주식회사비전.com/user/place/rest/select-currentrank"
UPDATE_URL = "https://주식회사비전.com/user/place/rest/update-currentrank"

# UPDATE_URL = "http://localhost/user/place/rest/update-currentrank"
# SELECT_URL = "http://localhost/user/place/rest/select-currentrank"


# 드라이버 설정
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless")  # 서버 실행 시 필요

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    driver.set_window_position(0, 0)
    driver.set_window_size(1000, 1000)
    return driver



def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')



def update_obj_list(obj_list):
    response = requests.put(UPDATE_URL, json=obj_list)

    # 결과 출력
    if response.status_code == 200:
        print("성공적으로 업데이트되었습니다.")
        print("응답 데이터:", response.json())
    else:
        print("업데이트 실패:", response.status_code)
        print("응답 데이터:", response.text)



def get_current_rank_json():
    return [
        {"no": 529, "regDt": "2024-11-22 18:45:16", "businessName": "백경식당", "placeNumber": 1027229757,
         "keyword": "파주오산리밥집", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "노유민", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:14:06", "highestDt": "2025-03-09 01:15:54", "deletedYn": "N",
         "empId": "shdbals", "crawlYn": "Y"},

        # 있는데 목록 못가져옴
        {"no": 840, "regDt": "2024-12-19 12:32:37", "businessName": "테크런 용인점", "placeNumber": 1098698239,
         "keyword": "용인키즈카페", "category": "기타", "initialRank": 234, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 14:35:38", "highestDt": "2025-03-09 01:25:20", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},

        {"no": 844, "regDt": "2024-12-19 12:50:21", "businessName": "테크런 용인점", "placeNumber": 1098698239,
         "keyword": "역북동키즈카페", "category": "기타", "initialRank": 8, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:22:41", "highestDt": "2025-03-09 01:25:23", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},
        {"no": 405, "regDt": "2024-11-18 21:09", "businessName": "테크런 용인점", "placeNumber": 1098698239,
         "keyword": "명지대키즈카페", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:10:14", "highestDt": "2025-03-09 01:11:09", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},


        # 아에 키워드 검색 결과 없음
        {"no": 1027, "regDt": "2025-01-07 15:02:09", "businessName": "붙이다니 홍대점", "placeNumber": 1113095229,
         "keyword": "서울붙임머리 네이버오류", "category": "뷰티", "initialRank": 275, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김예지", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-02-04 16:40:01", "highestDt": "2025-02-04 01:31:06", "deletedYn": "Y",
         "empId": "rladPwl", "crawlYn": "Y"},
        {"no": 1028, "regDt": "2025-01-07 15:02:18", "businessName": "붙이다니 홍대점", "placeNumber": 1113095229,
         "keyword": "홍대붙임머리 네이버오류", "category": "뷰티", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김예지", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-02-04 16:40:00", "highestDt": "2025-02-04 01:31:07", "deletedYn": "Y",
         "empId": "rladPwl", "crawlYn": "Y"},
        {"no": 1029, "regDt": "2025-01-07 15:02:21", "businessName": "붙이다니 홍대점", "placeNumber": 1113095229,
         "keyword": "합정붙임머리 네이버오류", "category": "뷰티", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김예지", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-02-04 16:39:59", "highestDt": "2025-02-04 01:31:07", "deletedYn": "Y",
         "empId": "rladPwl", "crawlYn": "Y"},
        {"no": 1030, "regDt": "2025-01-07 15:02:22", "businessName": "붙이다니 홍대점", "placeNumber": 1113095229,
         "keyword": "마포붙임머리 네이버오류", "category": "뷰티", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김예지", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-02-04 16:39:58", "highestDt": "2025-02-04 01:31:07", "deletedYn": "Y",
         "empId": "rladPwl", "crawlYn": "Y"},
        {"no": 1031, "regDt": "2025-01-07 15:02:26", "businessName": "붙이다니 홍대점", "placeNumber": 1113095229,
         "keyword": "홍대미용실 네이버오류", "category": "뷰티", "initialRank": 187, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김예지", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-02-04 16:39:58", "highestDt": "2025-02-04 01:31:08", "deletedYn": "Y",
         "empId": "rladPwl", "crawlYn": "Y"},
        {"no": 1032, "regDt": "2025-01-07 15:02:31", "businessName": "붙이다니 홍대점", "placeNumber": 1113095229,
         "keyword": "홍대염색 네이버오류", "category": "뷰티", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김예지", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-02-04 16:39:56", "highestDt": "2025-02-04 01:31:08", "deletedYn": "Y",
         "empId": "rladPwl", "crawlYn": "Y"},
        {"no": 1033, "regDt": "2025-01-07 15:02:37", "businessName": "붙이다니 홍대점", "placeNumber": 1113095229,
         "keyword": "홍대파마 네이버오류", "category": "뷰티", "initialRank": 175, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김예지", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-02-04 16:39:57", "highestDt": "2025-02-04 01:31:08", "deletedYn": "Y",
         "empId": "rladPwl", "crawlYn": "Y"},

        {"no": 568, "regDt": "2024-11-26 19:17:01", "businessName": "용궁별상아씨", "placeNumber": 1440048412,
         "keyword": "풍무역점사", "category": "심리상담", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-12 01:17:15", "highestDt": "2025-03-09 01:17:11", "deletedYn": "Y",
         "empId": "dhrudwn", "crawlYn": "Y"},
        {"no": 602, "regDt": "2024-11-29 15:18:17", "businessName": "진천대장간", "placeNumber": 1080668947,
         "keyword": "철가공소", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1, "currentRank": 1,
         "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:16:09", "highestDt": "2025-03-09 01:18:17", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},
        {"no": 634, "regDt": "2024-12-04 18:22:12", "businessName": "브룬디", "placeNumber": 1535827102,
         "keyword": "대부도애견동반", "category": "카페", "initialRank": 22, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 17:05:01", "highestDt": "2025-03-09 01:19:07", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},
        {"no": 841, "regDt": "2024-12-19 12:50:19", "businessName": "테크런 용인점", "placeNumber": 1098698239,
         "keyword": "역북동액티비티", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:22:40", "highestDt": "2025-03-09 01:25:21", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},
        {"no": 895, "regDt": "2024-12-23 16:24:46", "businessName": "진천대장간", "placeNumber": 1080668947,
         "keyword": "충북철가공소", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:24:33", "highestDt": "2025-03-09 01:27:11", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},




        {"no": 168, "regDt": "2024-11-18 21:09", "businessName": "나만의휴일", "placeNumber": 1676621764,
         "keyword": "둔산동찜질", "category": "기타", "initialRank": 2, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김주성", "blogReviews": 50, "visitorReviews": 156, "advertisement": "",
         "rankChkDt": "2025-03-24 01:03:16", "highestDt": "2025-03-09 01:03:40", "deletedYn": "N",
         "empId": "rlawntjd", "crawlYn": "Y"},
        {"no": 175, "regDt": "2024-11-18 21:09", "businessName": "온담", "placeNumber": 1665484217,
         "keyword": "대구남구공방", "category": "카페", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:03:40", "highestDt": "2025-03-09 01:04:04", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},
        {"no": 259, "regDt": "2024-11-18 21:09", "businessName": "프롬데이왁싱", "placeNumber": 1129644081,
         "keyword": "산울동왁싱", "category": "뷰티", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "서지우", "blogReviews": 0, "visitorReviews": 99, "advertisement": "",
         "rankChkDt": "2025-03-12 01:06:54", "highestDt": "2025-03-09 01:06:55", "deletedYn": "Y",
         "empId": "tjwldn", "crawlYn": "Y"},

        {"no": 406, "regDt": "2024-11-18 21:09", "businessName": "테크런 용인점", "placeNumber": 1098698239,
         "keyword": "역북키즈카페", "category": "기타", "initialRank": 9, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:10:15", "highestDt": "2025-03-09 01:11:09", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},
        {"no": 488, "regDt": "2024-11-19 16:08:33", "businessName": "육회야문연어 청주사창점", "placeNumber": 1469167964,
         "keyword": "사창본정맛집", "category": "맛집", "initialRank": 301, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-06 16:37:18", "highestDt": "2025-03-06 01:15:00", "deletedYn": "Y",
         "empId": "dhrudwn", "crawlYn": "Y"},
        {"no": 518, "regDt": "2024-11-22 09:47:38", "businessName": "테크런 용인점", "placeNumber": 1098698239,
         "keyword": "역북동키즈카페", "category": "기타", "initialRank": 8, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:13:36", "highestDt": "2025-03-09 01:15:15", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},


        {"no": 583, "regDt": "2024-11-27 19:44:22", "businessName": "버거존", "placeNumber": 1726560033,
         "keyword": "정읍수제버거", "category": "맛집", "initialRank": 3, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "심준섭", "blogReviews": 20, "visitorReviews": 56, "advertisement": "",
         "rankChkDt": "2025-03-24 01:15:37", "highestDt": "2025-03-09 01:17:29", "deletedYn": "N",
         "empId": "tlawnstjq", "crawlYn": "Y"},
        {"no": 591, "regDt": "2024-11-28 20:54:19", "businessName": "산이야", "placeNumber": 32518399,
         "keyword": "우이동밥집", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김주성", "blogReviews": 132, "visitorReviews": 519, "advertisement": "",
         "rankChkDt": "2025-03-24 01:15:50", "highestDt": "2025-03-09 01:18:03", "deletedYn": "N",
         "empId": "rlawntjd", "crawlYn": "Y"},
        {"no": 598, "regDt": "2024-11-29 15:18:10", "businessName": "진천대장간", "placeNumber": 1080668947,
         "keyword": "진천대장간", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 2, "advertisement": "",
         "rankChkDt": "2025-03-24 01:16:07", "highestDt": "2025-03-09 01:18:15", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},

        {"no": 628, "regDt": "2024-12-03 16:59:01", "businessName": "24시 열쇠집 번호키 도어락설치", "placeNumber": 1066403839,
         "keyword": "신림출장열쇠", "category": "인테리어", "initialRank": 17, "highestRank": 1, "recentRank": 54,
         "currentRank": 1, "empName": "노유민", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:16:55", "highestDt": "2025-03-06 01:19:21", "deletedYn": "N",
         "empId": "shdbals", "crawlYn": "Y"},
        {"no": 633, "regDt": "2024-12-04 18:22:10", "businessName": "브룬디", "placeNumber": 1535827102,
         "keyword": "대부도애견카페", "category": "카페", "initialRank": 10, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 17:05:02", "highestDt": "2025-03-09 01:19:07", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},

        {"no": 839, "regDt": "2024-12-19 12:32:27", "businessName": "테크런 용인점", "placeNumber": 1098698239,
         "keyword": "용인오락실", "category": "기타", "initialRank": 65, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 16:44:11", "highestDt": "2025-03-09 01:25:20", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},

        {"no": 843, "regDt": "2024-12-19 12:50:21", "businessName": "테크런 용인점", "placeNumber": 1098698239,
         "keyword": "역북동오락실", "category": "기타", "initialRank": 7, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:22:41", "highestDt": "2025-03-09 01:25:22", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},

        {"no": 894, "regDt": "2024-12-23 16:24:46", "businessName": "진천대장간", "placeNumber": 1080668947,
         "keyword": "진천대장간", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "오경주", "blogReviews": 0, "visitorReviews": 2, "advertisement": "",
         "rankChkDt": "2025-03-24 01:24:33", "highestDt": "2025-03-09 01:27:10", "deletedYn": "N",
         "empId": "dhrudwn", "crawlYn": "Y"},

        {"no": 904, "regDt": "2024-12-23 16:57:00", "businessName": "입주청소", "placeNumber": 1738307668,
         "keyword": "둔전역입주청소", "category": "청소", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김지민", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:24:52", "highestDt": "2025-03-09 01:27:19", "deletedYn": "N",
         "empId": "rlawlals", "crawlYn": "Y"},
        {"no": 907, "regDt": "2024-12-24 14:27:02", "businessName": "드림풋볼파크", "placeNumber": 1131115788,
         "keyword": "창원축구장", "category": "운동", "initialRank": 21, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김예지", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:24:54", "highestDt": "2025-03-09 01:27:20", "deletedYn": "N",
         "empId": "rladPwl", "crawlYn": "Y"},
        {"no": 995, "regDt": "2025-01-02 16:30:39", "businessName": "펀치라인복싱 미아삼양점", "placeNumber": 1063890692,
         "keyword": "삼양역복싱", "category": "운동", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김예지", "blogReviews": 3, "visitorReviews": 8, "advertisement": "",
         "rankChkDt": "2025-03-24 01:28:03", "highestDt": "2025-03-09 01:30:12", "deletedYn": "N",
         "empId": "rladPwl", "crawlYn": "Y"},
        {"no": 1010, "regDt": "2025-01-02 16:36:33", "businessName": "술고래빠라궈전문점", "placeNumber": 1827840664,
         "keyword": "천안빠라궈", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "이민정", "blogReviews": 0, "visitorReviews": 1, "advertisement": "",
         "rankChkDt": "2025-03-24 01:28:32", "highestDt": "2025-03-09 01:30:41", "deletedYn": "N",
         "empId": "dlalswjd", "crawlYn": "Y"},
        {"no": 1012, "regDt": "2025-01-02 16:36:44", "businessName": "술고래빠라궈전문점", "placeNumber": 1827840664,
         "keyword": "천안신부동빠라궈", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "이민정", "blogReviews": 0, "visitorReviews": 1, "advertisement": "",
         "rankChkDt": "2025-03-24 01:28:42", "highestDt": "2025-03-09 01:30:52", "deletedYn": "N",
         "empId": "dlalswjd", "crawlYn": "Y"},


        {"no": 1037, "regDt": "2025-01-07 15:08:08", "businessName": "가마솥팥죽", "placeNumber": 1785571772,
         "keyword": "포천가마솥팥죽", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김성하", "blogReviews": 17, "visitorReviews": 1, "advertisement": "",
         "rankChkDt": "2025-03-24 01:29:31", "highestDt": "2025-03-09 01:31:38", "deletedYn": "N",
         "empId": "rlatjdgk", "crawlYn": "Y"},
        {"no": 1041, "regDt": "2025-01-07 15:11:04", "businessName": "가마솥팥죽", "placeNumber": 1785571772,
         "keyword": "포천이동팥죽", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김성하", "blogReviews": 17, "visitorReviews": 1, "advertisement": "",
         "rankChkDt": "2025-03-24 01:29:33", "highestDt": "2025-03-09 01:31:40", "deletedYn": "N",
         "empId": "rlatjdgk", "crawlYn": "Y"},
        {"no": 1043, "regDt": "2025-01-09 10:36:56", "businessName": "설향꽃게찜", "placeNumber": 1541837092,
         "keyword": "창우언꽃게찜", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김주성", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:29:35", "highestDt": "2025-03-09 01:31:42", "deletedYn": "N",
         "empId": "rlawntjd", "crawlYn": "Y"},
        {"no": 1056, "regDt": "2025-01-09 10:50:23", "businessName": "아레나피나", "placeNumber": 1400692527,
         "keyword": "나정항카페", "category": "카페", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "안재영", "blogReviews": 88, "visitorReviews": 443, "advertisement": "",
         "rankChkDt": "2025-03-24 01:30:06", "highestDt": "2025-03-09 01:32:12", "deletedYn": "N",
         "empId": "dkswodud", "crawlYn": "Y"},
        {"no": 1057, "regDt": "2025-01-09 10:50:24", "businessName": "아레나피나", "placeNumber": 1400692527,
         "keyword": "나정고운모래해변카페", "category": "카페", "initialRank": 5, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "안재영", "blogReviews": 88, "visitorReviews": 443, "advertisement": "",
         "rankChkDt": "2025-03-24 01:30:07", "highestDt": "2025-03-09 01:32:12", "deletedYn": "N",
         "empId": "dkswodud", "crawlYn": "Y"},
        {"no": 1058, "regDt": "2025-01-09 10:50:24", "businessName": "아레나피나", "placeNumber": 1400692527,
         "keyword": "나정해변카페", "category": "카페", "initialRank": 5, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "안재영", "blogReviews": 88, "visitorReviews": 443, "advertisement": "",
         "rankChkDt": "2025-03-24 01:30:07", "highestDt": "2025-03-09 01:32:13", "deletedYn": "N",
         "empId": "dkswodud", "crawlYn": "Y"},
        {"no": 1072, "regDt": "2025-01-10 16:13:15", "businessName": "황제갈빗", "placeNumber": 1805361312,
         "keyword": "파주산내단체모임", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김정현", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:30:28", "highestDt": "2025-03-09 01:32:34", "deletedYn": "N",
         "empId": "rlawjdgus", "crawlYn": "Y"},
        {"no": 1086, "regDt": "2025-01-10 16:27:26", "businessName": "ABC스팀세차장 동탄점", "placeNumber": 1493711877,
         "keyword": "동탄스팀세차장", "category": "청소", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김성하", "blogReviews": 48, "visitorReviews": 16, "advertisement": "",
         "rankChkDt": "2025-03-24 01:31:29", "highestDt": "2025-03-09 01:33:14", "deletedYn": "N",
         "empId": "rlatjdgk", "crawlYn": "Y"},
        {"no": 1091, "regDt": "2025-01-10 16:29:18", "businessName": "ABC스팀세차장 동탄점", "placeNumber": 1493711877,
         "keyword": "동탄유막제거", "category": "청소", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김성하", "blogReviews": 48, "visitorReviews": 16, "advertisement": "",
         "rankChkDt": "2025-03-24 01:31:39", "highestDt": "2025-03-09 01:33:23", "deletedYn": "N",
         "empId": "rlatjdgk", "crawlYn": "Y"},
        {"no": 1109, "regDt": "2025-01-13 18:45:44", "businessName": "대영타이어마트", "placeNumber": 35044395,
         "keyword": "인천타이어", "category": "", "initialRank": 1, "highestRank": 1, "recentRank": 1, "currentRank": 1,
         "empName": "123", "blogReviews": 0, "visitorReviews": 51, "advertisement": "",
         "rankChkDt": "2025-01-13 18:45:44", "highestDt": None, "deletedYn": "Y", "empId": "123", "crawlYn": "Y"},
        {"no": 1117, "regDt": "2025-01-14 17:14:57", "businessName": "솔밭휴게식당", "placeNumber": 1128584163,
         "keyword": "함양점심식사", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김예지", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:33:15", "highestDt": "2025-03-09 01:34:53", "deletedYn": "N",
         "empId": "rladPwl", "crawlYn": "Y"},
        {"no": 1153, "regDt": "2025-01-16 11:09:20", "businessName": "쿤타이", "placeNumber": 21856565,
         "keyword": "서초역마사지", "category": "뷰티", "initialRank": 8, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김정현", "blogReviews": 0, "visitorReviews": 15, "advertisement": "",
         "rankChkDt": "2025-03-24 01:34:00", "highestDt": "2025-03-09 01:35:33", "deletedYn": "N",
         "empId": "rlawjdgus", "crawlYn": "Y"},
        {"no": 1183, "regDt": "2025-01-17 11:32:16", "businessName": "오렌지보틀 익산점", "placeNumber": 1963686189,
         "keyword": "익산바틀샵", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "임중구", "blogReviews": 33, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:35:03", "highestDt": "2025-03-09 01:36:33", "deletedYn": "N",
         "empId": "dlawndrn", "crawlYn": "Y"},
        {"no": 1234, "regDt": "2025-01-20 17:52:51", "businessName": "소보로 베이커리카페", "placeNumber": 1374743843,
         "keyword": "평택서정동베이커리", "category": "카페", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "안재영", "blogReviews": 24, "visitorReviews": 661, "advertisement": "",
         "rankChkDt": "2025-03-24 01:37:31", "highestDt": "2025-03-09 01:39:05", "deletedYn": "N",
         "empId": "dkswodud", "crawlYn": "Y"},
        {"no": 1243, "regDt": "2025-01-21 09:39:51", "businessName": "함평해장 마곡본점", "placeNumber": 1928810930,
         "keyword": "마곡역해장국", "category": "맛집", "initialRank": 5, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김도연", "blogReviews": 128, "visitorReviews": 295, "advertisement": "",
         "rankChkDt": "2025-03-24 01:37:56", "highestDt": "2025-03-09 01:39:18", "deletedYn": "N",
         "empId": "rlaehdus", "crawlYn": "Y"},
        {"no": 1251, "regDt": "2025-01-21 11:18:36", "businessName": "권혜진영어교습소", "placeNumber": 1573190047,
         "keyword": "명장동영어학원", "category": "교육", "initialRank": 17, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "정민기", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-02-06 01:38:43", "highestDt": "2025-02-06 01:38:43", "deletedYn": "Y",
         "empId": "wjdalsrl", "crawlYn": "Y"},
        {"no": 1293, "regDt": "2025-01-22 18:29:08", "businessName": "그리심옴므", "placeNumber": 1053679147,
         "keyword": "장위동정장", "category": "기타", "initialRank": 6, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "이민정", "blogReviews": 0, "visitorReviews": 10, "advertisement": "",
         "rankChkDt": "2025-03-24 01:40:31", "highestDt": "2025-03-09 01:41:49", "deletedYn": "N",
         "empId": "dlalswjd", "crawlYn": "Y"},
        {"no": 1322, "regDt": "2025-01-31 15:06:01", "businessName": "제주방충망 지아하우징", "placeNumber": 1994717718,
         "keyword": "제주도방충망", "category": "인테리어", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "노유민", "blogReviews": 0, "visitorReviews": 1, "advertisement": "",
         "rankChkDt": "2025-03-24 01:42:00", "highestDt": "2025-03-09 01:43:09", "deletedYn": "N",
         "empId": "shdbals", "crawlYn": "Y"},
        {"no": 1323, "regDt": "2025-01-31 15:06:02", "businessName": "제주방충망 지아하우징", "placeNumber": 1994717718,
         "keyword": "제주방충망", "category": "인테리어", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "노유민", "blogReviews": 0, "visitorReviews": 1, "advertisement": "",
         "rankChkDt": "2025-03-24 01:42:01", "highestDt": "2025-03-09 01:43:10", "deletedYn": "N",
         "empId": "shdbals", "crawlYn": "Y"},
        {"no": 1345, "regDt": "2025-02-03 17:34:42", "businessName": "동경어시장", "placeNumber": 1520686556,
         "keyword": "연제구회맛집", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "노유민", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:43:06", "highestDt": "2025-03-09 01:44:04", "deletedYn": "N",
         "empId": "shdbals", "crawlYn": "Y"},
        {"no": 1382, "regDt": "2025-02-04 18:20:02", "businessName": "태양개발", "placeNumber": 1782398891,
         "keyword": "응암동유리", "category": "인테리어", "initialRank": 8, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "이민정", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:44:19", "highestDt": "2025-03-09 01:45:40", "deletedYn": "N",
         "empId": "dlalswjd", "crawlYn": "Y"},
        {"no": 1391, "regDt": "2025-02-05 15:43:47", "businessName": "양파이 장기동 라베니체점", "placeNumber": 1923590958,
         "keyword": "장기동양갈비", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "노유민", "blogReviews": 325, "visitorReviews": 455, "advertisement": "",
         "rankChkDt": "2025-03-24 01:44:34", "highestDt": "2025-03-09 01:46:01", "deletedYn": "N",
         "empId": "shdbals", "crawlYn": "Y"},
        {"no": 1401, "regDt": "2025-02-05 16:42:40", "businessName": "돼지익스프레스", "placeNumber": 19454992,
         "keyword": "강서구이사전문", "category": "인테리어", "initialRank": 74, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김성하", "blogReviews": 0, "visitorReviews": 4, "advertisement": "",
         "rankChkDt": "2025-03-24 01:44:44", "highestDt": "2025-03-09 01:46:21", "deletedYn": "N",
         "empId": "rlatjdgk", "crawlYn": "Y"},
        {"no": 1428, "regDt": "2025-02-07 16:04:17", "businessName": "쟈스민미용실", "placeNumber": 1234325566,
         "keyword": "월평역여자머리", "category": "뷰티", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "임중구", "blogReviews": 7, "visitorReviews": 38, "advertisement": "",
         "rankChkDt": "2025-03-24 01:45:24", "highestDt": "2025-03-09 01:47:06", "deletedYn": "N",
         "empId": "dlawndrn", "crawlYn": "Y"},
        {"no": 1435, "regDt": "2025-02-07 17:43:57", "businessName": "노블아로마 서귀포본점", "placeNumber": 1226567335,
         "keyword": "서귀포아로마마사지", "category": "뷰티", "initialRank": 8, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "노유민", "blogReviews": 0, "visitorReviews": 1038, "advertisement": "",
         "rankChkDt": "2025-03-24 01:45:28", "highestDt": "2025-03-13 01:44:21", "deletedYn": "N",
         "empId": "shdbals", "crawlYn": "Y"},
        {"no": 1436, "regDt": "2025-02-07 17:43:58", "businessName": "노블아로마 서귀포본점", "placeNumber": 1226567335,
         "keyword": "법환동마사지", "category": "뷰티", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "노유민", "blogReviews": 0, "visitorReviews": 1038, "advertisement": "",
         "rankChkDt": "2025-03-24 01:45:29", "highestDt": "2025-03-09 01:47:21", "deletedYn": "N",
         "empId": "shdbals", "crawlYn": "Y"},
        {"no": 1474, "regDt": "2025-02-10 17:59:27", "businessName": "통통상회", "placeNumber": 1362962683,
         "keyword": "남천역횟집", "category": "맛집", "initialRank": 63, "highestRank": 1, "recentRank": 42,
         "currentRank": 1, "empName": "김예지", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:46:32", "highestDt": "2025-03-15 01:44:26", "deletedYn": "N",
         "empId": "rladPwl", "crawlYn": "Y"},
        {"no": 1481, "regDt": "2025-02-11 17:14:28", "businessName": "일죽24시레저사우나", "placeNumber": 1208352579,
         "keyword": "부천찜질방", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김예지", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:46:42", "highestDt": "2025-03-09 01:48:25", "deletedYn": "N",
         "empId": "rladPwl", "crawlYn": "Y"},
        {"no": 1482, "regDt": "2025-02-11 17:14:29", "businessName": "일죽24시레저사우나", "placeNumber": 1208352579,
         "keyword": "심곡동찜질방", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "김예지", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-02-26 01:49:13", "highestDt": "2025-02-26 01:49:13", "deletedYn": "Y",
         "empId": "rladPwl", "crawlYn": "Y"},
        {"no": 1494, "regDt": "2025-02-11 17:50:20", "businessName": "여리한다이어트 광주서구점", "placeNumber": 1263915307,
         "keyword": "농성동다이어트", "category": "운동", "initialRank": 3, "highestRank": 1, "recentRank": 2,
         "currentRank": 1, "empName": "임중구", "blogReviews": 0, "visitorReviews": 221, "advertisement": "",
         "rankChkDt": "2025-03-24 01:47:07", "highestDt": "2025-03-09 01:48:51", "deletedYn": "N",
         "empId": "dlawndrn", "crawlYn": "Y"},
        {"no": 1496, "regDt": "2025-02-12 17:59:05", "businessName": "그루공방", "placeNumber": 1050796091,
         "keyword": "남양주공방", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "이채원", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-02-13 17:16:21", "highestDt": "2025-02-13 01:50:03", "deletedYn": "Y",
         "empId": "dlcodnjs", "crawlYn": "Y"},
        {"no": 1497, "regDt": "2025-02-12 17:59:06", "businessName": "그루공방", "placeNumber": 1050796091,
         "keyword": "호평동공방", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "이채원", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:47:09", "highestDt": "2025-03-09 01:48:52", "deletedYn": "N",
         "empId": "dlcodnjs", "crawlYn": "Y"},
        {"no": 1498, "regDt": "2025-02-12 17:59:07", "businessName": "그루공방", "placeNumber": 1050796091,
         "keyword": "평내호평역공방", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "이채원", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-02-17 13:25:51", "highestDt": "2025-02-17 01:50:24", "deletedYn": "Y",
         "empId": "dlcodnjs", "crawlYn": "Y"},
        {"no": 1499, "regDt": "2025-02-12 17:59:07", "businessName": "그루공방", "placeNumber": 1050796091,
         "keyword": "남양주종이공방", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "이채원", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:47:09", "highestDt": "2025-03-09 01:48:53", "deletedYn": "N",
         "empId": "dlcodnjs", "crawlYn": "Y"},
        {"no": 1501, "regDt": "2025-02-12 17:59:08", "businessName": "그루공방", "placeNumber": 1050796091,
         "keyword": "호평동종이공방", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "이채원", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:47:10", "highestDt": "2025-03-09 01:48:54", "deletedYn": "N",
         "empId": "dlcodnjs", "crawlYn": "Y"},
        {"no": 1502, "regDt": "2025-02-12 17:59:09", "businessName": "그루공방", "placeNumber": 1050796091,
         "keyword": "평내호평역종이공방", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "이채원", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 01:47:11", "highestDt": "2025-03-09 01:48:54", "deletedYn": "N",
         "empId": "dlcodnjs", "crawlYn": "Y"},
        {"no": 1629, "regDt": "2025-02-20 16:51:15", "businessName": "테스트", "placeNumber": 1456868504,
         "keyword": "백두신여당", "category": "", "initialRank": 1, "highestRank": 1, "recentRank": 1, "currentRank": 1,
         "empName": "", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-02-20 16:51:15", "highestDt": None, "deletedYn": "Y", "empId": "", "crawlYn": "Y"},
        {"no": 1884, "regDt": "2025-03-17 18:17:22", "businessName": "엠투", "placeNumber": 1701994680,
         "keyword": "단계동노래방", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "심준섭", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 02:02:51", "highestDt": "2025-03-17 18:17:22", "deletedYn": "N",
         "empId": "tlawnstjq", "crawlYn": "Y"},
        {"no": 1888, "regDt": "2025-03-17 18:17:34", "businessName": "엠투", "placeNumber": 1701994680,
         "keyword": "원주노래방", "category": "기타", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "심준섭", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 10:52:48", "highestDt": "2025-03-17 18:17:34", "deletedYn": "N",
         "empId": "tlawnstjq", "crawlYn": "Y"},
        {"no": 1892, "regDt": "2025-03-17 18:23:18", "businessName": "담빛건강마사지", "placeNumber": 1393878938,
         "keyword": "고양화정역커플마사지", "category": "뷰티", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "노유민", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 02:03:15", "highestDt": "2025-03-17 18:23:18", "deletedYn": "N",
         "empId": "shdbals", "crawlYn": "Y"},
        {"no": 1961, "regDt": "2025-03-22 17:17:48", "businessName": "영흥도커플펜션", "placeNumber": 1320947611,
         "keyword": "1320947611", "category": "1320947611", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "테스트", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-22 17:17:48", "highestDt": None, "deletedYn": "Y", "empId": "test33333",
         "crawlYn": "Y"},
        {"no": 1962, "regDt": "2025-03-22 17:26:32", "businessName": "원주우삼겹", "placeNumber": 1651999364,
         "keyword": "1651999364", "category": "1651999364", "initialRank": 111, "highestRank": 111, "recentRank": 1,
         "currentRank": 1, "empName": "테스트1", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-22 17:26:32", "highestDt": None, "deletedYn": "Y", "empId": "1651999364",
         "crawlYn": "N"},
        {"no": 1971, "regDt": "2025-03-24 16:27:34", "businessName": "대한맥주집 울산달동점", "placeNumber": 1466248104,
         "keyword": "", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1, "currentRank": 1,
         "empName": "김민정", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 16:27:34", "highestDt": "2025-03-24 16:27:34", "deletedYn": "Y",
         "empId": "rlaalswjd", "crawlYn": "Y"},
        {"no": 1991, "regDt": "2025-03-24 17:24:05", "businessName": "통큰솥뚜껑닭볶음탕 충북혁신도시점", "placeNumber": 1534302924,
         "keyword": "음성닭볶음탕", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1,
         "currentRank": 1, "empName": "이채원", "blogReviews": 151, "visitorReviews": 180, "advertisement": "",
         "rankChkDt": "2025-03-24 17:24:05", "highestDt": "2025-03-24 17:24:05", "deletedYn": "N",
         "empId": "dlcodnjs", "crawlYn": "Y"},
        {"no": 1994, "regDt": "2025-03-24 17:24:09", "businessName": "통큰솥뚜껑닭볶음탕 충북혁신도시점", "placeNumber": 1534302924,
         "keyword": "음석한식", "category": "맛집", "initialRank": 1, "highestRank": 1, "recentRank": 1, "currentRank": 1,
         "empName": "이채원", "blogReviews": 0, "visitorReviews": 0, "advertisement": "",
         "rankChkDt": "2025-03-24 17:25:08", "highestDt": "2025-03-24 17:24:09", "deletedYn": "N",
         "empId": "dlcodnjs", "crawlYn": "Y"}]



def get_current_rank():
    try:
        params = {
            'type': 'currentRank'
        }
        response = requests.get(SELECT_URL, params=params)

        print(f"📡 상태 코드: {response.status_code}")
        print(f"📄 응답 본문:\n{response.text}")

        response.raise_for_status()  # 에러 코드면 예외 발생

        data = response.json()
        print(f"{get_current_time()} ✅ 응답 수신 성공")
        return data

    except requests.exceptions.RequestException as e:
        print(f"{get_current_time()} ⚠ 요청 실패: {e}")
    except ValueError as e:
        print(f"{get_current_time()} ⚠ JSON 파싱 실패: {e}")



def scroll_slowly_to_bottom(driver, obj):
    try:
        driver.switch_to.default_content()

        # 최초 iframe 진입 (한 번만!)
        WebDriverWait(driver, 15).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "searchIframe"))
        )

        scrollable_div_selector = 'div#_pcmap_list_scroll_container'
        target_name = obj.get('businessName', '').strip()
        business_names = []

        while True:
            try:
                scrollable_div = WebDriverWait(driver, 4).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, scrollable_div_selector))
                )
            except TimeoutException:
                try:
                    no_result_div = driver.find_element(By.CLASS_NAME, "FYvSc")
                    if no_result_div.text == "조건에 맞는 업체가 없습니다.":
                        print("조건에 맞는 업체가 없습니다.")
                except Exception:
                    pass
                return 999

            ActionChains(driver).move_to_element(scrollable_div).perform()
            time.sleep(1)

            prev_height = -1
            no_change_count = 0

            # 스크롤 끝까지 내리기
            while True:
                for _ in range(7):
                    driver.execute_script("arguments[0].scrollTop += 150;", scrollable_div)
                    time.sleep(0.3)

                time.sleep(1)

                current_scroll = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)
                max_scroll_height = driver.execute_script(
                    "return arguments[0].scrollHeight - arguments[0].clientHeight;", scrollable_div
                )
                if current_scroll >= max_scroll_height:
                    print(f"{get_current_time()} ✅ 스크롤이 끝까지 내려졌습니다.")
                    break

                # if current_scroll >= max_scroll_height:
                #     if prev_height == max_scroll_height:
                #         no_change_count += 1
                #     else:
                #         no_change_count = 0
                #
                #     if no_change_count >= 3:
                #         print(f"{get_current_time()} ✅ 스크롤이 끝까지 내려졌습니다.")
                #         break
                #
                #     prev_height = max_scroll_height
                # else:
                #     prev_height = max_scroll_height

            # 현재 페이지에서 사업장 이름 추출
            li_elements = scrollable_div.find_elements(By.CSS_SELECTOR, 'ul > li')
            for li in li_elements:
                try:
                    # 광고 요소는 건너뛰기
                    ad_elements = li.find_elements(By.CSS_SELECTOR, 'span.place_blind')
                    if any(ad.text.strip() == '광고' for ad in ad_elements):
                        continue  # 광고면 건너뛰기

                    # 세 가지 클래스 중 먼저 발견되는 것으로 이름 가져오기
                    name_element = None
                    for cls in ['span.TYaxT', 'span.YwYLL', 'span.t3s7S', 'span.CMy2_']:
                        try:
                            name_element = li.find_element(By.CSS_SELECTOR, cls)
                            if name_element:
                                break
                        except:
                            continue

                    if name_element:
                        business_name = name_element.text.strip()
                        if business_name and business_name not in business_names:
                            business_names.append(business_name)

                except Exception as e:
                    print(f"⚠️ 요소 처리 중 오류 발생: {e}")
                    continue

            print(f"{get_current_time()} 📌 현재까지 누적된 사업장 목록: {business_names}")

            # 타겟 이름이 있는지 확인
            if target_name in business_names:
                matched_index = business_names.index(target_name)
                print(f"{get_current_time()} ✅ '{target_name}'의 위치: {matched_index + 1}번째")
                driver.switch_to.default_content()
                return matched_index + 1

            # 다음 페이지로 이동 가능한지 체크
            try:
                # 현재 페이지 확인
                pages = driver.find_elements(By.CSS_SELECTOR, "div.zRM9F > a.mBN2s")
                current_page_index = -1

                for idx, page in enumerate(pages):
                    classes = page.get_attribute('class')
                    if 'qxokY' in classes:
                        current_page_index = idx
                        break

                if current_page_index == -1:
                    print(f"{get_current_time()} ⚠ 현재 페이지를 찾을 수 없습니다.")
                    break

                # 다음 페이지가 존재하는지 확인
                if current_page_index + 1 < len(pages):
                    next_page_button = pages[current_page_index + 1]
                    driver.execute_script("arguments[0].click();", next_page_button)
                    print(f"{get_current_time()} 📄 다음 페이지 ({current_page_index + 2})로 이동합니다.")
                    time.sleep(3)  # 페이지 로딩 대기
                else:
                    # 다음 페이지 그룹으로 이동 가능한지 체크 (마지막 '>' 버튼)
                    next_group_button = driver.find_element(By.CSS_SELECTOR,
                                                            "div.zRM9F > a.eUTV2[aria-disabled='false']:last-child")
                    driver.execute_script("arguments[0].click();", next_group_button)
                    print(f"{get_current_time()} 📄 다음 페이지 그룹으로 이동합니다.")
                    time.sleep(3)  # 페이지 로딩 대기

            except Exception:
                # 다음 페이지가 없으면 종료
                print(f"{get_current_time()} ⛔️ 다음 페이지가 없습니다")
                break

        # 마지막까지 못 찾은 경우
        last_position = len(business_names) + 1  # 꼴등 처리
        print(f"{get_current_time()} ⚠ '{target_name}'을(를) 찾지 못했습니다. 꼴등 처리 위치: {last_position}")
        driver.switch_to.default_content()
        return last_position

    except Exception as e:
        print(f"{get_current_time()} ⚠ [ERROR] 스크롤 중 오류: {e}")



def naver_cralwing():
    driver = setup_driver()
    driver.get("https://map.naver.com")
    try:

        time.sleep(2)  # 페이지 로딩 대기

        # 2. 현재 순위 가져오기
        obj_list = get_current_rank()
        # obj_list = get_current_rank_json()

        for obj in obj_list:

            if obj.get("crawlYn") == 'N':
                continue

            keyword = obj.get("keyword")
            print(f"{get_current_time()} 🔍 검색 키워드: {keyword}")

            # 3. 검색창 찾기 및 키워드 입력
            try:

                driver.switch_to.default_content()

                search_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "input_search"))
                )

                # 확실한 초기화 방법: clear() 후 backspace/delete 키 반복 전송
                search_input.click()
                search_input.clear()

                # 기존 내용을 완벽히 지우기 위한 확실한 조작 추가
                search_input.send_keys(Keys.CONTROL + "a")  # Ctrl + A 전체 선택
                search_input.send_keys(Keys.DELETE)  # Delete 키 눌러서 삭제
                time.sleep(0.3)

                search_input.send_keys(keyword)
                time.sleep(0.5)

                # 4. 검색 버튼 클릭
                # Enter 키를 눌러 검색 실행
                search_input.send_keys(Keys.ENTER)

                time.sleep(3)  # 검색 결과 대기 (필요 시 더 조절)

                current_rank = scroll_slowly_to_bottom(driver, obj)
                obj['currentRank'] = current_rank
                obj['rankChkDt'] = get_current_time()
                if int(obj.get("highestRank")) >= int(current_rank):
                    obj['highestRank'] = current_rank
                    obj['highestDt'] = get_current_time()

            except Exception as e:
                print(f"{get_current_time()} ⚠ [ERROR] 키워드 '{keyword}' 검색 중 오류 발생: {e}")

        update_obj_list(obj_list)

    except Exception as e:
        print(f"{get_current_time()} ⚠ [ERROR] 크롤링 중 오류 발생: {e}")


# 실행 (메인 루프)
if __name__ == "__main__":
    naver_cralwing()
    print(f"{get_current_time()} 순위 보정 프로그램 정상 시작 완료!!!")

    # 매일 04:00에 test() 실행
    schedule.every().day.at("04:00").do(naver_cralwing)

    # 1초마다 실행시간이 도래 했는지 확인
    while True:
        schedule.run_pending()
        time.sleep(1)
