import os

def count_python_lines(folder_path):
    total_lines = 0
    file_count = 0

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):  # 파이썬 파일만
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        line_count = len(lines)
                        total_lines += line_count
                        file_count += 1
                        print(f"{file_path}: {line_count} lines")
                except Exception as e:
                    print(f"⚠️ {file_path} 읽기 오류: {e}")

    print("-" * 50)
    print(f"총 파일 수: {file_count}")
    print(f"전체 라인 수 합계: {total_lines}")

# 사용 예시
if __name__ == "__main__":
    count_python_lines("E:\\git\\pythoncrawling\\kmong\\ko\\bitgate-crypto-exchanger-main")# 폴더 경로 넣어주세요
