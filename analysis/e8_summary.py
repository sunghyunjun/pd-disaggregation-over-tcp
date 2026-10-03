#!/usr/bin/env python3
"""Summary table of one measurement round (written for E8): per run, strict-SLO attainment (TTFT <=1 s, longest
gap per request <=50 ms), TTFT p50, p50/p90 of the longest gap per request, the number of global stalls (a gap
above 50 ms in 15 or more requests within 5 ms), and attainment with those stalls removed.
Usage: e8_summary.py [results/E8] [E8]   (prints a markdown table; the second argument is the round code, e.g. E9)
"""
import glob, json, os, re, sys

root = sys.argv[1] if len(sys.argv) > 1 else "results/E8"
stage = sys.argv[2] if len(sys.argv) > 2 else "E8"


def q(a, p):
    a = sorted(a)
    return a[int(p * (len(a) - 1))] if a else float("nan")


rows = []
for d in sorted(glob.glob(os.path.join(root, f"*_{stage}_*"))):
    f = os.path.join(d, "bench.json")
    if not os.path.isfile(f):
        continue
    m = re.match(r".*?(\d{4}-\d{2}-\d{2}T\d{6}Z)_" + stage + r"_(.+)_N0_(\w+)_r([\d.]+)$", d)
    if not m:
        continue
    ts, cfg, wl, rate = m.groups()
    b = json.load(open(f))
    T, I, S = b["ttfts"], b["itls"], b["start_times"]
    E = b.get("errors") or [""] * len(T)
    n = len(T)
    ok = [(not e) and t <= 1 and (not l or max(l) <= 0.05) for t, l, e in zip(T, I, E)]
    mx = [max(l) for l in I if l]
    ev = []
    for i, (s, t, l) in enumerate(zip(S, T, I)):
        tt = s + t
        for g in l:
            tt += g
            if g > 0.05:
                ev.append((tt, i))
    ev.sort()
    cl = []
    for e in ev:
        if cl and e[0] - cl[-1][-1][0] < 0.005:
            cl[-1].append(e)
        else:
            cl.append([e])
    glob_ = [c for c in cl if len({x[1] for x in c}) >= 15]
    greq = {x[1] for c in glob_ for x in c}
    oreq = {x[1] for c in cl if c not in glob_ for x in c}
    ok_wo = [o or ((not e) and t <= 1 and bool(l) and i in greq and i not in oreq)
             for i, (o, t, l, e) in enumerate(zip(ok, T, I, E))]
    ngpu = 2
    rows.append((cfg, wl, float(rate), ts, n, sum(ok) / n, sum(ok_wo) / n, len(glob_),
                 q(T, .5) * 1e3, q(mx, .5) * 1e3, q(mx, .9) * 1e3, sum(1 for e in E if e), float(rate) / ngpu))

rows.sort(key=lambda r: (r[0], r[1], r[2], r[3]))
print("| Config | Workload | Total req/s | Per GPU | n | Attainment | Without stalls | Global stalls | TTFT p50 ms | Longest gap p50 | p90 | Errors |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    cfg, wl, rate, ts, n, a, awo, g, t50, m50, m90, err, pg = r
    print(f"| {cfg} | {wl} | {rate:g} | {pg:g} | {n} | {a:.3f} | {awo:.3f} | {g} | {t50:.0f} | {m50:.1f} | {m90:.1f} | {err} |")
