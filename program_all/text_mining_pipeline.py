# -*- coding: utf-8 -*-
"""
text_mining_pipeline_nouns_pro3d.py
- 명사 중심 텍스트 마이닝 (Okt.nouns)
- WordCloud (PNG)
- 2D 네트워크 (PNG, 프로 스타일)
- 3D 네트워크 (HTML, 군집 색상 + 가중치 엣지 + 상위 라벨 항상 표시)

설치:
  pip install pandas matplotlib networkx wordcloud plotly konlpy JPype1
  # (선택) pip install scipy   # --use_kamada 사용 시 권장

실행 예:
  python text_mining_pipeline_nouns_pro3d.py --csv "2023-2025.csv" --headerless ^
    --font "C:\\Windows\\Fonts\\NanumGothic.ttf" --outdir out_pro ^
    --topn 300 --topn_pairs 400 --min_edge 3 --label_topk 30 --use_kamada
"""
from __future__ import annotations
import argparse, re, math
from pathlib import Path
from typing import List, Tuple, Dict
from collections import Counter
from itertools import combinations

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as pe
import networkx as nx
from wordcloud import WordCloud
import plotly.graph_objects as go
from konlpy.tag import Okt

# ---------------- 불용어 ----------------
BASIC_STOPWORDS = {
    "그리고","그러나","하지만","또한","위해","대한","관련","이번","오늘","지난",
    "우리","여러","많은","다른","이런","저런","그런","하는","했다","됐다","했다",
    "에서","으로","에게","에서는","까지","부터","이다","하면","아니다","보다",
    "보도","기사","사진","영상","기자","연합뉴스","뉴스","제공","대해",
    # 행님이 추가한 불용어 ↓
    "있다","있는","통해","라고","밝혔다","모든","이후","이어","것으로","진심으로",
    "당시","함께","그는","열린","이라고","감독은","전했다","지난해","징계를","최근",
    "한다","여러분께","말씀을","감독이","같은","없다","라며","결국","말했다","과정에서",
    "선수가","이에","사실을","사과의","책임을","논란이","자신의","않았다","사과드린다",
    "발표했다","사과했다","것은","받았다","이를","모두","받은","것을","때문에","일이",
    "라는","고개를","경기를","선수들이","덧붙였다","것이다","선수의","없는","있었다",
    "따르면","좋은","숙였다","것이","KIA는","많이","더욱","직접","못했다",
    "앞으로","조치를","못한","설명했다","등을","역시","않도록","오후","어떤","향후",
    "있습니다","지금","없이","올렸다","관련해","팬들의","혐의로","위한","가장","일부",
    "숙여","받고","아니라","있도록","재발","만에","소속","드린다","깊은","그런데",
    "않은","감독의","면서","사과를","하지","구단의","어떻게","구단에","다만","특히",
    "문제가","정말","생각한다","따라","지난달","제가","오전","있다는","것에","팬들에게",
    "벤탄쿠르는","먼저","입장을","그러면서","사실이","글을","내렸다","경우","결정했다",
    "같다","선수는","죄송하다","최선을","선수들의","없었다","이라며","깊이","SNS에",
    "혐의를","아닌","기간", "사과문을", "구단은", "다시","경기","선수","해당", "이날", "한국",
    "구단", "하고", "사과드립니다.", "알려졌다", "사과", "사과문"
}

# ---------------- 텍스트 전처리 ----------------
def clean_text(s: str) -> str:
    if not isinstance(s, str): return ""
    s = re.sub(r"https?://\S+|www\.\S+", " ", s)
    s = re.sub(r"[^\w\s가-힣]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# ---------------- 형태소 분석 (명사만) ----------------
okt = Okt()
def tokenize_nouns(s: str, stopwords: set[str]) -> List[str]:
    toks = okt.nouns(s)                  # 명사만 추출
    return [w for w in toks if len(w) >= 2 and w not in stopwords]

# ---------------- 공출현 ----------------
def count_cooccurrence(tokens_list: List[List[str]]) -> Counter[Tuple[str,str]]:
    c = Counter()
    for toks in tokens_list:
        uniq = sorted(set(toks))
        for a, b in combinations(uniq, 2):
            c[(a,b)] += 1
    return c

# ---------------- 유틸 ----------------
def norm(v, lo, hi):
    if hi <= lo: return 0.0
    return (v - lo) / (hi - lo)

# ---------------- 워드클라우드 ----------------
def save_wordcloud(freq: Dict[str,int], out_png: Path, font_path: str|None):
    if not freq:
        print("[WARN] 워드클라우드에 쓸 단어가 없습니다.")
        return
    wc = WordCloud(
        font_path=font_path,
        width=1400, height=900, background_color="white",
        collocations=False, prefer_horizontal=0.95
    ).generate_from_frequencies(freq)
    plt.figure(figsize=(12, 8))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title("Word Cloud", fontsize=16)
    plt.savefig(out_png, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"[OK] 워드클라우드 저장: {out_png}")

# ---------------- 커뮤니티 탐지 ----------------
def detect_communities(G: nx.Graph) -> Dict[str, int]:
    try:
        from networkx.algorithms.community import greedy_modularity_communities
        comms = list(greedy_modularity_communities(G))
        node2comm = {}
        for cid, nodes in enumerate(comms):
            for n in nodes:
                node2comm[n] = cid
        return node2comm
    except Exception:
        return {n: 0 for n in G.nodes()}

PALETTE10 = [
    "#A6CEE3", "#B2DF8A", "#FDBF6F", "#CAB2D6", "#FFFF99",
    "#FB9A99", "#CCEBC5", "#FFED6F", "#E0E0E0", "#FFD9C0"
]

# ---------------- 2D 네트워크 (PNG, 프로 스타일) ----------------
def save_network_2d(G: nx.Graph, out_png: Path, font_path: str|None,
                    label_topk: int = 30, use_kamada: bool = False, seed: int = 42):
    if G.number_of_nodes() == 0:
        print("[INFO] 2D: 노드가 없어 생략")
        return

    # 중심성
    wdeg = dict(G.degree(weight="weight"))
    btw = nx.betweenness_centrality(G, weight=lambda u,v,attrs: 1/attrs["weight"], normalized=True) if G.number_of_edges() else {n:0 for n in G.nodes()}
    max_wdeg = max(wdeg.values()) if wdeg else 1

    # 레이아웃
    try:
        if use_kamada:
            pos = nx.kamada_kawai_layout(G, weight="weight")  # scipy 필요
        else:
            pos = nx.spring_layout(G, k=0.6, weight="weight", seed=seed, iterations=200)
    except Exception:
        pos = nx.spring_layout(G, seed=seed)

    # 커뮤니티 색상
    node2comm = detect_communities(G)
    colors = [PALETTE10[node2comm[n] % len(PALETTE10)] for n in G.nodes()]

    # 노드 크기
    node_sizes = [300 + 1400*(wdeg[n]/max_wdeg) for n in G.nodes()]

    # 엣지 스타일(가중치 → 두께/투명도)
    weights = [G[u][v]["weight"] for u,v in G.edges()]
    if weights:
        lo, hi = min(weights), max(weights)
        edge_widths = [0.5 + 3.5*norm(G[u][v]["weight"], lo, hi) for u,v in G.edges()]
        edge_alphas = [0.15 + 0.35*norm(G[u][v]["weight"], lo, hi) for u,v in G.edges()]
    else:
        edge_widths = [1 for _ in G.edges()]
        edge_alphas = [0.3 for _ in G.edges()]

    plt.figure(figsize=(14,10))
    # 엣지를 하나씩 그려야 알파/두께 반영이 잘 됨
    for (u,v), lw, a in zip(G.edges(), edge_widths, edge_alphas):
        nx.draw_networkx_edges(G, pos, edgelist=[(u,v)], width=lw, alpha=a, edge_color="#7f8c8d")

    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=colors,
                           alpha=0.95, edgecolors="white", linewidths=1.5)

    # 상위 라벨 (중심성 + 가중차수)
    score = {n: 0.6*btw.get(n,0) + 0.4*(wdeg[n]/max_wdeg if max_wdeg else 0) for n in G.nodes()}
    top_nodes = sorted(G.nodes(), key=lambda n: score[n], reverse=True)[:label_topk]

    font_name = None
    if font_path:
        fm.fontManager.addfont(font_path)
        font_name = fm.FontProperties(fname=font_path).get_name()

    for n in top_nodes:
        x, y = pos[n]
        txt = plt.text(x, y, n, fontsize=10, ha="center", va="center",
                       color="#111111", fontfamily=font_name)
        # txt.set_path_effects([pe.withStroke(linewidth=3.0, foreground="white")])

    plt.title("Co-occurrence Network (2D, Professional Styling)", fontsize=15)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_png, dpi=220, bbox_inches="tight")
    plt.close()
    print(f"[OK] 2D 네트워크 저장: {out_png}")

# ---------------- 3D 네트워크 (HTML, 군집/가중치/라벨) ----------------
def save_network_3d(G: nx.Graph, out_html: Path, label_topk: int = 25, seed: int = 42):
    if G.number_of_nodes() == 0:
        print("[INFO] 3D: 노드가 없어 생략")
        return

    # 중심성/가중차수
    deg = dict(G.degree())
    wdeg = dict(G.degree(weight="weight"))
    btw = nx.betweenness_centrality(G, weight=lambda u,v,attrs: 1/attrs["weight"], normalized=True) if G.number_of_edges() else {n:0 for n in G.nodes()}
    max_wdeg = max(wdeg.values()) if wdeg else 1

    # 3D 좌표
    pos = nx.spring_layout(G, dim=3, seed=seed, weight="weight", iterations=400)

    # 군집 색상
    node2comm = detect_communities(G)
    comm_colors = [PALETTE10[node2comm[n] % len(PALETTE10)] for n in G.nodes()]
    node_idx = {n:i for i,n in enumerate(G.nodes())}

    # 엣지 트레이스(선마다 두께/투명도 반영 위해 edge별 trace 생성)
    edge_traces = []
    weights = [G[u][v]["weight"] for u,v in G.edges()]
    if weights:
        lo, hi = min(weights), max(weights)
    else:
        lo, hi = 1, 1
    for (u,v) in G.edges():
        x0,y0,z0 = pos[u]
        x1,y1,z1 = pos[v]
        w = G[u][v]["weight"]
        width = 1 + 4*norm(w, lo, hi)
        alpha = 0.25 + 0.45*norm(w, lo, hi)
        edge_traces.append(
            go.Scatter3d(
                x=[x0,x1], y=[y0,y1], z=[z0,z1],
                mode="lines",
                line=dict(width=width, color=f"rgba(90,90,90,{alpha:.2f})"),
                hoverinfo="none",
                showlegend=False
            )
        )

    # 노드 트레이스
    node_x, node_y, node_z, node_size, node_color, node_text = [],[],[],[],[],[]
    for n in G.nodes():
        x,y,z = pos[n]
        node_x.append(x); node_y.append(y); node_z.append(z)
        node_size.append(6 + 18*(wdeg[n]/max_wdeg))
        node_color.append(comm_colors[node_idx[n]])
        node_text.append(f"{n}<br>degree: {deg[n]}<br>w-degree: {wdeg[n]}<br>betweenness: {btw.get(n,0):.4f}")

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode="markers",
        marker=dict(size=node_size, color=node_color, opacity=0.98),
        text=node_text, hoverinfo="text", showlegend=False
    )

    # 항상 보이는 라벨: 상위 노드만
    score = {n: 0.6*btw.get(n,0) + 0.4*(wdeg[n]/max_wdeg if max_wdeg else 0) for n in G.nodes()}
    top_nodes = sorted(G.nodes(), key=lambda n: score[n], reverse=True)[:label_topk]
    lx, ly, lz, lt = [], [], [], []
    for n in top_nodes:
        x,y,z = pos[n]
        lx.append(x); ly.append(y); lz.append(z); lt.append(n)
    label_trace = go.Scatter3d(
        x=lx, y=ly, z=lz, mode="text",
        text=lt, textposition="top center",
        textfont=dict(size=15, color="black", family="NanumGothic Bold, Arial Black, Arial"),
        hoverinfo="none", showlegend=False
    )
    fig = go.Figure(data=[*edge_traces, node_trace, label_trace])
    fig.update_layout(
        title="Co-occurrence Network (3D, Communities & Weighted Edges)",
        showlegend=False,
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            aspectmode="data"
        ),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    fig.write_html(str(out_html))
    print(f"[OK] 3D 네트워크 저장: {out_html}")

# ---------------- 그래프 빌드 ----------------
def build_graph(pairs_sorted: List[Tuple[Tuple[str,str], int]],
                min_edge: int, top_pairs_cap: int) -> nx.Graph:
    filt = [((a,b), w) for (a,b), w in pairs_sorted if w >= min_edge]
    filt.sort(key=lambda x: x[1], reverse=True)
    filt = filt[:top_pairs_cap]
    G = nx.Graph()
    for (a,b), w in filt:
        G.add_edge(a, b, weight=w)
    return G

# ---------------- 메인 파이프라인 ----------------
def run_pipeline(args):
    font_path = args.font if args.font else None
    in_csv = Path(args.csv)
    out_dir = Path(args.outdir); out_dir.mkdir(parents=True, exist_ok=True)

    # CSV 로드
    if args.headerless:
        df = pd.read_csv(in_csv, header=None, names=["content"], encoding=args.encoding)
    else:
        df = pd.read_csv(in_csv, encoding=args.encoding)
        use_col = args.column or df.columns[0]
        df = df[[use_col]].rename(columns={use_col:"content"})

    # 전처리 → 명사 토큰화
    stop = set(BASIC_STOPWORDS)
    if args.stopwords:
        try:
            extra = Path(args.stopwords).read_text(encoding="utf-8").splitlines()
            stop.update(w.strip() for w in extra if w.strip())
        except Exception as e:
            print(f"[WARN] 불용어 파일 읽기 실패: {e}")

    df["clean"]   = df["content"].astype(str).map(clean_text)
    df["tokens2"] = df["clean"].map(lambda s: tokenize_nouns(s, stop))

    # 빈도
    all_tokens = [t for toks in df["tokens2"] for t in toks]
    counter = Counter(all_tokens)
    top_words = counter.most_common(args.topn)
    pd.DataFrame(top_words, columns=["word","count"]).to_csv(out_dir/"top_words.csv", index=False, encoding="utf-8-sig")
    print("[OK] top_words.csv 저장")

    # 워드클라우드
    save_wordcloud(dict(top_words), out_dir/"wordcloud.png", font_path)

    # 공출현
    pair_counter = count_cooccurrence(df["tokens2"].tolist())
    pairs_sorted = pair_counter.most_common(args.topn_pairs)
    pd.DataFrame([(a,b,c) for (a,b),c in pairs_sorted], columns=["word1","word2","count"]).to_csv(out_dir/"top_pairs.csv", index=False, encoding="utf-8-sig")
    print("[OK] top_pairs.csv 저장")

    # 그래프 생성 → 2D/3D
    G = build_graph(pairs_sorted, min_edge=args.min_edge, top_pairs_cap=args.topn_pairs)
    save_network_2d(G, out_dir/"cooccurrence_network.png", font_path, label_topk=args.label_topk, use_kamada=args.use_kamada)
    save_network_3d(G, out_dir/"cooccurrence_network_3d.html", label_topk=args.label_topk)

    print("\n[완료] 출력 폴더:", out_dir.resolve())

def parse_args():
    p = argparse.ArgumentParser(description="Text Mining (Nouns) with Pro 3D viz")
    p.add_argument("--csv", required=True, help="입력 CSV 경로")
    p.add_argument("--outdir", default="tm_out_pro3d", help="출력 폴더")
    p.add_argument("--encoding", default="utf-8-sig")
    p.add_argument("--headerless", action="store_true")
    p.add_argument("--column", default=None)
    p.add_argument("--font", default=None, help="워드클라우드/2D 라벨용 한글 폰트 파일(.ttf/.otf)")
    p.add_argument("--stopwords", default=None, help="추가 불용어 파일 경로(한 줄당 1단어)")

    p.add_argument("--topn", type=int, default=300, help="워드클라우드 상위 N")
    p.add_argument("--topn_pairs", type=int, default=400, help="공출현쌍 상위 N")
    p.add_argument("--min_edge", type=int, default=3, help="그래프에 포함할 엣지 최소 가중치")
    p.add_argument("--label_topk", type=int, default=30, help="라벨 붙일 상위 노드 수")
    p.add_argument("--use_kamada", action="store_true", help="2D에서 Kamada-Kawai 사용 (scipy 필요)")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args)
