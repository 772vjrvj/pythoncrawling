# -*- coding: utf-8 -*-
# contipro 인보이스: Invoice No. / Date of issue / Total price(EUR) 추출
import os, re, datetime
import pdfplumber, pytesseract, fitz  # pip install pdfplumber pymupdf pytesseract pillow
from PIL import Image
from io import BytesIO

# --- Tesseract 경로 고정(설치·배포 모두 커버) ---
_TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.isfile(_TESS):
    pytesseract.pytesseract.tesseract_cmd = _TESS
else:
    _vend = os.path.join(os.getcwd(), "vendor", "bin", "tesseract", "tesseract.exe")
    if os.path.isfile(_vend):
        pytesseract.pytesseract.tesseract_cmd = _vend

def extract_text(pdf_path):
    # 1) 텍스트 PDF 우선
    try:
        with pdfplumber.open(pdf_path) as pdf:
            t = "\n".join((p.extract_text() or "") for p in pdf.pages)
            if len(t.strip()) > 40:
                return t
    except Exception as e:
        pass
    # 2) 스캔 PDF → 300dpi 렌더 후 OCR (첫 페이지만)
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=300)
    img = Image.open(BytesIO(pix.tobytes("png")))
    try:
        return pytesseract.image_to_string(img, lang="eng+kor") or ""
    except Exception:
        return pytesseract.image_to_string(img, lang="eng") or ""

def parse_contipro(s):
    s = re.sub(r"[\u00A0\s]+", " ", s)
    # Invoice No. (상단: INVOICE - TAX CERTIFICATE 58001057)
    m_inv = re.search(r"INVOICE\s*[-–]?\s*TAX\s*CERTIFICATE\s*([A-Z0-9-]+)", s, re.I)
    # Date of issue (OCR 오인식 O→0, 구분자 . 또는 - 허용)
    m_dt  = re.search(r"Date\s*of\s*issue\s*([0-3O]?\d[.\-][01O]?\d[.\-]\d{4})", s, re.I)
    # Total price EUR (정/역순 모두 대응)
    m_amt = re.search(r"Total\s*price\s*(?:EUR|€)\s*([0-9][\d\s]*[.,]\d{2})", s, re.I) \
            or re.search(r"(?:EUR|€)\s*([0-9][\d\s]*[.,]\d{2})\s*Total\s*price", s, re.I)
    if not (m_inv and m_dt and m_amt): return None

    inv = m_inv.group(1).strip()
    d = m_dt.group(1).replace("O", "0").replace("o", "0")
    if "-" in d:
        iso = datetime.datetime.strptime(d, "%d-%m-%Y").date().isoformat()
    else:
        iso = datetime.datetime.strptime(d, "%d.%m.%Y").date().isoformat()
    amount = float(m_amt.group(1).replace(" ", "").replace(",", "."))
    return {"Invoice No.": inv, "Date": iso, "Amount": amount}

if __name__ == "__main__":
    base = os.path.join(os.getcwd(), "수입 선적서류", "contipro")
    if not os.path.isdir(base):
        print("폴더 없음:", base); raise SystemExit(1)
    for name in sorted(os.listdir(base)):
        if name.lower().endswith(".pdf"):

            path = os.path.join(base, name)
            try:
                obj = parse_contipro(extract_text(path))
                print(f"[{name}] ->", obj if obj else "필드 미검출")
            except Exception as e:
                print(f"[{name}] -> 에러:", (e and getattr(e, "message", None)) or str(e))
