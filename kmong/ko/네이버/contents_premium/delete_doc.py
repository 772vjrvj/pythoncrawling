from docx import Document

def delete_paragraph(paragraph):
    """문단 삭제 함수"""
    p_element = paragraph._element
    p_element.getparent().remove(p_element)
    p_element._p = p_element._element = None

def delete_text_between_inplace(doc_path, start_text, end_text):
    # 문서 열기
    doc = Document(doc_path)

    # 삭제 상태를 추적하는 변수
    deleting = False

    paragraphs_to_remove = []

    for paragraph in doc.paragraphs:
        if not deleting:
            # 시작 문구 발견 시 삭제 시작
            if start_text in paragraph.text:
                deleting = True
                paragraphs_to_remove.append(paragraph)  # 해당 문단도 삭제 대상에 포함
        else:
            # 삭제 상태
            paragraphs_to_remove.append(paragraph)
            # 끝 문구 발견 시 삭제 종료
            if end_text in paragraph.text:
                deleting = False

    # 삭제 대상 문단 제거
    for paragraph in paragraphs_to_remove:
        delete_paragraph(paragraph)

    # 기존 파일 덮어쓰기
    doc.save(doc_path)
    print(f"Updated document saved in-place: {doc_path}")

# 사용 예제
delete_text_between_inplace(
    doc_path="비플랜 테스트.docx",
    start_text="해당 콘텐츠는 프리미엄 구독자",  # 삭제 시작 문구
    end_text="NAVER Corp."      # 삭제 끝 문구
)
