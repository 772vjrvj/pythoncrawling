# -*- coding: utf-8 -*-
"""
BioRenuva 인보이스 파서 (3개 필드, Amount는 숫자만)
- 필드: Invoice no., Invoice date(YYYY-MM-DD), Amount(숫자만)
- 폴더: 수입 선적서류/BioRenuva
"""

import os
import re
from typing import Optional, Dict, Any, List

# --------------------------- PDF 텍스트 추출 ---------------------------

def read_text(pdf_path: str) -> str:
    """pypdf → PyPDF2 순서로 시도해서 모든 페이지 텍스트를 이어붙여 반환."""
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        from PyPDF2 import PdfReader  # type: ignore
    r = PdfReader(pdf_path)
    return "\n".join((p.extract_text() or "") for p in getattr(r, "pages", []))


# ---------------------------- 유틸 ----------------------------

def _ymd(s: str) -> Optional[str]:
    """06/26/2025, 2025-06-26, 2025.06.26, 26.06.2025 → 2025-06-26"""
    s = (s or "").strip()
    m = re.match(r"^(\d{4})[./-](\d{2})[./-](\d{2})$", s)
    if m:  # YYYY-MM-DD / YYYY.MM.DD / YYYY/MM/DD
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.match(r"^(\d{2})[./-](\d{2})[./-](\d{4})$", s)
    if m:  # MM/DD/YYYY
        mm, dd, yyyy = m.group(1), m.group(2), m.group(3)
        return f"{yyyy}-{mm}-{dd}"
    m = re.match(r"^(\d{2})[.](\d{2})[.](\d{4})$", s)
    if m:  # DD.MM.YYYY
        dd, mm, yyyy = m.group(1), m.group(2), m.group(3)
        return f"{yyyy}-{mm}-{dd}"
    return None

def _clean_amount(num: str) -> Optional[float]:
    """통화기호/문자 제거 후 숫자 float로. '9,712.50' → 9712.50"""
    if not num:
        return None
    t = re.sub(r"[^\d,.\-]", "", num.strip())  # 숫자/부호/쉼표/점만 남김
    t = t.replace(",", "")  # 천단위 구분 제거
    try:
        return float(t)
    except Exception:
        return None


# ---------------------------- 파서 ----------------------------

def parse_biorenuva(raw: str) -> Dict[str, Any]:
    """
    3필드만 반환:
      - invoice_no
      - invoice_date (YYYY-MM-DD)
      - amount (숫자만)
    """
    u = re.sub(r"[ \t]+", " ", raw)       # 라인 내 다중 공백 축소
    flat = re.sub(r"\s+", " ", u).strip() # 전체 1라인화(후보 탐색용)

    # 1) Invoice no.
    invoice_no = None
    for pat in [
        r"Invoice\s*no\.?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",
        r"Invoice\s*number\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",
        r"Invoice\s*#\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",
    ]:
        m = re.search(pat, u, re.I)
        if m:
            invoice_no = m.group(1).strip()
            break

    # 2) Invoice date
    invoice_date = None
    m = re.search(
        r"Invoice\s*date\s*[:\-]?\s*("
        r"[0-9]{2}[./-][0-9]{2}[./-][0-9]{4}|"
        r"[0-9]{4}[./-][0-9]{2}[./-][0-9]{2}|"
        r"[0-9]{2}[.][0-9]{2}[.][0-9]{4}"
        r")",
        u, re.I
    )
    if m:
        invoice_date = _ymd(m.group(1))

    # 3) Amount (Total) → 숫자만
    #  - 단어 경계 적용으로 Subtotal 방지
    #  - code/sym/num 후보 중 금액이 큰 것을 선택(테이블 "Total 1.0" 오탐 방지)
    sym_map = {"$": "USD", "€": "EUR", "£": "GBP"}  # 통화는 사용 안하지만 구분에는 도움
    candidates: List[Dict[str, Any]] = []

    # (a) 통화코드 + 숫자
    for m in re.finditer(
            r"(?<![A-Za-z])(Grand\s+Total|Total(?:\s*Amount)?|Total\s+Due)(?![A-Za-z])"
            r"\s*[:\-]?\s*([A-Z]{3})\s*([$€£]?\s*[0-9][0-9,\.]+)",
            flat, re.I
    ):
        num = m.group(3)
        val = _clean_amount(num)
        candidates.append({"kind":"code","value":val,"pos":m.start()})

    # (b) 통화기호 + 숫자
    for m in re.finditer(
            r"(?<![A-Za-z])(Grand\s+Total|Total(?:\s*Amount)?|Total\s+Due)(?![A-Za-z])"
            r"\s*[:\-]?\s*([$€£])\s*([0-9][0-9,\.]+)",
            flat, re.I
    ):
        num = m.group(3)
        val = _clean_amount(num)
        candidates.append({"kind":"sym","value":val,"pos":m.start()})

    # (c) 숫자만
    for m in re.finditer(
            r"(?<![A-Za-z])(Grand\s+Total|Total(?:\s*Amount)?|Total\s+Due)(?![A-Za-z])"
            r"\s*[:\-]?\s*([0-9][0-9,\.]+)",
            flat, re.I
    ):
        num = m.group(2)
        val = _clean_amount(num)
        candidates.append({"kind":"num","value":val,"pos":m.start()})

    chosen = None
    for kind in ("code", "sym", "num"):
        subset = [c for c in candidates if c["kind"] == kind and c["value"] is not None]
        if subset:
            chosen = max(subset, key=lambda c: (c["value"], c["pos"]))
            break

    amount = chosen["value"] if chosen else None

    return {
        "invoice_no": invoice_no,
        "invoice_date": invoice_date,
        "amount": amount,  # ✅ 숫자만
    }


def parse_biorenuva_pdf(pdf_path: str) -> Dict[str, Any]:
    return parse_biorenuva(read_text(pdf_path))


# -------------------------- 폴더 전체 실행 --------------------------

if __name__ == "__main__":
    folder = r"수입 선적서류/BioRenuva"
    results: List[Dict[str, Any]] = []

    for fname in os.listdir(folder):
        if not fname.lower().endswith(".pdf"):
            continue
        path = os.path.join(folder, fname)
        try:
            data = parse_biorenuva_pdf(path)
            data["file"] = fname
            results.append(data)
            print(f"✅ {fname} → No={data.get('invoice_no')}, Date={data.get('invoice_date')}, Amount={data.get('amount')}")
        except Exception as e:
            print(f"❌ {fname} 파싱 실패: {str(e)}")
