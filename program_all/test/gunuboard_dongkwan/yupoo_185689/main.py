import requests
from bs4 import BeautifulSoup
import pandas as pd

# 기본 설정
base_url = "https://tbstore.x.yupoo.com"
target_url = f"{base_url}/categories/185689?isSubCate=true&page="

# 사용자가 제공한 헤더
headers = {
    "authority": "tbstore.x.yupoo.com",
    "method": "GET",
    "scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "if-none-match": 'W/"59102-DA0thjIsSL0PJIxKgr9cjZQx9Vg"',
    "priority": "u=0, i",
    "referer": "https://tbstore.x.yupoo.com/categories/185689?isSubCate=true&page=2",
    "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "cookie": "_uab_collina=175206283153427863937987; language=en-US; version=7.10.41; _ga_5S4FNBRMVK=GS2.1.s1752062955$o1$g0$t1752062956$j59$l0$h0; _ga=GA1.1.2142819794.1752062832; indexlockcode=tb1234; _ga_3R06MM98Q4=GS2.1.s1752065376$o2$g0$t1752065377$j59$l0$h0; _ga_P5QMXEZ5BQ=GS2.1.s1752065376$o2$g0$t1752065377$j59$l0$h0; tfstk=glt-GK0kajcl2ttRnLu0tLQsu5kmIqvrqQJ_x6fuRIdvUs2urMjk9EdBgafWtgVKvII58UfhZ6IpLCHmscmMULSFVfcij9ioEISFODjIoiMdzMsSscmMFWrsNyGMxpqdv_BCAT_CdKMABOsQR6OCGZ61I7sBOBZfGO6QRysCR-MALs1CAMOBhxBhG6GkPXCbF6qpSXfmj-N4seLBDTQR1Kn4AkIzjaC6FsEI1nBJO195MkZC6F-3EKpowlJc4hdOIQmb2Cpw0IBX1DhAYI8BO9djbWjySQ-NkKu_cKSRgNTCkYiWHgCRWtbYFyIJRQ-dzUeEQKsWgF5NPqlVH3xGJ17YGb9DH__9JQc4A_Y9hIQMmSqGYI8BO9dbwgRwjhKVX5fOKzMxHyzFPtoeMyW5uIbVVtCieDUU8ZkVH1Dx9yzFPU6Asxf88y7yi; Hm_lvt_28019b8719a5fff5b26dfb4079a63dab=1752062832,1752125294; HMACCOUNT=3C1AA4ED5C2ACAE8; _ga_XMN82VEYLV=GS2.1.s1752153965$o3$g1$t1752154050$j59$l0$h0; Hm_lpvt_28019b8719a5fff5b26dfb4079a63dab=1752154051"
}

# 결과 저장 리스트
href_list = []

# 페이지 반복
for page in range(1, 4):
    url = target_url + str(page)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # album__main 찾기
    anchors = soup.find_all("a", class_="album__main")
    for idx, a in enumerate(anchors, start=len(href_list) + 1):
        href = a.get("href")
        if href:
            full_href = href if href.startswith("http") else base_url + href
            href_list.append(full_href)
            print(f"[{idx}] {full_href}")

# 엑셀 저장
df = pd.DataFrame(href_list, columns=["Album Links"])
df.to_excel("yupoo_links.xlsx", index_label="Index")

print("\n✅ 완료되었습니다. yupoo_links.xlsx 로 저장됨.")
