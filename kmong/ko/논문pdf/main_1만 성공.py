import fitz  # PyMuPDF
import re
import os

def extract_first_page_text(pdf_file):
    doc = fitz.open(pdf_file)
    first_page = doc.load_page(0)
    text = first_page.get_text("text")
    return text

def extract_paper_title(text):
    lines = text.split('\n')
    exclude_keywords = ['issn', 'coden', 'e-mail', 'www', 'doi', 'abstract', 'journal', 'research article', 'introduction']
    author_pattern = re.compile(r'^[A-Z][a-z]+\s[A-Z][a-z]+(?:\d|\*|,|[a-c])*')

    title = ""
    capture = False

    for line in lines:
        line_clean = line.strip()

        if any(keyword in line_clean.lower() for keyword in exclude_keywords):
            continue

        if author_pattern.match(line_clean):
            break

        if len(line_clean) > 10 and not capture:
            title = line_clean
            capture = True

    if title:
        return title
    else:
        return "제목을 찾을 수 없습니다."

def get_pdf_file_path(file_name):
    current_dir = os.getcwd()
    pdf_dir = os.path.join(current_dir, "pdf")
    pdf_file_path = os.path.join(pdf_dir, file_name)
    return pdf_file_path

pdf_file_name = "[1].pdf"
pdf_file_path = get_pdf_file_path(pdf_file_name)

first_page_text = extract_first_page_text(pdf_file_path)
paper_title = extract_paper_title(first_page_text)

print(f"논문 제목: {paper_title}")
