from bs4 import BeautifulSoup

def extract_values_from_file(filename):
    values = []
    # 파일 읽기
    with open(filename, encoding="utf-8") as f:
        html = f.read()

    # BeautifulSoup으로 파싱
    soup = BeautifulSoup(html, "html.parser")

    # div id="listpage" 찾기
    listpage_div = soup.find("div", id="listpage")
    if listpage_div:
        # table class="table table-bordered" 찾기
        table = listpage_div.find("table", class_="table table-bordered")
        if table:
            # tbody 안의 모든 tr 찾기
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                # 각 tr을 순회하면서
                for row in rows:
                    # 첫 번째 td 찾기
                    first_td = row.find("td")
                    if first_td:
                        # 첫 번째 td 안의 checkbox input 찾기
                        checkbox = first_td.find("input", {"type": "checkbox"})
                        if checkbox:
                            value = checkbox.get("value")
                            if value:
                                values.append(value)
    return values

def main():
    files = ["list1.html", "list2.html"]
    all_values = []
    for file in files:
        file_values = extract_values_from_file(file)
        all_values.extend(file_values)

    print(all_values)

if __name__ == "__main__":
    main()
