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
        "scene": "search",
        "pageSn": 10009,
        "offset": 0,
        "listId": "69426b1cc6dd4a499b2c56b3ce0e2389",
        "pageSize": 120,
        "query": "여성 목걸이",
        "filterItems": "",
        "searchMethod": "user",
        "disableCorrect": False
    }

    # 헤더 설정
    headers = {
        "authority": "www.temu.com",
        "method": "POST",
        "path": "/api/poppy/v1/search?scene=search",
        "scheme": "https",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "anti-content": "0aqAfaOYdySYy99oQBdozO90aHSqPHUVNon7fljkeH3ZUO5HAb0nikQ3BgFDurkOg-pK1FOuO0tsPe3jnxTcEXSx696g_NZPHr0w26837DoJg-iZI45CIbyhwpBlLoAWi30ii6-oG4jEajGAlG7GSFiQGU0D5FRIf6EeRwWb4WUr7d_RJ2NZMoQD5IAPFW2FBXnRTrmm6a0hC0j6cPfc01yTzPGofK0q9nqAEnHGyAxzvZjw1TZvfl-eXx2JHSVATESlJWUAp4RHUUAtdQfqlTcsPjtOTTcIrAzue0JjvIRCmwAkLM15nLukZFrqhZ0GwtrCJNiTNqCErHnJINDftk8_zozpqahUsas8XQsVyLTO70a0APRG-J5sh0UuNTZ6hR07K2HcIqdAEtIl8tzeepQY6_yzMvedtcJXIKB6aoVemfxwDvmldOpqqep9uSVtZfToT0s4LHp5174DHI0dfgoaWXd63TZL6JfmJyFb3Coji7m1YgIKNHVgjeCYASxJTTYdoDjRM1dr1NWWTzZfqYmaoz06luM9bxDiTur8TBQFLXq5fWyHu3wAILSr2jS_reZFL6Y1eSRIgN11ZIwQVu0u4AvS1a7xNpsBls-7goWCEtWr_n1WIk6J9y0Vd-E6FTHjcmncGaRSMHoBVHAlUjS_Cg_bjB-SQmTTHrdndZrQTg7HqRPXzF4XK7-FM18kBCyHkwfEZFDt5fx7Vw_wMKTYlyGS8FKktCYD9WgZ46DYomIW_nbUe6paefmd-lKI0ZevomgPkDPO5p1tyqGaoWmXNmQLE26MEG-5mTytv5p_Utn0YAhYs-vqJe4xaYh6DQ5rERu-iVLQxodXJ_KFZPL",
        "content-length": "192",
        "content-type": "application/json;charset=UTF-8",
        "cookie": "region=185; language=ko; currency=KRW; api_uid=Cm3EUma9xmqCxABHZ/glAg==; timezone=Asia%2FSeoul; webp=1; _nano_fp=XpmxXqmaXqgqn0djXC_pbKCoyOQjaLLqMy7XEpdy; _bee=4UoHmiJ1ctuzf2HydeOj5mhi7nHuDdOG; njrpl=4UoHmiJ1ctuzf2HydeOj5mhi7nHuDdOG; dilx=kLHZkv~x0z0Sh3yVGx54s; hfsc=L3yIeos26Tvx1ZLOeA==; _device_tag=CgI2WRIIWG9MU3RkbnkaMNrEOLr5zU44g5yZCOsCKkbF+KJZ3v8lnQCEfAd+uaOFk64ZYogVSw6JgFF0lRzKnjAC; _ttc=3.rEA8aZtsXcfk.1755249152; __cf_bm=j4dd_OBhgUAoFY95Pjo1tX7DT44vKOCY9B9ETI2RJkk-1723859956-1.0.1.1-jI.pQfuDmZKSzv1k1qA2ZgSTQiHvko4Ga64xOawYC4Bd2a_Vtu.26WPykw8zzMetVc4GSExtbkX5_WBqzVbOJA; _hal_tag=ANjXDmJCkcK9oIGkV9fDD4bb2R4QaSNHDR+w7q5+J/z5nCUk7sfiiNwsB+vtaa85vg==; AccessToken=YQNDL2NDMXKTIANEUD6QCVTCILIVQOZ7TCIWQNQODRNVNENK24YQ0110b9e1f65a; user_uin=BB6JGKXN5EDDJKIHK2SWSHR6PK5IQHPMSAQH6DJA; isLogin=1723859975843",
        "origin": "https://www.temu.com",
        "priority": "u=1, i",
        "referer": "https://www.temu.com/search_result.html?search_key=%EC%97%AC%EC%84%B1%20%EB%AA%A9%EA%B1%B8%EC%9D%B4&search_method=recent&refer_page_el_sn=200254&srch_enter_source=top_search_entrance_10005&_x_sessn_id=xpp1uvxosf&refer_page_name=home&refer_page_id=10005_1723859978935_7ijphpvhq8&refer_page_sn=10005",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "verifyauthtoken": "qsJbyNKrHuLw5b7hu5ofbQ59feea75b87f6729b",
        "x-document-referer": "https://www.temu.com/?_x_sessn_id=xpp1uvxosf&refer_page_name=login&refer_page_id=10013_1723859959420_w9nqcsf17l&refer_page_sn=10013&is_back=1"
    }

    # POST 요청 보내기
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    # 응답 데이터 확인
    if response.status_code == 200:
        data = response.json()
        print(f"data : {data}")
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

def save_to_excel(data, filename="temu_necklaces.xlsx"):
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
