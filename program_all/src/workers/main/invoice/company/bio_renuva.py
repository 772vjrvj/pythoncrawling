# -*- coding: utf-8 -*-
"""
BioRenuva 인보이스 파서 (3필드, Amount는 숫자만)
- Invoice no. / Invoice date(YYYY-MM-DD) / Amount(숫자만)
- 기본 폴더: 수입 선적서류/BioRenuva
"""

import os, re

class BioRenuvaInvoiceParser:
    def __init__(self, folder="수입 선적서류/BioRenuva", log_func=None):
        self.folder = folder
        self.log_func = log_func  # === 신규 ===

    # ---------- 내부 공용 로그 ----------
    def _log(self, msg):
        try:
            if self.log_func:
                self.log_func(msg)
            else:
                print(msg)
        except:
            print(msg)

    # ---------- PDF 텍스트 ----------
    def read_text(self, pdf_path):
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception:
            from PyPDF2 import PdfReader  # type: ignore
        r = PdfReader(pdf_path)
        return "\n".join((p.extract_text() or "") for p in getattr(r, "pages", []))

    # ---------- 유틸 ----------
    def _ymd(self, s):
        s = (s or "").strip()
        m = re.match(r"^(\d{4})[./-](\d{2})[./-](\d{2})$", s)
        if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        m = re.match(r"^(\d{2})[./-](\d{2})[./-](\d{4})$", s)      # MM/DD/YYYY
        if m: return f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
        m = re.match(r"^(\d{2})[.](\d{2})[.](\d{4})$", s)         # DD.MM.YYYY
        if m: return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        return None

    def _clean_amount(self, num):
        if not num: return None
        t = re.sub(r"[^\d,.\-]", "", num.strip()).replace(",", "")
        try: return float(t)
        except: return None

    # ---------- 파서 ----------
    def parse_text(self, raw):
        u = re.sub(r"[ \t]+", " ", raw)
        flat = re.sub(r"\s+", " ", u).strip()

        # Invoice no.
        invoice_no = None
        for pat in (
                r"Invoice\s*no\.?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",
                r"Invoice\s*number\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",
                r"Invoice\s*#\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",
        ):
            m = re.search(pat, u, re.I)
            if m: invoice_no = m.group(1).strip(); break

        # Invoice date
        invoice_date = None
        m = re.search(
            r"Invoice\s*date\s*[:\-]?\s*("
            r"[0-9]{2}[./-][0-9]{2}[./-][0-9]{4}|"
            r"[0-9]{4}[./-][0-9]{2}[./-][0-9]{2}|"
            r"[0-9]{2}[.][0-9]{2}[.][0-9]{4}"
            r")", u, re.I
        )
        if m: invoice_date = self._ymd(m.group(1))

        # Amount(총액 키워드 근처의 최대값 택1)
        cands = []
        for m in re.finditer(
                r"(?<![A-Za-z])(Grand\s+Total|Total(?:\s*Amount)?|Total\s+Due)(?![A-Za-z])\s*[:\-]?\s*([A-Z]{3})\s*([$€£]?\s*[0-9][0-9,\.]+)",
                flat, re.I
        ):
            v = self._clean_amount(m.group(3)); cands.append((v, m.start()))
        for m in re.finditer(
                r"(?<![A-Za-z])(Grand\s+Total|Total(?:\s*Amount)?|Total\s+Due)(?![A-Za-z])\s*[:\-]?\s*([$€£])\s*([0-9][0-9,\.]+)",
                flat, re.I
        ):
            v = self._clean_amount(m.group(3)); cands.append((v, m.start()))
        for m in re.finditer(
                r"(?<![A-Za-z])(Grand\s+Total|Total(?:\s*Amount)?|Total\s+Due)(?![A-Za-z])\s*[:\-]?\s*([0-9][0-9,\.]+)",
                flat, re.I
        ):
            v = self._clean_amount(m.group(2)); cands.append((v, m.start()))
        amount = max(cands, key=lambda x:(x[0], x[1]))[0] if cands else None

        return {"invoice_no": invoice_no, "invoice_date": invoice_date, "amount": amount}

    def parse_pdf(self, pdf_path):
        return self.parse_text(self.read_text(pdf_path))

    # ---------- 폴더 실행(내부 처리만, 리턴 없음) ----------
    def run(self, folder=None):
        folder = folder or self.folder
        for fname in os.listdir(folder):
            if not fname.lower().endswith(".pdf"):
                continue
            path = os.path.join(folder, fname)
            try:
                d = self.parse_pdf(path)
                self._log(f"✅ {fname} → No={d.get('invoice_no')}, Date={d.get('invoice_date')}, Amount={d.get('amount')}")
            except Exception as e:
                self._log(f"❌ {fname} 파싱 실패: {e}")
