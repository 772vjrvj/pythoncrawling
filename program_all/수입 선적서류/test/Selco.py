# -*- coding: utf-8 -*-
"""
Selco 인보이스 전체 파서
- 지정한 폴더 내 PDF 전부를 읽어서 주요 정보 추출
- 결과는 리스트/CSV 등으로 후처리 가능
"""

import os
import re
from typing import Any, Dict, List, Optional

# --------------------------- PDF 텍스트 추출 ---------------------------

def read_text(pdf_path: str) -> str:
    """pypdf → PyPDF2 순서로 시도하여 전체 텍스트를 결합해 반환"""
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        from PyPDF2 import PdfReader  # type: ignore
    r = PdfReader(pdf_path)
    return "\n".join((p.extract_text() or "") for p in getattr(r, "pages", []))


# ---------------------------- 유틸리티 ----------------------------

def _num(s: str) -> Optional[float]:
    """숫자 문자열을 float로 변환 (유럽/미국 표기 모두 지원)"""
    if not s:
        return None
    t = s.strip().replace(" ", "")
    if re.search(r"\d\.\d{3}(?:\.\d{3})*,\d{2}$", t):
        t = t.replace(".", "").replace(",", ".")
    elif re.search(r"\d,\d{3}(?:,\d{3})*\.\d{2}$", t):
        t = t.replace(",", "")
    elif re.search(r"^\d[\d,\.]*$", t):
        t = t.replace(",", "")
    try:
        return float(t)
    except Exception:
        return None

def _ymd(s: str) -> Optional[str]:
    """2025.08.29 → 2025-08-29 / 29.08.2025 → 2025-08-29"""
    s = s.strip()
    m1 = re.match(r"(\d{4})[./-](\d{2})[./-](\d{2})$", s)
    if m1:
        return f"{m1.group(1)}-{m1.group(2)}-{m1.group(3)}"
    m2 = re.match(r"(\d{2})[./-](\d{2})[./-](\d{4})$", s)
    if m2:
        return f"{m2.group(3)}-{m2.group(2)}-{m2.group(1)}"
    return None


# ---------------------------- 메인 파서 ----------------------------

def parse_selco(raw: str) -> Dict[str, Any]:
    """Selco 인보이스 텍스트(raw)에서 주요 정보를 파싱"""
    u = re.sub(r"[ \t]+", " ", raw)

    # Header
    m = re.search(r"Document Number\s+([A-Za-z0-9\-]+)", u, re.I)
    document_number = m.group(1) if m else None

    m = re.search(r"Document Date\s+([0-9./-]{10})", u, re.I)
    document_date = _ymd(m.group(1)) if m else None

    m = re.search(r"PO No\.\s*([A-Za-z0-9\-\/]+)", u, re.I)
    po_no = m.group(1) if m else None
    m = re.search(r"PO Date\s*([0-9./-]{8,10})", u, re.I)
    po_date = _ymd(m.group(1)) if m else None

    m = re.search(r"Incoterms\s+([A-Z]{3}(?:[^\n]+)?)", u, re.I)
    incoterms = m.group(1).strip() if m else None

    m = re.search(r"Terms of payment\s+([^\n]+)", raw, re.I)
    terms_of_payment = m.group(1).strip() if m else None

    # Totals
    total_value = total_currency = None
    m = re.search(r"Total Amount\s+([0-9.,]+)\s+([A-Z]{3})", u, re.I)
    if m:
        total_value, total_currency = _num(m.group(1)), m.group(2)
    else:
        m = re.search(r"Total Amount\s+([A-Z]{3})\s+([0-9.,]+)", u, re.I)
        if m:
            total_currency, total_value = m.group(1), _num(m.group(2))

    m = re.search(r"Subtotal before VAT\s+([0-9.,]+)\s+([A-Z]{3})", u, re.I)
    subtotal_value = _num(m.group(1)) if m else None

    m = re.search(r"(?:Taxable|Tax)[^\n]*\s+([0-9.,]+)\s+([A-Z]{3})", u, re.I)
    tax_value = _num(m.group(1)) if m else None

    # Parties
    buyer_block = None
    m = re.search(r"HanaCare Co\., Ltd\.[\s\S]+?South Korea", raw)
    if m: buyer_block = re.sub(r"\n+", " / ", m.group(0)).strip()

    consignee_block = None
    m = re.search(r"Goods Recipient\s+([\s\S]+?)\n(?:Document Number|Ref\.Order|PO No\.)", raw, re.I)
    if m: consignee_block = re.sub(r"\n+", " / ", m.group(1)).strip()

    seller_block = None
    m = re.search(r"Selco[\s\S]+?Germany", raw, re.I)
    if m: seller_block = re.sub(r"\n+", " / ", m.group(0)).strip()

    # Items
    items: List[Dict[str, Any]] = []
    m = re.search(r"Material/Description[^\n]*\n([^\n]+)", raw, re.I)
    if m:
        line = " ".join(m.group(1).split())
        m_code = re.match(r"([A-Z0-9\-\.]+)", line)
        material = m_code.group(1) if m_code else None
        m_amt = re.search(r"([0-9.,]+)\s+([A-Z]{3})\s*$", line)
        amount_value = _num(m_amt.group(1)) if m_amt else None
        amount_currency = m_amt.group(2) if m_amt else None
        items.append({
            "material": material,
            "amount": amount_value,
            "currency": amount_currency,
            "raw": line
        })

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


def parse_selco_pdf(pdf_path: str) -> Dict[str, Any]:
    """PDF 경로를 받아 즉시 파싱"""
    return parse_selco(read_text(pdf_path))


# -------------------------- 폴더 전체 실행 --------------------------

if __name__ == "__main__":
    folder = r"수입 선적서류/Selco"   # Selco 인보이스 폴더
    results = []

    for fname in os.listdir(folder):
        if fname.lower().endswith(".pdf"):
            path = os.path.join(folder, fname)
            try:
                data = parse_selco_pdf(path)
                data["file"] = fname
                results.append(data)
                print(f"✅ {fname} → {data['document_number']}, {data['total_amount_value']} {data['document_date']}")
            except Exception as e:
                print(f"❌ {fname} 파싱 실패:", str(e))

    # 필요하다면 여기서 results를 엑셀/CSV로 저장 가능
