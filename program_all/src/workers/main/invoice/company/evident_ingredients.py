# -*- coding: utf-8 -*-
"""
Evident Ingredients 인보이스 파서 (3필드)
- 경로 기본값: 프로그램 시작경로/수입 선적서류/Evident ingredients
- 출력: invoice_date, amount, invoice_no 만 로그로 출력 (리턴 없음)
"""

import os, re

class EvidentInvoiceParser:
    def __init__(self, folder=None, log_func=None):
        self.folder = folder or os.path.join(os.getcwd(), "수입 선적서류", "Evident ingredients")
        self.log_func = log_func

    # ---------- 내부 로그 ----------
    def _log(self, msg):
        try:
            if self.log_func: self.log_func(msg)
            else: print(msg)
        except:
            print(msg)

    # ---------- PDF 읽기 ----------
    def read_text(self, pdf_path):
        try:
            from pypdf import PdfReader
        except Exception:
            from PyPDF2 import PdfReader
        r = PdfReader(pdf_path)
        return "\n".join((p.extract_text() or "") for p in getattr(r, "pages", []))

    # ---------- 유틸 ----------
    def normalize_date(self, d):
        if not d: return None
        m = re.match(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", d.strip())
        if not m: return None
        dd, mm, yy = m.groups()
        yy = ("20" + yy) if len(yy) == 2 else yy
        return f"{yy}-{int(mm):02d}-{int(dd):02d}"

    def normalize_amount(self, s):
        if not s: return None
        s = re.sub(r"^[A-Z]{3}\s+", "", s.strip())  # "EUR " 등 제거
        s = s.replace(".", "").replace(",", ".")
        try: return float(s)
        except: return None

    # ---------- 파서 ----------
    def parse_text(self, text):
        no, raw_date, amount = None, None, None

        m = re.search(r"\bInvoice\s+([A-Z0-9\-]+)", text, re.I)
        if m: no = m.group(1).strip()

        # Document Date / Invoice Date 등 변형 대응
        m = re.search(r"\b(Document|Invoice)\s+Date\s+([0-9./-]{8,10})", text, re.I)
        if m: raw_date = m.group(2).strip()

        # Total CUR 1.234,56 / Total EUR 1,234.56
        m = re.search(r"\bTotal\s+[A-Z]{3}\s+([0-9][0-9.,]*)", text, re.I)
        if m: amount = self.normalize_amount(m.group(1))

        return {
            "invoice_no": no,
            "invoice_date": self.normalize_date(raw_date) if raw_date else None,
            "amount": amount,
        }

    def parse_pdf(self, pdf_path):
        return self.parse_text(self.read_text(pdf_path))

    # ---------- 폴더 실행(리턴 없음) ----------
    def run(self, folder=None):
        self._log("Evident ingredients 시작")
        folder = folder or self.folder
        if not os.path.isdir(folder):
            self._log(f"폴더 없음: {folder}"); return
        for fname in os.listdir(folder):
            if not fname.lower().endswith(".pdf"): continue
            path = os.path.join(folder, fname)
            try:
                row = self.parse_pdf(path)
                # ✅ 지정 3필드만 출력

                obj = {
                    "invoice_date": row.get("invoice_date"),
                    "amount": row.get("amount"),
                    "invoice_no": row.get("invoice_no"),
                    "file": fname
                }
                self._log(f"Evident ingredients: {obj}")

            except Exception as e:
                self._log({"error": str(e), "file": fname})
