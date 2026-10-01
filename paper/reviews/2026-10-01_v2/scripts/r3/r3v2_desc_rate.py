#!/usr/bin/env python3
"""R3 round-3: window-level relation between mean descriptor count and transfer rate, 26B 4K 1P1D at 3-4 req/s per GPU (E8, E9)."""
import re, glob, statistics as st, math
R = "results/"
pat = re.compile(r"Num successful transfers=(\d+), Avg xfer time \(ms\)=([\d.]+).*Avg MB per transfer=([\d.]+), Throughput \(MB/s\)=([\d.]+), Avg number of descriptors=([\d.]+)")
rows = []
for f in glob.glob(R + "E8/xfer_E8/26_1P1D_*_r[68]_*") + glob.glob(R + "E9/xfer_E9/26_*r8*"):
    for l in open(f):
        m = pat.search(l)
        if m:
            n, t, mb, thr, d = map(float, m.groups())
            if n >= 20 and mb >= 100: rows.append((d, thr * 0.008388608, t))
for lab, g in [("desc<1700", [r for r in rows if r[0] < 1700]), ("1700-2000", [r for r in rows if 1700 <= r[0] < 2000]), (">=2000", [r for r in rows if r[0] >= 2000])]:
    print(f"{lab:10s} windows {len(g):3d}  Gbps median {st.median(r[1] for r in g):5.2f}  xfer ms median {st.median(r[2] for r in g):4.0f}")
x = [r[0] for r in rows]; y = [r[1] for r in rows]; mx, my = st.mean(x), st.mean(y)
print("pearson r =", round(sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)), 2), "n =", len(rows))
