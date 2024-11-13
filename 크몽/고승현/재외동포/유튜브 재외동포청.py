from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import requests
import json
import re

countries = [
    # 아시아
    "아프가니스탄", "아르메니아", "아제르바이잔", "바레인", "방글라데시", "부탄", "브루나이",
    "캄보디아", "중국", "키프로스", "동티모르", "조지아", "인도", "인도네시아", "이란",
    "이라크", "이스라엘", "일본", "요르단", "카자흐스탄", "쿠웨이트", "키르기스스탄",
    "라오스", "레바논", "말레이시아", "몰디브", "몽골", "미얀마", "네팔", "북한", "오만",
    "파키스탄", "팔레스타인", "필리핀", "카타르", "사우디아라비아", "싱가포르", "대한민국",
    "스리랑카", "시리아", "타지키스탄", "태국", "터키", "투르크메니스탄", "아랍에미리트",
    "우즈베키스탄", "베트남", "예멘",

    # 유럽
    "알바니아", "안도라", "오스트리아", "벨라루스", "벨기에", "보스니아 헤르체고비나",
    "불가리아", "크로아티아", "체코", "덴마크", "에스토니아", "핀란드", "프랑스", "독일",
    "그리스", "헝가리", "아이슬란드", "아일랜드", "이탈리아", "라트비아", "리히텐슈타인",
    "리투아니아", "룩셈부르크", "몰타", "몰도바", "모나코", "몬테네그로", "네덜란드",
    "북마케도니아", "노르웨이", "폴란드", "포르투갈", "루마니아", "러시아", "산마리노",
    "세르비아", "슬로바키아", "슬로베니아", "스페인", "스웨덴", "스위스", "우크라이나",
    "영국", "바티칸 시국", "코소보",

    # 아프리카
    "알제리", "앙골라", "베냉", "보츠와나", "부르키나파소", "부룬디", "카보베르데", "카메룬",
    "중앙아프리카공화국", "차드", "코모로", "콩고 공화국", "콩고 민주 공화국", "지부티",
    "이집트", "적도기니", "에리트레아", "에스와티니", "에티오피아", "가봉", "감비아", "가나",
    "기니", "기니비사우", "코트디부아르", "케냐", "레소토", "라이베리아", "리비아",
    "마다가스카르", "말라위", "말리", "모리타니아", "모리셔스", "모로코", "모잠비크",
    "나미비아", "니제르", "나이지리아", "르완다", "상투메 프린시페", "세네갈", "세이셸",
    "시에라리온", "소말리아", "남아프리카공화국", "남수단", "수단", "탄자니아", "토고",
    "튀니지", "우간다", "잠비아", "짐바브웨",

    # 북아메리카
    "앵귈라", "앤티가 바부다", "바하마", "바베이도스", "벨리즈", "버뮤다",
    "보네르", "세인트 유스타티우스와 사바", "영국령 버진아일랜드", "캐나다", "케이맨 제도",
    "코스타리카", "쿠바", "퀴라소", "도미니카 공화국", "엘살바도르", "그레나다", "과들루프",
    "과테말라", "아이티", "온두라스", "자메이카", "마르티니크", "멕시코", "몬세라트",
    "니카라과", "파나마", "푸에르토리코", "세인트키츠 네비스", "세인트루시아", "세인트빈센트 그레나딘",
    "신트마르턴", "트리니다드 토바고", "터크스 케이커스 제도", "미국", "미국령 버진아일랜드",

    # 남아메리카
    "아르헨티나", "볼리비아", "브라질", "칠레", "콜롬비아", "에콰도르", "포클랜드 제도",
    "프랑스령 기아나", "가이아나", "파라과이", "페루", "수리남", "우루과이", "베네수엘라",

    # 오세아니아
    "미국령 사모아", "오스트레일리아", "쿡 제도", "피지", "프랑스령 폴리네시아", "괌",
    "키리바시", "마셜 제도", "미크로네시아 연방", "나우루", "뉴칼레도니아", "뉴질랜드",
    "니우에", "북마리아나 제도", "팔라우", "파푸아뉴기니", "피트케언 제도", "사모아",
    "솔로몬 제도", "토켈라우", "통가", "투발루", "바누아투", "왈리스 푸투나",

    # 중동
    "바레인", "이란", "이라크", "이스라엘", "요르단", "쿠웨이트", "레바논", "오만",
    "팔레스타인", "카타르", "사우디아라비아", "시리아", "아랍에미리트", "예멘"
]


# HTML 파일을 BeautifulSoup 객체로 읽어들이는 함수
def load_html_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return BeautifulSoup(file, "html.parser")

# 콘텐츠 내용
def extract_content_hash_tag(content_url):
    # 요청 헤더 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # URL에서 HTML 페이지 가져오기
    response = requests.get(content_url, headers=headers)
    if response.status_code != 200:
        print(f"페이지를 불러오는 데 실패했습니다. 상태 코드: {response.status_code}")
        return None

    # BeautifulSoup으로 HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")

    # <script> 태그 중 'ytInitialData' JSON이 포함된 스크립트를 찾기
    script_tag = soup.find("script", string=re.compile("ytInitialData"))
    if not script_tag:
        print("ytInitialData를 포함한 스크립트를 찾을 수 없습니다.")
        return None

    # JSON 데이터 추출 (ytInitialData 이후의 JSON 데이터만 남기기)
    script_content = script_tag.string
    json_data_match = re.search(r'var ytInitialData = ({.*});', script_content)
    if not json_data_match:
        print("ytInitialData JSON을 찾을 수 없습니다.")
        return None

    # JSON 문자열 파싱
    json_data = json.loads(json_data_match.group(1))

    # JSON 데이터 내의 superTitleLink -> runs -> text 값을 추출
    try:
        runs = json_data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][0]["videoPrimaryInfoRenderer"]["superTitleLink"]["runs"]
        hashtags = [run["text"].replace("#", "") for run in runs if run["text"].strip() != ""]
        # 배열이 1개인 경우에는 그대로 출력하고, 2개 이상인 경우에만 join
        if len(hashtags) == 1:
            result = hashtags[0]
        else:
            result = ', '.join(hashtags[:2])
        return result
    except KeyError:
        print("해당 경로에서 데이터를 찾을 수 없습니다.")
        return None


# 콘텐츠 주소 추출 함수
def extract_content_url(content):
    try:
        thumbnail = content.select_one('a#thumbnail.yt-simple-endpoint.inline-block.style-scope.ytd-thumbnail')
        return "https://www.youtube.com" + thumbnail["href"] if thumbnail else None
    except:
        return None

# 콘텐츠 이미지 URL 추출 함수
def extract_content_image_url(content):
    try:
        img_tag = content.select_one('a#thumbnail img')
        img_url = img_tag.get("src") or img_tag.get("data-src") or img_tag.get("data-thumb") if img_tag else None
        return img_url
    except:
        return None

# 콘텐츠 명 추출 함수
def extract_content_name(content):
    try:
        title_element = content.select_one('#details.style-scope.ytd-rich-grid-media #video-title.style-scope.ytd-rich-grid-media')
        return title_element.text.strip() if title_element else None
    except:
        return None

# 공개일자 계산 함수
def calculate_content_year(time_text, today):
    if "일 전" in time_text:
        days = int(time_text.split("일")[0].strip())
        return today - timedelta(days=days)
    elif "주 전" in time_text:
        weeks = int(time_text.split("주")[0].strip())
        return today - timedelta(weeks=weeks)
    elif "개월 전" in time_text:
        months = int(time_text.split("개월")[0].strip())
        return today - timedelta(days=months * 30)
    elif "년 전" in time_text:
        years = int(time_text.split("년")[0].strip())
        return today - timedelta(days=years * 365)
    return today

# 콘텐츠 리스트 생성 함수
def create_content_list(soup, today):
    global countries

    content_data = []
    contents = soup.select("#contents #content")

    for content in contents:

        content_name = extract_content_name(content)
        # '콘텐츠 명'에서 각 국가를 확인
        target_region = '세계'  # 기본값은 '세계'
        for country in countries:
            if country in content_name:
                target_region = country
                break  # 첫 번째 국가를 찾으면 더 이상 검색하지 않음

        data = {
            "콘텐츠 명": content_name,
            "콘텐츠 분류": '유튜브 영상',
            "공개일자": '',
            "노출매체": '제외동포청 유튜브',
            "퀄리티": '1080p',
            '콘텐츠 대상지역': target_region,
            '콘텐츠 내용': '',
            '콘텐츠 저작권 소유처': '제외동포청',
            '라이선스': '제작 저작권 소유',
            '콘텐츠 시청 방법': '유튜브',
            "이미지 url": extract_content_image_url(content),
            "콘텐츠 주소": extract_content_url(content),
        }

        data["콘텐츠 내용"] = extract_content_hash_tag(data["콘텐츠 주소"])

        try:
            metadata_line = content.select_one("#metadata-line")
            spans = metadata_line.select("span.inline-metadata-item.style-scope.ytd-video-meta-block") if metadata_line else []
            if len(spans) > 1:
                time_text = spans[1].text.strip()
                data["공개일자"] = calculate_content_year(time_text, today).strftime('%Y-%m-%d')
        except:
            data["공개일자"] = None

        print(f'data : {data}')
        content_data.append(data)
    return content_data

# 엑셀 파일로 저장하는 함수
def save_to_excel(content_data, file_name="제외동포청 Youtube.xlsx"):
    df = pd.DataFrame(content_data)
    df.to_excel(file_name, index=False)

# 메인 함수
def main():
    file_path = "제외동포청 Youtube.html"  # HTML 파일 경로 설정
    today = datetime.today()

    # HTML 파일 로드
    soup = load_html_file(file_path)

    # 콘텐츠 리스트 생성
    content_data = create_content_list(soup, today)

    # 엑셀 파일로 저장
    save_to_excel(content_data)

if __name__ == "__main__":
    main()
