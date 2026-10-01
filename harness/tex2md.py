#!/usr/bin/env python3
"""Convert paper/en/main.tex to the markdown dialect of harness/build_draft_html.py.

Handles only the LaTeX this paper uses: sections (numbered, appendix letters), \\paragraph, itemize/enumerate,
figures (-> <!-- FIG name | Figure N. caption -->), tabularx tables (-> markdown tables with a caption line),
the two display equations, inline math, \\cite (numeric, order of first use, list built from refs.bib),
\\ref/\\eqref, footnotes (inline in parentheses), \\todo, \\url.

Usage: python3 harness/tex2md.py paper/en/main.tex -o paper/en/draft.md
"""
import argparse, re


def braced(s, i):
    """s[i] == '{' -> (content, index after the closing brace)"""
    assert s[i] == "{", s[i:i + 30]
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    raise ValueError("unbalanced braces near " + s[i:i + 60])


def sub_cmd(s, name, fn, nargs=1, opt=False):
    """Replace \\name[opt]{a}{b} with fn(*args) (balanced braces)."""
    out, i, pat = [], 0, "\\" + name
    while True:
        k = s.find(pat, i)
        if k < 0:
            out.append(s[i:]); break
        after = k + len(pat)
        if after < len(s) and (s[after].isalpha()):
            out.append(s[i:after]); i = after; continue
        out.append(s[i:k]); j = after
        o = None
        if opt and j < len(s) and s[j] == "[":
            e = s.index("]", j); o = s[j + 1:e]; j = e + 1
        args = []
        for _ in range(nargs):
            while j < len(s) and s[j] in " \n":
                j += 1
            a, j = braced(s, j); args.append(a)
        out.append(fn(*args) if not opt else fn(o, *args)); i = j
    return "".join(out)


def math(m):
    m = m.strip()
    m = re.sub(r"\\(mathrm|text)\{([^{}]*)\}", r"\2", m)
    reps = [(r"\times\,", "× "), (r"\times", "×"), (r"\ge", "≥"), (r"\le", "≤"),
            (r"\div", "÷"), (r"\pm", "±"), (r"\dagger", "†"), (r"\max", "max"), (r"\min", "min"), (r"\approx", "≈"),
            (r"\,", " "), ("{,}", ","), (r"\lceil", "⌈"), (r"\rceil", "⌉"), (r"\sum", "Σ"), (r"\tfrac", "")]
    for a, b in reps:
        m = m.replace(a, b)
    m = re.sub(r"_\{([^{}]*)\}", r"<sub>\1</sub>", m)
    m = re.sub(r"_([A-Za-z0-9])", r"<sub>\1</sub>", m)
    m = re.sub(r"\^\{([^{}]*)\}|\^(\S)", lambda g: "<sup>" + (g.group(1) or g.group(2)) + "</sup>", m)
    m = m.replace("{", "").replace("}", "")
    if re.fullmatch(r"[A-Za-z]", m):
        return f"<i>{m}</i>"
    return m


def inline(s, ctx):
    s = s.replace("\\$", "\x00DOLLAR\x00")
    s = sub_cmd(s, "todo", lambda a: f'<span class="todo">{a}</span>')
    s = sub_cmd(s, "url", lambda a: f"<{a}>")
    s = sub_cmd(s, "footnote", lambda a: f" ({a})")
    s = sub_cmd(s, "emph", lambda a: f"*{a}*")
    s = sub_cmd(s, "textbf", lambda a: f"**{a}**")
    s = sub_cmd(s, "texttt", lambda a: "<code>" + a.replace("\\_", "_").replace("-{}-", "\x00DD\x00") + "</code>")
    s = sub_cmd(s, "eqref", lambda a: f"({ctx['labels'][a]})")
    s = sub_cmd(s, "ref", lambda a: ctx["labels"][a])
    s = sub_cmd(s, "cite", lambda a: "[" + ", ".join(str(ctx["cite"](k.strip())) for k in a.split(",")) + "]")
    s = s.replace("\\protect", "")
    s = re.sub(r"\$([^$]+)\$", lambda m: math(m.group(1)), s)
    reps = [("\\textless", "&lt;"), ("\\textgreater", "&gt;"), ("\\textmu ", "µ"), ("\\textmu", "µ"), ("\\%", "%"), ("\\$", "$"), ("\\&", "&amp;"),
            ("\\_", "_"), ("---", "—"), ("--", "–"), ("``", "“"), ("''", "”"), ("~", "\u00a0"), ("\\ ", " "),
            ("D\\'ej\\`aVu", "DéjàVu"), ("et al.\\", "et al.")]
    for a, b in reps:
        s = s.replace(a, b)
    return s.replace("\x00DOLLAR\x00", "$").replace("\x00DD\x00", "--")


def bib_entries(path):
    txt = open(path).read()
    ents = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),", txt):
        key, start = m.group(2).strip(), m.end()
        depth, j = 1, m.end() - 1
        # find end of entry: matching brace of '@type{'
        depth = 0
        for j in range(txt.index("{", m.start()), len(txt)):
            if txt[j] == "{":
                depth += 1
            elif txt[j] == "}":
                depth -= 1
                if depth == 0:
                    break
        body = txt[start:j]
        f = {}
        for fm in re.finditer(r"(\w+)\s*=\s*", body):
            k, p = fm.group(1).lower(), fm.end()
            if p < len(body) and body[p] == "{":
                v, _ = braced(body, p)
            else:
                v = re.match(r"[^,\n]*", body[p:]).group(0)
            f.setdefault(k, v)
        ents[key] = f
    return ents


def clean_bib(v):
    v = v.replace("\\textasciitilde{}", "~").replace("\\url", "").replace("\\&", "&").replace("---", "—").replace("--", "–")
    v = v.replace("\\_", "_")
    v = v.replace("\\~n", "ñ").replace("\\'e", "é").replace("\\`a", "à").replace("\\'", "").replace('\\"', "")
    v = re.sub(r"\$\\times\$", "×", v)
    return re.sub(r"[{}]", "", v).replace("\\#", "#").strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("tex"); ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--bib", default=None)
    a = ap.parse_args()
    src = open(a.tex).read()
    src = re.sub(r"(?<!\\)%.*", "", src)
    body = src[src.index("\\begin{document}") + len("\\begin{document}"):src.index("\\end{document}")]
    title = re.search(r"\\title\{(.*?)\}\n\\author", src, re.S).group(1)
    t1, t2 = title.split("\\\\")
    t2 = t2.replace("\\large", "").strip()

    # pass 1: numbering of labels
    labels, sec, sub, app, fig, tab, eq = {}, 0, 0, False, 0, 0, 0
    afig = 0
    tabsec = {}
    for m in re.finditer(r"\\(section|subsection)(\*?)(\[[^\]]*\])?\{|\\appendix|\\label\{([^}]*)\}|\\begin\{(figure|table|equation)\}", body):
        if m.group(0) == "\\appendix":
            app, sec = True, 0; continue
        if m.group(1) == "section" and not m.group(2):
            sec += 1; sub = 0; cur = (chr(64 + sec) if app else str(sec)); last = cur; continue
        if m.group(1) == "subsection":
            sub += 1; last = f"{cur}.{sub}"; continue
        if m.group(5) == "figure":
            if app:
                afig += 1; last = f"A{afig}"
            else:
                fig += 1; last = str(fig)
            continue
        if m.group(5) == "table":
            if app:
                tabsec[cur] = tabsec.get(cur, 0) + 1; last = f"{cur}{tabsec[cur]}"
            else:
                tab += 1; last = str(tab)
            continue
        if m.group(5) == "equation":
            eq += 1; last = str(eq); continue
        if m.group(4):
            labels[m.group(4)] = last

    cites = []

    def cite(k):
        if k not in cites:
            cites.append(k)
        return cites.index(k) + 1
    ctx = {"labels": labels, "cite": cite}

    out = [f"# {inline(t1.strip(), ctx)}", "", f"*{inline(t2, ctx)}*", "",
           "Sunghyun Jun · " + '<span class="todo">contact email</span>' + " · " +
           inline(re.search(r"\\date\{(.*)\}", src).group(1), ctx), ""]
    body = body.replace("\\maketitle", "")
    body = re.sub(r"\\(setcounter|renewcommand|counterwithin)\{[^{}]*\}(\{[^{}]*(\{[^{}]*\})?[^{}]*\})?", "", body)
    body = body.replace("\\clearpage", "").replace("\\bibliographystyle{unsrtnat}", "")

    # block-level pass
    lines = body.split("\n")
    i, app, sec, sub, fign, afign, tabn, tabsec, eqn = 0, False, 0, 0, 0, 0, 0, {}, 0
    curletter = ""
    blk = []

    def flush():
        if blk:
            out.append(inline(" ".join(x.strip() for x in blk), ctx)); out.append(""); blk.clear()

    while i < len(lines):
        L = lines[i].strip()
        if not L:
            flush(); i += 1; continue
        if L == "\\appendix":
            flush(); app, sec = True, 0; i += 1; continue
        if L.startswith("\\begin{abstract}"):
            flush(); out += ["## Abstract", ""]; i += 1; continue
        if L.startswith("\\end{abstract}"):
            flush(); i += 1; continue
        m = re.match(r"\\section(\*?)(\[[^\]]*\])?\{", L)
        if m:
            flush()
            j = L.index("{", m.start() + len("\\section") + len(m.group(1)) + len(m.group(2) or ""))
            t, _ = braced(L, j)
            notes = []
            t = sub_cmd(t.replace("\\protect", ""), "footnote", lambda x: notes.append(x) or "")
            if m.group(1):
                out += [f"## {inline(t, ctx)}", ""]
            else:
                sec += 1; sub = 0
                num = chr(64 + sec) if app else str(sec)
                curletter = num
                out += [f"## {num}. {inline(t, ctx)}", ""]
            out += [f'<p class="cap">{inline(x, ctx)}</p>' for x in notes] + ([""] if notes else [])
            i += 1; continue
        m = re.match(r"\\subsection\{", L)
        if m:
            flush(); sub += 1
            t, _ = braced(L, L.index("{"))
            out += [f"### {curletter}.{sub} {inline(t, ctx)}", ""]
            i += 1; continue
        if L.startswith("\\paragraph{"):
            flush()
            t, j = braced(L, len("\\paragraph"))
            blk.append(f"**{t}** " + L[j:].strip()); i += 1; continue
        if L.startswith("\\begin{itemize}") or L.startswith("\\begin{enumerate}"):
            flush(); num = L.startswith("\\begin{enumerate}"); items, cur = [], None
            i += 1
            while not (lines[i].strip().startswith("\\end{itemize}") or lines[i].strip().startswith("\\end{enumerate}")):
                x = lines[i].strip()
                if x.startswith("\\item"):
                    if cur is not None:
                        items.append(cur)
                    cur = x[len("\\item"):].strip()
                elif x and cur is not None:
                    cur += " " + x
                i += 1
            if cur is not None:
                items.append(cur)
            for n, it in enumerate(items, 1):
                out.append((f"{n}. " if num else "- ") + inline(it.rstrip("}").strip() if it.endswith("}") and it.count("{") < it.count("}") else it, ctx))
            out.append(""); i += 1; continue
        if L.startswith("\\begin{equation}"):
            flush(); eqn += 1; buf = []
            i += 1
            while not lines[i].strip().startswith("\\end{equation}"):
                buf.append(lines[i].strip()); i += 1
            e = " ".join(buf)
            e = re.sub(r"\\label\{[^}]*\}", "", e)
            e = e.replace("\\frac{V(L)}{m \\times C_{\\mathrm{flow}}}", "V(L) ÷ (m × C_{flow})")
            e = e.replace("\\mathrm{TTFT}_{\\mathrm{PD}}", "TTFT_{PD}").replace("\\mathrm{TTFT}_{\\mathrm{coloc}}", "TTFT_{coloc}")
            e = e.replace("\\text{residual}", "residual").replace("b_{\\mathrm{g}}\\,L", "b_{g} L")
            e = math(e)
            e = re.sub(r"\b([LWVm])\b(?![^<]*>)", r"<i>\1</i>", e)
            out += [f'<div class="eq"><span>{e}</span><span class="eqno">({eqn})</span></div>', ""]
            i += 1; continue
        if L.startswith("\\begin{figure}"):
            flush(); buf = []
            i += 1
            while not lines[i].strip().startswith("\\end{figure}"):
                buf.append(lines[i].strip()); i += 1
            b = " ".join(buf)
            name = re.search(r"\\includegraphics(\[[^\]]*\])?\{([^}]*)\}", b).group(2).replace(".pdf", "")
            cap, _ = braced(b, b.index("\\caption") + len("\\caption"))
            if app:
                afign += 1; fnum = f"A{afign}"
            else:
                fign += 1; fnum = str(fign)
            out += [f"<!-- FIG {name} | Figure {fnum}. {inline(cap, ctx).replace('|', '/')} -->", ""]
            i += 1; continue
        if L.startswith("\\begin{table}"):
            flush(); buf = []
            i += 1
            while not lines[i].strip().startswith("\\end{table}"):
                buf.append(lines[i]); i += 1
            b = "\n".join(buf)
            cap, _ = braced(b, b.index("\\caption") + len("\\caption"))
            if app:
                tabsec[curletter] = tabsec.get(curletter, 0) + 1; tnum = f"{curletter}{tabsec[curletter]}"
            else:
                tabn += 1; tnum = str(tabn)
            inner = re.search(r"\\begin\{tabularx?\}(\{[^}]*\})?\{[^}]*\}(.*?)\\end\{tabularx?\}", b, re.S).group(2)
            inner = inner.replace("\\toprule", "").replace("\\bottomrule", "")
            parts = inner.split("\\midrule")
            head, rows = parts[0], "\\\\".join(parts[1:]) if len(parts) > 1 else ""
            def cells(r):
                return [inline(c.strip(), ctx) for c in re.split(r"(?<!\\)&", r)]
            hrow = [r for r in head.split("\\\\") if r.strip()][0]
            hc = cells(hrow)
            out.append("| " + " | ".join(hc) + " |")
            out.append("|" + "---|" * len(hc))
            for r in rows.split("\\\\"):
                if r.strip():
                    out.append("| " + " | ".join(cells(r)) + " |")
            out += ["", f'<p class="cap"><b>Table {tnum}.</b> {inline(cap, ctx)}</p>', ""]
            i += 1; continue
        if L.startswith("\\bibliography{"):
            flush(); i += 1; continue
        if L.startswith("{\\small") or L == "}" or L.startswith("\\centering"):
            i += 1; continue
        blk.append(L); i += 1
    flush()

    # references
    ents = bib_entries(a.bib or a.tex.replace("main.tex", "refs.bib"))
    refs = ["## References", "", '<div class="refs" markdown="1">', ""]
    for n, k in enumerate(cites, 1):
        f = ents.get(k, {})
        au = clean_bib(f.get("author", "")).replace(" and others", " et al.").replace(" and ", ", ")
        ti = clean_bib(f.get("title", ""))
        venue = clean_bib(f.get("booktitle") or f.get("journal") or f.get("howpublished") or "")
        yr = clean_bib(f.get("year", ""))
        url = clean_bib(f.get("url", "")) or (("https://doi.org/" + clean_bib(f["doi"])) if f.get("doi") else "")
        if venue.startswith("http"):
            url, venue = venue, ""
        txt = " ".join(x if x.endswith(".") else x + "." for x in (au, ti, venue, yr) if x)
        refs.append(f"- [{n}] {txt}" + (f" <{url}>" if url else ""))
    refs += ["", "</div>", ""]
    # put references before the appendix (the first appendix section is "A.")
    md = "\n".join(out)
    k = md.find("\n## A. ")
    md = md[:k] + "\n" + "\n".join(refs) + md[k:] if k >= 0 else md + "\n" + "\n".join(refs)
    md = re.sub(r"\n{3,}", "\n\n", md)
    open(a.out, "w").write(md)
    print(f"wrote {a.out}: {len(md)//1024} KB, {len(cites)} references, {fign + afign} figures, {tabn + sum(tabsec.values())} tables")


if __name__ == "__main__":
    main()
