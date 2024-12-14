import requests
from bs4 import BeautifulSoup
from requests.exceptions import Timeout, RequestException
import pandas as pd
from tqdm import tqdm


def setup_headers():
    """헤더 정보를 설정하는 함수"""
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "ASPSESSIONIDSAQDRDCQ=EJLBIGGCGANANDDJHNGKGPIM; Nsys=photofile=Photo%5FC01%5F2023217105648630%2Ejpg&ceo%5Fmobile=010%2D0000%2D0000&Ttel=%2D%2D&Auth=5&user%5Femail=kkdh9930%40naver%2Ecom&code%5Fid=&grd=%B0%FA%C0%E5&team%5Fid=mrnbd&company%5Fceo=&company%5Faddr=%BC%AD%BF%EF&company%5Femail=&company%5Fhomepage=&company%5Fj%5Fnumber=000&company%5Ffax=02%2D517%2D3300&company%5Ftel=02%2D543%2D5500&company%5Fname=%B9%CC%B7%A1%BE%D8%BA%F4%B5%F9&company%5Fid=D01&company%5FUID=U%5F202230510001&htel=010%2D6670%2D9930&user%5Fid=kimdaeho%5F202212&user%5Fname=%B1%E8%B4%EB%C8%A3&user%5FUID=N2022122188827",
        "Host": "mrnbd.co.kr",
        "Referer": "http://mrnbd.co.kr/D01/bd_info_list.asp?page=1&keyword=&keyword2=&price1=&price2=&area1=&area2=&barea1=&barea2=&su_rate1=&su_rate2=&ing_1=&ing_2=&ing_3=&ing_4=&ing_5=&ing_6=&ing_7=&ing_8=&grp=&team_member=&orderby=&st=1&ing_kind=&andor=&orderbyCnt=50",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    return headers

def send_get_request(url, headers, retries=3, timeout=10):
    """GET 요청을 보내고 HTML 응답을 반환하는 함수"""
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response.content
            else:
                print(f"Failed to retrieve the page. Status code: {response.status_code}")
                return None
        except Timeout:
            # 연결 시간이 초과되었을 경우 처리
            attempt += 1
            print(f"Timeout occurred. Retrying... ({attempt}/{retries})")
        except RequestException as e:
            # 그 외 네트워크 관련 오류 처리
            print(f"Request error occurred: {e}")
            break
    print("Max retries exceeded. Could not fetch the page.")
    return None

def parse_html(html_content):
    """HTML을 BeautifulSoup으로 파싱하는 함수"""
    return BeautifulSoup(html_content, 'html.parser')

def extract_content(soup):
    """HTML에서 checked인 input 태그의 다음 td 텍스트를 추출하는 함수"""

    obj = {
        'CARD': '',
        '진행': '',
        '기본': '',
        '주소': '',
        '상세주소': '',
        '입금가': '',
        '매매가': '',
        '보증금': '',
        '월 임대로': '',
        '관리비': '',
        '고객': '',
        '핸드폰': '',
        '이메일': '',
        '회사전화': '',
        '자택전화': '',
        '기타전화': '',
        '매각완료일': '',
        '참고': '',
    }

    # 'frm_bd_info_view' 이름을 가진 form 태그 찾기
    form_tag = soup.find('form', {'name': 'frm_bd_info_view'})

    if form_tag:
        first_table = form_tag.find('table', recursive=False)
        if first_table:
            if first_table.find('tr') and first_table.find('tr').find('td') and first_table.find('tr').find('td').find_all('table', recursive=False):
                first_all_tables =first_table.find('tr').find('td').find_all('table', recursive=False)
                if(len(first_all_tables) > 5):
                    forth_table = first_table.find('tr').find('td').find_all('table', recursive=False)[4]

                    if forth_table.find('tr') and len(forth_table.find('tr').find_all('td', recursive=False)) > 1:
                        card = forth_table.find('tr').find_all('td', recursive=False)[1]
                        obj['CARD'] = card.get_text(strip=True)

                    sixth_table = first_table.find('tr').find('td').find_all('table', recursive=False)[5]
                    if sixth_table and sixth_table.find('tr') and sixth_table.find('tr').find_all('td', recursive=False):

                        # 좌측 테이블들
                        fist_tds = sixth_table.find('tr').find_all('td', recursive=False)[0]
                        if fist_tds and fist_tds.find_all('table', recursive=False):
                            fist_tds_tables = fist_tds.find_all('table', recursive=False)

                            # 진행
                            if fist_tds_tables[0] and fist_tds_tables[0].find('tr'):
                                fist_tds_tr = fist_tds_tables[0].find('tr')
                                if fist_tds_tr.find_all('td', recursive=False) and fist_tds_tr.find_all('td', recursive=False)[1]:
                                    tds_all_table_tr_td_first = fist_tds_tr.find_all('td', recursive=False)[1]
                                    if tds_all_table_tr_td_first and tds_all_table_tr_td_first.find('table') and tds_all_table_tr_td_first.find('table').find('tr'):
                                        tds_all_table_tr_td_first_tr = tds_all_table_tr_td_first.find('table').find('tr')

                                        inputs = tds_all_table_tr_td_first_tr.find_all('input', {'checked': True})
                                        for inp in inputs:
                                            # checked된 input 태그의 부모 td의 다음 td의 텍스트 추출
                                            next_td = inp.find_parent('td').find_next_sibling('td')
                                            if next_td:
                                                obj['진행'] = next_td.get_text(strip=True)
                                                print(obj['진행'])



                            # 기본, 주소, 상세주소)
                            if fist_tds_tables[2] and fist_tds_tables[2].find_all('tr', recursive=False):
                                fist_tds_tables_trs = fist_tds_tables[2].find_all('tr', recursive=False)
                                obj['기본'] = adress_info(fist_tds_tables_trs, 0, 'N')
                                obj['주소'] = adress_info(fist_tds_tables_trs, 1, 'N')
                                obj['상세주소'] = adress_info(fist_tds_tables_trs, 2, 'Y')

                            # 입금가, 매매가
                            obj['입금가'] = get_price_ipgum(fist_tds_tables, 4)
                            obj['매매가'] = get_price_ipgum(fist_tds_tables, 6)

                            # 보증금, 월 임대료, 관리비
                            if fist_tds_tables[8] and fist_tds_tables[8].find_all('tr', recursive=False):
                                fist_tds_tables_trs = fist_tds_tables[8].find_all('tr', recursive=False)

                                obj['보증금'] = controll_price(fist_tds_tables_trs, 0)
                                obj['월 임대로'] = controll_price(fist_tds_tables_trs, 1)
                                obj['관리비'] = controll_price(fist_tds_tables_trs, 2)

                        # 우측 테이블
                        last_tds = sixth_table.find('tr').find_all('td', recursive=False)[2]
                        if last_tds and last_tds.find_all('table', recursive=False):
                            last_tds_tables = last_tds.find_all('table', recursive=False)

                            # 고객정보
                            if last_tds_tables[2] and last_tds_tables[2].find('tr'):
                                last_tds_tr = last_tds_tables[2].find('tr')
                                if last_tds_tr.find('td') and last_tds_tr.find('td').find('div'):
                                    last_div = last_tds_tr.find('td').find('div')
                                    if last_div and last_div.find('table') and len(last_div.find('table').find_all('tr', recursive=False)) > 7:
                                        last_trs = last_div.find('table').find_all('tr', recursive=False)

                                        obj['고객'] = cust_info(last_trs, 0) # 고객
                                        obj['핸드폰'] = cust_info(last_trs, 1) # 핸드폰
                                        obj['이메일'] = cust_info(last_trs, 2) # 이메일
                                        obj['회사전화'] = cust_info(last_trs, 3)
                                        obj['자택전화'] = cust_info(last_trs, 4)
                                        obj['기타전화'] = cust_info(last_trs, 5)
                                        obj['매각완료일'] = cust_info(last_trs, 6)
                                        obj['참고'] = cust_info(last_trs,7)

    return obj

def get_price_ipgum(fist_tds_tables, index):
    if fist_tds_tables[index] and fist_tds_tables[index].find('tr'):
        fist_tds_tr = fist_tds_tables[index].find('tr')
        if fist_tds_tr.find_all('td', recursive=False) and fist_tds_tr.find_all('td', recursive=False)[1]:
            tds_all_table_tr_td_first = fist_tds_tr.find_all('td', recursive=False)[1]
            if tds_all_table_tr_td_first and tds_all_table_tr_td_first.find('table') and tds_all_table_tr_td_first.find('table').find('tr'):
                tds_all_table_tr_td_first_tr = tds_all_table_tr_td_first.find('table').find('tr')
                inputs = tds_all_table_tr_td_first_tr.find_all('td', recursive=False)
                if len(inputs)>1:
                    if inputs[0] and inputs[0].find('input') and inputs[1]:
                        price_ipgum = inputs[0].find('input').get('value') + inputs[1].get_text(strip=True)
                        return price_ipgum
    return ''

def controll_price(fist_tds_tables_trs, index):
    if fist_tds_tables_trs[index] and fist_tds_tables_trs[index].find_all('td', recursive=False) and len(fist_tds_tables_trs[index].find_all('td', recursive=False)) > 1:
        basic = fist_tds_tables_trs[index].find_all('td', recursive=False)
        if basic[1].find('table') and basic[1].find('table').find('tr'):
            inputs = basic[1].find('table').find('tr').find_all('td', recursive=False)

            if len(inputs)>1:
                if inputs[0] and inputs[0].find('input') and inputs[1]:
                    price_ipgum = inputs[0].find('input').get('value') + inputs[1].get_text(strip=True)
                    return price_ipgum
    return ''

def adress_info(fist_tds_tables_trs, index, detail):
    if fist_tds_tables_trs[index] and fist_tds_tables_trs[index].find_all('td', recursive=False) and len(fist_tds_tables_trs[index].find_all('td', recursive=False)) > 1:
        basic = fist_tds_tables_trs[index].find_all('td', recursive=False)
        if basic[1].find('table') and basic[1].find('table').find('tr'):
            if detail == 'Y':
                basic_td = basic[1].find('table').find('tr').find_all('td', recursive=False)
                if len(basic_td) > 1 and basic_td[1].find('input'):
                    return basic_td[1].find('input').get('value')
            else:
                basic_td = basic[1].find('table').find('tr').find('td')
                if basic_td and basic_td.find('input'):
                    return basic_td.find('input').get('value')
    return ''

def cust_info(last_trs, index):
    if len(last_trs[index].find_all('td', recursive=False))>1:
        cust_td = last_trs[index].find_all('td', recursive=False)[1]
        if cust_td and cust_td.find('input'):
            return cust_td.find('input').get('value')
    return ''

def extract_card(soup):

    process_list = []

    if soup and soup.find('body') and soup.find('body').find_all('table', recursive=False):
        tables = soup.find('body').find_all('table', recursive=False)

        if len(tables) > 0:
            for index, table in enumerate(tables):
                if table.find('tr') and len(table.find('tr').find_all('td')) > 0:
                    tds = table.find('tr').find_all('td')

                    time = tds[0].get_text(strip=True)
                    name = tds[1].get_text(strip=True)
                    cont = tds[2].get_text(strip=True)

                    obj = {
                        '진행 시간': time,
                        '진행자 이름': name,
                        '진행 내용': cont,
                    }
                    process_list.append(obj)

    print(f'process_list : {process_list}')
    return process_list


def merge_obj_with_process_list(obj, process_list):
    """obj와 process_list의 항목을 합쳐서 새로운 리스트 반환"""
    merged_list = []

    # process_list의 항목 개수만큼 반복
    for process in process_list:
        merged_item = obj.copy()  # obj 복사
        merged_item.update(process)  # process의 내용으로 업데이트
        merged_list.append(merged_item)

    return merged_list

def load_urls_from_excel(excel_file):
    """엑셀 파일에서 URL 리스트를 읽어오는 함수"""
    df = pd.read_excel(excel_file)
    return df['URL'].tolist()  # 엑셀 파일에 'URL'이라는 컬럼이 있어야 합니다.

def save_results_to_excel(results, output_file):
    """결과를 엑셀 파일로 저장하는 함수"""
    df = pd.DataFrame(results)
    df.to_excel(output_file, index=False)

def main():

    results = []

    # 엑셀 파일에서 URL 읽어오기
    # urls = load_urls_from_excel('url.xlsx')
    urls = ['http://mrnbd.co.kr/D01/bd_info_view.asp?SEQ=35103']


    for index, url in tqdm(urls):
        print(f'index : {index}')
        headers = setup_headers()  # 헤더 설정

        # GET 요청 보내기
        html_content = send_get_request(url, headers)
        if html_content:
            # HTML 파싱
            soup = parse_html(html_content)
            # 원하는 데이터 추출
            obj = extract_content(soup)
            obj['URL'] = url
            print(f'obj: {obj}')

            card_url = f'http://mrnbd.co.kr/D01/bd_info_view_history.asp?bd_UID={obj["CARD"]}'
            card_content = send_get_request(card_url, headers)

            if card_content:
                # HTML 파싱
                soup = parse_html(card_content)
                historys = extract_card(soup)

                merge_obj_list = merge_obj_with_process_list(obj, historys)

                results.extend(merge_obj_list)

    # 결과를 엑셀 파일로 저장
    save_results_to_excel(results, 'results.xlsx')

if __name__ == "__main__":
    main()