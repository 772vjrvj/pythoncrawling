import fitz  # PyMuPDF
import spacy
import os

# spaCy의 영어 모델 로드
nlp = spacy.load('en_core_web_sm')

# PDF 파일에서 첫 페이지 텍스트 추출 함수
def extract_first_page_text(pdf_file):
    doc = fitz.open(pdf_file)
    first_page = doc.load_page(0)  # 첫 번째 페이지 로드
    text = first_page.get_text("text")  # 텍스트 추출
    return text

# 논문 제목 추출 함수 (사람 이름 감지 전까지 제목 추출)
def extract_paper_title(text):
    # 텍스트를 줄 단위로 분할
    lines = text.split('\n')

    # 제외할 키워드 정의 (이 키워드는 제목에 포함되지 않도록 필터링)
    exclude_keywords = ['issn', 'coden', 'e-mail', 'www', 'doi', 'abstract', 'journal', 'research article', 'introduction']

    title = ""
    capture = False  # 제목을 추출할 때 사용되는 플래그

    for line in lines:
        line_clean = line.strip()

        # 제외할 키워드가 포함된 라인은 제외
        if any(keyword in line_clean.lower() for keyword in exclude_keywords):
            continue

        # 사람 이름 감지 (spaCy 사용)
        doc = nlp(line_clean)
        if any(ent.label_ == "PERSON" for ent in doc.ents):
            break  # 사람 이름이 감지되면 제목 추출 중단

        # 적절히 긴 줄을 제목 후보로 추가 (일반적으로 제목은 10자 이상)
        if len(line_clean) > 10:
            if capture:
                title += " " + line_clean  # 이전 줄과 이어 붙이기
            else:
                title = line_clean  # 첫 줄일 때 새로 시작
            capture = True  # 제목을 추출하기 시작한 상태

    # 추출된 제목 반환
    if title:
        return title
    else:
        return "제목을 찾을 수 없습니다."

# 현재 디렉토리의 'pdf' 폴더에 있는 파일 경로 설정
def get_pdf_file_path(file_name):
    current_dir = os.getcwd()  # 현재 실행되는 디렉토리
    pdf_dir = os.path.join(current_dir, "pdf")  # 현재 디렉토리의 'pdf' 폴더
    pdf_file_path = os.path.join(pdf_dir, file_name)  # pdf 폴더 내 PDF 파일 경로
    return pdf_file_path

# PDF 파일 경로 설정
pdf_file_name = "[5].pdf"  # 논문 파일 이름
pdf_file_path = get_pdf_file_path(pdf_file_name)

# PDF에서 첫 페이지 텍스트 추출
first_page_text = extract_first_page_text(pdf_file_path)

# 논문 제목 추출
paper_title = extract_paper_title(first_page_text)

# 결과 출력
print(f"논문 제목: {paper_title}")
