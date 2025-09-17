# -*- coding: utf-8 -*-
"""
Selco 인보이스 파서 (폴더 일괄)
- 추출 필드 예: Document Number/Date, PO No/Date, Incoterms, Terms of payment,
             Subtotal, Tax, Total(값/통화), Parties 블록, 1개 라인아이템 요약
- 기본 경로: 프로그램 시작경로/수입 선적서류/Selco
- run()은 내부 로그만 출력하고 리턴 없음
"""

import os, re

class SelcoInvoiceParser:
    def __init__(self, folder=None, log_func=None):
        self.folder = folder or os.path.join(os.getcwd(), "수입 선적서류", "Selco")
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

    # ---------- 유틸 ----------
    def _num(self, s):
        if not s: return None
        t = s.strip().replace(" ", "")
        if re.search(r"\d\.\d{3}(?:\.\d{3})*,\d{2}$", t):   # 1.234,56
            t = t.replace(".", "").replace(",", ".")
        elif re.search(r"\d,\d{3}(?:,\d{3})*\.\d{2}$", t): # 1,234.56
            t = t.replace(",", "")
        elif re.search(r"^\d[\d,\.]*$", t):
            t = t.replace(",", "")
        try: return float(t)
        except: return None

    def _ymd(self, s):
        s = (s or "").strip()
        m = re.match(r"(\d{4})[./-](\d{2})[./-](\d{2})$", s)
        if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        m = re.match(r"(\d{2})[./-](\d{2})[./-](\d{4})$", s)
        if m: return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        return None

    # ---------- 파서 ----------
    def parse_text(self, raw):
        u = re.sub(r"[ \t]+", " ", raw or "")

        m = re.search(r"Document Number\s+([A-Za-z0-9\-]+)", u, re.I)
        document_number = m.group(1) if m else None

        m = re.search(r"Document Date\s+([0-9./-]{10})", u, re.I)
        document_date = self._ymd(m.group(1)) if m else None

        m = re.search(r"PO No\.\s*([A-Za-z0-9\-\/]+)", u, re.I)
        po_no = m.group(1) if m else None
        m = re.search(r"PO Date\s*([0-9./-]{8,10})", u, re.I)
        po_date = self._ymd(m.group(1)) if m else None

        m = re.search(r"Incoterms\s+([A-Z]{3}(?:[^\n]+)?)", u, re.I)
        incoterms = m.group(1).strip() if m else None

        m = re.search(r"Terms of payment\s+([^\n]+)", raw or "", re.I)
        terms_of_payment = m.group(1).strip() if m else None

        total_value = total_currency = None
        m = re.search(r"Total Amount\s+([0-9.,]+)\s+([A-Z]{3})", u, re.I)
        if m:
            total_value, total_currency = self._num(m.group(1)), m.group(2)
        else:
            m = re.search(r"Total Amount\s+([A-Z]{3})\s+([0-9.,]+)", u, re.I)
            if m:
                total_currency, total_value = m.group(1), self._num(m.group(2))

        m = re.search(r"Subtotal before VAT\s+([0-9.,]+)\s+[A-Z]{3}", u, re.I)
        subtotal_value = self._num(m.group(1)) if m else None

        m = re.search(r"(?:Taxable|Tax)[^\n]*\s+([0-9.,]+)\s+[A-Z]{3}", u, re.I)
        tax_value = self._num(m.group(1)) if m else None

        buyer_block = None
        m = re.search(r"HanaCare Co\., Ltd\.[\s\S]+?South Korea", raw or "")
        if m: buyer_block = re.sub(r"\n+", " / ", m.group(0)).strip()

        consignee_block = None
        m = re.search(r"Goods Recipient\s+([\s\S]+?)\n(?:Document Number|Ref\.Order|PO No\.)", raw or "", re.I)
        if m: consignee_block = re.sub(r"\n+", " / ", m.group(1)).strip()

        seller_block = None
        m = re.search(r"Selco[\s\S]+?Germany", raw or "", re.I)
        if m: seller_block = re.sub(r"\n+", " / ", m.group(0)).strip()

        items = []
        m = re.search(r"Material/Description[^\n]*\n([^\n]+)", raw or "", re.I)
        if m:
            line = " ".join(m.group(1).split())
            m_code = re.match(r"([A-Z0-9\-\.]+)", line)
            material = m_code.group(1) if m_code else None
            m_amt = re.search(r"([0-9.,]+)\s+([A-Z]{3})\s*$", line)
            amount_value = self._num(m_amt.group(1)) if m_amt else None
            amount_currency = m_amt.group(2) if m_amt else None
            items.append({"material": material, "amount": amount_value, "currency": amount_currency, "raw": line})

        return {
            "vendor": "Selco",
            "document_number": document_number,
            "document_date": document_date,
            "po_no": po_no,
            "po_date": po_date,
            "incoterms": incoterms,
            "terms_of_payment": terms_of_payment,
            "subtotal_value": subtotal_value,
            "tax_value": tax_value,
            "total_amount_value": total_value,
            "total_amount_currency": total_currency,
            "buyer_block": buyer_block,
            "consignee_block": consignee_block,
            "seller_block": seller_block,
            "items": items,
        }

    def parse_pdf(self, pdf_path):
        return self.parse_text(self.read_text(pdf_path))

    # ---------- 폴더 실행(로그 출력, 리턴 없음) ----------
    def run(self, folder=None):
        folder = folder or self.folder
        if not os.path.isdir(folder):
            self._log(f"폴더 없음: {folder}"); return
        for fname in sorted(os.listdir(folder)):
            if not fname.lower().endswith(".pdf"): continue
            path = os.path.join(folder, fname)
            try:
                d = self.parse_pdf(path)
                self._log(f"✅ {fname} → DocNo={d.get('document_number')}, Total={d.get('total_amount_value')} {d.get('total_amount_currency')}, Date={d.get('document_date')}")
            except Exception as e:
                self._log(f"❌ {fname} 파싱 실패: {(getattr(e,'message',None) or str(e))}")
