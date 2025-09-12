import csv

def csv_to_txt(csv_filename="review_details.csv", txt_filename="review_details.txt"):
    with open(csv_filename, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        with open(txt_filename, "w", encoding="utf-8") as out:
            for row in reader:
                title = row.get("제목", "").strip()
                content = row.get("내용", "").strip()
                out.write(f"제목: {title}\n")
                out.write(f"내용: {content}\n\n\n\n\n\n\n")  # 항목 간 간격

    print(f"💾 {txt_filename} 저장 완료")

if __name__ == "__main__":
    csv_to_txt("review_details.csv", "review_details.txt")
