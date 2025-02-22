import requests

def fetch_albamon_jobs(page=1, areas="I000", employment_types="FULL_TIME"):
    url = f"https://www.albamon.com/_next/data/ATAI5UtAAxHVNzlMofNXK/jobs/area.json?page={page}&areas={areas}&employmentTypes={employment_types}"

    headers = {
        "authority": "www.albamon.com",
        "method": "GET",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=1, i",
        "referer": f"https://www.albamon.com/jobs/area?page={page+1}&areas={areas}&employmentTypes={employment_types}",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "x-nextjs-data": "1"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()

        # collection 리스트 추출
        collection_list = data.get("pageProps", {}).get("dehydratedState", {}).get("queries", [])[0].get("state", {}).get("data", {}).get("base", {}).get("normal", {}).get("collection", [])

        # pagination 정보 추출
        pagination = data.get("pageProps", {}).get("dehydratedState", {}).get("queries", [])[0].get("state", {}).get("data", {}).get("base", {}).get("pagination", {})

        return collection_list, pagination
    else:
        print(f"Error: {response.status_code}")
        return [], {}

def fetch_albamon_detail(recruit_no="107944833"):
    url = f"https://bff-general.albamon.com/company/companies/8UO2ay3e07ocecyhQ0ENmw==/detail-info?recruitNo={recruit_no}"

    headers = {
        "authority": "bff-general.albamon.com",
        "method": "GET",
        "scheme": "https",
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "albamon-domain-type": "pc",
        "origin": "https://www.albamon.com",
        "priority": "u=1, i",
        "referer": "https://www.albamon.com/jobs/area?page=1&areas=I000&employmentTypes=FULL_TIME",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("Detail Info:", data)
        return data
    else:
        print(f"Error: {response.status_code}")
        return {}

if __name__ == "__main__":
    collection, pagination = fetch_albamon_jobs()
    print("Collection List:", collection)
    print("Pagination:", pagination)

    detail_info = fetch_albamon_detail()
    print("Detail Info:", detail_info)
