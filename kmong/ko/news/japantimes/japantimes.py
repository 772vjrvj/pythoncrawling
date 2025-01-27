import requests
from bs4 import BeautifulSoup
import logging
import time
import random
import re
from datetime import datetime
import pandas as pd


def japantimes_url_request(keyword, page):
    url = f"https://www.japantimes.co.jp/search?query={keyword}&section=all&qsort=newest&pgno={page}"

    headers = {
        "authority": "www.japantimes.co.jp",
        "method": "GET",
        "path": f"/search?query={keyword}&section=all&qsort=newest&pgno={page}",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cookie": "device=web; _gcl_au=1.1.1385575139.1734580044; _fbp=fb.2.1734580043949.905598485277066431; _pctx=%7Bu%7DN4IgrgzgpgThIC4B2YA2qA05owMoBcBDfSREQpAeyRCwgEt8oBJAEzIEYOBmANm4AsATgDsYgBwch43uIEcBIAL5A; _pcid=%7B%22browserId%22%3A%22m4us67sfqeg0h3sn%22%7D; _clck=matcmz%7C2%7Cfru%7C0%7C1814; _yjsu_yjad=1734580044.a9b2995a-3a2c-4618-aaee-c4e40475dabc; __pid=.japantimes.co.jp; __pnahc=0; __pat=32400000; cX_P=m4us67sfqeg0h3sn; __pb_unicorn_aud=%7B%22uid%22%3A%226ec69ef6-9f36-4518-ad89-0c6ec844e021%22%7D; dicbo_id=%7B%22dicbo_fetch%22%3A1734580045459%7D; cX_G=cx%3A3jj6tgz6itqnr3e0eekhl47ogj%3A1l99i2l087epq; _cb=CJm5bbDdPD6_Byey55; _cb_svref=https%3A%2F%2Fwww.google.com%2F; __gads=ID=4ea9effef9f9a2ef:T=1734580047:RT=1734580047:S=ALNI_Ma6H23MiA4JFEWk5dwe6upuk4gzgw; __gpi=UID=00000faca706f9a0:T=1734580047:RT=1734580047:S=ALNI_MbTcF7exfUIJ1mzWsq7p7h9cAKjZw; __eoi=ID=ab8c625246fc2648:T=1734580047:RT=1734580047:S=AA-AfjZBdzvnXgT1vT8SDsNdaC0D; _gid=GA1.3.1588069796.1734580053; _pcus=eyJ1c2VyU2VnbWVudHMiOnsiQ09NUE9TRVIxWCI6eyJzZWdtZW50cyI6WyJMVHM6Mjg2MjI4NzI5YTNmYzBhMDNiNTYxNmZiNjVkMWY2NzkxNWU5YTQzMjo2Il19fX0%3D; AWSALB=ihpalbOHjVeVvX9/Ih1q/O+rNzbiqi4NK3t5zhtICS2IEvD8DAuILOOqt2grtPY0xyUVJNFyP4Z+Uv/49wvq2IBL1xau01ErYzJCSEXmHnWUXkUbigq98rPexN5z; AWSALBCORS=ihpalbOHjVeVvX9/Ih1q/O+rNzbiqi4NK3t5zhtICS2IEvD8DAuILOOqt2grtPY0xyUVJNFyP4Z+Uv/49wvq2IBL1xau01ErYzJCSEXmHnWUXkUbigq98rPexN5z; __pvi=eyJpZCI6InYtbTR1czd0cWgzN3BtNTlvZiIsImRvbWFpbiI6Ii5qYXBhbnRpbWVzLmNvLmpwIiwidGltZSI6MTczNDU4MDExOTExM30%3D; __adblocker=false; __tbc=%7Bkpex%7DM0IHtP0L10IraaUL14ZA2Kp_gnrsxK934Z_lzf2SH86eubY2OdWH2CjlHrUbunX6; xbc=%7Bkpex%7DbdGTyyXry1YAPiJfv1TsXTsf3DlGFQD5smwT8-96Yw4; _clsk=1v5mqv8%7C1734580120036%7C4%7C1%7Cz.clarity.ms%2Fcollect; FCNEC=%5B%5B%22AKsRol9m7IQK5wFj6i8MePeUnZvtCuBlavcb4yVJI6yGHSeP7qXaW9IIYdCfGsDd1rbilAfVAtuGUDuiPsPjHgunTfvmcdRmmupgJ63T_LLQzFVlDdKvglA60bVMbyRTbakzkEuR4HWqgYIfomUVjoI5RYjv20U7wQ%3D%3D%22%5D%5D; _ga=GA1.3.618191953.1734580043; _gat_pianoTracker=1; _chartbeat2=.1734580047053.1734580127033.1.192lTCK0yxUinVuEr1RjsBn9Yxi.4; _gat_UA-37091063-1=1; cto_bundle=PpW5XV9tbmtwS1F5bFAlMkJydEQlMkJLaVhwQ2pvVUVxWHlBeGp5VTJkcDFSSEZsbDdNVzh2alYyenp0cG5naHIwNjZsemJIb2hDWjk0b3hveFlpM0hwVk1BNlVabTFGVU5BMVRFY0JkRnA1RVVjRUVuc3E1dU14eEplMXR4cm8wTFRKbm1aVnJYYWpXclNaNjYzdXhOUmR0a2V5NzR3JTNEJTNE; cto_bidid=TxlMfF9ZQmhsMG9OWjNMbEtnTTk3SnZVYTRJdDlhZyUyQmp1SDFLY0hWM25MSTE5TW43T2pZQ1U0dUFJYWQ4RnE5JTJCaWpBYlJHYXgzZkdzM3R4YWVnSEgxSzk0YzFrNXJxMWFNR0ZqY0d4TjV0a3lYc0N5RFAlMkZLMHlFRlByRFBuU0pJJTJGd1R2; _ga_PFG2Q35R7H=GS1.1.1734580042.1.1.1734580149.0.0.0; _chartbeat5=271|5239|%2Fsearch|https%3A%2F%2Fwww.japantimes.co.jp%2Fsearch%3Fquery%3DSouth%2520Korea%25E2%2580%2599s%2520President%26section%3Dall%26qsort%3Dnewest%26pgno%3D2|JtiCiB4trRhDT_-NCBiDn0FHcR-u||c|JtiCiB4trRhDT_-NCBiDn0FHcR-u|japantimes.co.jp|; _ga_QNMQPDT7PZ=GS1.3.1734580059.1.0.1734580168.0.0.0; _ga_B5LD4SWLGB=GS1.1.1734580043.1.1.1734580168.1.0.0",
        "priority": "u=0, i",
        "referer": f"https://www.japantimes.co.jp/search?query={keyword}&section=all&qsort=newest",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    headers = {k: v.encode('ascii', 'ignore') for k, v in headers.items()}

    # GET 요청
    try:
        # HTTP GET 요청
        response = requests.get(url, headers=headers)

        # 요청이 성공적인 경우
        response.raise_for_status()  # 상태 코드가 200이 아니면 예외 발생

        return response.text
    except requests.exceptions.RequestException as e:
        print(f"HTTP 요청 중 오류 발생: {e}")
        return None



def get_japantimes_url(html, keyword):
    url_list = []

    try:
        soup = BeautifulSoup(html, 'html.parser')
        board_list = soup.find('div', class_='search-results') if soup else None

        if not board_list:
            logging.error("Board list not found")
            return []

        for index, div in enumerate(board_list.find_all('div', class_="article", recursive=False)):
            obj = {
                'NEWS': 'The Japan Times',
                '키워드': keyword,
                'URL': '',
                'DATE': '',
                'TITLE': '',
                'CONTENT': ''
            }
            article_title = div.find('h2', class_='article-title')
            if article_title:
                a_tag = article_title.find('a', recursive=False)

                news_link_href = a_tag['href'] if 'href' in a_tag.attrs else None
                if news_link_href:
                    obj['URL'] = news_link_href

                    # 정규 표현식 패턴: URL에서 'YYYYMMDD' 형식의 날짜를 추출
                    pattern = r'(\d{4})/(\d{2})/(\d{2})'

                    # 정규 표현식에 맞는 날짜 부분을 찾습니다.
                    match = re.search(pattern, news_link_href)

                    if match:
                        # 날짜를 'YYYYMMDD' 형식으로 추출
                        extracted_date = match.group(1) + match.group(2) + match.group(3)
                        obj['DATE'] = extracted_date

            print(f'obj : {obj}')
            url_list.append(obj)

    except Exception as e:
        logging.error(f"Error during scraping: {e}")

    return url_list


def japantimes_detail_request(url):

    headers = {
        "authority": "www.japantimes.co.jp",
        "method": "GET",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "cookie": "__qca=I0-526893380-1734606588722; _pctx=%7Bu%7DN4IgrgzgpgThIC4B2YA2qA05owMoBcBDfSREQpAeyRCwgEt8oBJAEzIEYOBmANm4AsATgDsYgBwch43uIEcBIAL5A; _pcid=%7B%22browserId%22%3A%22m4spjzh89r1ein6p%22%7D; _gcl_au=1.1.1077662921.1734454715; _yjsu_yjad=1734454715.1a41f259-44cc-46e4-a41d-7bb388f0d3f2; __pid=.japantimes.co.jp; _fbp=fb.2.1734454715785.8520262966231727; __pnahc=0; __pat=32400000; cX_P=m4spjzh89r1ein6p; __pb_unicorn_aud=%7B%22uid%22%3A%22874819fa-fb58-41bd-9430-d44caaf232c2%22%7D; cX_G=cx%3A3dxtmybvsq5b6yibfn2v8lpj%3A3uxglnyofccwq; _cb=i2SkKDy91TuCiDa44; device=web; _clck=yc82vf%7C2%7Cfru%7C0%7C1812; _gid=GA1.3.1890397439.1734606260; __pvi=eyJpZCI6InYtbTR2N3llaDh1bmxuOWp3cSIsImRvbWFpbiI6Ii5qYXBhbnRpbWVzLmNvLmpwIiwidGltZSI6MTczNDYwNjU1MzI5Mn0%3D; __tbc=%7Bkpex%7D51dRD2I2mICk-pHo_Z628Dic-pK5nACnJ9pZetWlMTyeubY2OdWH2CjlHrUbunX6; xbc=%7Bkpex%7DE-a6RStLx1btRRwcbeGlCB9vS8wltx2ofH9WdH_FuNJXqnatDgoF7l6mQndfkMe-HHZibn1wfu2sBKAUkbU38QePbdfKf7LXjczjpzbigMwjCCJiROC2z7e1BxoPuSbqDcjiig2v2Si7WXBuRfHXd0X8uS8zMeEnlzsV_RWDsJi3sf753VvxqMF_pbdZxsjZQpscK0Vgzon7HtSV2_UQB8jR4FBgqjJFmuqrHa_MOfiW11hCNVQrMOZrxFc1XYch; _pcus=eyJ1c2VyU2VnbWVudHMiOnsiQ09NUE9TRVIxWCI6eyJzZWdtZW50cyI6WyI4bzFhc2s3dnpmOHciLCI4b25nem5mOHNpYnYiLCJMVHM6Mjg2MjI4NzI5YTNmYzBhMDNiNTYxNmZiNjVkMWY2NzkxNWU5YTQzMjo5Il19fX0%3D; _clsk=1t6qrt0%7C1734606554543%7C2%7C1%7Cx.clarity.ms%2Fcollect; FCNEC=%5B%5B%22AKsRol-fOAqGOdpt1Yo-KGsME6A61MZKNzthdzfer4n-5b2MVJac4iL2kqp8m6IrM55O6poqhfyboqXZPc4v4ydjDZ-aZDqZ9xuJLEMnqJBd4fcDbFKBCE0acszxKD-liMBDHfOVhyRBQ1iKihT66wbYfDoa42Zwmg%3D%3D%22%5D%5D; _ga=GA1.3.2007489235.1734454715; AWSALB=PcUug7LEh3MhKSOa/+ErJXysEGKeHXt21fw1Qi5ZYxPacBL2kX9ajEg0CQbe3cCgnd8lIu1ZDPIwPwdQ0Z7D0u5+GE7iaOED0mIkh5I4auKEB7LSsP7TOh5WgCoj; AWSALBCORS=PcUug7LEh3MhKSOa/+ErJXysEGKeHXt21fw1Qi5ZYxPacBL2kX9ajEg0CQbe3cCgnd8lIu1ZDPIwPwdQ0Z7D0u5+GE7iaOED0mIkh5I4auKEB7LSsP7TOh5WgCoj; _ga_QNMQPDT7PZ=GS1.3.1734606561.2.0.1734606561.0.0.0; _chartbeat2=.1734454718245.1734606561486.11.DM9mC7AhI9g2HZfCnN1EmBOY3hX.1; _cb_svref=external; cto_bidid=gYdi0l81dDNwWnJwUXZYbUlGdVclMkJHblVmVlZOSW9pJTJGdE02dUNHc3lCNmtIclBCVENvNWdIb25jc1ZydDBUVVVLYlVtbGNSenFXd2ZvREx0NnRUa2dCcnAzNVJseE8xdFdrVzZkNFlyT1phSzJGZE9SazdmUVNFOGVDVFZUS1NXZFJkQ3A; tempest_usersync=1; sharedid=b8aa2791-bf33-4ca0-95d8-c94c5e60391d; sharedid_cst=zix7LPQsHA%3D%3D; _lr_retry_request=true; _lr_env_src_ats=false; _pubcid=ecfacf6f-a9b5-4c2c-9a48-564a7b2ff626; _pubcid_cst=zix7LPQsHA%3D%3D; _li_dcdm_c=.japantimes.co.jp; _lc2_fpi=fdf8509aa187--01jff9qfqk5y39d80cjg2sh6n0; _lc2_fpi_meta=%7B%22w%22%3A1734606569204%7D; cto_bundle=JbnrOV9kWSUyQlhWamVjY1VkU1Nibk9uM3FJVmptNHBvQkhybnFUZXdJS0RuJTJGJTJCV25tcXBzR2lienJUYXhzaEMzMSUyRiUyQmxmJTJCUHdEbjNxUlpFckRLYk9tbGROYlBBYldzcWVIdXR1OU1NOTZIV1E3d2VyZlFranh1SmZsbnZsVXlIVE9VQTN3NFNjdGc0dnlpMVg2YWFMOGRSaDAxVURWSyUyRmFzUEdmV1ZEQkdiRDJac0NWbTZkQ1ZUWXFPUlVJdWh4QXNjWDB5MDRRbzFjWGRKWTBJZ0E4RXNGaTZ1S0ElM0QlM0Q; cto_bundle=JbnrOV9kWSUyQlhWamVjY1VkU1Nibk9uM3FJVmptNHBvQkhybnFUZXdJS0RuJTJGJTJCV25tcXBzR2lienJUYXhzaEMzMSUyRiUyQmxmJTJCUHdEbjNxUlpFckRLYk9tbGROYlBBYldzcWVIdXR1OU1NOTZIV1E3d2VyZlFranh1SmZsbnZsVXlIVE9VQTN3NFNjdGc0dnlpMVg2YWFMOGRSaDAxVURWSyUyRmFzUEdmV1ZEQkdiRDJac0NWbTZkQ1ZUWXFPUlVJdWh4QXNjWDB5MDRRbzFjWGRKWTBJZ0E4RXNGaTZ1S0ElM0QlM0Q; _ga_PFG2Q35R7H=GS1.1.1734606255.2.1.1734606582.0.0.0; _ga_B5LD4SWLGB=GS1.1.1734606255.2.1.1734606582.31.0.0; __gads=ID=87c62e58a8bfcbe6:T=1734454716:RT=1734606587:S=ALNI_MYDzzRxXTwqUhB6PJdbxTbVm8dKTg; __gpi=UID=00000fa94b9c37c0:T=1734454716:RT=1734606587:S=ALNI_MZi3CcMhDtWmnMHD6sio43eGIXMlQ; __eoi=ID=d40bcc752c8a221d:T=1734454716:RT=1734606587:S=AA-AfjYos_gKV4gQo22Lzj6PqlhI",
        "priority": "u=0, i",
        "referer": f"{url}",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    # GET 요청
    try:
        # HTTP GET 요청
        response = requests.get(url, headers=headers)

        # 요청이 성공적인 경우
        response.raise_for_status()  # 상태 코드가 200이 아니면 예외 발생

        return response.text
    except requests.exceptions.RequestException as e:
        print(f"HTTP 요청 중 오류 발생: {e}")
        return None

def japantimes_detail_data(html, data):

    try:
        soup = BeautifulSoup(html, 'html.parser')
        title_article = soup.find('h1', class_='title-article') if soup else None
        data['TITLE'] = title_article.get_text(strip=True) if title_article else ''

        article_body = soup.find('div', class_='article-body') if soup else None
        data['CONTENT'] = article_body.get_text(strip=True) if article_body else ''

    except Exception as e:
        logging.error(f"Error during scraping: {e}")

    return data


def save_to_excel(results):

    # 현재 시간을 'yyyymmddhhmmss' 형식으로 가져오기
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")

    # 파일 이름 설정
    file_name = f"신문_{current_time}.xlsx"

    try:
        # 파일이 없으면 새로 생성
        df = pd.DataFrame(results)

        # 엑셀 파일 저장
        df.to_excel(file_name, index=False)

    except Exception as e:
        # 예기치 않은 오류 처리
        logging.error(f"엑셀 저장 실패: {e}")


def main():

    all_data_list = []

    # keyword = 'South Korea’s President'
    # keyword = 'Yoon Suk Yeol'
    # keyword = 'Martial Law'
    keyword = 'Impeachment'
    main_url = 'https://www.japantimes.co.jp'
    for page in range(1, 3):
        html = japantimes_url_request(keyword, page)
        time.sleep(random.uniform(1, 2))
        if html:
            url_list = get_japantimes_url(html, keyword)
            print(f'page : {page}, data_list {len(url_list)}')

            all_data_list.extend(url_list)

    all_result_list = []
    for idx, data in enumerate(all_data_list, start=1):
        html = japantimes_detail_request(data['URL'])
        time.sleep(random.uniform(1, 2))
        result = japantimes_detail_data(html, data)
        print(f'result : {result}')
        all_result_list.append(result)

    save_to_excel(all_result_list)


if __name__ == '__main__':
    main()