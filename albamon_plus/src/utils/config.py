from src.vo.site import Site

SITE_LIST = [
    Site("알바몬", "ALBAMON", "#FF6600",            enabled=True, user=False, setting=[]),
    Site("네이버플레이스", "NAVER_PLACE", "#03C75A", enabled=True, user=False, setting=[]),
    Site("쿠팡", "COUPANG", "#D73227",             enabled=True, user=False, setting=[
        {'name': '제품 딜레이 시간(초)', 'code': 'html_source_delay_time','value': 10},
        {'name': '크롬 재시작 딜레이 시간(초)', 'code': 'chrome_delay_time','value': 3600}
    ]),
    Site("알바천국", "ALBA", "#FFF230",             enabled=True, user=False, setting=[
        {'name': '감지 대기 딜레이 시간(초)', 'code': 'alba_delay_time','value': 1200}
    ]),
]

# 전역 변수
server_url = "http://vjrvj.cafe24.com"
server_name = "MyAppAutoLogin"








