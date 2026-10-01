#!/usr/bin/env python3
"""Render paper/<lang>/draft.md to a standalone HTML page with the figures inlined.

Usage:
  uv run --with markdown python3 harness/build_draft_html.py paper/ko/draft.md -o OUT.html

Figures are written in the markdown as HTML comments:
  <!-- FIG fig01_request_vs_system | caption text -->
and replaced with the SVG from paper/figures/, recoloured to CSS variables so the page follows
light/dark theme. Figure colours match harness/make_figures.py.
"""
import argparse, html, os, re
import markdown

FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "paper", "figures")
CMAP = {"#0b0b0b": "var(--f-ink)", "#52514e": "var(--f-ink2)", "#dcdcd6": "var(--f-grid)",
        "#1d4f91": "var(--s1)", "#c8501e": "var(--s2)", "#e9a23b": "var(--s3)", "#6b3410": "var(--s4)",
        "#6aa8e0": "var(--s5)", "#9a9a94": "var(--f-neutral)", "#f4b79c": "var(--s2soft)", "#ffffff": "var(--paper)"}


def svg(name, idx):
    s = open(os.path.join(FIG_DIR, name + ".svg")).read()
    s = s[s.index("<svg"):]
    s = re.sub(r"<metadata>.*?</metadata>", "", s, flags=re.S)
    s = re.sub(r'(<svg[^>]*?) width="[^"]*" height="[^"]*"', r"\1", s, count=1)
    s = s.replace("<svg ", f'<svg role="img" aria-labelledby="cap{idx}" ', 1)
    p = f"f{idx}-"
    s = s.replace('id="', f'id="{p}').replace("url(#", f"url(#{p}").replace('xlink:href="#', f'xlink:href="#{p}')
    for k, v in CMAP.items():
        s = s.replace(k, v)
    return re.sub(r"font-family: '?DejaVu Sans'?[^;\"]*", "font-family: var(--figfont)", s)


CSS = """
:root{
  --ground:#F4F5F3; --paper:#FFFFFF; --ink:#1B2127; --ink-2:#3D4852; --muted:#6A7682;
  --line:#D8DDDA; --accent:#1d4f91; --accent-soft:#E3ECF7; --amber:#9A5B12; --amber-soft:#F7ECD9;
  --f-ink:#1b232b; --f-ink2:#56626c; --f-grid:#E1E6E4; --f-neutral:#9aa3a1;
  --s1:#1d4f91; --s2:#c8501e; --s3:#e9a23b; --s4:#6b3410; --s5:#6aa8e0; --s2soft:#f4b79c;
  --serif:"Noto Serif KR",Georgia,serif;
  --sans:"IBM Plex Sans KR","Apple SD Gothic Neo",system-ui,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
  --figfont:"IBM Plex Sans","IBM Plex Sans KR",system-ui,sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  color-scheme:dark;
  --ground:#12171C; --paper:#1A2027; --ink:#E6EAE8; --ink-2:#C3CBCA; --muted:#8D999D;
  --line:#2E3842; --accent:#7fa9e6; --accent-soft:#1B2A3E; --amber:#E0A94E; --amber-soft:#342913;
  --f-ink:#E6ECEA; --f-ink2:#A9B5B8; --f-grid:#26323A; --f-neutral:#6E7A7F;
  --s1:#7fa9e6; --s2:#e87a43; --s3:#f4c46a; --s4:#a45a26; --s5:#c2dcf7; --s2soft:#7a3e25;
}}
:root[data-theme="dark"]{
  color-scheme:dark;
  --ground:#12171C; --paper:#1A2027; --ink:#E6EAE8; --ink-2:#C3CBCA; --muted:#8D999D;
  --line:#2E3842; --accent:#7fa9e6; --accent-soft:#1B2A3E; --amber:#E0A94E; --amber-soft:#342913;
  --f-ink:#E6ECEA; --f-ink2:#A9B5B8; --f-grid:#26323A; --f-neutral:#6E7A7F;
  --s1:#7fa9e6; --s2:#e87a43; --s3:#f4c46a; --s4:#a45a26; --s5:#c2dcf7; --s2soft:#7a3e25;
}
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.8;margin:0;padding-inline:18px;padding-block:40px 90px;word-break:keep-all;overflow-wrap:anywhere}
.page{max-width:860px;margin:0 auto;background:var(--paper);border:1px solid var(--line);border-radius:3px;padding:44px clamp(18px,5vw,64px) 56px}
.meta{font-family:var(--mono);font-size:12px;color:var(--muted);display:flex;flex-wrap:wrap;gap:6px 16px;margin-bottom:22px}
.meta a{color:var(--accent)}
h1{font-family:var(--serif);font-weight:800;font-size:clamp(24px,3.6vw,32px);line-height:1.35;margin:0 0 18px;text-wrap:balance}
h2{font-family:var(--serif);font-weight:800;font-size:22px;margin:44px 0 12px;padding-top:14px;border-top:1px solid var(--line);text-wrap:balance}
h3{font-size:17px;font-weight:700;margin:30px 0 8px;text-wrap:balance}
p{margin:0 0 14px}
ul,ol{margin:0 0 14px;padding-left:1.3em}
li{margin:3px 0}
strong{color:var(--ink)}
.titlebox{background:var(--amber-soft);border-left:3px solid var(--amber);padding:12px 18px;border-radius:0 3px 3px 0;font-size:14px;color:var(--ink-2);margin:0 0 22px;line-height:1.65}
.titlebox ol{margin:6px 0 6px}
.titlebox i{color:var(--muted);font-size:13px}
.todo{display:inline-block;font-family:var(--mono);font-size:11.5px;color:var(--amber);background:var(--amber-soft);padding:1px 7px;border-radius:2px;margin-left:4px}
.eq{font-family:var(--serif);font-size:16.5px;background:var(--ground);border:1px solid var(--line);border-radius:3px;padding:14px 18px;margin:8px 0 16px;display:flex;flex-wrap:wrap;gap:6px 14px;justify-content:space-between;align-items:center}
.eqno{font-family:var(--mono);font-size:13px;color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:14px;margin:8px 0 4px;font-variant-numeric:tabular-nums}
.tw{overflow-x:auto}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-family:var(--mono);font-weight:500;font-size:12px;color:var(--muted);background:var(--ground)}
.cap{font-size:13.5px;color:var(--ink-2);margin:4px 0 18px}
figure{margin:18px 0 22px}
figure .plot{overflow-x:auto;background:var(--paper)}
figure svg{display:block;width:100%;min-width:540px;height:auto;margin:0 auto}
figcaption{font-size:13.5px;color:var(--ink-2);margin-top:6px;line-height:1.6}
figcaption b{color:var(--ink)}
.refs ul{padding-left:1.1em;font-size:14px}
nav.toc{font-size:13.5px;margin:0 0 10px;padding:12px 16px;background:var(--ground);border:1px solid var(--line);border-radius:3px}
nav.toc a{color:var(--ink-2);text-decoration:none}
nav.toc a:hover,nav.toc a:focus-visible{color:var(--accent);text-decoration:underline}
nav.toc ol{margin:4px 0 0;padding-left:1.2em;columns:2;column-gap:28px}
@media (max-width:640px){nav.toc ol{columns:1}}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
footer{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin-top:36px;padding-top:12px;border-top:1px solid var(--line)}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--title", default="PD 논문 한국어 원고")
    ap.add_argument("--meta", default="")
    ap.add_argument("--fig-dir", default=None, help="그림 SVG 폴더(기본 paper/figures)")
    ap.add_argument("--lang", default="ko", choices=["ko", "en"])
    a = ap.parse_args()
    global FIG_DIR
    if a.fig_dir:
        FIG_DIR = a.fig_dir
    src = open(a.md).read()
    figs = []

    def fig(m):
        name, cap = m.group(1).strip(), m.group(2).strip()
        figs.append(name)
        i = len(figs)
        num, _, rest = cap.partition(".")
        return (f'\n<figure id="{name}"><div class="plot">{svg(name, i)}</div>'
                f'<figcaption id="cap{i}"><b>{html.escape(num)}.</b>{html.escape(rest)}</figcaption></figure>\n')

    src = re.sub(r"<!--\s*FIG\s+(\S+)\s*\|\s*(.*?)-->", fig, src, flags=re.S)
    body = markdown.markdown(src, extensions=["tables", "md_in_html"])
    body = body.replace("<table>", '<div class="tw"><table>').replace("</table>", "</table></div>")
    # table of contents from h2
    heads = re.findall(r"<h2>(.*?)</h2>", body)
    for i, h in enumerate(heads):
        body = body.replace(f"<h2>{h}</h2>", f'<h2 id="s{i}">{h}</h2>', 1)
    toc_label = "목차" if a.lang == "ko" else "Contents"
    toc = f'<nav class="toc" aria-label="{toc_label}"><b>{toc_label}</b><ol>' + "".join(
        f'<li><a href="#s{i}">{h}</a></li>' for i, h in enumerate(heads)) + "</ol></nav>"
    body = re.sub(r"(</h1>)", r"\1" + toc, body, count=1)
    foot = (f"원본 {a.md} · 그림 {len(figs)}장 · harness/build_draft_html.py로 생성" if a.lang == "ko"
            else f"Source {a.md} · {len(figs)} figures · generated by harness/build_draft_html.py")
    page = (f"<title>{html.escape(a.title)}</title>\n"
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;700&'
            'family=IBM+Plex+Sans+KR:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&family=Noto+Serif+KR:wght@600;800&display=swap">\n'
            f"<style>{CSS}</style>\n<main class=\"page\">\n<div class=\"meta\">{a.meta}</div>\n{body}\n"
            f"<footer>{foot}</footer>\n</main>\n")
    open(a.out, "w").write(page)
    print(f"wrote {a.out}: {len(page)//1024} KB, {len(figs)} figures")


if __name__ == "__main__":
    main()
