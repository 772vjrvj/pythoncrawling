import fitz  # PyMuPDF
import re
import os

# PDF 파일에서 첫 페이지 텍스트 추출 함수
def extract_first_page_text(pdf_file):
    doc = fitz.open(pdf_file)
    first_page = doc.load_page(0)
    text = first_page.get_text("text")
    return text

# 논문 제목 추출 함수
def extract_paper_title(text):
    lines = text.split('\n')
    exclude_keywords = ['issn', 'coden', 'e-mail', 'www', 'doi', 'abstract', 'journal', 'research article', 'introduction']

    title = ""
    capture = False

    # 사람 이름이 포함된 줄을 감지하는 패턴 (콤마(,) 앞에 숫자나 *, a, b, c가 2개 이상 있는 경우)
    author_line_pattern = re.compile(r'.*[\da-c\*].*[\da-c\*].*,')  # 숫자, *, a-c가 2개 이상 포함된 줄

    for line in lines:
        line_clean = line.strip()

        # 제외할 키워드가 포함된 라인은 건너뜀
        if any(keyword in line_clean.lower() for keyword in exclude_keywords):
            continue

        # 저자 이름이 포함된 줄 감지되면 제목 추출 중단
        if author_line_pattern.match(line_clean):
            break

        # 제목 추출: 제목을 이어붙임
        if len(line_clean) > 10:
            if capture:
                title += " " + line_clean
            else:
                title = line_clean
                capture = True

    if title:
        return title
    else:
        return "제목을 찾을 수 없습니다."

# 현재 디렉토리의 'pdf' 폴더에 있는 파일 경로 설정
def get_pdf_file_path(file_name):
    current_dir = os.getcwd()
    pdf_dir = os.path.join(current_dir, "pdf")
    pdf_file_path = os.path.join(pdf_dir, file_name)
    return pdf_file_path

# PDF 파일 경로 설정 1,2,3 통과
pdf_file_name = "[3].pdf"  # 파일 이름 수정
pdf_file_path = get_pdf_file_path(pdf_file_name)

# PDF에서 첫 페이지 텍스트 추출
first_page_text = extract_first_page_text(pdf_file_path)

# 논문 제목 추출
paper_title = extract_paper_title(first_page_text)

# 결과 출력
print(f"논문 제목: {paper_title}")
