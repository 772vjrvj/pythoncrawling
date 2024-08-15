import requests
import json
import pandas as pd

def fetch_data():
    # mainUrl 설정
    mainUrl = "https://www.temu.com"

    # 조회할 url
    url = "https://www.temu.com/api/poppy/v1/search?scene=search"

    # payload 설정
    payload = {
        "disableCorrect": False,
        "filterItems": "",
        "listId": "9418d09961014fdcbce2dacdd1c21248",
        "offset": 0,
        "pageSize": 120,
        "pageSn": 10009,
        "query": "여성용 가방",
        "scene": "search",
        "searchMethod": "user"
    }

    # 헤더 설정
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "anti-content": "0aqAfxnZLOloF99VZg-3cD1eXbx44pkRoYnUDk40DuCIntns61CKkm7jKf_2-vYf66vaX72s80otear4uN24PE6XQNxNvNRWxAWxRvWKz7ApKPoQZ7fngjf26UqEVVJePqXkB58PapQmgGEZEWQOrKszT7zvsCzSkacTltCThreBmKFxs4ofUlsCOPkF98PbmGj336g01atVPDPpoSwB1BS6RERL5zxc5aELzO6O4woPUWq64HtG4OtfLpPXPxoD-vwEGIG1hByiNaSeUJjfAe2lyCJBfHUpy4Cj6nrtYV5Yng2pw6dBvCGCpH0mJgI9pUXXA1VTunf_fJv4vE9akk-Oyh690Hc9KuS39EFSnKwJ4B_eU_4jCwm-xXqmIk7eugPhDM2uxmBeT8r1p7sAMiHG4kJSk13Ej7-sANApzJkiXlNFxR61KWvlKLKRySuBjnF8G1JImh5_cvOiqjNRhFRY5iqhYtcVxcg1eEZN",
        "content-length": "194",
        "content-type": "application/json;charset=UTF-8",
        "cookie": "region=185; language=ko; currency=KRW; api_uid=CmyENmannHFlXgBgLDVFAg==; timezone=Asia%2FSeoul; webp=1; _nano_fp=XpmxX5PjX0dbnqdqlT_gXzjlJCCTidyaQ5k~jUJ1; _bee=4UoHmiJ1ctuzf2HydeOj5mhi7nHuDdOG; njrpl=4UoHmiJ1ctuzf2HydeOj5mhi7nHuDdOG; dilx=kLHZkv~x0z0Sh3yVGx54s; hfsc=L3yIeos26Tvx1ZLOeA==; _ttc=3.Dgqp8qZKZeBR.1753796618; verifyAuthToken=ldrFseqtunY8WxWpYYH5GQ6875bc747cadf7e45; __cf_bm=hyZjON66FLTruzjYK7NDOGH89wpNY5d4NHAqQJsZldI-1722263304-1.0.1.1-gfIBGCf9COozgtdN2wMGWUNgqw5.EaB7HA6d10iIAW7x.X49IVyBjAopuhrOR6jJa2qCVkilCraz2Uq3V4J4uw",
        "origin": "https://www.temu.com",
        "priority": "u=1, i",
        "referer": "https://www.temu.com/search_result.html?search_key=%EC%97%AC%EC%84%B1%EC%9A%A9%20%EA%B0%80%EB%B0%A9&search_method=recent&refer_page_el_sn=200254&srch_enter_source=top_search_entrance_10005&refer_page_name=home&refer_page_id=10005_1722263757154_iftos7c1ms&refer_page_sn=10005&_x_sessn_id=2d9vdugdsw",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "verifyauthtoken": "ldrFseqtunY8WxWpYYH5GQ6875bc747cadf7e45"
    }

    # POST 요청 보내기
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    # 응답 데이터 확인
    if response.status_code == 200:
        data = response.json()
        return data, mainUrl
    else:
        print("데이터를 불러오는데 실패했습니다. 상태 코드:", response.status_code)
        return None, None

def parse_data(data, mainUrl):
    # 결과에서 필요한 정보 추출
    goods_list = data['result']['data']['goods_list']

    # 추출한 데이터를 저장할 리스트 초기화
    extracted_data = []

    for item in goods_list:
        image_url = item['image']['url'] if 'image' in item else ''
        detail_url = mainUrl + "/" + item['link_url'] if 'link_url' in item else ''
        title = item['title'] if 'title' in item else ''
        price = item['price_info']['price_str'] if 'price_info' in item and 'price_str' in item['price_info'] else ''
        rating = item['comment']['goods_score'] if 'comment' in item and 'goods_score' in item['comment'] else ''

        data = {
            "메인 이미지": image_url,
            "상세 Url": detail_url,
            "이름": title,
            "가격": price,
            "평점": rating
        }


        extracted_data.append(data)

    return extracted_data

def save_to_excel(data, filename="temu_bags.xlsx"):
    # DataFrame으로 변환
    df = pd.DataFrame(data)

    # 엑셀 파일로 저장
    df.to_excel(filename, index=False)
    print(f"데이터가 엑셀 파일로 저장되었습니다: {filename}")

def main():
    data, mainUrl = fetch_data()
    if data:
        parsed_data = parse_data(data, mainUrl)
        save_to_excel(parsed_data)

if __name__ == "__main__":
    main()
