from src.vo.site import Site

SITE_LIST = [
    Site("알바몬", "ALBAMON", "#FF6600", enabled=True, user=False, setting=[]),
    Site("네이버플레이스", "NAVER_PLACE", "#03C75A", enabled=True, user=False, setting=[]),
    Site("쿠팡", "COUPANG", "#D73227", enabled=True, user=False, setting=[
        {'name': '제품 딜레이 시간(초)', 'code': 'html_source_delay_time','value': 6},
        {'name': '크롬 재시작 딜레이 시간(초)', 'code': 'chrome_delay_time','value': 3600}
    ]),
    Site("알바천국", "ALBA", "#FFF230", enabled=True, user=False, setting=[
        {'name': '감지 대기 딜레이 시간(초)', 'code': 'alba_delay_time','value': 1200}
    ]),
    Site("소통한방병원", "SOTONG", "#29ADA6", enabled=True, user=False, setting=[
        {'name': '시작 날짜(YYYY-MM-DD)', 'code': 'fr_date','value': '', 'type': 'input'},
        {'name': '종료 날짜(YYYY-MM-DD)', 'code': 'to_date','value': '', 'type': 'input'}
    ]),
    Site("SEOUL FOOD 2025", "SEOUL_FOOD_2025", "#000000", enabled=True, user=False, setting=[]),
    Site("네이버 블로그 글조회", "NAVER_BLOG_CTT", "#03C75A", enabled=True, user=False, setting=[
        {'name': '블로그 URL', 'code': 'url',        'value': '', 'type': 'button'},
        {'name': '게시판 선택', 'code': 'url_select', 'value': '', 'type': 'select'},
        {'name': '시작 페이지', 'code': 'st_page',    'value': '', 'type': 'input'},
        {'name': '종료 페이지', 'code': 'ed_page',    'value': '', 'type': 'input'}
    ]),
    Site("IHERB", "IHERB", "#458500", enabled=True, user=False, setting=[
        {'name': '시작 페이지', 'code': 'st_page','value': '', 'type': 'input'},
        {'name': '종료 페이지', 'code': 'ed_page','value': '', 'type': 'input'}
    ]),
]

# 전역 변수
server_url = "http://vjrvj.cafe24.com"
server_name = "MyAppAutoLogin"








