import re

from bs4 import BeautifulSoup

from utils.date import get_current_yyyy, get_current_yymmddhhmm
from utils.logger import logger
from utils.request_util import common_request


class MaffPress:
    def __init__(self):
        self.url = "https://www.maff.go.jp/j/press"
        self.url_main_path = 'index.html'
        self.url_main = f'{self.url}/{self.url_main_path}'

        self.src = '일본 농림수산성 보도자료'

    def request(self):
        return common_request(self.url_main)


    def process_data(self, html):
        data_list = []
        try:
            soup = BeautifulSoup(html, 'html.parser')

            board_list = soup.find('div', id='main_content')
            if not board_list:
                logger.error("Board list not found")
                return []

            # main_content의 직계 자식만 가져옴
            # p 태그는 날짜를 dl은 내용을 가져온다.
            children = board_list.find_all(recursive=False)

            if children:

                # h1과 h2 태그를 제외한 자식들만 필터링
                filtered_children = [child for child in children if child.name not in ['h1', 'h2']]

                if filtered_children:

                    # 날짜 세팅을 위함
                    # 현재 연도 가져오기
                    current_year = get_current_yyyy()
                    
                    # 날짜 태그가 나오고 그 뒤에 내용이 나오므로 미리 넣어둠
                    formatted_date = ''

                    # 고유 dmnfr_trend_no 세팅을 위함
                    today_str = get_current_yymmddhhmm()  # 'YYMMDDHHMM' 형식으로

                    # 2일치만 가져오기 위함
                    p_cnt = 0
                    dl_cnt = 0

                    # 결과 출력 (필터링된 자식들)
                    for child in filtered_children:

                        url = ''
                        ttl = ''
                        reg_ymd = ''
                        dmnfr_trend_no = ''

                        if p_cnt > 2:
                            break

                        if child.name == 'p' and 'list_item_date' in child.get('class', []):
                            p_cnt += 1
                            date_str = child.get_text(strip=True)  # '12月25日'와 같은 문자열
                            if date_str:
                                # 월과 일을 추출하고, 현재 연도를 붙여서 날짜 만들기
                                month, day = date_str.split('月')  # '12月'에서 '12'를 분리
                                day = day.replace('日', '')  # '25日'에서 '日'을 제거
                                formatted_date = f"{current_year}{month.zfill(2)}{day.zfill(2)}"  # yyyyMMdd 형식으로 만들기
                        else:
                            dl_cnt += 1
                            url = ''
                            ttl = ''
                            reg_ymd = formatted_date

                            # index를 두 자릿수로 포맷 (1 -> '01', 2 -> '02', ... , 10 -> '10')
                            index_str = f'{dl_cnt:02}'  # index를 두 자릿수로 변환
                            dmnfr_trend_no = f'{today_str}{index_str}'  # 'YYMMDDHHMM' + 두 자릿수 index
                            dt_tag = child.find('dt')
                            dd_tag = child.find('dd')

                            if dt_tag and dd_tag:
                                a_tag = dd_tag.find('a') if dd_tag else None

                                if a_tag:
                                    ttl = f'{dt_tag.get_text(strip=True)} {a_tag.get_text(strip=True)}'
                                    url = a_tag['href'] if 'href' in a_tag.attrs else ''

                                    # Step 2: URL이 "./"로 시작하는 경우 완전한 URL로 변환
                                    if url and url.startswith('./'):
                                        url = "https://www.maff.go.jp/j/press" + url[1:]  # "./"를 제거하고 기본 URL을 붙임

                            data_obj = {
                                "DMNFR_TREND_NO": dmnfr_trend_no,
                                "STTS_CHG_CD": "succ",
                                "TTL": ttl,
                                "SRC": self.src,
                                "REG_YMD": reg_ymd,
                                "URL": url
                            }
                            data_list.append(data_obj)

        except Exception as e:
            logger.error(f"Error : {e}")
        finally:
            return data_list


    def run(self):
        """크롤러 실행"""
        html = self.request()
        if html:
            return self.process_data(html)
        else:
            return None