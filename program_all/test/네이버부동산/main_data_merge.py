# -*- coding: utf-8 -*-
import json

def merge_city_cluster(city_file: str, cluster_file: str, output_file: str):
    # JSON 파일 읽기
    with open(city_file, "r", encoding="utf-8") as f:
        city_data = json.load(f)

    with open(cluster_file, "r", encoding="utf-8") as f:
        cluster_data = json.load(f)

    # cluster 데이터를 (lat, lon) -> 객체 매핑으로 변환
    cluster_map = {(c["lat"], c["lon"]): c for c in cluster_data}

    merged_result = []

    for city in city_data:
        lat, lon = city.get("lat", ""), city.get("lon", "")
        cluster = cluster_map.get((lat, lon))

        if cluster:
            merged = {
                "시도": city.get("시도", ""),
                "시군구": city.get("시군구", ""),
                "읍면동": city.get("읍면동", ""),
                "lat": lat,
                "lon": lon,
                "clusterList_url": cluster.get("clusterList_url", ""),
                "articleList": cluster.get("articleList", "")
            }
        else:
            # 매칭 실패 시 빈값
            merged = {
                "시도": city.get("시도", ""),
                "시군구": city.get("시군구", ""),
                "읍면동": city.get("읍면동", ""),
                "lat": "",
                "lon": "",
                "clusterList_url": "",
                "articleList": ""
            }

        merged_result.append(merged)

    # 결과 JSON 저장
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_result, f, ensure_ascii=False, indent=2)

    print(f"✅ 병합 완료! 결과 저장: {output_file}")


if __name__ == "__main__":
    merge_city_cluster("city_latlon.json", "cluster_result.json", "naver_real_estate_data.json")
