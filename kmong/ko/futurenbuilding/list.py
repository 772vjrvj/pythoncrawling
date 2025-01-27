import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

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

def get_onclick_links():
    start_url = "http://mrnbd.co.kr/D01/"

    headers = setup_headers()

    # 페이지 1부터 169까지 순회하여 링크 추출
    all_links = []  # 결과를 담을 배열

    for page in range(1, 170):
        url = f"http://mrnbd.co.kr/D01/bd_info_list.asp?page={page}&orderbyCnt=50"
        response = requests.get(url, headers=headers)
        time.sleep(0.5)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            try:
                # 'input.N_list_title_space_title' CSS 선택자를 이용해 클릭 가능한 링크 찾기
                inputs = soup.select("input.N_list_title_space_title")
                for idx, inp in enumerate(inputs):  # enumerate를 사용하여 인덱스와 함께 반복
                    onclick_value = inp.get('onclick')
                    if onclick_value:
                        seq = onclick_value.split("'")[1]
                        detail_url = f"http://mrnbd.co.kr/D01/bd_info_view.asp?SEQ={seq}"
                        print(f'detail_url {idx}: {detail_url}')
                        all_links.append(detail_url)
            except Exception as e:
                print(f"Error on page {page}: {e}")

    return all_links

def save_links_to_excel(links, file_name="urls.xlsx"):
    """링크 리스트를 엑셀 파일로 저장하는 함수"""
    df = pd.DataFrame(links, columns=["URLs"])  # URL들을 "URLs" 컬럼에 저장
    df.to_excel(file_name, index=False)  # 엑셀 파일로 저장

def main():

    # 링크 추출 함수 호출
    links = get_onclick_links()

    # 추출된 링크들을 엑셀로 저장
    save_links_to_excel(links)

if __name__ == "__main__":
    main()
