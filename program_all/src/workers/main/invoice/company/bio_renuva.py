# -*- coding: utf-8 -*-
import os, re
from datetime import datetime
from pypdf import PdfReader

class BioRenuvaInvoiceParser:

    def __init__(self, folder="수입 선적서류/BioRenuva", log_func=print):
        self.folder, self.log_func = folder, log_func


    # region 유틸: 영어 월 → 숫자
    _MONTHS = {
        'JANUARY': 1, 'JAN': 1,
        'FEBRUARY': 2, 'FEB': 2,
        'MARCH': 3, 'MAR': 3,
        'APRIL': 4, 'APR': 4,
        'MAY': 5,
        'JUNE': 6, 'JUN': 6,
        'JULY': 7, 'JUL': 7,
        'AUGUST': 8, 'AUG': 8,
        'SEPTEMBER': 9, 'SEP': 9, 'SEPT': 9,
        'OCTOBER': 10, 'OCT': 10,
        'NOVEMBER': 11, 'NOV': 11,
        'DECEMBER': 12, 'DEC': 12,
    }
    # endregion


    # region 날짜 변환1 : January 4, 2024 → YYYY-MM-DD
    def _to_iso_date_named(self, s: str) -> str:
        """'January 4, 2024' / 'Jan 4, 2024' / 'Aug. 17, 2023' → 'YYYY-MM-DD'"""
        if not s:
            return ""
        m = re.search(r'(?i)\b([A-Za-z]+)\.?\s+(\d{1,2}),\s*(\d{4})\b', s.strip())
        if not m:
            return ""
        mon_name, day, year = m.group(1), int(m.group(2)), int(m.group(3))
        mon = self._MONTHS.get(mon_name.strip().upper(), 0)
        if mon == 0:
            return ""
        try:
            return datetime(year, mon, day).strftime('%Y-%m-%d')
        except ValueError:
            return ""
    # endregion


    # region 날짜 변환2 : 06/26/2025 → YYYY-MM-DD
    def _to_iso_date_numeric(self, s: str) -> str:
        """'06/26/2025' or '6-26-25' → 'YYYY-MM-DD' (2자리 연도도 허용)"""
        if not s:
            return ""
        m = re.search(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', s.strip())
        if not m:
            return ""
        mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if yy < 100:
            yy += 2000 if yy < 70 else 1900
        try:
            return datetime(yy, mm, dd).strftime('%Y-%m-%d')
        except ValueError:
            return ""

    def _to_iso_date_any(self, s: str) -> str:
        """영문/숫자 형식 모두 지원"""
        return self._to_iso_date_named(s) or self._to_iso_date_numeric(s)
    # endregion


    # region pdf안에 전체 text읽기
    def read_text(self, path):
        r = PdfReader(path)
        for i, p in enumerate(getattr(r, "pages", []), 1):
            t = p.extract_text() or ""
            # 디버깅: 페이지별 길이/인덱스 출력
            # self.log_func(f"[{os.path.basename(path)}] page {i} - {len(t)} chars")

            # 첫 줄 체크: INVOICE/PROFORMA INVOICE 페이지만 사용
            first_line = t.strip().splitlines()[0] if t.strip() else ""
            u = first_line.upper()
            if u.startswith("PROFORMA INVOICE") or u.startswith("INVOICE"):
                # self.log_func(t)  # 전체 텍스트 확인 원하면 주석 해제
                return t
        return ""  # 조건 맞는 페이지가 없으면 빈 문자열
    # endregion


    # region 전용 파서: "Invoice details" 블록 ---
    def _parse_invoice_details_block(self, page_text: str, res: dict) -> dict:
        """
        아래 형태를 우선 정확히 파싱:
            Invoice details
            Invoice no.: 1062
            Terms: Net 30
            Invoice date: 06/26/2025
            Due date: 07/26/2025
        """
        if not page_text or not re.search(r'(?i)\bInvoice\s+details\b', page_text):
            return res

        # Invoice no.
        m_no = re.search(r'(?i)\bInvoice\s*no\.?\s*[:#-]?\s*([A-Za-z0-9\-_/ ]+)', page_text)
        if m_no:
            res.setdefault("Invoice no.", m_no.group(1).strip())
            if not res["Invoice no."]:
                res["Invoice no."] = m_no.group(1).strip()

        # Invoice date (숫자/영문 다 커버)
        m_dt_num = re.search(r'(?i)\bInvoice\s*date\b[:#-]?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})', page_text)
        if m_dt_num:
            res_date = self._to_iso_date_numeric(m_dt_num.group(1))
            if res_date:
                res["Invoice date"] = res_date

        # Amount: 기존 Total 규칙 재사용(Subtotal 제외, 마지막 Total)
        if res.get("Amount") is None:
            totals = []
            for m in re.finditer(r'(?is)(?<!sub)\btotal\b[^0-9$]{0,16}\$?\s*([\d,]+(?:\.\d{2})?)', page_text, flags=re.I):
                val = m.group(1)
                if val:
                    try:
                        totals.append(float(val.replace(",", "")))
                    except ValueError:
                        pass
            if totals:
                res["Amount"] = totals[-1]

        return res
    # endregion


    # region field 추출
    def parse_fields(self, page_text: str):
        """
        page_text에서 3개 필드 추출:
        - Invoice date (YYYY-MM-DD)
        - Invoice no.
        - Amount (마지막 'Total $', Subtotal 제외)
        """
        res = {"Invoice date": None, "Invoice no.": None, "Amount": None}
        if not page_text:
            return res

        lines = [ln.strip() for ln in page_text.splitlines()]

        # 0) "Invoice details" 블록이 있으면 전용 파서를 먼저 시도
        if re.search(r'(?i)\bInvoice\s+details\b', page_text):
            res = self._parse_invoice_details_block(page_text, res)

        # 1) Shipment Information 라인 기준 (기존 규칙) — 아직 비어있으면 보조로 시도
        if res.get("Invoice no.") is None or res.get("Invoice date") is None:
            idx_ship = -1
            for idx, ln in enumerate(lines):
                if re.fullmatch(r'(?i)\s*Shipment\s+Information\s*', ln or ""):
                    idx_ship = idx
                    break

            if idx_ship > 0:
                up_nonempty = []
                j = idx_ship - 1
                while j >= 0 and len(up_nonempty) < 2:
                    if lines[j]:
                        up_nonempty.append(lines[j])
                    j -= 1
                if len(up_nonempty) >= 1 and res.get("Invoice no.") is None:
                    res["Invoice no."] = up_nonempty[0]
                if len(up_nonempty) >= 2 and res.get("Invoice date") is None:
                    res["Invoice date"] = self._to_iso_date_any(up_nonempty[1])

        # 2) 라벨 기반 보조 매칭(여전히 비어있을 때)
        if not res.get("Invoice no."):
            m_no = re.search(r'(?i)\bInvoice\s*no\.?\s*[:#-]?\s*([A-Za-z0-9\-_/ ]+)', page_text)
            if m_no:
                res["Invoice no."] = m_no.group(1).strip()

        if not res.get("Invoice date"):
            m_dt_txt = re.search(r'(?i)\bInvoice\s*date\b[:#-]?\s*([A-Za-z]+\.?\s+\d{1,2},\s*\d{4})', page_text)
            m_dt_num = re.search(r'(?i)\bInvoice\s*date\b[:#-]?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})', page_text)
            if m_dt_txt:
                res["Invoice date"] = self._to_iso_date_named(m_dt_txt.group(1))
            elif m_dt_num:
                res["Invoice date"] = self._to_iso_date_numeric(m_dt_num.group(1))

        # 3) Amount: Subtotal 제외, 'Total $ 725.00' 패턴(가장 마지막 Total)
        if res.get("Amount") is None:
            totals = []
            for m in re.finditer(r'(?is)(?<!sub)\btotal\b[^0-9$]{0,16}\$?\s*([\d,]+(?:\.\d{2})?)', page_text, flags=re.I):
                val = m.group(1)
                if val:
                    try:
                        totals.append(float(val.replace(",", "")))
                    except ValueError:
                        pass
            if totals:
                res["Amount"] = totals[-1]

        return res
    # endregion


    def run(self):
        # .pdf 로 끝나는 파일들을 가져옴.
        files = [f for f in sorted(os.listdir(self.folder)) if f.lower().endswith(".pdf")]
        total = len(files)

        for idx, fname in enumerate(files, 1):
            self.log_func(f"[{idx}/{total}] : {fname}")  # === 신규 ===

            fpath = os.path.join(self.folder, fname)
            txt = self.read_text(fpath)
            fields = self.parse_fields(txt)
            self.log_func(
                f"[RESULT] {fname} -> "
                f"Invoice date={fields.get('Invoice date')}, "
                f"Invoice no.={fields.get('Invoice no.')}, "
                f"Amount={fields.get('Amount')}"
            )