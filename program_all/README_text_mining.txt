텍스트 마이닝 파이프라인 사용법
================================

[필수 설치]
pip install pandas matplotlib wordcloud networkx
# (선택) 명사 추출을 쓰려면
pip install konlpy

[입력 CSV]
- 기사 본문 1컬럼 CSV (헤더 없는 경우 --headerless 사용)
- 인코딩은 기본 utf-8-sig (엑셀 저장 시 호환)

[빠른 실행 예시]
python text_mining_pipeline.py --csv "2023-2025 [내용-컬럼전부제거].csv" --headerless --outdir out_basic

# 명사 추출(konlpy) 버전
python text_mining_pipeline.py --csv "2023-2025 [내용-컬럼전부제거].csv" --headerless --use_konlpy --outdir out_nouns

# 폰트가 깨질 때 (Windows 예시: 맑은 고딕)
python text_mining_pipeline.py --csv "2023-2025 [내용-컬럼전부제거].csv" --headerless --font "C:\Windows\Fonts\malgun.ttf"

[출력 파일]
- top_words.csv              : 상위 단어 빈도
- wordcloud.png              : 워드클라우드
- top_pairs.csv              : 상위 단어쌍(공출현)
- cooccurrence_network.png   : 단어 네트워크 그래프
- trend_top10.png (옵션)     : CSV에 날짜 컬럼 있을 때 월별 트렌드

[팁]
- 불용어는 결과를 보면서 한두 개씩 추가해가면 정확도가 좋아집니다.
- 네트워크 그래프는 상위 100~200쌍만 그려야 보기 좋습니다.
- 엑셀/파워포인트에 이미지를 바로 붙이면 발표용 자료 완성!
