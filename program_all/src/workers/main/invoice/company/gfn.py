# -*- coding: utf-8 -*-
"""
GFN 인보이스 파서
- 추출: Document Number / Document Date / Total Amount(EUR)
- 경로 기본값: 프로그램 시작경로/수입 선적서류/GFN
- 출력만 하고 리턴 없음
"""

import os, re

class GfnInvoiceParser:
    def __init__(self, folder=None, log_func=None):
        self.folder = folder or os.path.join(os.getcwd(), "수입 선적서류", "GFN")
        self.log_func = log_func

    # ---------- 내부 로그 ----------
    def _log(self, msg):
        try:
            if self.log_func: self.log_func(msg)
            else: print(msg)
        except:
            print(msg)

    # ---------- PDF 텍스트 ----------
    def read_text(self, pdf_path):
        try:
            from pypdf import PdfReader
        except Exception:
            from PyPDF2 import PdfReader
        r = PdfReader(pdf_path)
        return "\n".join((p.extract_text() or "") for p in getattr(r, "pages", []))

    # ---------- 파서 ----------
    def parse_text(self, raw):
        if not raw: return None
        s = raw.replace("\u00A0", " ")
        s = re.sub(r"\s+", " ", s).strip()

        # Document Number
        m_num = re.search(r"\bDocument\s*Number\s*([A-Z0-9-]+)\b", s, re.I)
        # Document Date
        m_dt  = re.search(r"\bDocument\s*Date\s*([12]\d{3}\.[01]?\d\.[0-3]?\d)\b", s, re.I)
        if not (m_num and m_dt): return None

        inv = m_num.group(1).strip()
        dstr = m_dt.group(1).strip()
        y, m, d = re.match(r"(\d{4})\.([01]?\d)\.([0-3]?\d)", dstr).groups()
        iso = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

        # Total Amount
        m_amt = re.search(r"\bTotal\s*Amount\s*([0-9][\d,]*\.\d{2})\s*(?:EUR|€)\b", s, re.I) \
                or re.search(r"\bTotal\s*Amount\s*(?:EUR|€)\s*([0-9][\d,]*\.\d{2})\b", s, re.I)
        if not m_amt: return None

        val = m_amt.group(1).replace(",", "")
        amount = f"{float(val):.2f}"

        return {"Invoice No.": inv, "Date": iso, "Amount": amount}

    def parse_pdf(self, pdf_path):
        return self.parse_text(self.read_text(pdf_path))

    # ---------- 폴더 실행 ----------
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
                self._log(f"❌ {name} → 에러: {str(e)}")

# 외부 사용 예:
# GfnInvoiceParser(log_func=self.log_signal_func).run()
