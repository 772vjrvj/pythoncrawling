import os
import pdfplumber
import fitz  # PyMuPDF
import pandas as pd
import re


months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

def clean_abstract(text):
    # 다양한 형태의 'abstract' 문자열을 찾기 위한 정규식 패턴
    pattern = r'\b[Aa][\s]*[Bb][\s]*[Ss][\s]*[Tt][\s]*[Rr][\s]*[Aa][\s]*[Cc][\s]*[Tt][\s]*[.:]?\b'

    # 정규식을 사용하여 패턴을 제거
    cleaned_text = re.sub(pattern, '', text)

    return cleaned_text.strip()

def find_tilde_number_pattern(text):
    # 문자열의 앞뒤 공백을 제거
    text = text.strip()

    # 문자열이 "~ 숫자 ~" 패턴을 포함하는지 확인
    if len(text) >= 5 and text[0] == '~' and text[-1] == '~':
        middle_part = text[1:-1].strip()  # 틸다 사이의 숫자 부분을 추출하고 공백 제거
        if middle_part.isdigit():  # 숫자인지 확인
            return True
    return False



def is_accepted_date_format(text):
    global months

    # 텍스트가 "Accepted "로 시작하는지 확인
    if not text.startswith("Accepted "):
        return False

    # "Accepted " 이후의 부분을 추출
    rest_of_text = text[len("Accepted "):]

    # 나머지 텍스트를 공백으로 나누기
    parts = rest_of_text.split()

    # parts 리스트가 날짜 형식에 맞는지 확인
    if len(parts) != 4:
        return False

    day = parts[0]
    month = parts[1].strip(',')
    year = parts[2].strip(',')

    # 날짜가 숫자인지 확인
    if not day.isdigit():
        return False

    # 달이 months 배열에 있는지 확인
    if month not in months:
        return False

    # 연도가 숫자인지 확인
    if not year.isdigit():
        return False

    return True



# 함수: PDF 파일의 첫 번째 페이지에서 텍스트를 읽어들이는 함수
def read_pages(file_path):
    try:
        # PDF 파일 열기
        with pdfplumber.open(file_path) as pdf:
            text = ""

            # 첫 번째와 두 번째 페이지가 있는지 확인 후 추출
            for page_number in range(min(3, len(pdf.pages))):  # 페이지가 2개 이상 있는지 확인
                page = pdf.pages[page_number]
                text += page.extract_text() + "\n"

            return text
    except FileNotFoundError:
        print(f"Error: {file_path} 파일을 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


# 함수: PDF 파일의 첫 번째와 두 번째 페이지에서 텍스트를 읽어들이는 함수
def read_pages_with_pymupdf(file_path):
    try:
        # PDF 파일 열기
        pdf_document = fitz.open(file_path)
        text = ""

        # 첫 번째와 두 번째 페이지에서 텍스트 추출
        for page_number in range(min(3, pdf_document.page_count)):  # 페이지 수 확인
            if page_number < len(pdf_document):
                page = pdf_document.load_page(page_number)  # 페이지 인덱스는 0부터 시작
                page_text = page.get_text("text")  # "text" 옵션으로 페이지의 텍스트 추출

                if '...' in page_text and page_number == 0:  # [15].pdf 의 유일한 예외 케이스 때문에 추라
                    pdf_document.close()
                    return False, ''

                text += page_text + "\n"

        pdf_document.close()
        return True, text

    except FileNotFoundError:
        print(f"Error: {file_path} 파일을 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


# 함수: PDF 폴더 내에서 첫 번째 페이지만 읽는 함수
def read_pdf_from_folder(pdf_folder, file_name):
    file_path = os.path.join(pdf_folder, file_name)

    tf, text = read_pages_with_pymupdf(file_path)

    if not tf:
        return read_pages(file_path)

    return text



def should_skip_if_number_and_space(line):
    # 문자열의 길이가 5이고, 앞의 4자리가 숫자, 마지막 자리가 공백인지 확인
    if len(line) == 5 and line[:4].isdigit() and line[4] == ' ':
        return True
    return False


def should_skip_if_number_and_space_3(line):
    # 문자열의 길이가 3이고, 앞의 3자리가 숫자
    if len(line) == 3 and line[:3].isdigit():
        return True
    return False


def should_skip_if_number_and_space_2(line):
    # 문자열의 길이가 5이고, 앞의 4자리가 숫자, 마지막 자리가 공백인지 확인
    if len(line) == 3 and line[0].isdigit() and line[1] == ' ' and line[2].isdigit():
        return True
    return False



def find_capital_dot_space_pattern(text):
    # 문자열 길이가 6 이상일 때만 검사
    for i in range(len(text) - 5):  # 패턴이 6글자이므로 len(text) - 5까지 확인
        if (text[i].isupper() and               # 첫 번째는 대문자
                text[i + 1] == '.' and              # 두 번째는 점
                text[i + 2] == ' ' and              # 세 번째는 공백
                text[i + 3].isupper() and           # 네 번째는 대문자
                text[i + 4] == '.' and              # 다섯 번째는 점
                text[i + 5] == ' '):                # 여섯 번째는 공백
            return True  # 패턴이 발견되면 True 반환
    return False  # 패턴이 없으면 False 반환


def find_capital_dot_pattern(text):
    # 문자열 길이가 4 이상일 때만 검사 (F.V.는 4글자)
    for i in range(len(text) - 3):  # 패턴이 4글자이므로 len(text) - 3까지 확인
        if (text[i].isupper() and       # 첫 번째는 대문자
                text[i + 1] == '.' and  # 두 번째는 점
                text[i + 2].isupper() and  # 세 번째는 대문자
                text[i + 3] == '.'):    # 네 번째는 점
            return True  # 패턴이 발견되면 True 반환
    return False  # 패턴이 없으면 False 반환

def find_capital_dot_pattern_2(text):
    # 문자열 길이가 4 이상일 때만 검사 (F.V.는 4글자)
    for i in range(len(text) - 4):  # 패턴이 4글자이므로 len(text) - 3까지 확인
        if (text[i].isupper() and       # 첫 번째는 대문자
                text[i + 1] == '.' and  # 두 번째는 점
                text[i + 2].isupper() and  # 세 번째는 대문자
                text[i + 3] == '.' and    # 네 번째는 점
                text[i + 4] == ' '):    # 네 번째는 점
            return True  # 패턴이 발견되면 True 반환
    return False  # 패턴이 없으면 False 반환




# [1].pdf [2].pdf
def should_skip_line_with_number_pattern(line):
    # ':' 기준으로 나눈 각 부분을 확인
    parts = line.split(':')
    for part in parts:
        cleaned_part = part.replace(" ", "")  # 모든 공백 제거

        # '-' 또는 '–'를 기준으로 나눠서 숫자 4개 - 숫자 4개 패턴을 찾음
        if '-' in cleaned_part or '–' in cleaned_part:  # 일반 대시('-') 또는 긴 대시('–')를 모두 처리
            left_right = cleaned_part.split('-') if '-' in cleaned_part else cleaned_part.split('–')
            if len(left_right) == 2:
                left, right = left_right

                # 숫자 3개 - 숫자 3개 패턴을 찾음
                if left.isdigit() and right.isdigit() and len(left) == 3 and len(right) == 3:
                    return True
    return False

def find_number_space_number_pattern(text):
    # 문자열의 길이가 3인지 확인하고, 숫자 공백 숫자 패턴인지 확인
    if len(text) == 3 and text[0].isdigit() and text[1] == ' ' and text[2].isdigit():
        return True
    return False


# [15].pdf
# '...' 뒤에 숫자 3개가 있는 경우 건너뜀
def should_skip_line_with_dots_and_numbers(line):
    parts = line.split()
    # '...' 뒤에 숫자 3개가 있는 경우 확인
    for i, part in enumerate(parts):
        if '...' in part and i + 1 < len(parts) and parts[i + 1].isdigit() and len(parts[i + 1]) == 3:
            return True
    return False

def is_four_digit_number(line):
    # 문자열의 길이가 4인지 확인하고, 모두 숫자인지 확인
    if len(line) == 4 and line.isdigit():
        return True
    return False

def find_month_in_text(text):
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    for month in months:
        if month in text:
            return True  # 달이 발견되면 해당 달 이름 반환
    return False  # 달이 없으면 None 반환


# 함수: 텍스트에서 제목 추출
def extract_title_from_text(text_lines, skip_keywords, break_keywords, small_values):
    title = ""
    process_title = True
    research_paper = True

    for line in text_lines:

        # "Cien. Inv. Agr."를 찾을 경우 "research paper"까지 continue
        if "IJCS" in line:
            process_title = False
            continue

        # "research paper"가 나올 때까지 continue
        if not process_title:
            if "Effect of different" in line:
                title += line + "\n"
                process_title = True
            continue

        # "Cien. Inv. Agr."를 찾을 경우 "research paper"까지 continue
        if "Cien. Inv. Agr." in line:
            research_paper = False
            continue

        # "research paper"가 나올 때까지 continue
        if not research_paper:
            if "research paper" in line.lower():
                research_paper = True
            continue

        # skip_keywords 중 하나라도 포함되어 있으면 건너뜀
        if any(skip_keyword in line for skip_keyword in skip_keywords):
            continue

        # '... 공백 숫자 3개' 조건을 만족하는 경우 건너뜀
        if should_skip_line_with_dots_and_numbers(line):
            continue

        if any(small_value == line for small_value in small_values):
            continue

        if should_skip_if_number_and_space(line):
            continue

        if should_skip_line_with_number_pattern(line):
            continue

        if find_number_space_number_pattern(line):
            continue

        if should_skip_if_number_and_space_3(line.strip()):
            continue

        if is_four_digit_number(line):
            continue

        if find_tilde_number_pattern(line):
            continue

        if any(break_keyword in line for break_keyword in break_keywords):
            if '1, ' in line and '1, 4' in line:
                title += line + "\n"
                continue
            break

        if find_capital_dot_pattern_2(line):
            break

        if find_capital_dot_space_pattern(line):
            break


        # 조건을 만족하지 않으면 제목에 라인 추가
        title += line + "\n"

    return title.strip()

# 함수: 텍스트에서 ABSTRACT와 INTRODUCTION 사이의 텍스트 추출
def extract_abstract_from_text(text_lines, skip_keywords, small_values):
    # ABSTRACT와 INTRODUCTION 위치 찾기
    abstract_start_idx = -1
    introduction_start_idx = -1
    abstract_lines = []

    key_words = False
    dataset_link = False

    # 줄에서 ABSTRACT와 INTRODUCTION 위치 찾기
    for idx, line in enumerate(text_lines):

        if 'Dataset link:' in line:
            dataset_link = True
            continue

        if dataset_link and 'a b s t r a c t' not in line:
            continue

        if dataset_link and 'a b s t r a c t' in line:
            abstract_start_idx = idx
            dataset_link = False

        if 'Speciﬁcations Table' in line:
            introduction_start_idx = idx
            break

        if abstract_start_idx == -1 and is_accepted_date_format(line):
            abstract_start_idx = idx + 2

        if "Cien. Inv. Agr." in line:
            key_words = True
            continue

        if "Accepted " in line:
            key_words = True
            continue

        if (abstract_start_idx == -1
                and ('ABSTRACT' in line.upper() or 'A B S T R A C T' in line.upper() or 'a b s t r a c t ' in line)):
            abstract_start_idx = idx

        if 'Medical Science,' in line:
            abstract_start_idx = idx + 1

        if abstract_start_idx != -1 and 'Received ' in line  and 'Received in' not in line and find_month_in_text(line) and 'history:' not in text_lines[idx-1]:
            introduction_start_idx = idx

        if (abstract_start_idx != -1 and introduction_start_idx == -1
                and ('INTRODUCTION' in line.upper() or 'Statement of Novelty' in line or 'Background ' in line or 'INTRODUCCIÓN' in line)):

            if idx == abstract_start_idx + 1:
                continue

            introduction_start_idx = idx
            break


        if (abstract_start_idx != -1 and introduction_start_idx == -1
                and ('Key words' in line) and key_words == True):
            introduction_start_idx = idx + 2
            break


    # ABSTRACT가 존재하고, INTRODUCTION이 그 뒤에 존재할 때
    if abstract_start_idx != -1 and introduction_start_idx != -1 and abstract_start_idx < introduction_start_idx:
        # ABSTRACT 다음 줄부터 INTRODUCTION 전까지 텍스트를 한 줄씩 추가
        for i in range(abstract_start_idx, introduction_start_idx):
            line = text_lines[i].strip()

            # if any(skip_keyword in line for skip_keyword in skip_keywords):
            #     continue

            if any(small_value == line for small_value in small_values):
                continue

            # if should_skip_if_number_and_space_3(line):
            #     continue
            #
            # if should_skip_if_number_and_space_2(line):
            #     continue
            #
            # if should_skip_line_with_number_pattern(line):
            #     continue

            if '_____________________________________________________________________________________________' in line:
                break

            if '____________________________________________________________________________________________' in line:
                break

            # if 'Abbreviations:' in line:
            #     break

            if 'Received:' in line:
                abstract_lines.append('Article history')

            if '* Correspondence' in line:
                break

            abstract_lines.append(line)

        # 추출한 ABSTRACT 텍스트 반환
        return "\n".join(abstract_lines).strip()
    else:
        return ""


def is_accepted_date_format(text):
    global months

    # 텍스트가 "Accepted "로 시작하는지 확인
    if not text.startswith("Accepted "):
        return False

    # "Accepted " 이후의 부분을 추출
    rest_of_text = text[len("Accepted "):]

    # 나머지 텍스트를 공백으로 나누기
    parts = rest_of_text.split()

    # parts 리스트가 날짜 형식에 맞는지 확인
    if len(parts) != 3:
        return False

    day = parts[0]
    month = parts[1].strip(',')
    year = parts[2].strip(',')

    # 날짜가 숫자인지 확인
    if not day.isdigit():
        return False

    # 달이 months 배열에 있는지 확인
    if month not in months:
        return False

    # 연도가 숫자인지 확인
    if not year.isdigit():
        return False

    return True




# 메인 함수
def main():
    # 현재 디렉토리의 pdf 폴더 경로 설정
    # 프로그램이 실행되는 경로에 pdf폴더 안에 pdf파일들을 넣으면 됩니다.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_folder = os.path.join(current_dir, 'pdf')

    # pdf_folder 안에 있는 모든 파일 이름을 확장자 포함해서 배열로 가져오기
    pdf_files = [file for file in os.listdir(pdf_folder) if os.path.isfile(os.path.join(pdf_folder, file))]

    extracted_data = []

    for pdf_file_name in pdf_files:
        # PDF 파일의 첫 페이지 텍스트 읽기
        text = read_pdf_from_folder(pdf_folder, pdf_file_name)

        # 텍스트가 존재하는 경우 줄바꿈 단위로 리스트로 분리
        if text:
            text_lines = text.splitlines()  # 줄바꿈을 기준으로 배열로 분리

            # skip_keywords 정의
            skip_keywords = ['Available online',
                             'www.',
                             'Journal of',
                             'ISSN',
                             'Research Article',
                             'CODEN',
                             'Contents lists available at',
                             'Food Chemistry',
                             'Article no.',
                             'Journal International',
                             'author:',
                             'E-mail:',
                             '_____________________________________________________________________________________________________',
                             '_____________________________________________________________________________________________',
                             '______',
                             'DOI:',
                             'GLOBAL JOURNAL OF',
                             'https:',
                             'http:',
                             'Vol.',
                             'Vol ',
                             'ORIGINAL PAPER',
                             '*	 ',
                             '@gmail.com',
                             'Graphical Abstract',
                             'Extended author information available',
                             'Nomico Journal',
                             'Education Publishing',
                             'Science and Biotechnology',
                             'Global Science Books',
                             'Research Journal',
                             'Corresponding author',
                             'Email:',
                             'DOI',
                             'All Rights Reserved',
                             'Scientiﬁc African',
                             'Pharmaceutical Biology',
                             'Full Terms & Conditions of access',
                             'ARTÍCULO ORIGINAL',
                             'Academic Publishers.',
                             'Mycopathologia',
                             'A multifaceted review journal',
                             'CARICA PAPAYA ON PITUITARY–GONADAL AXIS',
                             ', Ltd.',
                             '. Res.',
                             'PHYTOTHERAPY RESEARCH',
                             'SHORT COMMUNICATION',
                             '© Universiti ',
                             'E-mail addresses:',
                             'Article history:',
                             'SCIENCE & TECHNOLOGY',
                             '& Technol.',
                             'ARTICLE INFO',
                             '(Chia Chay Tay)',
                             'Published:',
                             'Accepted:',
                             'Received:',
                             'Research ',
                             'Review ',
                             'RESEARCH ARTICLE',
                             'Open Access',
                             'Reports |',
                             'This is an open access',
                             'article under the CC BY',
                             'NLM ID:',
                             'Data in Brief',
                             'Data Article',
                             'Science and Technology',
                             'Published by'
                             ]

            # break_keywords 정의
            break_keywords = ['* ,',
                              '*,',
                              ',⁎',
                              'Article · ',
                              '1 · ',
                              '2 · ',
                              ',1,',
                              ',2,',
                              ',3,',
                              '* • ',
                              '∗,',
                              'CITATIONS',
                              'I,',
                              'II,',
                              'III,',
                              '1* ',
                              '* and',
                              ' A, ',
                              '1, ',
                              ', and',
                              ' Q. ',
                              'Natural Science · '
                              ]

            small_values = ["T", " ", "",
                            "1","2","3","4","5","6","7","8","9",
                            "1 ","2 ","3 ","4 ","5 ","6 ","7 ","8 ","9 "
                            ]

            # 제목 추출
            title = extract_title_from_text(text_lines, skip_keywords, break_keywords, small_values)

            # 추출한 제목 출력

            # ABSTRACT 추출
            abstract = extract_abstract_from_text(text_lines, skip_keywords, small_values)

            # 추출한 Abstract 출력
            # 데이터를 객체 배열에 추가
            cleaned_abstract = clean_abstract(abstract)

            obj = {
                "file_name": pdf_file_name,
                "title": title,
                "abstract": cleaned_abstract if cleaned_abstract else "ABSTRACT 또는 INTRODUCTION을 찾을 수 없습니다."
            }

            print(f"=============================================================================")
            print(f"file_name : {pdf_file_name}")
            print(f"title : {title}")
            print(f"abstract : {cleaned_abstract}")
            print(f"=============================================================================")

            extracted_data.append(obj)


    # DataFrame 생성 및 엑셀 파일로 저장
    df = pd.DataFrame(extracted_data)
    output_file = os.path.join(current_dir, 'extracted_data.xlsx')
    df.to_excel(output_file, index=False)

    print(f"데이터가 {output_file}에 저장되었습니다.")

if __name__ == "__main__":
    main()
