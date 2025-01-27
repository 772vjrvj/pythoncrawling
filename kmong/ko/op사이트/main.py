import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 카테고리 별 페이로드 설정
categories = {
    "1": "오피",
    "4": "건마",
    "3": "휴게텔",
    "6": "립카페",
    "2": "유흥주점",
    "5": "핸플.키스방",
    "8": "패티쉬",
    "7": "안마"
}

url = "https://starop03.com"
headers = {
    "authority": "starop03.com",
    "method": "GET",
    "path": "/?cate1=1",
    "scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko,en;q=0.9,en-US;q=0.8",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
    "sec-ch-ua-arch": "x86",
    "Cookie": "mchk=p; dt=20240902; visid_incap_3129864=r8HTlClDT921N/DfFqqkRjqK1GYAAAAAQUIPAAAAAABXY29qpqBd+NRS/LNNfttK; incap_ses_170_3129864=KkZvbuXHYnB0lswuOPZbAjuK1GYAAAAAcSxqgP3ZLLxMEYTs0IwjHw==; _gid=GA1.2.1685249802.1725205053; popup_banner_tf=true; incap_ses_224_3129864=HS6zZefaWi4O6Pfl8M4bA4iK1GYAAAAA7V5oJpi+qDR976O74465kA==; incap_ses_539_3129864=8sGlXVbmrFOnl0Dyx+l6BziL1GYAAAAAQIEh1Mu1GxwVLzMMj4zRdQ==; incap_ses_540_3129864=8lZ7cu0y9DUdhuCTRnd+B5+N1GYAAAAAitqFCuz5aGhDKUkhZJ29TA==; incap_ses_551_3129864=nyX/TSJ0S27uTdCPtYulBxiO1GYAAAAAJyvEAUX0Uzn3l6tj26CgKQ==; incap_ses_1832_3129864=C0AlO4aDUCOnwZWQaZJsGSOP1GYAAAAAKGmfkYJqzeONU8pXGUNTzw==; incap_ses_1828_3129864=f5EdTTeFoEW+rJX4blxeGSSP1GYAAAAAFg8n6Xl2FaOwzc1XRq1hHg==; incap_ses_1827_3129864=6KdLCX7dFADFNo5V8M5aGSWP1GYAAAAAun5ZLUIYNNVst9vaqDk8EA==; user_auth=eXe3vs3Robew2nO9eWw%3D; wuinfo=XFSKmq6nZtuwoZ6BopPEx%2BzYp8K%2BqFmBpH%2BC35jmLgsCYsIaFr%2FcURz2dZN18YOIo0TQl5jooYvLmp3ClYW50dnbr9W%2Bt5O%2FoIbKlNjdsA%3D%3D; incap_ses_553_3129864=6Jjtew944z8s9+2hsqasB3aR1GYAAAAA/9yteJ0FpeSM7wY6wHe48w==; incap_ses_1163_3129864=hWGxVNEqe1PBdDXudM4jEJSR1GYAAAAAr+2tjWC8yg6bAU5jRtZPqw==; incap_ses_881_3129864=65XPYdFviQeELJ138/A5DJOU1GYAAAAAl8oKuzetqEm3RcPrdMCDVw==; incap_ses_883_3129864=ohLvFZo49R5Lg2XA8AtBDJSU1GYAAAAA7BfdfKLVwZI/hO6OwIRf0g==; incap_ses_172_3129864=hphdejnws2HNVwV5NRFjApSU1GYAAAAABAfoook5v7eI9GmYGfJErg==; incap_ses_549_3129864=Uw/TZzSHBxMFpO4VuHCeB5SU1GYAAAAAVJPfS5oQAHIusX8bvS0ZLw==; incap_ses_1357_3129864=U3LZfboKzEH7GkE5YgjVEpSU1GYAAAAAVwTnyKGM6cdYtn+vIQyE/Q==; incap_ses_173_3129864=HoMwYv9k3SPQzW4d155mApSU1GYAAAAAHSgVl43vp6PYRGOfOrZW0w==; incap_ses_1360_3129864=O2DpX0ZHC2LR3WI23rDfEpSU1GYAAAAAvBmBApYKWGd+CbQ49QMmCA==; incap_ses_171_3129864=Bc/UYcdRkX7R/YIduYNfApSU1GYAAAAAqjBp8C27MisAMwgNirBPQQ==; incap_ses_1448_3129864=hW0aOVM4+2jTle4dW1QYFKmU1GYAAAAA/e4l+2hwF9TjOeKZ2YfHYA==; incap_ses_1359_3129864=xGAZByVgoy0y+tx5XyPcEqqU1GYAAAAAqga9PUJeUg8PJwy7TCJuHA==; incap_ses_1449_3129864=v2R7BeXiIwMTXGfQ2eEbFLWU1GYAAAAA0YaM+Prn/TQkWuB0xJW0vQ==; incap_ses_415_3129864=X4C4TqcRRg+R7vEocGDCBbWU1GYAAAAAfp0wusZ1bua+/M0o4fQAVg==; incap_ses_32_3129864=7oc2ZaypJhl902pc/K9xALaU1GYAAAAAmM0FdQIvQ28UQcrWL36usg==; incap_ses_538_3129864=j6/dRiqeGTGMfBykS1x3B7WU1GYAAAAAbhVy1VG8FufzNhnlkiQK4g==; incap_ses_541_3129864=5HpyKZISLAKMQmLqwgSCB8KU1GYAAAAA3+clLIUsAPLZrKsa+jEmbA==; incap_ses_1358_3129864=Ttqab7aC8FLMIuDX4JXYEvOU1GYAAAAAMkpKIymZv0trvGIV3+4TQw==; incap_ses_1308_3129864=S9XUGkdCVRXcwQBPMPMmEv+U1GYAAAAANUDcstQXdsCM2l6KYxcRCg==; cf_clearance=Zgj0tfcoIboIGpS9P_HvnmThtfAg8MpSrygVLzU_UAk-1725208743-1.2.1.1-Rgki.L_OHH6alyl_rW1bMCat9W9EjXwhPcNYRiHoN6PUpPBqOLR1fr7K4f2bg2NcIYP0OMquZHg50KhTlzYAu.dPWnvkYgr_IDANL6._s1XtIsgTgYEd8TmvN9gPtoYPUI8T4tkN_jhhcUcu6ZuoopLqgbqyL73jRwm08SCFHlQ7_m9VXLtwkqscuOkjqIztO.1qRYVjL48gEMZKAbWASUOeWtQ7PtRdZHjw_fzAHCOpDTfSlRaMUqYWQkoL3NWXX_Zb8Eq5S9gAeLS892pTBpeMYKhYb9hx5PiTVaDWsr0NM1PZ5S5gOMKRyuA1tBUica6n3NaRHbXQUgR9pDjkadIJjGTZktgOGBCN904OPY3x8wOzJ32PeB0zUbFXn3mMlYpCnft9j7acxlyLyyoqTlkJyfM91ZoUM11aL_v_vBcBN.aQqjOqQ1A5sk1.13QBHk5zzyBwUKnQ7aaP3uy7Yg; incap_ses_225_3129864=/hVSNqLWdnosZvvhcVwfA6yY1GYAAAAAJlCEeXDkF6ADivzOdCuCsQ==; incap_ses_1287_3129864=7nGIHeYktU0bhELNzFfcEbOY1GYAAAAAQEIlPT0USwcQsy6EZywt0Q==; incap_ses_552_3129864=krqLHIGpd2I6S3FVNhmpB7SY1GYAAAAASpFu6gz+uNGL/Fg4rkWrww==; incap_ses_884_3129864=mPK5ZktCByZ6c9Jeb5lEDLyY1GYAAAAAFtRFQq2+d2YRlYPJCM2bvg==; incap_ses_880_3129864=C4QkCXok4j3FiBTUdGM2DL+Y1GYAAAAAcJvCjSPFLIQAGh/7yrD2LQ==; incap_ses_1447_3129864=fvM3bWhQyEplZ07B88YUFNGY1GYAAAAACu6613MRZX82nf45vUJo8g==; incap_ses_882_3129864=BdnKd/Imgwl5RZgXcn49DNGY1GYAAAAAVzgy/kdFGaMqcEnnRvwvWg==; incap_ses_1249_3129864=wBLhLtyvg3lPoOpSAFdVEdGY1GYAAAAAzOuUlX7AlogFFY4i35UIZA==; incap_ses_1248_3129864=wVpXc7ptwhb5FEqxgclREdKY1GYAAAAA1PJ04PG/zHgi35fdWrkDyw==; incap_ses_133_3129864=XpwLQS9D9B1CRuRS7ILYAXSZ1GYAAAAAlvDwKQ4ZobnGV9kKTqr+8g==; _ga_9FRGLJE1MP=GS1.1.1725205052.1.1.1725209163.0.0.0; _ga=GA1.2.996194746.1725205052; _gat=1; _ga_YWJTRKWPVS=GS1.2.1725205052.1.1.1725209163.0.0.0; incap_ses_1356_3129864=En7db6GKAyLtK1yR43rREkua1GYAAAAAYqh5IjcP7VJgMeyOY6TNtg==; incap_ses_1355_3129864=BWblIOWvEzVHPKOHcO3NEkya1GYAAAAA5VJ7rG/1+Qn5ens4hDAUDQ==; incap_ses_543_3129864=FI05JMYQgyzgOUo3wB+JB0ya1GYAAAAA1fGVk764m6CFjW2fqAwa9w==",
    "sec-ch-ua-bitness": "64",
    "sec-ch-ua-full-version": "128.0.2739.54",
    "sec-ch-ua-full-version-list": '"Chromium";v="128.0.6613.114", "Not;A=Brand";v="24.0.0.0", "Microsoft Edge";v="128.0.2739.54"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": "",
    "sec-ch-ua-platform": "Windows",
    "sec-ch-ua-platform-version": "10.0.0",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
}


# 수집된 데이터를 담을 리스트
data = []
seen = set()

# 데이터가 없을 때까지 페이지를 반복해서 처리하는 함수
def scrape_data(cate1, cate_name):
    page = 1
    while True:
        time.sleep(1)
        # 페이로드 설정
        params = {
            "cate1": cate1,
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
        if not elements or len(elements) == 2:
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
                    "카테고리": cate_name,
                    "업소이름": 업소이름,
                    "업소번호": 업소번호
                }
                print(f"{page} - obj : {obj}")
                data.append(obj)

                print(f"==========================================")
                page += 1  # 다음 페이지로 넘어가기

def main():
    # 각 카테고리에 대해 데이터를 추출
    for cate1, cate_name in categories.items():
        print(f"\n카테고리: {cate_name} (cate1={cate1})")
        scrape_data(cate1, cate_name)

    # 수집된 데이터를 데이터프레임으로 변환
    df = pd.DataFrame(data)

    # 엑셀 파일로 저장
    df.to_excel("output.xlsx", index=False)
    print("데이터가 output.xlsx 파일에 저장되었습니다.")

if __name__ == "__main__":
    main()
