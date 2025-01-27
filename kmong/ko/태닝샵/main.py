import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_ids_from_page(page):
    url = f"https://www.naviya.net/bbs/board.php?bo_table=b49&bannertab2=76%4096%40&page={page}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to retrieve page {page}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    elements = soup.find_all("tr", class_="class_list_tr")

    ids = []
    for element in elements:
        element_id = element.get("id")
        if element_id and element_id.startswith("list_tr_"):
            id_number = element_id.replace("list_tr_", "")
            ids.append(id_number)

    return ids

def extract_info_from_id(id):
    url = f"https://www.naviya.net/bbs/board.php?bo_table=b49&wr_id={id}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to retrieve details for ID {id}")
        return None

    soup = BeautifulSoup(response.content, "html.parser")

    # Extract telephone number
    tel_element = soup.find(class_="tel_01_pc")
    tel = tel_element.text.strip().replace(" ", "") if tel_element else ""

    # Extract ID
    id_element = soup.find(class_="mw_basic_view_title").find("a")
    extracted_id = id_element.text.strip() if id_element else ""

    # Extract title
    title_element = soup.find(class_="mw_basic_view_subject").find("h1")
    title = title_element.text.strip() if title_element else ""

    # Extract location
    loc_element = soup.find(style="margin:0 auto;line-height:22px;width:500px;text-align:right;")
    loc = loc_element.text.strip() if loc_element else ""

    obj =  {
        "작성자": extracted_id,
        "전화번호": tel,
        "위치": loc,
        "게시글 제목": title
    }

    print(f" obj {obj} ")

    return obj

def main():
    all_ids = []
    for page in range(1, 42):
        print(f"page : {page}")
        ids = get_ids_from_page(page)
        print(f"ids : {ids}")
        all_ids.extend(ids)

    all_info = []

    for id in all_ids:
        info = extract_info_from_id(id)
        if info:
            all_info.append(info)

    # Create a DataFrame
    df = pd.DataFrame(all_info, columns=["작성자", "전화번호", "위치", "게시글 제목"])

    # Save the DataFrame to an Excel file
    df.to_excel('naviya_info.xlsx', index=False)

    print("Data has been saved to naviya_info.xlsx")

if __name__ == "__main__":
    main()
