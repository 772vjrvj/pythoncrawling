import requests
from bs4 import BeautifulSoup
import pandas as pd

# 추출한 goodNum 값 리스트
good_nums = ['205373386', '205366003', '205366000', '205357361', '205356424', '205352746', '205348785', '205344738', '205326963', '205320733', '205320288', '205312279', '205291614', '205257438', '205093254', '205058475', '205372969', '205372876', '205366021', '205361907', '205358545', '205357367', '205356402', '205353476', '205343436', '205337927', '205332487', '205330335', '205326957', '205326939', '205326560', '205325451', '205320712', '205313936', '205313921', '205313704', '205312639', '205306448', '205274516', '205002823', '205320756', '205313939', '205313935', '205292571', '205288948', '205284977', '205284908', '205281428', '205273012', '205271596', '205257550', '205246512', '205245422', '205243586', '205113909', '205021742', '204954044', '204556735', '204552939', '205298615', '205291733', '205275824', '205273034', '205271588', '205270585', '205266287', '205257235', '205255326', '205254372', '205253001', '205245829', '205222754', '204985339', '204973473', '204956038', '204954155', '204749468', '204511361', '205257856', '205256574', '205253557', '205248784', '205246527', '205246497', '205243463', '205131606', '205128020', '205123903', '205092448', '205079778', '205077024', '205075570', '204939899', '204922830', '204883887', '204830912', '204801387', '204494797', '205164942', '205146830', '205132276', '205124164', '205084223', '205058166', '205005246', '205198838', '205171843', '205152100', '205148092', '205146451', '205144909', '204830371', '205193437', '205161804', '205161522', '205161369', '205152084', '205126713', '205117427', '205115432', '205109885', '205096896', '204821380', '204818712', '204430818', '204317297', '205094872', '205078421', '205075574', '205058476', '205033118', '204719442', '204979433', '204969191', '204301422', '204927802', '204921431', '204920586', '204859454', '204858640', '204858351', '204418083', '204446441', '204307982', '205368385', '205363094', '205081992', '204613241', '204546840', '204517664', '204511470', '204447676']


# 요청에 사용할 헤더
headers = {
    "authority": "chsjjj.shop.blogpay.co.kr",
    "method": "GET",
    "scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "cookie": "ch-veil-id=84ceba26-7f6d-43b9-bae9-7dd55bec1412; bHideResizeNotice=1; PHPSESSID=di6o0nppojeln93elraldjro3b; device=pro; user_agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36; _gid=GA1.3.657263305.1740573205; bannerType=2; _ga_VQPYCBY0KG=GS1.1.1740581285.5.1.1740589306.5.0.0; _ga=GA1.1.773170237.1740329654; blogpay_session=eyJpdiI6InBXNFwvVzZwMzJFY05UbzVZNTFNN0lRPT0iLCJ2YWx1ZSI6Im94QUxxaE9ud2V3emxHRnRFN3VIOVpJVVlyckFuNGIwaTdIWkxIWm9VK1doeUQ2ZUlpdnQ1WWd5ZFhhXC9jN2dlY0JiUUdyMDZxdTBuSXNTMzgrRzFRZz09IiwibWFjIjoiYjZiYjA0N2IxZjFjYmI1MWRlZGEyOTA4OWM3MTM5MDgxZTRlOWNiOTZjYWY4YmExMmQzMjQ5ZjBiYWU5YjM4ZSJ9",
    "priority": "u=0, i",
    "sec-ch-ua": "\"Not(A:Brand\";v=\"99\", \"Google Chrome\";v=\"133\", \"Chromium\";v=\"133\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
}

data_list = []

# 각 goodNum 값마다 URL 요청 및 데이터 추출
for goodNum in good_nums:
    url = f"https://chsjjj.shop.blogpay.co.kr/controller/goods/gmodify?goodNum={goodNum}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # 전시카테고리 추출
        select_tag = soup.find('select', {'name': 'sCate1'})
        selected_option = select_tag.find('option', selected=True) if select_tag else None
        category = selected_option.text.strip() if selected_option else ""

        # 상품명 추출
        goodName_input = soup.find("input", id="goodName")
        goodName = goodName_input.get("value", "").strip() if goodName_input else ""

        # 상품가격 추출
        goodPrice_input = soup.find("input", id="goodPrice")
        goodPrice = goodPrice_input.get("value", "").strip() if goodPrice_input else ""

        # 재고수량 추출
        inven_input = soup.find("input", id="inven")
        inven = inven_input.get("value", "").strip() if inven_input else ""

        # 대표 이미지 URL 추출
        img_tag = soup.find("img", id="tmpGoodImg")
        image_url = img_tag.get("src", "").strip() if img_tag else ""

        # 옵션 테이블 파싱
        option_data = []
        opt_table = soup.find("table", id="optListTable")
        if opt_table:
            tbody = opt_table.find("tbody")
            if tbody:
                for idx, tr in enumerate(tbody.find_all("tr"), start=1):
                    tds = tr.find_all("td")
                    if len(tds) >= 5:
                        option_name = tds[1].find("input").get("value", "").strip() if tds[1].find("input") else ""
                        option_value = tds[2].find("input").get("value", "").strip() if tds[2].find("input") else ""

                        select_tag = tds[4].find("select")
                        option_use = ""
                        if select_tag:
                            selected_option = select_tag.find("option", selected=True)
                            option_use = selected_option.get("value", "").strip() if selected_option else ""

                        option_data.append({
                            "옵션명": option_name,
                            "옵션값": option_value,
                            "옵션사용여부": "Y" if option_use == "1" else "N"
                        })

        print(option_data)

        # 기본 상품 정보 저장
        obj = {
            "goodNum": goodNum,
            "전시카테고리": category,
            "상품명": goodName,
            "상품가격": goodPrice,
            "재고수량": inven,
            "대표 이미지": image_url,
            "옵션 정보": option_data
        }

        print(obj)
        data_list.append(obj)
    else:
        print(f"goodNum {goodNum} 요청 실패, 상태 코드: {response.status_code}")

# ✅ Excel 저장
data_expanded = []
for item in data_list:
    base_info = {
        "goodNum": item["goodNum"],
        "전시카테고리": item["전시카테고리"],
        "상품명": item["상품명"],
        "상품가격": item["상품가격"],
        "재고수량": item["재고수량"],
        "대표 이미지": item["대표 이미지"]
    }

    if item["옵션 정보"]:
        for opt in item["옵션 정보"]:
            row = base_info.copy()
            row.update(opt)
            data_expanded.append(row)
    else:
        data_expanded.append(base_info)



# DataFrame 생성 및 저장
df = pd.DataFrame(data_expanded)
excel_filename = "goods_data_with_options.xlsx"
df.to_excel(excel_filename, index=False)
print(f"✅ Excel 파일 저장 완료: {excel_filename}")
