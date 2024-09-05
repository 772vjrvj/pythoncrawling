import os
import re

# PdfReader 또는 PdfFileReader를 가져옴
try:
    from PyPDF2 import PdfReader  # 최신 버전
except ImportError:
    from PyPDF2 import PdfFileReader as PdfReader  # 구버전 대체

def extract_title_from_pdf(pdf_path):
    """
    주어진 PDF 파일에서 논문 제목을 추출하는 함수
    """
    try:
        # PDF 파일 열기
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            first_page = reader.pages[0]
            text = first_page.extract_text()

            # 논문 제목 추출 (패턴은 필요에 따라 조정 가능)
            title_pattern = re.compile(r'(?i)(?:title:|abstract|study).*?\n([^\n]+)')
            match = title_pattern.search(text)

            if match:
                return match.group(1).strip()
            else:
                return "Title not found"
    except Exception as e:
        return f"Error reading {pdf_path}: {e}"

def extract_titles_from_folder(folder_path):
    """
    주어진 폴더 내 모든 PDF 파일에서 제목을 추출하는 함수
    """
    if not os.path.exists(folder_path):
        print(f"Error: The folder {folder_path} does not exist.")
        return

    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in the folder: {folder_path}")
        return

    for filename in pdf_files:
        pdf_path = os.path.join(folder_path, filename)
        title = extract_title_from_pdf(pdf_path)
        print(f"PDF 파일: {filename} - 제목: {title}")

def main():
    """
    프로그램 실행 경로의 'pdf' 폴더에서 모든 PDF 파일의 제목을 추출하는 메인 함수
    """
    try:
        # 현재 프로그램 실행 경로에 있는 'pdf' 폴더를 타겟으로 설정
        current_directory = os.path.dirname(os.path.abspath(__file__))
        pdf_folder_path = os.path.join(current_directory, "pdf")

        # PDF 파일들에서 제목 추출
        extract_titles_from_folder(pdf_folder_path)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
