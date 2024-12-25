import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import re
import cx_Oracle
import warnings
from urllib3.exceptions import InsecureRequestWarning
import time
import random
import os


# 경고 숨기기
warnings.simplefilter('ignore', InsecureRequestWarning)


def common_request(url, headers, payload, timeout=30):
    try:
        # GET 요청
        if payload:
            response = requests.get(url, headers=headers, verify=False, params=payload, timeout=timeout)
        else:
            response = requests.get(url, headers=headers, verify=False, timeout=timeout)

        # 응답 인코딩을 UTF-8로 강제 설정
        response.encoding = 'utf-8'

        response.raise_for_status()

        # 상태 코드 200이 아닌 경우 처리
        if response.status_code == 200:
            return response.text
        else:
            # HTTP 오류가 있을 경우 예외 발생
            logging.error(f"Unexpected status code: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        logging.error("Request timed out")
        return None
    except requests.exceptions.TooManyRedirects:
        logging.error("Too many redirects")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None


# DB 연결 함수 (매번 호출 시마다 연결을 설정)
def connect_to_db():
    # 환경 변수로 DB 연결 정보 읽기
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    dbname = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')

    # 연결 문자열 생성
    dsn_tns = cx_Oracle.makedsn(host, port, service_name=dbname)

    try:
        # DB 연결
        conn = cx_Oracle.connect(user=username, password=password, dsn=dsn_tns)
        logging.info("DB 연결 성공")
        return conn
    except cx_Oracle.DatabaseError as e:
        logging.error(f"DB 연결 실패: {e}")
        return None


# DB 연결 종료 함수
def close_db_connection(conn):
    if conn:
        conn.close()
        logging.info("DB 연결 종료")


# DB에 데이터 삽입하는 함수 1row
def insert_data_to_db(data):
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()

        # 데이터 삽입 쿼리
        insert_query = f"""
        INSERT INTO DMNFR_TREND (DMNFR_TREND_NO, STTS_CHG_CD, TTL, SRC, REG_YMD, URL)
        VALUES (:DMNFR_TREND_NO, :STTS_CHG_CD, :TTL, :SRC, :REG_YMD, :URL)
        """

        try:
            # 쿼리 실행
            cursor.execute(insert_query, data)

            # 커밋
            conn.commit()

        except cx_Oracle.DatabaseError as e:
            logging.error(f"데이터 삽입 실패: {e}")
        finally:
            # 커서 종료
            cursor.close()
    else:
        logging.error("DB 연결 실패")


# 데이터 삽입 함수 (INSERT ALL 사용)
def insert_all_data_to_db(conn, cursor, data_list):
    # INSERT ALL 쿼리 준비
    insert_query = "INSERT ALL "

    # 데이터와 그에 대응하는 파라미터 이름 설정
    bind_params = {}
    for idx, data in enumerate(data_list):
        insert_query += f"""
        INTO DMNFR_TREND (DMNFR_TREND_NO, STTS_CHG_CD, TTL, SRC, REG_YMD, URL)
        VALUES (:DMNFR_TREND_NO_{idx}, :STTS_CHG_CD_{idx}, :TTL_{idx}, :SRC_{idx}, :REG_YMD_{idx}, :URL_{idx})
        """

        # 데이터 파라미터 매핑
        bind_params[f"DMNFR_TREND_NO_{idx}"] = data['DMNFR_TREND_NO']
        bind_params[f"STTS_CHG_CD_{idx}"] = data['STTS_CHG_CD']
        bind_params[f"TTL_{idx}"] = data['TTL']
        bind_params[f"SRC_{idx}"] = data['SRC']
        bind_params[f"REG_YMD_{idx}"] = data['REG_YMD']
        bind_params[f"URL_{idx}"] = data['URL']

    # 구문 종료 역할
    insert_query += "SELECT * FROM dual"

    try:
        # 쿼리 실행
        cursor.execute(insert_query, bind_params)

        # 커밋
        conn.commit()
        logging.info(f"{len(data_list)}개의 데이터 삽입 완료")

    except cx_Oracle.DatabaseError as e:
        logging.error(f"데이터 삽입 실패: {e}")


# 날짜 계산 (오늘과 어제 날짜)
def get_date_range():
    # 오늘 날짜와 어제 날짜 계산
    today = datetime.today()
    yesterday = today - timedelta(days=1)

    # 날짜를 yyyymmdd 형식으로 반환
    today_str = today.strftime('%Y%m%d')
    yesterday_str = yesterday.strftime('%Y%m%d')

    return today_str, yesterday_str


# 데이터 조회 함수 (SELECT) - 내부에서 날짜 계산
def select_existing_data(cursor, src):
    # 오늘 날짜와 어제 날짜 구하기
    reg_ymd_today, reg_ymd_yesterday = get_date_range()

    # DB 조회 쿼리 (src와 reg_ymd를 조건으로 추가)
    select_query = """
    SELECT DMNFR_TREND_NO, STTS_CHG_CD, TTL, SRC, REG_YMD, URL
    FROM DMNFR_TREND
    WHERE SRC = :src
    AND REG_YMD IN (:reg_ymd_today, :reg_ymd_yesterday)
    """

    cursor.execute(select_query, {
        'src': src,
        'reg_ymd_today': reg_ymd_today,
        'reg_ymd_yesterday': reg_ymd_yesterday
    })

    existing_data = cursor.fetchall()  # 기존 데이터 조회
    return existing_data


# kistep_gpsTrendList 요청
def kistep_gpsTrendList_request():
    url = "https://www.kistep.re.kr/gpsTrendList.es"

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

    return common_request(url, headers, payload)


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
def kistep_gpsTrendList():
    html = kistep_gpsTrendList_request()
    if html:
        data_list = kistep_gpsTrendList_data(html)
        for data in data_list:
            print(f'\n{data}')

            # 데이터 삽입 함수 호출
            # insert_data_to_db(data)







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

        dmnfr_trend_no = ''
        ttl = ''
        reg_ymd_text = ''
        url = ''

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

                # 정규 표현식으로 biblioId 값 추출
                match = re.search(r'biblioId=(\d+)', url)

                # 값이 매칭되면 출력
                if match:
                    biblio_id = match.group(1)
                    dmnfr_trend_no = biblio_id  # 출력: 542169

            # '등록일', 맨뒤.(점) 제거하고 앞뒤 공백 제거
            reg_ymd_text = tds[2].get_text(strip=True).replace("등록일", "").replace(".", "")

            # 데이터 객체 구성
            data_obj = {
                "DMNFR_TREND_NO": dmnfr_trend_no,
                "STTS_CHG_CD": "succ",
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
            print(f'\n{data}')
            # 데이터 삽입 함수 호출
            insert_data_to_db(data)



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
                        date_str = span_tags[0].get_text(strip=True).replace("등록일", "").strip()
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        reg_ymd_text = date_obj.strftime("%Y%m%d")

                data_obj = {
                    "DMNFR_TREND_NO": dmnfr_trend_no,
                    "STTS_CHG_CD": "succ",
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
            print(f'\n{data}')
            # 데이터 삽입 함수 호출
            insert_data_to_db(data)



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
                date_str = span_tag.get_text(strip=True).replace("등록일", "").strip()
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                reg_ymd_text = date_obj.strftime("%Y%m%d")


            data_obj = {
                "DMNFR_TREND_NO": dmnfr_trend_no,
                "STTS_CHG_CD": "succ",
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
            print(f'\n{data}')
            # 데이터 삽입 함수 호출
            insert_data_to_db(data)



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

        cbIdx = 1292
        pageIndex = 1
        tgtTypeCd = 'ALL'

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
                if span_tags and len(span_tags) > 1:
                    reg_ymd_text = span_tags[1].get_text(strip=True)

                    if reg_ymd_text:
                        # 문자열을 datetime 객체로 변환
                        date_obj = datetime.strptime(reg_ymd_text, '%Y-%m-%d')

                        # 원하는 형식 (yyyymmdd)으로 변환
                        reg_ymd_text = date_obj.strftime('%Y%m%d')


            data_obj = {
                "DMNFR_TREND_NO": dmnfr_trend_no,
                "STTS_CHG_CD": "succ",
                "TTL": ttl,
                "SRC": "과학기술정책연구원	STEPI",
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
            print(f'\n{data}')

            # 데이터 삽입 함수 호출
            insert_data_to_db(data)





# 국외	미국 USDA	보도자료	USDA 보도자료	https://www.usda.gov/media/press-releases
# usda_press_request 요청
def usda_press_request(page):
    url = f"https://www.usda.gov/about-usda/news/press-releases?page={page}"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": f"https://www.usda.gov/about-usda/news/press-releases?page={page}",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    return common_request(url, headers)


# Release No를 위한 요청
def usda_press_no_request(url):

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://www.usda.gov/about-usda/news/press-releases",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    return common_request(url, headers)


# usda_press_data 데이터 가공
def usda_press_data(html):
    data_list = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        board_list = soup.find('div', class_='views-element-container') if soup else None

        if not board_list:
            logging.error("Board list not found")
            return []

        views = board_list.find_all('div', class_='views-row')

        if views and len(views) > 0:

            for index, view in enumerate(views):

                url = ''
                dmnfr_trend_no = ''
                ttl = ''
                reg_ymd_text = ''

                h2_tag = view.find('h2')
                a_tag = h2_tag.find('a') if h2_tag else None

                if a_tag:
                    ttl = a_tag.get_text(strip=True)

                    href_text = a_tag['href'] if 'href' in a_tag.attrs else ''

                    if href_text:
                        url = f'https://www.usda.gov{href_text}'
                        html = usda_press_no_request(url)
                        if html:
                            press_no_soup = BeautifulSoup(html, 'html.parser') if soup else None
                            article_release_no_value = press_no_soup.find('div', class_='article-release-no-value') if press_no_soup else None
                            field_item = article_release_no_value.find('div', class_='field__item') if article_release_no_value else None
                            field_item_text = field_item.get_text(strip=True) if field_item else ''
                            # 숫자에서 소수점(.)을 제거하고, 문자열을 정수로 변환
                            dmnfr_trend_no = int(field_item_text.replace('.', '')) if field_item_text else 0


                # 'time' 태그에서 datetime 속성 가져오기
                time_tag = view.find('time')

                # datetime 속성에서 날짜만 추출하고, YYYYMMDD 형식으로 변환
                if time_tag:
                    date_str = time_tag['datetime'][:10]  # '2024-12-23T16:55:00Z'에서 '2024-12-23'만 추출
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')  # 문자열을 datetime 객체로 변환
                    formatted_date = date_obj.strftime('%Y%m%d')  # YYYYMMDD 형식으로 변환
                    reg_ymd_text = formatted_date

                data_obj = {
                    "DMNFR_TREND_NO": dmnfr_trend_no,
                    "STTS_CHG_CD": "succ",
                    "TTL": ttl,
                    "SRC": "미국 USDA 보도자료",
                    "REG_YMD": reg_ymd_text,
                    "URL": url
                }
                data_list.append(data_obj)
                time.sleep(random.uniform(2, 3))

    except Exception as e:
        logging.error(f"Error : {e}")

    return data_list


# usda_press DB
def usda_press():
    html = usda_press_request('0')
    if html:
        data_list = usda_press_data(html)

        for data in data_list:
            print(f'\n{data}')

            # 데이터 삽입 함수 호출
            insert_data_to_db(data)


# 국외	일본 농림수산성	보도자료	일본 농림수산성 보도자료	https://www.maff.go.jp/j/press/index.html
# https://www.maff.go.jp/j/press/index.html # 현재 월은 이렇게 구하고
# https://www.maff.go.jp/j/press/arc/2410.html # 이전 월은 이렇게 구함


# usda_press_request 요청
def maff_press_request():
    url = f"https://www.maff.go.jp/j/press/index.html"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://www.maff.go.jp/j/press/index.html",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    return common_request(url, headers)


# usda_press_data 데이터 가공
def maff_press_data(html):
    data_list = []
    try:
        soup = BeautifulSoup(html, 'html.parser')

        board_list = soup.find('div', id='main_content')
        if not board_list:
            logging.error("Board list not found")
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
                current_year = datetime.now().year
                formatted_date = ''

                # 고유 dmnfr_trend_no 세팅을 위함
                # 오늘 날짜를 YYMMDDHHMM 형식으로 가져오기
                now = datetime.now()
                today_str = now.strftime('%y%m%d%H%M')  # 'YYMMDDHHMM' 형식으로

                # 2일치만 가져오기 위함
                p_cnt = 0
                dl_cnt = 0

                # 결과 출력 (필터링된 자식들)
                for child in filtered_children:

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
                        reg_ymd_text = formatted_date

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
                            "SRC": "일본 농림수산성 보도자료",
                            "REG_YMD": reg_ymd_text,
                            "URL": url
                        }
                        data_list.append(data_obj)


    except Exception as e:
        logging.error(f"Error : {e}")

    return data_list


# usda_press DB
def maff_press():
    html = maff_press_request()
    if html:
        data_list = maff_press_data(html)

        for data in data_list:
            print(f'\n{data}')

            # 데이터 삽입 함수 호출
            insert_data_to_db(data)



# 국외	중국 농업농촌부	소식	중국 농업농촌부 소식	http://www.moa.gov.cn/xw/zwdt/
def moa_press_request():
    url = f"http://www.moa.gov.cn/xw/zwdt/"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "connection": "keep-alive",
        "host": "www.moa.gov.cn",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    return common_request(url, headers)


# moa_press_data 데이터 가공
def moa_press_data(html):
    data_list = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        board_list = soup.find('div', class_='pub-media1-txt-list') if soup else None

        if not board_list:
            logging.error("Board list not found")
            return []

        list_items = board_list.find_all('li', class_='ztlb')

        if list_items and len(list_items) > 0:
            # list_items를 10개 이하로 자르기
            list_items = list_items[:10]

            for index, item in enumerate(list_items):

                url = ''
                ttl = ''
                reg_ymd_text = ''
                dmnfr_trend_no = ''

                # 날짜
                span_tag = item.find('span')
                if span_tag:
                    date_str = span_tag.get_text(strip=True) if span_tag else ''

                    # 문자열을 datetime 객체로 변환
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')

                    # 원하는 형식 (yyyymmdd)으로 변환
                    formatted_date = date_obj.strftime('%Y%m%d')
                    reg_ymd_text = formatted_date

                a_tag = item.find('a')
                if a_tag:
                    title_value = a_tag['title'] if 'title' in a_tag.attrs else ''
                    ttl = title_value

                    url = a_tag['href'] if 'href' in a_tag.attrs else ''

                    if url:
                        if url.startswith('./'):
                            url = "http://www.moa.gov.cn/xw/zwdt" + url[1:]  # "./"를 제거하고 기본 URL을 붙임

                        # 정규 표현식을 사용하여 URL에서 숫자 추출
                        match = re.search(r'(\d+)(?=\.htm$)', url)
                        if match:
                            dmnfr_trend_no = match.group(1)  # 6468463 추출

                data_obj = {
                    "DMNFR_TREND_NO": dmnfr_trend_no,
                    "STTS_CHG_CD": "succ",
                    "TTL": ttl,
                    "SRC": "중국 농업농촌부 소식",
                    "REG_YMD": reg_ymd_text,
                    "URL": url
                }
                data_list.append(data_obj)

    except Exception as e:
        logging.error(f"Error : {e}")

    return data_list


# usda_press DB
def moa_press():
    html = moa_press_request()
    if html:
        data_list = moa_press_data(html)

        for data in data_list:
            print(f'\n{data}')

            # 데이터 삽입 함수 호출
            # insert_data_to_db(data)




def main():

    kistep_gpsTrendList()
    # kistep_board()
    # krei_list()
    # krei_research()
    # kati_export()
    # kati_report()
    # stepi_report()
    # usda_press()
    # maff_press()
    # moa_press()

if __name__ == '__main__':
    main()