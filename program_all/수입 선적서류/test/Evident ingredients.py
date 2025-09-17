# -*- coding: utf-8 -*-
"""
Evident Ingredients 인보이스 파서
- 경로: 프로그램 시작경로/수입 선적서류/Evident ingredients
- 결과: invoice_date, amount, invoice_no 만 출력
"""

import os, re

# === 기본 경로 ===
BASE_DIR = os.path.join(os.getcwd(), "수입 선적서류", "Evident ingredients")

# === PDF 읽기 ===
def read_text(pdf_path: str) -> str:
    try:
        from pypdf import PdfReader
    except:
        from PyPDF2 import PdfReader
    r = PdfReader(pdf_path)
    return "\n".join((p.extract_text() or "") for p in getattr(r, "pages", []))

# === 날짜 정규화 ===
def normalize_date(d: str) -> str | None:
    m = re.match(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", d.strip())
    if not m:
        return None
    dd, mm, yy = m.groups()
    yy = ("20" + yy) if len(yy) == 2 else yy
    return f"{yy}-{int(mm):02d}-{int(dd):02d}"

# === 금액 변환 ===
def normalize_amount(s: str) -> float | None:
    s = re.sub(r"^[A-Z]{3}\s+", "", s.strip())  # "EUR " 제거
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except:
        return None

# === 파서 ===
def parse_invoice(text: str):
    no, raw_date, amount = None, None, None

    m = re.search(r"\bInvoice\s+([A-Z0-9-]+)", text, re.I)
    if m:
        no = m.group(1).strip()

    m = re.search(r"\bDocument\s+Date\s+([0-9./-]{8,10})", text, re.I)
    if m:
        raw_date = m.group(1).strip()

    m = re.search(r"\bTotal\s+[A-Z]{3}\s+([0-9][0-9.,]*)", text, re.I)
    if m:
        amount = normalize_amount(m.group(1))

    return {
        "invoice_no": no,
        "invoice_date": normalize_date(raw_date) if raw_date else None,
        "amount": amount,
    }

# === 실행 ===
def main():
    for fname in os.listdir(BASE_DIR):
        if not fname.lower().endswith(".pdf"):
            continue
        path = os.path.join(BASE_DIR, fname)
        try:
            txt = read_text(path)
            row = parse_invoice(txt)
            print(row)  # invoice_date, amount, invoice_no 만 출력
        except Exception as e:
            print({"error": str(e), "file": fname})

if __name__ == "__main__":
    main()
