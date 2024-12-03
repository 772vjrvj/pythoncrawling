import fitz  # PyMuPDF
import re
import os

# 월-월 연도를 확인하는 함수
def is_month_to_month_year(line):
    # 월 리스트 정의
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # 불필요한 공백을 모두 제거한 후에 패턴 검색
    cleaned_line = ' '.join(line.split())

    # 월-월 연도 형식을 확인하는 패턴
    for month1 in months:
        for month2 in months:
            if f"{month1}-{month2} " in cleaned_line:
                # 월-월 뒤에 4자리 숫자가 있는지 확인
                next_part = cleaned_line.split(f"{month1}-{month2} ")[1][:4]
                if next_part.isdigit():
                    return True
    return False

# PDF 파일에서 첫 페이지 텍스트 추출 함수
def extract_first_page_text(pdf_file):
    doc = fitz.open(pdf_file)
    first_page = doc.load_page(0)
    text = first_page.get_text("text")
    return text

# 숫자 4자리와 점을 확인하는 함수
def is_four_digits_with_dot(line):
    # 공백을 제거한 후, 마지막에서 5자리를 추출하여 확인
    stripped_line = line.strip()
    if len(stripped_line) >= 5 and stripped_line[-5:-1].isdigit() and stripped_line[-1] == '.':
        return True
    return False


# 논문 제목 추출 함수
def extract_paper_title(text):
    lines = text.split('\n')

    # 제외할 키워드 목록
    exclude_keywords = [
        'issn', 'coden', 'e-mail', 'www', 'doi', 'journal', 'research article',
        'vol.', 'original paper', 'Scientiﬁc African', 'at ScienceDirect',
        'Contents lists available at ScienceDirect',
        'Full Terms & Conditions of access and use can be found at',
        'Pharmaceutical Biology', 'Food Chemistry', '©Science and Education Publishing', 'crop protection', 'cereal crop', 'ARTÍCULO ORIGINAL', 'Res.'
        , 'PITUITARY–GONADAL', 'PHYTOTHERAPY RESEARCH', 'SHORT COMMUNICATION'
    ]

    title = ""
    capture = False

    # 패턴 정의
    star_comma_pattern = re.compile(r'[\*\u204E],')
    star_comma_pattern_2 = re.compile(r'[\*\u204E]\s+and')
    numbers_letters_comma_pattern = re.compile(r'[1-9a-c],')
    numbers_letters_and_pattern = re.compile(r'[1-9a-c]\s+and')
    author_line_pattern_2 = re.compile(r'([A-Z]\.\s[A-Z]\.\s[A-Za-z]+)(,\s[A-Z]\.\s[A-Z]\.\s[A-Za-z]+)*(,?\s?AND\s[A-Z]\.\s[A-Z]\.\s[A-Za-z]+)?')

    # 대문자.대문자. 공백 패턴 2개 이상
    initials_pattern = re.compile(r'\b[A-Z]\.[A-Z]\.\s.*?\b[A-Z]\.[A-Z]\.\s')

    # 대문자.대문자. 공백 대문자 패턴 추가
    author_initial_pattern = re.compile(r'\b[A-Z]\.[A-Z]\.\s[A-Z]')

    # 연도(yyyy;) 패턴을 감지하는 패턴
    year_semicolon_pattern = re.compile(r'.*\d{4};')

    # 월과 연도 패턴 (예: August 2016)
    month_year_pattern = re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b')

    # 밑줄이 포함된 줄을 필터링하기 위한 패턴
    underline_pattern = re.compile(r'^_+$')  # 밑줄만 있는 줄을 제외

    # 4자리 숫자와 점 (예: 2023.) 패턴 추가
    four_digits_dot_pattern = re.compile(r'\b\d{4}\.\b')

    # 제외할 패턴 추가
    vol_pattern = re.compile(r'\bVol\.\s+\d+')
    original_paper_pattern = re.compile(r'\bORIGINAL PAPER\b')
    year_volume_pattern = re.compile(r'\(\d{4}\)\s+\d+')  # 예: (2023) 14

    # 저자 패턴 추가
    author_pattern_1 = re.compile(r'\s·\s[A-Z]\.\s')
    author_pattern_2 = re.compile(r'\s[A-Z]\.\s')
    roman_numerals_comma_pattern = re.compile(r'[I|II|III],')

    # URL 패턴 추가
    url_pattern = re.compile(r'https?://\S+')

    # 숫자와 콤마가 2개 이상 포함된 패턴 정의 (숫자와 콤마 사이의 공백을 고려)
    multiple_commas_pattern = re.compile(r'(,\d+\s*,\s*){1,}')

    # © 기호와 연도 패턴
    copyright_year_pattern = re.compile(r'©\s*\d{4}')

    # Received: 또는 Accepted: 패턴
    received_accepted_pattern = re.compile(r'Received:|Accepted:')

    # 연도로 끝나는 줄 패턴
    year_end_pattern = re.compile(r'\d{4}\.$')

    # *Corresponding author. 패턴
    corresponding_author_pattern = re.compile(r'\*Corresponding\s+author\.')

    # Email: 패턴
    email_pattern = re.compile(r'Email:\s*')

    # University 앞뒤 공백 패턴
    # Article in 패턴 추가
    article_in_pattern = re.compile(r'Article\s+in\b')

    # 전화번호 패턴 추가 (예: :567-577)
    phone_pattern = re.compile(r':\d{3}-\d{3}')

    # 숫자만으로 이루어진 라인 패턴 추가
    numbers_only_pattern = re.compile(r'^\d+$')

    # Introduction과 정확히 일치하는 라인 패턴
    introduction_pattern = re.compile(r'^Introduction$')

    process_title = True

    for line in lines:
        line_clean = line.strip()

        # "Cien. Inv. Agr."를 찾을 경우 "research paper"까지 continue
        if "Cien. Inv. Agr." in line_clean:
            process_title = False
            continue

        # "research paper"가 나올 때까지 continue
        if not process_title:
            if "research paper" in line_clean.lower():
                process_title = True
            continue

        if is_month_to_month_year(line_clean):
            continue


        # 숫자로만 구성된 라인은 continue
        if numbers_only_pattern.match(line_clean):
            continue

        # 4자리 숫자와 점 패턴이 감지되면 continue
        if four_digits_dot_pattern.search(line_clean):
            continue

        # 대문자.대문자. 공백 패턴 2개 이상이 감지되면 break
        if initials_pattern.search(line_clean):
            break

        # 대문자.대문자. 공백 대문자 패턴 검출
        if author_initial_pattern.search(line_clean):
            break

        # Article in 패턴 검출
        if article_in_pattern.search(line_clean):
            break

        # URL이 포함된 라인 건너뜀
        if url_pattern.search(line_clean):
            continue

        # 제외할 키워드가 포함된 라인 건너뜀
        if any(keyword.lower() in line_clean.lower() for keyword in exclude_keywords):
            continue

        # 연도(yyyy;) 패턴이 있는 라인은 건너뜀
        if year_semicolon_pattern.match(line_clean):
            continue

        # 월과 연도가 포함된 라인 감지
        if month_year_pattern.search(line_clean):
            break

        if is_four_digits_with_dot(line_clean):
            continue

        # 밑줄이 포함된 라인은 건너뜀
        if underline_pattern.match(line_clean):
            continue

        # 패턴 검출: Vol., ORIGINAL PAPER, (2023) 14 형식
        if vol_pattern.search(line_clean) or original_paper_pattern.search(line_clean) or year_volume_pattern.search(line_clean):
            continue

        # 숫자와 콤마가 2개 이상 포함된 패턴 검출
        if multiple_commas_pattern.search(line_clean):
            break

        # 전화번호 패턴 검출 (예: :567-577)
        if phone_pattern.search(line_clean):
            continue

        # Introduction 패턴 검출
        if introduction_pattern.match(line_clean):
            continue

        if "1," in line_clean and "* AND" in line_clean:
            break

        if "*," in line_clean:
            break



        # 저자 패턴 검출
        if ((numbers_letters_comma_pattern.search(line_clean) or numbers_letters_and_pattern.search(line_clean)) and star_comma_pattern.search(line_clean)) or \
                author_line_pattern_2.match(line_clean) or \
                author_pattern_1.search(line_clean) or \
                roman_numerals_comma_pattern.search(line_clean) or \
                (author_pattern_2.search(line_clean) and not "L. en" in line_clean):
            break

        # © 기호와 연도 패턴 검출
        if copyright_year_pattern.search(line_clean):
            continue

        # Received: 또는 Accepted: 패턴 검출
        if received_accepted_pattern.search(line_clean):
            continue

        # 연도로 끝나는 줄 검출
        if year_end_pattern.match(line_clean):
            continue

        # *Corresponding author. 패턴 검출
        if corresponding_author_pattern.search(line_clean):
            continue

        # Email: 패턴 검출
        if email_pattern.search(line_clean):
            continue

        # 제목 추출: 제목을 이어붙임
        if len(line_clean) > 0 and not line_clean.startswith("_"):  # 밑줄로 시작하지 않는 긴 줄만 제목으로 간주
            if capture:
                title += " " + line_clean
            else:
                title = line_clean
                capture = True


    # 제목이 발견되지 않았을 경우, 제목 추출 시도 범위를 확장
    if not title:
        # 제목이 포함될 가능성이 있는 추가 구간을 시도하여 찾기
        for line in lines:
            if len(line.strip()) > 10 and not line.strip().startswith("_"):
                title = line.strip()
                break

    if title and title.strip("_"):  # 제목이 빈 문자열이 아닌 경우에만 반환
        return title.strip()
    else:
        return "제목을 찾을 수 없습니다."

# 현재 디렉토리의 'pdf' 폴더에 있는 파일 경로 설정
def get_pdf_file_path(file_name):
    current_dir = os.getcwd()
    pdf_dir = os.path.join(current_dir, "pdf")
    pdf_file_path = os.path.join(pdf_dir, file_name)
    return pdf_file_path

# PDF 파일 경로 설정
pdf_file_name = "[28].pdf"  # PDF 파일 이름 수정
pdf_file_path = get_pdf_file_path(pdf_file_name)

# PDF에서 첫 페이지 텍스트 추출
first_page_text = extract_first_page_text(pdf_file_path)

# 논문 제목 추출
paper_title = extract_paper_title(first_page_text)

# 결과 출력
print(f"논문 제목: {paper_title}")
