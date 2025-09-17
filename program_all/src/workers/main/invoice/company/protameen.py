# -*- coding: utf-8 -*-
"""
Protameen 인보이스 파서 (텍스트 PDF 전용)
- 추출: NUMBER(Invoice No.) / INVOICE DATE(YYYY-MM-DD) / AMOUNT($)
- 기본 경로: 프로그램 시작경로/수입 선적서류/Protameen
- 출력만 하고 리턴 없음
"""

import os, re

class ProtameenInvoiceParser:
    def __init__(self, folder=None, log_func=None):
        self.folder = folder or os.path.join(os.getcwd(), "수입 선적서류", "Protameen")
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

    # ---------- 유틸 ----------
    def _nearest_value(self, s, label, patt, max_span=220):
        u = (s or "").upper()
        li = u.find(label)
        if li == -1: return None
        best, best_d = None, None
        for m in re.finditer(patt, s, re.I):
            d = abs((m.start()+m.end())//2 - li)
            if d <= max_span and (best is None or d < best_d):
                best, best_d = m, d
        return best

    # ---------- 파서 ----------
    def parse_text(self, raw):
        if not raw: return None
        s = (raw or "").replace("\u00A0", " ")
        s = re.sub(r"[ \t]+", " ", s)

        # 1) INVOICE DATE 근처의 MM/DD/YYYY
        m_dt = self._nearest_value(s, "INVOICE DATE", r"([01]?\d/[0-3]?\d/\d{4})")
        if not m_dt: return None
        mm, dd, yyyy = m_dt.group(1).split("/")
        iso = f"{int(yyyy):04d}-{int(mm):02d}-{int(dd):02d}"

        # 2) NUMBER 근처의 6~10자리 숫자(우편번호 5자리 배제)
        m_no = self._nearest_value(s, "NUMBER", r"(?<!\d)(\d{6,10})(?!\d)", max_span=600)
        if not m_no: return None
        inv = m_no.group(1)

        # 3) AMOUNT 하위 400자 내 마지막 $금액
        ui = s.upper().find("AMOUNT")
        if ui == -1: return None
        win = s[ui: ui+400]
        dollars = list(re.finditer(r"\$\s*([\d,]+\.\d{2})", win))
        if not dollars: return None
        amt = f"{float(dollars[-1].group(1).replace(',', '')):.2f}"

        return {"Invoice No.": inv, "Date": iso, "Amount": amt}

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
