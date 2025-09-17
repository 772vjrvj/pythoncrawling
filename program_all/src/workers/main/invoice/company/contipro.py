# -*- coding: utf-8 -*-
"""
CONTIPRO 인보이스 파서 (3필드 고정)
- Invoice No. / Date of issue(YYYY-MM-DD) / Total price(EUR → 숫자)
- 기본 폴더: 수입 선적서류/contipro
- 동작: run()은 내부 로그 출력만 수행(리턴 없음)
"""

import os, re, datetime
import pdfplumber, pytesseract, fitz
from PIL import Image
from io import BytesIO

class ContiproInvoiceParser:
    def __init__(self, folder=None, log_func=None):
        self.folder = folder or os.path.join(os.getcwd(), "수입 선적서류", "contipro")
        self.log_func = log_func
        # --- Tesseract 경로 고정(설치·배포 모두 커버) ---
        _tess = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.isfile(_tess):
            pytesseract.pytesseract.tesseract_cmd = _tess
        else:
            _vend = os.path.join(os.getcwd(), "vendor", "bin", "tesseract", "tesseract.exe")
            if os.path.isfile(_vend):
                pytesseract.pytesseract.tesseract_cmd = _vend

    # ---------- 내부 공용 로그 ----------
    def _log(self, msg):
        try:
            if self.log_func: self.log_func(msg)
            else: print(msg)
        except: print(msg)

    # ---------- PDF → 텍스트 ----------
    def extract_text(self, pdf_path):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                t = "\n".join((p.extract_text() or "") for p in pdf.pages)
                if len((t or "").strip()) > 40:
                    return t
        except Exception:
            pass
        # 스캔 PDF → 300dpi 렌더 후 OCR(첫 페이지만)
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=300)
        img = Image.open(BytesIO(pix.tobytes("png")))
        try:
            return pytesseract.image_to_string(img, lang="eng+kor") or ""
        except Exception:
            return pytesseract.image_to_string(img, lang="eng") or ""

    # ---------- 파서 ----------
    def parse_text(self, s):
        s = re.sub(r"[\u00A0\s]+", " ", s or "")
        # Invoice No. (상단: INVOICE - TAX CERTIFICATE 58001057)
        m_inv = re.search(r"INVOICE\s*[-–]?\s*TAX\s*CERTIFICATE\s*([A-Z0-9-]+)", s, re.I)
        # Date of issue (OCR 오인식 O→0, 구분자 . 또는 - 허용)
        m_dt  = re.search(r"Date\s*of\s*issue\s*([0-3O]?\d[.\-][01O]?\d[.\-]\d{4})", s, re.I)
        # Total price EUR (정/역순 모두 대응)
        m_amt = re.search(r"Total\s*price\s*(?:EUR|€)\s*([0-9][\d\s]*[.,]\d{2})", s, re.I) \
                or re.search(r"(?:EUR|€)\s*([0-9][\d\s]*[.,]\d{2})\s*Total\s*price", s, re.I)
        if not (m_inv and m_dt and m_amt):
            return None

        inv = (m_inv.group(1) or "").strip()

        d = (m_dt.group(1) or "").replace("O", "0").replace("o", "0")
        if "-" in d:
            iso = datetime.datetime.strptime(d, "%d-%m-%Y").date().isoformat()
        else:
            iso = datetime.datetime.strptime(d, "%d.%m.%Y").date().isoformat()

        amount = float((m_amt.group(1) or "").replace(" ", "").replace(",", "."))

        return {"Invoice No.": inv, "Date": iso, "Amount": amount}

    def parse_pdf(self, pdf_path):
        return self.parse_text(self.extract_text(pdf_path))

    # ---------- 폴더 실행(내부 처리만, 리턴 없음) ----------
    def run(self, folder=None):
        folder = folder or self.folder
        if not os.path.isdir(folder):
            self._log(f"폴더 없음: {folder}")
            return
        for name in sorted(os.listdir(folder)):
            if not name.lower().endswith(".pdf"): continue
            path = os.path.join(folder, name)
            try:
                obj = self.parse_pdf(path)
                if obj:
                    self._log(f"✅ {name} → No={obj['Invoice No.']}, Date={obj['Date']}, Amount={obj['Amount']}")
                else:
                    self._log(f"⚠️ {name} → 필드 미검출")
            except Exception as e:
                self._log(f"❌ {name} → 에러: {(getattr(e,'message',None) or str(e))}")

