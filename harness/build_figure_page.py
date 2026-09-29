#!/usr/bin/env python3
"""Build the figure gallery page from the paper draft, so captions have a single source.

Usage: python3 harness/build_figure_page.py paper/ko/draft.md -o OUT.html

Each <!-- FIG name | 그림 N. caption --> in the draft becomes one card with the themed SVG and the same
caption, labelled with the section it sits in. Figures in paper/figures/ that the draft does not use
are listed at the end with EXTRA captions below.
"""
import argparse, html, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_draft_html import svg, FIG_DIR

EXTRA = {"fig12_cost": "표 2의 그림 버전. SLO를 지킨 출력 토큰 100만 개당 원가(로그 눈금). 모든 반복이 대화형 SLO를 지킨 가장 높은 요청률에서 계산했다(g7e 시간당 3.363달러 × GPU 수). none은 그 구성이 달성률 0.9에 닿지 못했다는 뜻이다."}

CSS = """
:root{
  --ground:#F3F5F4; --paper:#FFFFFF; --ink:#18212B; --ink-2:#3B4754; --muted:#667481;
  --line:#D5DCDA; --accent:#0E6568; --accent-soft:#DCEDEC; --amber:#A66A12; --amber-soft:#F6EAD4;
  --f-ink:#1b232b; --f-ink2:#56626c; --f-grid:#E1E6E4; --f-neutral:#9aa3a1;
  --s1:#1d4f91; --s2:#c8501e; --s3:#e9a23b; --s4:#6b3410; --s5:#6aa8e0; --s2soft:#f4b79c;
  --serif:"Noto Serif KR",Georgia,serif;
  --sans:"IBM Plex Sans KR","Apple SD Gothic Neo",system-ui,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
  --figfont:"IBM Plex Sans","IBM Plex Sans KR",system-ui,sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  color-scheme:dark;
  --ground:#12181D; --paper:#1A2229; --ink:#E6ECEA; --ink-2:#C2CCCA; --muted:#8C9A9E;
  --line:#2E3A42; --accent:#5FB8B6; --accent-soft:#183436; --amber:#E0A94E; --amber-soft:#342913;
  --f-ink:#E6ECEA; --f-ink2:#A9B5B8; --f-grid:#26323A; --f-neutral:#6E7A7F;
  --s1:#7fa9e6; --s2:#e87a43; --s3:#f4c46a; --s4:#a45a26; --s5:#c2dcf7; --s2soft:#7a3e25;
}}
:root[data-theme="dark"]{
  color-scheme:dark;
  --ground:#12181D; --paper:#1A2229; --ink:#E6ECEA; --ink-2:#C2CCCA; --muted:#8C9A9E;
  --line:#2E3A42; --accent:#5FB8B6; --accent-soft:#183436; --amber:#E0A94E; --amber-soft:#342913;
  --f-ink:#E6ECEA; --f-ink2:#A9B5B8; --f-grid:#26323A; --f-neutral:#6E7A7F;
  --s1:#7fa9e6; --s2:#e87a43; --s3:#f4c46a; --s4:#a45a26; --s5:#c2dcf7; --s2soft:#7a3e25;
}
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.65;margin:0;padding-inline:18px;padding-block:36px 80px;word-break:keep-all;overflow-wrap:anywhere}
.wrap{max-width:980px;margin:0 auto;display:grid;gap:30px}
header{display:grid;gap:10px;padding-bottom:20px;border-bottom:2px solid var(--ink)}
h1{font-family:var(--serif);font-weight:800;font-size:clamp(26px,4vw,38px);margin:0;line-height:1.2;text-wrap:balance}
.sub{color:var(--ink-2);font-size:15.5px;max-width:48em;margin:0}
.meta{font-family:var(--mono);font-size:12px;color:var(--muted);display:flex;flex-wrap:wrap;gap:6px 16px}
.meta a{color:var(--accent)}
h2{font-family:var(--serif);font-size:23px;font-weight:800;margin:0;text-wrap:balance}
p{margin:0}
.tbl{overflow-x:auto;border:1px solid var(--line);background:var(--paper);border-radius:3px}
table{border-collapse:collapse;width:100%;min-width:620px;font-size:13.5px}
th,td{text-align:left;padding:7px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-family:var(--mono);font-weight:500;font-size:11.5px;color:var(--muted);background:var(--ground)}
tr:last-child td{border-bottom:0}
td.n{font-family:var(--mono);white-space:nowrap;color:var(--accent)}
td a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--line)}
td a:hover,td a:focus-visible{color:var(--accent);border-color:var(--accent)}
.figs{display:grid;gap:26px}
figure{margin:0;background:var(--paper);border:1px solid var(--line);border-radius:3px;display:grid;scroll-margin-top:20px}
.fh{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 14px;padding:14px 18px 6px}
.fh .no{font-family:var(--mono);font-size:12px;color:var(--accent);letter-spacing:.04em}
.fh h3{font-family:var(--serif);font-size:18.5px;font-weight:800;margin:0;flex:1 1 20em;text-wrap:balance}
.chips{display:flex;gap:6px;font-family:var(--mono);font-size:11px}
.chips span{padding:1px 7px;border-radius:2px;background:var(--accent-soft);color:var(--accent)}
.chips span.k{background:var(--ground);color:var(--ink-2);border:1px solid var(--line)}
.plot{padding:6px 14px 4px;overflow-x:auto}
.plot svg{display:block;width:100%;min-width:560px;height:auto;max-width:860px;margin:0 auto}
figcaption{display:grid;gap:6px;padding:10px 18px 16px;border-top:1px solid var(--line);font-size:14px;max-width:none}
figcaption .r{display:grid;grid-template-columns:5.2em 1fr;gap:10px}
figcaption .r b{font-family:var(--mono);font-weight:500;font-size:11.5px;color:var(--muted);padding-top:3px}
figcaption .r.warn b{color:var(--amber)}
.box{background:var(--paper);border:1px solid var(--line);border-left:3px solid var(--accent);padding:14px 18px;display:grid;gap:6px;font-size:14px;border-radius:2px}
ul{margin:0;padding-left:1.1em;display:grid;gap:4px}
.links{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:14px}
.links a{color:var(--accent)}
footer{font-family:var(--mono);font-size:11.5px;color:var(--muted);border-top:1px solid var(--line);padding-top:12px}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
"""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("md"); ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    src = open(a.md).read()
    figs, sec = [], ""
    for line in src.split("\n"):
        m = re.match(r"^(#{2,3}) (.+)$", line)
        if m:
            sec = m.group(2).strip()
        for fm in re.finditer(r"<!--\s*FIG\s+(\S+)\s*\|\s*(.*?)-->", line):
            name, cap = fm.group(1), fm.group(2).strip()
            num, _, rest = cap.partition(".")
            figs.append((name, num.strip(), rest.strip(), sec))
    used = {f[0] for f in figs}
    for name, cap in EXTRA.items():
        if name not in used and os.path.exists(os.path.join(FIG_DIR, name + ".svg")):
            figs.append((name, "추가", cap, "원고 밖"))
    rows, cards = [], []
    for i, (name, num, cap, s) in enumerate(figs, 1):
        head = cap.split(". ")[0].rstrip(".")
        rows.append(f'<tr><td class="n">{html.escape(num)}</td><td><a href="#{name}">{html.escape(head)}</a></td>'
                    f'<td>{html.escape(s)}</td><td style="font-family:var(--mono);font-size:12px;color:var(--muted)">{name}.pdf</td></tr>')
        cards.append(f'<figure id="{name}"><div class="fh"><span class="no">{html.escape(num)}</span>'
                     f'<h3 id="t{i}">{html.escape(head)}</h3><div class="chips"><span>{html.escape(s)}</span></div></div>'
                     f'<div class="plot">{svg(name, i).replace("aria-labelledby=\"cap", "aria-labelledby=\"t")}</div>'
                     f'<figcaption><p>{html.escape(cap)}</p></figcaption></figure>')
    page = f"""<title>PD 논문 그림</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;700&family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Noto+Serif+KR:wght@600;800&display=swap">
<style>{CSS}
figcaption p{{margin:0;font-size:14px;color:var(--ink-2)}}</style>
<div class="wrap">
<header>
  <h1>PD 논문 그림</h1>
  <p class="sub">한국어 원고에 들어간 그림을 원고와 같은 번호와 캡션으로 모았습니다. 캡션은 원고(paper/ko/draft.md)에서 그대로 가져오므로 둘이 어긋나지 않습니다. 그림 안의 글자는 논문용이라 영어입니다. 같은 그림이 저장소에 PDF 벡터로 있습니다.</p>
  <div class="meta"><span>생성 harness/build_figure_page.py</span><span>그림 스크립트 harness/make_figures.py, slo_sensitivity.py</span><a href="(artifact link removed)" target="_blank" rel="noopener">한국어 원고</a><a href="(artifact link removed)" target="_blank" rel="noopener">PD 검증 결론</a></div>
</header>
<section style="display:grid;gap:12px">
  <h2>그림 목록</h2>
  <div class="tbl"><table><thead><tr><th>번호</th><th>제목</th><th>원고 위치</th><th>파일</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
  <div class="box"><span><b>읽는 법.</b> 파랑 계열은 복제본(진한 파랑 2대, 연한 파랑 3대), 주황 계열은 분리(주황 1P1D, 노랑 1P2D, 갈색 2P1D)입니다. 실선은 2노드, 점선과 일점쇄선은 3노드입니다. 가로 점선은 달성률 0.9입니다. 판정은 요청별 대화형 SLO(첫 토큰 1초 이하, 요청 안 최대 토큰 간격 50 ms 이하)입니다.</span></div>
</section>
<section class="figs">{''.join(cards)}</section>
<footer>PD 분리 연구 · 논문 그림 · 원고 캡션에서 생성</footer>
</div>
"""
    open(a.out, "w").write(page)
    print(f"wrote {a.out}: {len(figs)} figures")


if __name__ == "__main__":
    main()
