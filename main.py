import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re


# kistep_gpsTrendList 요청
def kistep_gpsTrendList_request():
    url = "https://www.kistep.re.kr/gpsTrendList.es?mid=a30200000000"

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'connection': 'keep-alive',
        'host': 'www.kistep.re.kr',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }

    # 페이로드 데이터 설정
    payload = {
        'actionUrl': 'gpsTrendList.es',
        'mid': 'a30200000000',
        'list_no': '',
        'nPage': 1,
        'b_list': 10,
        'data02': '',
        'data01': '',
        'dt01_sdate': '',
        'dt01_edate': '',
        'keyField': '',
        'keyWord': ''
    }

    # POST 요청
    response = requests.post(url, headers=headers, data=payload)

    # 응답이 정상적으로 왔을 때 처리
    if response.status_code == 200:
        return response.text
    else:
        print("Failed to retrieve data")
        return None

# kistep_gpsTrendList 데이터 가공
def kistep_gpsTrendList_data(html):
    soup = BeautifulSoup(html, 'html.parser')

    # 'tstyle_list' 클래스의 테이블을 찾기
    table = soup.find('table', class_='tstyle_list')

    if not table:
        print("Table not found")
        return []

    # tbody 내의 tr 요소들을 가져오기
    tbody = table.find('tbody')
    rows = tbody.find_all('tr')

    data_list = []

    for row in rows:
        # 각 td 요소들을 추출
        tds = row.find_all('td')

        if len(tds) >= 5:
            dmnfr_trend_no = tds[0].get_text(strip=True)  # DMNFR_TREND_NO
            ttl = tds[2].find('a').get_text(strip=True)  # TTL
            ttl = ttl.replace('새글', '').strip()  # "새글" 제거하고 앞뒤 공백도 제거
            reg_ymd = tds[4].get_text(strip=True)  # REG_YMD
            url = "https://www.kistep.re.kr/gpsTrendList.es?mid=a30200000000" + tds[2].find('a')['href']  # URL

            # SRC와 STTS_CHG_CD는 고정값
            src = "한국과학기술기획평가원 S&T GPS(글로벌 과학기술정책정보서비스)"
            stts_chg_cd = "success"

            # 데이터를 객체로 구성
            data_obj = {
                "DMNFR_TREND_NO": dmnfr_trend_no,
                "STTS_CHG_CD": stts_chg_cd,
                "TTL": ttl,
                "SRC": src,
                "REG_YMD": reg_ymd,
                "URL": url
            }
            data_list.append(data_obj)

    return data_list

# kistep_gpsTrendList DB
def kistep_gpsTrendList(date):
    html = kistep_gpsTrendList_request()
    if html:
        data_list = kistep_gpsTrendList_data(html)




# kistep_board_request 요청
def kistep_board_request():
    url = "https://www.kistep.re.kr/board.es?mid=a10306010000&bid=0031"

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }

    # 페이로드 데이터 설정
    payload = {
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

    # POST 요청
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.text
    else:
        print("Failed to retrieve data")
        return None

# kistep_board_data 데이터 가공
def kistep_board_data(html):
    soup = BeautifulSoup(html, 'html.parser')

    # 'board_pdf publication_list' 클래스의 li 요소들을 가져오기
    board_list = soup.find('ul', class_='board_pdf publication_list')
    if not board_list:
        logging.error("Board list not found")
        return []

    data_list = []
    # ul 바로 아래 자식 li만 순회 (내부에 다른 li가 포함된 경우 제외)
    for li in board_list.find_all('li', recursive=False):
        try:
            # 'group'과 'item' 요소 찾기
            group = li.find('div', class_='group')
            item = group.find('div', class_='item') if group else None

            if not item:
                logging.warning("Item not found in li")
                continue  # item이 없으면 해당 li를 건너뛰기

            # 제목 추출
            title = item.find('strong', class_='title')
            a_tag = title.find('a') if title else None

            # DMNFR_TREND_NO 값 추출 (href에서 list_no 파라미터 추출)
            dmnfr_trend_no = ''
            if a_tag and 'href' in a_tag.attrs:
                href = a_tag['href']
                match = re.search(r'list_no=(\d+)', href)  # list_no 값 추출
                if match:
                    dmnfr_trend_no = match.group(1)

            ttl = a_tag.get_text(strip=True) if a_tag else ''
            url = "https://www.kistep.re.kr" + a_tag['href'] if a_tag and 'href' in a_tag.attrs else ''

            # 기본 정보 추출
            basic_info = item.find('ul', class_='basic_info')
            lis = basic_info.find_all('li') if basic_info else []
            reg_ymd = lis[1].find('span', class_='txt') if len(lis) > 1 else None

            reg_ymd_text = reg_ymd.get_text(strip=True) if reg_ymd else ''

            # 데이터 객체 구성
            data_obj = {
                "DMNFR_TREND_NO": dmnfr_trend_no,
                "STTS_CHG_CD": "success",
                "TTL": ttl,
                "SRC": "KISTEP브리프",
                "REG_YMD": reg_ymd_text,
                "URL": url
            }
            data_list.append(data_obj)

        except Exception as e:
            logging.error(f"Error processing li: {e}")
            continue  # 에러가 발생해도 다른 li는 계속 처리

    # 최종적으로 data_list 반환
    return data_list

# kistep_board DB
def kistep_board(date):
    html = kistep_board_request()
    if html:
        data_list = kistep_board_data(html)

        for data in data_list:
            print(data)




# krei_list_request 요청
def krei_list_request():
    url = "https://www.krei.re.kr/krei/selectBbsNttList.do"

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'connection': 'keep-alive',
        'host': 'www.krei.re.kr'
    }

    # 페이로드 데이터 설정
    payload = {
        'bbsNo': '76',
        'key': '271'
    }

    # POST 요청
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.text
    else:
        print("Failed to retrieve data")
        return None


# krei_list_data 데이터 가공
def krei_list_data(html):
    data_list = []

    soup = BeautifulSoup(html, 'html.parser')

    # 'tbl default' 클래스의 table 요소 찾기
    board_list = soup.find('table', class_='tbl default')
    if not board_list:
        logging.error("Board list not found")
        return []

    tbody = board_list.find('tbody')
    if not tbody:
        logging.error("tbody not found")
        return []

    # tr 요소 순회
    for index, tr in enumerate(tbody.find_all('tr', recursive=False)):
        tds = tr.find_all('td', recursive=False)

        # td 요소가 부족하면 skip
        if len(tds) < 3:
            logging.warning(f"Skipping row {index} due to insufficient td elements")
            continue

        try:
            # 'NO' 제거하고 앞뒤 공백 제거
            dmnfr_trend_no = tds[0].get_text(strip=True).replace("NO", "").strip()
            a_tag = tds[1].find('a')

            if a_tag:
                ttl = a_tag.get_text(strip=True)
                url = "https://www.krei.re.kr/krei" + a_tag['href'].lstrip('.') if 'href' in a_tag.attrs else ''
            else:
                ttl = ''
                url = ''
                logging.warning(f"No anchor tag found in row {index}")

            # '일자' 제거하고 앞뒤 공백 제거
            reg_ymd_text = tds[2].get_text(strip=True).replace("일자", "").strip()

            # 데이터 객체 구성
            data_obj = {
                "DMNFR_TREND_NO": dmnfr_trend_no,
                "STTS_CHG_CD": "success",
                "TTL": ttl,
                "SRC": "KREI 주간브리프",
                "REG_YMD": reg_ymd_text,
                "URL": url
            }
            data_list.append(data_obj)

        except Exception as e:
            logging.error(f"Error processing row {index}: {e}")
            continue  # 에러가 발생해도 다른 행은 계속 처리

    # 최종적으로 data_list 반환
    return data_list


# krei_list DB
def krei_list(date):
    html = krei_list_request()
    if html:
        data_list = krei_list_data(html)

        for data in data_list:
            print(data)



# krei_research_request 요청
def krei_research_request():
    url = "https://www.krei.re.kr/krei/research.do"

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'connection': 'keep-alive',
        'host': 'www.krei.re.kr'
    }

    # 페이로드 데이터 설정
    payload = {
        'key': '71',
        'pageType': '010302',
        'searchCnd': 'all',
        'searchKrwd': '',
        'pageIndex': '1',
    }

    # POST 요청
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.text
    else:
        print("Failed to retrieve data")
        return None


# krei_research_data 데이터 가공
def krei_research_data(html):
    data_list = []

    soup = BeautifulSoup(html, 'html.parser')

    # 'tbl default' 클래스의 table 요소 찾기
    board_list = soup.find('table', class_='tbl default')
    if not board_list:
        logging.error("Board list not found")
        return []

    tbody = board_list.find('tbody')
    if not tbody:
        logging.error("tbody not found")
        return []

    # tr 요소 순회
    for index, tr in enumerate(tbody.find_all('tr', recursive=False)):
        tds = tr.find_all('td', recursive=False)

        # td 요소가 부족하면 skip
        if len(tds) < 3:
            logging.warning(f"Skipping row {index} due to insufficient td elements")
            continue

        try:
            # 'NO' 제거하고 앞뒤 공백 제거
            dmnfr_trend_no = tds[0].get_text(strip=True).replace("번호", "").strip()
            a_tag = tds[1].find('a')

            if a_tag:
                ttl = a_tag.get_text(strip=True)
                url = "https://www.krei.re.kr/krei" + a_tag['href'].lstrip('.') if 'href' in a_tag.attrs else ''
            else:
                ttl = ''
                url = ''
                logging.warning(f"No anchor tag found in row {index}")

            # '등록일', 맨뒤.(점) 제거하고 앞뒤 공백 제거
            reg_ymd_text = tds[2].get_text(strip=True).replace("등록일", "").rstrip('.')

            # 데이터 객체 구성
            data_obj = {
                "DMNFR_TREND_NO": dmnfr_trend_no,
                "STTS_CHG_CD": "success",
                "TTL": ttl,
                "SRC": "KREI 이슈+",
                "REG_YMD": reg_ymd_text,
                "URL": url
            }
            data_list.append(data_obj)

        except Exception as e:
            logging.error(f"Error processing row {index}: {e}")
            continue  # 에러가 발생해도 다른 행은 계속 처리

    # 최종적으로 data_list 반환
    return data_list


# krei_research DB
def krei_research(date):
    html = krei_research_request()
    if html:
        data_list = krei_research_data(html)

        for data in data_list:
            print(data)




# kati_export_request 요청
def kati_export_request():
    url = "https://www.kati.net/board/exportNewsList.do"

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'connection': 'keep-alive',
        'host': 'www.kati.net',
        'origin': 'https://www.kati.net',
        'referer': 'https://www.kati.net/board/exportNewsList.do'
    }

    # 페이로드 데이터 설정
    payload = {
        'page': '1',
        'menu_dept3': '',
        'srchGubun': '',
        'dateSearch': 'year',
        'srchFr': '',
        'srchTo': '',
        'srchTp': '2',
        'srchWord': ''
    }

    # POST 요청
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.text
    else:
        print("Failed to retrieve data")
        return None


# kati_export_data 데이터 가공
def kati_export_data(html):
    data_list = []

    try:
        soup = BeautifulSoup(html, 'html.parser')

        board_list = soup.find('div', class_='board-list-area mt10')
        if not board_list:
            logging.error("Board list not found")
            return []

        ul = board_list.find('ul')
        if not ul:
            logging.error("ul not found")
            return []

        for index, li in enumerate(ul.find_all('li', recursive=False)):
            a_tag = li.find('a', recursive=False)

            if a_tag:
                before_url = "https://www.kati.net/board" + a_tag['href'].lstrip('.') if 'href' in a_tag.attrs else ''
                url = before_url.replace('\r\n\t\t\t\t\t\t', '')
                dmnfr_trend_no = ''
                ttl = ''
                reg_ymd_text = ''

                match = re.search(r'board_seq=(\d+)', a_tag['href']) if 'href' in a_tag.attrs else ''
                if match:
                    dmnfr_trend_no = match.group(1)

                ttl_tag = a_tag.find('span', class_='fs-15 ff-ngb')
                if ttl_tag:
                    ttl = ttl_tag.get_text(strip=True)

                date_tag = a_tag.find('span', class_='option-area')
                if date_tag:
                    span_tags = date_tag.find_all('span')
                    if span_tags and len(span_tags) > 0:
                        reg_ymd_text = span_tags[0].get_text(strip=True).replace("등록일", "").strip()

                data_obj = {
                    "DMNFR_TREND_NO": dmnfr_trend_no,
                    "STTS_CHG_CD": "success",
                    "TTL": ttl,
                    "SRC": "농식품수출정보-해외시장동향",
                    "REG_YMD": reg_ymd_text,
                    "URL": url
                }
                data_list.append(data_obj)

    except Exception as e:
        logging.error(f"Error : {e}")

    return data_list


# kati_export DB
def kati_export(date):
    html = kati_export_request()
    if html:
        data_list = kati_export_data(html)

        for data in data_list:
            print(data)



# kati_report_request 요청
def kati_report_request():
    url = "https://www.kati.net/board/reportORpubilcationList.do"

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'connection': 'keep-alive',
        'host': 'www.kati.net',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1'
    }

    # GET 요청
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print("Failed to retrieve data")
        return None


# kati_report_data 데이터 가공
def kati_report_data(html):
    data_list = []

    try:
        soup = BeautifulSoup(html, 'html.parser')

        board_list = soup.find('div', class_='report-list-area mt10')
        if not board_list:
            logging.error("Board list not found")
            return []

        report_items = board_list.find_all('div', class_='report-item')
        if not report_items:
            logging.error("report_items not found")
            return []

        for index, report_item in enumerate(report_items):

            url = ''
            dmnfr_trend_no = ''
            ttl = ''
            reg_ymd_text = ''

            em_tag = report_item.find('em', class_='report-tit')
            span_tag = report_item.find('span', class_='report-date')

            if em_tag:
                a_tag = em_tag.find('a')
                if a_tag:
                    before_url = "https://www.kati.net/board" + a_tag['href'].lstrip('.') if 'href' in a_tag.attrs else ''
                    url = before_url.replace('\r\n\t\t\t\t\t\t\t\t\t\t', '')
                    ttl = a_tag.get_text(strip=True)

                    match = re.search(r'board_seq=(\d+)', a_tag['href']) if 'href' in a_tag.attrs else ''
                    if match:

                        dmnfr_trend_no = match.group(1)

            if span_tag:
                reg_ymd_text = span_tag.get_text(strip=True).replace("등록일", "").strip()

            data_obj = {
                "DMNFR_TREND_NO": dmnfr_trend_no,
                "STTS_CHG_CD": "success",
                "TTL": ttl,
                "SRC": "농식품수출정보-보고서",
                "REG_YMD": reg_ymd_text,
                "URL": url
            }
            data_list.append(data_obj)

    except Exception as e:
        logging.error(f"Error : {e}")

    return data_list


# kati_report DB
def kati_report(date):
    html = kati_report_request()
    if html:
        data_list = kati_report_data(html)

        for data in data_list:
            print(data)



# stepi_report_request 요청
def stepi_report_request():
    url = "https://www.stepi.re.kr/site/stepiko/ex/bbs/reportList.do?cbIdx=1292"

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'connection': 'keep-alive',
        'host': 'www.stepi.re.kr',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1'
    }

    # GET 요청
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        return response.text
    else:
        print("Failed to retrieve data")
        return None


# stepi_report_data 데이터 가공
def stepi_report_data(html):
    data_list = []

    try:
        soup = BeautifulSoup(html, 'html.parser')

        board_list = soup.find('ul', class_='boardList')
        if not board_list:
            logging.error("Board list not found")
            return []

        cbIdx = 1292  # cbIdx 값 예시
        pageIndex = 1  # pageIndex 기본 값
        tgtTypeCd = 'ALL'  # tgtTypeCd 기본 값

        for index, li in enumerate(board_list.find_all('li', recursive=False)):

            url = ''
            dmnfr_trend_no = ''
            ttl = ''
            reg_ymd_text = ''

            title_tag = li.find('div', class_='title')
            info_tag = li.find('div', class_='info')
            if title_tag:
                tit_tag = title_tag.find('a', class_='tit')
                if tit_tag:
                    report_view = tit_tag['href'] if 'href' in tit_tag.attrs else ''

                    if report_view:

                        if "reportView2" in report_view:
                            # 정규 표현식을 사용하여 reIdx와 cateCont 추출
                            match = re.search(r"reportView2\('([^']+)',\s*'([^']+)'\)", report_view)
                            if match:
                                reIdx = match.group(1)
                                dmnfr_trend_no = reIdx
                                cateCont = match.group(2)
                                url = f"https://www.stepi.re.kr/site/stepiko/report/View.do?pageIndex={pageIndex}&cateTypeCd=&tgtTypeCd={tgtTypeCd}&searchType=&reIdx={reIdx}&cateCont={cateCont}&cbIdx={cbIdx}&searchKey="
                        else:
                            # 정규 표현식을 사용하여 reIdx와 cateCont 추출
                            match = re.search(r"reportView\((\d+),\s*'([^']+)'\)", report_view)

                            if match:
                                reIdx = match.group(1)
                                dmnfr_trend_no = reIdx
                                cateCont = match.group(2)
                                url = f"https://www.stepi.re.kr/site/stepiko/report/View.do?pageIndex={pageIndex}&cateTypeCd=&tgtTypeCd={tgtTypeCd}&searchType=&reIdx={reIdx}&cateCont={cateCont}&cbIdx={cbIdx}&searchKey="
                    ttl = tit_tag.get_text(strip=True)

            if info_tag:
                span_tags = info_tag.find_all('span')
                if span_tags and len(span_tags) > 0:
                    reg_ymd_text = span_tags[1].get_text(strip=True)

            data_obj = {
                "DMNFR_TREND_NO": dmnfr_trend_no,
                "STTS_CHG_CD": "success",
                "TTL": ttl,
                "SRC": "농식품수출정보-보고서",
                "REG_YMD": reg_ymd_text,
                "URL": url
            }
            data_list.append(data_obj)

    except Exception as e:
        logging.error(f"Error : {e}")

    return data_list


# stepi_report DB
def stepi_report(date):
    html = stepi_report_request()
    if html:
        data_list = stepi_report_data(html)

        for data in data_list:
            print(data)






def main():
    date = datetime.now().strftime('%Y-%m-%d')

    # kistep_gpsTrendList(date)
    # kistep_board(date)
    # krei_list(date)
    # krei_research(date)
    # kati_export(date)
    # kati_report(date)
    stepi_report(date)

if __name__ == '__main__':
    main()