# -*- coding: utf-8 -*-
"""
Lignopure 인보이스 파서
- 추출: Invoice No. / Date(YYYY-MM-DD) / TOTAL(incl. VAT) € → 숫자
- 기본 경로: 프로그램 시작경로/수입 선적서류/Lignopure
- 출력만 하고 리턴 없음
"""

import os, re, datetime

class LignopureInvoiceParser:
    def __init__(self, folder=None, log_func=None):
        self.folder = folder or os.path.join(os.getcwd(), "수입 선적서류", "Lignopure")
        self.log_func = log_func

    # ---------- 내부 로그 ----------
    def _log(self, msg):
        try:
            if self.log_func: self.log_func(msg)
            else: print(msg)
        except:
            print(msg)

    # ---------- PDF → 텍스트 ----------
    def read_text(self, pdf_path):
        try:
            from pypdf import PdfReader
        except Exception:
            from PyPDF2 import PdfReader
        r = PdfReader(pdf_path)
        return "\n".join((p.extract_text() or "") for p in getattr(r, "pages", []))

    # ---------- 파서 ----------
    def parse_text(self, raw):
        s = re.sub(r"[\u00A0\s]+", " ", raw or "")

        m_inv = re.search(r"\bInvoice\s+([A-Z0-9-]+)", s, re.I)
        m_dt  = re.search(r"(?:Date\s*(?:of\s*(?:issue|invoice))?\s*[:\-]?\s*)([0-3]?\d\.[01]?\d\.\d{4})", s, re.I) \
                or re.search(r"\b([0-3]?\d\.[01]?\d\.\d{4})\b", s)
        m_amt = re.search(r"TOTAL\s*\((?:inkl|incl)\.?\s*(?:MwSt|VAT)\.?\)\s*([0-9][\d\s.,]*)\s*€", s, re.I) \
                or re.search(r"€\s*([0-9][\d\s.,]*)\s*TOTAL\s*\((?:inkl|incl)\.?\s*(?:MwSt|VAT)\.?\)", s, re.I)
        if not (m_inv and m_dt and m_amt): return None

        inv = m_inv.group(1).strip()
        iso = datetime.datetime.strptime(m_dt.group(1), "%d.%m.%Y").date().isoformat()

        val = m_amt.group(1).strip().replace(" ", "")
        if "," in val and "." in val: val = val.replace(".", "").replace(",", ".")
        elif "," in val: val = val.replace(",", ".")
        amount = f"{float(val):.2f}"

        return {"Invoice No.": inv, "Date": iso, "Amount": amount}

    def parse_pdf(self, pdf_path):
        return self.parse_text(self.read_text(pdf_path))

    # ---------- 폴더 실행 ----------
    def run(self, folder=None):
        folder = folder or self.folder
        if not os.path.isdir(folder):
            self._log(f"폴더 없음: {folder}"); return
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

# (외부 사용 예)
# from src.workers.main.invoice.company.lignopure import LignopureInvoiceParser
# LignopureInvoiceParser(log_func=self.log_signal_func).run()
