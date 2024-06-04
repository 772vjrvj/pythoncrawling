import requests
from bs4 import BeautifulSoup
import openpyxl
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os  # os 모듈 추가
import threading


# 크롤링할 키워드 리스트
keywords = []

# 최대 연관 키워드 수
max_keywords = 0

# 크롤링 결과를 저장할 리스트
data = []

# 각 키워드에 대해 크롤링 수행하는 함수
def crawl_keyword(keyword):
    url = f'https://www.cardveryview.com/네이버-키워드-검색량-조회-확인/?keyword={keyword}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # id가 firstKeyword인 테이블 찾기
    table1 = soup.find('table', id='firstKeyword')

    if table1:
        rows = table1.find_all('tr')
        pc_search_volume = int(rows[0].find_all('td')[1].text.strip().replace(',', ''))
        mobile_search_volume = int(rows[1].find_all('td')[1].text.strip().replace(',', ''))
        total_search_volume = int(rows[2].find_all('td')[1].text.strip().replace(',', ''))
        competition_index = rows[3].find_all('td')[1].text.strip()
        data.append({
            '연관키워드': keyword,
            '월간 PC 검색량': pc_search_volume,
            '월간 MOBILE 검색량': mobile_search_volume,
            '총합': total_search_volume,
            '경쟁지수': competition_index
        })

    # id가 keywordTableth인 테이블 찾기
    table2 = soup.find('table', id='keywordTableth')

    if table2:
        rows = table2.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 5:  # 데이터가 있는 행인지 확인
                related_keyword = cols[0].text.strip()
                pc_search_volume = int(cols[1].text.strip().replace(',', ''))  # 콤마 제거 후 숫자로 변환
                mobile_search_volume = int(cols[2].text.strip().replace(',', ''))  # 콤마 제거 후 숫자로 변환
                total_search_volume = int(cols[3].text.strip().replace(',', ''))  # 콤마 제거 후 숫자로 변환
                competition_index = cols[4].text.strip()
                if pc_search_volume + mobile_search_volume >= 20:
                    if related_keyword not in keywords and len(keywords) < max_keywords:  # 중복 및 최대 키워드 개수 체크
                        keywords.append(related_keyword)
                        data.append({
                            '연관키워드': related_keyword,
                            '월간 PC 검색량': pc_search_volume,
                            '월간 MOBILE 검색량': mobile_search_volume,
                            '총합': total_search_volume,
                            '경쟁지수': competition_index
                        })

def update_progress_bar(progress, total):
    progress_bar['value'] = progress
    progress_bar['maximum'] = total
    root.update_idletasks()

def start_crawling():
    global data
    data = []

    global keywords
    keywords = []

    global max_keywords

    input_keywords = keyword_entry.get().strip()  # 입력 필드에서 키워드를 가져옴
    if not input_keywords:  # 입력값이 없으면 경고창을 띄움
        messagebox.showwarning("경고", "키워드를 입력하세요.")
        keyword_entry.focus_force()  # 경고창 띄운 후 입력 필드에 포커스 설정
        return

    keywords = keyword_entry.get().split(',')  # 입력 필드에서 키워드를 가져와서 쉼표로 분리하여 리스트로 변환


    max_keywords = max_keywords_entry.get()  # 최대 연관 키워드 수를 입력받음
    if not max_keywords:  # 입력값이 없으면 경고창을 띄움
        messagebox.showwarning("경고", "크롤링 하려는 수를 입력하세요.")
        max_keywords_entry.focus_force()  # 경고창 띄운 후 입력 필드에 포커스 설정
        return

    max_keywords = int(max_keywords_entry.get())

    if max_keywords > 10000:
        messagebox.showwarning("경고", "최대 연관 키워드 수는 10,000을 초과할 수 없습니다.")
        max_keywords_entry.focus_force()  # 경고창 띄운 후 입력 필드에 포커스 설정
        return


    # 입력 필드와 버튼 비활성화
    keyword_entry.config(state=tk.DISABLED)
    max_keywords_entry.config(state=tk.DISABLED)
    crawl_button.config(state=tk.DISABLED)
    save_button.config(state=tk.DISABLED)


    # 크롤링 작업을 백그라운드 스레드에서 실행
    crawling_thread = threading.Thread(target=crawling_worker)
    crawling_thread.start()

def crawling_worker():
    start_time = time.time()
    for i, keyword in enumerate(keywords):
        crawl_keyword(keyword.strip())  # 키워드 좌우의 공백 제거 후 크롤링 함수에 전달
        update_progress_bar(i + 1, len(keywords))  # 프로그래스 바 업데이트
    end_time = time.time()
    total_time = end_time - start_time

    result_text.set(f"총 걸린 시간: {total_time:.2f} 초\n총 키워드 수: {len(data)}")

    # 크롤링 완료 후 입력 필드와 버튼 활성화
    keyword_entry.config(state=tk.NORMAL)
    max_keywords_entry.config(state=tk.NORMAL)
    crawl_button.config(state=tk.NORMAL)
    save_button.config(state=tk.NORMAL)

def save_to_excel():
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
    if file_path:
        # 파일 경로와 파일 이름을 분리
        folder, filename = os.path.split(file_path)
        # 파일 이름에 확장자를 지정하여 저장
        filename = os.path.join(folder, f"{filename}.xlsx")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['연관키워드', '월간 PC 검색량', '월간 MOBILE 검색량', '총합', '경쟁지수'])
        for row in data:
            ws.append(list(row.values()))
        wb.save(filename)
        messagebox.showinfo("저장 성공", "엑셀 파일이 성공적으로 생성되었습니다.")
        print("데이터가 성공적으로 저장되었습니다.")
    else:
        print("파일 경로를 선택하지 않았습니다.")



# GUI 설정
root = tk.Tk()
root.title("네이버 키워드 크롤러")
root.geometry("450x300")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# 제목 레이블 생성
title_label = ttk.Label(frame, text="네이버 연관 키워드 검색")
title_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

# 네이버 연관 키워드 검색 링크
link_text = """https://www.cardveryview.com"""

# 텍스트 위젯 생성
link_text_widget = tk.Text(frame, height=1, width=30)
link_text_widget.insert(tk.END, link_text)
link_text_widget.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
link_text_widget.config(state=tk.DISABLED)  # 텍스트 편집 비활성화

# 결과 출력 라벨
result_text = tk.StringVar()
result_label = ttk.Label(frame, textvariable=result_text, wraplength=300)
result_label.grid(row=2, column=0, columnspan=2, pady=10)

# 입력 필드 및 라벨
keyword_label = ttk.Label(frame, text="키워드를 입력하세요(쉼표로 구분):")
keyword_label.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
keyword_entry = ttk.Entry(frame, width=30)
keyword_entry.grid(row=3, column=1, padx=5, pady=5)

max_keywords_label = ttk.Label(frame, text="크롤링 하려는 수(최대 10000):")
max_keywords_label.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
max_keywords_entry = ttk.Entry(frame, width=30)
max_keywords_entry.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)

# 프로그래스 바 생성
progress_bar = ttk.Progressbar(frame, orient='horizontal', mode='determinate')
progress_bar.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)

# 크롤링 시작 버튼
crawl_button = ttk.Button(frame, text="크롤링 시작", command=start_crawling)
crawl_button.grid(row=6, column=0, padx=5, pady=5)

# 엑셀 저장 버튼
save_button = ttk.Button(frame, text="엑셀로 저장", command=save_to_excel)
save_button.grid(row=6, column=1, padx=5, pady=5)




root.mainloop()