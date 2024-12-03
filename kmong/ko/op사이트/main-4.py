import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 카테고리 별 페이로드 설정
categories = {
    "1": "서울(강남)",
    "2": "서울(비강남)",
    "3": "경기",
    "4": "인천,부천",
    "5": "강원,대전,충청",
    "6": "경상,전라,제주"
}

url = "https://starop03.com"

headers = {
    "authority": "starop03.com",
    "method": "GET",
    "path": "/?cate1=3",
    "scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko,en;q=0.9,en-US;q=0.8",
    "referer": "https://starop03.com/",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
    "sec-ch-ua-arch": "x86",
    "sec-ch-ua-bitness": "64",
    "sec-ch-ua-full-version": "128.0.2739.54",
    "cookie": "mchk=p; dt=20240902; visid_incap_3129864=r8HTlClDT921N/DfFqqkRjqK1GYAAAAAQUIPAAAAAABXY29qpqBd+NRS/LNNfttK; incap_ses_170_3129864=KkZvbuXHYnB0lswuOPZbAjuK1GYAAAAAcSxqgP3ZLLxMEYTs0IwjHw==; _gid=GA1.2.1685249802.1725205053; popup_banner_tf=true; incap_ses_224_3129864=HS6zZefaWi4O6Pfl8M4bA4iK1GYAAAAA7V5oJpi+qDR976O74465kA==; incap_ses_540_3129864=8lZ7cu0y9DUdhuCTRnd+B5+N1GYAAAAAitqFCuz5aGhDKUkhZJ29TA==; incap_ses_1832_3129864=C0AlO4aDUCOnwZWQaZJsGSOP1GYAAAAAKGmfkYJqzeONU8pXGUNTzw==; incap_ses_1828_3129864=f5EdTTeFoEW+rJX4blxeGSSP1GYAAAAAFg8n6Xl2FaOwzc1XRq1hHg==; incap_ses_1827_3129864=6KdLCX7dFADFNo5V8M5aGSWP1GYAAAAAun5ZLUIYNNVst9vaqDk8EA==; user_auth=eXe3vs3Robew2nO9eWw%3D; wuinfo=XFSKmq6nZtuwoZ6BopPEx%2BzYp8K%2BqFmBpH%2BC35jmLgsCYsIaFr%2FcURz2dZN18YOIo0TQl5jooYvLmp3ClYW50dnbr9W%2Bt5O%2FoIbKlNjdsA%3D%3D; incap_ses_553_3129864=6Jjtew944z8s9+2hsqasB3aR1GYAAAAA/9yteJ0FpeSM7wY6wHe48w==; incap_ses_1163_3129864=hWGxVNEqe1PBdDXudM4jEJSR1GYAAAAAr+2tjWC8yg6bAU5jRtZPqw==; incap_ses_881_3129864=65XPYdFviQeELJ138/A5DJOU1GYAAAAAl8oKuzetqEm3RcPrdMCDVw==; incap_ses_883_3129864=ohLvFZo49R5Lg2XA8AtBDJSU1GYAAAAA7BfdfKLVwZI/hO6OwIRf0g==; incap_ses_172_3129864=hphdejnws2HNVwV5NRFjApSU1GYAAAAABAfoook5v7eI9GmYGfJErg==; incap_ses_549_3129864=Uw/TZzSHBxMFpO4VuHCeB5SU1GYAAAAAVJPfS5oQAHIusX8bvS0ZLw==; incap_ses_173_3129864=HoMwYv9k3SPQzW4d155mApSU1GYAAAAAHSgVl43vp6PYRGOfOrZW0w==; incap_ses_171_3129864=Bc/UYcdRkX7R/YIduYNfApSU1GYAAAAAqjBp8C27MisAMwgNirBPQQ==; incap_ses_1359_3129864=xGAZByVgoy0y+tx5XyPcEqqU1GYAAAAAqga9PUJeUg8PJwy7TCJuHA==; incap_ses_538_3129864=j6/dRiqeGTGMfBykS1x3B7WU1GYAAAAAbhVy1VG8FufzNhnlkiQK4g==; incap_ses_1358_3129864=Ttqab7aC8FLMIuDX4JXYEvOU1GYAAAAAMkpKIymZv0trvGIV3+4TQw==; incap_ses_1287_3129864=7nGIHeYktU0bhELNzFfcEbOY1GYAAAAAQEIlPT0USwcQsy6EZywt0Q==; incap_ses_884_3129864=mPK5ZktCByZ6c9Jeb5lEDLyY1GYAAAAAFtRFQq2+d2YRlYPJCM2bvg==; incap_ses_880_3129864=C4QkCXok4j3FiBTUdGM2DL+Y1GYAAAAAcJvCjSPFLIQAGh/7yrD2LQ==; incap_ses_1447_3129864=fvM3bWhQyEplZ07B88YUFNGY1GYAAAAACu6613MRZX82nf45vUJo8g==; incap_ses_882_3129864=BdnKd/Imgwl5RZgXcn49DNGY1GYAAAAAVzgy/kdFGaMqcEnnRvwvWg==; incap_ses_1356_3129864=En7db6GKAyLtK1yR43rREkua1GYAAAAAYqh5IjcP7VJgMeyOY6TNtg==; incap_ses_543_3129864=FI05JMYQgyzgOUo3wB+JB0ya1GYAAAAA1fGVk764m6CFjW2fqAwa9w==; incap_ses_551_3129864=f0d2MlvP605OOvqPtYulB0+a1GYAAAAAmF7NyiwHqhireXb4dln4DA==; incap_ses_539_3129864=gNVwLL4oJFAW4U3yx+l6B1Ca1GYAAAAADcFVzF2smSIeOJ3qtqUSSw==; cf_clearance=i3e2h5mhgdIorOrqaBsDT6PlCzZDSdkj5vZO9IgE9MU-1725210603-1.2.1.1-f5QWYW9XfsFwZ0WQnUhjuQBkW2iwCGaAmu6Q18Xfn1P.mT0RIqvRFu29RSJQXyujk21xQ77xTQFN1VLesOeJNj_pegYH_dLqzPaBQkmg31i6EnI.4aUGFzbMOikG9BjQi0ePnKrCoB5s3NpFiqC76OnKFYlppWNQ_dGqvYOl_cJFVv05701zV7fAw1uZH51IQ4iAt6pbO5YjINTobAyEog5pkikAQ6CIQ4.OiHNEIqP8sJlsAVEiyCEmk93aTIftpI3lR_nk3qQ_wz48Pa4l_LbJFAaJJmrr2PPmF1QdJPnBoc7TTMZzmyvbUUllreLGaJEkbI8eATFoSU80t5CEnqNq.hX97sD7yNYSJov9WtUHkkxBMP6lPktICeenBrqXM_mj4rmniHqgDMYI1rWDNTlAtMKHEDALAQpyqu0YC6uoAK9gpXDt4Yi8h61Qkwn.riHIXctbkwV6H4ZmMVg1Vw; incap_ses_1449_3129864=ZtibTJ73TAfStHvQ2eEbFPGf1GYAAAAA7wcyAXim7i2N2FfiNAc4Wg==; incap_ses_1357_3129864=00Z5L3Yn+hJ6R1I5YgjVEvCf1GYAAAAA1mxgiATN+jqv7IGbA5StzQ==; incap_ses_1249_3129864=I1AVc9Ft5AmWhfJSAFdVEfCf1GYAAAAA0CjVgZoFrZJzPSjDhlcv+g==; incap_ses_1355_3129864=vOJyfsizkwC8z6mHcO3NEhWh1GYAAAAAE1aeNOO2Vek9qcydjCJoWA==; incap_ses_552_3129864=taLBdLcNQVg/xHlVNhmpBxWh1GYAAAAAK8iW4cBF9J3mMw5Tx0/Edg==; incap_ses_415_3129864=5NQXEzQwghS14v4ocGDCBRWh1GYAAAAAN/bU1O/8SGNsU3Y4zWzIvg==; incap_ses_1360_3129864=9TjfGpPdKD823IQ23rDfEhWh1GYAAAAAamTNo0wqwTQs6QLRUTaqVw==; incap_ses_541_3129864=cYdZBtbwyETwfG3qwgSCBxWh1GYAAAAAIqMoMXNN/HkuRvWH3mc57g==; incap_ses_225_3129864=+RBzSYc8yRCLnwbicVwfAxWh1GYAAAAAKNo2ryOP+ydVfRnlqh0/Ig==; _gat=1; _ga_9FRGLJE1MP=GS1.1.1725205052.1.1.1725211082.0.0.0; _ga=GA1.1.996194746.1725205052; _ga_YWJTRKWPVS=GS1.2.1725205052.1.1.1725211082.0.0.0; incap_ses_1448_3129864=2IjcGQG+AwMIAv0dW1QYFMqh1GYAAAAAOJtHq1hLkwckBMLCG1OLig==; incap_ses_1248_3129864=bdzTWeRmrwe4zFWxgclREcqh1GYAAAAA+i9k569FsuH/LvRB0xh9Yg==; incap_ses_32_3129864=b/e8ZBXvAyI4x35c/K9xAMqh1GYAAAAAOaFmiqYT6EkmnvenB9wt1g==; incap_ses_1308_3129864=2Yw2eflhciPa/Q9PMPMmEsqh1GYAAAAAxDbbJrPyXcEBVEjcoJpSqQ==; incap_ses_133_3129864=G+4ZfQ5aBhGvJe5S7ILYAcqh1GYAAAAAJTEZnsLSKbdnWpOLu/s1Mg==",
    "sec-ch-ua-full-version-list": '"Chromium";v="128.0.6613.114", "Not;A=Brand";v="24.0.0.0", "Microsoft Edge";v="128.0.2739.54"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": "",
    "sec-ch-ua-platform": "Windows",
    "sec-ch-ua-platform-version": "10.0.0",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
}

# 수집된 데이터를 담을 리스트
data = []
seen = set()

# 데이터가 없을 때까지 페이지를 반복해서 처리하는 함수
def scrape_data(area1, area_name):
    page = 1
    previous_data_length = 0  # 이전 데이터 길이를 저장할 변수
    while True:
        time.sleep(1)
        # 페이로드 설정
        params = {
            "cate1": "",
            "cate2": "",
            "area1": area1,
            "display_cnt": "100",
            "page": str(page)
        }

        try:
            # GET 요청 보내기
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # HTTP 에러 발생 시 예외 발생
        except requests.exceptions.HTTPError as errh:
            print(f"HTTP Error: {errh}")
            break
        except requests.exceptions.ConnectionError as errc:
            print(f"Error Connecting: {errc}")
            break
        except requests.exceptions.Timeout as errt:
            print(f"Timeout Error: {errt}")
            break
        except requests.exceptions.RequestException as err:
            print(f"An error occurred: {err}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')

        # 'ent_tit' 클래스 요소 찾기
        elements = soup.find_all(class_='ent_tit')
        if not elements:
            break  # 데이터가 없으면 종료

        # 각 요소에서 업소이름과 업소번호 추출
        for element in elements:
            # 업소이름 추출
            h4_tag = element.find('h4')
            if h4_tag:
                업소이름 = h4_tag.get_text(strip=True)
            else:
                ent_name = element.find(class_='ent_name')
                if ent_name:
                    업소이름 = ent_name.get_text(strip=True)
                else:
                    업소이름 = "이름 없음"

            # 업소번호 추출
            a_tag = element.find('a')
            if a_tag:
                업소번호 = a_tag.get_text(strip=True)
            else:
                업소번호 = "번호 없음"

            # 중복 체크 (업소번호만 기준)
            if 업소번호 not in seen:
                seen.add(업소번호)

                obj = {
                    "카테고리": area_name,
                    "업소이름": 업소이름,
                    "업소번호": 업소번호
                }
                print(f"{page} - obj : {obj}")
                data.append(obj)

        # 현재 데이터 길이와 이전 길이를 비교하여 같으면 중지
        if len(data) == previous_data_length:
            print(f"No new data found on page {page}. Stopping.")
            break
        else:
            previous_data_length = len(data)

        print(f"==========================================")
        page += 1  # 다음 페이지로 넘어가기

def main():
    # 각 지역에 대해 데이터를 추출
    for area1, area_name in categories.items():
        print(f"\n카테고리: {area_name} (area1={area1})")
        scrape_data(area1, area_name)

    # 수집된 데이터를 데이터프레임으로 변환
    df = pd.DataFrame(data)

    # 엑셀 파일로 저장
    df.to_excel("output.xlsx", index=False)
    print("데이터가 output.xlsx 파일에 저장되었습니다.")

if __name__ == "__main__":
    main()
