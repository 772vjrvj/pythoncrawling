import os
import json
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Pt
from docx.enum.text import WD_BREAK  # 추가

# 송창록.json 파일 읽기
file_path = os.path.join(os.getcwd(), "송창록.json")
with open(file_path, "r", encoding="utf-8") as json_file:
    data = json.load(json_file)

# 결과 리스트 (JSON 데이터를 리스트 형태로 변환)
records = data if isinstance(data, list) else [data]

# Word 문서를 100개씩 나눠 저장
chunk_size = 100
for i in range(0, len(records), chunk_size):
    doc = Document()
    chunk = records[i:i + chunk_size]

    for record in chunk:
        title = record.get("제목", "")
        content = record.get("내용", "")

        # 제목 추가
        title_paragraph = doc.add_paragraph()
        title_run = title_paragraph.add_run(title)
        title_run.bold = True
        title_run.font.size = Pt(14)
        title_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # 내용 추가
        doc.add_paragraph(content)

        # 페이지 나누기
        page_break = doc.add_paragraph()
        page_break._element.getparent().remove(page_break._element)
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)  # Ctrl+Enter

    # Word 문서 저장
    output_path = os.path.join(os.getcwd(), f"송창록_결과_{i // chunk_size + 1}.docx")
    doc.save(output_path)
    print(f"Word 문서가 생성되었습니다: {output_path}")
