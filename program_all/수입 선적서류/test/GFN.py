# -*- coding: utf-8 -*-
# GFN 인보이스: Document Number / Document Date / Total Amount(EUR) 추출
import os, re, datetime

def read_text(pdf_path):
    try:
        from pypdf import PdfReader
    except:
        from PyPDF2 import PdfReader
    r = PdfReader(pdf_path)
    return "\n".join((p.extract_text() or "") for p in getattr(r, "pages", []))

def parse_gfn(raw):
    if not raw: return None
    s = raw.replace("\u00A0", " ")
    s = re.sub(r"\s+", " ", s).strip()

    # Document Number & Date
    m_num = re.search(r"\bDocument\s*Number\s*([A-Z0-9-]+)\b", s, re.I)
    m_dt  = re.search(r"\bDocument\s*Date\s*([12]\d{3}\.[01]?\d\.[0-3]?\d)\b", s, re.I)
    if not (m_num and m_dt): return None

    inv = m_num.group(1).strip()

    # 2025.07.17 -> 2025-07-17
    dstr = m_dt.group(1).strip()
    # 0 패딩 허용
    y, m, d = re.match(r"(\d{4})\.([01]?\d)\.([0-3]?\d)", dstr).groups()
    iso = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

    # Total Amount
    m_amt = re.search(r"\bTotal\s*Amount\s*([0-9][\d,]*\.\d{2})\s*(?:EUR|€)\b", s, re.I) \
            or re.search(r"\bTotal\s*Amount\s*(?:EUR|€)\s*([0-9][\d,]*\.\d{2})\b", s, re.I)
    if not m_amt: return None
    val = m_amt.group(1).replace(",", "")
    amount = f"{float(val):.2f}"  # 항상 소수점 2자리 문자열

    return {"Invoice No.": inv, "Date": iso, "Amount": amount}

if __name__ == "__main__":
    base = os.path.join(os.getcwd(), "수입 선적서류", "GFN")
    if not os.path.isdir(base):
        print("폴더 없음:", base); raise SystemExit(1)
    for name in sorted(os.listdir(base)):
        if name.lower().endswith(".pdf"):
            path = os.path.join(base, name)
            try:
                obj = parse_gfn(read_text(path))
                print(f"[{name}] ->", obj if obj else "필드 미검출")
            except Exception as e:
                print(f"[{name}] -> 에러:", str(e))
