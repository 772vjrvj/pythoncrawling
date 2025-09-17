# -*- coding: utf-8 -*-
"""
HALLSTAR ITALY & US 인보이스 파서
- 추출: Invoice No. / Date(YYYY-MM-DD) / Total Amount Due
- 기본 경로: 프로그램 시작경로/수입 선적서류/HALLSTAR ITALY & US
- 출력만 하고 리턴 없음
"""

import os, re, datetime

class HallstarInvoiceParser:
    def __init__(self, folder=None, log_func=None):
        self.folder = folder or os.path.join(os.getcwd(), "수입 선적서류", "HALLSTAR ITALY & US")
        self.log_func = log_func

    # ---------- 내부 로그 ----------
    def _log(self, msg):
        try:
            if self.log_func: self.log_func(msg)
            else: print(msg)
        except: print(msg)

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

        # 케이스1: "Invoice No. / Date / Internal No.: INV / 17.07.2025 / INT-123"
        m = re.search(
            r"Invoice\s*No\.\s*/\s*Date\s*/\s*Internal\s*No\.\s*:\s*([^/]+?)\s*/\s*([0-3]?\d\.[01]?\d\.\d{4}).*?/\s*([A-Za-z0-9-]+)",
            s, re.I
        )
        # 케이스2: "Invoice No.: INV-001  ...  Date: 17.07.2025"
        if not m:
            m = re.search(
                r"Invoice\s*No\.?\s*:\s*([^\s/]+).*?Date\s*:\s*([0-3]?\d\.[01]?\d\.\d{4})",
                s, re.I
            )
        if not m: return None

        inv_no = m.group(1).strip()
        dstr = m.group(2).strip()
        iso = datetime.datetime.strptime(dstr, "%d.%m.%Y").date().isoformat()

        # 금액: "Total Amount Due 52,724.59 USD" / "Total Amount Due USD 52,724.59"
        m_amt = re.search(r"Total\s*Amount\s*Due\s*([0-9][\d,]*\.\d{2})(?:\s*[A-Z]{3}|€|$)?", s, re.I) \
                or re.search(r"Total\s*Amount\s*Due\s*(?:[A-Z]{3}|€|$)\s*([0-9][\d,]*\.\d{2})", s, re.I)
        if not m_amt: return None
        amount = float(m_amt.group(1).replace(",", ""))

        return {"Invoice No.": inv_no, "Date": iso, "Amount": amount}

    def parse_pdf(self, pdf_path):
        return self.parse_text(self.read_text(pdf_path))

    # ---------- 폴더 실행 ----------
    def run(self, folder=None):
        folder = folder or self.folder
        if not os.path.isdir(folder):
            self._log(f"폴더를 찾을 수 없습니다: {folder}")
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

# (외부 사용 예)
# HallstarInvoiceParser(log_func=self.log_signal_func).run()
