from docx import Document

def delete_paragraph(paragraph):
    """문단 삭제 함수"""
    p_element = paragraph._element
    p_element.getparent().remove(p_element)
    p_element._p = p_element._element = None

def delete_text_between_multiple(doc_path, delete_ranges):
    # 문서 열기
    doc = Document(doc_path)

    paragraphs_to_remove = []
    deleting = False
    current_start = None
    current_end = None

    for paragraph in doc.paragraphs:
        if not deleting:
            # 각 구간의 시작 문구를 확인
            for start_text, end_text in delete_ranges:
                if start_text in paragraph.text:
                    deleting = True
                    current_start = start_text
                    current_end = end_text
                    paragraphs_to_remove.append(paragraph)
                    break  # 시작 문구 확인되면 다음 문구로 넘어감
        else:
            # 삭제 상태인 경우 현재 구간 처리
            paragraphs_to_remove.append(paragraph)
            if current_end in paragraph.text:
                deleting = False  # 현재 구간 종료
                current_start = None
                current_end = None

    # 삭제 대상 문단 제거
    for paragraph in paragraphs_to_remove:
        delete_paragraph(paragraph)

    # 기존 파일 덮어쓰기
    doc.save(doc_path)
    print(f"Updated document saved in-place: {doc_path}")

# 사용 예제
delete_text_between_multiple(
    doc_path="비플랜 테스트.docx",
    delete_ranges=[
        ("본문 바로가기", "해외 드랍쉬핑 실전판매의 정석"),  # 첫 번째 구간
        ("해당 콘텐츠는 프리미엄 구독자", "NAVER Corp.")  # 두 번째 구간
    ]
)
