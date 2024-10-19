import pandas as pd
import requests
import time
import random
from bs4 import BeautifulSoup


def main():
    # 엑셀 파일 읽기
    file_path = "2405건 테스트.xlsx"
    df = pd.read_excel(file_path)

    # 사업자번호 배열 만들기
    사업자번호 = df['사업자번호'].tolist()

    # 결과를 저장할 리스트
    results = []

    # 각 사업자번호에 대해 정보 가져오기
    for idx, no in enumerate(사업자번호, start=1):
        print(f"no : {no}")
        url = f"https://bizno.net/article/{no}"

        # 요청 헤더 설정
        headers = {
            "authority": "bizno.net",
            "method": "GET",
            "path": f"/article/{no}",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "cookie": "_fwb=245OBtNwJVQSlilnFL8AGIU.1729260902361; ASPSESSIONIDAWDTTQSR=DHMPOOJBBDNHHFNOHKLDEBGD; ASPSESSIONIDAWCRSQTQ=LLLLDEKBCIFEOOJCJPPGELPO; ASPSESSIONIDQUBQQQQQ=JNFNDEKBOBCNMEDJCLKEOIMO; ASPSESSIONIDAGCRQTSR=OHMDEEKBBNIOJGHODLEKLBEI; ASPSESSIONIDCGASQSQS=PIKBFEKBKCDAFMDHDLGDPCPL; ASPSESSIONIDAGBQQRRT=JDLDGEKBGEAAKFCKHFCBMPPC; ASPSESSIONIDSEBTRSSR=GNKLGEKBCDBOBNEBMIKLCCPN; ASPSESSIONIDCUCSQRTR=NGPPGEKBMCHOFBCGNJNFHFLL; ASPSESSIONIDSWDSQRTR=HACHHEKBLBHLODLOHDBEKHJH; ASPSESSIONIDQEBTRSSS=JBNBMEKBNIMBAFBFPBLLHGCN; wcs_bt=29d6cd0a469df6:1729317252; __gads=ID=9eaabee3cd743bc7:T=1729260902:RT=1729317251:S=ALNI_MY8SqC_-nheXLkFzyp6IT8gYKWa9A; __gpi=UID=00000f48fa7382e2:T=1729260902:RT=1729317251:S=ALNI_MaEkuoEtSt81P4uZY2eCINmei5TVA; __eoi=ID=76aba3d4bc0031e5:T=1729260902:RT=1729317251:S=AA-AfjbQbmpcNAzsNZLxfSnHcn7D; FCNEC=%5B%5B%22AKsRol_1KgKV4YA6cCb_iy9ffAjOVVr8xLOn9mYaywUDGWqg78QQCqCwpiVefpVedYW6X1ohKc0nhrX6CWfiZNU6DRrXhfrlz3pV7ZDCMDE_xjJGYt3yqlVQgsYipePyAIAXhhryUUx0Eca3R1v7nwLB6E2zqFPy_Q%3D%3D%22%5D%5D",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        }

        # 요청 보내기
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 홈페이지 정보 가져오기
            homepage_tag = soup.find('th', string='홈페이지')
            homepage = homepage_tag.find_next_sibling('td').text.strip() if homepage_tag else ""

            # 'https://'가 없으면 추가
            if homepage and not homepage.startswith("https://"):
                homepage = "https://" + homepage

            # 회사이메일 정보 가져오기
            email_tag = soup.find('th', string='회사이메일')
            email = email_tag.find_next_sibling('td').text.strip() if email_tag else ""

            obj = {'사업자번호': no, '홈페이지': homepage, '이메일': email}
            print(f"obj : {obj}")
            results.append(obj)
        else:
            print(f"Error fetching data for {no}: {response.status_code}")

        # 50개마다 엑셀 업데이트
        if idx % 50 == 0:
            print(f"{idx}개 완료, 엑셀 파일 업데이트 중...")
            # 결과를 데이터프레임으로 변환
            results_df = pd.DataFrame(results)

            # 기존 데이터프레임에 새로운 컬럼 추가
            df['홈페이지'] = results_df.set_index('사업자번호')['홈페이지']
            df['이메일'] = results_df.set_index('사업자번호')['이메일']

            # 엑셀 파일로 저장
            df.to_excel(f"2405건 테스트_업데이트_{idx}.xlsx", index=False)
            print(f"{idx}개 업데이트 완료!")

            # 결과 리스트 초기화
            results.clear()

        # 요청 사이 시간 간격을 둠
        time.sleep(random.uniform(2, 3))

    # 남은 결과가 있으면 마지막으로 업데이트
    if results:
        print(f"남은 데이터 업데이트 중...")
        results_df = pd.DataFrame(results)

        # 기존 데이터프레임에 새로운 컬럼 추가
        df['홈페이지'] = results_df.set_index('사업자번호')['홈페이지']
        df['이메일'] = results_df.set_index('사업자번호')['이메일']

        # 엑셀 파일로 저장
        df.to_excel("2405건 테스트_최종업데이트.xlsx", index=False)
        print("최종 업데이트 완료!")


if __name__ == "__main__":
    main()
