import os
import win32com.client


def paste_to_docx_with_format():
    # 실행 경로를 기준으로 파일 저장 경로 생성
    current_path = os.getcwd()  # 현재 실행 경로 가져오기
    output_path = os.path.join(current_path, "output2.docx")  # 파일 경로 설정

    # Word 애플리케이션 시작
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False  # Word 창 숨기기

    # 새 문서 생성
    doc = word.Documents.Add()

    # 클립보드에서 붙여넣기
    selection = word.Selection
    try:
        # 기본 붙여넣기 (서식 포함)
        wdPasteDefault = 0  # 하드코딩된 상수 값
        selection.PasteAndFormat(wdPasteDefault)
    except Exception as e:
        print(f"Error with PasteAndFormat: {e}")
        try:
            selection.Paste()  # 일반 붙여넣기
        except Exception as paste_error:
            print(f"Error with Paste: {paste_error}")

    # 문서 저장
    doc.SaveAs(output_path)
    doc.Close()
    word.Quit()
    print(f"Document saved to: {output_path}")

# 사용 예제
paste_to_docx_with_format()
