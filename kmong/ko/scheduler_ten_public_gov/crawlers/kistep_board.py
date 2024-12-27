import re

from bs4 import BeautifulSoup

from utils.date import convert_to_yyyymmdd
from utils.logger import logger
from utils.request_util import common_request


class KistepBoard:
    def __init__(self):
        self.url = "https://www.kistep.re.kr"
        self.url_main_path = 'board.es'
        self.url_main = f'{self.url}/{self.url_main_path}'
        self.payload = {
            'mid': 'a10306010000',
            'bid': '0031',
            'nPage': 1,
            'b_list': 10,
            'orderby': '',
            'dept_code': '',
            'tag': '',
            'list_no': '',
            'act': 'list',
            'cg_code': '',
            'keyField': '',
            'keyWord': ''
        }
        self.src = 'KISTEP 브리프'


    def request(self):
        return common_request(self.url_main, self.payload)


    def process_data(self, html):
        data_list = []
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 'board_pdf publication_list' 클래스의 li 요소들을 가져오기
            board_list = soup.find('ul', class_='board_pdf publication_list')
            if not board_list:
                logger.error("Board list not found")
                return []


            # ul 바로 아래 자식 li만 순회 (내부에 다른 li가 포함된 경우 제외)
            for li in board_list.find_all('li', recursive=False):
                url = ''
                ttl = ''
                reg_ymd = ''
                dmnfr_trend_no = ''

                # 'group'과 'item' 요소 찾기
                group = li.find('div', class_='group')
                item = group.find('div', class_='item') if group else None

                # 제목 추출
                title = item.find('strong', class_='title') if item else None
                a_tag = title.find('a') if title else None

                # DMNFR_TREND_NO 값 추출 (href에서 list_no 파라미터 추출)
                if a_tag and 'href' in a_tag.attrs:
                    href = a_tag['href']
                    match = re.search(r'list_no=(\d+)', href)  # list_no 값 추출
                    if match:
                        dmnfr_trend_no = match.group(1)

                ttl = a_tag.get_text(strip=True) if a_tag else ''
                url = f'{self.url}{a_tag["href"]}' if a_tag and "href" in a_tag.attrs else ''

                # 기본 정보 추출
                basic_info = item.find('ul', class_='basic_info') if item else None
                lis = basic_info.find_all('li') if basic_info else []
                reg_ymd = lis[1].find('span', class_='txt') if len(lis) > 1 else None

                reg_ymd = reg_ymd.get_text(strip=True) if reg_ymd else ''
                reg_ymd = convert_to_yyyymmdd(reg_ymd, '-')

                # 데이터 객체 구성
                data_obj = {
                    "DMNFR_TREND_NO": dmnfr_trend_no,
                    "STTS_CHG_CD": "succ",
                    "TTL": ttl,
                    "SRC": self.src,
                    "REG_YMD": reg_ymd,
                    "URL": url
                }
                data_list.append(data_obj)

            return data_list

        except Exception as e:
            logger.error(f"An error occurred while processing the data: {e}")

        finally:
            return data_list

    def run(self):
        """크롤러 실행"""
        html = self.request()
        if html:
            return self.process_data(html)
        else:
            return None