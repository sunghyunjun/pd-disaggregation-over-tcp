#!/usr/bin/env python3
"""Chair check (read-only): decisive head-to-head points. Attainment under old (1-token = fail if no gap?) and new
(1-token judged on TTFT only) rules, seed, median TTFT, p99 TTFT, median per-request max gap, median ITL, and for
replica runs the attainment among requests that arrived with <100 in flight. Run: python3 r6_keypoints.py"""
import json, glob, os, re, bisect, statistics as st
ROOT = "results"
pats = ["E8/*_26_B2_c1024_*_r8", "E8/*_26_B2_c1024_*_r10", "E8/*_26_B2_c1024_*_r6", "E8/*_26_B2_c1024_*_r4",
        "E8/*_26_1P1D_aio_*_r8", "E8/*_26_1P1D_toyi_*_r8", "E8/*_26_1P1D_aio_*_r6", "E8/*_26_1P1D_toyi_*_r6", "E7/*_26_1P1D_*random_r8", "E7/*_26_1P1D_*random_r6",
        "E8/*_26_1P1D_aio_*_r10", "E8/*_26_B2_c1024_*_r2",
        "E8/*_31_B2_c256_*", "E8/*_31_1P1D_aio_*", "E5/*_31_1P1D_*sharegpt_r8", "E7/*_31_1P1D_*sharegpt_r8", "E7/*_31_1P1D_*sharegpt_r4", "E5/*_31_1P1D_*sharegpt_r4",
        "E7/*_31_1P1D_*sharegpt_r1*", "E5/*_31_1P1D_*sharegpt_r1*"]
def seed(d):
    try:
        t = open(d + "/bench.log").read()
        m = re.search(r"seed[=: ]+(\d+)", t); return m.group(1) if m else "?"
    except Exception: return "?"
seen = set()
print(f"{'run':52s} {'seed':>6s} {'n':>5s} {'att_new':>7s} {'att_old':>7s} {'1tok':>4s} {'ttft50':>6s} {'ttft99':>6s} {'mg50':>5s} {'itl50':>5s} {'att<100':>7s}")
for p in pats:
    for d in sorted(glob.glob(ROOT + "/" + p)):
        if d in seen or not os.path.exists(d + "/bench.json"): continue
        seen.add(d)
        b = json.load(open(d + "/bench.json"))
        n = len(b["ttfts"]); ok_new = ok_old = one = 0
        mg = []; itl = []
        st_, lat = b["start_times"], b["latencies"]
        se = sorted(s + l for s, l in zip(st_, lat)); ss = sorted(st_)
        good_lo = tot_lo = 0
        for i in range(n):
            t, it, e = b["ttfts"][i], b["itls"][i], b["errors"][i]
            if e or not t: continue
            m = max(it) if it else None
            if m is not None: mg.append(m); itl += it
            if not it: one += 1
            new = t <= 1.0 and (m is None or m <= 0.05)
            old = t <= 1.0 and (m is not None and m <= 0.05)
            ok_new += new; ok_old += old
            inf = bisect.bisect_left(ss, st_[i]) - bisect.bisect_right(se, st_[i])
            if inf < 100: tot_lo += 1; good_lo += new
        tt = sorted(x for x in b["ttfts"] if x)
        q = lambda xs, p: xs[min(len(xs) - 1, int(p * len(xs)))]
        lab = os.path.basename(d)[:-0] if False else d.split("/")[-2] + "/" + os.path.basename(d)[11:]
        print(f"{lab:52s} {seed(d):>6s} {n:5d} {ok_new/n:7.3f} {ok_old/n:7.3f} {one:4d} {q(tt,.5)*1e3:6.0f} {q(tt,.99)*1e3:6.0f} {st.median(mg)*1e3:5.1f} {st.median(itl)*1e3:5.1f} {good_lo/max(tot_lo,1):7.3f}")
