import requests, time, re, json
from bs4 import BeautifulSoup

def main(page_index: int):
    """
    화순군 고시공고 목록 + 상세 내용 크롤러 (단일 함수)
    반환: [{'not_ancmt_mgt_no', '번호', '고시공고번호', '제목', '담당부서', '등록일', '게재기간', '조회수', '내용'}, ...]
    """
    URL = "https://eminwon.hwasun.go.kr/emwp/gov/mogaha/ntis/web/ofr/action/OfrAction.do"

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        # "Cookie": "...",  # ← 쿠키 제거
        "Host": "eminwon.hwasun.go.kr",
        "Origin": "https://eminwon.hwasun.go.kr",
        "Referer": URL,
        "Sec-CH-UA": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/141.0.0.0 Safari/537.36"),
    }

    # === 내부 POST 재시도 함수 ===
    def post_retry(data, max_retries=3, delay=2):
        import urllib3
        from urllib3.exceptions import InsecureRequestWarning
        urllib3.disable_warnings(InsecureRequestWarning)

        for i in range(max_retries):
            try:
                r = requests.post(
                    URL, data=data, headers=headers,
                    timeout=(15, 30),  # connect 15s / read 30s
                    verify=False
                )
                r.raise_for_status()
                return r.text
            except requests.exceptions.ReadTimeout:
                # 필요시 로그 남기고 싶으면 아래 주석 해제
                # print(f"[WARN] ({i+1}/{max_retries}) ReadTimeout, retry...")
                pass
            except Exception:
                # print(f"[WARN] ({i+1}/{max_retries}) 기타 오류: {e}")
                pass
            time.sleep(delay * (i + 1))
        return ""

    # === 1. 목록 요청 (★ 1페이지만 initValue/countYn = Y) ===
    is_first = (page_index == 1)
    list_payload = {
        "pageIndex": str(page_index),
        "jndinm": "OfrNotAncmtEJB",
        "context": "NTIS",
        "method": "selectListOfrNotAncmt",
        "methodnm": "selectListOfrNotAncmtHomepage",
        "not_ancmt_mgt_no": "",
        "homepage_pbs_yn": "Y",
        "subCheck": "Y",
        "ofr_pageSize": "10",
        "not_ancmt_se_code": "01,02,03,04,05",
        "title": "고시 공고",
        "cha_dep_code_nm": "",
        "initValue": "Y" if is_first else "N",
        "countYn": "Y" if is_first else "N",
        "list_gubun": "A",
        "yyyy": "",
        "not_ancmt_sj": ""
    }

    html = post_retry(list_payload)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if len(tables) < 5:
        return []

    table = tables[4]
    rows = table.find_all("tr")

    items = []
    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) < 7:
            continue
        if tds[0].get_text(strip=True) == "번호":
            continue

        onclick_attr = tds[0].get("onclick") or ""
        m = re.search(r"searchDetail\('(\d+)'\)", onclick_attr)
        not_ancmt_mgt_no = m.group(1) if m else ""

        def txt(i): return tds[i].get_text(strip=True) if i < len(tds) else ""

        items.append({
            "not_ancmt_mgt_no": not_ancmt_mgt_no,
            "번호": txt(0),
            "고시공고번호": txt(1),
            "제목": txt(2),
            "담당부서": txt(3),
            "등록일": txt(4),
            "게재기간": txt(5),
            "조회수": txt(6)
        })

    if not items:
        return []

    # === 2. 상세 내용 요청 (요청 간 0.25s 지연) ===
    for it in items:
        no = it["not_ancmt_mgt_no"]
        if not no:
            it["내용"] = ""
            continue

        detail_payload = {
            "pageIndex": "1",
            "jndinm": "OfrNotAncmtEJB",
            "context": "NTIS",
            "method": "selectOfrNotAncmt",
            "methodnm": "selectOfrNotAncmtRegst",
            "not_ancmt_mgt_no": no,
            "homepage_pbs_yn": "Y",
            "subCheck": "Y",
            "ofr_pageSize": "10",
            "not_ancmt_se_code": "01,02,03,04,05",
            "title": "고시 공고",
            "cha_dep_code_nm": "",
            "initValue": "Y",
            "countYn": "Y",
            "list_gubun": "A",
            "yyyy": "",
            "not_ancmt_sj": ""
        }

        html2 = post_retry(detail_payload)
        if not html2:
            it["내용"] = ""
            continue

        soup2 = BeautifulSoup(html2, "html.parser")
        td = soup2.find("td", style=re.compile("word-break: *break-all"), colspan="4")
        if td:
            it["내용"] = td.get_text(separator="\r\n", strip=True)
        else:
            it["내용"] = ""

        time.sleep(0.25)  # 상세 간 지연

    return items


# 실행 예시
if __name__ == "__main__":
    all_data = []
    page = 1

    while True:
        print(f"\n[INFO] === {page}페이지 수집 중 ===")
        result = main(page)

        if not result:
            print(f"[INFO] {page}페이지에서 데이터 없음 → 종료")
            break

        print(f"[INFO] {page}페이지 수집 완료 ({len(result)}건)")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        all_data.extend(result)
        page += 1
        time.sleep(1)  # 서버 부하 방지

    print(f"\n[INFO] 총 {len(all_data)}건 수집 완료")
    # print(json.dumps(all_data, ensure_ascii=False, indent=2))
