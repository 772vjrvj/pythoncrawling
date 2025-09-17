# -*- coding: utf-8 -*-
import os, re, datetime

def read_text(pdf_path):
    try:
        from pypdf import PdfReader
    except:
        from PyPDF2 import PdfReader
    r = PdfReader(pdf_path)
    return "\n".join((p.extract_text() or "") for p in getattr(r, "pages", []))

def parse_lignopure(raw):
    s = re.sub(r"[\u00A0\s]+", " ", raw)
    m_inv = re.search(r"\bInvoice\s+([A-Z0-9-]+)", s, re.I)
    m_dt  = re.search(r"(?:Date\s*(?:of\s*(?:issue|invoice))?\s*[:\-]?\s*)([0-3]?\d\.[01]?\d\.\d{4})", s, re.I) \
            or re.search(r"\b([0-3]?\d\.[01]?\d\.\d{4})\b", s)  # 라벨 없으면 첫 날짜
    m_amt = re.search(r"TOTAL\s*\((?:inkl|incl)\.?\s*(?:MwSt|VAT)\.?\)\s*([0-9][\d\s.,]*)\s*€", s, re.I) \
            or re.search(r"€\s*([0-9][\d\s.,]*)\s*TOTAL\s*\((?:inkl|incl)\.?\s*(?:MwSt|VAT)\.?\)", s, re.I)
    if not (m_inv and m_dt and m_amt): return None

    inv = m_inv.group(1).strip()
    iso = datetime.datetime.strptime(m_dt.group(1), "%d.%m.%Y").date().isoformat()

    val = m_amt.group(1).strip().replace(" ", "")
    if "," in val and "." in val: val = val.replace(".", "").replace(",", ".")
    elif "," in val: val = val.replace(",", ".")
    amount = f"{float(val):.2f}"  # 항상 소수점 2자리

    return {"Invoice No.": inv, "Date": iso, "Amount": amount}

if __name__ == "__main__":
    base = os.path.join(os.getcwd(), "수입 선적서류", "Lignopure")
    if not os.path.isdir(base):
        print("폴더 없음:", base); raise SystemExit(1)
    for name in sorted(os.listdir(base)):
        if name.lower().endswith(".pdf"):
            path = os.path.join(base, name)
            try:
                obj = parse_lignopure(read_text(path))
                print(f"[{name}] ->", obj if obj else "필드 미검출")
            except Exception as e:
                print(f"[{name}] -> 에러:", str(e))
