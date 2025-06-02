import os
import json
import pandas as pd

def load_reviews_from_json(folder_path):
    all_reviews = []
    seen_ids = set()

    # 폴더 내 모든 JSON 파일 순회
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    reviews = data.get("data", {}).get("vehicleReviews", {}).get("reviews", [])
                    for r in reviews:
                        review_id = r.get("id")
                        if review_id and review_id not in seen_ids:
                            seen_ids.add(review_id)
                            all_reviews.append({
                                "차량": r.get("spans",""),
                                "제목": r.get("title", ""),
                                "내용": r.get("text", ""),
                                "작성자": r.get("author", {}).get("authorName", ""),
                                "작성일": r.get("created", "")
                            })
                except Exception as e:
                    print(f"⚠️ 파일 {filename} 로드 중 오류: {e}")

    return all_reviews

def save_reviews_to_excel(reviews, filename="merged_reviews.xlsx"):
    df = pd.DataFrame(reviews)
    df.to_excel(filename, index=False)
    print(f"✅ 엑셀 저장 완료: {filename}")

def main():
    folder = "json"  # JSON 파일이 저장된 폴더명
    reviews = load_reviews_from_json(folder)
    save_reviews_to_excel(reviews)

if __name__ == "__main__":
    main()
