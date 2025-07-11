import requests
from bs4 import BeautifulSoup
import openpyxl

# 요청 헤더 설정
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "connection": "keep-alive",
    "cookie": '2a0d2363701f23f8a75028924a3af643=MjE4LjE0Ny4xMzIuMjM2; _ga=GA1.1.1939587267.1752063067; _fbp=fb.1.1752063066681.197719143388228130; _fcOM={"k":"d8f6b4914290d3cd-372f2c75197ef17f944-64b","i":"218.147.132.236.4437","r":1752063066742}; PHPSESSID=u29u98n389r34da8foolhhjed4; 5b1ceb69146c0bafdc082ff42248da98=MTc0OTc4NzU0Mg%3D%3D; _ga_ZYPC3VQM7S=GS2.1.s1752074826$o3$g1$t1752076461$j60$l0$h0',
    "host": "www.luxurycelebrity2.kr",
    "if-modified-since": "Wed, 09 Jul 2025 15:53:44 GMT",
    "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}

data_it_ids = []

# 페이지 반복
for page in range(1, 52):
    url = f"https://www.luxurycelebrity2.kr/shop/list.php?ca_id=2010&sort=&sortodr=&page={page}"
    print(f"[+] 요청: {url}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"[!] 실패: {url} (status {response.status_code})")
        continue

    soup = BeautifulSoup(response.text, "html.parser")
    buttons = soup.select("button.btn_cart.sct_cart")

    for index, btn in enumerate(buttons):
        it_id = btn.get("data-it_id")
        print(f"{index}: {it_id}")
        if it_id:
            data_it_ids.append(it_id)

print(f"[✓] 총 {len(data_it_ids)}개 it_id 수집 완료")

# 엑셀 저장
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "data_it_id"
ws.append(["data-it_id"])

for it_id in data_it_ids:
    ws.append([it_id])  # 엑셀은 여전히 행 단위로 쓰기 때문에 여긴 [] 유지

wb.save("it_ids.xlsx")
print("[✓] 엑셀 저장 완료 → it_ids.xlsx")
